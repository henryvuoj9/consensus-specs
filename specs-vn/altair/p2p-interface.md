# Altair -- Networking

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Types](#types)
  - [New `Syncnets`](#new-syncnets)
- [Helpers](#helpers)
  - [Modified `Seen`](#modified-seen)
  - [Modified `compute_fork_version`](#modified-compute_fork_version)
  - [New `is_current_slot`](#new-is_current_slot)
  - [New `get_sync_subcommittee_pubkeys`](#new-get_sync_subcommittee_pubkeys)
- [MetaData](#metadata)
- [The gossip domain: gossipsub](#the-gossip-domain-gossipsub)
  - [Topics and messages](#topics-and-messages)
    - [Global topics](#global-topics)
      - [Modified `beacon_block`](#modified-beacon_block)
      - [New `sync_committee_contribution_and_proof`](#new-sync_committee_contribution_and_proof)
    - [Sync committee subnets](#sync-committee-subnets)
      - [New `sync_committee_{subnet_id}`](#new-sync_committee_subnet_id)
    - [Sync committees and aggregation](#sync-committees-and-aggregation)
  - [Transitioning the gossip](#transitioning-the-gossip)
- [The Req/Resp domain](#the-reqresp-domain)
  - [Req-Resp interaction](#req-resp-interaction)
    - [`ForkDigest`-context](#forkdigest-context)
  - [Messages](#messages)
    - [BeaconBlocksByRange v2](#beaconblocksbyrange-v2)
    - [BeaconBlocksByRoot v2](#beaconblocksbyroot-v2)
    - [GetMetaData v2](#getmetadata-v2)
  - [Transitioning from v1 to v2](#transitioning-from-v1-to-v2)
- [The discovery domain: discv5](#the-discovery-domain-discv5)
  - [ENR structure](#enr-structure)
    - [Sync committee bitfield](#sync-committee-bitfield)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả đặc tả mạng (networking) của consensus layer cho bản nâng cấp
Altair. Tài liệu này được xem là phần *bổ sung* cho
[tài liệu của Phase 0](../phase0/p2p-interface.md), từ đây về sau gọi tắt là
"tài liệu Phase 0". Người đọc nên nắm vững tài liệu Phase 0 và dùng nó làm nền
tảng để hiểu các thay đổi được nêu trong tài liệu này.

Altair bổ sung các message, topic và data mới cho các domain Req-Resp, Gossip và
Discovery. Một số tính năng của Phase 0 sẽ bị đánh dấu là lỗi thời (deprecated),
nhưng không bị loại bỏ ngay lập tức.

## Types

### New `Syncnets`

```python
class Syncnets(BitVector):
    """
    The sync committee subnets a node is subscribed to, one bit per subnet.
    """

    LENGTH = SYNC_COMMITTEE_SUBNET_COUNT
```

## Helpers

### Modified `Seen`

```python
@dataclass
class Seen:
    proposer_slots: set[tuple[Slot, ValidatorIndex]]
    aggregator_epochs: set[tuple[Epoch, ValidatorIndex]]
    aggregate_data_roots: dict[Root, set[tuple[bool, ...]]]
    voluntary_exit_indices: set[ValidatorIndex]
    proposer_slashing_indices: set[ValidatorIndex]
    attester_slashing_indices: set[ValidatorIndex]
    attestation_validator_epochs: set[tuple[Epoch, ValidatorIndex]]
    # [Mới trong Altair]
    sync_contribution_aggregator_slots: set[tuple[Slot, ValidatorIndex, Uint64]]
    # [Mới trong Altair]
    sync_contribution_data: dict[tuple[Slot, Root, Uint64], set[tuple[bool, ...]]]
    # [Mới trong Altair]
    sync_message_validator_slots: set[tuple[Slot, ValidatorIndex, Uint64]]
```

> 💡 Ghi chú: `Seen` là cấu trúc lưu lại những gì node đã thấy trên gossip, dùng
> để loại bỏ message trùng lặp. Altair thêm ba trường mới phục vụ các message của
> sync committee.

### Modified `compute_fork_version`

```python
def compute_fork_version(epoch: Epoch) -> Version:
    """
    Return the fork version at the given ``epoch``.
    """
    if epoch >= ALTAIR_FORK_EPOCH:
        return ALTAIR_FORK_VERSION
    return GENESIS_FORK_VERSION
```

### New `is_current_slot`

```python
def is_current_slot(
    store: Store,
    slot: Slot,
    current_time_ms: Uint64,
) -> bool:
    """
    Check if the given slot is the current slot
    (with MAXIMUM_GOSSIP_CLOCK_DISPARITY allowance).
    """
    return is_within_slot_range(store, slot, Uint64(0), current_time_ms)
```

### New `get_sync_subcommittee_pubkeys`

```python
def get_sync_subcommittee_pubkeys(
    state: BeaconState, subcommittee_index: Uint64
) -> Sequence[BLSPubkey]:
    # Các committee được giao cho `slot` sẽ ký cho `slot - 1`
    # Điều này tạo ra logic ngoại lệ bên dưới khi chuyển giao giữa các sync committee period
    next_slot_epoch = compute_epoch_at_slot(state.slot + 1)
    if compute_sync_committee_period(get_current_epoch(state)) == compute_sync_committee_period(
        next_slot_epoch
    ):
        sync_committee = state.current_sync_committee
    else:
        sync_committee = state.next_sync_committee

    # Trả về các pubkey của subcommittee có chỉ số tương ứng
    sync_subcommittee_size = SYNC_COMMITTEE_SIZE // SYNC_COMMITTEE_SUBNET_COUNT
    i = subcommittee_index * sync_subcommittee_size
    return sync_committee.pubkeys[i : i + sync_subcommittee_size]
```

> 💡 Ghi chú: Vì thành viên sync committee ở `slot` ký cho block root của
> `slot - 1`, tại slot cuối cùng của một sync committee period, message gửi ở
> slot kế tiếp sẽ thuộc về period mới. Do đó hàm này kiểm tra epoch của
> `state.slot + 1`: nếu nó vẫn nằm trong period hiện tại thì dùng
> `current_sync_committee`, ngược lại dùng `next_sync_committee`.

## MetaData

`MetaData` được client lưu cục bộ nay có thêm một trường để thông báo các sync
committee subnet mà node đang subscribe:

```
(
  seq_number: Uint64
  attnets: Attnets
  syncnets: Syncnets
)
```

Trong đó

- `seq_number` và `attnets` có cùng ý nghĩa như đã định nghĩa trong tài liệu
  Phase 0.
- `syncnets` là một `BitVector` biểu diễn các sync committee subnet mà node đang
  subscribe. Trường này cần phản ánh đúng dữ liệu trong ENR của node, như được mô
  tả trong [validator guide](./validator.md#sync-committee-subnet-stability).

## The gossip domain: gossipsub

Altair bổ sung các gossip mesh mới để phục vụ hoạt động đồng thuận của các sync
committee. Các validator sử dụng một cơ chế aggregation (gộp chữ ký) để cân bằng
tải xử lý và tải mạng giữa tất cả các bên liên quan.

### Topics and messages

Các topic tuân theo cùng đặc tả như trong tài liệu Phase 0. Altair thêm các topic
mới để hỗ trợ sync committee, và topic beacon block được cập nhật với kiểu dữ liệu
đã sửa đổi.

Các quy định về việc tạo, kiểm tra hợp lệ (validation) và lan truyền message
không thay đổi so với tài liệu Phase 0, trừ khi được ghi chú rõ ràng ở đây.

Cách tính `message-id` thay đổi kể từ Altair: nay nó bao gồm cả `topic` của
message bên cạnh `data` của message. Đây là các trường của Protobuf `Message`, và
được hiểu là chuỗi byte rỗng nếu bị thiếu. `message-id` MUST là giá trị 20 byte
sau đây, được tính từ message:

- Nếu `message.data` giải nén snappy thành công (hợp lệ), đặt `message-id` bằng
  20 byte đầu tiên của hash `SHA256` của chuỗi ghép nối các dữ liệu sau:
  `MESSAGE_DOMAIN_VALID_SNAPPY`, độ dài chuỗi byte của topic (mã hóa dưới dạng
  `Uint64` little-endian), chuỗi byte của topic, và data của message sau khi giải
  nén snappy; tức là
  `SHA256(MESSAGE_DOMAIN_VALID_SNAPPY + uint_to_bytes(Uint64(len(message.topic))) + message.topic + snappy_decompress(message.data))[:20]`.
- Ngược lại, đặt `message-id` bằng 20 byte đầu tiên của hash `SHA256` của chuỗi
  ghép nối các dữ liệu sau: `MESSAGE_DOMAIN_INVALID_SNAPPY`, độ dài chuỗi byte
  của topic (mã hóa dưới dạng `Uint64` little-endian), chuỗi byte của topic, và
  data thô (raw) của message; tức là
  `SHA256(MESSAGE_DOMAIN_INVALID_SNAPPY + uint_to_bytes(Uint64(len(message.topic))) + message.topic + message.data)[:20]`.

Các implementation cần xử lý cẩn thận hàm tính `message-id`. Cụ thể, message trên
các topic mang fork digest của Phase 0 nên dùng thủ tục tính `message-id` được
đặc tả trong tài liệu Phase 0. Message trên các topic mang fork digest của Altair
nên dùng thủ tục tính `message-id` được định nghĩa ở đây. Nếu một implementation
chỉ hỗ trợ một hàm `message-id` duy nhất, nó có thể rẽ nhánh ngay bên trong hàm;
ví dụ:
`if topic in phase0_topics: return phase0_msg_id_fn(message) else return altair_msg_id_fn(message)`.

> 💡 Ghi chú: Việc đưa `topic` vào `message-id` giúp cùng một nội dung nhưng được
> gửi trên các topic khác nhau (ví dụ topic của fork cũ và fork mới) sẽ có
> `message-id` khác nhau, tránh bị gossipsub coi nhầm là trùng lặp.

Các topic mới cùng với kiểu của trường `data` trong gossipsub message được liệt kê
trong bảng sau:

| Name                                    | Message Type                   |
| --------------------------------------- | ------------------------------ |
| `beacon_block`                          | `SignedBeaconBlock` (modified) |
| `sync_committee_contribution_and_proof` | `SignedContributionAndProof`   |
| `sync_committee_{subnet_id}`            | `SyncCommitteeMessage`         |

Định nghĩa của các kiểu mới này có trong
[Altair validator guide](./validator.md#containers).

Lưu ý rằng phân đoạn `ForkDigestValue` trong đường dẫn topic chính là thứ phân
biệt topic `beacon_block` cũ và mới.

#### Global topics

Altair thay đổi kiểu dữ liệu của global topic beacon block và thêm một global
topic để lan truyền các sync committee message đã được aggregate một phần tới tất
cả các proposer tiềm năng của beacon block.

##### Modified `beacon_block`

Đặc tả hiện có cho topic này không thay đổi so với tài liệu Phase 0, nhưng kiểu
của payload đổi thành `SignedBeaconBlock` (đã sửa đổi). Kiểu này thay đổi vì nó
chứa bên trong `BeaconBlockBody`, vốn đã được sửa đổi trong Altair.

Xem [tài liệu state transition](./beacon-chain.md#beaconblockbody) của Altair để
biết thêm chi tiết.

##### New `sync_committee_contribution_and_proof`

Topic này dùng để lan truyền các sync committee message đã được aggregate một
phần, nhằm đưa vào các block trong tương lai.

> 💡 Ghi chú: Hàm dưới đây mô tả các điều kiện kiểm tra hợp lệ (gossip
> validation). `[IGNORE]` nghĩa là bỏ qua message (không lan truyền tiếp nhưng
> không phạt peer); `[REJECT]` nghĩa là từ chối message và peer gửi nó có thể bị
> trừ điểm.

```python
def validate_sync_committee_contribution_and_proof_gossip(
    seen: Seen,
    store: Store,
    signed_contribution_and_proof: SignedContributionAndProof,
    current_time_ms: Uint64,
) -> None:
    """
    Validate a SignedContributionAndProof for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    contribution_and_proof = signed_contribution_and_proof.message
    contribution = contribution_and_proof.contribution

    # [IGNORE] Chưa từng thấy một sync committee contribution hợp lệ nào có cùng slot,
    # beacon_block_root và subcommittee_index mà aggregation_bits của nó là tập cha
    # (không nghiêm ngặt) của aggregation_bits của contribution này
    contribution_key = (
        contribution.slot,
        contribution.beacon_block_root,
        contribution.subcommittee_index,
    )
    contribution_bits = tuple(bool(bit) for bit in contribution.aggregation_bits)
    seen_bits = seen.sync_contribution_data.get(contribution_key, set())
    if is_non_strict_superset(seen_bits, contribution_bits):
        raise GossipIgnore("already seen contribution for this data")

    # [IGNORE] Sync committee contribution này là contribution hợp lệ đầu tiên nhận được
    # cho slot contribution.slot, aggregator có chỉ số contribution_and_proof.aggregator_index,
    # và subcommittee có chỉ số contribution.subcommittee_index
    aggregator_key = (
        contribution.slot,
        contribution_and_proof.aggregator_index,
        contribution.subcommittee_index,
    )
    if aggregator_key in seen.sync_contribution_aggregator_slots:
        raise GossipIgnore("already seen contribution from this aggregator")

    # [IGNORE] Slot của contribution là slot hiện tại
    if not is_current_slot(store, contribution.slot, current_time_ms):
        raise GossipIgnore("contribution is not for the current slot")

    # [REJECT] Chỉ số subcommittee nằm trong khoảng cho phép
    if contribution.subcommittee_index >= SYNC_COMMITTEE_SUBNET_COUNT:
        raise GossipReject("subcommittee index out of range")

    # [REJECT] Contribution có ít nhất một người tham gia
    if not any(contribution.aggregation_bits):
        raise GossipReject("contribution has no participants")

    # [REJECT] selection_proof chọn validator này làm aggregator cho slot
    if not is_sync_committee_aggregator(contribution_and_proof.selection_proof):
        raise GossipReject("validator is not selected as aggregator")

    state = store.block_states[get_head(store).root]

    # [REJECT] Chỉ số aggregator hợp lệ
    if contribution_and_proof.aggregator_index >= len(state.validators):
        raise GossipReject("aggregator index out of range")

    # [REJECT] Aggregator là thành viên của committee (subcommittee tương ứng)
    aggregator_pubkey = state.validators[contribution_and_proof.aggregator_index].pubkey
    subcommittee_pubkeys = get_sync_subcommittee_pubkeys(state, contribution.subcommittee_index)
    if aggregator_pubkey not in subcommittee_pubkeys:
        raise GossipReject("aggregator is not a member of the committee")

    # [REJECT] contribution_and_proof.selection_proof là chữ ký hợp lệ
    # trên SyncAggregatorSelectionData (suy ra từ contribution)
    # của validator có chỉ số contribution_and_proof.aggregator_index
    selection_data = SyncAggregatorSelectionData(
        slot=contribution.slot,
        subcommittee_index=contribution.subcommittee_index,
    )
    domain = get_domain(
        state, DOMAIN_SYNC_COMMITTEE_SELECTION_PROOF, compute_epoch_at_slot(contribution.slot)
    )
    signing_root = compute_signing_root(selection_data, domain)
    if not bls.Verify(aggregator_pubkey, signing_root, contribution_and_proof.selection_proof):
        raise GossipReject("invalid selection proof signature")

    # [REJECT] Chữ ký của aggregator, signed_contribution_and_proof.signature, hợp lệ
    domain = get_domain(
        state, DOMAIN_CONTRIBUTION_AND_PROOF, compute_epoch_at_slot(contribution.slot)
    )
    signing_root = compute_signing_root(contribution_and_proof, domain)
    if not bls.Verify(aggregator_pubkey, signing_root, signed_contribution_and_proof.signature):
        raise GossipReject("invalid aggregator signature")

    # [REJECT] Aggregate signature hợp lệ đối với message beacon_block_root
    # và aggregate pubkey được suy ra từ thông tin tham gia trong aggregation_bits
    # của subcommittee được chỉ định bởi contribution.subcommittee_index
    participant_pubkeys = [
        subcommittee_pubkeys[index]
        for index, bit in enumerate(contribution.aggregation_bits)
        if bit
    ]
    domain = get_domain(state, DOMAIN_SYNC_COMMITTEE, compute_epoch_at_slot(contribution.slot))
    signing_root = compute_signing_root(contribution.beacon_block_root, domain)
    if not eth_fast_aggregate_verify(participant_pubkeys, signing_root, contribution.signature):
        raise GossipReject("invalid aggregate signature")

    # Đánh dấu contribution này là đã thấy
    seen.sync_contribution_aggregator_slots.add(aggregator_key)
    if contribution_key not in seen.sync_contribution_data:
        seen.sync_contribution_data[contribution_key] = set()
    seen.sync_contribution_data[contribution_key].add(contribution_bits)
```

#### Sync committee subnets

Các sync committee subnet được dùng để lan truyền các sync committee message
chưa được aggregate tới từng phân vùng nhỏ của mạng.

##### New `sync_committee_{subnet_id}`

Các topic `sync_committee_{subnet_id}` được dùng để lan truyền các sync committee
message chưa aggregate tới subnet `subnet_id`, để chúng được aggregate trước khi
được gossip lên global topic `sync_committee_contribution_and_proof`.

```python
def validate_sync_committee_message_gossip(
    seen: Seen,
    store: Store,
    sync_committee_message: SyncCommitteeMessage,
    current_time_ms: Uint64,
    subnet_id: SubnetID,
) -> None:
    """
    Validate a SyncCommitteeMessage for gossip propagation on a subnet.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    # [IGNORE] Chưa có sync committee message hợp lệ nào khác cho slot đã khai báo
    # từ validator được tham chiếu bởi sync_committee_message.validator_index
    # (việc kiểm tra này thực hiện theo từng topic, nên trong cùng một slot, nhiều message
    # có cùng validator_index vẫn có thể được chuyển tiếp miễn là subnet_id khác nhau)
    message_key = (sync_committee_message.slot, sync_committee_message.validator_index, subnet_id)
    if message_key in seen.sync_message_validator_slots:
        raise GossipIgnore("already seen message from this validator for this slot and subnet")

    # [IGNORE] Slot của message là slot hiện tại
    if not is_current_slot(store, sync_committee_message.slot, current_time_ms):
        raise GossipIgnore("message is not for the current slot")

    state = store.block_states[get_head(store).root]

    # [REJECT] Chỉ số validator hợp lệ
    if sync_committee_message.validator_index >= len(state.validators):
        raise GossipReject("validator index out of range")

    # [REJECT] subnet_id hợp lệ đối với validator này
    # (điều này ngụ ý validator là thành viên của sync committee hiện tại
    # và thuộc đúng subcommittee tương ứng)
    valid_subnets = compute_subnets_for_sync_committee(
        state, sync_committee_message.validator_index
    )
    if subnet_id not in valid_subnets:
        raise GossipReject("subnet_id is not valid for the validator")

    # [REJECT] Chữ ký hợp lệ
    validator = state.validators[sync_committee_message.validator_index]
    domain = get_domain(
        state, DOMAIN_SYNC_COMMITTEE, compute_epoch_at_slot(sync_committee_message.slot)
    )
    signing_root = compute_signing_root(sync_committee_message.beacon_block_root, domain)
    if not bls.Verify(validator.pubkey, signing_root, sync_committee_message.signature):
        raise GossipReject("invalid sync committee message signature")

    # Đánh dấu message này là đã thấy
    seen.sync_message_validator_slots.add(message_key)
```

> 💡 Ghi chú: Một validator có thể xuất hiện nhiều lần trong sync committee (xem
> mục bên dưới), nên nó có thể hợp lệ trên nhiều subnet cùng lúc. Vì vậy khóa
> chống trùng lặp bao gồm cả `subnet_id`.

#### Sync committees and aggregation

Cơ chế aggregation bám sát thiết kế của cơ chế aggregation cho attestation. Các
sync committee message được broadcast vào các "subnet" được xác định bởi topic.
Số lượng subnet được định nghĩa bởi `SYNC_COMMITTEE_SUBNET_COUNT` trong
[Altair validator guide](./validator.md#constants). Các thành viên sync committee
được chia thành các "subcommittee" (committee con), mỗi subcommittee được gán vào
một subnet trong suốt nhiệm kỳ của sync committee đó. Một validator có thể bị lặp
lại trong sync committee tổng thể, tức là nó có thể xuất hiện nhiều lần trong
cùng một subcommittee hoặc trong nhiều subcommittee khác nhau.

Các message chưa aggregate (kèm metadata) được gửi dưới dạng
`SyncCommitteeMessage` trên các topic `sync_committee_{subnet_id}`.

Các sync committee message đã aggregate được đóng gói thành
`SyncCommitteeContribution` (có chữ ký) kèm theo các proof, rồi được gossip lên
topic `sync_committee_contribution_and_proof`.

### Transitioning the gossip

Với mỗi fork, fork version thay đổi, và do đó `ForkDigestValue` cũng thay đổi.
Mỗi topic chỉ gắn với một kiểu message duy nhất, nên để chuyển tiếp suôn sẻ, node
phải tạm thời subscribe cả topic cũ và topic mới.

Các topic không bị loại bỏ trong fork sẽ được cập nhật với `ForkDigestValue` mới.
Trước thời điểm fork, node SHOULD subscribe vào các biến thể sau-fork (post-fork)
của các topic.

Các subscription này được kỳ vọng sẽ được các peer đón nhận tốt, vì tất cả các
node đã cập nhật cũng sẽ subscribe tương tự. Các topic-mesh có thể được graft
(ghép) nhanh chóng vì các node vốn đã kết nối với nhau và đang trao đổi các
gossip control message.

Message SHOULD NOT được broadcast lại từ fork này sang fork kia. Hành vi của node
trước và sau fork như sau:

Trước fork (pre-fork):

- Các peer lan truyền message trên các topic post-fork MAY bị chấm điểm âm, tỷ lệ
  với khoảng thời gian còn lại đến fork, để tính đến sai lệch đồng hồ.
- Message trên các topic post-fork có thể bị IGNORE, với biên độ
  `MAXIMUM_GOSSIP_CLOCK_DISPARITY`.

Sau fork (post-fork):

- Các peer lan truyền message trên các topic pre-fork MUST NOT bị chấm điểm âm.
  (Lý do: các IWANT đến trễ có thể buộc họ phải làm vậy.)
- Message trên biến thể pre-fork và post-fork của cùng một topic dùng chung các
  cache ở tầng ứng dụng. Ví dụ: một attestation xuất hiện trên cả topic cũ lẫn
  topic mới sẽ bị bỏ qua như mọi message trùng lặp khác.
- Hai epoch sau fork, node SHOULD hủy subscribe khỏi các topic pre-fork. Thời
  điểm này đã trễ hơn nhiều so với `seen_ttl` được cấu hình.

## The Req/Resp domain

### Req-Resp interaction

Một trường bổ sung `<context-bytes>` được đưa vào `response_chunk` như đã định
nghĩa trong tài liệu Phase 0:

```
response_chunk  ::= <result> | <context-bytes> | <encoding-dependent-header> | <encoded-payload>
```

Tất cả các method của Phase 0 vẫn tương thích: mặc định `<context-bytes>` là rỗng.
Khi `<result>` khác 0 với payload là `ErrorMessage`, `<context-bytes>` cũng rỗng.

Trong Altair và các fork sau, `<context-bytes>` đóng vai trò như một đoạn
meta-data ngắn, được định nghĩa riêng cho từng req-resp method, và có thể dùng để
tham số hóa bộ giải mã (decoder) payload.

#### `ForkDigest`-context

Kể từ Altair và trong các fork tương lai, định nghĩa kiểu SSZ có thể thay đổi. Cho
trường hợp phổ biến này, ta định nghĩa `ForkDigest`-context:

Một `<context-bytes>` có độ dài cố định 4 byte, được đặt bằng `ForkDigest` tương
ứng với chunk: `compute_fork_digest(genesis_validators_root, epoch)`.

> 💡 Ghi chú: Nhờ 4 byte này, bên nhận biết được chunk thuộc fork nào và do đó
> chọn đúng kiểu SSZ để giải mã.

### Messages

#### BeaconBlocksByRange v2

**Protocol ID:** `/eth2/beacon_chain/req/beacon_blocks_by_range/2/`

Request và Response giữ nguyên. Một `ForkDigest`-context được dùng để chọn
namespace của fork cho kiểu Response.

Với mỗi `response_chunk` thành công, epoch dùng cho `ForkDigest` context được xác
định bởi `compute_epoch_at_slot(signed_beacon_block.message.slot)`.

Tương ứng với `fork_version = compute_fork_version(epoch)`:

<!-- eth_consensus_specs: skip -->

| `fork_version`         | Chunk SSZ type             |
| ---------------------- | -------------------------- |
| `GENESIS_FORK_VERSION` | `phase0.SignedBeaconBlock` |
| `ALTAIR_FORK_VERSION`  | `altair.SignedBeaconBlock` |

#### BeaconBlocksByRoot v2

**Protocol ID:** `/eth2/beacon_chain/req/beacon_blocks_by_root/2/`

Request và Response giữ nguyên. Một `ForkDigest`-context được dùng để chọn
namespace của fork cho kiểu Response.

Với mỗi `response_chunk` thành công, epoch dùng cho `ForkDigest` context được xác
định bởi `compute_epoch_at_slot(signed_beacon_block.message.slot)`.

Tương ứng với `fork_version = compute_fork_version(epoch)`:

<!-- eth_consensus_specs: skip -->

| `fork_version`         | Chunk SSZ type             |
| ---------------------- | -------------------------- |
| `GENESIS_FORK_VERSION` | `phase0.SignedBeaconBlock` |
| `ALTAIR_FORK_VERSION`  | `altair.SignedBeaconBlock` |

#### GetMetaData v2

**Protocol ID:** `/eth2/beacon_chain/req/metadata/2/`

Không có nội dung Request.

Nội dung Response:

```
(
  MetaData
)
```

Yêu cầu MetaData của một peer, sử dụng định nghĩa `MetaData` mới ở trên (được mở
rộng từ phase 0 trong Altair). Các điều kiện khác của giao thức `GetMetaData`
không thay đổi so với tài liệu p2p networking của phase 0.

### Transitioning from v1 to v2

Trước thời điểm fork, các implementation có thể chọn chạy song song cả v1 và v2 để
chuyển tiếp suôn sẻ. Việc này không gây phá vỡ tương thích (non-breaking), và
được khuyến nghị thực hiện ngay khi đặc tả của fork đã ổn định.

Các biến thể v1 sẽ bị deprecated, và các implementation nên dùng v2 khi có thể
(dựa trên kết quả thương lượng với peer qua LibP2P multistream-select).

Method v1 MAY bị hủy đăng ký tại ranh giới fork. Nếu nhận được request qua v1 cho
một payload đặc thù của Altair, bên trả lời MUST trả về response code
**InvalidRequest**.

## The discovery domain: discv5

### ENR structure

#### Sync committee bitfield

Một bitfield bổ sung được thêm vào ENR dưới key `syncnets` để hỗ trợ discovery các
sync committee subnet. Độ dài bitfield này là `SYNC_COMMITTEE_SUBNET_COUNT`, trong
đó mỗi bit tương ứng với một `subnet_id` riêng biệt của một sync committee subnet.
Bit thứ `i` được bật trong bitfield nếu validator hiện đang subscribe topic
`sync_committee_{i}`.

| Key        | Value      |
| ---------- | ---------- |
| `syncnets` | `Syncnets` |

Xem [tài liệu validator](./validator.md#sync-committee-subnet-stability) để biết
thêm chi tiết về cách sử dụng các bit mới này.
