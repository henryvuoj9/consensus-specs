# Phase 0 -- Honest Validator

Đây là tài liệu đi kèm với
[Phase 0 -- The Beacon Chain](./beacon-chain.md), mô tả các hành động mà một
"validator" tham gia vào giao thức proof-of-stake của Ethereum được kỳ vọng sẽ
thực hiện.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Constants](#constants)
  - [Misc](#misc)
- [Configs](#configs)
  - [Time parameters](#time-parameters)
- [Containers](#containers)
  - [`Eth1Block`](#eth1block)
  - [`AggregateAndProof`](#aggregateandproof)
  - [`SignedAggregateAndProof`](#signedaggregateandproof)
- [Becoming a validator](#becoming-a-validator)
  - [Initialization](#initialization)
    - [BLS public key](#bls-public-key)
    - [Withdrawal credentials](#withdrawal-credentials)
      - [`BLS_WITHDRAWAL_PREFIX`](#bls_withdrawal_prefix)
      - [`ETH1_ADDRESS_WITHDRAWAL_PREFIX`](#eth1_address_withdrawal_prefix)
  - [Submit deposit](#submit-deposit)
  - [Process deposit](#process-deposit)
  - [Validator index](#validator-index)
  - [Activation](#activation)
- [Validator assignments](#validator-assignments)
  - [Lookahead](#lookahead)
- [Beacon chain responsibilities](#beacon-chain-responsibilities)
  - [Block proposal](#block-proposal)
    - [Preparing for a `BeaconBlock`](#preparing-for-a-beaconblock)
      - [Slot](#slot)
      - [Proposer index](#proposer-index)
      - [Parent root](#parent-root)
    - [Constructing the `BeaconBlockBody`](#constructing-the-beaconblockbody)
      - [Randao reveal](#randao-reveal)
      - [Eth1 Data](#eth1-data)
        - [`get_eth1_data`](#get_eth1_data)
      - [Proposer slashings](#proposer-slashings)
      - [Attester slashings](#attester-slashings)
      - [Attestations](#attestations)
      - [Deposits](#deposits)
      - [Voluntary exits](#voluntary-exits)
    - [Packaging into a `SignedBeaconBlock`](#packaging-into-a-signedbeaconblock)
      - [State root](#state-root)
      - [Signature](#signature)
  - [Attesting](#attesting)
    - [Attestation data](#attestation-data)
      - [General](#general)
      - [LMD GHOST vote](#lmd-ghost-vote)
      - [FFG vote](#ffg-vote)
    - [Construct attestation](#construct-attestation)
      - [Data](#data)
      - [Aggregation bits](#aggregation-bits)
      - [Aggregate signature](#aggregate-signature)
    - [Broadcast attestation](#broadcast-attestation)
  - [Attestation aggregation](#attestation-aggregation)
    - [Aggregation selection](#aggregation-selection)
    - [Construct aggregate](#construct-aggregate)
      - [Data](#data-1)
      - [Aggregation bits](#aggregation-bits-1)
      - [Aggregate signature](#aggregate-signature-1)
    - [Broadcast aggregate](#broadcast-aggregate)
- [How to avoid slashing](#how-to-avoid-slashing)
  - [Proposer slashing](#proposer-slashing)
  - [Attester slashing](#attester-slashing)
- [Protection best practices](#protection-best-practices)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả hành vi được kỳ vọng của một "validator trung thực" (honest
validator) đối với Phase 0 của giao thức proof-of-stake Ethereum. Tài liệu không
phân biệt giữa "node" (tức phần chức năng theo dõi và đọc beacon chain) và
"validator client" (tức phần chức năng chủ động tham gia đồng thuận). Việc tách
hai phần này thành (có thể là) hai phần mềm riêng biệt là một quyết định thiết kế
nằm ngoài phạm vi tài liệu.

Validator là một thực thể tham gia vào cơ chế đồng thuận của giao thức
proof-of-stake Ethereum. Đây là vai trò tùy chọn: người dùng đặt cọc ETH làm tài
sản thế chấp, rồi kiểm tra và attest (xác nhận) tính hợp lệ của các block để nhận
lợi nhuận, đổi lại việc họ góp phần xây dựng và bảo vệ giao thức. Điều này tương tự
các mạng proof-of-work, nơi thợ đào bỏ ra tài sản thế chấp dưới dạng phần
cứng/hash-power để nhận lợi nhuận khi xây dựng và bảo vệ giao thức.

## Prerequisites

Toàn bộ thuật ngữ, hằng số, hàm và cơ chế giao thức được định nghĩa trong các spec
[Phase 0 -- The Beacon Chain](./beacon-chain.md) và
[Phase 0 -- Deposit Contract](./deposit-contract.md) là kiến thức bắt buộc cho tài
liệu này và được dùng xuyên suốt. Hãy đọc các spec Phase 0 đó trước khi tiếp tục và
dùng chúng làm tài liệu tham chiếu trong suốt quá trình đọc.

## Constants

### Misc

| Name                               | Value                 |
| ---------------------------------- | --------------------- |
| `TARGET_AGGREGATORS_PER_COMMITTEE` | `Uint64(2**4)` (= 16) |

## Configs

### Time parameters

| Name                  | Value          | Duration                         |
| --------------------- | -------------- | -------------------------------- |
| `ATTESTATION_DUE_BPS` | `Uint64(3333)` | ~33% của `SLOT_DURATION_MS`      |
| `AGGREGATE_DUE_BPS`   | `Uint64(6667)` | ~67% của `SLOT_DURATION_MS`      |

> 💡 Ghi chú: "BPS" là basis points (1/10000). Ví dụ `3333` BPS nghĩa là mốc thời
> gian bằng khoảng 33,33% độ dài một slot, tính từ đầu slot.

## Containers

### `Eth1Block`

```python
class Eth1Block(Container):
    timestamp: Uint64
    deposit_root: Root
    deposit_count: Uint64
    # All other eth1 block fields
```

### `AggregateAndProof`

```python
class AggregateAndProof(Container):
    aggregator_index: ValidatorIndex
    aggregate: Attestation
    selection_proof: BLSSignature
```

### `SignedAggregateAndProof`

```python
class SignedAggregateAndProof(Container):
    message: AggregateAndProof
    signature: BLSSignature
```

## Becoming a validator

### Initialization

Validator phải khởi tạo nhiều tham số ở local trước khi gửi deposit và gia nhập
validator registry (danh sách validator trong state).

#### BLS public key

Public key của validator là các [điểm G1](beacon-chain.md#bls-signatures) trên
[đường cong BLS12-381](https://z.cash/blog/new-snark-curve). Private key
`privkey` phải được sinh một cách an toàn, cùng với `pubkey` tương ứng. `privkey`
này phải ở trạng thái "hot", tức là luôn sẵn sàng để ký data trong suốt vòng đời
của validator.

#### Withdrawal credentials

Trường `withdrawal_credentials` quy định ràng buộc cho việc withdrawal của
validator. Byte đầu tiên của trường 32 byte này là withdrawal prefix, xác định ý
nghĩa của 31 byte còn lại.

Hiện tại hỗ trợ các withdrawal prefix sau.

##### `BLS_WITHDRAWAL_PREFIX`

Withdrawal credentials dùng BLS withdrawal prefix cho phép một cặp khóa BLS
`(bls_withdrawal_privkey, bls_withdrawal_pubkey)` kích hoạt withdrawal. Trường
`withdrawal_credentials` phải thỏa mãn:

- `withdrawal_credentials[:1] == BLS_WITHDRAWAL_PREFIX`
- `withdrawal_credentials[1:] == sha256(bls_withdrawal_pubkey)[1:]`

*Lưu ý*: `bls_withdrawal_privkey` không cần thiết cho việc validate và có thể được
cất trong cold storage (lưu trữ ngoại tuyến).

##### `ETH1_ADDRESS_WITHDRAWAL_PREFIX`

Withdrawal credentials dùng Eth1 address withdrawal prefix chỉ định một địa chỉ
Eth1 20 byte `eth1_withdrawal_address` làm nơi nhận toàn bộ các khoản withdrawal.
`eth1_withdrawal_address` có thể là địa chỉ của một tài khoản externally owned
account (EOA) hoặc của một contract.

Trường `withdrawal_credentials` phải thỏa mãn:

- `withdrawal_credentials[:1] == ETH1_ADDRESS_WITHDRAWAL_PREFIX`
- `withdrawal_credentials[1:12] == b'\x00' * 11`
- `withdrawal_credentials[12:] == eth1_withdrawal_address`

Sau khi execution layer hiện tại của Ethereum được hợp nhất (the merge) vào beacon
chain, các khoản withdrawal về `eth1_withdrawal_address` chỉ đơn giản là tăng
balance ETH của tài khoản đó, và **KHÔNG** kích hoạt bất kỳ việc thực thi EVM nào.

> 💡 Ghi chú: Nói cách khác, nếu `eth1_withdrawal_address` là một contract thì
> code của contract (ví dụ hàm `receive`/`fallback`) sẽ không được gọi khi nhận
> tiền withdrawal.

### Submit deposit

Trong Phase 0, mọi deposit của validator đều đến từ chuỗi proof-of-work Ethereum
được xác định bởi `DEPOSIT_CHAIN_ID` và `DEPOSIT_NETWORK_ID`. Deposit được gửi tới
[deposit contract](./deposit-contract.md) đặt tại `DEPOSIT_CONTRACT_ADDRESS`.

Để gửi một deposit:

- Đóng gói các [tham số khởi tạo](#initialization) của validator vào
  `deposit_data`, là một object SSZ kiểu [`DepositData`](./beacon-chain.md#depositdata).
- Gọi `amount` là số Gwei mà validator sẽ deposit, với
  `amount >= MIN_DEPOSIT_AMOUNT`.
- Gán `deposit_data.pubkey` bằng `pubkey` của validator.
- Gán `deposit_data.withdrawal_credentials` bằng `withdrawal_credentials`.
- Gán `deposit_data.amount` bằng `amount`.
- Gọi `deposit_message` là một `DepositMessage` chứa toàn bộ nội dung của
  `DepositData` ngoại trừ `signature`.
- Gọi `signature` là kết quả của `bls.Sign` trên
  `compute_signing_root(deposit_message, domain)` với
  `domain=compute_domain(DOMAIN_DEPOSIT)`. (_Cảnh báo_: Deposit _bắt buộc_ phải
  được ký với `GENESIS_FORK_VERSION`; gọi `compute_domain` mà không truyền tham số
  thứ hai sẽ mặc định dùng đúng version này).
- Gọi `deposit_data_root` là `hash_tree_root(deposit_data)`.
- Gửi một transaction trên chuỗi proof-of-work Ethereum tới
  `DEPOSIT_CONTRACT_ADDRESS`, thực thi
  `def deposit(pubkey: bytes[48], withdrawal_credentials: bytes[32], signature: bytes[96], deposit_data_root: bytes32)`
  kèm theo khoản deposit `amount` Gwei.

*Lưu ý*: Các deposit cho cùng một `pubkey` được coi là của cùng một validator. Chỉ
một `Validator` duy nhất được thêm vào `state.validators`, và mỗi khoản deposit bổ
sung sẽ được cộng vào balance của validator đó. Validator chỉ có thể được kích hoạt
khi tổng deposit cho pubkey của nó đạt hoặc vượt `MAX_EFFECTIVE_BALANCE`.

### Process deposit

Deposit chưa thể được xử lý vào beacon chain cho đến khi block proof-of-work chứa
deposit đó (hoặc một block hậu duệ bất kỳ của nó) được đưa vào `state.eth1_data`
của beacon chain. Việc này mất _tối thiểu_ `ETH1_FOLLOW_DISTANCE` block Eth1 cộng
thêm `EPOCHS_PER_ETH1_VOTING_PERIOD` epoch. Khi data của block proof-of-work cần
thiết đã được thêm vào, deposit thường sẽ được đưa vào một block của beacon chain
và được xử lý vào `state.validators` trong vòng một hoặc hai epoch. Sau đó
validator sẽ nằm trong hàng đợi chờ được kích hoạt.

### Validator index

Khi validator đã được xử lý và thêm vào `validators` của beacon state,
`validator_index` của validator được xác định là chỉ số (index) trong registry tại
đó [`ValidatorRecord`](./beacon-chain.md#validator) chứa `pubkey` đã khai báo trong
deposit của validator. `validator_index` được đảm bảo không thay đổi kể từ lúc
deposit ban đầu cho tới khi validator exit và withdraw hoàn toàn. `validator_index`
này được dùng xuyên suốt spec để xác định vai trò và trách nhiệm của validator tại
mọi thời điểm, và nên được lưu lại ở local.

### Activation

Trong điều kiện hoạt động bình thường, validator sẽ được kích hoạt nhanh chóng; khi
đó validator được đưa vào shuffling và bắt đầu thực hiện nhiệm vụ validate sau thêm
`MAX_SEED_LOOKAHEAD` epoch.

Hàm [`is_active_validator`](./beacon-chain.md#is_active_validator) có thể được dùng
để kiểm tra validator có đang active trong một epoch nhất định hay không. Cách dùng
như sau:

```python
def check_if_validator_active(state: BeaconState, validator_index: ValidatorIndex) -> bool:
    validator = state.validators[validator_index]
    return is_active_validator(validator, get_current_epoch(state))
```

Khi validator đã được kích hoạt, validator sẽ được giao các
[trách nhiệm](#beacon-chain-responsibilities) cho tới khi exit.

*Lưu ý*: Có giới hạn tối đa về validator churn (số validator được vào/ra) trên mỗi
epoch được finalized, vì vậy thời gian chờ đến lúc kích hoạt là không cố định, phụ
thuộc vào finality, tổng balance của các validator đang active, và số lượng
validator đang xếp hàng chờ kích hoạt.

## Validator assignments

Validator có thể lấy committee assignment (phân công vào committee) cho một epoch
cho trước bằng hàm hỗ trợ dưới đây, thông qua
`get_committee_assignment(state, epoch, validator_index)` với `epoch <= next_epoch`.

```python
def get_committee_assignment(
    state: BeaconState, epoch: Epoch, validator_index: ValidatorIndex
) -> tuple[Sequence[ValidatorIndex], CommitteeIndex, Slot] | None:
    """
    Return the committee assignment in the ``epoch`` for ``validator_index``.
    ``assignment`` returned is a tuple of the following form:
        * ``assignment[0]`` is the list of validators in the committee
        * ``assignment[1]`` is the index to which the committee is assigned
        * ``assignment[2]`` is the slot at which the committee is assigned
    Return None if no assignment.
    """
    next_epoch = get_current_epoch(state) + 1
    assert epoch <= next_epoch

    start_slot = compute_start_slot_at_epoch(epoch)
    committee_count_per_slot = get_committee_count_per_slot(state, epoch)
    for slot in range(start_slot, start_slot + SLOTS_PER_EPOCH):
        for index in range(committee_count_per_slot):
            committee = get_beacon_committee(state, Slot(slot), CommitteeIndex(index))
            if validator_index in committee:
                return committee, CommitteeIndex(index), Slot(slot)
    return None
```

> 💡 Ghi chú: Hàm trả về một tuple gồm: (0) danh sách validator trong committee,
> (1) index của committee, (2) slot mà committee được phân công. Trả về `None` nếu
> validator không có assignment nào trong epoch đó.

Validator có thể dùng hàm sau để kiểm tra mình có phải propose block trong một slot
hay không. Hàm này chỉ chạy được với `state` của chính slot đang xét. Việc chọn
proposer chỉ ổn định (không đổi) trong phạm vi epoch hiện tại.

```python
def is_proposer(state: BeaconState, validator_index: ValidatorIndex) -> bool:
    return get_beacon_proposer_index(state) == validator_index
```

*Lưu ý*: Để biết validator có được phân công propose trong slot hay không, beacon
state phải đang ở trong epoch cần kiểm tra. Tại ranh giới epoch, validator phải
chạy epoch transition sang epoch mới thì mới kiểm tra đúng được proposal assignment
của slot đầu tiên.

*Lưu ý*: Việc propose `BeaconBlock` tách biệt với beacon committee assignment, và
trong một epoch, mỗi trách nhiệm có thể rơi vào một slot khác nhau.

### Lookahead

Shuffling của beacon chain được thiết kế để cung cấp tối thiểu 1 epoch lookahead
(biết trước) về các committee assignment sắp tới của validator cho việc attest, được
xác định bởi shuffling và slot. Lưu ý rằng lookahead này không áp dụng cho việc
propose — việc propose phải được kiểm tra trong chính epoch đang xét.

Nên gọi `get_committee_assignment` vào đầu mỗi epoch để lấy assignment cho epoch kế
tiếp (`current_epoch + 1`). Validator nên chuẩn bị trước cho các assignment trong
tương lai bằng cách ghi nhận slot attestation được giao và tham gia attestation
subnet tương ứng với committee index trong assignment của mình.

Cụ thể, validator nên:

- Gọi
  `_, committee_index, _ = get_committee_assignment(state, next_epoch, validator_index)`
  khi kiểm tra assignment cho epoch kế tiếp.
- Tính số committee mỗi slot cho epoch kế tiếp:
  `committees_per_slot = get_committee_count_per_slot(state, next_epoch)`
- Tính subnet index:
  `subnet_id = compute_subnet_for_attestation(committees_per_slot, slot, committee_index)`
- Tìm các peer của pubsub topic `beacon_attestation_{subnet_id}`.
  - Nếu số lượng peer hiện tại đang subscribe topic này là _không đủ_, validator
    phải discover thêm peer mới trên topic này. Thông qua giao thức discovery, tìm
    các peer có ENR chứa mục `attnets` sao cho
    `ENR["attnets"][subnet_id] == True`. Sau đó xác minh rằng các peer đó vẫn còn
    duy trì trên topic mong muốn bằng cách gửi request `GetMetaData` và kiểm tra
    trường `attnets` trong kết quả trả về.
  - Nếu validator được phân công làm aggregator cho slot đó (xem
    `is_aggregator()`), thì subscribe topic này.

*Lưu ý*: Nếu validator _không_ được phân công làm aggregator, validator chỉ cần đủ
số peer trên topic để có thể publish message. Validator không cần _subscribe_ và
lắng nghe tất cả message trên topic.

## Beacon chain responsibilities

Validator có hai trách nhiệm chính đối với beacon chain:
[propose block](#block-proposal) và [tạo attestation](#attesting). Việc propose diễn
ra không thường xuyên, trong khi attestation nên được tạo mỗi epoch một lần.

### Block proposal

Validator được kỳ vọng sẽ propose một
[`SignedBeaconBlock`](./beacon-chain.md#signedbeaconblock) vào đầu bất kỳ `slot`
nào mà `is_proposer(state, validator_index)` trả về `True`.

Để propose, validator chọn một `BeaconBlock` làm `parent` theo quy trình sau:

1. Tính head theo góc nhìn của fork choice tại thời điểm bắt đầu `slot`, sau khi đã
   chạy `on_tick` và áp dụng mọi attestation đang chờ từ `slot - 1`. Gán
   `head_node = get_head(store)`.
2. Tính _proposer head_, là head mà proposer SHOULD (nên) xây block lên trên, nhằm
   khuyến khích các validator khác lan truyền block đúng hạn. Gán
   `parent_node = get_proposer_head(store, head_node, slot)`. Proposer có thể
   (may) đặt `parent_node == head_node` nếu cơ chế proposer re-org chưa được cài
   đặt hoặc đã bị tắt.
3. Gọi `parent` là block có root bằng `parent_node.root`.

> 💡 Ghi chú: "Proposer re-org" là cơ chế cho phép proposer bỏ qua (re-org) một
> head block đến muộn và yếu, để xây trực tiếp lên parent của nó — qua đó phạt các
> proposer phát block trễ.

Validator tạo, ký và broadcast một `block` là con của `parent` và thỏa mãn một
[state transition hợp lệ của beacon chain](./beacon-chain.md#beacon-chain-state-transition-function).
Lưu ý rằng slot của parent phải nhỏ hơn hẳn slot của block sắp được propose, tức là
`parent.slot < slot`.

Mỗi slot có một proposer, nên nếu có N validator đang active thì trung bình mỗi
validator sẽ được phân công propose một lần trong N slot.

*Lưu ý*: Trong phần này, `state` là state của slot dùng để propose block, _chưa_ áp
dụng block. Nghĩa là `state` là `previous_state` đã được xử lý qua các slot trống
cho tới slot được phân công, bằng `process_slots(previous_state, slot)`.

#### Preparing for a `BeaconBlock`

Để xây dựng `BeaconBlockBody`, một `block` (`BeaconBlock`) được định nghĩa với ngữ
cảnh cần thiết cho việc propose block:

##### Slot

Gán `block.slot = slot`, trong đó `slot` là slot hiện tại mà validator được chọn để
propose. `parent` được chọn phải thỏa mãn `parent.slot < block.slot`.

*Lưu ý*: Có thể có các slot bị "bỏ qua" (skipped) giữa `parent` và `block`. Các
skipped slot này được xử lý trong hàm state transition mà không có phần xử lý theo
từng block (per-block processing).

##### Proposer index

Gán `block.proposer_index = validator_index`, trong đó `validator_index` là
validator được chọn để propose tại slot này. Private key tương ứng với
`state.validators[validator_index].pubkey` được dùng để ký block.

##### Parent root

Gán `block.parent_root = hash_tree_root(parent)`.

#### Constructing the `BeaconBlockBody`

##### Randao reveal

Gán `block.body.randao_reveal = epoch_signature`, trong đó `epoch_signature` được
tính như sau:

```python
def get_epoch_signature(state: BeaconState, block: BeaconBlock, privkey: int) -> BLSSignature:
    domain = get_domain(state, DOMAIN_RANDAO, compute_epoch_at_slot(block.slot))
    signing_root = compute_signing_root(compute_epoch_at_slot(block.slot), domain)
    return bls.Sign(privkey, signing_root)
```

> 💡 Ghi chú: RANDAO reveal là chữ ký BLS của proposer lên số epoch. Vì chữ ký BLS
> là tất định (deterministic) nhưng không đoán trước được, giá trị này được trộn vào
> RANDAO mix để tạo nguồn ngẫu nhiên cho giao thức.

##### Eth1 Data

Trường `block.body.eth1_data` dùng để các block proposer bỏ phiếu (vote) cho data
Eth1 gần đây. Data này gồm một block hash của Eth1, cùng với deposit root tương ứng
(được tính bằng hàm `get_deposit_root()` của deposit contract) và deposit count sau
khi thực thi block Eth1 đó. Nếu hơn một nửa số block proposer trong Eth1 voting
period hiện tại bỏ phiếu cho cùng một `eth1_data`, thì `state.eth1_data` được cập
nhật ngay lập tức, cho phép xử lý các deposit mới. Mỗi deposit trong
`block.body.deposits` phải được xác minh dựa trên `state.eth1_data.deposit_root`.

###### `get_eth1_data`

Gọi `Eth1Block` là một object trừu tượng đại diện cho block Eth1, có sẵn
`timestamp` và data của deposit contract.

Gọi `get_eth1_data(block: Eth1Block) -> Eth1Data` là hàm trả về data Eth1 của một
block Eth1 cho trước.

Một block proposer trung thực sẽ gán
`block.body.eth1_data = get_eth1_vote(state, eth1_chain)`, trong đó:

```python
def voting_period_start_time(state: BeaconState) -> Uint64:
    eth1_voting_period_start_slot = state.slot - state.slot % (
        Uint64(EPOCHS_PER_ETH1_VOTING_PERIOD) * SLOTS_PER_EPOCH
    )
    return compute_time_at_slot(state.genesis_time, eth1_voting_period_start_slot)
```

```python
def is_candidate_block(block: Eth1Block, period_start: Uint64) -> bool:
    return (
        block.timestamp + SECONDS_PER_ETH1_BLOCK * ETH1_FOLLOW_DISTANCE <= period_start
        and block.timestamp + SECONDS_PER_ETH1_BLOCK * ETH1_FOLLOW_DISTANCE * 2 >= period_start
    )
```

```python
def get_eth1_vote(state: BeaconState, eth1_chain: Sequence[Eth1Block]) -> Eth1Data:
    period_start = voting_period_start_time(state)
    # `eth1_chain` abstractly represents all blocks in the eth1 chain sorted by ascending block height
    votes_to_consider = [
        get_eth1_data(block)
        for block in eth1_chain
        if (
            is_candidate_block(block, period_start)
            # Ensure cannot move back to earlier deposit contract states
            and get_eth1_data(block).deposit_count >= state.eth1_data.deposit_count
        )
    ]

    # Valid votes already cast during this period
    valid_votes = [vote for vote in state.eth1_data_votes if vote in votes_to_consider]

    # Default vote on latest eth1 block data in the period range unless eth1 chain is not live
    # Non-substantive casting for linter
    state_eth1_data: Eth1Data = state.eth1_data
    default_vote = (
        votes_to_consider[len(votes_to_consider) - 1] if any(votes_to_consider) else state_eth1_data
    )

    return max(
        valid_votes,
        # Tiebreak by smallest distance
        key=lambda v: (
            valid_votes.count(v),
            -valid_votes.index(v),
        ),
        default=default_vote,
    )
```

> 💡 Ghi chú: Tóm tắt logic `get_eth1_vote`:
>
> - Block Eth1 "ứng viên" là block có timestamp nằm trong khoảng từ
>   `ETH1_FOLLOW_DISTANCE` đến `2 * ETH1_FOLLOW_DISTANCE` block (quy đổi ra thời
>   gian) trước thời điểm bắt đầu voting period, và deposit count không nhỏ hơn
>   giá trị hiện có trong state (không được lùi lại).
> - Trong các vote đã có trong `state.eth1_data_votes` thuộc tập ứng viên, chọn vote
>   xuất hiện nhiều nhất; nếu hòa, chọn vote xuất hiện sớm nhất.
> - Nếu chưa có vote hợp lệ nào, vote mặc định cho ứng viên mới nhất; nếu không có
>   ứng viên nào (ví dụ chuỗi Eth1 không hoạt động), giữ nguyên `state.eth1_data`.

##### Proposer slashings

Có thể đưa tối đa `MAX_PROPOSER_SLASHINGS` object
[`ProposerSlashing`](./beacon-chain.md#proposerslashing) vào `block`. Các proposer
slashing phải thỏa mãn các điều kiện xác minh trong
[proposer slashings processing](./beacon-chain.md#proposer-slashings). Validator
nhận một khoản reward nhỏ dành cho "whistleblower" (người tố giác) với mỗi proposer
slashing mà nó tìm thấy và đưa vào block.

##### Attester slashings

Có thể đưa tối đa `MAX_ATTESTER_SLASHINGS` object
[`AttesterSlashing`](./beacon-chain.md#attesterslashing) vào `block`. Các attester
slashing phải thỏa mãn các điều kiện xác minh trong
[attester slashings processing](./beacon-chain.md#attester-slashings). Validator
nhận một khoản reward nhỏ dành cho "whistleblower" với mỗi attester slashing mà nó
tìm thấy và đưa vào block.

##### Attestations

Có thể đưa tối đa `MAX_ATTESTATIONS` aggregate attestation vào `block`. Các
attestation được thêm vào phải thỏa mãn các điều kiện xác minh trong
[attestation processing](./beacon-chain.md#attestations). Để tối đa hóa lợi nhuận,
validator nên cố gắng thu thập các aggregate attestation bao gồm attestation đơn lẻ
từ nhiều validator nhất có thể, mà chữ ký của các validator đó trong cùng epoch
chưa từng được đưa lên chain trước đây.

##### Deposits

Nếu còn deposit chưa được xử lý ứng với `state.eth1_data` hiện tại (tức là
`state.eth1_data.deposit_count > state.eth1_deposit_index`), thì các deposit đang
chờ _bắt buộc_ phải được đưa vào block. Số deposit cần đưa vào chính xác là
`min(MAX_DEPOSITS, eth1_data.deposit_count - state.eth1_deposit_index)`. Các
[`deposits`](./beacon-chain.md#deposit) này được tạo từ các log `Deposit` của
[deposit contract](./deposit-contract.md) và phải được xử lý theo đúng thứ tự tuần
tự. Các deposit đưa vào `block` phải thỏa mãn các điều kiện xác minh trong
[deposits processing](./beacon-chain.md#deposits).

`proof` của mỗi deposit phải được xây dựng dựa trên deposit root chứa trong
`state.eth1_data`, chứ không phải deposit root tại thời điểm deposit được ghi log
lần đầu trên chuỗi proof-of-work. Điều này đòi hỏi phải lưu trữ toàn bộ deposit
Merkle tree ở local và tính lại proof theo `eth1_data.deposit_root` khi cần. Xem
[`minimal_merkle.py`](https://github.com/ethereum/research/blob/master/spec_pythonizer/utils/merkle_minimal.py)
để tham khảo một cài đặt mẫu.

##### Voluntary exits

Có thể đưa tối đa `MAX_VOLUNTARY_EXITS` object
[`VoluntaryExit`](./beacon-chain.md#voluntaryexit) vào `block`. Các exit phải thỏa
mãn các điều kiện xác minh trong [exits processing](./beacon-chain.md#voluntary-exits).

*Lưu ý*: Nếu một slashing của một validator được đưa vào cùng block với voluntary
exit của chính validator đó, voluntary exit sẽ thất bại và khiến block không hợp
lệ, vì slashing được xử lý trước. Người cài đặt phải chú ý đến tương tác này giữa
các operation khi đóng gói block.

#### Packaging into a `SignedBeaconBlock`

##### State root

Gán `block.state_root = hash_tree_root(state)` của `state` kết quả sau state
transition `parent -> block`.

*Lưu ý*: Để tính `state_root`, trước tiên validator nên chạy hàm state transition
trên một `block` chưa ký có chứa giá trị tạm (stub) cho `state_root`. Vì mục đích
này, sẽ rất hữu ích nếu có một hàm state transition (chạy trên bản sao của state)
_không_ kiểm tra chữ ký hay state root:

```python
def compute_new_state_root(state: BeaconState, block: BeaconBlock) -> Root:
    temp_state: BeaconState = state.copy()
    signed_block = SignedBeaconBlock(message=block, signature=BLSSignature())
    state_transition(temp_state, signed_block, validate_result=False)
    return hash_tree_root(temp_state)
```

##### Signature

`signed_block = SignedBeaconBlock(message=block, signature=block_signature)`,
trong đó `block_signature` được tính như sau:

```python
def get_block_signature(state: BeaconState, block: BeaconBlock, privkey: int) -> BLSSignature:
    domain = get_domain(state, DOMAIN_BEACON_PROPOSER, compute_epoch_at_slot(block.slot))
    signing_root = compute_signing_root(block, domain)
    return bls.Sign(privkey, signing_root)
```

### Attesting

Validator được kỳ vọng sẽ tạo, ký và broadcast một attestation trong mỗi epoch.
`committee`, `index` được giao và `slot` được giao — tức nơi validator thực hiện vai
trò này trong một epoch — được xác định bởi
`get_committee_assignment(state, epoch, validator_index)`.

Validator nên tạo và broadcast `attestation` tới attestation subnet tương ứng khi
xảy ra một trong hai điều sau, tùy điều nào đến trước: (a) validator đã nhận được
một block hợp lệ từ block proposer dự kiến cho `slot` được giao, hoặc (b) đã trôi
qua `get_attestation_due_ms()` mili giây kể từ đầu slot.

*Lưu ý*: Mặc dù các attestation trong `GENESIS_EPOCH` không được tính vào FFG
finality, những attestation đầu tiên này vẫn góp trọng số cho fork choice, vẫn được
nhận reward, và vẫn nên được tạo.

#### Attestation data

Trước tiên, validator nên xây dựng `attestation_data`, một object
[`AttestationData`](./beacon-chain.md#attestationdata) dựa trên state tại slot được
giao.

- Gọi `head_block` là kết quả của việc chạy fork choice trong slot được giao.
- Gọi `head_state` là state của `head_block` đã được xử lý qua các slot trống cho
  tới slot được giao, bằng `process_slots(state, slot)`.

##### General

- Gán `attestation_data.slot = slot`, trong đó `slot` là slot được giao.
- Gán `attestation_data.index = index`, trong đó `index` là index gắn với committee
  của validator.

##### LMD GHOST vote

Gán `attestation_data.beacon_block_root = hash_tree_root(head_block)`.

> 💡 Ghi chú: Đây là phiếu bầu cho head của chain, được fork choice LMD-GHOST sử
> dụng.

##### FFG vote

- Gán `attestation_data.source = head_state.current_justified_checkpoint`.
- Gán
  `attestation_data.target = Checkpoint(epoch=get_current_epoch(head_state), root=epoch_boundary_block_root)`
  trong đó `epoch_boundary_block_root` là root của block tại ranh giới epoch gần
  nhất.

*Lưu ý*: `epoch_boundary_block_root` có thể được tra cứu trong state như sau:

- Gọi `start_slot = compute_start_slot_at_epoch(get_current_epoch(head_state))`.
- Gọi
  `epoch_boundary_block_root = hash_tree_root(head_block) if start_slot == head_state.slot else get_block_root(head_state, get_current_epoch(head_state))`.

> 💡 Ghi chú: Nói cách khác, nếu head state đang ở đúng slot đầu tiên của epoch thì
> chính `head_block` là block ranh giới epoch; nếu không, lấy block root tại slot
> đầu epoch hiện tại từ lịch sử lưu trong state.

#### Construct attestation

Tiếp theo, validator tạo `attestation`, một object
[`Attestation`](./beacon-chain.md#attestation).

##### Data

Gán `attestation.data = attestation_data`, trong đó `attestation_data` là object
`AttestationData` đã định nghĩa ở phần trước,
[attestation data](#attestation-data).

##### Aggregation bits

- Gọi `attestation.aggregation_bits` là một `AggregationBits` có độ dài
  `len(committee)`, trong đó bit ở vị trí index của validator trong `committee`
  được đặt thành `0b1`.

*Lưu ý*: Gọi `get_attesting_indices(state, attestation)` sẽ trả về một danh sách
có độ dài bằng 1, chứa `validator_index`.

##### Aggregate signature

Gán `attestation.signature = attestation_signature`, trong đó
`attestation_signature` được tính như sau:

```python
def get_attestation_signature(
    state: BeaconState, attestation_data: AttestationData, privkey: int
) -> BLSSignature:
    domain = get_domain(state, DOMAIN_BEACON_ATTESTER, attestation_data.target.epoch)
    signing_root = compute_signing_root(attestation_data, domain)
    return bls.Sign(privkey, signing_root)
```

#### Broadcast attestation

Cuối cùng, validator broadcast `attestation` tới attestation subnet tương ứng, tức
pubsub topic `beacon_attestation_{subnet_id}`.

`subnet_id` của `attestation` được tính như sau:

- Gọi
  `committees_per_slot = get_committee_count_per_slot(state, attestation.data.target.epoch)`.
- Gọi
  `subnet_id = compute_subnet_for_attestation(committees_per_slot, attestation.data.slot, attestation.data.index)`.

```python
def compute_subnet_for_attestation(
    committees_per_slot: Uint64, slot: Slot, committee_index: CommitteeIndex
) -> SubnetID:
    """
    Compute the correct subnet for an attestation for Phase 0.
    Note, this mimics expected future behavior where attestations will be mapped to their shard subnet.
    """
    slots_since_epoch_start = Uint64(slot % SLOTS_PER_EPOCH)
    committees_since_epoch_start = committees_per_slot * slots_since_epoch_start

    return SubnetID((committees_since_epoch_start + committee_index) % ATTESTATION_SUBNET_COUNT)
```

> 💡 Ghi chú: Hàm này đánh số tuần tự tất cả committee trong epoch (slot trước,
> committee index sau) rồi lấy modulo `ATTESTATION_SUBNET_COUNT` để ra subnet. Thiết
> kế này mô phỏng hành vi dự kiến trong tương lai, khi attestation được ánh xạ tới
> subnet của shard tương ứng.

### Attestation aggregation

Một số validator được chọn để aggregate (gộp) ở local các attestation có
`attestation_data` giống với `attestation` mà chính họ đã tạo cho `slot` được giao.

#### Aggregation selection

Validator được chọn làm aggregator dựa trên giá trị trả về của `is_aggregator()`.

```python
def get_slot_signature(state: BeaconState, slot: Slot, privkey: int) -> BLSSignature:
    domain = get_domain(state, DOMAIN_SELECTION_PROOF, compute_epoch_at_slot(slot))
    signing_root = compute_signing_root(slot, domain)
    return bls.Sign(privkey, signing_root)
```

```python
def is_aggregator(
    state: BeaconState, slot: Slot, index: CommitteeIndex, slot_signature: BLSSignature
) -> bool:
    committee = get_beacon_committee(state, slot, index)
    modulo = max(1, len(committee) // TARGET_AGGREGATORS_PER_COMMITTEE)
    return bytes_to_uint64(sha256(slot_signature)[0:8]) % modulo == 0
```

> 💡 Ghi chú: Mỗi validator ký lên số slot; hash của chữ ký này đóng vai trò như một
> số ngẫu nhiên có thể kiểm chứng. Với `modulo = len(committee) // 16`, xác suất mỗi
> validator được chọn là khoảng `1/modulo`, nên kỳ vọng mỗi committee có khoảng
> `TARGET_AGGREGATORS_PER_COMMITTEE` (16) aggregator. Chữ ký này cũng chính là
> `selection_proof` để người khác kiểm chứng.

#### Construct aggregate

Nếu validator được chọn làm aggregator (`is_aggregator()`), họ tạo một aggregate
attestation như sau.

Thu thập các `attestations` nhận được qua gossip trong `slot` có `attestation_data`
giống với `attestation_data` mà validator đã tạo. Nếu `len(attestations) > 0`, tạo
một `aggregate_attestation: Attestation` với các trường sau.

##### Data

Gán `aggregate_attestation.data = attestation_data`, trong đó `attestation_data` là
object `AttestationData` chung của mọi attestation đơn lẻ đang được aggregate.

##### Aggregation bits

Gọi `aggregate_attestation.aggregation_bits` là một `AggregationBits` có độ dài
`len(committee)`, trong đó mọi bit đã được bật trong từng attestation đơn lẻ đều
được đặt thành `0b1`.

##### Aggregate signature

Gán `aggregate_attestation.signature = aggregate_signature`, trong đó
`aggregate_signature` được tính như sau:

```python
def get_aggregate_signature(attestations: Sequence[Attestation]) -> BLSSignature:
    signatures = [attestation.signature for attestation in attestations]
    return bls.Aggregate(signatures)
```

#### Broadcast aggregate

Nếu validator được chọn làm aggregator (`is_aggregator`), họ broadcast aggregate tốt
nhất của mình dưới dạng `SignedAggregateAndProof` tới kênh aggregate toàn cục
(`beacon_aggregate_and_proof`) tại thời điểm `get_aggregate_due_ms()` mili giây kể
từ đầu slot.

Selection proof được đính kèm trong `AggregateAndProof` để chứng minh với kênh
gossip rằng validator đã được chọn làm aggregator.

Các message `AggregateAndProof` được aggregator ký và broadcast bên trong object
`SignedAggregateAndProof` nhằm ngăn chặn một nhóm tấn công DoS và việc giả mạo
message.

Trước tiên, tạo
`aggregate_and_proof = get_aggregate_and_proof(state, validator_index, aggregate_attestation, privkey)`.

```python
def get_aggregate_and_proof(
    state: BeaconState, aggregator_index: ValidatorIndex, aggregate: Attestation, privkey: int
) -> AggregateAndProof:
    return AggregateAndProof(
        aggregator_index=aggregator_index,
        aggregate=aggregate,
        selection_proof=get_slot_signature(state, aggregate.data.slot, privkey),
    )
```

Sau đó tạo và broadcast
`signed_aggregate_and_proof = SignedAggregateAndProof(message=aggregate_and_proof, signature=signature)`,
trong đó `signature` được tính như sau:

```python
def get_aggregate_and_proof_signature(
    state: BeaconState, aggregate_and_proof: AggregateAndProof, privkey: int
) -> BLSSignature:
    aggregate = aggregate_and_proof.aggregate
    domain = get_domain(
        state, DOMAIN_AGGREGATE_AND_PROOF, compute_epoch_at_slot(aggregate.data.slot)
    )
    signing_root = compute_signing_root(aggregate_and_proof, domain)
    return bls.Sign(privkey, signing_root)
```

## How to avoid slashing

"Slashing" (phạt cắt giảm stake) là việc đốt một phần tiền của validator và lập tức
loại validator khỏi tập validator đang active. Trong Phase 0, có hai cách khiến tiền
bị slash: [proposer slashing](#proposer-slashing) và
[attester slashing](#attester-slashing). Mặc dù bị slash có hậu quả nghiêm trọng,
việc tránh hoàn toàn slashing khá đơn giản: chỉ cần luôn _nhất quán_ với các message
mà validator đã ký trước đó.

*Lưu ý*: Data đã ký chỉ có thể xung đột nếu nằm trong cùng một ngữ cảnh `Fork` liên
tiếp. Không thể slash message giữa các fork đã rẽ nhánh khác nhau. Nếu fork version
trước đó là 1 và chain tách thành fork 2 và fork 102, thì message từ fork 1 có thể
bị coi là slashable khi đối chiếu với message trong fork 1, 2 và 102. Message trong
fork 2 không thể bị slash khi đối chiếu với message trong fork 102, và ngược lại.

### Proposer slashing

Để tránh "proposer slashing", validator không được ký hai
[`BeaconBlock`](./beacon-chain.md#beaconblock) xung đột, trong đó "xung đột" được
định nghĩa là hai block khác nhau trong cùng một slot.

*Trong Phase 0, chỉ cần validator không ký hai beacon block khác nhau cho cùng một
slot thì validator sẽ an toàn trước proposer slashing.*

Cụ thể, khi ký một `BeaconBlock`, validator nên thực hiện các bước sau theo đúng
thứ tự:

1. Lưu một bản ghi xuống ổ cứng rằng đã ký một beacon block cho
   `slot=block.slot`.
2. Tạo và broadcast block.

Nếu phần mềm bị crash tại bất kỳ thời điểm nào trong quy trình này, thì khi
validator online trở lại, ổ cứng đã có bản ghi về block *có thể* đã được
ký/broadcast, nhờ đó tránh được slashing một cách hiệu quả.

### Attester slashing

Để tránh "attester slashing", validator không được ký hai object
[`AttestationData`](./beacon-chain.md#attestationdata) xung đột, tức là hai
attestation thỏa mãn
[`is_slashable_attestation_data`](./beacon-chain.md#is_slashable_attestation_data).

> 💡 Ghi chú: Theo `is_slashable_attestation_data`, hai attestation xung đột khi
> (1) "double vote": hai attestation khác nhau có cùng target epoch, hoặc
> (2) "surround vote": attestation này "bao quanh" attestation kia, tức source epoch
> nhỏ hơn và target epoch lớn hơn.

Cụ thể, khi ký một `Attestation`, validator nên thực hiện các bước sau theo đúng
thứ tự:

1. Lưu một bản ghi xuống ổ cứng rằng đã ký một attestation với source (tức
   `attestation_data.source.epoch`) và target (tức
   `attestation_data.target.epoch`).
2. Tạo và broadcast attestation.

Nếu phần mềm bị crash tại bất kỳ thời điểm nào trong quy trình này, thì khi
validator online trở lại, ổ cứng đã có bản ghi về attestation *có thể* đã được
ký/broadcast, nhờ đó tránh được slashing một cách hiệu quả.

## Protection best practices

Validator client nên được coi là một thành phần độc lập và nên coi beacon node là
không đáng tin cậy (untrusted). Điều này có nghĩa là validator client nên bảo vệ:

1. Private key -- private key cần được bảo vệ để không bị export ra ngoài do vô
   tình hoặc bởi kẻ tấn công.
2. Slashing -- trước khi ký một message, validator client nên validate data, đối
   chiếu với slashing database ở local (không ký attestation hoặc block có thể bị
   slash) và cập nhật slashing database nội bộ với object vừa được ký.
3. Validator được khôi phục -- Khôi phục validator từ private key sẽ dẫn đến
   slashing db ở local bị trống. Best practice là import (từ một nguồn đáng tin
   cậy) lịch sử attestation của validator đó. Xem
   [EIP 3076](https://github.com/ethereum/EIPs/pull/3076/files) để biết định dạng
   chuẩn cho việc trao đổi dữ liệu slashing (slashing interchange format).
4. Yêu cầu ký cho thời điểm quá xa trong tương lai -- Validator client có thể bị
   yêu cầu ký một attestation ở rất xa trong tương lai; đây là một request hợp lệ và
   không slashable. Nếu validator client ký message này, nó sẽ tự chặn chính mình
   không thể attest bất kỳ attestation nào khác cho đến khi beacon chain tiến tới
   epoch xa trong tương lai đó. Điều này dẫn tới penalty do không hoạt động
   (inactivity penalty) và có khả năng bị loại khỏi tập validator do balance thấp.
   Validator client nên tự ngăn việc ký các request như vậy bằng cách: a) duy trì
   đồng hồ thời gian ở local nếu có thể và tuân theo best practice để chống tấn công
   vào time server, và b) mặc định từ chối ký bất kỳ message nào có khoảng cách lớn
   (>6h) so với slashing protection database hiện tại — dấu hiệu của việc thời gian
   bị "nhảy" hoặc một đợt offline kéo dài. Quản trị viên có thể ghi đè thủ công cơ
   chế bảo vệ này để khởi động lại validator sau một đợt offline dài thực sự.
