# Phase 0 -- The Beacon Chain

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Notation](#notation)
- [Types](#types)
  - [`AggregationBits`](#aggregationbits)
  - [`Attestations`](#attestations)
  - [`AttesterSlashings`](#attesterslashings)
  - [`AttestingIndices`](#attestingindices)
  - [`Balances`](#balances)
  - [`BlockRoots`](#blockroots)
  - [`BLSPubkey`](#blspubkey)
  - [`BLSSignature`](#blssignature)
  - [`CommitteeIndex`](#committeeindex)
  - [`DepositDataList`](#depositdatalist)
  - [`DepositProof`](#depositproof)
  - [`Deposits`](#deposits)
  - [`Domain`](#domain)
  - [`DomainType`](#domaintype)
  - [`Epoch`](#epoch)
  - [`Eth1DataVotes`](#eth1datavotes)
  - [`ForkDigest`](#forkdigest)
  - [`Gwei`](#gwei)
  - [`Hash32`](#hash32)
  - [`HistoricalRoots`](#historicalroots)
  - [`JustificationBits`](#justificationbits)
  - [`PendingAttestations`](#pendingattestations)
  - [`ProposerSlashings`](#proposerslashings)
  - [`RandaoMixes`](#randaomixes)
  - [`Root`](#root)
  - [`Slashings`](#slashings)
  - [`Slot`](#slot)
  - [`StateRoots`](#stateroots)
  - [`ValidatorIndex`](#validatorindex)
  - [`Validators`](#validators)
  - [`Version`](#version)
  - [`VoluntaryExits`](#voluntaryexits)
- [Constants](#constants)
  - [Misc](#misc)
  - [Withdrawal prefixes](#withdrawal-prefixes)
  - [Domains](#domains)
- [Presets](#presets)
  - [Misc](#misc-1)
  - [Gwei values](#gwei-values)
  - [Time parameters](#time-parameters)
  - [State list lengths](#state-list-lengths)
  - [Rewards and penalties](#rewards-and-penalties)
  - [Max operations per block](#max-operations-per-block)
- [Configs](#configs)
  - [Genesis settings](#genesis-settings)
  - [Time parameters](#time-parameters-1)
  - [Validator cycle](#validator-cycle)
- [Containers](#containers)
  - [Misc dependencies](#misc-dependencies)
    - [`Fork`](#fork)
    - [`ForkData`](#forkdata)
    - [`Checkpoint`](#checkpoint)
    - [`Validator`](#validator)
    - [`AttestationData`](#attestationdata)
    - [`IndexedAttestation`](#indexedattestation)
    - [`PendingAttestation`](#pendingattestation)
    - [`Eth1Data`](#eth1data)
    - [`HistoricalBatch`](#historicalbatch)
    - [`DepositMessage`](#depositmessage)
    - [`DepositData`](#depositdata)
    - [`BeaconBlockHeader`](#beaconblockheader)
    - [`SigningData`](#signingdata)
  - [Beacon operations](#beacon-operations)
    - [`ProposerSlashing`](#proposerslashing)
    - [`AttesterSlashing`](#attesterslashing)
    - [`Attestation`](#attestation)
    - [`Deposit`](#deposit)
    - [`VoluntaryExit`](#voluntaryexit)
  - [Beacon blocks](#beacon-blocks)
    - [`BeaconBlockBody`](#beaconblockbody)
    - [`BeaconBlock`](#beaconblock)
  - [Beacon state](#beacon-state)
    - [`BeaconState`](#beaconstate)
  - [Signed envelopes](#signed-envelopes)
    - [`SignedVoluntaryExit`](#signedvoluntaryexit)
    - [`SignedBeaconBlock`](#signedbeaconblock)
    - [`SignedBeaconBlockHeader`](#signedbeaconblockheader)
- [Helpers](#helpers)
  - [Math](#math)
    - [`get_set_bit_count`](#get_set_bit_count)
    - [`integer_squareroot`](#integer_squareroot)
    - [`xor`](#xor)
    - [`uint_to_bytes`](#uint_to_bytes)
    - [`bytes_to_uint64`](#bytes_to_uint64)
    - [`saturating_sub`](#saturating_sub)
  - [Crypto](#crypto)
    - [`sha256`](#sha256)
    - [`hash_tree_root`](#hash_tree_root)
    - [BLS signatures](#bls-signatures)
  - [Predicates](#predicates)
    - [`is_active_validator`](#is_active_validator)
    - [`is_eligible_for_activation_queue`](#is_eligible_for_activation_queue)
    - [`is_eligible_for_activation`](#is_eligible_for_activation)
    - [`is_slashable_validator`](#is_slashable_validator)
    - [`is_slashable_attestation_data`](#is_slashable_attestation_data)
    - [`is_valid_indexed_attestation`](#is_valid_indexed_attestation)
    - [`compute_merkle_branch_root`](#compute_merkle_branch_root)
    - [`is_valid_merkle_branch`](#is_valid_merkle_branch)
  - [Misc](#misc-2)
    - [`compute_shuffled_permutation`](#compute_shuffled_permutation)
    - [`compute_shuffled_index`](#compute_shuffled_index)
    - [`compute_proposer_index`](#compute_proposer_index)
    - [`compute_committee`](#compute_committee)
    - [`compute_time_at_slot`](#compute_time_at_slot)
    - [`compute_slot_at_time`](#compute_slot_at_time)
    - [`compute_time_at_slot_ms`](#compute_time_at_slot_ms)
    - [`compute_slot_at_time_ms`](#compute_slot_at_time_ms)
    - [`compute_epoch_at_slot`](#compute_epoch_at_slot)
    - [`compute_start_slot_at_epoch`](#compute_start_slot_at_epoch)
    - [`compute_activation_exit_epoch`](#compute_activation_exit_epoch)
    - [`compute_fork_data_root`](#compute_fork_data_root)
    - [`compute_domain`](#compute_domain)
    - [`compute_signing_root`](#compute_signing_root)
  - [Beacon state accessors](#beacon-state-accessors)
    - [`get_current_epoch`](#get_current_epoch)
    - [`get_previous_epoch`](#get_previous_epoch)
    - [`get_block_root`](#get_block_root)
    - [`get_block_root_at_slot`](#get_block_root_at_slot)
    - [`get_randao_mix`](#get_randao_mix)
    - [`get_active_validator_indices`](#get_active_validator_indices)
    - [`get_validator_churn_limit`](#get_validator_churn_limit)
    - [`get_seed`](#get_seed)
    - [`get_committee_count_per_slot`](#get_committee_count_per_slot)
    - [`get_beacon_committee`](#get_beacon_committee)
    - [`get_beacon_proposer_index`](#get_beacon_proposer_index)
    - [`get_total_balance`](#get_total_balance)
    - [`get_total_active_balance`](#get_total_active_balance)
    - [`get_domain`](#get_domain)
    - [`get_indexed_attestation`](#get_indexed_attestation)
    - [`get_attesting_indices`](#get_attesting_indices)
    - [`get_pending_attesting_indices`](#get_pending_attesting_indices)
  - [Beacon state mutators](#beacon-state-mutators)
    - [`increase_balance`](#increase_balance)
    - [`decrease_balance`](#decrease_balance)
    - [`initiate_validator_exit`](#initiate_validator_exit)
    - [`slash_validator`](#slash_validator)
- [Genesis](#genesis)
  - [Genesis state](#genesis-state)
  - [Genesis block](#genesis-block)
- [Beacon chain state transition function](#beacon-chain-state-transition-function)
  - [Epoch processing](#epoch-processing)
    - [Helpers](#helpers-1)
    - [Justification and finalization](#justification-and-finalization)
    - [Rewards and penalties](#rewards-and-penalties-1)
      - [Helpers](#helpers-2)
      - [Components of attestation deltas](#components-of-attestation-deltas)
      - [`get_attestation_deltas`](#get_attestation_deltas)
      - [`process_rewards_and_penalties`](#process_rewards_and_penalties)
    - [Registry updates](#registry-updates)
    - [Slashings](#slashings)
    - [Eth1 data votes updates](#eth1-data-votes-updates)
    - [Effective balances updates](#effective-balances-updates)
    - [Slashings balances updates](#slashings-balances-updates)
    - [Randao mixes updates](#randao-mixes-updates)
    - [Historical roots updates](#historical-roots-updates)
    - [Participation records rotation](#participation-records-rotation)
  - [Block processing](#block-processing)
    - [Block header](#block-header)
    - [RANDAO](#randao)
    - [Eth1 data](#eth1-data)
    - [Operations](#operations)
      - [Proposer slashings](#proposer-slashings)
      - [Attester slashings](#attester-slashings)
      - [Attestations](#attestations)
      - [Deposits](#deposits)
      - [Voluntary exits](#voluntary-exits)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này là đặc tả (spec) cho Phase 0 -- Beacon Chain.

Cốt lõi của proof-of-stake trên Ethereum là một chuỗi hệ thống gọi là "beacon
chain". Beacon chain lưu trữ và quản lý registry (sổ đăng ký) của các validator.
Trong các giai đoạn triển khai ban đầu của proof-of-stake, cách duy nhất để trở
thành validator là gửi một giao dịch ETH một chiều (không thể rút lại ngay) vào
deposit contract trên chuỗi proof-of-work của Ethereum. Một validator được kích
hoạt khi: các biên nhận deposit đã được beacon chain xử lý, balance đạt mức kích
hoạt, và validator đã đi hết hàng đợi kích hoạt. Việc exit (rời khỏi tập
validator) có thể là tự nguyện, hoặc bị cưỡng chế như một hình phạt cho hành vi
sai trái. Nguồn tải chính trên beacon chain là các "attestation". Mỗi
attestation đồng thời là phiếu bầu xác nhận tính sẵn có (availability) cho một
shard block (trong một bản nâng cấp sau này) và là phiếu bầu proof-of-stake cho
một beacon block (Phase 0).

## Notation

Các đoạn code xuất hiện theo `kiểu này` được hiểu là code Python 3.

## Types

Chúng ta định nghĩa các kiểu Python tùy biến sau đây để phục vụ type hinting và
giúp code dễ đọc hơn:

### `AggregationBits`

*(Các bit tham gia của một committee: mỗi thành viên ứng với một bit, theo đúng thứ tự trong committee.)*

```python
class AggregationBits(BitList):
    """
    The participation bits of a single committee, one bit per member in
    committee order.
    """

    LIMIT = MAX_VALIDATORS_PER_COMMITTEE
```

### `Attestations`

*(Danh sách các attestation được đưa vào một beacon block.)*

```python
class Attestations(List[Attestation]):
    """
    The attestations included in a beacon block.
    """

    LIMIT = MAX_ATTESTATIONS
```

### `AttesterSlashings`

*(Danh sách các attester slashing được đưa vào một beacon block.)*

```python
class AttesterSlashings(List[AttesterSlashing]):
    """
    The attester slashings included in a beacon block.
    """

    LIMIT = MAX_ATTESTER_SLASHINGS
```

### `AttestingIndices`

*(Danh sách index của các validator tham gia một attestation.)*

```python
class AttestingIndices(List[ValidatorIndex]):
    """
    The indices of the validators participating in an attestation.
    """

    LIMIT = MAX_VALIDATORS_PER_COMMITTEE
```

### `Balances`

*(Balance của tất cả validator.)*

```python
class Balances(List[Gwei]):
    """
    The balances of all validators.
    """

    LIMIT = VALIDATOR_REGISTRY_LIMIT
```

### `BlockRoots`

*(Cửa sổ trượt chứa các block root gần đây, được đánh index theo `slot % SLOTS_PER_HISTORICAL_ROOT` — tức là dùng như bộ đệm vòng, giá trị mới ghi đè giá trị cũ.)*

```python
class BlockRoots(Vector[Root]):
    """
    A rolling window of recent block roots, indexed by slot modulo
    ``SLOTS_PER_HISTORICAL_ROOT``.
    """

    LENGTH = SLOTS_PER_HISTORICAL_ROOT
```

### `BLSPubkey`

*(Public key BLS12-381, là một điểm nén trong nhóm `G1`.)*

```python
class BLSPubkey(Bytes48):
    """
    A BLS12-381 public key, a compressed point in the ``G1`` group.
    """
```

### `BLSSignature`

*(Signature BLS12-381, là một điểm nén trong nhóm `G2`.)*

```python
class BLSSignature(Bytes96):
    """
    A BLS12-381 signature, a compressed point in the ``G2`` group.
    """
```

### `CommitteeIndex`

*(Index của một committee trong phạm vi một slot.)*

```python
class CommitteeIndex(Uint64):
    """
    The index of a committee within a slot.
    """
```

### `DepositDataList`

*(Danh sách `DepositData` của các deposit đã gửi vào deposit contract.)*

```python
class DepositDataList(List[DepositData]):
    """
    The ``DepositData`` of deposits made to the deposit contract.
    """

    LIMIT = 2**DEPOSIT_CONTRACT_TREE_DEPTH
```

### `DepositProof`

*(Merkle proof cho một deposit trong cây của deposit contract. Phần tử thêm vào ngoài độ sâu của cây dùng cho việc mix-in số lượng deposit.)*

```python
class DepositProof(Vector[Bytes32]):
    """
    A Merkle proof of a deposit in the deposit contract's tree. The node
    beyond the tree depth accounts for the deposit count mix-in.
    """

    LENGTH = DEPOSIT_CONTRACT_TREE_DEPTH + 1
```

### `Deposits`

*(Danh sách các deposit được đưa vào một beacon block.)*

```python
class Deposits(List[Deposit]):
    """
    The deposits included in a beacon block.
    """

    LIMIT = MAX_DEPOSITS
```

### `Domain`

*(Một signature domain — giá trị dùng để phân tách ngữ cảnh ký, tránh việc một chữ ký hợp lệ ở ngữ cảnh này bị tái sử dụng ở ngữ cảnh khác.)*

```python
class Domain(Bytes32):
    """
    A signature domain.
    """
```

### `DomainType`

*(Loại signature domain, xác định loại message đang được ký.)*

```python
class DomainType(Bytes4):
    """
    A signature domain type, identifying the kind of message being signed.
    """
```

### `Epoch`

*(Số thứ tự epoch. Một epoch kéo dài `SLOTS_PER_EPOCH` slot.)*

```python
class Epoch(Uint64):
    """
    An epoch number. An epoch is a span of ``SLOTS_PER_EPOCH`` slots.
    """
```

### `Eth1DataVotes`

*(Các phiếu bầu `Eth1Data` trong voting period hiện tại.)*

```python
class Eth1DataVotes(List[Eth1Data]):
    """
    The ``Eth1Data`` votes of the current voting period.
    """

    LIMIT = Uint64(EPOCHS_PER_ETH1_VOTING_PERIOD) * Uint64(SLOTS_PER_EPOCH)
```

### `ForkDigest`

*(Bản digest ngắn của dữ liệu fork hiện tại.)*

```python
class ForkDigest(Bytes4):
    """
    A short digest of the current fork data.
    """
```

### `Gwei`

*(Một lượng tính bằng Gwei — đơn vị nhỏ nhất của Ether trên beacon chain. 1 Ether = `10**9` Gwei, 1 Gwei = `10**9` Wei.)*

```python
class Gwei(Uint64):
    """
    An amount in Gwei, the smallest unit of Ether on the beacon chain. One
    Ether is equal to ``10**9`` Gwei, and one Gwei is equal to ``10**9`` Wei.
    """
```

### `Hash32`

*(Một hash 256-bit không phải Merkle root, ví dụ hash của một block thuộc execution layer.)*

```python
class Hash32(Bytes32):
    """
    A 256-bit hash that is not a Merkle root, like the hash of an
    execution-layer block.
    """
```

### `HistoricalRoots`

*(Danh sách root của các object `HistoricalBatch`.)*

```python
class HistoricalRoots(List[Root]):
    """
    The roots of ``HistoricalBatch`` objects.
    """

    LIMIT = HISTORICAL_ROOTS_LIMIT
```

### `JustificationBits`

*(Trạng thái justification của `JUSTIFICATION_BITS_LENGTH` epoch gần nhất.)*

```python
class JustificationBits(BitVector):
    """
    The justification status of the last ``JUSTIFICATION_BITS_LENGTH`` epochs.
    """

    LENGTH = JUSTIFICATION_BITS_LENGTH
```

### `PendingAttestations`

*(Các attestation đã được đưa vào block trong một epoch.)*

```python
class PendingAttestations(List[PendingAttestation]):
    """
    The attestations included in blocks during an epoch.
    """

    LIMIT = MAX_ATTESTATIONS * SLOTS_PER_EPOCH
```

### `ProposerSlashings`

*(Danh sách các proposer slashing được đưa vào một beacon block.)*

```python
class ProposerSlashings(List[ProposerSlashing]):
    """
    The proposer slashings included in a beacon block.
    """

    LIMIT = MAX_PROPOSER_SLASHINGS
```

### `RandaoMixes`

*(Cửa sổ trượt chứa các RANDAO mix tích lũy, được đánh index theo `epoch % EPOCHS_PER_HISTORICAL_VECTOR`.)*

```python
class RandaoMixes(Vector[Bytes32]):
    """
    A rolling window of accumulated RANDAO mixes, indexed by epoch modulo
    ``EPOCHS_PER_HISTORICAL_VECTOR``.
    """

    LENGTH = EPOCHS_PER_HISTORICAL_VECTOR
```

### `Root`

*(Một Merkle root, thường là hash tree root của một object SSZ.)*

```python
class Root(Bytes32):
    """
    A Merkle root, usually the hash tree root of an SSZ object.
    """
```

### `Slashings`

*(Tổng effective balance bị slash theo từng epoch, được đánh index theo `epoch % EPOCHS_PER_SLASHINGS_VECTOR`.)*

```python
class Slashings(Vector[Gwei]):
    """
    Per-epoch sums of slashed effective balances, indexed by epoch modulo
    ``EPOCHS_PER_SLASHINGS_VECTOR``.
    """

    LENGTH = EPOCHS_PER_SLASHINGS_VECTOR
```

### `Slot`

*(Số thứ tự slot. Thời gian được chia thành các slot có độ dài cố định.)*

```python
class Slot(Uint64):
    """
    A slot number. Time is divided into fixed-length slots.
    """
```

### `StateRoots`

*(Cửa sổ trượt chứa các state root gần đây, được đánh index theo `slot % SLOTS_PER_HISTORICAL_ROOT`.)*

```python
class StateRoots(Vector[Root]):
    """
    A rolling window of recent state roots, indexed by slot modulo
    ``SLOTS_PER_HISTORICAL_ROOT``.
    """

    LENGTH = SLOTS_PER_HISTORICAL_ROOT
```

### `ValidatorIndex`

*(Index của một validator trong validator registry.)*

```python
class ValidatorIndex(Uint64):
    """
    The index of a validator in the validator registry.
    """
```

### `Validators`

*(Validator registry — danh sách toàn bộ validator.)*

```python
class Validators(List[Validator]):
    """
    The validator registry.
    """

    LIMIT = VALIDATOR_REGISTRY_LIMIT
```

### `Version`

*(Số phiên bản fork.)*

```python
class Version(Bytes4):
    """
    A fork version number.
    """
```

### `VoluntaryExits`

*(Danh sách các voluntary exit (đã ký) được đưa vào một beacon block.)*

```python
class VoluntaryExits(List[SignedVoluntaryExit]):
    """
    The signed voluntary exits included in a beacon block.
    """

    LIMIT = MAX_VOLUNTARY_EXITS
```

## Constants

Các giá trị sau là hằng số (không thể cấu hình) được dùng xuyên suốt đặc tả.

### Misc

| Name                        | Value                |
| --------------------------- | -------------------- |
| `UINT64_MAX`                | `Uint64(2**64 - 1)`  |
| `UINT64_MAX_SQRT`           | `Uint64(4294967295)` |
| `GENESIS_SLOT`              | `Slot(0)`            |
| `GENESIS_EPOCH`             | `Epoch(0)`           |
| `FAR_FUTURE_EPOCH`          | `Epoch(2**64 - 1)`   |
| `BASE_REWARDS_PER_EPOCH`    | `Uint64(4)`          |
| `JUSTIFICATION_BITS_LENGTH` | `Uint64(4)`          |
| `ENDIANNESS`                | `"little"`           |

### Withdrawal prefixes

| Name                             | Value            |
| -------------------------------- | ---------------- |
| `BLS_WITHDRAWAL_PREFIX`          | `Bytes1("0x00")` |
| `ETH1_ADDRESS_WITHDRAWAL_PREFIX` | `Bytes1("0x01")` |

### Domains

| Name                         | Value                      |
| ---------------------------- | -------------------------- |
| `DOMAIN_BEACON_PROPOSER`     | `DomainType("0x00000000")` |
| `DOMAIN_BEACON_ATTESTER`     | `DomainType("0x01000000")` |
| `DOMAIN_RANDAO`              | `DomainType("0x02000000")` |
| `DOMAIN_DEPOSIT`             | `DomainType("0x03000000")` |
| `DOMAIN_VOLUNTARY_EXIT`      | `DomainType("0x04000000")` |
| `DOMAIN_SELECTION_PROOF`     | `DomainType("0x05000000")` |
| `DOMAIN_AGGREGATE_AND_PROOF` | `DomainType("0x06000000")` |
| `DOMAIN_APPLICATION_MASK`    | `DomainType("0x00000001")` |

*Lưu ý*: `DOMAIN_APPLICATION_MASK` dành riêng phần còn lại của không gian bit
trong `DomainType` cho mục đích ứng dụng (application). Điều này có nghĩa là với
một `DomainType` ứng dụng nào đó, ví dụ `DOMAIN_SOME_APPLICATION`, thì biểu thức
`DOMAIN_SOME_APPLICATION & DOMAIN_APPLICATION_MASK` **MUST** (BẮT BUỘC) khác 0.
Ngược lại, với mọi `DomainType` khác trong các đặc tả consensus-layer, biểu thức
này **MUST** (BẮT BUỘC) bằng 0.

> 💡 Ghi chú: Nói cách khác, bit được `DOMAIN_APPLICATION_MASK` đánh dấu dùng để
> phân biệt domain của ứng dụng bên ngoài với domain của chính giao thức
> consensus, nhờ đó chữ ký của ứng dụng không bao giờ trùng ngữ cảnh với chữ ký
> của giao thức.

## Presets

*Lưu ý*: Cấu hình bên dưới được đóng gói thành một preset: tức là một bộ biến cấu
hình được kỳ vọng sẽ khác nhau giữa các chế độ vận hành (ví dụ: testing), nhưng
thường không khác nhau giữa các network.

### Misc

| Name                             | Value                     |
| -------------------------------- | ------------------------- |
| `MAX_COMMITTEES_PER_SLOT`        | `Uint64(2**6)` (= 64)     |
| `TARGET_COMMITTEE_SIZE`          | `Uint64(2**7)` (= 128)    |
| `MAX_VALIDATORS_PER_COMMITTEE`   | `Uint64(2**11)` (= 2,048) |
| `SHUFFLE_ROUND_COUNT`            | `Uint64(90)`              |
| `HYSTERESIS_QUOTIENT`            | `Uint64(4)`               |
| `HYSTERESIS_DOWNWARD_MULTIPLIER` | `Uint64(1)`               |
| `HYSTERESIS_UPWARD_MULTIPLIER`   | `Uint64(5)`               |

- Để đảm bảo an toàn cho các committee, `TARGET_COMMITTEE_SIZE` được đặt lớn hơn
  [kích thước committee tối thiểu được khuyến nghị là 111](http://web.archive.org/web/20190504131341/https://vitalik.ca/files/Ithaca201807_Sharding.pdf);
  khi có đủ validator đang hoạt động (ít nhất
  `SLOTS_PER_EPOCH * TARGET_COMMITTEE_SIZE`), thuật toán shuffling đảm bảo kích
  thước mỗi committee tối thiểu là `TARGET_COMMITTEE_SIZE`. (Nguồn ngẫu nhiên
  không thể bị thao túng (unbiasable) dựa trên Verifiable Delay Function (VDF) sẽ
  giúp committee vững chắc hơn và cho phép hạ kích thước committee tối thiểu an
  toàn.)

### Gwei values

| Name                          | Value                                   |
| ----------------------------- | --------------------------------------- |
| `MIN_DEPOSIT_AMOUNT`          | `Gwei(2**0 * 10**9)` (= 1,000,000,000)  |
| `MAX_EFFECTIVE_BALANCE`       | `Gwei(2**5 * 10**9)` (= 32,000,000,000) |
| `EFFECTIVE_BALANCE_INCREMENT` | `Gwei(2**0 * 10**9)` (= 1,000,000,000)  |

### Time parameters

| Name                               | Value                   |
| ---------------------------------- | ----------------------- |
| `MIN_ATTESTATION_INCLUSION_DELAY`  | `Slot(2**0)` (= 1)      |
| `SLOTS_PER_EPOCH`                  | `Slot(2**5)` (= 32)     |
| `MIN_SEED_LOOKAHEAD`               | `Epoch(2**0)` (= 1)     |
| `MAX_SEED_LOOKAHEAD`               | `Epoch(2**2)` (= 4)     |
| `MIN_EPOCHS_TO_INACTIVITY_PENALTY` | `Epoch(2**2)` (= 4)     |
| `EPOCHS_PER_ETH1_VOTING_PERIOD`    | `Epoch(2**6)` (= 64)    |
| `SLOTS_PER_HISTORICAL_ROOT`        | `Slot(2**13)` (= 8,192) |

### State list lengths

| Name                           | Value                                 |
| ------------------------------ | ------------------------------------- |
| `EPOCHS_PER_HISTORICAL_VECTOR` | `Epoch(2**16)` (= 65,536)             |
| `EPOCHS_PER_SLASHINGS_VECTOR`  | `Epoch(2**13)` (= 8,192)              |
| `HISTORICAL_ROOTS_LIMIT`       | `Uint64(2**24)` (= 16,777,216)        |
| `VALIDATOR_REGISTRY_LIMIT`     | `Uint64(2**40)` (= 1,099,511,627,776) |

### Rewards and penalties

| Name                               | Value                          |
| ---------------------------------- | ------------------------------ |
| `BASE_REWARD_FACTOR`               | `Uint64(2**6)` (= 64)          |
| `WHISTLEBLOWER_REWARD_QUOTIENT`    | `Uint64(2**9)` (= 512)         |
| `PROPOSER_REWARD_QUOTIENT`         | `Uint64(2**3)` (= 8)           |
| `INACTIVITY_PENALTY_QUOTIENT`      | `Uint64(2**26)` (= 67,108,864) |
| `MIN_SLASHING_PENALTY_QUOTIENT`    | `Uint64(2**7)` (= 128)         |
| `PROPORTIONAL_SLASHING_MULTIPLIER` | `Uint64(1)`                    |

- `INACTIVITY_PENALTY_QUOTIENT` bằng `INVERSE_SQRT_E_DROP_TIME**2`, trong đó
  `INVERSE_SQRT_E_DROP_TIME := 2**13` epoch là khoảng thời gian cần thiết để
  inactivity penalty làm balance của các validator không tham gia giảm xuống còn
  khoảng `1/sqrt(e) ~= 60.6%`. Thật vậy, balance còn lại của một validator
  offline sau `n` epoch xấp xỉ
  `(1 - 1/INACTIVITY_PENALTY_QUOTIENT)**(n**2/2)`; do đó sau
  `INVERSE_SQRT_E_DROP_TIME` epoch, giá trị này xấp xỉ
  `(1 - 1/INACTIVITY_PENALTY_QUOTIENT)**(INACTIVITY_PENALTY_QUOTIENT/2) ~= 1/sqrt(e)`.
  Lưu ý giá trị này sẽ được nâng cấp thành `2**24` sau khi mainnet Phase 0 ổn
  định, nhằm giúp khôi phục nhanh hơn khi xảy ra inactivity leak (tình trạng
  chain không finalize được và validator offline bị trừ dần balance).

- `PROPORTIONAL_SLASHING_MULTIPLIER` được đặt bằng `1` khi mainnet mới ra mắt,
  dẫn đến biên an toàn có thể quy trách nhiệm (accountable safety margin) tối
  thiểu chỉ bằng một phần ba khi xảy ra tấn công vào finality. Sau khi mainnet
  Phase 0 ổn định, giá trị này sẽ được nâng lên `3` để đạt biên an toàn có thể
  quy trách nhiệm tối thiểu ở mức tối đa.

> 💡 Ghi chú: Ý tưởng là khi có từ 1/3 tổng stake cùng vi phạm (mức cần thiết để
> tấn công finality), hệ số `3` sẽ khiến các validator vi phạm bị slash toàn bộ
> balance; với hệ số `1`, họ chỉ mất khoảng một phần ba.

### Max operations per block

| Name                     | Value                  |
| ------------------------ | ---------------------- |
| `MAX_PROPOSER_SLASHINGS` | `Uint64(2**4)` (= 16)  |
| `MAX_ATTESTER_SLASHINGS` | `Uint64(2**1)` (= 2)   |
| `MAX_ATTESTATIONS`       | `Uint64(2**7)` (= 128) |
| `MAX_DEPOSITS`           | `Uint64(2**4)` (= 16)  |
| `MAX_VOLUNTARY_EXITS`    | `Uint64(2**4)` (= 16)  |

## Configs

*Lưu ý*: Các giá trị cấu hình mặc định của mainnet được liệt kê ở đây chỉ nhằm
mục đích minh họa. Giá trị mặc định cho loại cấu hình linh động hơn này có sẵn
trong các preset. Testnet và các loại chain instance khác có thể dùng cấu hình
khác.

> 💡 Ghi chú: Preset được cố định khi biên dịch (compile-time), còn config có thể
> thay đổi lúc chạy (runtime) tùy theo network.

### Genesis settings

| Name                                 | Value                                        |
| ------------------------------------ | -------------------------------------------- |
| `MIN_GENESIS_ACTIVE_VALIDATOR_COUNT` | `Uint64(2**14)` (= 16,384)                   |
| `MIN_GENESIS_TIME`                   | `Uint64(1606824000)` (Dec 1, 2020, 12pm UTC) |
| `GENESIS_FORK_VERSION`               | `Version("0x00000000")`                      |
| `GENESIS_DELAY`                      | `Uint64(604800)` (7 days)                    |

### Time parameters

| Name                                  | Value                     |
| ------------------------------------- | ------------------------- |
| `SLOT_DURATION_MS`                    | `Uint64(12000)`           |
| `SECONDS_PER_ETH1_BLOCK`              | `Uint64(14)`              |
| `MIN_VALIDATOR_WITHDRAWABILITY_DELAY` | `Epoch(2**8)` (= 256)     |
| `SHARD_COMMITTEE_PERIOD`              | `Epoch(2**8)` (= 256)     |
| `ETH1_FOLLOW_DISTANCE`                | `Uint64(2**11)` (= 2,048) |

### Validator cycle

| Name                        | Value                                   |
| --------------------------- | --------------------------------------- |
| `EJECTION_BALANCE`          | `Gwei(2**4 * 10**9)` (= 16,000,000,000) |
| `MIN_PER_EPOCH_CHURN_LIMIT` | `Uint64(2**2)` (= 4)                    |
| `CHURN_LIMIT_QUOTIENT`      | `Uint64(2**16)` (= 65,536)              |

## Containers

Các kiểu sau đây là container
[SimpleSerialize (SSZ)](https://github.com/ethereum/ssz-specs).

*Lưu ý*: Các định nghĩa được sắp xếp theo thứ tự topo (kiểu nào được dùng thì
được định nghĩa trước) để thuận tiện cho việc thực thi đặc tả.

*Lưu ý*: Những field bị bỏ trống khi khởi tạo container sẽ nhận giá trị mặc định
là giá trị zero của kiểu tương ứng.

### Misc dependencies

#### `Fork`

```python
class Fork(Container):
    previous_version: Version
    current_version: Version
    epoch: Epoch
```

#### `ForkData`

```python
class ForkData(Container):
    current_version: Version
    genesis_validators_root: Root
```

#### `Checkpoint`

```python
class Checkpoint(Container):
    epoch: Epoch
    root: Root
```

#### `Validator`

```python
class Validator(Container):
    pubkey: BLSPubkey
    withdrawal_credentials: Bytes32
    effective_balance: Gwei
    slashed: Boolean
    activation_eligibility_epoch: Epoch
    activation_epoch: Epoch
    exit_epoch: Epoch
    withdrawable_epoch: Epoch
```

#### `AttestationData`

```python
class AttestationData(Container):
    slot: Slot
    index: CommitteeIndex
    beacon_block_root: Root
    source: Checkpoint
    target: Checkpoint
```

#### `IndexedAttestation`

```python
class IndexedAttestation(Container):
    attesting_indices: AttestingIndices
    data: AttestationData
    signature: BLSSignature
```

#### `PendingAttestation`

```python
class PendingAttestation(Container):
    aggregation_bits: AggregationBits
    data: AttestationData
    inclusion_delay: Slot
    proposer_index: ValidatorIndex
```

#### `Eth1Data`

```python
class Eth1Data(Container):
    deposit_root: Root
    deposit_count: Uint64
    block_hash: Hash32
```

#### `HistoricalBatch`

```python
class HistoricalBatch(Container):
    block_roots: BlockRoots
    state_roots: StateRoots
```

#### `DepositMessage`

```python
class DepositMessage(Container):
    pubkey: BLSPubkey
    withdrawal_credentials: Bytes32
    amount: Gwei
```

#### `DepositData`

*Lưu ý*: `signature` là chữ ký trên `DepositMessage` (tức là ký lên các field
`pubkey`, `withdrawal_credentials`, `amount`, không bao gồm chính `signature`).

```python
class DepositData(Container):
    pubkey: BLSPubkey
    withdrawal_credentials: Bytes32
    amount: Gwei
    signature: BLSSignature
```

#### `BeaconBlockHeader`

```python
class BeaconBlockHeader(Container):
    slot: Slot
    proposer_index: ValidatorIndex
    parent_root: Root
    state_root: Root
    body_root: Root
```

#### `SigningData`

```python
class SigningData(Container):
    object_root: Root
    domain: Domain
```

### Beacon operations

#### `ProposerSlashing`

```python
class ProposerSlashing(Container):
    signed_header_1: SignedBeaconBlockHeader
    signed_header_2: SignedBeaconBlockHeader
```

#### `AttesterSlashing`

```python
class AttesterSlashing(Container):
    attestation_1: IndexedAttestation
    attestation_2: IndexedAttestation
```

#### `Attestation`

```python
class Attestation(Container):
    aggregation_bits: AggregationBits
    data: AttestationData
    signature: BLSSignature
```

#### `Deposit`

*Lưu ý*: `proof` là Merkle path (đường dẫn Merkle) dẫn tới deposit root.

```python
class Deposit(Container):
    proof: DepositProof
    data: DepositData
```

#### `VoluntaryExit`

```python
class VoluntaryExit(Container):
    epoch: Epoch
    validator_index: ValidatorIndex
```

### Beacon blocks

#### `BeaconBlockBody`

```python
class BeaconBlockBody(Container):
    randao_reveal: BLSSignature
    eth1_data: Eth1Data
    graffiti: Bytes32
    proposer_slashings: ProposerSlashings
    attester_slashings: AttesterSlashings
    attestations: Attestations
    deposits: Deposits
    voluntary_exits: VoluntaryExits
```

#### `BeaconBlock`

```python
class BeaconBlock(Container):
    slot: Slot
    proposer_index: ValidatorIndex
    parent_root: Root
    state_root: Root
    body: BeaconBlockBody
```

### Beacon state

#### `BeaconState`

```python
class BeaconState(Container):
    genesis_time: Uint64
    genesis_validators_root: Root
    slot: Slot
    fork: Fork
    latest_block_header: BeaconBlockHeader
    block_roots: BlockRoots
    state_roots: StateRoots
    historical_roots: HistoricalRoots
    eth1_data: Eth1Data
    eth1_data_votes: Eth1DataVotes
    eth1_deposit_index: Uint64
    validators: Validators
    balances: Balances
    randao_mixes: RandaoMixes
    slashings: Slashings
    previous_epoch_attestations: PendingAttestations
    current_epoch_attestations: PendingAttestations
    justification_bits: JustificationBits
    previous_justified_checkpoint: Checkpoint
    current_justified_checkpoint: Checkpoint
    finalized_checkpoint: Checkpoint
```

### Signed envelopes

#### `SignedVoluntaryExit`

```python
class SignedVoluntaryExit(Container):
    message: VoluntaryExit
    signature: BLSSignature
```

#### `SignedBeaconBlock`

```python
class SignedBeaconBlock(Container):
    message: BeaconBlock
    signature: BLSSignature
```

#### `SignedBeaconBlockHeader`

```python
class SignedBeaconBlockHeader(Container):
    message: BeaconBlockHeader
    signature: BLSSignature
```

## Helpers

*(Các hàm tiện ích dùng xuyên suốt spec)*

*Lưu ý*: Các định nghĩa dưới đây được viết nhằm mục đích đặc tả (để mô tả hành vi
một cách rõ ràng), không nhất thiết là cách cài đặt tối ưu. Client có thể cài đặt
khác (ví dụ dùng cache) miễn là cho ra cùng kết quả.

### Math

*(Các hàm toán học cơ bản)*

#### `get_set_bit_count`

Trả về số bit đang được bật (bằng `True`) trong `bits`.

```python
def get_set_bit_count(bits: Sequence[Boolean]) -> Uint64:
    """
    Return the number of bits that are set in ``bits``.
    """
    return Uint64(sum(1 for bit in bits if bit))
```

#### `integer_squareroot`

Trả về căn bậc hai nguyên của `n`, tức là số nguyên `x` lớn nhất thỏa mãn
`x**2 <= n`. Hàm dùng phương pháp Newton trên số nguyên, và xử lý riêng trường hợp
`n == UINT64_MAX` để tránh tràn số khi tính `x + 1`.

```python
def integer_squareroot(n: Uint64) -> Uint64:
    """
    Return the largest integer ``x`` such that ``x**2 <= n``.
    """
    if n == UINT64_MAX:
        return UINT64_MAX_SQRT
    x = n
    y = (x + 1) // 2
    while y < x:
        x = y
        y = (x + n // x) // 2
    return x
```

#### `xor`

Trả về kết quả phép XOR (exclusive-or) từng byte của hai chuỗi 32 byte.

```python
def xor(bytes_1: Bytes32, bytes_2: Bytes32) -> Bytes32:
    """
    Return the exclusive-or of two 32-byte strings.
    """
    return Bytes32(byte_1 ^ byte_2 for byte_1, byte_2 in zip(bytes_1, bytes_2, strict=True))
```

#### `uint_to_bytes`

Trả về dạng SSZ serialization của số nguyên không dấu `n` (kiểu `Uint`), tức là
biểu diễn little-endian với độ dài đúng bằng kích thước của kiểu đó.

```python
def uint_to_bytes(n: Uint) -> bytes:
    """
    Return the SSZ serialization of ``n``, a ``Uint``.
    """
    return ssz_serialize(n)
```

#### `bytes_to_uint64`

*Lưu ý*: `data` có thể ngắn hơn tám byte.

Hàm chuyển `data` thành số nguyên `Uint64` theo thứ tự byte `ENDIANNESS`
(little-endian).

```python
def bytes_to_uint64(data: bytes) -> Uint64:
    """
    Return the integer deserialization of ``data`` as a ``Uint64``.
    """
    return Uint64(int.from_bytes(data, ENDIANNESS))
```

#### `saturating_sub`

Trả về `a - b`, nhưng "bão hòa" tại 0: nếu `b >= a` thì kết quả là 0 thay vì bị
underflow (âm). Biểu thức `a - a` được dùng để trả về số 0 cùng kiểu với `a`.

```python
def saturating_sub(a: Uint64, b: int) -> Any:
    """
    Return ``a - b``, saturating at zero.
    """
    return a - b if a > b else a - a
```

### Crypto

*(Các hàm mật mã)*

#### `sha256`

Trả về hash SHA256 của `data`.

```python
def sha256(data: bytes) -> Bytes32:
    """
    Return the SHA256 hash of ``data``.
    """
    return Bytes32(sha256_hash(data).digest())
```

#### `hash_tree_root`

Các object được hash thành một root duy nhất bằng cách sử dụng cấu trúc cây hash
(hash tree, về bản chất là Merkle tree), như được định nghĩa trong
[SSZ specification](https://github.com/ethereum/ssz-specs).

```python
def hash_tree_root(object: SSZObject) -> Root:
    """
    Return the hash tree root of ``object``.
    """
    return Root(object.hash_tree_root())
```

#### BLS signatures

[IETF BLS signature draft standard v4](https://tools.ietf.org/html/draft-irtf-cfrg-bls-signature-04)
với ciphersuite `BLS_SIG_BLS12381G2_XMD:SHA-256_SSWU_RO_POP_` định nghĩa các hàm
sau:

- `def Sign(privkey: int, message: Bytes) -> BLSSignature`
- `def Verify(pubkey: BLSPubkey, message: Bytes, signature: BLSSignature) -> bool`
- `def Aggregate(signatures: Sequence[BLSSignature]) -> BLSSignature`
- `def FastAggregateVerify(pubkeys: Sequence[BLSPubkey], message: Bytes, signature: BLSSignature) -> bool`
- `def AggregateVerify(pubkeys: Sequence[BLSPubkey], messages: Sequence[Bytes], signature: BLSSignature) -> bool`
- `def KeyValidate(pubkey: BLSPubkey) -> bool`

Các hàm trên được truy cập thông qua module `bls`, ví dụ `bls.Verify`.

> 💡 Ghi chú: `Aggregate` gộp nhiều signature thành một signature duy nhất.
> `FastAggregateVerify` kiểm tra một signature gộp trong trường hợp tất cả public
> key cùng ký **một** message (đây là trường hợp của attestation), còn
> `AggregateVerify` dùng khi mỗi public key ký một message khác nhau.
> `KeyValidate` kiểm tra một public key có hợp lệ hay không. Hậu tố `POP` (proof of
> possession) trong tên ciphersuite cho biết lược đồ dựa trên việc chứng minh sở hữu
> private key để chống tấn công rogue-key.

### Predicates

*(Các hàm kiểm tra điều kiện, trả về `bool`)*

#### `is_active_validator`

Kiểm tra `validator` có đang active tại `epoch` hay không: validator active khi
`epoch` nằm trong khoảng `[activation_epoch, exit_epoch)`.

```python
def is_active_validator(validator: Validator, epoch: Epoch) -> bool:
    """
    Check if ``validator`` is active.
    """
    return validator.activation_epoch <= epoch < validator.exit_epoch
```

#### `is_eligible_for_activation_queue`

Kiểm tra `validator` có đủ điều kiện để được đưa vào hàng đợi kích hoạt (activation
queue) hay không: validator chưa từng được đánh dấu đủ điều kiện
(`activation_eligibility_epoch == FAR_FUTURE_EPOCH`) và effective balance đã đạt mức
tối đa `MAX_EFFECTIVE_BALANCE`.

```python
def is_eligible_for_activation_queue(validator: Validator) -> bool:
    """
    Check if ``validator`` is eligible to be placed into the activation queue.
    """
    return (
        validator.activation_eligibility_epoch == FAR_FUTURE_EPOCH
        and validator.effective_balance == MAX_EFFECTIVE_BALANCE
    )
```

#### `is_eligible_for_activation`

Kiểm tra `validator` có đủ điều kiện để được kích hoạt hay không: vị trí của nó trong
hàng đợi đã được finalized, và nó chưa được kích hoạt.

```python
def is_eligible_for_activation(state: BeaconState, validator: Validator) -> bool:
    """
    Check if ``validator`` is eligible for activation.
    """
    return (
        # Vị trí trong hàng đợi đã được finalized
        validator.activation_eligibility_epoch <= state.finalized_checkpoint.epoch
        # Chưa được kích hoạt
        and validator.activation_epoch == FAR_FUTURE_EPOCH
    )
```

#### `is_slashable_validator`

Kiểm tra `validator` có thể bị slashing (phạt cắt giảm stake) tại `epoch` hay không:
validator chưa bị slash trước đó, và `epoch` nằm trong khoảng
`[activation_epoch, withdrawable_epoch)`.

```python
def is_slashable_validator(validator: Validator, epoch: Epoch) -> bool:
    """
    Check if ``validator`` is slashable.
    """
    return (not validator.slashed) and (
        validator.activation_epoch <= epoch < validator.withdrawable_epoch
    )
```

#### `is_slashable_attestation_data`

Kiểm tra hai `AttestationData` `data_1` và `data_2` có vi phạm luật slashing của
Casper FFG hay không. Có hai loại vi phạm:

- **Double vote** (bỏ phiếu kép): hai attestation khác nhau nhưng có cùng target
  epoch.
- **Surround vote** (bỏ phiếu bao quanh): khoảng `source → target` của `data_1` bao
  trọn khoảng `source → target` của `data_2`.

```python
def is_slashable_attestation_data(data_1: AttestationData, data_2: AttestationData) -> bool:
    """
    Check if ``data_1`` and ``data_2`` are slashable according to Casper FFG rules.
    """
    return (
        # Double vote (bỏ phiếu kép)
        (data_1 != data_2 and data_1.target.epoch == data_2.target.epoch)
        or
        # Surround vote (bỏ phiếu bao quanh)
        (data_1.source.epoch < data_2.source.epoch and data_2.target.epoch < data_1.target.epoch)
    )
```

#### `is_valid_indexed_attestation`

Kiểm tra `indexed_attestation` không rỗng, có danh sách index được sắp xếp tăng dần
và không trùng lặp, và có aggregate signature hợp lệ.

```python
def is_valid_indexed_attestation(
    state: BeaconState, indexed_attestation: IndexedAttestation
) -> bool:
    """
    Check if ``indexed_attestation`` is not empty, has sorted and unique indices and has a valid aggregate signature.
    """
    # Kiểm tra các index đã được sắp xếp và không trùng lặp
    indices = indexed_attestation.attesting_indices
    if len(indices) == 0 or list(indices) != sorted(set(indices)):
        return False
    # Kiểm tra aggregate signature
    pubkeys = [state.validators[index].pubkey for index in indices]
    domain = get_domain(state, DOMAIN_BEACON_ATTESTER, indexed_attestation.data.target.epoch)
    signing_root = compute_signing_root(indexed_attestation.data, domain)
    return bls.FastAggregateVerify(pubkeys, signing_root, indexed_attestation.signature)
```

#### `compute_merkle_branch_root`

Trả về Merkle root thu được khi hash `leaf` (nằm ở vị trí `index`) lần lượt với các
node trong `branch`. Tại mỗi tầng `i`, bit thứ `i` của `index` quyết định node hiện
tại là con trái hay con phải, tức là quyết định thứ tự ghép trước khi hash.

```python
def compute_merkle_branch_root(
    leaf: Bytes32, branch: Sequence[Bytes32], depth: Uint64, index: Uint64
) -> Root:
    """
    Return the Merkle root obtained by hashing ``leaf`` at ``index`` with ``branch``.
    """
    value = leaf
    for i in range(depth):
        if index // (2**i) % 2:
            value = sha256(branch[i] + value)
        else:
            value = sha256(value + branch[i])
    return Root(value)
```

#### `is_valid_merkle_branch`

Kiểm tra `leaf` tại vị trí `index` có khớp với Merkle `root` khi dùng `branch` hay
không (tức là xác minh một Merkle proof). Độ dài `branch` phải đúng bằng `depth`.

```python
def is_valid_merkle_branch(
    leaf: Bytes32, branch: Sequence[Bytes32], depth: Uint64, index: Uint64, root: Root
) -> bool:
    """
    Check if ``leaf`` at ``index`` verifies against the Merkle ``root`` and ``branch``.
    """
    if depth != len(branch):
        return False
    return compute_merkle_branch_root(leaf, branch, depth, index) == root
```

### Misc

*(Các hàm tính toán khác)*

#### `compute_shuffled_permutation`

Trả về toàn bộ hoán vị (permutation) đã được shuffle tương ứng với `seed` (và
`index_count`). Thuật toán dùng là "swap-or-not": qua `SHUFFLE_ROUND_COUNT` vòng, ở
mỗi vòng mỗi phần tử được ghép cặp với phần tử "đối xứng" qua một `pivot`, rồi một
bit giả ngẫu nhiên (lấy từ hash của `seed`) quyết định có hoán đổi hay không.

> 💡 Ghi chú: Nhờ kết quả hash được cache theo từng bucket 256 vị trí, mỗi vòng chỉ
> cần khoảng `index_count / 256` lần hash. Vì đây là một hoán vị đầy đủ, mỗi
> validator xuất hiện đúng một lần trong kết quả.

```python
def compute_shuffled_permutation(index_count: Uint64, seed: Bytes32) -> Sequence[Uint64]:
    """
    Return the full shuffled permutation corresponding to ``seed`` (and ``index_count``).
    """
    # Swap or not (https://link.springer.com/content/pdf/10.1007%2F978-3-642-32009-5_1.pdf)
    # Xem thuật toán 'generalized domain' ở trang 3
    indices = [Uint64(index) for index in range(index_count)]
    for current_round in range(SHUFFLE_ROUND_COUNT):
        round_bytes = uint_to_bytes(Uint8(current_round))
        pivot = bytes_to_uint64(sha256(seed + round_bytes)[0:8]) % index_count
        source_by_bucket: dict[Uint64, Bytes32] = {}
        for i in range(index_count):
            flip = (pivot + index_count - indices[i]) % index_count
            position = max(indices[i], flip)
            position_bucket = position // 256
            if position_bucket not in source_by_bucket:
                source_by_bucket[position_bucket] = sha256(
                    seed + round_bytes + uint_to_bytes(Uint32(position_bucket))
                )
            source = source_by_bucket[position_bucket]
            byte_val = source[(position % 256) // 8]
            bit = (byte_val >> (position % 8)) % 2
            indices[i] = flip if bit else indices[i]
    return indices
```

#### `compute_shuffled_index`

Trả về index đã được shuffle tương ứng với `index`, dựa trên `seed` (và
`index_count`). Yêu cầu `index < index_count`.

```python
def compute_shuffled_index(index: Uint64, index_count: Uint64, seed: Bytes32) -> Uint64:
    """
    Return the shuffled index corresponding to ``seed`` (and ``index_count``).
    """
    assert index < index_count
    return compute_shuffled_permutation(index_count, seed)[index]
```

#### `compute_proposer_index`

Chọn ngẫu nhiên một index từ `indices`, với xác suất tỉ lệ theo effective balance.

> 💡 Ghi chú: Đây là phương pháp lấy mẫu loại bỏ (rejection sampling): duyệt các
> ứng viên theo thứ tự đã shuffle; với mỗi ứng viên, lấy một byte ngẫu nhiên
> `random_byte` trong `[0, 255]` và chấp nhận ứng viên nếu
> `effective_balance / MAX_EFFECTIVE_BALANCE >= random_byte / 255`. Validator có
> effective balance tối đa luôn được chấp nhận ngay khi tới lượt; validator có
> balance thấp hơn có xác suất được chọn thấp hơn tương ứng.

```python
def compute_proposer_index(
    state: BeaconState, indices: Sequence[ValidatorIndex], seed: Bytes32
) -> ValidatorIndex:
    """
    Return from ``indices`` a random index sampled by effective balance.
    """
    assert len(indices) > 0
    MAX_RANDOM_BYTE = 2**8 - 1
    i = Uint64(0)
    total = Uint64(len(indices))
    while True:
        candidate_index = indices[compute_shuffled_index(i % total, total, seed)]
        random_byte = sha256(seed + uint_to_bytes(Uint64(i // 32)))[i % 32]
        effective_balance = state.validators[candidate_index].effective_balance
        if effective_balance * MAX_RANDOM_BYTE >= MAX_EFFECTIVE_BALANCE * random_byte:
            return candidate_index
        i += 1
```

#### `compute_committee`

Trả về committee ứng với `indices`, `seed`, `index` và tổng số committee `count`.
Danh sách `indices` (sau khi shuffle) được chia thành `count` đoạn liên tiếp có kích
thước gần bằng nhau; committee thứ `index` là đoạn `[start, end)`.

```python
def compute_committee(
    indices: Sequence[ValidatorIndex], seed: Bytes32, index: Uint64, count: Uint64
) -> Sequence[ValidatorIndex]:
    """
    Return the committee corresponding to ``indices``, ``seed``, ``index``, and committee ``count``.
    """
    start = (len(indices) * index) // count
    end = (len(indices) * Uint64(index + 1)) // count
    return [
        indices[compute_shuffled_index(Uint64(index), Uint64(len(indices)), seed)]
        for index in range(start, end)
    ]
```

#### `compute_time_at_slot`

*Lưu ý*: Hàm này không an toàn đối với overflow và underflow (không có kiểm tra tràn
số).

Trả về thời điểm (tính bằng giây) bắt đầu của slot cho trước.

```python
def compute_time_at_slot(genesis_time: Uint64, slot: Slot) -> Uint64:
    """
    Return the time in seconds at the start of the given slot.
    """
    genesis_time_ms = seconds_to_milliseconds(genesis_time)
    time_ms = compute_time_at_slot_ms(genesis_time_ms, slot)
    return milliseconds_to_seconds(time_ms)
```

#### `compute_slot_at_time`

Trả về slot tương ứng với thời điểm Unix `time` (tính bằng giây).

```python
def compute_slot_at_time(genesis_time: Uint64, time: Uint64) -> Slot:
    """
    Return the slot at Unix time ``time``.
    """
    genesis_time_ms = seconds_to_milliseconds(genesis_time)
    time_ms = seconds_to_milliseconds(time)
    return compute_slot_at_time_ms(genesis_time_ms, time_ms)
```

#### `compute_time_at_slot_ms`

Trả về thời điểm (tính bằng mili giây) bắt đầu của slot cho trước.

```python
def compute_time_at_slot_ms(genesis_time_ms: Uint64, slot: Slot) -> Uint64:
    """
    Return the time in milliseconds at the start of the given slot.
    """
    return Uint64(genesis_time_ms + slot * SLOT_DURATION_MS)
```

#### `compute_slot_at_time_ms`

Trả về slot tương ứng với thời điểm Unix `time_ms` (tính bằng mili giây).

```python
def compute_slot_at_time_ms(genesis_time_ms: Uint64, time_ms: Uint64) -> Slot:
    """
    Return the slot at Unix time ``time_ms``.
    """
    return Slot((time_ms - genesis_time_ms) // SLOT_DURATION_MS)
```

#### `compute_epoch_at_slot`

Trả về số thứ tự epoch chứa `slot`.

```python
def compute_epoch_at_slot(slot: Slot) -> Epoch:
    """
    Return the epoch number at ``slot``.
    """
    return Epoch(slot // SLOTS_PER_EPOCH)
```

#### `compute_start_slot_at_epoch`

Trả về slot đầu tiên của `epoch`.

```python
def compute_start_slot_at_epoch(epoch: Epoch) -> Slot:
    """
    Return the start slot of ``epoch``.
    """
    return Slot(epoch) * SLOTS_PER_EPOCH
```

#### `compute_activation_exit_epoch`

Trả về epoch mà tại đó các yêu cầu kích hoạt (activation) và exit của validator được
khởi tạo trong `epoch` sẽ có hiệu lực. Độ trễ `1 + MAX_SEED_LOOKAHEAD` epoch đảm bảo
tập validator active không thay đổi trong khoảng thời gian mà seed cho shuffling đã
có thể bị biết trước.

```python
def compute_activation_exit_epoch(epoch: Epoch) -> Epoch:
    """
    Return the epoch during which validator activations and exits initiated in ``epoch`` take effect.
    """
    return epoch + 1 + MAX_SEED_LOOKAHEAD
```

#### `compute_fork_data_root`

Trả về fork data root 32 byte ứng với `current_version` và
`genesis_validators_root`. Giá trị này chủ yếu được dùng trong signature domain để
tránh việc một signature hợp lệ trên fork/chain này cũng hợp lệ trên fork/chain khác
(tránh "va chạm" giữa các fork/chain, hay replay attack).

```python
def compute_fork_data_root(current_version: Version, genesis_validators_root: Root) -> Root:
    """
    Return the 32-byte fork data root for the ``current_version`` and ``genesis_validators_root``.
    This is used primarily in signature domains to avoid collisions across forks/chains.
    """
    return hash_tree_root(
        ForkData(
            current_version=current_version,
            genesis_validators_root=genesis_validators_root,
        )
    )
```

#### `compute_domain`

Trả về domain ứng với `domain_type` và `fork_version`. Domain gồm 4 byte
`domain_type` ghép với 28 byte đầu của fork data root. Nếu không truyền vào,
`fork_version` mặc định là `GENESIS_FORK_VERSION` và `genesis_validators_root` mặc
định là toàn byte 0.

```python
def compute_domain(
    domain_type: DomainType,
    fork_version: Version | None = None,
    genesis_validators_root: Root | None = None,
) -> Domain:
    """
    Return the domain for the ``domain_type`` and ``fork_version``.
    """
    if fork_version is None:
        fork_version = GENESIS_FORK_VERSION
    if genesis_validators_root is None:
        genesis_validators_root = Root()  # mặc định toàn bộ byte bằng 0
    fork_data_root = compute_fork_data_root(fork_version, genesis_validators_root)
    return Domain(domain_type + fork_data_root[:28])
```

#### `compute_signing_root`

Trả về signing root (giá trị thực sự được ký) cho dữ liệu cần ký: đó là
`hash_tree_root` của container `SigningData` gồm root của object và `domain`.

```python
def compute_signing_root(ssz_object: SSZObject, domain: Domain) -> Root:
    """
    Return the signing root for the corresponding signing data.
    """
    return hash_tree_root(
        SigningData(
            object_root=hash_tree_root(ssz_object),
            domain=domain,
        )
    )
```

### Beacon state accessors

*(Các hàm đọc/truy xuất dữ liệu từ beacon state, không làm thay đổi state)*

#### `get_current_epoch`

Trả về epoch hiện tại (epoch chứa `state.slot`).

```python
def get_current_epoch(state: BeaconState) -> Epoch:
    """
    Return the current epoch.
    """
    return compute_epoch_at_slot(state.slot)
```

#### `get_previous_epoch`

Trả về epoch trước đó (trừ khi epoch hiện tại là `GENESIS_EPOCH`, khi đó trả về
chính `GENESIS_EPOCH`).

```python
def get_previous_epoch(state: BeaconState) -> Epoch:
    """`
    Return the previous epoch (unless the current epoch is ``GENESIS_EPOCH``).
    """
    return saturating_sub(get_current_epoch(state), 1)
```

#### `get_block_root`

Trả về block root tại slot đầu tiên của một `epoch` gần đây.

```python
def get_block_root(state: BeaconState, epoch: Epoch) -> Root:
    """
    Return the block root at the start of a recent ``epoch``.
    """
    return get_block_root_at_slot(state, compute_start_slot_at_epoch(epoch))
```

#### `get_block_root_at_slot`

Trả về block root tại một `slot` gần đây. "Gần đây" nghĩa là `slot` phải nhỏ hơn
slot hiện tại và cách không quá `SLOTS_PER_HISTORICAL_ROOT` slot, vì
`state.block_roots` là một vector vòng (circular buffer) chỉ lưu bấy nhiêu giá trị.

```python
def get_block_root_at_slot(state: BeaconState, slot: Slot) -> Root:
    """
    Return the block root at a recent ``slot``.
    """
    assert slot < state.slot <= slot + SLOTS_PER_HISTORICAL_ROOT
    return state.block_roots[slot % SLOTS_PER_HISTORICAL_ROOT]
```

#### `get_randao_mix`

Trả về randao mix tại một `epoch` gần đây (lấy từ vector vòng `state.randao_mixes`).

```python
def get_randao_mix(state: BeaconState, epoch: Epoch) -> Bytes32:
    """
    Return the randao mix at a recent ``epoch``.
    """
    return state.randao_mixes[epoch % EPOCHS_PER_HISTORICAL_VECTOR]
```

#### `get_active_validator_indices`

Trả về danh sách index của các validator đang active tại `epoch`.

```python
def get_active_validator_indices(state: BeaconState, epoch: Epoch) -> Sequence[ValidatorIndex]:
    """
    Return the sequence of active validator indices at ``epoch``.
    """
    return [
        ValidatorIndex(index)
        for index, validator in enumerate(state.validators)
        if is_active_validator(validator, epoch)
    ]
```

#### `get_validator_churn_limit`

Trả về churn limit của validator cho epoch hiện tại, tức là số validator tối đa được
phép kích hoạt (hoặc exit) trong một epoch. Giá trị này bằng số validator active chia
cho `CHURN_LIMIT_QUOTIENT`, nhưng không nhỏ hơn `MIN_PER_EPOCH_CHURN_LIMIT`.

```python
def get_validator_churn_limit(state: BeaconState) -> Uint64:
    """
    Return the validator churn limit for the current epoch.
    """
    active_validator_indices = get_active_validator_indices(state, get_current_epoch(state))
    return max(
        MIN_PER_EPOCH_CHURN_LIMIT, Uint64(len(active_validator_indices)) // CHURN_LIMIT_QUOTIENT
    )
```

#### `get_seed`

Trả về seed tại `epoch` cho một `domain_type` nhất định. Seed được tính từ randao mix
của epoch `epoch - MIN_SEED_LOOKAHEAD - 1` (cộng thêm `EPOCHS_PER_HISTORICAL_VECTOR`
để tránh underflow), nên seed của một epoch đã được xác định từ trước đó vài epoch.

```python
def get_seed(state: BeaconState, epoch: Epoch, domain_type: DomainType) -> Bytes32:
    """
    Return the seed at ``epoch``.
    """
    mix = get_randao_mix(
        state, epoch + EPOCHS_PER_HISTORICAL_VECTOR - MIN_SEED_LOOKAHEAD - 1
    )  # Tránh underflow
    return sha256(domain_type + uint_to_bytes(epoch) + mix)
```

#### `get_committee_count_per_slot`

Trả về số committee trong mỗi slot của `epoch`. Số này được chọn sao cho mỗi
committee có khoảng `TARGET_COMMITTEE_SIZE` validator, nằm trong khoảng từ 1 đến
`MAX_COMMITTEES_PER_SLOT`.

```python
def get_committee_count_per_slot(state: BeaconState, epoch: Epoch) -> Uint64:
    """
    Return the number of committees in each slot for the given ``epoch``.
    """
    return max(
        Uint64(1),
        min(
            MAX_COMMITTEES_PER_SLOT,
            Uint64(len(get_active_validator_indices(state, epoch)))
            // Uint64(SLOTS_PER_EPOCH)
            // TARGET_COMMITTEE_SIZE,
        ),
    )
```

#### `get_beacon_committee`

Trả về beacon committee tại `slot` với chỉ số committee `index`. Toàn bộ validator
active trong epoch được chia thành `committees_per_slot * SLOTS_PER_EPOCH`
committee; hàm này tính vị trí tổng thể của committee cần lấy rồi gọi
`compute_committee`.

```python
def get_beacon_committee(
    state: BeaconState, slot: Slot, index: CommitteeIndex
) -> Sequence[ValidatorIndex]:
    """
    Return the beacon committee at ``slot`` for ``index``.
    """
    epoch = compute_epoch_at_slot(slot)
    committees_per_slot = get_committee_count_per_slot(state, epoch)
    return compute_committee(
        indices=get_active_validator_indices(state, epoch),
        seed=get_seed(state, epoch, DOMAIN_BEACON_ATTESTER),
        index=Uint64(slot % SLOTS_PER_EPOCH) * committees_per_slot + index,
        count=committees_per_slot * Uint64(SLOTS_PER_EPOCH),
    )
```

#### `get_beacon_proposer_index`

Trả về index của beacon proposer tại slot hiện tại. Seed được tạo từ seed của epoch
(với `DOMAIN_BEACON_PROPOSER`) kết hợp với số slot, nên mỗi slot có một proposer
riêng.

```python
def get_beacon_proposer_index(state: BeaconState) -> ValidatorIndex:
    """
    Return the beacon proposer index at the current slot.
    """
    epoch = get_current_epoch(state)
    seed = sha256(get_seed(state, epoch, DOMAIN_BEACON_PROPOSER) + uint_to_bytes(state.slot))
    indices = get_active_validator_indices(state, epoch)
    return compute_proposer_index(state, indices, seed)
```

#### `get_total_balance`

Trả về tổng effective balance của các validator trong `indices`. Kết quả tối thiểu là
`EFFECTIVE_BALANCE_INCREMENT` Gwei để tránh phép chia cho 0. Phép tính an toàn cho
đến khoảng 10 tỷ ETH; vượt quá mức đó sẽ bị tràn `Uint64`.

```python
def get_total_balance(state: BeaconState, indices: set[ValidatorIndex]) -> Gwei:
    """
    Return the combined effective balance of the ``indices``.
    ``EFFECTIVE_BALANCE_INCREMENT`` Gwei minimum to avoid divisions by zero.
    Math safe up to ~10B ETH, after which this overflows Uint64.
    """
    return Gwei(
        max(
            EFFECTIVE_BALANCE_INCREMENT,
            sum([state.validators[index].effective_balance for index in indices]),
        )
    )
```

#### `get_total_active_balance`

Trả về tổng effective balance của các validator đang active trong epoch hiện tại.
Lưu ý: `get_total_balance` trả về tối thiểu `EFFECTIVE_BALANCE_INCREMENT` Gwei để
tránh chia cho 0.

```python
def get_total_active_balance(state: BeaconState) -> Gwei:
    """
    Return the combined effective balance of the active validators.
    Note: ``get_total_balance`` returns ``EFFECTIVE_BALANCE_INCREMENT`` Gwei minimum to avoid divisions by zero.
    """
    return get_total_balance(
        state, set(get_active_validator_indices(state, get_current_epoch(state)))
    )
```

#### `get_domain`

Trả về signature domain (fork version ghép với domain type) của một message. Nếu
`epoch` nhỏ hơn `state.fork.epoch` thì dùng `previous_version`, ngược lại dùng
`current_version`; nhờ vậy các message ký trước thời điểm fork vẫn được xác minh
đúng.

```python
def get_domain(state: BeaconState, domain_type: DomainType, epoch: Epoch | None = None) -> Domain:
    """
    Return the signature domain (fork version concatenated with domain type) of a message.
    """
    epoch = get_current_epoch(state) if epoch is None else epoch
    fork_version = (
        state.fork.previous_version if epoch < state.fork.epoch else state.fork.current_version
    )
    return compute_domain(domain_type, fork_version, state.genesis_validators_root)
```

#### `get_indexed_attestation`

Trả về `IndexedAttestation` tương ứng với `attestation`: thay vì bitfield
`aggregation_bits`, nó chứa danh sách (đã sắp xếp) các index của validator đã
attest.

```python
def get_indexed_attestation(state: BeaconState, attestation: Attestation) -> IndexedAttestation:
    """
    Return the indexed attestation corresponding to ``attestation``.
    """
    attesting_indices = get_attesting_indices(state, attestation)

    return IndexedAttestation(
        attesting_indices=AttestingIndices(data=sorted(attesting_indices)),
        data=attestation.data,
        signature=attestation.signature,
    )
```

#### `get_attesting_indices`

Trả về tập index của các validator đã attest, xác định từ `data` (để tìm committee)
và `bits` (`aggregation_bits`, bit thứ `i` bật nghĩa là thành viên thứ `i` của
committee đã tham gia).

```python
def get_attesting_indices(state: BeaconState, attestation: Attestation) -> set[ValidatorIndex]:
    """
    Return the set of attesting indices corresponding to ``data`` and ``bits``.
    """
    committee = get_beacon_committee(state, attestation.data.slot, attestation.data.index)
    return {
        validator_index
        for index, validator_index in enumerate(committee)
        if attestation.aggregation_bits[index]
    }
```

#### `get_pending_attesting_indices`

Trả về tập index của các validator đã attest đối với một `PendingAttestation` (cách
tính giống `get_attesting_indices`).

```python
def get_pending_attesting_indices(
    state: BeaconState, attestation: PendingAttestation
) -> set[ValidatorIndex]:
    """
    Return the set of attesting indices for a ``PendingAttestation``.
    """
    committee = get_beacon_committee(state, attestation.data.slot, attestation.data.index)
    return {
        validator_index
        for index, validator_index in enumerate(committee)
        if attestation.aggregation_bits[index]
    }
```

### Beacon state mutators

*(Các hàm làm thay đổi beacon state)*

#### `increase_balance`

Tăng balance của validator có index `index` thêm `delta`.

```python
def increase_balance(state: BeaconState, index: ValidatorIndex, delta: Gwei) -> None:
    """
    Increase the validator balance at index ``index`` by ``delta``.
    """
    state.balances[index] += delta
```

#### `decrease_balance`

Giảm balance của validator có index `index` đi `delta` (không thấp hơn 0).

```python
def decrease_balance(state: BeaconState, index: ValidatorIndex, delta: Gwei) -> None:
    """
    Decrease the validator balance at index ``index`` by ``delta``.
    """
    state.balances[index] = saturating_sub(state.balances[index], delta)
```

#### `initiate_validator_exit`

Khởi tạo exit cho validator có index `index`.

> 💡 Ghi chú: Exit được xếp vào một "hàng đợi exit". Epoch exit được chọn là giá trị
> lớn nhất giữa các `exit_epoch` đã được xếp lịch và epoch sớm nhất có thể
> (`compute_activation_exit_epoch` của epoch hiện tại). Nếu epoch đó đã đủ số
> validator exit theo churn limit thì đẩy sang epoch kế tiếp. Sau khi exit, validator
> phải chờ thêm `MIN_VALIDATOR_WITHDRAWABILITY_DELAY` epoch mới có thể rút tiền.

```python
def initiate_validator_exit(state: BeaconState, index: ValidatorIndex) -> None:
    """
    Initiate the exit of the validator with index ``index``.
    """
    # Thoát sớm nếu validator đã khởi tạo exit trước đó
    validator = state.validators[index]
    if validator.exit_epoch != FAR_FUTURE_EPOCH:
        return

    # Tính epoch trong hàng đợi exit
    exit_epochs = [
        validator.exit_epoch
        for validator in state.validators
        if validator.exit_epoch != FAR_FUTURE_EPOCH
    ]
    exit_queue_epoch = max(exit_epochs + [compute_activation_exit_epoch(get_current_epoch(state))])
    exit_queue_churn = len([
        validator for validator in state.validators if validator.exit_epoch == exit_queue_epoch
    ])
    if exit_queue_churn >= get_validator_churn_limit(state):
        exit_queue_epoch += 1

    # Đặt exit epoch và withdrawable epoch cho validator
    validator.exit_epoch = exit_queue_epoch
    validator.withdrawable_epoch = validator.exit_epoch + MIN_VALIDATOR_WITHDRAWABILITY_DELAY
```

#### `slash_validator`

Slash validator có index `slashed_index`.

> 💡 Ghi chú: Các bước thực hiện: (1) khởi tạo exit cho validator; (2) đánh dấu
> `slashed = True` và kéo dài `withdrawable_epoch` ít nhất
> `EPOCHS_PER_SLASHINGS_VECTOR` epoch (để validator còn chịu thêm penalty tương quan
> trong quá trình xử lý slashings ở epoch processing); (3) cộng effective balance vào
> `state.slashings` và trừ ngay một penalty ban đầu
> `effective_balance // MIN_SLASHING_PENALTY_QUOTIENT`; (4) trả reward cho
> whistleblower (người tố giác) và proposer. Nếu không có whistleblower riêng thì
> proposer nhận toàn bộ reward.

```python
def slash_validator(
    state: BeaconState,
    slashed_index: ValidatorIndex,
    whistleblower_index: ValidatorIndex | None = None,
) -> None:
    """
    Slash the validator with index ``slashed_index``.
    """
    epoch = get_current_epoch(state)
    initiate_validator_exit(state, slashed_index)
    validator = state.validators[slashed_index]
    validator.slashed = Boolean(True)
    validator.withdrawable_epoch = max(
        validator.withdrawable_epoch, epoch + EPOCHS_PER_SLASHINGS_VECTOR
    )
    state.slashings[epoch % EPOCHS_PER_SLASHINGS_VECTOR] += validator.effective_balance
    decrease_balance(
        state, slashed_index, validator.effective_balance // MIN_SLASHING_PENALTY_QUOTIENT
    )

    # Trả reward cho proposer và whistleblower
    proposer_index = get_beacon_proposer_index(state)
    if whistleblower_index is None:
        whistleblower_index = proposer_index
    whistleblower_reward = validator.effective_balance // WHISTLEBLOWER_REWARD_QUOTIENT
    proposer_reward = whistleblower_reward // PROPOSER_REWARD_QUOTIENT
    increase_balance(state, proposer_index, proposer_reward)
    increase_balance(state, whistleblower_index, whistleblower_reward - proposer_reward)
```

## Genesis

*(Khởi tạo trạng thái ban đầu của beacon chain)*

Trước khi genesis của Ethereum beacon chain được kích hoạt, với mỗi block
proof-of-work của Ethereum, đặt
`candidate_state = initialize_beacon_state_from_eth1(eth1_block_hash, eth1_timestamp, deposits)`
trong đó:

- `eth1_block_hash` là hash của block proof-of-work Ethereum
- `eth1_timestamp` là Unix timestamp tương ứng với `eth1_block_hash`
- `deposits` là chuỗi tất cả các deposit, sắp xếp theo thứ tự thời gian, tính
  đến (và bao gồm) block có hash `eth1_block_hash`

Chỉ được xét các block proof-of-work khi chúng đã có tuổi ít nhất
`SECONDS_PER_ETH1_BLOCK * ETH1_FOLLOW_DISTANCE` giây (tức là
`eth1_timestamp + SECONDS_PER_ETH1_BLOCK * ETH1_FOLLOW_DISTANCE <= current_unix_time`).
Do ràng buộc này, nếu
`GENESIS_DELAY < SECONDS_PER_ETH1_BLOCK * ETH1_FOLLOW_DISTANCE` thì
`genesis_time` có thể xảy ra trước cả thời điểm mà thời gian/state lần đầu được
biết đến. Các giá trị cấu hình nên được chọn để tránh trường hợp này.

> 💡 Ghi chú: Nói cách khác, node chỉ "nhìn thấy" một block proof-of-work sau khi
> nó đã đủ cũ (đi sau đầu chuỗi PoW một khoảng `ETH1_FOLLOW_DISTANCE` block). Nếu
> `GENESIS_DELAY` nhỏ hơn khoảng trễ này thì thời điểm genesis tính ra sẽ nằm ở
> quá khứ so với lúc node biết được candidate state.

```python
def initialize_beacon_state_from_eth1(
    eth1_block_hash: Hash32, eth1_timestamp: Uint64, deposits: Sequence[Deposit]
) -> BeaconState:
    state = BeaconState.empty()
    state.genesis_time = eth1_timestamp + GENESIS_DELAY
    state.fork = Fork(
        previous_version=GENESIS_FORK_VERSION,
        current_version=GENESIS_FORK_VERSION,
        epoch=GENESIS_EPOCH,
    )
    state.eth1_data.deposit_count = Uint64(len(deposits))
    state.eth1_data.block_hash = eth1_block_hash
    state.latest_block_header.body_root = hash_tree_root(BeaconBlockBody.empty())
    state.randao_mixes = RandaoMixes(data=[eth1_block_hash] * EPOCHS_PER_HISTORICAL_VECTOR)

    # Xử lý các deposit
    leaves = [deposit.data for deposit in deposits]
    for index, deposit in enumerate(deposits):
        deposit_data_list = DepositDataList(data=leaves[: index + 1])
        state.eth1_data.deposit_root = hash_tree_root(deposit_data_list)
        process_deposit(state, deposit)

    # Xử lý kích hoạt validator
    for index, validator in enumerate(state.validators):
        balance = state.balances[index]
        validator.effective_balance = min(
            balance - balance % EFFECTIVE_BALANCE_INCREMENT, MAX_EFFECTIVE_BALANCE
        )
        if validator.effective_balance == MAX_EFFECTIVE_BALANCE:
            validator.activation_eligibility_epoch = GENESIS_EPOCH
            validator.activation_epoch = GENESIS_EPOCH

    # Đặt genesis validators root để phân tách domain và đánh phiên bản chain
    state.genesis_validators_root = hash_tree_root(state.validators)

    return state
```

*Lưu ý*: Block ETH1 có `eth1_timestamp` thỏa mãn tiêu chí về số lượng validator
active tối thiểu tại genesis cũng có thể xuất hiện trước `MIN_GENESIS_TIME`.

### Genesis state

Đặt `genesis_state = candidate_state` tại thời điểm đầu tiên mà
`is_valid_genesis_state(candidate_state) is True`.

> 💡 Ghi chú: Tức là genesis state là candidate state đầu tiên vừa thỏa mãn thời
> gian tối thiểu (`MIN_GENESIS_TIME`) vừa có đủ số validator active
> (`MIN_GENESIS_ACTIVE_VALIDATOR_COUNT`).

```python
def is_valid_genesis_state(state: BeaconState) -> bool:
    if state.genesis_time < MIN_GENESIS_TIME:
        return False
    if len(get_active_validator_indices(state, GENESIS_EPOCH)) < MIN_GENESIS_ACTIVE_VALIDATOR_COUNT:
        return False
    return True
```

### Genesis block

Đặt `genesis_block = BeaconBlock(state_root=hash_tree_root(genesis_state))`.

## Beacon chain state transition function

*(Hàm chuyển trạng thái của beacon chain)*

Post-state (state sau khi chuyển) tương ứng với một pre-state `state` và một
block đã ký `signed_block` được định nghĩa là `state_transition(state, signed_block)`.
Các phép chuyển state gây ra exception không được xử lý (ví dụ một `assert` thất
bại, hoặc truy cập list ngoài phạm vi) được coi là không hợp lệ. Các phép chuyển
state gây ra tràn trên (overflow) hoặc tràn dưới (underflow) `Uint64` cũng bị
coi là không hợp lệ.

```python
def state_transition(
    state: BeaconState, signed_block: SignedBeaconBlock, validate_result: bool = True
) -> None:
    block = signed_block.message
    # Xử lý các slot (kể cả các slot không có block) cho tới slot của block
    process_slots(state, block.slot)
    # Kiểm tra signature
    if validate_result:
        assert verify_block_signature(state, signed_block)
    # Xử lý block
    process_block(state, block)
    # Kiểm tra state root
    if validate_result:
        assert block.state_root == hash_tree_root(state)
```

```python
def verify_block_signature(state: BeaconState, signed_block: SignedBeaconBlock) -> bool:
    proposer = state.validators[signed_block.message.proposer_index]
    signing_root = compute_signing_root(
        signed_block.message, get_domain(state, DOMAIN_BEACON_PROPOSER)
    )
    return bls.Verify(proposer.pubkey, signing_root, signed_block.signature)
```

```python
def process_slots(state: BeaconState, slot: Slot) -> None:
    assert state.slot < slot
    while state.slot < slot:
        process_slot(state)
        # Xử lý epoch tại slot bắt đầu của epoch tiếp theo
        if (state.slot + 1) % SLOTS_PER_EPOCH == 0:
            process_epoch(state)
        state.slot = state.slot + 1
```

```python
def process_slot(state: BeaconState) -> None:
    slot_index = state.slot % SLOTS_PER_HISTORICAL_ROOT
    # Lưu cache state root
    previous_state_root = hash_tree_root(state)
    state.state_roots[slot_index] = previous_state_root
    # Lưu cache state root vào latest block header
    if state.latest_block_header.state_root == Bytes32():
        state.latest_block_header.state_root = previous_state_root
    # Lưu cache block root
    previous_block_root = hash_tree_root(state.latest_block_header)
    state.block_roots[slot_index] = previous_block_root
```

> 💡 Ghi chú: `process_slot` chạy cho mỗi slot (kể cả slot trống). Nó lưu state
> root của slot vừa qua, và điền nốt `state_root` còn để trống trong
> `latest_block_header` (trường này được để là `Bytes32()` khi xử lý block, vì
> lúc đó chưa biết state root sau block).

### Epoch processing

*(Xử lý cuối mỗi epoch)*

```python
def process_epoch(state: BeaconState) -> None:
    process_justification_and_finalization(state)
    process_rewards_and_penalties(state)
    process_registry_updates(state)
    process_slashings(state)
    process_eth1_data_reset(state)
    process_effective_balance_updates(state)
    process_slashings_reset(state)
    process_randao_mixes_reset(state)
    process_historical_roots_update(state)
    process_participation_record_updates(state)
```

#### Helpers

```python
def get_matching_source_attestations(
    state: BeaconState, epoch: Epoch
) -> Sequence[PendingAttestation]:
    assert epoch in (get_previous_epoch(state), get_current_epoch(state))
    return (
        state.current_epoch_attestations
        if epoch == get_current_epoch(state)
        else state.previous_epoch_attestations
    )
```

```python
def get_matching_target_attestations(
    state: BeaconState, epoch: Epoch
) -> Sequence[PendingAttestation]:
    return [
        attestation
        for attestation in get_matching_source_attestations(state, epoch)
        if attestation.data.target.root == get_block_root(state, epoch)
    ]
```

```python
def get_matching_head_attestations(
    state: BeaconState, epoch: Epoch
) -> Sequence[PendingAttestation]:
    return [
        attestation
        for attestation in get_matching_target_attestations(state, epoch)
        if attestation.data.beacon_block_root
        == get_block_root_at_slot(state, attestation.data.slot)
    ]
```

> 💡 Ghi chú: Ba hàm trên lọc dần: source attestations là mọi attestation của
> epoch (đã được kiểm tra source khi đưa vào block); target attestations là
> những attestation có target trùng với block root đầu epoch trên chain hiện
> tại; head attestations là những target attestation có thêm vote head đúng.

```python
def get_unslashed_attesting_indices(
    state: BeaconState, attestations: Sequence[PendingAttestation]
) -> set[ValidatorIndex]:
    output: set[ValidatorIndex] = set()
    for a in attestations:
        output = output.union(get_pending_attesting_indices(state, a))
    return set(filter(lambda index: not state.validators[index].slashed, output))
```

```python
def get_attesting_balance(state: BeaconState, attestations: Sequence[PendingAttestation]) -> Gwei:
    """
    Return the combined effective balance of the set of unslashed validators participating in ``attestations``.
    Note: ``get_total_balance`` returns ``EFFECTIVE_BALANCE_INCREMENT`` Gwei minimum to avoid divisions by zero.
    """
    return get_total_balance(state, get_unslashed_attesting_indices(state, attestations))
```

#### Justification and finalization

```python
def process_justification_and_finalization(state: BeaconState) -> None:
    # Các checkpoint FFG ban đầu có `root` là giá trị giữ chỗ `0x00`.
    # Bỏ qua cập nhật FFG trong hai epoch đầu tiên để tránh các trường hợp biên có thể làm thay đổi giá trị giữ chỗ này.
    if get_current_epoch(state) <= GENESIS_EPOCH + 1:
        return
    previous_attestations = get_matching_target_attestations(state, get_previous_epoch(state))
    current_attestations = get_matching_target_attestations(state, get_current_epoch(state))
    total_active_balance = get_total_active_balance(state)
    previous_target_balance = get_attesting_balance(state, previous_attestations)
    current_target_balance = get_attesting_balance(state, current_attestations)
    weigh_justification_and_finalization(
        state, total_active_balance, previous_target_balance, current_target_balance
    )
```

```python
def weigh_justification_and_finalization(
    state: BeaconState,
    total_active_balance: Gwei,
    previous_epoch_target_balance: Gwei,
    current_epoch_target_balance: Gwei,
) -> None:
    previous_epoch = get_previous_epoch(state)
    current_epoch = get_current_epoch(state)
    old_previous_justified_checkpoint = state.previous_justified_checkpoint
    old_current_justified_checkpoint = state.current_justified_checkpoint

    # Xử lý justification
    state.previous_justified_checkpoint = state.current_justified_checkpoint
    state.justification_bits[1:] = state.justification_bits[: JUSTIFICATION_BITS_LENGTH - 1]
    state.justification_bits[0] = Boolean(False)
    if previous_epoch_target_balance * 3 >= total_active_balance * 2:
        state.current_justified_checkpoint = Checkpoint(
            epoch=previous_epoch, root=get_block_root(state, previous_epoch)
        )
        state.justification_bits[1] = Boolean(True)
    if current_epoch_target_balance * 3 >= total_active_balance * 2:
        state.current_justified_checkpoint = Checkpoint(
            epoch=current_epoch, root=get_block_root(state, current_epoch)
        )
        state.justification_bits[0] = Boolean(True)

    # Xử lý finalization
    bits = state.justification_bits
    # Các epoch gần nhất thứ 2/3/4 đã justified, epoch thứ 2 dùng epoch thứ 4 làm source
    if all(bits[1:4]) and old_previous_justified_checkpoint.epoch + 3 == current_epoch:
        state.finalized_checkpoint = old_previous_justified_checkpoint
    # Các epoch gần nhất thứ 2/3 đã justified, epoch thứ 2 dùng epoch thứ 3 làm source
    if all(bits[1:3]) and old_previous_justified_checkpoint.epoch + 2 == current_epoch:
        state.finalized_checkpoint = old_previous_justified_checkpoint
    # Các epoch gần nhất thứ 1/2/3 đã justified, epoch thứ 1 dùng epoch thứ 3 làm source
    if all(bits[0:3]) and old_current_justified_checkpoint.epoch + 2 == current_epoch:
        state.finalized_checkpoint = old_current_justified_checkpoint
    # Các epoch gần nhất thứ 1/2 đã justified, epoch thứ 1 dùng epoch thứ 2 làm source
    if all(bits[0:2]) and old_current_justified_checkpoint.epoch + 1 == current_epoch:
        state.finalized_checkpoint = old_current_justified_checkpoint
```

> 💡 Ghi chú: Một epoch được justified khi các attestation có target là epoch đó
> chiếm ít nhất 2/3 tổng active balance. `justification_bits[i] = True` nghĩa là
> epoch cách epoch hiện tại `i` epoch đã được justified. Bốn điều kiện
> finalization ở trên là các quy tắc Casper FFG: một checkpoint justified được
> finalized khi các epoch kế tiếp nó (đến epoch được justify bằng nó làm
> source) đều đã justified liên tiếp.

#### Rewards and penalties

##### Helpers

```python
def get_base_reward(state: BeaconState, index: ValidatorIndex) -> Gwei:
    total_balance = get_total_active_balance(state)
    effective_balance = state.validators[index].effective_balance
    return Gwei(
        effective_balance
        * BASE_REWARD_FACTOR
        // integer_squareroot(total_balance)
        // BASE_REWARDS_PER_EPOCH
    )
```

```python
def get_proposer_reward(state: BeaconState, attesting_index: ValidatorIndex) -> Gwei:
    return get_base_reward(state, attesting_index) // PROPOSER_REWARD_QUOTIENT
```

```python
def get_finality_delay(state: BeaconState) -> Epoch:
    return get_previous_epoch(state) - state.finalized_checkpoint.epoch
```

```python
def is_in_inactivity_leak(state: BeaconState) -> bool:
    return get_finality_delay(state) > MIN_EPOCHS_TO_INACTIVITY_PENALTY
```

> 💡 Ghi chú: Chain rơi vào inactivity leak (giai đoạn "rò rỉ" balance của các
> validator không hoạt động) khi đã quá `MIN_EPOCHS_TO_INACTIVITY_PENALTY` epoch
> mà không đạt được finality.

```python
def get_eligible_validator_indices(state: BeaconState) -> Sequence[ValidatorIndex]:
    previous_epoch = get_previous_epoch(state)
    return [
        ValidatorIndex(index)
        for index, validator in enumerate(state.validators)
        if is_active_validator(validator, previous_epoch)
        or (validator.slashed and previous_epoch + 1 < validator.withdrawable_epoch)
    ]
```

```python
def get_attestation_component_deltas(
    state: BeaconState, attestations: Sequence[PendingAttestation]
) -> tuple[Sequence[Gwei], Sequence[Gwei]]:
    """
    Helper with shared logic for use by get source, target, and head deltas functions
    """
    rewards = [Gwei(0)] * len(state.validators)
    penalties = [Gwei(0)] * len(state.validators)
    total_balance = get_total_active_balance(state)
    unslashed_attesting_indices = get_unslashed_attesting_indices(state, attestations)
    attesting_balance = get_total_balance(state, unslashed_attesting_indices)
    for index in get_eligible_validator_indices(state):
        if index in unslashed_attesting_indices:
            increment = EFFECTIVE_BALANCE_INCREMENT  # Chia trước tổng balance cho increment để tránh tràn Uint64
            if is_in_inactivity_leak(state):
                # Vì toàn bộ base reward sẽ bị triệt tiêu bởi inactivity penalty deltas,
                # validator tham gia tối ưu được bù đủ base reward ở đây.
                rewards[index] += get_base_reward(state, index)
            else:
                reward_numerator = get_base_reward(state, index) * (attesting_balance // increment)
                rewards[index] += reward_numerator // (total_balance // increment)
        else:
            penalties[index] += get_base_reward(state, index)
    return rewards, penalties
```

> 💡 Ghi chú: Ở trạng thái bình thường, reward của mỗi thành phần (source, target,
> head) tỉ lệ với phần balance đã vote đúng trên tổng active balance: càng nhiều
> validator tham gia, reward của từng người càng cao. Validator đủ điều kiện mà
> không vote đúng bị penalty bằng đúng một base reward.

##### Components of attestation deltas

```python
def get_source_deltas(state: BeaconState) -> tuple[Sequence[Gwei], Sequence[Gwei]]:
    """
    Return attester micro-rewards/penalties for source-vote for each validator.
    """
    matching_source_attestations = get_matching_source_attestations(
        state, get_previous_epoch(state)
    )
    return get_attestation_component_deltas(state, matching_source_attestations)
```

```python
def get_target_deltas(state: BeaconState) -> tuple[Sequence[Gwei], Sequence[Gwei]]:
    """
    Return attester micro-rewards/penalties for target-vote for each validator.
    """
    matching_target_attestations = get_matching_target_attestations(
        state, get_previous_epoch(state)
    )
    return get_attestation_component_deltas(state, matching_target_attestations)
```

```python
def get_head_deltas(state: BeaconState) -> tuple[Sequence[Gwei], Sequence[Gwei]]:
    """
    Return attester micro-rewards/penalties for head-vote for each validator.
    """
    matching_head_attestations = get_matching_head_attestations(state, get_previous_epoch(state))
    return get_attestation_component_deltas(state, matching_head_attestations)
```

```python
def get_inclusion_delay_deltas(state: BeaconState) -> tuple[Sequence[Gwei], Sequence[Gwei]]:
    """
    Return proposer and inclusion delay micro-rewards/penalties for each validator.
    """
    rewards = [Gwei(0)] * len(state.validators)
    matching_source_attestations = get_matching_source_attestations(
        state, get_previous_epoch(state)
    )
    for index in get_unslashed_attesting_indices(state, matching_source_attestations):
        attestation = min(
            [
                attestation
                for attestation in matching_source_attestations
                if index in get_pending_attesting_indices(state, attestation)
            ],
            key=lambda a: a.inclusion_delay,
        )
        rewards[attestation.proposer_index] += get_proposer_reward(state, index)
        max_attester_reward = get_base_reward(state, index) - get_proposer_reward(state, index)
        rewards[index] += max_attester_reward // Uint64(attestation.inclusion_delay)

    # Không có penalty nào gắn với inclusion delay
    penalties = [Gwei(0)] * len(state.validators)
    return rewards, penalties
```

> 💡 Ghi chú: Với mỗi validator, chỉ attestation được đưa vào block sớm nhất
> (inclusion delay nhỏ nhất) được tính. Proposer đưa attestation đó vào block
> nhận proposer reward; attester nhận phần còn lại chia cho inclusion delay, nên
> attestation được include càng sớm thì reward càng cao.

```python
def get_inactivity_penalty_deltas(state: BeaconState) -> tuple[Sequence[Gwei], Sequence[Gwei]]:
    """
    Return inactivity reward/penalty deltas for each validator.
    """
    penalties = [Gwei(0)] * len(state.validators)
    if is_in_inactivity_leak(state):
        matching_target_attestations = get_matching_target_attestations(
            state, get_previous_epoch(state)
        )
        matching_target_attesting_indices = get_unslashed_attesting_indices(
            state, matching_target_attestations
        )
        for index in get_eligible_validator_indices(state):
            # Nếu validator hoạt động tối ưu, khoản này triệt tiêu toàn bộ reward để balance không đổi
            base_reward = get_base_reward(state, index)
            penalties[index] += BASE_REWARDS_PER_EPOCH * base_reward - get_proposer_reward(
                state, index
            )
            if index not in matching_target_attesting_indices:
                effective_balance = state.validators[index].effective_balance
                penalties[index] += (
                    effective_balance
                    * Uint64(get_finality_delay(state))
                    // INACTIVITY_PENALTY_QUOTIENT
                )

    # Không có reward nào gắn với inactivity penalty
    rewards = [Gwei(0)] * len(state.validators)
    return rewards, penalties
```

> 💡 Ghi chú: Trong inactivity leak, ngay cả validator hoạt động tốt cũng không
> được lợi (reward bị triệt tiêu, balance giữ nguyên), còn validator không vote
> đúng target bị penalty tăng dần theo số epoch chưa finality. Cơ chế này làm
> giảm dần tỉ trọng stake của các validator offline cho đến khi phần online
> chiếm lại được 2/3 và chain finalize trở lại.

##### `get_attestation_deltas`

```python
def get_attestation_deltas(state: BeaconState) -> tuple[Sequence[Gwei], Sequence[Gwei]]:
    """
    Return attestation reward/penalty deltas for each validator.
    """
    source_rewards, source_penalties = get_source_deltas(state)
    target_rewards, target_penalties = get_target_deltas(state)
    head_rewards, head_penalties = get_head_deltas(state)
    inclusion_delay_rewards, _ = get_inclusion_delay_deltas(state)
    _, inactivity_penalties = get_inactivity_penalty_deltas(state)

    rewards = [
        source_rewards[index]
        + target_rewards[index]
        + head_rewards[index]
        + inclusion_delay_rewards[index]
        for index in range(len(state.validators))
    ]

    penalties = [
        source_penalties[index]
        + target_penalties[index]
        + head_penalties[index]
        + inactivity_penalties[index]
        for index in range(len(state.validators))
    ]

    return rewards, penalties
```

##### `process_rewards_and_penalties`

```python
def process_rewards_and_penalties(state: BeaconState) -> None:
    # Không áp dụng reward vào cuối `GENESIS_EPOCH` vì reward là cho công việc đã làm ở epoch trước
    if get_current_epoch(state) == GENESIS_EPOCH:
        return

    rewards, penalties = get_attestation_deltas(state)
    for index in range(len(state.validators)):
        increase_balance(state, ValidatorIndex(index), rewards[index])
        decrease_balance(state, ValidatorIndex(index), penalties[index])
```

#### Registry updates

*(Cập nhật danh sách validator: hàng đợi kích hoạt và ejection)*

```python
def process_registry_updates(state: BeaconState) -> None:
    # Xử lý điều kiện được kích hoạt và ejection (buộc rời)
    for index, validator in enumerate(state.validators):
        if is_eligible_for_activation_queue(validator):
            validator.activation_eligibility_epoch = get_current_epoch(state) + 1

        if (
            is_active_validator(validator, get_current_epoch(state))
            and validator.effective_balance <= EJECTION_BALANCE
        ):
            initiate_validator_exit(state, ValidatorIndex(index))

    # Đưa vào hàng đợi các validator đủ điều kiện kích hoạt và chưa được lấy ra khỏi hàng đợi để kích hoạt
    activation_queue = sorted(
        [
            index
            for index, validator in enumerate(state.validators)
            if is_eligible_for_activation(state, validator)
        ],
        # Sắp xếp theo thứ tự thời điểm đặt activation_eligibility_epoch, sau đó theo index
        key=lambda index: (state.validators[index].activation_eligibility_epoch, index),
    )
    # Lấy validator ra khỏi hàng đợi để kích hoạt, tối đa bằng churn limit
    for index in activation_queue[: get_validator_churn_limit(state)]:
        validator = state.validators[index]
        validator.activation_epoch = compute_activation_exit_epoch(get_current_epoch(state))
```

> 💡 Ghi chú: Mỗi epoch chỉ kích hoạt tối đa `get_validator_churn_limit(state)`
> validator, nhằm giới hạn tốc độ thay đổi tập validator. Validator có effective
> balance giảm xuống `EJECTION_BALANCE` hoặc thấp hơn sẽ bị buộc exit.

#### Slashings

```python
def process_slashings(state: BeaconState) -> None:
    epoch = get_current_epoch(state)
    total_balance = get_total_active_balance(state)
    adjusted_total_slashing_balance = min(
        Gwei(sum(state.slashings)) * PROPORTIONAL_SLASHING_MULTIPLIER, total_balance
    )
    for index, validator in enumerate(state.validators):
        if (
            validator.slashed
            and epoch + EPOCHS_PER_SLASHINGS_VECTOR // 2 == validator.withdrawable_epoch
        ):
            increment = EFFECTIVE_BALANCE_INCREMENT  # Tách ra khỏi tử số penalty để tránh tràn Uint64
            penalty_numerator = (
                validator.effective_balance // increment * adjusted_total_slashing_balance
            )
            penalty = penalty_numerator // total_balance * increment
            decrease_balance(state, ValidatorIndex(index), penalty)
```

> 💡 Ghi chú: Đây là penalty slashing "tương quan" (correlation penalty), áp dụng
> ở giữa khoảng thời gian chờ rút của validator bị slashed. Mức phạt tỉ lệ với
> tổng balance bị slashing trong khoảng `EPOCHS_PER_SLASHINGS_VECTOR` epoch gần
> đây: càng nhiều validator bị slashing cùng lúc (dấu hiệu tấn công phối hợp),
> mức phạt càng nặng.

#### Eth1 data votes updates

```python
def process_eth1_data_reset(state: BeaconState) -> None:
    next_epoch = get_current_epoch(state) + 1
    # Reset các vote eth1 data
    if next_epoch % EPOCHS_PER_ETH1_VOTING_PERIOD == 0:
        state.eth1_data_votes = Eth1DataVotes()
```

#### Effective balances updates

```python
def process_effective_balance_updates(state: BeaconState) -> None:
    # Cập nhật effective balance có hysteresis (độ trễ)
    for index, validator in enumerate(state.validators):
        balance = state.balances[index]
        HYSTERESIS_INCREMENT = Uint64(EFFECTIVE_BALANCE_INCREMENT // HYSTERESIS_QUOTIENT)
        DOWNWARD_THRESHOLD = HYSTERESIS_INCREMENT * HYSTERESIS_DOWNWARD_MULTIPLIER
        UPWARD_THRESHOLD = HYSTERESIS_INCREMENT * HYSTERESIS_UPWARD_MULTIPLIER
        if (
            balance + DOWNWARD_THRESHOLD < validator.effective_balance
            or validator.effective_balance + UPWARD_THRESHOLD < balance
        ):
            validator.effective_balance = min(
                balance - balance % EFFECTIVE_BALANCE_INCREMENT, MAX_EFFECTIVE_BALANCE
            )
```

> 💡 Ghi chú: Effective balance chỉ được cập nhật khi balance thực lệch khỏi nó
> vượt một ngưỡng (hysteresis). Nhờ vậy effective balance không dao động liên tục
> khi balance thực biến động nhẹ quanh một bội số của
> `EFFECTIVE_BALANCE_INCREMENT`, giúp giảm số lần phải tính lại hash của state.

#### Slashings balances updates

```python
def process_slashings_reset(state: BeaconState) -> None:
    next_epoch = get_current_epoch(state) + 1
    # Reset slashings
    state.slashings[next_epoch % EPOCHS_PER_SLASHINGS_VECTOR] = Gwei(0)
```

#### Randao mixes updates

```python
def process_randao_mixes_reset(state: BeaconState) -> None:
    current_epoch = get_current_epoch(state)
    next_epoch = current_epoch + 1
    # Đặt randao mix
    state.randao_mixes[next_epoch % EPOCHS_PER_HISTORICAL_VECTOR] = get_randao_mix(
        state, current_epoch
    )
```

#### Historical roots updates

```python
def process_historical_roots_update(state: BeaconState) -> None:
    # Đặt bộ tích lũy historical root
    next_epoch = get_current_epoch(state) + 1
    if next_epoch % Uint64(SLOTS_PER_HISTORICAL_ROOT // SLOTS_PER_EPOCH) == 0:
        historical_batch = HistoricalBatch(
            block_roots=state.block_roots, state_roots=state.state_roots
        )
        state.historical_roots.append(hash_tree_root(historical_batch))
```

#### Participation records rotation

```python
def process_participation_record_updates(state: BeaconState) -> None:
    # Xoay vòng attestation của epoch hiện tại/epoch trước
    state.previous_epoch_attestations = state.current_epoch_attestations
    state.current_epoch_attestations = PendingAttestations()
```

### Block processing

*(Xử lý block)*

```python
def process_block(state: BeaconState, block: BeaconBlock) -> None:
    process_block_header(state, block)
    process_randao(state, block.body)
    process_eth1_data(state, block.body)
    process_operations(state, block.body)
```

#### Block header

```python
def process_block_header(state: BeaconState, block: BeaconBlock) -> None:
    # Kiểm tra slot khớp nhau
    assert block.slot == state.slot
    # Kiểm tra block mới hơn latest block header
    assert block.slot > state.latest_block_header.slot
    # Kiểm tra proposer index là index đúng
    assert block.proposer_index == get_beacon_proposer_index(state)
    # Kiểm tra parent khớp
    assert block.parent_root == hash_tree_root(state.latest_block_header)
    # Lưu cache block hiện tại làm latest block mới
    state.latest_block_header = BeaconBlockHeader(
        slot=block.slot,
        proposer_index=block.proposer_index,
        parent_root=block.parent_root,
        state_root=Root(),  # Sẽ được ghi đè ở lần gọi process_slot tiếp theo
        body_root=hash_tree_root(block.body),
    )

    # Kiểm tra proposer chưa bị slashed
    proposer = state.validators[block.proposer_index]
    assert not proposer.slashed
```

#### RANDAO

```python
def process_randao(state: BeaconState, body: BeaconBlockBody) -> None:
    epoch = get_current_epoch(state)
    # Kiểm tra RANDAO reveal
    proposer = state.validators[get_beacon_proposer_index(state)]
    signing_root = compute_signing_root(epoch, get_domain(state, DOMAIN_RANDAO))
    assert bls.Verify(proposer.pubkey, signing_root, body.randao_reveal)
    # Trộn RANDAO reveal vào mix
    mix = xor(get_randao_mix(state, epoch), sha256(body.randao_reveal))
    state.randao_mixes[epoch % EPOCHS_PER_HISTORICAL_VECTOR] = mix
```

> 💡 Ghi chú: RANDAO reveal là chữ ký BLS của proposer lên số epoch hiện tại. Vì
> chữ ký BLS là tất định, proposer không thể tùy chọn giá trị reveal; cách duy
> nhất để tác động đến randomness là bỏ không propose block (và mất reward).

#### Eth1 data

```python
def process_eth1_data(state: BeaconState, body: BeaconBlockBody) -> None:
    state.eth1_data_votes.append(body.eth1_data)
    if (
        state.eth1_data_votes.count(body.eth1_data) * 2
        > Uint64(EPOCHS_PER_ETH1_VOTING_PERIOD) * SLOTS_PER_EPOCH
    ):
        state.eth1_data = body.eth1_data
```

> 💡 Ghi chú: Mỗi block mang một vote cho `eth1_data`. Khi một giá trị nhận được
> hơn một nửa số slot của voting period, nó trở thành `state.eth1_data` mới.

#### Operations

```python
def process_operations(state: BeaconState, body: BeaconBlockBody) -> None:
    # Kiểm tra các deposit đang chờ được xử lý tới số lượng deposit tối đa
    assert len(body.deposits) == min(
        MAX_DEPOSITS, state.eth1_data.deposit_count - state.eth1_deposit_index
    )

    def for_ops(operations: Sequence[Any], fn: Callable[[BeaconState, Any], None]) -> None:
        for operation in operations:
            fn(state, operation)

    for_ops(body.proposer_slashings, process_proposer_slashing)
    for_ops(body.attester_slashings, process_attester_slashing)
    for_ops(body.attestations, process_attestation)
    for_ops(body.deposits, process_deposit)
    for_ops(body.voluntary_exits, process_voluntary_exit)
```

> 💡 Ghi chú: Block bắt buộc phải chứa đủ số deposit đang chờ (tối đa
> `MAX_DEPOSITS`); proposer không được bỏ qua deposit.

##### Proposer slashings

```python
def process_proposer_slashing(state: BeaconState, proposer_slashing: ProposerSlashing) -> None:
    header_1 = proposer_slashing.signed_header_1.message
    header_2 = proposer_slashing.signed_header_2.message

    # Kiểm tra slot của hai header khớp nhau
    assert header_1.slot == header_2.slot
    # Kiểm tra proposer index của hai header khớp nhau
    assert header_1.proposer_index == header_2.proposer_index
    # Kiểm tra hai header khác nhau
    assert header_1 != header_2
    # Kiểm tra proposer có thể bị slashing
    proposer = state.validators[header_1.proposer_index]
    assert is_slashable_validator(proposer, get_current_epoch(state))
    # Kiểm tra các signature
    for signed_header in (proposer_slashing.signed_header_1, proposer_slashing.signed_header_2):
        domain = get_domain(
            state, DOMAIN_BEACON_PROPOSER, compute_epoch_at_slot(signed_header.message.slot)
        )
        signing_root = compute_signing_root(signed_header.message, domain)
        assert bls.Verify(proposer.pubkey, signing_root, signed_header.signature)

    slash_validator(state, header_1.proposer_index)
```

##### Attester slashings

```python
def process_attester_slashing(state: BeaconState, attester_slashing: AttesterSlashing) -> None:
    attestation_1 = attester_slashing.attestation_1
    attestation_2 = attester_slashing.attestation_2
    assert is_slashable_attestation_data(attestation_1.data, attestation_2.data)
    assert is_valid_indexed_attestation(state, attestation_1)
    assert is_valid_indexed_attestation(state, attestation_2)

    slashed_any = False
    indices = set(attestation_1.attesting_indices).intersection(attestation_2.attesting_indices)
    for index in sorted(indices):
        if is_slashable_validator(state.validators[index], get_current_epoch(state)):
            slash_validator(state, index)
            slashed_any = True
    assert slashed_any
```

> 💡 Ghi chú: Chỉ các validator xuất hiện trong cả hai attestation vi phạm (giao
> của hai tập attesting indices) mới bị slashing. Một attester slashing phải
> slashing được ít nhất một validator, nếu không thì không hợp lệ.

##### Attestations

```python
def process_attestation(state: BeaconState, attestation: Attestation) -> None:
    data = attestation.data
    assert data.target.epoch in (get_previous_epoch(state), get_current_epoch(state))
    assert data.target.epoch == compute_epoch_at_slot(data.slot)
    assert data.slot + MIN_ATTESTATION_INCLUSION_DELAY <= state.slot <= data.slot + SLOTS_PER_EPOCH
    assert data.index < get_committee_count_per_slot(state, data.target.epoch)

    committee = get_beacon_committee(state, data.slot, data.index)
    assert len(attestation.aggregation_bits) == len(committee)

    pending_attestation = PendingAttestation(
        aggregation_bits=attestation.aggregation_bits,
        data=data,
        inclusion_delay=state.slot - data.slot,
        proposer_index=get_beacon_proposer_index(state),
    )

    if data.target.epoch == get_current_epoch(state):
        assert data.source == state.current_justified_checkpoint
        state.current_epoch_attestations.append(pending_attestation)
    else:
        assert data.source == state.previous_justified_checkpoint
        state.previous_epoch_attestations.append(pending_attestation)

    # Kiểm tra signature
    assert is_valid_indexed_attestation(state, get_indexed_attestation(state, attestation))
```

> 💡 Ghi chú: Một attestation chỉ được đưa vào block trong khoảng từ
> `MIN_ATTESTATION_INCLUSION_DELAY` slot đến `SLOTS_PER_EPOCH` slot sau slot của
> nó, và source của nó phải khớp với justified checkpoint tương ứng trong state.
> Attestation hợp lệ được lưu lại dưới dạng `PendingAttestation` để tính reward
> và justification ở cuối epoch.

##### Deposits

```python
def get_validator_from_deposit(
    pubkey: BLSPubkey, withdrawal_credentials: Bytes32, amount: Gwei
) -> Validator:
    effective_balance = min(amount - amount % EFFECTIVE_BALANCE_INCREMENT, MAX_EFFECTIVE_BALANCE)

    return Validator(
        pubkey=pubkey,
        withdrawal_credentials=withdrawal_credentials,
        effective_balance=effective_balance,
        slashed=Boolean(False),
        activation_eligibility_epoch=FAR_FUTURE_EPOCH,
        activation_epoch=FAR_FUTURE_EPOCH,
        exit_epoch=FAR_FUTURE_EPOCH,
        withdrawable_epoch=FAR_FUTURE_EPOCH,
    )
```

```python
def add_validator_to_registry(
    state: BeaconState, pubkey: BLSPubkey, withdrawal_credentials: Bytes32, amount: Gwei
) -> None:
    state.validators.append(get_validator_from_deposit(pubkey, withdrawal_credentials, amount))
    state.balances.append(amount)
```

```python
def apply_deposit(
    state: BeaconState,
    pubkey: BLSPubkey,
    withdrawal_credentials: Bytes32,
    amount: Gwei,
    signature: BLSSignature,
) -> None:
    validator_pubkeys = [validator.pubkey for validator in state.validators]
    if pubkey not in validator_pubkeys:
        # Kiểm tra signature của deposit (proof of possession), vốn không được deposit contract kiểm tra
        deposit_message = DepositMessage(
            pubkey=pubkey,
            withdrawal_credentials=withdrawal_credentials,
            amount=amount,
        )
        # Domain không phụ thuộc fork vì deposit có hiệu lực xuyên suốt các fork
        domain = compute_domain(DOMAIN_DEPOSIT)
        signing_root = compute_signing_root(deposit_message, domain)
        if bls.Verify(pubkey, signing_root, signature):
            add_validator_to_registry(state, pubkey, withdrawal_credentials, amount)
    else:
        # Tăng balance thêm một lượng bằng số tiền deposit
        index = ValidatorIndex(validator_pubkeys.index(pubkey))
        increase_balance(state, index, amount)
```

> 💡 Ghi chú: Nếu pubkey là mới, deposit chỉ tạo validator khi signature hợp lệ;
> deposit có signature sai sẽ bị bỏ qua (không làm block bị invalid), vì deposit
> contract không kiểm tra signature. Nếu pubkey đã tồn tại, deposit chỉ đơn giản
> là nạp thêm balance và không cần kiểm tra signature.

```python
def process_deposit(state: BeaconState, deposit: Deposit) -> None:
    # Kiểm tra Merkle branch
    assert is_valid_merkle_branch(
        leaf=hash_tree_root(deposit.data),
        branch=deposit.proof,
        # Cộng thêm 1 cho phần mix-in độ dài List
        depth=DEPOSIT_CONTRACT_TREE_DEPTH + 1,
        index=state.eth1_deposit_index,
        root=state.eth1_data.deposit_root,
    )

    # Các deposit phải được xử lý theo đúng thứ tự
    state.eth1_deposit_index += 1

    apply_deposit(
        state=state,
        pubkey=deposit.data.pubkey,
        withdrawal_credentials=deposit.data.withdrawal_credentials,
        amount=deposit.data.amount,
        signature=deposit.data.signature,
    )
```

##### Voluntary exits

```python
def process_voluntary_exit(state: BeaconState, signed_voluntary_exit: SignedVoluntaryExit) -> None:
    voluntary_exit = signed_voluntary_exit.message
    validator = state.validators[voluntary_exit.validator_index]
    # Kiểm tra validator đang active
    assert is_active_validator(validator, get_current_epoch(state))
    # Kiểm tra exit chưa được khởi tạo
    assert validator.exit_epoch == FAR_FUTURE_EPOCH
    # Exit phải chỉ định epoch bắt đầu có hiệu lực; trước epoch đó exit không hợp lệ
    assert get_current_epoch(state) >= voluntary_exit.epoch
    # Kiểm tra validator đã active đủ lâu
    assert get_current_epoch(state) >= validator.activation_epoch + SHARD_COMMITTEE_PERIOD
    # Kiểm tra signature
    domain = get_domain(state, DOMAIN_VOLUNTARY_EXIT, voluntary_exit.epoch)
    signing_root = compute_signing_root(voluntary_exit, domain)
    assert bls.Verify(validator.pubkey, signing_root, signed_voluntary_exit.signature)
    # Khởi tạo exit
    initiate_validator_exit(state, voluntary_exit.validator_index)
```
