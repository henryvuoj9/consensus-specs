# EIP-7716 -- Fork Logic

*Note*: Tài liệu này đang trong quá trình soạn thảo (work-in-progress), dành cho
các nhà nghiên cứu và người triển khai (implementer).

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Configs](#configs)
- [Helper functions](#helper-functions)
  - [New `get_fork_initial_smoothed_offline_balance`](#new-get_fork_initial_smoothed_offline_balance)
- [Fork to EIP-7716](#fork-to-eip-7716)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả quy trình nâng cấp (upgrade) lên EIP-7716.

## Configs

Cảnh báo: config này chưa phải là bản cuối cùng.

| Name                   | Value                                 |
| ---------------------- | ------------------------------------- |
| `EIP7716_FORK_VERSION` | `Version("0x77160000")`               |
| `EIP7716_FORK_EPOCH`   | `Epoch(18446744073709551615)` **TBD** |

## Helper functions

### New `get_fork_initial_smoothed_offline_balance`

Giá trị trung bình động được khởi tạo bằng offline balance trung bình mỗi slot
quan sát được trong epoch ngay trước fork, để tránh xuất hiện penalty factor sai
lệch (không phản ánh thực tế) ngay tại thời điểm kích hoạt fork.

> 💡 Ghi chú: Nếu khởi tạo bằng `0`, mọi offline balance ở epoch đầu tiên sau
> fork đều sẽ bị coi là "vượt mức" và validator offline sẽ bị phạt nặng một cách
> không công bằng.

```python
def get_fork_initial_smoothed_offline_balance(state: BeaconState) -> Gwei:
    total = Gwei(0)
    start_slot = compute_start_slot_at_epoch(get_previous_epoch(state))
    for slot_offset in range(SLOTS_PER_EPOCH):
        slot = start_slot + slot_offset
        total += get_slot_offline_balance(state, slot)
    return total // Uint64(SLOTS_PER_EPOCH)
```

## Fork to EIP-7716

Nếu `state.slot % SLOTS_PER_EPOCH == 0` và
`compute_epoch_at_slot(state.slot) == EIP7716_FORK_EPOCH`, một thay đổi state
bất thường (irregular state change) sẽ được thực hiện để nâng cấp lên EIP-7716.

Việc nâng cấp diễn ra sau khi vòng lặp bên trong của `process_slots` hoàn tất,
tức là vòng lặp đặt `state.slot` bằng `EIP7716_FORK_EPOCH * SLOTS_PER_EPOCH`.

```python
def upgrade_to_eip7716(pre: heze.BeaconState) -> BeaconState:
    epoch = heze.get_current_epoch(pre)

    post = BeaconState(
        genesis_time=pre.genesis_time,
        genesis_validators_root=pre.genesis_validators_root,
        slot=pre.slot,
        fork=Fork(
            previous_version=pre.fork.current_version,
            # [New in EIP7716]
            current_version=EIP7716_FORK_VERSION,
            epoch=epoch,
        ),
        latest_block_header=pre.latest_block_header,
        block_roots=pre.block_roots,
        state_roots=pre.state_roots,
        historical_roots=pre.historical_roots,
        validators=pre.validators,
        balances=pre.balances,
        randao_mixes=pre.randao_mixes,
        slashings=pre.slashings,
        previous_epoch_participation=pre.previous_epoch_participation,
        current_epoch_participation=pre.current_epoch_participation,
        justification_bits=pre.justification_bits,
        previous_justified_checkpoint=pre.previous_justified_checkpoint,
        current_justified_checkpoint=pre.current_justified_checkpoint,
        finalized_checkpoint=pre.finalized_checkpoint,
        inactivity_scores=pre.inactivity_scores,
        current_sync_committee=pre.current_sync_committee,
        next_sync_committee=pre.next_sync_committee,
        latest_block_hash=pre.latest_block_hash,
        next_withdrawal_index=pre.next_withdrawal_index,
        next_withdrawal_validator_index=pre.next_withdrawal_validator_index,
        historical_summaries=pre.historical_summaries,
        deposit_balance_to_consume=pre.deposit_balance_to_consume,
        exit_balance_to_consume=pre.exit_balance_to_consume,
        earliest_exit_epoch=pre.earliest_exit_epoch,
        consolidation_balance_to_consume=pre.consolidation_balance_to_consume,
        earliest_consolidation_epoch=pre.earliest_consolidation_epoch,
        pending_deposits=pre.pending_deposits,
        pending_partial_withdrawals=pre.pending_partial_withdrawals,
        pending_consolidations=pre.pending_consolidations,
        proposer_lookahead=pre.proposer_lookahead,
        builders=pre.builders,
        next_withdrawal_builder_index=pre.next_withdrawal_builder_index,
        execution_payload_availability=pre.execution_payload_availability,
        builder_pending_payments=pre.builder_pending_payments,
        builder_pending_withdrawals=pre.builder_pending_withdrawals,
        latest_execution_payload_bid=pre.latest_execution_payload_bid,
        payload_expected_withdrawals=pre.payload_expected_withdrawals,
        ptc_window=pre.ptc_window,
        # [New in EIP7716]
        smoothed_offline_balance=Gwei(0),
    )

    # [New in EIP7716]
    post.smoothed_offline_balance = get_fork_initial_smoothed_offline_balance(post)

    return post
```
