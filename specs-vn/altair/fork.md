# Altair -- Fork Logic

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Configs](#configs)
- [Fork to Altair](#fork-to-altair)
  - [Fork trigger](#fork-trigger)
  - [Upgrading the state](#upgrading-the-state)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả quy trình nâng cấp đầu tiên của beacon chain: bản nâng cấp
Altair, bổ sung hỗ trợ light client cùng nhiều cải tiến khác.

## Configs

| Name                  | Value                                         |
| --------------------- | --------------------------------------------- |
| `ALTAIR_FORK_VERSION` | `Version("0x01000000")`                       |
| `ALTAIR_FORK_EPOCH`   | `Epoch(74240)` (Oct 27, 2021, 10:56:23am UTC) |

## Fork to Altair

### Fork trigger

Fork được kích hoạt tại epoch `ALTAIR_FORK_EPOCH`.

*Lưu ý*: Với các mạng chạy Altair ngay từ đầu (pure Altair network), hàm
`upgrade_to_altair` được áp dụng lên genesis state để chuyển nó sang fork này.

### Upgrading the state

Nếu `state.slot % SLOTS_PER_EPOCH == 0` và
`compute_epoch_at_slot(state.slot) == ALTAIR_FORK_EPOCH`, một thay đổi state bất
thường (irregular state change — không thuộc state transition thông thường) được
thực hiện để nâng cấp lên Altair.

Việc nâng cấp diễn ra sau khi vòng lặp bên trong của `process_slots` hoàn tất và
đã đặt `state.slot` bằng `ALTAIR_FORK_EPOCH * SLOTS_PER_EPOCH`. Cần cẩn thận khi
chuyển qua ranh giới fork, vì các implementation sẽ cần một
[state transition function](../phase0/beacon-chain.md#beacon-chain-state-transition-function)
đã được sửa đổi, khác với tài liệu Phase 0. Cụ thể, hàm `state_transition` bên
ngoài được định nghĩa trong tài liệu Phase 0 sẽ không cho biết chính xác slot
fork để thực hiện nâng cấp nếu có các slot bị bỏ qua (skipped slot, không có
block) tại ranh giới fork. Vì vậy, logic nâng cấp phải nằm bên trong
`process_slots`.

> 💡 Ghi chú: Hàm `translate_participation` chuyển các `PendingAttestation` của
> epoch trước (cách ghi nhận của phase 0) sang dạng participation flag mới của
> Altair, để việc tính reward/penalty cho epoch trước ranh giới fork vẫn chính
> xác. Hàm `upgrade_to_altair` tạo `BeaconState` mới: giữ nguyên phần lớn các
> trường, thay `fork.current_version`, khởi tạo participation flag và
> `inactivity_scores` bằng 0, rồi tính sync committee. Tại ranh giới fork,
> current sync committee và next sync committee được gán cùng một committee.

```python
def translate_participation(
    state: BeaconState, pending_attestations: Sequence[phase0.PendingAttestation]
) -> None:
    for attestation in pending_attestations:
        data = attestation.data
        inclusion_delay = attestation.inclusion_delay
        # Translate attestation inclusion info to flag indices
        participation_flag_indices = get_attestation_participation_flag_indices(
            state, data, inclusion_delay
        )

        # Apply flags to all attesting validators
        epoch_participation = state.previous_epoch_participation
        committee = get_beacon_committee(state, data.slot, data.index)
        attesting_indices = {
            validator_index
            for index, validator_index in enumerate(committee)
            if attestation.aggregation_bits[index]
        }
        for index in attesting_indices:
            for flag_index in participation_flag_indices:
                epoch_participation[index] = add_flag(epoch_participation[index], flag_index)


def upgrade_to_altair(pre: phase0.BeaconState) -> BeaconState:
    epoch = phase0.get_current_epoch(pre)
    post = BeaconState(
        genesis_time=pre.genesis_time,
        genesis_validators_root=pre.genesis_validators_root,
        slot=pre.slot,
        fork=Fork(
            previous_version=pre.fork.current_version,
            # [New in Altair]
            current_version=ALTAIR_FORK_VERSION,
            epoch=epoch,
        ),
        latest_block_header=pre.latest_block_header,
        block_roots=pre.block_roots,
        state_roots=pre.state_roots,
        historical_roots=pre.historical_roots,
        # [New in Altair]
        current_sync_committee=SyncCommittee.empty(),
        # [New in Altair]
        next_sync_committee=SyncCommittee.empty(),
        eth1_data=pre.eth1_data,
        eth1_data_votes=pre.eth1_data_votes,
        eth1_deposit_index=pre.eth1_deposit_index,
        validators=pre.validators,
        balances=pre.balances,
        randao_mixes=pre.randao_mixes,
        slashings=pre.slashings,
        previous_epoch_participation=EpochParticipation(
            data=[ParticipationFlags(0b0000_0000) for _ in range(len(pre.validators))]
        ),
        current_epoch_participation=EpochParticipation(
            data=[ParticipationFlags(0b0000_0000) for _ in range(len(pre.validators))]
        ),
        justification_bits=pre.justification_bits,
        previous_justified_checkpoint=pre.previous_justified_checkpoint,
        current_justified_checkpoint=pre.current_justified_checkpoint,
        finalized_checkpoint=pre.finalized_checkpoint,
        inactivity_scores=InactivityScores(data=[Uint64(0) for _ in range(len(pre.validators))]),
    )
    # Fill in previous epoch participation from the pre state's pending attestations
    translate_participation(post, pre.previous_epoch_attestations)

    # Fill in sync committees
    # Note: A duplicate committee is assigned for the current and next committee at the fork boundary
    post.current_sync_committee = get_next_sync_committee(post)
    post.next_sync_committee = get_next_sync_committee(post)
    return post
```
