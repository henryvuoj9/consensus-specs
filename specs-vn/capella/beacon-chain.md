# Capella -- The Beacon Chain

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Types](#types)
  - [New `BLSToExecutionChanges`](#new-blstoexecutionchanges)
  - [New `HistoricalSummaries`](#new-historicalsummaries)
  - [New `WithdrawalIndex`](#new-withdrawalindex)
  - [New `Withdrawals`](#new-withdrawals)
- [Constants](#constants)
  - [Domains](#domains)
- [Presets](#presets)
  - [Max operations per block](#max-operations-per-block)
  - [Execution](#execution)
  - [Withdrawals processing](#withdrawals-processing)
- [Containers](#containers)
  - [New containers](#new-containers)
    - [`Withdrawal`](#withdrawal)
    - [`BLSToExecutionChange`](#blstoexecutionchange)
    - [`SignedBLSToExecutionChange`](#signedblstoexecutionchange)
    - [`HistoricalSummary`](#historicalsummary)
  - [Modified containers](#modified-containers)
    - [`ExecutionPayload`](#executionpayload)
    - [`ExecutionPayloadHeader`](#executionpayloadheader)
    - [`BeaconBlockBody`](#beaconblockbody)
    - [`BeaconState`](#beaconstate)
- [Dataclasses](#dataclasses)
  - [New dataclasses](#new-dataclasses)
    - [`ExpectedWithdrawals`](#expectedwithdrawals)
- [Helpers](#helpers)
  - [Predicates](#predicates)
    - [`has_eth1_withdrawal_credential`](#has_eth1_withdrawal_credential)
    - [`is_fully_withdrawable_validator`](#is_fully_withdrawable_validator)
    - [`is_partially_withdrawable_validator`](#is_partially_withdrawable_validator)
- [Beacon chain state transition function](#beacon-chain-state-transition-function)
  - [Epoch processing](#epoch-processing)
    - [Historical summaries updates](#historical-summaries-updates)
  - [Block processing](#block-processing)
    - [New `get_balance_after_withdrawals`](#new-get_balance_after_withdrawals)
    - [New `get_validators_sweep_withdrawals`](#new-get_validators_sweep_withdrawals)
    - [New `get_expected_withdrawals`](#new-get_expected_withdrawals)
    - [New `apply_withdrawals`](#new-apply_withdrawals)
    - [New `update_next_withdrawal_index`](#new-update_next_withdrawal_index)
    - [New `update_next_withdrawal_validator_index`](#new-update_next_withdrawal_validator_index)
    - [New `process_withdrawals`](#new-process_withdrawals)
    - [Modified `process_execution_payload`](#modified-process_execution_payload)
    - [Modified `process_operations`](#modified-process_operations)
    - [New `process_bls_to_execution_change`](#new-process_bls_to_execution_change)

<!-- mdformat-toc end -->

## Introduction

Capella là một bản nâng cấp của consensus layer, bao gồm một loạt tính năng liên
quan đến withdrawal (rút tiền) của validator, cụ thể:

- Tự động withdrawal toàn bộ cho các validator đã ở trạng thái `withdrawable`
  (có thể rút).
- Cơ chế "quét" (sweep) để thực hiện partial withdrawal (rút một phần) cho các
  validator có withdrawal credential dạng 0x01 và có balance vượt quá
  `MAX_EFFECTIVE_BALANCE`.
- Một operation mới cho phép chuyển withdrawal credential từ phiên bản
  `BLS_WITHDRAWAL_PREFIX` sang phiên bản `ETH1_ADDRESS_WITHDRAWAL_PREFIX`, nhờ đó
  validator mới có thể thực hiện withdrawal.

Một tính năng mới khác là các accumulator lịch sử mới, độc lập cho state và cho
block, thay thế cho `historical_roots` gộp chung (singular) ban đầu. Với các
accumulator này, ta có thể kiểm chứng toàn bộ lịch sử block dẫn đến một state cụ
thể mà không cần thêm bất kỳ thông tin nào ngoài chính state đó và các block.

> 💡 Ghi chú: Trước Capella, validator chỉ có thể bị buộc rời mạng (exit) nhưng
> tiền vẫn bị "khóa" trên beacon chain. Capella là bản nâng cấp đầu tiên thực sự
> chuyển ETH từ consensus layer sang địa chỉ trên execution layer. Withdrawal
> được thực hiện tự động trong mỗi block (không cần validator gửi giao dịch), dựa
> trên một con trỏ quét vòng tròn qua danh sách validator.

## Types

Chúng ta định nghĩa các kiểu Python tùy biến sau để phục vụ type hinting và giúp
code dễ đọc hơn:

### New `BLSToExecutionChanges`

```python
class BLSToExecutionChanges(List[SignedBLSToExecutionChange]):
    """
    The signed BLS-to-execution credential changes included in a beacon
    block.
    """

    LIMIT = MAX_BLS_TO_EXECUTION_CHANGES
```

### New `HistoricalSummaries`

```python
class HistoricalSummaries(List[HistoricalSummary]):
    """
    Summaries of the chain's block and state root history.
    """

    LIMIT = HISTORICAL_ROOTS_LIMIT
```

### New `WithdrawalIndex`

```python
class WithdrawalIndex(Uint64):
    """
    The index of a withdrawal, counting all withdrawals ever made.
    """
```

### New `Withdrawals`

```python
class Withdrawals(List[Withdrawal]):
    """
    A list of withdrawals.
    """

    LIMIT = MAX_WITHDRAWALS_PER_PAYLOAD
```

## Constants

### Domains

| Name                             | Value                      |
| -------------------------------- | -------------------------- |
| `DOMAIN_BLS_TO_EXECUTION_CHANGE` | `DomainType("0x0A000000")` |

## Presets

### Max operations per block

| Name                           | Value                 |
| ------------------------------ | --------------------- |
| `MAX_BLS_TO_EXECUTION_CHANGES` | `Uint64(2**4)` (= 16) |

### Execution

| Name                          | Value                 | Description                                              |
| ----------------------------- | --------------------- | -------------------------------------------------------- |
| `MAX_WITHDRAWALS_PER_PAYLOAD` | `Uint64(2**4)` (= 16) | Số lượng withdrawal tối đa được phép trong mỗi payload   |

### Withdrawals processing

| Name                                   | Value                      |
| -------------------------------------- | -------------------------- |
| `MAX_VALIDATORS_PER_WITHDRAWALS_SWEEP` | `Uint64(2**14)` (= 16,384) |

> 💡 Ghi chú: `MAX_VALIDATORS_PER_WITHDRAWALS_SWEEP` giới hạn số validator được
> duyệt qua trong một lần sweep (mỗi block), để chi phí xử lý block luôn bị chặn
> trên, kể cả khi rất ít validator đủ điều kiện withdrawal.

## Containers

### New containers

#### `Withdrawal`

```python
class Withdrawal(Container):
    index: WithdrawalIndex
    validator_index: ValidatorIndex
    address: ExecutionAddress
    amount: Gwei
```

#### `BLSToExecutionChange`

```python
class BLSToExecutionChange(Container):
    validator_index: ValidatorIndex
    from_bls_pubkey: BLSPubkey
    to_execution_address: ExecutionAddress
```

#### `SignedBLSToExecutionChange`

```python
class SignedBLSToExecutionChange(Container):
    message: BLSToExecutionChange
    signature: BLSSignature
```

#### `HistoricalSummary`

*Lưu ý*: `HistoricalSummary` có các thành phần khớp với `HistoricalBatch` của
phase0, khiến hai kiểu này \*tương thích về hash_tree_root (tức là cho ra cùng
một root nếu cùng dữ liệu).

```python
class HistoricalSummary(Container):
    block_summary_root: Root
    state_summary_root: Root
```

### Modified containers

#### `ExecutionPayload`

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
    # [New in Capella]
    withdrawals: Withdrawals
```

#### `ExecutionPayloadHeader`

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
    # [New in Capella]
    withdrawals_root: Root
```

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
    execution_payload: ExecutionPayload
    # [New in Capella]
    bls_to_execution_changes: BLSToExecutionChanges
```

#### `BeaconState`

*Lưu ý*: `historical_roots` bị "đóng băng" (không cập nhật thêm) kể từ Capella
và được thay thế bởi `historical_summaries`.

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
    # [Modified in Capella]
    latest_execution_payload_header: ExecutionPayloadHeader
    # [New in Capella]
    next_withdrawal_index: WithdrawalIndex
    # [New in Capella]
    next_withdrawal_validator_index: ValidatorIndex
    # [New in Capella]
    historical_summaries: HistoricalSummaries
```

> 💡 Ghi chú: `next_withdrawal_index` là bộ đếm toàn cục, tăng dần, gán cho mỗi
> withdrawal một chỉ số duy nhất. `next_withdrawal_validator_index` là "con trỏ"
> chỉ ra validator mà lần sweep tiếp theo sẽ bắt đầu duyệt từ đó.

## Dataclasses

### New dataclasses

#### `ExpectedWithdrawals`

```python
@dataclass
class ExpectedWithdrawals:
    withdrawals: Sequence[Withdrawal]
    processed_sweep_withdrawals_count: Uint64
```

## Helpers

### Predicates

#### `has_eth1_withdrawal_credential`

```python
def has_eth1_withdrawal_credential(validator: Validator) -> bool:
    """
    Check if ``validator`` has an 0x01 prefixed "eth1" withdrawal credential.
    """
    return validator.withdrawal_credentials[:1] == ETH1_ADDRESS_WITHDRAWAL_PREFIX
```

#### `is_fully_withdrawable_validator`

```python
def is_fully_withdrawable_validator(validator: Validator, balance: Gwei, epoch: Epoch) -> bool:
    """
    Check if ``validator`` is fully withdrawable.
    """
    return (
        has_eth1_withdrawal_credential(validator)
        and validator.withdrawable_epoch <= epoch
        and balance > 0
    )
```

#### `is_partially_withdrawable_validator`

```python
def is_partially_withdrawable_validator(validator: Validator, balance: Gwei) -> bool:
    """
    Check if ``validator`` is partially withdrawable.
    """
    has_max_effective_balance = validator.effective_balance == MAX_EFFECTIVE_BALANCE
    has_excess_balance = balance > MAX_EFFECTIVE_BALANCE
    return (
        has_eth1_withdrawal_credential(validator)
        and has_max_effective_balance
        and has_excess_balance
    )
```

> 💡 Ghi chú: Validator được *rút toàn bộ* khi đã có credential 0x01, đã đến
> `withdrawable_epoch` và còn balance > 0. Validator được *rút một phần* khi có
> credential 0x01, effective balance đã đạt mức tối đa và balance thực tế vượt
> quá `MAX_EFFECTIVE_BALANCE` — phần vượt này (thường là reward tích lũy) sẽ được
> rút ra.

## Beacon chain state transition function

### Epoch processing

*Lưu ý*: Trong Capella, hàm `process_historical_summaries_update` thay thế cho
`process_historical_roots_update`.

```python
def process_epoch(state: BeaconState) -> None:
    process_justification_and_finalization(state)
    process_inactivity_updates(state)
    process_rewards_and_penalties(state)
    process_registry_updates(state)
    process_slashings(state)
    process_eth1_data_reset(state)
    process_effective_balance_updates(state)
    process_slashings_reset(state)
    process_randao_mixes_reset(state)
    # [Modified in Capella]
    # Đã loại bỏ `process_historical_roots_update`
    # [New in Capella]
    process_historical_summaries_update(state)
    process_participation_flag_updates(state)
    process_sync_committee_updates(state)
```

#### Historical summaries updates

```python
def process_historical_summaries_update(state: BeaconState) -> None:
    # Cập nhật accumulator lịch sử của block root.
    next_epoch = get_current_epoch(state) + 1
    if next_epoch % Uint64(SLOTS_PER_HISTORICAL_ROOT // SLOTS_PER_EPOCH) == 0:
        historical_summary = HistoricalSummary(
            block_summary_root=hash_tree_root(state.block_roots),
            state_summary_root=hash_tree_root(state.state_roots),
        )
        state.historical_summaries.append(historical_summary)
```

> 💡 Ghi chú: Cứ mỗi `SLOTS_PER_HISTORICAL_ROOT` slot (khi các vòng đệm
> `block_roots`/`state_roots` vừa được ghi đầy một vòng), một `HistoricalSummary`
> chứa hai root riêng biệt của block roots và state roots được thêm vào state.
> Khác với `historical_roots` cũ (chỉ lưu một root gộp), việc tách riêng cho phép
> chứng minh trực tiếp một block root thuộc lịch sử chain.

### Block processing

```python
def process_block(state: BeaconState, block: BeaconBlock) -> None:
    process_block_header(state, block)
    # [Modified in Capella]
    # Đã loại bỏ lời gọi `is_execution_enabled`
    # [New in Capella]
    process_withdrawals(state, block.body.execution_payload)
    # [Modified in Capella]
    process_execution_payload(state, block.body, EXECUTION_ENGINE)
    process_randao(state, block.body)
    process_eth1_data(state, block.body)
    # [Modified in Capella]
    process_operations(state, block.body)
    process_sync_aggregate(state, block.body.sync_aggregate)
```

> 💡 Ghi chú: `process_withdrawals` chạy *trước* `process_execution_payload` và
> trước các operation khác trong block. Danh sách withdrawal trong payload phải
> khớp chính xác với danh sách mà beacon state tính ra.

#### New `get_balance_after_withdrawals`

*(Tính balance còn lại của một validator sau khi trừ đi các withdrawal đã được
xếp vào danh sách trước đó trong cùng block.)*

```python
def get_balance_after_withdrawals(
    state: BeaconState,
    validator_index: ValidatorIndex,
    withdrawals: Sequence[Withdrawal],
) -> Gwei:
    withdrawn = sum(
        withdrawal.amount
        for withdrawal in withdrawals
        if withdrawal.validator_index == validator_index
    )
    return state.balances[validator_index] - withdrawn
```

#### New `get_validators_sweep_withdrawals`

*(Duyệt vòng tròn qua danh sách validator, bắt đầu từ
`state.next_withdrawal_validator_index`, để tạo các withdrawal toàn bộ hoặc một
phần.)*

```python
def get_validators_sweep_withdrawals(
    state: BeaconState,
    withdrawal_index: WithdrawalIndex,
    prior_withdrawals: Sequence[Withdrawal],
) -> tuple[Sequence[Withdrawal], WithdrawalIndex, Uint64]:
    epoch = get_current_epoch(state)
    validators_limit = min(len(state.validators), MAX_VALIDATORS_PER_WITHDRAWALS_SWEEP)
    withdrawals_limit = MAX_WITHDRAWALS_PER_PAYLOAD
    # Phải còn ít nhất một chỗ trống dành cho các withdrawal từ validator sweep
    assert len(prior_withdrawals) < withdrawals_limit

    processed_count = Uint64(0)
    withdrawals: list[Withdrawal] = []
    validator_index = state.next_withdrawal_validator_index
    for _ in range(validators_limit):
        all_withdrawals = list(prior_withdrawals) + withdrawals
        has_reached_limit = len(all_withdrawals) >= withdrawals_limit
        if has_reached_limit:
            break

        validator = state.validators[validator_index]
        balance = get_balance_after_withdrawals(state, validator_index, all_withdrawals)
        if is_fully_withdrawable_validator(validator, balance, epoch):
            withdrawals.append(
                Withdrawal(
                    index=withdrawal_index,
                    validator_index=validator_index,
                    address=ExecutionAddress(validator.withdrawal_credentials[12:]),
                    amount=balance,
                )
            )
            withdrawal_index += 1
        elif is_partially_withdrawable_validator(validator, balance):
            withdrawals.append(
                Withdrawal(
                    index=withdrawal_index,
                    validator_index=validator_index,
                    address=ExecutionAddress(validator.withdrawal_credentials[12:]),
                    amount=balance - MAX_EFFECTIVE_BALANCE,
                )
            )
            withdrawal_index += 1

        validator_index = (validator_index + 1) % len(state.validators)
        processed_count += 1

    return withdrawals, withdrawal_index, processed_count
```

> 💡 Ghi chú: Vòng lặp dừng khi đã đủ `MAX_WITHDRAWALS_PER_PAYLOAD` withdrawal
> hoặc khi đã duyệt `validators_limit` validator. Địa chỉ nhận tiền là 20 byte
> cuối của `withdrawal_credentials` (byte 12 trở đi). Hàm trả về danh sách
> withdrawal mới, `withdrawal_index` kế tiếp và số validator đã duyệt.

#### New `get_expected_withdrawals`

```python
def get_expected_withdrawals(state: BeaconState) -> ExpectedWithdrawals:
    withdrawal_index = state.next_withdrawal_index
    withdrawals: list[Withdrawal] = []

    # Lấy các withdrawal từ validator sweep
    validators_sweep_withdrawals, withdrawal_index, processed_validators_sweep_count = (
        get_validators_sweep_withdrawals(state, withdrawal_index, withdrawals)
    )
    withdrawals.extend(validators_sweep_withdrawals)

    return ExpectedWithdrawals(
        withdrawals,
        processed_validators_sweep_count,
    )
```

#### New `apply_withdrawals`

```python
def apply_withdrawals(state: BeaconState, withdrawals: Sequence[Withdrawal]) -> None:
    for withdrawal in withdrawals:
        decrease_balance(state, withdrawal.validator_index, withdrawal.amount)
```

#### New `update_next_withdrawal_index`

```python
def update_next_withdrawal_index(state: BeaconState, withdrawals: Sequence[Withdrawal]) -> None:
    # Cập nhật next withdrawal index nếu block này có chứa withdrawal
    if len(withdrawals) != 0:
        latest_withdrawal = withdrawals[-1]
        state.next_withdrawal_index = latest_withdrawal.index + 1
```

#### New `update_next_withdrawal_validator_index`

```python
def update_next_withdrawal_validator_index(
    state: BeaconState, withdrawals: Sequence[Withdrawal]
) -> None:
    # Cập nhật validator index tiếp theo để bắt đầu lần withdrawal sweep kế tiếp
    if len(withdrawals) == MAX_WITHDRAWALS_PER_PAYLOAD:
        # Lần sweep tiếp theo bắt đầu ngay sau validator index của withdrawal cuối cùng
        next_validator_index = (withdrawals[-1].validator_index + 1) % len(state.validators)
        state.next_withdrawal_validator_index = next_validator_index
    else:
        # Nếu không đủ một bộ withdrawal đầy đủ, dịch con trỏ sweep đi đúng độ dài tối đa của một lần sweep
        next_index = state.next_withdrawal_validator_index + MAX_VALIDATORS_PER_WITHDRAWALS_SWEEP
        next_validator_index = next_index % len(state.validators)
        state.next_withdrawal_validator_index = next_validator_index
```

> 💡 Ghi chú: Nếu payload đã đầy (đủ `MAX_WITHDRAWALS_PER_PAYLOAD`), lần sweep
> sau tiếp tục ngay từ validator kế tiếp sau withdrawal cuối, để không bỏ sót ai.
> Nếu chưa đầy, nghĩa là toàn bộ `MAX_VALIDATORS_PER_WITHDRAWALS_SWEEP` validator
> đã được duyệt, nên con trỏ được dịch đi đúng chừng đó.

#### New `process_withdrawals`

```python
def process_withdrawals(state: BeaconState, payload: ExecutionPayload) -> None:
    # Lấy danh sách withdrawal kỳ vọng
    expected = get_expected_withdrawals(state)
    assert list(payload.withdrawals) == expected.withdrawals

    # Áp dụng các withdrawal kỳ vọng
    apply_withdrawals(state, expected.withdrawals)

    # Cập nhật các trường liên quan đến withdrawal trong state
    update_next_withdrawal_index(state, expected.withdrawals)
    update_next_withdrawal_validator_index(state, expected.withdrawals)
```

#### Modified `process_execution_payload`

*Lưu ý*: Hàm `process_execution_payload` được sửa đổi để dùng kiểu
`ExecutionPayloadHeader` mới và loại bỏ bước kiểm tra
`is_merge_transition_complete` (vì sau Capella, merge chắc chắn đã hoàn tất).

```python
def process_execution_payload(
    state: BeaconState, body: BeaconBlockBody, execution_engine: ExecutionEngine
) -> None:
    payload = body.execution_payload
    # [Modified in Capella]
    # Đã loại bỏ bước kiểm tra `is_merge_transition_complete`
    # Kiểm tra parent hash khớp với execution payload header trước đó
    assert payload.parent_hash == state.latest_execution_payload_header.block_hash
    # Kiểm tra prev_randao
    assert payload.prev_randao == get_randao_mix(state, get_current_epoch(state))
    # Kiểm tra timestamp
    assert payload.timestamp == compute_time_at_slot(state.genesis_time, state.slot)
    # Kiểm tra execution payload hợp lệ
    assert execution_engine.verify_and_notify_new_payload(
        NewPayloadRequest(execution_payload=payload)
    )
    # Lưu cache execution payload header
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
        # [New in Capella]
        withdrawals_root=hash_tree_root(payload.withdrawals),
    )
```

#### Modified `process_operations`

*Lưu ý*: Hàm `process_operations` được sửa đổi để xử lý thêm các operation
`BLSToExecutionChange` có trong block.

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
    # [New in Capella]
    for_ops(body.bls_to_execution_changes, process_bls_to_execution_change)
```

#### New `process_bls_to_execution_change`

```python
def process_bls_to_execution_change(
    state: BeaconState, signed_address_change: SignedBLSToExecutionChange
) -> None:
    address_change = signed_address_change.message

    assert address_change.validator_index < len(state.validators)

    validator = state.validators[address_change.validator_index]

    assert validator.withdrawal_credentials[:1] == BLS_WITHDRAWAL_PREFIX
    assert validator.withdrawal_credentials[1:] == sha256(address_change.from_bls_pubkey)[1:]

    # Domain không phụ thuộc fork vì thay đổi địa chỉ có hiệu lực xuyên suốt các fork
    domain = compute_domain(
        DOMAIN_BLS_TO_EXECUTION_CHANGE, genesis_validators_root=state.genesis_validators_root
    )
    signing_root = compute_signing_root(address_change, domain)
    assert bls.Verify(address_change.from_bls_pubkey, signing_root, signed_address_change.signature)

    validator.withdrawal_credentials = Bytes32(
        ETH1_ADDRESS_WITHDRAWAL_PREFIX + b"\x00" * 11 + address_change.to_execution_address
    )
```

> 💡 Ghi chú: Để đổi credential, validator phải đang dùng credential dạng BLS
> (0x00), và public key `from_bls_pubkey` phải khớp với hash đã cam kết trong
> credential (so sánh từ byte thứ 1 trở đi). Chữ ký được kiểm tra với domain tính
> từ `genesis_validators_root` và fork version mặc định `GENESIS_FORK_VERSION`
> (không gắn với fork hiện tại), nên một message đã ký vẫn hợp lệ sau các lần nâng cấp. Credential mới có
> dạng: `0x01` + 11 byte 0 + 20 byte địa chỉ execution.
