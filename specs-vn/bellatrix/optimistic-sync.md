# Bellatrix -- Optimistic Sync

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Constants](#constants)
- [Helpers](#helpers)
- [Mechanisms](#mechanisms)
  - [When to optimistically import blocks](#when-to-optimistically-import-blocks)
  - [How to optimistically import blocks](#how-to-optimistically-import-blocks)
  - [How to apply `latestValidHash` when payload status is `INVALID`](#how-to-apply-latestvalidhash-when-payload-status-is-invalid)
  - [Execution Engine Errors](#execution-engine-errors)
  - [Assumptions about Execution Engine Behaviour](#assumptions-about-execution-engine-behaviour)
  - [Re-Orgs](#re-orgs)
- [Fork Choice](#fork-choice)
  - [Fork Choice Poisoning](#fork-choice-poisoning)
- [Checkpoint Sync (Weak Subjectivity Sync)](#checkpoint-sync-weak-subjectivity-sync)
- [Validator assignments](#validator-assignments)
  - [Block Production](#block-production)
  - [Attesting](#attesting)
  - [Participating in Sync Committees](#participating-in-sync-committees)
- [Ethereum Beacon APIs](#ethereum-beacon-apis)
- [Design Decision Rationale](#design-decision-rationale)
  - [Why sync optimistically?](#why-sync-optimistically)
  - [Why `SAFE_SLOTS_TO_IMPORT_OPTIMISTICALLY`?](#why-safe_slots_to_import_optimistically)
  - [Transitioning from VALID -> INVALIDATED or INVALIDATED -> VALID](#transitioning-from-valid---invalidated-or-invalidated---valid)
  - [What about Light Clients?](#what-about-light-clients)
  - [What if `TERMINAL_BLOCK_HASH` is used?](#what-if-terminal_block_hash-is-used)

<!-- mdformat-toc end -->

## Introduction

Để cung cấp cho một execution engine đang sync một góc nhìn một phần về head của
chain, consensus engine có thể cần import các beacon block mà không kiểm tra các
execution payload của chúng. Kiểu sync một phần này được gọi là *optimistic
sync* (sync "lạc quan").

> 💡 Ghi chú: "Lạc quan" ở đây nghĩa là consensus client tạm thời tin rằng
> execution payload hợp lệ (vì execution engine chưa đủ dữ liệu để kiểm tra), và
> sẽ cập nhật lại trạng thái của block khi execution engine đưa ra kết luận.

Optimistic sync được thiết kế theo kiểu tùy chọn (opt-in) và tương thích ngược
(tức là các node không optimistic có thể cùng tồn tại với các node optimistic
trên mạng và ngược lại). Optimistic sync không phải là yêu cầu cốt lõi đối với
consensus node. Đúng hơn, đây là một giải pháp tạm thời để cho phép execution
node sync bằng các phương pháp sẵn có cho tới khi các hạng mục tương lai trong
lộ trình (roadmap) của Ethereum được hiện thực (ví dụ: statelessness).

## Constants

| Name                                  | Value       |
| ------------------------------------- | ----------- |
| `SAFE_SLOTS_TO_IMPORT_OPTIMISTICALLY` | `Slot(128)` |

*Lưu ý: `SAFE_SLOTS_TO_IMPORT_OPTIMISTICALLY` phải (must) cho phép người dùng cấu
hình được. Xem [Fork Choice Poisoning](#fork-choice-poisoning).*

## Helpers

Để ngắn gọn, ta định nghĩa hai bí danh (alias) cho các giá trị của trường
`status` trong `PayloadStatusV1`:

- Bí danh `NOT_VALIDATED` cho:
  - `SYNCING`
  - `ACCEPTED`
- Bí danh `INVALIDATED` cho:
  - `INVALID`
  - `INVALID_BLOCK_HASH`

Gọi `head: BeaconBlock` là kết quả của việc gọi thuật toán fork choice tại thời
điểm sản xuất block. Gọi `head_block_root: Root` là root của block đó.

Gọi `blocks: dict[Root, BeaconBlock]` và
`block_states: dict[Root, BeaconState]` là các block (và state đi kèm) đã được
kiểm tra hoặc đầy đủ, hoặc theo kiểu optimistic.

Gọi `optimistic_roots: set[Root]` là tập hợp các `hash_tree_root(block)` của tất
cả các block được import theo kiểu optimistic mà mới chỉ nhận được trạng thái
`NOT_VALIDATED` từ execution engine (tức là chưa biết chúng là `INVALIDATED` hay
`VALID`).

Gọi `current_slot: Slot` là `compute_slot_at_time(genesis_time, time)`, trong đó
`time` là thời gian UNIX theo đồng hồ hệ thống cục bộ.

```python
@dataclass
class OptimisticStore:
    optimistic_roots: set[Root]
    head_block_root: Root
    blocks: dict[Root, BeaconBlock]
    block_states: dict[Root, BeaconState]
```

```python
def is_optimistic(opt_store: OptimisticStore, block: BeaconBlock) -> bool:
    return hash_tree_root(block) in opt_store.optimistic_roots
```

```python
def latest_verified_ancestor(opt_store: OptimisticStore, block: BeaconBlock) -> BeaconBlock:
    # Giả định rằng tham số `block` không bao giờ là một block INVALIDATED.
    while True:
        if not is_optimistic(opt_store, block) or block.parent_root == Root():
            return block
        block = opt_store.blocks[block.parent_root]
```

```python
def is_execution_block(block: BeaconBlock) -> bool:
    return block.body.execution_payload != ExecutionPayload.empty()
```

```python
def is_optimistic_candidate_block(
    opt_store: OptimisticStore, current_slot: Slot, block: BeaconBlock
) -> bool:
    if is_execution_block(opt_store.blocks[block.parent_root]):
        return True

    if block.slot + SAFE_SLOTS_TO_IMPORT_OPTIMISTICALLY <= current_slot:
        return True

    return False
```

Một node được gọi là *optimistic node* nếu fork choice của nó ở một trong các
trạng thái sau:

1. `is_optimistic(opt_store, head) is True`
2. Các block từ mọi nhánh khả thi (viable, xét theo FFG) đều đã chuyển từ
   `NOT_VALIDATED` sang `INVALIDATED`, khiến cây block không còn nhánh khả thi
   nào

Chỉ validator chạy trên một optimistic node mới được gọi là *optimistic
validator*.

Khi đặc tả này chỉ định nghĩa hành vi cho optimistic node/validator mà *không*
định nghĩa cho trường hợp không optimistic, hãy giả định hành vi mặc định như
khi không có optimistic sync.

## Mechanisms

### When to optimistically import blocks

Một block MAY được import theo kiểu optimistic khi
`is_optimistic_candidate_block(opt_store, current_slot, block)` trả về `True`.
Điều này đảm bảo block chỉ được import optimistic nếu ít nhất một trong các điều
kiện sau là đúng:

1. Block cha của block đó đã bật execution (có execution payload).
2. Slot hiện tại (theo đồng hồ hệ thống) đi trước slot của block đang được import
   ít nhất `SAFE_SLOTS_TO_IMPORT_OPTIMISTICALLY` slot.

Về thực chất, có các giới hạn về thời điểm một *merge block* có thể được import
optimistic. Merge block là block đầu tiên trong một chain bất kỳ thỏa mãn
`is_execution_block(block) == True`. Mọi hậu duệ của merge block đều có thể được
import optimistic vào bất kỳ lúc nào.

*Xem [Fork Choice Poisoning](#fork-choice-poisoning) để hiểu động cơ đằng sau các
điều kiện này.*

### How to optimistically import blocks

Để import một block theo kiểu optimistic:

- Hàm
  [`verify_and_notify_new_payload`](./beacon-chain.md#verify_and_notify_new_payload)
  MUST trả về `True` nếu execution engine trả về `NOT_VALIDATED` hoặc `VALID`.
  Phản hồi `INVALIDATED` MUST trả về `False`.
- Hàm [`validate_merge_block`](./fork-choice.md#validate_merge_block) MUST NOT
  raise assertion nếu cả `pow_block` và `pow_parent` đều chưa được execution
  engine biết đến.
  - Mọi assertion khác trong
    [`validate_merge_block`](./fork-choice.md#validate_merge_block) (ví dụ:
    `TERMINAL_BLOCK_HASH`) MUST ngăn việc import optimistic.
- Block cha của block MUST NOT có execution payload ở trạng thái `INVALIDATED`.

Ngoài thay đổi trong việc kiểm tra hợp lệ này, consensus engine MUST theo dõi
block nào đã trả về `NOT_VALIDATED` và block nào trả về `VALID` để xử lý về sau.

Các block được import optimistic MUST vượt qua mọi bước kiểm tra trong
`process_block` (ngoại trừ phần đã sửa đổi của `verify_and_notify_new_payload`).

Consensus engine MUST có khả năng sửa đổi hồi tố (tức là sau khi import) trạng
thái của các block `NOT_VALIDATED` thành `VALID` hoặc `INVALIDATED` dựa trên phản
hồi từ execution engine. Tức là thực hiện các chuyển đổi sau:

- `NOT_VALIDATED` -> `VALID`
- `NOT_VALIDATED` -> `INVALIDATED`

Khi một block chuyển từ `NOT_VALIDATED` -> `VALID`, mọi *tổ tiên (ancestor)* của
block đó cũng MUST chuyển từ `NOT_VALIDATED` -> `VALID`. Block đó cùng mọi tổ
tiên trước đây ở trạng thái `NOT_VALIDATED` không còn được coi là "được import
optimistic" nữa.

Khi một block chuyển từ `NOT_VALIDATED` -> `INVALIDATED`, mọi *hậu duệ
(descendant)* của block đó cũng MUST chuyển từ `NOT_VALIDATED` -> `INVALIDATED`.

> 💡 Ghi chú: Logic ở đây là: nếu một block hợp lệ thì toàn bộ chuỗi dẫn tới nó
> cũng phải hợp lệ; ngược lại, nếu một block không hợp lệ thì mọi block xây dựng
> trên nó cũng không thể hợp lệ.

Khi một block rời khỏi trạng thái `NOT_VALIDATED`, nó bị xóa khỏi tập
`opt_store.optimistic_roots`.

Khi một "merge block" (tức là block đầu tiên bật execution trong một chain) được
execution engine tuyên bố là `VALID` (trực tiếp hoặc gián tiếp), hàm
[`validate_merge_block`](./fork-choice.md#validate_merge_block) đầy đủ MUST được
chạy đối với merge block đó. Nếu block không vượt qua
[`validate_merge_block`](./fork-choice.md#validate_merge_block), merge block MUST
được xử lý giống như một block `INVALIDATED` (tức là nó và mọi hậu duệ của nó bị
vô hiệu hóa và bị xóa khỏi cây block).

### How to apply `latestValidHash` when payload status is `INVALID`

Việc xử lý trạng thái payload `INVALID` phụ thuộc vào tham số `latestValidHash`.
Cách tiếp cận chung như sau:

1. Consensus engine MUST xác định `invalidBlock` theo định nghĩa trong bảng dưới
   đây.
2. `invalidBlock` và mọi hậu duệ của nó MUST được chuyển từ `NOT_VALIDATED` sang
   `INVALIDATED`.

| `latestValidHash`       | `invalidBlock`                                                                                                                                                    |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Execution block hash    | Block *con* của block có `body.execution_payload.block_hash == latestValidHash`, nằm trong chain chứa block có payload đang xét                                    |
| `0x00..00` (all zeroes) | Block đầu tiên có `body.execution_payload != ExecutionPayload.empty()` trong chain chứa block có payload đang xét                                                 |
| `null`                  | Chính block có payload đang xét                                                                                                                                   |

Khi `latestValidHash` là một execution block hash có ý nghĩa nhưng consensus
engine không tìm được block nào thỏa mãn
`body.execution_payload.block_hash == latestValidHash`, consensus engine SHOULD
hành xử giống như khi `latestValidHash` là `null`.

### Execution Engine Errors

Khi execution engine trả về lỗi hoặc không phản hồi yêu cầu kiểm tra tính hợp lệ
của payload cho một block nào đó, consensus engine:

- MUST NOT import optimistic block đó.
- MUST NOT áp dụng block đó vào fork choice store.
- MAY đưa block vào hàng đợi để xử lý sau.

### Assumptions about Execution Engine Behaviour

Đặc tả này giả định execution engine chỉ trả về `NOT_VALIDATED` khi không có đủ
thông tin để đưa ra kết luận `VALID` hoặc `INVALIDATED` đối với `ExecutionPayload`
được cung cấp (ví dụ: payload cha chưa được biết). Cụ thể, các phản hồi
`NOT_VALIDATED` nên gắn với từng fork riêng, nghĩa là việc tìm kiếm một block
trên một chain MUST NOT kích hoạt phản hồi `NOT_VALIDATED` cho một chain khác.

### Re-Orgs

Consensus engine MUST hỗ trợ mọi chain reorganisation (tái tổ chức chain) *không*
ảnh hưởng đến justified checkpoint.

Nếu justified checkpoint chuyển từ `NOT_VALIDATED` -> `INVALIDATED`, consensus
engine MAY chọn cách cảnh báo người dùng và buộc ứng dụng thoát.

## Fork Choice

Consensus engine MUST hỗ trợ việc loại bỏ khỏi fork choice các block chuyển từ
`NOT_VALIDATED` sang `INVALIDATED`. Cụ thể, một block bị coi là `INVALIDATED` vào
bất kỳ thời điểm nào MUST NOT được đưa vào canonical chain, và trọng số (weight)
từ các block `INVALIDATED` đó MUST NOT được cộng vào bất kỳ tổ tiên `VALID` hay
`NOT_VALIDATED` nào.

### Fork Choice Poisoning

Trong quá trình chuyển đổi merge, kẻ tấn công có thể tạo ra một `BeaconBlock` có
execution payload tham chiếu tới một `body.execution_payload.parent_hash` vĩnh
viễn không thể có được (tức là parent hash là các byte ngẫu nhiên). Trong một số
trường hợp hiếm, kẻ tấn công có thể xây dựng tiếp trên block như vậy để kích hoạt
justification. Nếu một optimistic node import chain độc hại này, node đó sẽ có một
fork choice store bị "đầu độc" (poisoned): node không thể sản xuất block là hậu
duệ của head (do chuỗi payload không hợp lệ), và cũng không thể sản xuất block
rẽ nhánh khỏi head (do chain độc hại đã được justified).

Nếu tồn tại một honest chain (chain trung thực) justify một epoch cao hơn chain
độc hại, chain đó sẽ được ưu tiên và "hồi sinh" mọi store bị đầu độc. Nếu được
import trước chain độc hại, chain như vậy sẽ ngăn store bị đầu độc ngay từ đầu.
Do đó, tấn công đầu độc chỉ mang tính tạm thời nếu >= 2/3 mạng là trung thực và
không gặp lỗi.

Tham số `SAFE_SLOTS_TO_IMPORT_OPTIMISTICALLY` giả định rằng mạng sẽ justify một
honest chain trong vòng một số slot nhất định. Với giả định này, việc import
optimistic các transition block trong quá trình sync là chấp nhận được. Vì đã giả
định tồn tại một honest chain với justified checkpoint cao hơn, mọi fork choice
poisoning sẽ chỉ tồn tại ngắn và được giải quyết trước khi node đó cần sản xuất
block.

Tuy nhiên, giả định rằng honest canonical chain sẽ luôn được justify trong vòng
`SAFE_SLOTS_TO_IMPORT_OPTIMISTICALLY` slot là đáng ngờ. Vì vậy, client MUST cung
cấp cờ dòng lệnh (command line flag) sau để hỗ trợ khôi phục thủ công khi có sự
cố nghiêm trọng:

- `--safe-slots-to-import-optimistically`: thay đổi giá trị
  `SAFE_SLOTS_TO_IMPORT_OPTIMISTICALLY`.

## Checkpoint Sync (Weak Subjectivity Sync)

Consensus engine MAY giả định rằng `ExecutionPayload` của block được dùng làm
anchor (điểm neo) cho checkpoint sync là `VALID` mà không nhất thiết phải gửi
payload đó cho execution engine.

## Validator assignments

Một optimistic node *không* phải là full node. Nó không thể sản xuất block, vì
execution engine không thể tạo payload trên một block cha chưa biết. Nó cũng
không thể attest một cách trung thực cho head block của chain, vì nó chưa kiểm
tra đầy đủ block đó.

### Block Production

Optimistic validator MUST NOT sản xuất block (tức là ký trên domain
`DOMAIN_BEACON_PROPOSER`).

### Attesting

Optimistic validator MUST NOT tham gia attestation (tức là ký trên các domain
`DOMAIN_BEACON_ATTESTER`, `DOMAIN_SELECTION_PROOF` hoặc
`DOMAIN_AGGREGATE_AND_PROOF`).

### Participating in Sync Committees

Optimistic validator MUST NOT tham gia sync committee (tức là ký trên các domain
`DOMAIN_SYNC_COMMITTEE`, `DOMAIN_SYNC_COMMITTEE_SELECTION_PROOF` hoặc
`DOMAIN_CONTRIBUTION_AND_PROOF`).

## Ethereum Beacon APIs

Các consensus engine có hiện thực
[Ethereum Beacon APIs](https://github.com/ethereum/beacon-APIs) phải (must) chú ý
đảm bảo giá trị `execution_optimistic` được đặt thành `True` bất cứ khi nào
request tham chiếu tới block optimistic (và ngược lại).

## Design Decision Rationale

### Why sync optimistically?

Hầu hết execution engine dùng state sync làm cơ chế sync mặc định trên Ethereum
Mainnet, vì việc thực thi lại các block từ genesis mất vài tuần trên phần cứng
phổ thông.

State sync cần biết head hiện tại của chain để cuối cùng có thể hội tụ. Nếu không
liên tục được cung cấp head mới nhất, state sync sẽ không thể hoàn tất, vì state
gần đây sẽ nhanh chóng không còn khả dụng do state trie bị pruning (cắt tỉa).

Import block theo kiểu optimistic (tức là import khi execution engine hiện *chưa
thể* kiểm tra payload) phá vỡ thế bế tắc (deadlock) giữa tiến trình sync của
execution layer và việc import beacon block trong lúc execution engine đang sync.

> 💡 Ghi chú: Bế tắc ở đây là: execution engine cần biết head mới nhất từ
> consensus layer để sync, còn consensus layer lại cần execution engine kiểm tra
> payload trước khi import block để cập nhật head.

Optimistic sync cũng là chiến lược tối ưu cho các execution engine dùng việc thực
thi block làm cơ chế sync mặc định (ví dụ: Erigon). Một cách khác là consensus
engine gửi cho execution engine payload lấy từ một checkpoint block, đợi cho tới
khi execution layer bắt kịp, rồi sau đó tiến hành song song từng bước (lock step).
Cách tiếp cận thay thế này sẽ khiến người dùng phải chờ đợi vài giờ và làm tăng
thời gian sync, vì batch sync (sync theo lô) có nhiều cơ hội tối ưu hơn so với
lock step.

Những tiền đề nêu trên khiến optimistic sync trở thành một giải pháp *tổng quát*
cho việc tương tác giữa consensus engine và execution engine trong quá trình sync.

### Why `SAFE_SLOTS_TO_IMPORT_OPTIMISTICALLY`?

Node chỉ có thể import một block optimistic nếu justified checkpoint của nó đã
được kiểm tra, hoặc block đó cũ hơn `SAFE_SLOTS_TO_IMPORT_OPTIMISTICALLY`.

Các ràng buộc này được áp dụng nhằm giảm thiểu một kiểu tấn công trong đó một
block bật execution (một *transition block*) có thể tham chiếu tới một parent hash
rác. Điều này khiến các node trung thực không thể xây dựng tiếp trên block đó.
Nếu kẻ tấn công khai thác một điểm tinh tế trong `filter_node_tree` của fork
choice, trong một số trường hợp hiếm, chúng có thể tạo ra một block rác thắng tất
cả các block được sản xuất cục bộ trong cuộc cạnh tranh làm head. Điều này ngăn
node sản xuất một chuỗi block, từ đó phá vỡ liveness (tính sống của mạng).

May mắn là nếu 2/3 validator không bị đầu độc, họ có thể justify một honest chain
và "giải độc" cho tất cả các node khác.

Đáng chú ý, tấn công này chỉ tồn tại đối với optimistic node. Các node kiểm tra
đầy đủ transition block sẽ từ chối block có parent hash rác. Vì vậy, liveness
không bị ảnh hưởng nếu đại đa số node đã sync đầy đủ cả execution client và
consensus client trước và trong quá trình chuyển đổi.

Từ tất cả những điều trên, ta có thể rút ra hai điều:

1. **Các BN (beacon node) đang theo dõi head trong quá trình chuyển đổi không nên
   import optimistic transition block.** Nếu 1/3 validator import optimistic
   block bị đầu độc, sẽ không còn đủ node để justify một honest chain.
2. **Các BN đang sync có thể import optimistic transition block.** Trong trường
   hợp này, một chain đã được justified đã tồn tại. Block bị đầu độc sẽ nhanh
   chóng bị loại bỏ và không ảnh hưởng tới liveness.

Người đọc tinh ý sẽ nhận ra rằng (2) chứa một giả định rõ ràng về liveness của
mạng. Điều này là cần thiết, vì một node không thể xác định một cách khả thi rằng
transition block đã được justified nếu không import block đó và chấp nhận rủi ro
bị đầu độc. Do đó, ta dùng `SAFE_SLOTS_TO_IMPORT_OPTIMISTICALLY` để diễn đạt đại
ý: *"nếu transition block đã đủ cũ, ta có thể giả định block đó là trung thực,
hoặc đã tồn tại một honest justified chain có thể thắng nó."*

Lưu ý việc dùng từ "khả thi" trong đoạn trước. Có thể hình dung các cơ chế kiểm
tra một block đã được justified hay chưa trước khi import nó. Ví dụ: cứ tiếp tục
xử lý các block mà không đưa chúng vào fork choice. Tuy nhiên, ở đây vẫn còn các
trường hợp biên (ví dụ: khi nào thì dừng và kết luận rằng không có justification?)
và vấn đề làm sao giảm độ phức tạp khi hiện thực. Tại điểm này, cần cân nhắc lại
về kiểu tấn công và khả năng nó xảy ra. Nó đòi hỏi những hoàn cảnh khá gượng ép
và có vẻ rất khó xảy ra. Vì vậy, ta cần xem xét liệu việc thêm độ phức tạp để
tránh một tấn công khó xảy ra sẽ làm tăng hay giảm tổng rủi ro. Hiện tại,
`SAFE_SLOTS_TO_IMPORT_OPTIMISTICALLY` có vẻ là điểm cân bằng hợp lý cho sự đánh
đổi này.

### Transitioning from VALID -> INVALIDATED or INVALIDATED -> VALID

Các thao tác này được cố ý bỏ qua. Chúng nằm ngoài phạm vi của đặc tả vì chỉ có
thể xảy ra khi EE (execution engine) bị lỗi.

Tình huống như vậy cần can thiệp thủ công.

### What about Light Clients?

Một giải pháp thay thế cho optimistic sync là chạy một light client bên
trong/bên cạnh beacon node, giúp loại bỏ nhu cầu optimistic sync bằng cách cung
cấp các block ở đỉnh chain (tip-of-chain) cho execution engine. Tuy nhiên, light
client cũng có những độ phức tạp riêng. Việc phụ thuộc vào light client cũng có
thể hạn chế node sync từ genesis, nếu node muốn làm vậy.

Một điểm đáng chú ý của optimistic sync là nó *không bắt buộc*. Nếu một bản hiện
thực quyết định đi theo hướng light client, họ có thể bỏ qua hoàn toàn optimistic
sync.

### What if `TERMINAL_BLOCK_HASH` is used?

Nếu cơ chế ghi đè terminal block hash được sử dụng (tức là
`TERMINAL_BLOCK_HASH != Hash32()`), hàm
[`validate_merge_block`](./fork-choice.md#validate_merge_block) sẽ trả về `True`
hoặc `False` một cách tất định (deterministic). Mặc dù về *mặt kỹ thuật* không bắt
buộc phải gọi hồi tố
[`validate_merge_block`](./fork-choice.md#validate_merge_block) trên một
transition block khớp với `TERMINAL_BLOCK_HASH` sau khi optimistic sync, việc gọi
như vậy cũng không gây ảnh hưởng gì. Để đơn giản, đặc tả optimistic sync không
định nghĩa hành vi cho trường hợp biên khi `TERMINAL_BLOCK_HASH` được sử dụng.
