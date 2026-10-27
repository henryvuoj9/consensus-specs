# EIP-8148 -- The Beacon Chain

*Lưu ý*: Tài liệu này vẫn đang được soạn thảo, dành cho các nhà nghiên cứu và
người triển khai.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Types](#types)
  - [New `SweepThresholdRequests`](#new-sweepthresholdrequests)
  - [New `SweepThresholds`](#new-sweepthresholds)
- [Constants](#constants)
  - [New execution layer triggered request type](#new-execution-layer-triggered-request-type)
  - [Sweep threshold validation](#sweep-threshold-validation)
- [Presets](#presets)
  - [Execution](#execution)
- [Containers](#containers)
  - [Modified containers](#modified-containers)
    - [`BeaconState`](#beaconstate)
    - [`ExecutionRequests`](#executionrequests)
  - [New containers](#new-containers)
    - [`SetSweepThresholdRequest`](#setsweepthresholdrequest)
- [Helper functions](#helper-functions)
  - [Math](#math)
    - [New `bytes_to_uint16`](#new-bytes_to_uint16)
  - [Predicates](#predicates)
    - [Modified `is_partially_withdrawable_validator`](#modified-is_partially_withdrawable_validator)
  - [Misc](#misc)
    - [New `get_initial_sweep_threshold`](#new-get_initial_sweep_threshold)
    - [New `get_effective_sweep_threshold`](#new-get_effective_sweep_threshold)
  - [Validator registry](#validator-registry)
    - [Modified `add_validator_to_registry`](#modified-add_validator_to_registry)
  - [Beacon state mutators](#beacon-state-mutators)
    - [Modified `switch_to_compounding_validator`](#modified-switch_to_compounding_validator)
- [Beacon chain state transition function](#beacon-chain-state-transition-function)
  - [Epoch processing](#epoch-processing)
    - [Modified `process_effective_balance_updates`](#modified-process_effective_balance_updates)
  - [Block processing](#block-processing)
    - [Execution payload](#execution-payload)
      - [Modified `get_execution_requests_list`](#modified-get_execution_requests_list)
    - [Withdrawals](#withdrawals)
      - [Modified `get_validators_sweep_withdrawals`](#modified-get_validators_sweep_withdrawals)
    - [Operations](#operations)
      - [New `process_set_sweep_threshold_request`](#new-process_set_sweep_threshold_request)
    - [Parent execution payload](#parent-execution-payload)
      - [Modified `apply_parent_execution_payload`](#modified-apply_parent_execution_payload)

<!-- mdformat-toc end -->

## Introduction

Bản nâng cấp này bổ sung vào beacon chain tính năng sweep threshold (ngưỡng
sweep) tùy chỉnh cho từng validator, như một phần của bản nâng cấp EIP-8148.

Tài liệu này đặc tả những thay đổi trên beacon chain cần thiết để hỗ trợ các
ngưỡng tùy chỉnh đó. Bản nâng cấp giới thiệu một loại request mới nằm trong
execution payload, được kích hoạt bởi các giao dịch trên execution layer, dùng
để cập nhật cấu hình sweep của một validator trong beacon state. Nhờ đó,
validator có thể kiểm soát việc rút balance của mình chính xác hơn.

> 💡 Ghi chú: "Sweep" là cơ chế mà beacon chain tự động quét lần lượt qua các
> validator và tạo withdrawal cho phần balance vượt quá một mức nhất định
> (partial withdrawal). Trước EIP-8148, mức này cố định bằng max effective
> balance của validator (`MIN_ACTIVATION_BALANCE` = 32 ETH với credential `0x01`,
> `MAX_EFFECTIVE_BALANCE_ELECTRA` = 2048 ETH với credential compounding `0x02`).
> EIP-8148 cho phép validator compounding tự đặt mức này (sweep threshold),
> ví dụ: chỉ giữ lại 100 ETH và để phần dư được tự động rút về.

*Lưu ý*: Đặc tả này được xây dựng dựa trên [Heze](../../heze/beacon-chain.md).

## Types

### New `SweepThresholdRequests`

```python
class SweepThresholdRequests(ProgressiveList[SetSweepThresholdRequest]):
    """
    The set-sweep-threshold requests pertaining to a single execution
    payload.
    """
```

### New `SweepThresholds`

```python
class SweepThresholds(ProgressiveList[Gwei]):
    """
    Per-validator withdrawal sweep thresholds.
    """
```

## Constants

### New execution layer triggered request type

*(Loại request mới được kích hoạt từ execution layer)*

| Name                           | Value            |
| ------------------------------ | ---------------- |
| `SWEEP_THRESHOLD_REQUEST_TYPE` | `Bytes1("0x05")` |

### Sweep threshold validation

*(Các hằng số dùng để đọc sweep threshold được mã hóa trong withdrawal credentials)*

| Name                                | Value        |
| ----------------------------------- | ------------ |
| `SWEEP_THRESHOLD_CREDENTIAL_OFFSET` | `Uint64(10)` |
| `SWEEP_THRESHOLD_CREDENTIAL_LENGTH` | `Uint64(2)`  |

## Presets

### Execution

| Name                                           | Value                 | Description                                                                                       |
| ---------------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------- |
| `MAX_SET_SWEEP_THRESHOLD_REQUESTS_PER_PAYLOAD` | `Uint64(2**4)` (= 16) | *[New in EIP8148]* Số lượng tối đa request đặt sweep threshold từ execution layer trong mỗi payload |

## Containers

### Modified containers

#### `BeaconState`

```python
class BeaconState(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=47, gaps=(8, 9, 10, 28))

    genesis_time: Uint64
    genesis_validators_root: Root
    slot: Slot
    fork: Fork
    latest_block_header: BeaconBlockHeader
    block_roots: BlockRoots
    state_roots: StateRoots
    historical_roots: HistoricalRoots
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
    latest_block_hash: Hash32
    next_withdrawal_index: WithdrawalIndex
    next_withdrawal_validator_index: ValidatorIndex
    historical_summaries: HistoricalSummaries
    deposit_balance_to_consume: Gwei
    exit_balance_to_consume: Gwei
    earliest_exit_epoch: Epoch
    consolidation_balance_to_consume: Gwei
    earliest_consolidation_epoch: Epoch
    pending_deposits: PendingDeposits
    pending_partial_withdrawals: PendingPartialWithdrawals
    pending_consolidations: PendingConsolidations
    proposer_lookahead: ProposerLookahead
    builders: Builders
    next_withdrawal_builder_index: BuilderIndex
    execution_payload_availability: ExecutionPayloadAvailability
    builder_pending_payments: BuilderPendingPayments
    builder_pending_withdrawals: BuilderPendingWithdrawals
    latest_execution_payload_bid: ExecutionPayloadBid
    payload_expected_withdrawals: Withdrawals
    ptc_window: PayloadTimelinessCommitteeWindow
    # [New in EIP8148]
    validator_sweep_thresholds: SweepThresholds
```

> 💡 Ghi chú: Field mới `validator_sweep_thresholds` là một danh sách song song
> với `validators` (cùng chỉ số). Giá trị `0` nghĩa là validator dùng ngưỡng mặc
> định (max effective balance của nó).

#### `ExecutionRequests`

```python
class ExecutionRequests(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=6)

    deposits: DepositRequests
    withdrawals: WithdrawalRequests
    consolidations: ConsolidationRequests
    builder_deposits: BuilderDepositRequests
    builder_exits: BuilderExitRequests
    # [New in EIP8148]
    sweep_thresholds: SweepThresholdRequests
```

### New containers

#### `SetSweepThresholdRequest`

```python
class SetSweepThresholdRequest(Container):
    source_address: ExecutionAddress
    validator_pubkey: BLSPubkey
    threshold: Gwei
```

> 💡 Ghi chú: `source_address` là địa chỉ execution layer đã gửi request; nó phải
> trùng với địa chỉ trong withdrawal credentials của validator (xem
> `process_set_sweep_threshold_request`). `threshold` là ngưỡng mới tính bằng Gwei.

## Helper functions

### Math

#### New `bytes_to_uint16`

```python
def bytes_to_uint16(data: bytes) -> Uint16:
    """
    Return the integer deserialization of ``data`` interpreted as ``ENDIANNESS``-endian.
    """
    return Uint16(int.from_bytes(data, ENDIANNESS))
```

### Predicates

#### Modified `is_partially_withdrawable_validator`

```python
def is_partially_withdrawable_validator(
    validator: Validator, balance: Gwei, sweep_threshold: Gwei
) -> bool:
    """
    Check if ``validator`` is partially withdrawable.
    """
    # [Modified in EIP8148]
    effective_sweep_threshold = get_effective_sweep_threshold(validator, sweep_threshold)
    # [Modified in EIP8148]
    has_effective_sweep_threshold = validator.effective_balance >= effective_sweep_threshold
    # [Modified in EIP8148]
    has_excess_balance = balance > effective_sweep_threshold
    return (
        has_execution_withdrawal_credential(validator)
        # [Modified in EIP8148]
        and has_effective_sweep_threshold
        and has_excess_balance
    )
```

> 💡 Ghi chú: Validator chỉ được partial withdrawal khi có execution withdrawal
> credential, effective balance đã đạt tới ngưỡng sweep hiệu lực, và balance
> thực tế vượt quá ngưỡng đó. Phần được rút là phần balance vượt ngưỡng.

### Misc

#### New `get_initial_sweep_threshold`

Một validator có thể được tạo ra với sẵn một sweep threshold tùy chỉnh, bằng
cách mã hóa ngưỡng này vào compounding withdrawal credentials của deposit tạo ra
validator đó. `SWEEP_THRESHOLD_CREDENTIAL_LENGTH` byte bắt đầu từ vị trí
`SWEEP_THRESHOLD_CREDENTIAL_OFFSET` — vốn không được sử dụng trước bản nâng cấp
này — chứa giá trị ngưỡng, tính theo đơn vị `EFFECTIVE_BALANCE_INCREMENT` và được
mã hóa dưới dạng số nguyên little-endian:

| Bytes    | Contents                                         |
| -------- | ------------------------------------------------ |
| `0`      | `COMPOUNDING_WITHDRAWAL_PREFIX` (`0x02`)         |
| `1..9`   | Dành riêng (reserved)                            |
| `10..11` | Ngưỡng tính theo đơn vị `EFFECTIVE_BALANCE_INCREMENT` |
| `12..31` | Địa chỉ execution (execution address)            |

*Lưu ý*: Một ngưỡng nằm ngoài khoảng hợp lệ sẽ bị bỏ qua chứ không bị từ chối,
để một deposit được tạo bởi công cụ chưa biết đến bản nâng cấp này, hoặc mang một
giá trị vô nghĩa, vẫn tạo ra validator với ngưỡng mặc định. Chỉ compounding
credentials mới mang ngưỡng; với mọi prefix khác hàm này trả về 0, nghĩa là áp
dụng ngưỡng mặc định.

> 💡 Ghi chú: Ví dụ, với `EFFECTIVE_BALANCE_INCREMENT` = 1 ETH, hai byte
> `0x64 0x00` (little-endian = 100) cho ngưỡng 100 ETH. Nếu giá trị giải mã nhỏ
> hơn `MIN_ACTIVATION_BALANCE` (bao gồm cả trường hợp hai byte đều bằng 0) hoặc
> lớn hơn `MAX_EFFECTIVE_BALANCE_ELECTRA`, hàm trả về
> `MAX_EFFECTIVE_BALANCE_ELECTRA` — tức ngưỡng mặc định của validator compounding.

```python
def get_initial_sweep_threshold(withdrawal_credentials: Bytes32) -> Gwei:
    """
    Get the initial sweep threshold for a validator created with
    ``withdrawal_credentials``.
    """
    if not is_compounding_withdrawal_credential(withdrawal_credentials):
        return Gwei(0)

    start = SWEEP_THRESHOLD_CREDENTIAL_OFFSET
    end = start + SWEEP_THRESHOLD_CREDENTIAL_LENGTH
    increments = bytes_to_uint16(withdrawal_credentials[start:end])
    threshold = Gwei(increments) * EFFECTIVE_BALANCE_INCREMENT

    if threshold < MIN_ACTIVATION_BALANCE:
        return MAX_EFFECTIVE_BALANCE_ELECTRA
    if threshold > MAX_EFFECTIVE_BALANCE_ELECTRA:
        return MAX_EFFECTIVE_BALANCE_ELECTRA

    return threshold
```

#### New `get_effective_sweep_threshold`

```python
def get_effective_sweep_threshold(validator: Validator, sweep_threshold: Gwei) -> Gwei:
    """
    Get effective sweep threshold for ``validator``.
    """
    if sweep_threshold != 0:
        return sweep_threshold
    else:
        return get_max_effective_balance(validator)
```

> 💡 Ghi chú: Ngưỡng `0` được hiểu là "dùng mặc định", khi đó ngưỡng hiệu lực
> bằng `get_max_effective_balance(validator)`.

### Validator registry

#### Modified `add_validator_to_registry`

*Lưu ý*: Hàm `add_validator_to_registry` được sửa đổi để khởi tạo phần tử tương
ứng trong danh sách `validator_sweep_thresholds`.

```python
def add_validator_to_registry(
    state: BeaconState, pubkey: BLSPubkey, withdrawal_credentials: Bytes32, amount: Gwei
) -> None:
    index = get_index_for_new_validator(state)
    validator = get_validator_from_deposit(pubkey, withdrawal_credentials, amount)
    set_or_append_list(state.validators, index, validator)
    set_or_append_list(state.balances, index, amount)
    set_or_append_list(state.previous_epoch_participation, index, ParticipationFlags(0b0000_0000))
    set_or_append_list(state.current_epoch_participation, index, ParticipationFlags(0b0000_0000))
    set_or_append_list(state.inactivity_scores, index, Uint64(0))
    # [New in EIP8148]
    threshold = get_initial_sweep_threshold(withdrawal_credentials)
    set_or_append_list(state.validator_sweep_thresholds, index, threshold)
```

### Beacon state mutators

#### Modified `switch_to_compounding_validator`

```python
def switch_to_compounding_validator(state: BeaconState, index: ValidatorIndex) -> None:
    validator = state.validators[index]
    validator.withdrawal_credentials = Bytes32(
        COMPOUNDING_WITHDRAWAL_PREFIX + validator.withdrawal_credentials[1:]
    )
    queue_excess_active_balance(state, index)
    # [New in EIP8148]
    state.validator_sweep_thresholds[index] = MAX_EFFECTIVE_BALANCE_ELECTRA
```

> 💡 Ghi chú: Khi validator chuyển sang compounding credential, ngưỡng sweep của
> nó được đặt về `MAX_EFFECTIVE_BALANCE_ELECTRA` (tức mặc định của validator
> compounding).

## Beacon chain state transition function

### Epoch processing

#### Modified `process_effective_balance_updates`

*Lưu ý*: Hàm `process_effective_balance_updates` được sửa đổi để sử dụng sweep
threshold tùy chỉnh.

```python
def process_effective_balance_updates(state: BeaconState) -> None:
    # Update effective balances with hysteresis
    for index, validator in enumerate(state.validators):
        balance = state.balances[index]
        HYSTERESIS_INCREMENT = Uint64(EFFECTIVE_BALANCE_INCREMENT // HYSTERESIS_QUOTIENT)
        DOWNWARD_THRESHOLD = HYSTERESIS_INCREMENT * HYSTERESIS_DOWNWARD_MULTIPLIER
        UPWARD_THRESHOLD = HYSTERESIS_INCREMENT * HYSTERESIS_UPWARD_MULTIPLIER
        # [Modified in EIP8148]
        sweep_threshold = state.validator_sweep_thresholds[index]
        effective_sweep_threshold = get_effective_sweep_threshold(validator, sweep_threshold)

        if (
            balance + DOWNWARD_THRESHOLD < validator.effective_balance
            or validator.effective_balance + UPWARD_THRESHOLD < balance
        ):
            # [Modified in EIP8148]
            validator.effective_balance = min(
                balance - balance % EFFECTIVE_BALANCE_INCREMENT, effective_sweep_threshold
            )
```

> 💡 Ghi chú: Effective balance giờ bị giới hạn trên bởi ngưỡng sweep hiệu lực
> thay vì luôn là max effective balance. Như vậy validator đặt ngưỡng 100 ETH sẽ
> có effective balance tối đa là 100 ETH.

### Block processing

#### Execution payload

##### Modified `get_execution_requests_list`

*Lưu ý*: Hàm này mã hóa các execution request theo định nghĩa trong
[EIP-7685](https://eips.ethereum.org/EIPS/eip-7685).

```python
def get_execution_requests_list(execution_requests: ExecutionRequests) -> Sequence[bytes]:
    requests: Sequence[tuple[Bytes1, ProgressiveList]] = [
        (DEPOSIT_REQUEST_TYPE, execution_requests.deposits),
        (WITHDRAWAL_REQUEST_TYPE, execution_requests.withdrawals),
        (CONSOLIDATION_REQUEST_TYPE, execution_requests.consolidations),
        (BUILDER_DEPOSIT_REQUEST_TYPE, execution_requests.builder_deposits),
        (BUILDER_EXIT_REQUEST_TYPE, execution_requests.builder_exits),
        # [New in EIP8148]
        (SWEEP_THRESHOLD_REQUEST_TYPE, execution_requests.sweep_thresholds),
    ]

    return [
        request_type + ssz_serialize(request_data)
        for request_type, request_data in requests
        if len(request_data) != 0
    ]
```

#### Withdrawals

##### Modified `get_validators_sweep_withdrawals`

```python
def get_validators_sweep_withdrawals(
    state: BeaconState,
    withdrawal_index: WithdrawalIndex,
    prior_withdrawals: Sequence[Withdrawal],
) -> tuple[Sequence[Withdrawal], WithdrawalIndex, Uint64]:
    epoch = get_current_epoch(state)
    validators_limit = min(len(state.validators), MAX_VALIDATORS_PER_WITHDRAWALS_SWEEP)
    withdrawals_limit = MAX_WITHDRAWALS_PER_PAYLOAD
    # There must be at least one space reserved for validator sweep withdrawals
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
        # [New in EIP8148]
        sweep_threshold = state.validator_sweep_thresholds[validator_index]
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
        # [Modified in EIP8148]
        elif is_partially_withdrawable_validator(validator, balance, sweep_threshold):
            withdrawals.append(
                Withdrawal(
                    index=withdrawal_index,
                    validator_index=validator_index,
                    address=ExecutionAddress(validator.withdrawal_credentials[12:]),
                    # [Modified in EIP8148]
                    amount=balance - get_effective_sweep_threshold(validator, sweep_threshold),
                )
            )
            withdrawal_index += 1

        validator_index = (validator_index + 1) % len(state.validators)
        processed_count += 1

    return withdrawals, withdrawal_index, processed_count
```

#### Operations

##### New `process_set_sweep_threshold_request`

*Lưu ý*: Một request sẽ bị từ chối nếu ngưỡng của nó thấp hơn balance hiện tại
của validator. Điều này ngăn validator lợi dụng chu kỳ sweep để đi vòng qua hàng
đợi partial withdrawal và rút tiền ngay lập tức. Để hạ ngưỡng, validator trước
tiên phải gửi một request partial withdrawal, chờ nó được xử lý, rồi mới đặt
ngưỡng mong muốn.

> 💡 Ghi chú: Request bị bỏ qua (không có lỗi, chỉ `return`) nếu bất kỳ điều kiện
> nào sau đây xảy ra: pubkey không tồn tại; validator không có compounding
> credential; `source_address` không khớp địa chỉ trong withdrawal credentials;
> validator đã bắt đầu exit; ngưỡng mới bằng ngưỡng hiện tại; ngưỡng mới nhỏ hơn
> balance hiện tại; ngưỡng không chia hết cho `EFFECTIVE_BALANCE_INCREMENT`; hoặc
> ngưỡng nằm ngoài khoảng [`MIN_ACTIVATION_BALANCE`, `MAX_EFFECTIVE_BALANCE_ELECTRA`].

```python
def process_set_sweep_threshold_request(
    state: BeaconState, request: SetSweepThresholdRequest
) -> None:
    validator_pubkeys = [validator.pubkey for validator in state.validators]
    if request.validator_pubkey not in validator_pubkeys:
        return

    index = ValidatorIndex(validator_pubkeys.index(request.validator_pubkey))
    validator = state.validators[index]

    if not has_compounding_withdrawal_credential(validator):
        return
    if validator.withdrawal_credentials[12:] != request.source_address:
        return
    if validator.exit_epoch != FAR_FUTURE_EPOCH:
        return
    if state.validator_sweep_thresholds[index] == request.threshold:
        return
    if request.threshold < state.balances[index]:
        return
    if request.threshold % EFFECTIVE_BALANCE_INCREMENT != 0:
        return
    if request.threshold < MIN_ACTIVATION_BALANCE:
        return
    if request.threshold > MAX_EFFECTIVE_BALANCE_ELECTRA:
        return

    state.validator_sweep_thresholds[index] = request.threshold
```

#### Parent execution payload

##### Modified `apply_parent_execution_payload`

*Lưu ý*: Hàm này đưa khoản thanh toán cho builder vào hàng đợi, xử lý các
execution request của payload cha (parent), cập nhật trạng thái payload
availability, và cập nhật latest block hash. Nó được gọi bởi
`process_parent_execution_payload` trong quá trình xử lý block, và bởi validator
trong quá trình tạo block, trước khi tính toán các withdrawal.

```python
def apply_parent_execution_payload(
    state: BeaconState,
    requests: ExecutionRequests,
) -> None:
    parent_bid = state.latest_execution_payload_bid
    parent_slot = state.latest_block_header.slot
    parent_epoch = compute_epoch_at_slot(parent_slot)

    assert len(requests.withdrawals) <= MAX_WITHDRAWAL_REQUESTS_PER_PAYLOAD
    assert len(requests.consolidations) <= MAX_CONSOLIDATION_REQUESTS_PER_PAYLOAD
    assert len(requests.builder_deposits) <= MAX_BUILDER_DEPOSIT_REQUESTS_PER_PAYLOAD
    assert len(requests.builder_exits) <= MAX_BUILDER_EXIT_REQUESTS_PER_PAYLOAD
    # [New in EIP8148]
    assert len(requests.sweep_thresholds) <= MAX_SET_SWEEP_THRESHOLD_REQUESTS_PER_PAYLOAD

    # Settle the builder payment before the requests so that a builder exit
    # request is rejected while the payment is pending
    if parent_epoch == get_current_epoch(state):
        payment_index = SLOTS_PER_EPOCH + parent_slot % SLOTS_PER_EPOCH
        settle_builder_payment(state, payment_index)
    elif parent_epoch == get_previous_epoch(state):
        payment_index = parent_slot % SLOTS_PER_EPOCH
        settle_builder_payment(state, payment_index)
    elif parent_bid.value > 0:
        # Parent is older than the previous epoch, its payment entry has been
        # evicted from builder_pending_payments. Append the withdrawal directly.
        state.builder_pending_withdrawals.append(
            BuilderPendingWithdrawal(
                fee_recipient=parent_bid.fee_recipient,
                amount=parent_bid.value,
                builder_index=parent_bid.builder_index,
            )
        )

    # Process execution requests from parent's payload. The execution
    # requests are processed at state.slot (child's slot), not the parent's slot.
    def for_ops(operations: Sequence[Any], fn: Callable[[BeaconState, Any], None]) -> None:
        for operation in operations:
            fn(state, operation)

    for_ops(requests.deposits, process_deposit_request)
    for_ops(requests.withdrawals, process_withdrawal_request)
    for_ops(requests.consolidations, process_consolidation_request)
    for_ops(requests.builder_deposits, process_builder_deposit_request)
    for_ops(requests.builder_exits, process_builder_exit_request)
    # [New in EIP8148]
    for_ops(requests.sweep_thresholds, process_set_sweep_threshold_request)

    # Update parent payload availability and latest block hash
    state.execution_payload_availability[parent_slot % SLOTS_PER_HISTORICAL_ROOT] = Boolean(True)
    state.latest_block_hash = parent_bid.block_hash
```
