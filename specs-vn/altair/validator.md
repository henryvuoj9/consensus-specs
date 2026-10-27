# Altair -- Honest Validator

Đây là tài liệu đi kèm với
[Altair -- The Beacon Chain](./beacon-chain.md), mô tả các hành động mà một
"validator" tham gia giao thức proof-of-stake của Ethereum được kỳ vọng thực
hiện.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Types](#types)
  - [`SyncSubcommitteeBits`](#syncsubcommitteebits)
- [Constants](#constants)
  - [Misc](#misc)
- [Configs](#configs)
  - [Time parameters](#time-parameters)
- [Containers](#containers)
  - [`SyncCommitteeMessage`](#synccommitteemessage)
  - [`SyncCommitteeContribution`](#synccommitteecontribution)
  - [`ContributionAndProof`](#contributionandproof)
  - [`SignedContributionAndProof`](#signedcontributionandproof)
  - [`SyncAggregatorSelectionData`](#syncaggregatorselectiondata)
- [Validator assignments](#validator-assignments)
  - [Sync Committee](#sync-committee)
  - [Lookahead](#lookahead)
- [Beacon chain responsibilities](#beacon-chain-responsibilities)
  - [Block proposal](#block-proposal)
    - [Preparing a `BeaconBlock`](#preparing-a-beaconblock)
    - [Constructing the `BeaconBlockBody`](#constructing-the-beaconblockbody)
      - [Sync committee](#sync-committee)
    - [Packaging into a `SignedBeaconBlock`](#packaging-into-a-signedbeaconblock)
  - [Attesting and attestation aggregation](#attesting-and-attestation-aggregation)
  - [Sync committees](#sync-committees)
    - [Sync committee messages](#sync-committee-messages)
      - [Prepare sync committee message](#prepare-sync-committee-message)
      - [Broadcast sync committee message](#broadcast-sync-committee-message)
    - [Sync committee contributions](#sync-committee-contributions)
      - [Aggregation selection](#aggregation-selection)
      - [Construct sync committee contribution](#construct-sync-committee-contribution)
        - [Slot](#slot)
        - [Beacon block root](#beacon-block-root)
        - [Subcommittee index](#subcommittee-index)
        - [Aggregation bits](#aggregation-bits)
        - [Signature](#signature)
      - [Broadcast sync committee contribution](#broadcast-sync-committee-contribution)
- [Sync committee subnet stability](#sync-committee-subnet-stability)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả hành vi được kỳ vọng của một "honest validator" (validator
trung thực) đối với bản nâng cấp Altair của giao thức proof-of-stake Ethereum.
Nó được xây dựng dựa trên
[tài liệu trước đó về hành vi của "honest validator" từ Phase 0](../phase0/validator.md)
của giao thức proof-of-stake Ethereum. Bên dưới, tài liệu trước đó được gọi là
"tài liệu Phase 0".

Altair giới thiệu một loại committee mới: sync committee. Các sync committee chịu
trách nhiệm ký lên từng block của chuỗi chính tắc (canonical chain), và có một
thuật toán hiệu quả cho phép light client đồng bộ chuỗi dựa trên đầu ra của các
sync committee. Xem [sync protocol](./light-client/sync-protocol.md) để biết thêm
chi tiết về cơ chế sync của light client. Với bản nâng cấp mạng này, các
validator theo dõi việc mình có tham gia loại committee mới này hay không và tạo
ra các signature liên quan khi được yêu cầu. Block proposer đưa các signature
(đã được aggregate) của sync committee vào mỗi block mà họ tạo ra.

> 💡 Ghi chú: Nhờ sync committee, light client chỉ cần theo dõi một tập nhỏ
> validator (thay vì toàn bộ validator set) để xác minh header của chuỗi.

## Prerequisites

Mọi thuật ngữ, hằng số, hàm và cơ chế giao thức được định nghĩa trong spec
[Altair -- The Beacon Chain](./beacon-chain.md) đều là kiến thức tiên quyết cho
tài liệu này và được sử dụng xuyên suốt. Vui lòng đọc tài liệu đó trước khi tiếp
tục và dùng nó làm tài liệu tham chiếu trong suốt quá trình đọc.

## Types

### `SyncSubcommitteeBits`

```python
class SyncSubcommitteeBits(BitVector):
    """
    The participation bits of a single sync subcommittee, one bit per member
    in subcommittee order.
    """

    LENGTH = SYNC_COMMITTEE_SIZE // SYNC_COMMITTEE_SUBNET_COUNT
```

## Constants

### Misc

| Name                                       | Value                 |
| ------------------------------------------ | --------------------- |
| `TARGET_AGGREGATORS_PER_SYNC_SUBCOMMITTEE` | `Uint64(2**4)` (= 16) |
| `SYNC_COMMITTEE_SUBNET_COUNT`              | `Uint64(2**2)` (= 4)  |

## Configs

### Time parameters

| Name                   | Value          | Duration                       |
| ---------------------- | -------------- | ------------------------------ |
| `SYNC_MESSAGE_DUE_BPS` | `Uint64(3333)` | ~33% của `SLOT_DURATION_MS`    |
| `CONTRIBUTION_DUE_BPS` | `Uint64(6667)` | ~67% của `SLOT_DURATION_MS`    |

## Containers

### `SyncCommitteeMessage`

```python
class SyncCommitteeMessage(Container):
    slot: Slot
    beacon_block_root: Root
    validator_index: ValidatorIndex
    signature: BLSSignature
```

### `SyncCommitteeContribution`

```python
class SyncCommitteeContribution(Container):
    slot: Slot
    beacon_block_root: Root
    subcommittee_index: Uint64
    aggregation_bits: SyncSubcommitteeBits
    signature: BLSSignature
```

### `ContributionAndProof`

```python
class ContributionAndProof(Container):
    aggregator_index: ValidatorIndex
    contribution: SyncCommitteeContribution
    selection_proof: BLSSignature
```

### `SignedContributionAndProof`

```python
class SignedContributionAndProof(Container):
    message: ContributionAndProof
    signature: BLSSignature
```

### `SyncAggregatorSelectionData`

```python
class SyncAggregatorSelectionData(Container):
    slot: Slot
    subcommittee_index: Uint64
```

## Validator assignments

Validator xác định nhiệm vụ trong beacon committee và nhiệm vụ đề xuất beacon
block theo đúng như mô tả trong tài liệu Phase 0.

### Sync Committee

Để xác định mình có được phân công vào sync committee hay không, validator có thể
chạy hàm sau: `is_assigned_to_sync_committee(state, epoch, validator_index)`,
trong đó `epoch` là một số epoch nằm trong sync committee period (chu kỳ sync
committee) hiện tại hoặc kế tiếp. Hàm này là một predicate (hàm trả về đúng/sai)
cho biết validator có hay không có mặt trong sync committee tương ứng với sync
committee period được hỏi.

*Lưu ý*: Được phân công vào một sync committee cho một `slot` nhất định có nghĩa
là validator tạo và broadcast signature cho `slot - 1` để được đưa vào block ở
`slot`. Điều này có nghĩa là khi được phân công cho một `epoch`, các signature
của sync committee phải được tạo và broadcast cho các slot trong khoảng
`[compute_start_slot_at_epoch(epoch) - 1, compute_start_slot_at_epoch(epoch) + SLOTS_PER_EPOCH - 1)`
chứ không phải trong khoảng
`[compute_start_slot_at_epoch(epoch), compute_start_slot_at_epoch(epoch) + SLOTS_PER_EPOCH)`.
Để giảm độ phức tạp trong quá trình nâng cấp Altair, các sync committee không cần
tạo signature cho `compute_start_slot_at_epoch(ALTAIR_FORK_EPOCH) - 1`.

> 💡 Ghi chú: Nói cách khác, mọi thứ "lệch" đi một slot: signature ký lên head
> block của slot `N - 1` sẽ được proposer của slot `N` đưa vào block. Do đó
> khoảng slot mà validator phải ký cũng dịch sớm hơn một slot so với epoch được
> phân công.

```python
def compute_sync_committee_period(epoch: Epoch) -> Uint64:
    return epoch // EPOCHS_PER_SYNC_COMMITTEE_PERIOD
```

```python
def is_assigned_to_sync_committee(
    state: BeaconState, epoch: Epoch, validator_index: ValidatorIndex
) -> bool:
    sync_committee_period = compute_sync_committee_period(epoch)
    current_epoch = get_current_epoch(state)
    current_sync_committee_period = compute_sync_committee_period(current_epoch)
    next_sync_committee_period = current_sync_committee_period + 1
    assert sync_committee_period in (current_sync_committee_period, next_sync_committee_period)

    pubkey = state.validators[validator_index].pubkey
    if sync_committee_period == current_sync_committee_period:
        return pubkey in state.current_sync_committee.pubkeys
    else:  # sync_committee_period == next_sync_committee_period
        return pubkey in state.next_sync_committee.pubkeys
```

### Lookahead

Việc shuffling sync committee cho phép validator biết trước (lookahead) 1 sync
committee period, tức là `EPOCHS_PER_SYNC_COMMITTEE_PERIOD` epoch. Tại bất kỳ
`epoch` nào, `BeaconState` đều chứa `SyncCommittee` hiện tại và `SyncCommittee`
kế tiếp. Cứ mỗi `EPOCHS_PER_SYNC_COMMITTEE_PERIOD` epoch một lần, `SyncCommittee`
kế tiếp trở thành `SyncCommittee` hiện tại, và committee kế tiếp mới được tính
toán rồi lưu lại.

*Lưu ý*: Dữ liệu cần thiết để tính một committee nhất định không được cache trong
`BeaconState` sau khi các committee đã được tính tại ranh giới period. Vì lý do
này, hãy *luôn luôn* lấy thông tin phân công committee thông qua các trường của
`BeaconState` (`current_sync_committee` và `next_sync_committee`) hoặc dùng đoạn
code tham chiếu ở trên.

Validator nên lên kế hoạch cho các nhiệm vụ sync committee trong tương lai bằng
cách ghi nhận những sync committee period mà mình được chọn tham gia. Cụ thể,
validator nên:

- Khi (re)sync chuỗi và tại mỗi ranh giới sync committee period, kiểm tra việc
  phân công trong sync committee period hiện tại và kế tiếp.
- Nếu validator nằm trong sync committee của period hiện tại, họ thực hiện các
  nhiệm vụ được mô tả bên dưới để nhận reward của sync committee.
- Nếu validator nằm trong sync committee của period kế tiếp, họ nên chờ đến ranh
  giới `EPOCHS_PER_SYNC_COMMITTEE_PERIOD` tiếp theo rồi thực hiện các nhiệm vụ
  trong suốt period đó.

## Beacon chain responsibilities

Validator vẫn duy trì các nhiệm vụ được nêu trong tài liệu Phase 0.

Việc đề xuất block được sửa đổi để đưa thêm các signature của sync committee vào,
như mô tả chi tiết bên dưới.

Khi được phân công vào một sync committee, validator có thêm một nhiệm vụ mới: ký
và broadcast beacon block root trong mỗi slot của sync committee period. Các
signature này được aggregate và chuyển tới proposer qua gossip để được đưa vào
beacon block. Với số lượng validator thông thường, việc được phân công vào một
sync committee cụ thể là không thường xuyên; tuy nhiên, khi đang ở trong sync
committee đang hoạt động, validator phải thực hiện hành động ở mỗi slot.

### Block proposal

Tham khảo tài liệu phase 0 cho phần lớn
[nhiệm vụ đề xuất block](../phase0/validator.md#block-proposal). Validator nên
làm theo các hướng dẫn đó để chuẩn bị một `SignedBeaconBlock` nhằm đưa vào chuỗi.
Mọi thay đổi đều là bổ sung thêm so với phase 0 và được ghi chú bên dưới.

#### Preparing a `BeaconBlock`

Không thay đổi so với
[Preparing for a `BeaconBlock`](../phase0/validator.md#preparing-for-a-beaconblock).

#### Constructing the `BeaconBlockBody`

Cần làm theo từng mục trong
[Constructing the `BeaconBlockBody`](../phase0/validator.md#constructing-the-beaconblockbody).
Sau khi xây dựng `BeaconBlockBody` theo mục đó, proposer có thêm một việc là đưa
các signature của sync committee vào:

##### Sync committee

Proposer nhận được một số `SyncCommitteeContribution` (được bọc trong
`SignedContributionAndProof` khi truyền trên mạng) từ các validator trong sync
committee — những người được chọn để aggregate một phần các signature từ các
subcommittee độc lập. Các subcommittee này được hình thành bằng cách chia toàn bộ
sync committee thành `SYNC_COMMITTEE_SUBNET_COUNT` phần (xem chi tiết bên dưới).

Proposer thu thập các contribution khớp với góc nhìn cục bộ của mình về chuỗi
(tức là `contribution.beacon_block_root == block.parent_root`) để aggregate tiếp
khi chuẩn bị block. Trong số các contribution này, proposer nên chọn contribution
tốt nhất đã thấy từ tất cả các aggregator cho mỗi subnet/subcommittee. Một
contribution có nhiều signature hợp lệ hơn được coi là tốt hơn contribution có
ít signature hơn.

Nhắc lại: `block.body.sync_aggregate.sync_committee_bits` là một `BitVector`,
trong đó bit thứ `i` là `True` nếu validator tương ứng trong sync committee đã
tạo ra một signature hợp lệ, và
`block.body.sync_aggregate.sync_committee_signature` là BLS signature aggregate
kết hợp tất cả các signature hợp lệ.

Cho trước một tập các `contributions` tốt nhất đã thấy (không có giá trị
`subcommittee_index` nào bị lặp lại) và `BeaconBlock` đang được xây dựng,
proposer xử lý chúng như sau:

```python
def process_sync_committee_contributions(
    block: BeaconBlock, contributions: set[SyncCommitteeContribution]
) -> None:
    sync_aggregate = SyncAggregate.empty()
    signatures = []
    sync_subcommittee_size = SYNC_COMMITTEE_SIZE // SYNC_COMMITTEE_SUBNET_COUNT

    for contribution in contributions:
        subcommittee_index = contribution.subcommittee_index
        for index, participated in enumerate(contribution.aggregation_bits):
            if participated:
                participant_index = sync_subcommittee_size * subcommittee_index + index
                sync_aggregate.sync_committee_bits[participant_index] = Boolean(True)
        signatures.append(contribution.signature)

    sync_aggregate.sync_committee_signature = bls.Aggregate(signatures)

    block.body.sync_aggregate = sync_aggregate
```

*Lưu ý*: Block kết quả phải vượt qua các bước kiểm tra hợp lệ đối với
`SyncAggregate` được định nghĩa trong `process_sync_aggregate` thuộc
[tài liệu state transition](./beacon-chain.md#sync-aggregate-processing). Đặc
biệt, điều này có nghĩa là các `SyncCommitteeContribution` nhận được từ gossip
phải có `beacon_block_root` khớp với góc nhìn cục bộ của proposer về chuỗi.

#### Packaging into a `SignedBeaconBlock`

Không thay đổi so với
[Packaging into a `SignedBeaconBlock`](../phase0/validator.md#packaging-into-a-signedbeaconblock).

### Attesting and attestation aggregation

Tham khảo tài liệu phase 0 cho các nhiệm vụ
[attesting](../phase0/validator.md#attesting) và
[attestation aggregation](../phase0/validator.md#attestation-aggregation). Không
có thay đổi nào so với tài liệu phase 0.

### Sync committees

Các thành viên sync committee sử dụng một cơ chế aggregation để giảm tải cho kênh
proposer toàn cục — kênh được tất cả các proposer tiềm năng theo dõi để có thể
đưa toàn bộ đầu ra của sync committee vào block ở mỗi slot. Các thành viên sync
committee tạo ra signature riêng lẻ trên các subnet (tương tự như các attestation
subnet) thông qua `SyncCommitteeMessage`. Các message này sau đó được thu thập
bởi các aggregator (được lấy mẫu từ các sync subcommittee) để tạo ra một
`SyncCommitteeContribution`, rồi được gossip tới các proposer. Quá trình này diễn
ra ở mỗi slot.

> 💡 Ghi chú: Luồng tổng quát: thành viên ký `SyncCommitteeMessage` → gửi lên
> subnet `sync_committee_{subnet_id}` → aggregator của subcommittee gộp lại thành
> `SyncCommitteeContribution` → gửi lên topic toàn cục
> `sync_committee_contribution_and_proof` → proposer gộp các contribution vào
> `SyncAggregate` của block.

#### Sync committee messages

##### Prepare sync committee message

Nếu một validator nằm trong sync committee hiện tại (tức là
`is_assigned_to_sync_committee()` ở trên trả về `True`), thì với mỗi `slot` trong
sync committee period hiện tại, validator nên chuẩn bị một `SyncCommitteeMessage`
cho slot trước đó (`slot - 1`) theo logic trong `get_sync_committee_message` ngay
khi họ đã xác định được head block của `slot - 1`. Điều này có nghĩa là khi được
phân công cho `slot`, một `SyncCommitteeMessage` sẽ được chuẩn bị và broadcast
trong `slot-1 ` thay vì `slot`.

Logic này được kích hoạt theo cùng các điều kiện như khi tạo một attestation.
Nghĩa là, một thành viên sync committee nên tạo và broadcast một
`SyncCommitteeMessage` khi (a) validator đã nhận được một block hợp lệ từ block
proposer dự kiến của `slot` hiện tại, hoặc (b) đã trôi qua
`get_sync_message_due_ms()` mili giây kể từ đầu slot -- tùy điều kiện nào xảy ra
trước.

`get_sync_committee_message(state, block_root, validator_index, privkey)` giả
định rằng tham số `state` là head state tương ứng với việc xử lý block cho đến
slot hiện tại theo kết quả của fork choice (bao gồm cả các slot trống cho đến
slot hiện tại, được xử lý bằng `process_slots` trên block mới nhất), `block_root`
là root của head block, `validator_index` là index của validator (do `privkey`
kiểm soát) trong registry `state.validators`, và `privkey` là BLS private key của
validator.

```python
def get_sync_committee_message(
    state: BeaconState, block_root: Root, validator_index: ValidatorIndex, privkey: int
) -> SyncCommitteeMessage:
    epoch = get_current_epoch(state)
    domain = get_domain(state, DOMAIN_SYNC_COMMITTEE, epoch)
    signing_root = compute_signing_root(block_root, domain)
    signature = bls.Sign(privkey, signing_root)

    return SyncCommitteeMessage(
        slot=state.slot,
        beacon_block_root=block_root,
        validator_index=validator_index,
        signature=signature,
    )
```

##### Broadcast sync committee message

Validator broadcast signature đã tạo tới subnet được phân công, tức là pubsub
topic `sync_committee_{subnet_id}`.

`subnet_id` được suy ra từ vị trí của validator trong sync committee, theo cách
sync committee được chia thành các "subcommittee". `subnet_id` có thể được tính
bằng `compute_subnets_for_sync_committee(state, validator_index)`, trong đó
`state` là một `BeaconState` thuộc sync committee period tương ứng.

*Lưu ý*: Hàm này trả về nhiều subnet (đã loại bỏ trùng lặp) nếu một validator
index được đưa vào một sync committee nhiều lần, rải rác trên nhiều
subcommittee.

```python
def compute_subnets_for_sync_committee(
    state: BeaconState, validator_index: ValidatorIndex
) -> set[SubnetID]:
    next_slot_epoch = compute_epoch_at_slot(state.slot + 1)
    if compute_sync_committee_period(get_current_epoch(state)) == compute_sync_committee_period(
        next_slot_epoch
    ):
        sync_committee = state.current_sync_committee
    else:
        sync_committee = state.next_sync_committee

    target_pubkey = state.validators[validator_index].pubkey
    sync_committee_indices = [
        index for index, pubkey in enumerate(sync_committee.pubkeys) if pubkey == target_pubkey
    ]
    return {
        SubnetID(index // (SYNC_COMMITTEE_SIZE // SYNC_COMMITTEE_SUBNET_COUNT))
        for index in sync_committee_indices
    }
```

*Lưu ý*: Việc phân công subnet không thay đổi trong suốt thời gian validator được
phân công vào một sync committee nhất định.

*Lưu ý*: Nếu `compute_subnets_for_sync_committee` trả về nhiều `subnet_id` cho
một validator, validator nên broadcast một bản sao của `sync_committee_message`
trên mỗi subnet khác nhau đó.

#### Sync committee contributions

Ở mỗi slot, một số thành viên sync committee trong mỗi subcommittee được chọn để
aggregate các `SyncCommitteeMessage` thành một `SyncCommitteeContribution`, được
broadcast trên một kênh toàn cục để đưa vào block tiếp theo.

##### Aggregation selection

Một validator được chọn làm aggregator dựa trên giá trị trả về của
`is_sync_committee_aggregator()`, trong đó `signature` là BLS signature được trả
về bởi `get_sync_committee_selection_proof()`. Hàm tạo signature nhận vào một
`BeaconState` chứa các sync committee liên quan tới `slot` được hỏi (tức là
`state.slot` nằm trong khoảng thời gian được bao phủ bởi sync committee period
hiện tại hoặc kế tiếp), `subcommittee_index` bằng với `subnet_id`, và `privkey`
là BLS private key của validator.

```python
def get_sync_committee_selection_proof(
    state: BeaconState, slot: Slot, subcommittee_index: Uint64, privkey: int
) -> BLSSignature:
    domain = get_domain(state, DOMAIN_SYNC_COMMITTEE_SELECTION_PROOF, compute_epoch_at_slot(slot))
    signing_data = SyncAggregatorSelectionData(
        slot=slot,
        subcommittee_index=subcommittee_index,
    )
    signing_root = compute_signing_root(signing_data, domain)
    return bls.Sign(privkey, signing_root)
```

```python
def is_sync_committee_aggregator(signature: BLSSignature) -> bool:
    modulo = max(
        1,
        SYNC_COMMITTEE_SIZE
        // SYNC_COMMITTEE_SUBNET_COUNT
        // TARGET_AGGREGATORS_PER_SYNC_SUBCOMMITTEE,
    )
    return bytes_to_uint64(sha256(signature)[0:8]) % modulo == 0
```

*Lưu ý*: Tập các aggregator nhìn chung thay đổi ở mỗi slot; tuy nhiên, việc phân
công có thể được tính trước ngay khi biết committee.

> 💡 Ghi chú: Với giá trị mainnet (`SYNC_COMMITTEE_SIZE = 512`), mỗi subcommittee
> có 128 thành viên và `modulo = 128 // 16 = 8`, nên mỗi thành viên có xác suất
> khoảng 1/8 được chọn — trung bình khoảng 16 aggregator cho mỗi subcommittee.

##### Construct sync committee contribution

Nếu một validator được chọn để aggregate các `SyncCommitteeMessage` được tạo ra
trên một subnet trong một `slot` nhất định, họ sẽ xây dựng một
`SyncCommitteeContribution` đã aggregate.

Thu thập tất cả các `sync_committee_messages: set[SyncCommitteeMessage]` (hợp lệ)
từ gossip `sync_committee_{subnet_id}` trong `slot` đã chọn, có
`beacon_block_root` giống với của aggregator. Nếu
`len(sync_committee_messages) > 0`, aggregator tạo một
`contribution: SyncCommitteeContribution` với các trường sau:

###### Slot

Đặt `contribution.slot = state.slot`, trong đó `state` là `BeaconState` của slot
đang xét.

###### Beacon block root

Đặt `contribution.beacon_block_root = beacon_block_root`, lấy từ
`beacon_block_root` có trong `sync_committee_messages`.

###### Subcommittee index

Đặt `contribution.subcommittee_index` bằng index của subcommittee được phân công
cho subnet này. Index này trùng với `subnet_id` được dùng để tạo tên topic.

###### Aggregation bits

Đặt `contribution.aggregation_bits` là một `SyncSubcommitteeBits`, trong đó bit
thứ `index` được bật cho mỗi validator tương ứng (thuộc subcommittee tương ứng)
được đưa vào aggregate này. Aggregator tìm index trong sync committee (bằng cách
tra ngược pubkey trong `state.current_sync_committee.pubkeys`) của validator được
tham chiếu bởi `sync_committee_message.validator_index`, rồi ánh xạ sync
committee index đó thành một index bên trong subcommittee (cùng với
`subcommittee_index` đã có ở trên). Index bên trong subcommittee này được bật
trong `contribution.aggregation_bits`.

Ví dụ, giả sử validator có index `2044` được lấy mẫu giả ngẫu nhiên vào sync
committee index `135`. Sync committee index này ánh xạ tới `subcommittee_index`
`1` với vị trí `7` trong `BitVector` của contribution.

> 💡 Ghi chú: Với kích thước subcommittee 128: `135 // 128 = 1` (subcommittee
> index) và `135 % 128 = 7` (vị trí bit).

*Lưu ý*: Một validator **có thể được đưa vào nhiều lần** trong một subcommittee,
dẫn đến việc nhiều bit được bật cho cùng một `SyncCommitteeMessage`.

###### Signature

Đặt `contribution.signature = aggregate_signature`, trong đó
`aggregate_signature` có được bằng cách tập hợp các `BLSSignature` thích hợp từ
tập `sync_committee_messages` và dùng hàm `bls.Aggregate()` để tạo ra một
`BLSSignature` aggregate.

Tập signature đầu vào nên bao gồm một signature cho mỗi validator có bit được bật
trong bitfield `aggregation_bits`, với signature được lặp lại nếu một validator
ánh xạ tới nhiều index bên trong subcommittee.

##### Broadcast sync committee contribution

Nếu validator được chọn làm aggregator (`is_sync_committee_aggregator()`), họ sẽ
broadcast aggregate tốt nhất của mình dưới dạng `SignedContributionAndProof` tới
kênh aggregate toàn cục (topic `sync_committee_contribution_and_proof`) vào thời
điểm `get_slot_component_duration_ms(CONTRIBUTION_DUE_BPS)` mili giây kể từ đầu
slot.

Selection proof được cung cấp trong `ContributionAndProof` để chứng minh với kênh
gossip rằng validator đã được chọn làm aggregator.

Các message `ContributionAndProof` được aggregator ký và broadcast bên trong các
object `SignedContributionAndProof` để ngăn chặn một lớp tấn công DoS và việc giả
mạo message.

Đầu tiên,
`contribution_and_proof = get_contribution_and_proof(state, validator_index, contribution, privkey)`
được xây dựng.

```python
def get_contribution_and_proof(
    state: BeaconState,
    aggregator_index: ValidatorIndex,
    contribution: SyncCommitteeContribution,
    privkey: int,
) -> ContributionAndProof:
    selection_proof = get_sync_committee_selection_proof(
        state,
        contribution.slot,
        contribution.subcommittee_index,
        privkey,
    )
    return ContributionAndProof(
        aggregator_index=aggregator_index,
        contribution=contribution,
        selection_proof=selection_proof,
    )
```

Sau đó
`signed_contribution_and_proof = SignedContributionAndProof(message=contribution_and_proof, signature=signature)`
được xây dựng và broadcast, trong đó `signature` có được từ:

```python
def get_contribution_and_proof_signature(
    state: BeaconState, contribution_and_proof: ContributionAndProof, privkey: int
) -> BLSSignature:
    contribution = contribution_and_proof.contribution
    domain = get_domain(
        state, DOMAIN_CONTRIBUTION_AND_PROOF, compute_epoch_at_slot(contribution.slot)
    )
    signing_root = compute_signing_root(contribution_and_proof, domain)
    return bls.Sign(privkey, signing_root)
```

## Sync committee subnet stability

Các subnet của sync committee cần được chăm sóc đặc biệt để đảm bảo tính ổn định,
vì số lượng validator tham gia sync committee tại mỗi thời điểm tương đối nhỏ. Để
đảm bảo sự ổn định này, validator phải thực hiện những việc sau:

- Duy trì việc quảng bá (advertise) subnet mà validator trong sync committee được
  phân công trong ENR của node mình, ngay khi họ đã tham gia subnet đó. Việc phân
  công subnet được biết trước `EPOCHS_PER_SYNC_COMMITTEE_PERIOD` epoch và có thể
  được tính bằng `compute_subnets_for_sync_committee` đã định nghĩa ở trên. Việc
  quảng bá qua ENR được thể hiện bằng cách bật (các) bit thích hợp trong bitfield
  nằm dưới key `syncnets` của ENR, tương ứng với (các) `subnet_id` đã suy ra. Mọi
  bit đã được bật vì nhiệm vụ sync committee sẽ được tắt trong ENR khi node không
  còn validator nào trong subcommittee đó.

  *Lưu ý*: Sync committee đầu tiên khi chuyển từ phase 0 sang bản nâng cấp Altair
  sẽ không được biết cho đến khi nâng cấp diễn ra, nghĩa là việc phân công subnet
  cũng không được biết cho đến lúc đó. Các thành viên sync committee đầu tiên nên
  lắng nghe việc subscribe topic từ các peer và dùng discovery thông qua các quảng
  bá ENR gần ranh giới fork để hình thành các subnet ban đầu. Một số reward của
  sync committee ban đầu có thể bị bỏ lỡ trong khi các subnet ban đầu đang hình
  thành.

- Để tham gia một subnet của sync committee, chọn ngẫu nhiên một số epoch trước
  khi kết thúc sync committee period hiện tại, nằm trong khoảng từ 1 đến
  `SYNC_COMMITTEE_SUBNET_COUNT` (bao gồm cả hai đầu). Validator nên tham gia subnet
  của mình vào đầu epoch đã được chọn ngẫu nhiên đó. Ví dụ, nếu sync committee
  period tiếp theo bắt đầu ở epoch `853,248` và validator chọn ngẫu nhiên độ lệch
  `3`, họ nên tham gia subnet vào đầu epoch `853,245`. Validator nên tận dụng
  khoảng thời gian lookahead của việc phân công sync committee để có thể tham gia
  các subnet thích hợp trước sync committee period được phân công.
