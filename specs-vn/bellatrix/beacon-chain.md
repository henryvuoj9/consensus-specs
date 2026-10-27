# Bellatrix -- The Beacon Chain

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Types](#types)
  - [New `ExtraData`](#new-extradata)
  - [New `LogsBloom`](#new-logsbloom)
  - [New `Transaction`](#new-transaction)
  - [New `Transactions`](#new-transactions)
- [Constants](#constants)
- [Presets](#presets)
  - [Rewards and penalties](#rewards-and-penalties)
  - [Execution](#execution)
- [Configs](#configs)
  - [Transition settings](#transition-settings)
- [Containers](#containers)
  - [Modified containers](#modified-containers)
    - [`BeaconBlockBody`](#beaconblockbody)
    - [`BeaconState`](#beaconstate)
  - [New containers](#new-containers)
    - [`ExecutionPayload`](#executionpayload)
    - [`ExecutionPayloadHeader`](#executionpayloadheader)
    - [`NewPayloadRequest`](#newpayloadrequest)
- [Helpers](#helpers)
  - [Predicates](#predicates)
    - [`is_merge_transition_complete`](#is_merge_transition_complete)
    - [`is_merge_transition_block`](#is_merge_transition_block)
    - [`is_execution_enabled`](#is_execution_enabled)
  - [Beacon state accessors](#beacon-state-accessors)
    - [Modified `get_inactivity_penalty_deltas`](#modified-get_inactivity_penalty_deltas)
  - [Beacon state mutators](#beacon-state-mutators)
    - [Modified `slash_validator`](#modified-slash_validator)
- [Beacon chain state transition function](#beacon-chain-state-transition-function)
  - [Execution engine](#execution-engine)
    - [Engine APIs](#engine-apis)
    - [`notify_new_payload`](#notify_new_payload)
    - [`is_valid_block_hash`](#is_valid_block_hash)
    - [`verify_and_notify_new_payload`](#verify_and_notify_new_payload)
  - [Block processing](#block-processing)
    - [Execution payload](#execution-payload)
      - [`process_execution_payload`](#process_execution_payload)
  - [Epoch processing](#epoch-processing)
    - [Slashings](#slashings)

<!-- mdformat-toc end -->

## Introduction

Bellatrix là một bản nâng cấp ở tầng đồng thuận (consensus layer) bao gồm một số
tính năng, cụ thể:

- Thực thi transaction (transaction execution)
- Cập nhật các tham số penalty lên giá trị trừng phạt tối đa như đã dự kiến từ
  trước

> 💡 Ghi chú: Bellatrix là phần consensus layer của sự kiện "The Merge". Từ đây,
> mỗi beacon block mang theo một `ExecutionPayload` (tương đương một block của
> execution layer), và beacon chain dựa vào execution engine để xác minh
> payload đó.

## Types

### New `ExtraData`

```python
class ExtraData(ByteList):
    """
    Arbitrary extra data included in an execution payload.
    """

    LIMIT = MAX_EXTRA_DATA_BYTES
```

### New `LogsBloom`

```python
class LogsBloom(ByteVector):
    """
    A Bloom filter aggregating the logs emitted by an execution payload.
    """

    LENGTH = BYTES_PER_LOGS_BLOOM
```

### New `Transaction`

*Lưu ý*: Kiểu `Transaction` hiện chỉ là bản tạm (stub), chưa phải phiên bản cuối
cùng.

*Lưu ý*: Một `Transaction` có thể là một
[typed transaction envelope](https://eips.ethereum.org/EIPS/eip-2718#opaque-byte-array-rather-than-an-rlp-array)
hoặc một legacy transaction.

```python
class Transaction(ByteList):
    """
    An opaque execution-layer transaction, either a typed transaction
    envelope or a legacy RLP-encoded transaction.
    """

    LIMIT = MAX_BYTES_PER_TRANSACTION
```

### New `Transactions`

```python
class Transactions(List[Transaction]):
    """
    A list of execution-layer transactions.
    """

    LIMIT = MAX_TRANSACTIONS_PER_PAYLOAD
```

## Constants

| Name               | Value      |
| ------------------ | ---------- |
| `EMPTY_BLOCK_HASH` | `Hash32()` |

## Presets

### Rewards and penalties

Bellatrix cập nhật một vài giá trị cấu hình để đưa các tham số penalty về giá trị
cuối cùng, ứng với mức bảo mật tối đa.

| Name                                         | Value                          |
| -------------------------------------------- | ------------------------------ |
| `INACTIVITY_PENALTY_QUOTIENT_BELLATRIX`      | `Uint64(2**24)` (= 16,777,216) |
| `MIN_SLASHING_PENALTY_QUOTIENT_BELLATRIX`    | `Uint64(2**5)` (= 32)          |
| `PROPORTIONAL_SLASHING_MULTIPLIER_BELLATRIX` | `Uint64(3)`                    |

> 💡 Ghi chú: Ở Phase 0 và Altair, các tham số này được đặt "nhẹ tay" hơn trong
> giai đoạn đầu của mạng. Bellatrix đưa chúng về mức đầy đủ: inactivity leak
> mạnh hơn, slashing penalty ban đầu là 1/32 effective balance, và hệ số
> slashing tỉ lệ (correlation penalty) là 3.

### Execution

| Name                           | Value                             |
| ------------------------------ | --------------------------------- |
| `MAX_BYTES_PER_TRANSACTION`    | `Uint64(2**30)` (= 1,073,741,824) |
| `MAX_TRANSACTIONS_PER_PAYLOAD` | `Uint64(2**20)` (= 1,048,576)     |
| `BYTES_PER_LOGS_BLOOM`         | `Uint64(2**8)` (= 256)            |
| `MAX_EXTRA_DATA_BYTES`         | `Uint64(2**5)` (= 32)             |

## Configs

### Transition settings

| Name                                   | Value                              |
| -------------------------------------- | ---------------------------------- |
| `TERMINAL_TOTAL_DIFFICULTY`            | `Uint256(58750000000000000000000)` |
| `TERMINAL_BLOCK_HASH`                  | `Hash32()`                         |
| `TERMINAL_BLOCK_HASH_ACTIVATION_EPOCH` | `Epoch(FAR_FUTURE_EPOCH)`          |

## Containers

### Modified containers

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
    sync_aggregate: SyncAggregate
    # [New in Bellatrix]
    execution_payload: ExecutionPayload
```

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
    previous_epoch_participation: EpochParticipation
    current_epoch_participation: EpochParticipation
    justification_bits: JustificationBits
    previous_justified_checkpoint: Checkpoint
    current_justified_checkpoint: Checkpoint
    finalized_checkpoint: Checkpoint
    inactivity_scores: InactivityScores
    current_sync_committee: SyncCommittee
    next_sync_committee: SyncCommittee
    # [New in Bellatrix]
    latest_execution_payload_header: ExecutionPayloadHeader
```

### New containers

#### `ExecutionPayload`

*Lưu ý*: `fee_recipient`, `prev_randao` và `block_number` lần lượt tương ứng với
`beneficiary`, `difficulty` và `number` trong
[the yellow paper](https://ethereum.github.io/yellowpaper/paper.pdf).

```python
class ExecutionPayload(Container):
    parent_hash: Hash32
    fee_recipient: ExecutionAddress
    state_root: Bytes32
    receipts_root: Bytes32
    logs_bloom: LogsBloom
    prev_randao: Bytes32
    block_number: Uint64
    gas_limit: Uint64
    gas_used: Uint64
    timestamp: Uint64
    extra_data: ExtraData
    base_fee_per_gas: Uint256
    block_hash: Hash32
    transactions: Transactions
```

#### `ExecutionPayloadHeader`

*Lưu ý*: `block_hash` là hash của execution block.

> 💡 Ghi chú: `ExecutionPayloadHeader` giống `ExecutionPayload` nhưng thay danh
> sách `transactions` bằng `transactions_root` (hash tree root của danh sách
> đó), giúp beacon state chỉ cần lưu bản tóm tắt gọn nhẹ của payload gần nhất.

```python
class ExecutionPayloadHeader(Container):
    parent_hash: Hash32
    fee_recipient: ExecutionAddress
    state_root: Bytes32
    receipts_root: Bytes32
    logs_bloom: LogsBloom
    prev_randao: Bytes32
    block_number: Uint64
    gas_limit: Uint64
    gas_used: Uint64
    timestamp: Uint64
    extra_data: ExtraData
    base_fee_per_gas: Uint256
    block_hash: Hash32
    transactions_root: Root
```

#### `NewPayloadRequest`

```python
class NewPayloadRequest(Container):
    execution_payload: ExecutionPayload
```

## Helpers

### Predicates

#### `is_merge_transition_complete`

```python
def is_merge_transition_complete(state: BeaconState) -> bool:
    return state.latest_execution_payload_header != ExecutionPayloadHeader.empty()
```

#### `is_merge_transition_block`

```python
def is_merge_transition_block(state: BeaconState, body: BeaconBlockBody) -> bool:
    return (
        not is_merge_transition_complete(state)
        and body.execution_payload != ExecutionPayload.empty()
    )
```

#### `is_execution_enabled`

```python
def is_execution_enabled(state: BeaconState, body: BeaconBlockBody) -> bool:
    return is_merge_transition_block(state, body) or is_merge_transition_complete(state)
```

> 💡 Ghi chú: Ba predicate trên mô tả quá trình merge: trước merge, state chưa
> có execution payload header nào (header rỗng); block merge transition là block
> đầu tiên chứa một payload không rỗng; sau đó merge được coi là hoàn tất và
> execution luôn được bật cho mọi block.

### Beacon state accessors

#### Modified `get_inactivity_penalty_deltas`

*Lưu ý*: Hàm `get_inactivity_penalty_deltas` được sửa đổi để dùng
`INACTIVITY_PENALTY_QUOTIENT_BELLATRIX`.

```python
def get_inactivity_penalty_deltas(state: BeaconState) -> tuple[Sequence[Gwei], Sequence[Gwei]]:
    """
    Return the inactivity penalty deltas by considering timely target participation flags and inactivity scores.
    """
    rewards = [Gwei(0)] * len(state.validators)
    penalties = [Gwei(0)] * len(state.validators)
    previous_epoch = get_previous_epoch(state)
    matching_target_indices = get_unslashed_participating_indices(
        state, TIMELY_TARGET_FLAG_INDEX, previous_epoch
    )
    for index in get_eligible_validator_indices(state):
        if index not in matching_target_indices:
            penalty_numerator = (
                state.validators[index].effective_balance * state.inactivity_scores[index]
            )
            # [Modified in Bellatrix]
            penalty_denominator = INACTIVITY_SCORE_BIAS * INACTIVITY_PENALTY_QUOTIENT_BELLATRIX
            penalties[index] += penalty_numerator // penalty_denominator
    return rewards, penalties
```

### Beacon state mutators

#### Modified `slash_validator`

*Lưu ý*: Hàm `slash_validator` được sửa đổi để dùng
`MIN_SLASHING_PENALTY_QUOTIENT_BELLATRIX`.

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
    # [Modified in Bellatrix]
    slashing_penalty = validator.effective_balance // MIN_SLASHING_PENALTY_QUOTIENT_BELLATRIX
    decrease_balance(state, slashed_index, slashing_penalty)

    # Thưởng cho proposer và whistleblower (người tố giác)
    proposer_index = get_beacon_proposer_index(state)
    if whistleblower_index is None:
        whistleblower_index = proposer_index
    whistleblower_reward = validator.effective_balance // WHISTLEBLOWER_REWARD_QUOTIENT
    proposer_reward = whistleblower_reward * PROPOSER_WEIGHT // WEIGHT_DENOMINATOR
    increase_balance(state, proposer_index, proposer_reward)
    increase_balance(state, whistleblower_index, whistleblower_reward - proposer_reward)
```

## Beacon chain state transition function

### Execution engine

#### Engine APIs

Protocol `ExecutionEngine` (phụ thuộc vào cách hiện thực của từng client) đóng
gói logic của hệ thống con execution thông qua:

- một state object `self.execution_state` có kiểu `ExecutionState`
- một hàm thông báo `self.notify_new_payload`, có thể áp dụng thay đổi lên
  `self.execution_state`

Phần thân của các hàm này phụ thuộc vào cách hiện thực. Engine API có thể được
dùng để hiện thực hàm này và các hàm được định nghĩa tương tự thông qua một
execution engine bên ngoài.

> 💡 Ghi chú: Trong thực tế, consensus client gọi execution client (Geth,
> Nethermind, Besu, Erigon, Reth, ...) qua Engine API (JSON-RPC, ví dụ
> `engine_newPayload`) để thực hiện các hàm này.

#### `notify_new_payload`

`notify_new_payload` là một hàm được truy cập thông qua module
`EXECUTION_ENGINE`, module này hiện thực protocol `ExecutionEngine`.

```python
def notify_new_payload(self: ExecutionEngine, execution_payload: ExecutionPayload) -> bool:
    """
    Return ``True`` if and only if ``execution_payload`` is valid with respect to ``self.execution_state``.
    """
```

#### `is_valid_block_hash`

```python
def is_valid_block_hash(self: ExecutionEngine, execution_payload: ExecutionPayload) -> bool:
    """
    Return ``True`` if and only if ``execution_payload.block_hash`` is computed correctly.
    """
```

#### `verify_and_notify_new_payload`

```python
def verify_and_notify_new_payload(
    self: ExecutionEngine, new_payload_request: NewPayloadRequest
) -> bool:
    """
    Return ``True`` if and only if ``new_payload_request`` is valid with respect to ``self.execution_state``.
    """
    execution_payload = new_payload_request.execution_payload

    if b"" in execution_payload.transactions:
        return False

    if not self.is_valid_block_hash(execution_payload):
        return False

    if not self.notify_new_payload(execution_payload):
        return False

    return True
```

> 💡 Ghi chú: Payload bị coi là không hợp lệ nếu chứa transaction rỗng
> (`b""`), nếu `block_hash` tính sai, hoặc nếu execution engine báo payload
> không hợp lệ.

### Block processing

*Lưu ý*: Lời gọi `process_execution_payload` phải diễn ra trước lời gọi
`process_randao`, vì hàm đầu tiên phụ thuộc vào `randao_mix` được tính từ phần
reveal của block trước đó.

> 💡 Ghi chú: `payload.prev_randao` phải bằng RANDAO mix *trước khi* trộn
> `randao_reveal` của block hiện tại vào. Nếu gọi `process_randao` trước, mix
> trong state sẽ đã bị cập nhật và phép kiểm tra sẽ sai.

```python
def process_block(state: BeaconState, block: BeaconBlock) -> None:
    process_block_header(state, block)
    if is_execution_enabled(state, block.body):
        # [New in Bellatrix]
        process_execution_payload(state, block.body, EXECUTION_ENGINE)
    process_randao(state, block.body)
    process_eth1_data(state, block.body)
    process_operations(state, block.body)
    process_sync_aggregate(state, block.body.sync_aggregate)
```

#### Execution payload

##### `process_execution_payload`

```python
def process_execution_payload(
    state: BeaconState, body: BeaconBlockBody, execution_engine: ExecutionEngine
) -> None:
    payload = body.execution_payload

    # Kiểm tra parent hash nhất quán với execution payload header trước đó
    if is_merge_transition_complete(state):
        assert payload.parent_hash == state.latest_execution_payload_header.block_hash
    # Kiểm tra prev_randao
    assert payload.prev_randao == get_randao_mix(state, get_current_epoch(state))
    # Kiểm tra timestamp
    assert payload.timestamp == compute_time_at_slot(state.genesis_time, state.slot)
    # Kiểm tra execution payload hợp lệ
    assert execution_engine.verify_and_notify_new_payload(
        NewPayloadRequest(execution_payload=payload)
    )
    # Cache execution payload header
    state.latest_execution_payload_header = ExecutionPayloadHeader(
        parent_hash=payload.parent_hash,
        fee_recipient=payload.fee_recipient,
        state_root=payload.state_root,
        receipts_root=payload.receipts_root,
        logs_bloom=payload.logs_bloom,
        prev_randao=payload.prev_randao,
        block_number=payload.block_number,
        gas_limit=payload.gas_limit,
        gas_used=payload.gas_used,
        timestamp=payload.timestamp,
        extra_data=payload.extra_data,
        base_fee_per_gas=payload.base_fee_per_gas,
        block_hash=payload.block_hash,
        transactions_root=hash_tree_root(payload.transactions),
    )
```

### Epoch processing

#### Slashings

*Lưu ý*: Hàm `process_slashings` được sửa đổi để dùng
`PROPORTIONAL_SLASHING_MULTIPLIER_BELLATRIX`.

```python
def process_slashings(state: BeaconState) -> None:
    epoch = get_current_epoch(state)
    total_balance = get_total_active_balance(state)
    adjusted_total_slashing_balance = min(
        Gwei(sum(state.slashings))
        # [Modified in Bellatrix]
        * PROPORTIONAL_SLASHING_MULTIPLIER_BELLATRIX,
        total_balance,
    )
    for index, validator in enumerate(state.validators):
        if (
            validator.slashed
            and epoch + EPOCHS_PER_SLASHINGS_VECTOR // 2 == validator.withdrawable_epoch
        ):
            increment = EFFECTIVE_BALANCE_INCREMENT  # Factored out from penalty numerator to avoid Uint64 overflow
            penalty_numerator = (
                validator.effective_balance // increment * adjusted_total_slashing_balance
            )
            penalty = penalty_numerator // total_balance * increment
            decrease_balance(state, ValidatorIndex(index), penalty)
```
