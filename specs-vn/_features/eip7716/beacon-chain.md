# EIP-7716 -- The Beacon Chain

*Note*: Tài liệu này đang trong quá trình soạn thảo (work-in-progress), dành cho
các nhà nghiên cứu và người triển khai (implementer).

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Presets](#presets)
  - [Penalty factor](#penalty-factor)
- [Containers](#containers)
  - [Modified containers](#modified-containers)
    - [`BeaconState`](#beaconstate)
- [Helper functions](#helper-functions)
  - [Predicates](#predicates)
    - [New `is_offline_in_previous_epoch`](#new-is_offline_in_previous_epoch)
  - [Beacon state accessors](#beacon-state-accessors)
    - [New `get_slot_offline_balance`](#new-get_slot_offline_balance)
    - [New `get_slot_reference_balance`](#new-get_slot_reference_balance)
    - [New `get_updated_smoothed_offline_balance`](#new-get_updated_smoothed_offline_balance)
    - [New `get_slot_penalty_factors`](#new-get_slot_penalty_factors)
    - [New `get_validator_slot_offsets`](#new-get_validator_slot_offsets)
- [Beacon chain state transition function](#beacon-chain-state-transition-function)
  - [Epoch processing](#epoch-processing)
    - [Modified `process_epoch`](#modified-process_epoch)
    - [Rewards and penalties](#rewards-and-penalties)
      - [Modified `get_flag_index_deltas`](#modified-get_flag_index_deltas)
    - [New `process_smoothed_offline_balance`](#new-process_smoothed_offline_balance)

<!-- mdformat-toc end -->

## Introduction

Feature này đưa vào cơ chế phạt attestation chống tương quan (anti-correlation
attestation penalties) cho các validator. Penalty cho timely target của một
validator hoàn toàn không tạo ra attestation đúng hạn nào — tức là thiếu cả hai
flag timely source và timely target, dấu hiệu của sự cố hạ tầng (máy chết, mất
mạng...) chứ không phải do bất đồng quan điểm về chain — sẽ được nhân với một
`penalty_factor` tính riêng cho từng slot. Hệ số này tỉ lệ với phần offline
balance của slot đó vượt quá trung bình động hàm mũ (exponential moving average)
của offline balance, và bằng `1` khi offline balance không vượt quá trung bình
động, nhờ vậy các sự cố không tương quan với nhau chỉ phải chịu đúng mức penalty
như trước fork. `PENALTY_SLOPE` được đặt bằng `3 * (MAX_PENALTY_FACTOR - 1)` để
hệ số đạt mức trần khi một phần ba lượng stake vừa mới chuyển sang offline — đây
cũng là ngưỡng mà inactivity leak bắt đầu đảm nhận vai trò cơ chế "định giá" sự
tương quan của giao thức.

> 💡 Ghi chú: Ý tưởng chính là phạt nặng hơn khi nhiều validator cùng offline
> trong cùng một slot (ví dụ cùng dùng một nhà cung cấp cloud bị sập), nhằm
> khuyến khích đa dạng hoá hạ tầng. Một validator offline lẻ tẻ vẫn chỉ bị phạt
> như cũ.

*Note*: Spec này được xây dựng dựa trên [Heze](../../heze/beacon-chain.md).

## Presets

### Penalty factor

| Name                               | Value                                  | Description                                                    |
| ---------------------------------- | -------------------------------------- | -------------------------------------------------------------- |
| `MAX_PENALTY_FACTOR`               | `Uint64(2**8)` (= 256)                 | Penalty factor tối đa, là tham số duy nhất quyết định mức phạt |
| `PENALTY_SLOPE`                    | `Uint64(3 * (MAX_PENALTY_FACTOR - 1))` | Độ dốc của penalty factor theo phần offline balance vượt mức   |
| `OFFLINE_BALANCE_SMOOTHING_FACTOR` | `Uint64(2**16)` (= 65,536)             | Số chia làm mượt của trung bình động offline balance           |

## Containers

### Modified containers

#### `BeaconState`

*Note*: Container `BeaconState` được sửa đổi để theo dõi thêm
`smoothed_offline_balance`, là trung bình động hàm mũ của offline balance theo
từng slot.

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
    # [New in EIP7716]
    smoothed_offline_balance: Gwei
```

## Helper functions

### Predicates

#### New `is_offline_in_previous_epoch`

```python
def is_offline_in_previous_epoch(state: BeaconState, index: ValidatorIndex) -> bool:
    """
    Check if ``index`` produced no timely attestation at all in the previous epoch.
    Validators that attested with a correct and timely source but an incorrect
    target demonstrated liveness and are not considered offline.
    """
    return (
        not state.validators[index].slashed
        and not has_flag(state.previous_epoch_participation[index], TIMELY_SOURCE_FLAG_INDEX)
        and not has_flag(state.previous_epoch_participation[index], TIMELY_TARGET_FLAG_INDEX)
    )
```

### Beacon state accessors

#### New `get_slot_offline_balance`

```python
def get_slot_offline_balance(state: BeaconState, slot: Slot) -> Gwei:
    """
    Return the sum of effective balances of offline validators whose committees
    were assigned to ``slot``. ``slot`` must be within the previous epoch.
    """
    epoch = compute_epoch_at_slot(slot)
    offline_balance = Gwei(0)
    for committee_index in range(get_committee_count_per_slot(state, epoch)):
        committee = get_beacon_committee(state, slot, CommitteeIndex(committee_index))
        for index in committee:
            if is_offline_in_previous_epoch(state, index):
                offline_balance += state.validators[index].effective_balance
    return offline_balance
```

#### New `get_slot_reference_balance`

```python
def get_slot_reference_balance(state: BeaconState) -> Gwei:
    """
    Return the average active balance per slot, the normalizer of the penalty factor.
    """
    return get_total_active_balance(state) // Uint64(SLOTS_PER_EPOCH)
```

#### New `get_updated_smoothed_offline_balance`

```python
def get_updated_smoothed_offline_balance(smoothed_balance: Gwei, offline_balance: Gwei) -> Gwei:
    """
    Return the exponential moving average updated with one slot's offline balance.
    """
    if offline_balance > smoothed_balance:
        delta = offline_balance - smoothed_balance
        smoothed_delta = delta // OFFLINE_BALANCE_SMOOTHING_FACTOR
        return smoothed_balance + smoothed_delta
    else:
        delta = smoothed_balance - offline_balance
        smoothed_delta = delta // OFFLINE_BALANCE_SMOOTHING_FACTOR
        return smoothed_balance - smoothed_delta
```

#### New `get_slot_penalty_factors`

```python
def get_slot_penalty_factors(state: BeaconState) -> Sequence[Uint64]:
    """
    Return the penalty factor for each slot of the previous epoch.
    Does not mutate ``state``; the moving average is persisted by
    ``process_smoothed_offline_balance``.
    """
    factors = []
    smoothed_balance = state.smoothed_offline_balance
    reference_balance = get_slot_reference_balance(state)
    start_slot = compute_start_slot_at_epoch(get_previous_epoch(state))
    for slot_offset in range(SLOTS_PER_EPOCH):
        slot = start_slot + slot_offset
        offline_balance = get_slot_offline_balance(state, slot)
        excess = offline_balance - min(offline_balance, smoothed_balance)
        excess_factor = PENALTY_SLOPE * excess // reference_balance
        penalty_factor = min(Uint64(1) + excess_factor, MAX_PENALTY_FACTOR)
        factors.append(penalty_factor)
        smoothed_balance = get_updated_smoothed_offline_balance(smoothed_balance, offline_balance)
    return factors
```

#### New `get_validator_slot_offsets`

```python
def get_validator_slot_offsets(state: BeaconState) -> Sequence[Uint64]:
    """
    Return the slot offset within the previous epoch of each validator's
    committee assignment.
    """
    slot_offsets = [Uint64(0)] * len(state.validators)
    previous_epoch = get_previous_epoch(state)
    start_slot = compute_start_slot_at_epoch(previous_epoch)
    for slot_offset in range(SLOTS_PER_EPOCH):
        slot = start_slot + slot_offset
        for committee_index in range(get_committee_count_per_slot(state, previous_epoch)):
            committee = get_beacon_committee(state, slot, CommitteeIndex(committee_index))
            for index in committee:
                slot_offsets[index] = Uint64(slot_offset)
    return slot_offsets
```

## Beacon chain state transition function

### Epoch processing

#### Modified `process_epoch`

*Note*: Hàm `process_epoch` được sửa đổi để gọi helper mới
`process_smoothed_offline_balance` sau `process_rewards_and_penalties`, nhờ đó
các penalty factor áp dụng cho epoch trước được tính dựa trên giá trị trung bình
động tại thời điểm bắt đầu epoch đó (chưa bị cập nhật bởi chính dữ liệu của
epoch này).

```python
def process_epoch(state: BeaconState) -> None:
    process_justification_and_finalization(state)
    process_inactivity_updates(state)
    process_rewards_and_penalties(state)
    # [New in EIP7716]
    process_smoothed_offline_balance(state)
    process_registry_updates(state)
    process_slashings(state)
    process_pending_deposits(state)
    process_pending_consolidations(state)
    process_builder_pending_payments(state)
    process_effective_balance_updates(state)
    process_slashings_reset(state)
    process_randao_mixes_reset(state)
    process_historical_summaries_update(state)
    process_participation_flag_updates(state)
    process_sync_committee_updates(state)
    process_proposer_lookahead(state)
    process_ptc_window(state)
```

#### Rewards and penalties

##### Modified `get_flag_index_deltas`

*Note*: Hàm `get_flag_index_deltas` được sửa đổi để nhân penalty timely target
của các validator offline với penalty factor của slot mà committee của họ được
phân công. Penalty timely source không thay đổi, việc bỏ lỡ timely head vẫn
không bị phạt, và những validator bỏ lỡ target nhưng vẫn attest với timely
source thì chỉ chịu penalty bình thường (không bị nhân hệ số).

```python
def get_flag_index_deltas(
    state: BeaconState, flag_index: int
) -> tuple[Sequence[Gwei], Sequence[Gwei]]:
    """
    Return the deltas for a given ``flag_index`` by scanning through the participation flags.
    """
    rewards = [Gwei(0)] * len(state.validators)
    penalties = [Gwei(0)] * len(state.validators)
    previous_epoch = get_previous_epoch(state)
    unslashed_participating_indices = get_unslashed_participating_indices(
        state, flag_index, previous_epoch
    )
    weight = PARTICIPATION_FLAG_WEIGHTS[flag_index]
    unslashed_participating_balance = get_total_balance(state, unslashed_participating_indices)
    unslashed_participating_increments = (
        unslashed_participating_balance // EFFECTIVE_BALANCE_INCREMENT
    )
    active_increments = get_total_active_balance(state) // EFFECTIVE_BALANCE_INCREMENT

    # [New in EIP7716]
    if flag_index == TIMELY_TARGET_FLAG_INDEX:
        penalty_factors = get_slot_penalty_factors(state)
        slot_offsets = get_validator_slot_offsets(state)

    for index in get_eligible_validator_indices(state):
        base_reward = get_base_reward(state, index)
        if index in unslashed_participating_indices:
            if not is_in_inactivity_leak(state):
                reward_numerator = base_reward * weight * unslashed_participating_increments
                rewards[index] += reward_numerator // (active_increments * WEIGHT_DENOMINATOR)
        # [New in EIP7716]
        elif flag_index == TIMELY_TARGET_FLAG_INDEX:
            penalty_factor = Uint64(1)
            if is_offline_in_previous_epoch(state, index):
                penalty_factor = penalty_factors[slot_offsets[index]]
            penalties[index] += penalty_factor * base_reward * weight // WEIGHT_DENOMINATOR
        elif flag_index != TIMELY_HEAD_FLAG_INDEX:
            penalties[index] += base_reward * weight // WEIGHT_DENOMINATOR
    return rewards, penalties
```

#### New `process_smoothed_offline_balance`

```python
def process_smoothed_offline_balance(state: BeaconState) -> None:
    start_slot = compute_start_slot_at_epoch(get_previous_epoch(state))
    for slot_offset in range(SLOTS_PER_EPOCH):
        slot = start_slot + slot_offset
        state.smoothed_offline_balance = get_updated_smoothed_offline_balance(
            state.smoothed_offline_balance, get_slot_offline_balance(state, slot)
        )
```
