# Electra -- Fork Logic

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Configs](#configs)
- [Fork to Electra](#fork-to-electra)
  - [Fork trigger](#fork-trigger)
  - [Upgrading the state](#upgrading-the-state)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả quy trình nâng cấp (upgrade) lên Electra: khi nào fork được kích hoạt và beacon state được chuyển đổi từ định dạng Deneb sang định dạng Electra như thế nào.

## Configs

Cảnh báo: cấu hình này chưa phải là bản cuối cùng.

| Name                   | Value                                         |
| ---------------------- | --------------------------------------------- |
| `ELECTRA_FORK_VERSION` | `Version("0x05000000")`                       |
| `ELECTRA_FORK_EPOCH`   | `Epoch(364032)` (May 7, 2025, 10:05:11am UTC) |

## Fork to Electra

### Fork trigger

Fork được kích hoạt tại epoch `ELECTRA_FORK_EPOCH`.

*Lưu ý*: Với các mạng chạy Electra "thuần" (tức là mạng khởi tạo trực tiếp ở Electra ngay từ genesis), hàm `upgrade_to_electra` được áp dụng để chuyển genesis state sang fork này.

### Upgrading the state

Nếu `state.slot % SLOTS_PER_EPOCH == 0` và
`compute_epoch_at_slot(state.slot) == ELECTRA_FORK_EPOCH`, một thay đổi state bất thường (irregular state change — tức là không theo quy trình chuyển trạng thái thông thường) sẽ được thực hiện để nâng cấp lên Electra.

> 💡 Ghi chú: Nói cách khác, việc nâng cấp diễn ra đúng tại slot đầu tiên của epoch `ELECTRA_FORK_EPOCH`. Hàm `upgrade_to_electra` dưới đây làm các việc chính sau:
>
> - Sao chép toàn bộ các trường của beacon state Deneb sang `BeaconState` mới, cập nhật `fork.current_version` thành `ELECTRA_FORK_VERSION`.
> - Khởi tạo các trường mới của Electra: `deposit_requests_start_index` (EIP-6110, deposit được đưa vào từ execution layer), và các trường liên quan đến churn (giới hạn tốc độ vào/ra), consolidation và hàng đợi pending deposit / pending partial withdrawal / pending consolidation (EIP-7251).
> - Tính `earliest_exit_epoch` bằng cách lấy giá trị lớn nhất giữa `compute_activation_exit_epoch(epoch)` và mọi `exit_epoch` đã được lên lịch của các validator, rồi cộng thêm 1.
> - Với các validator chưa được kích hoạt (`activation_epoch == FAR_FUTURE_EPOCH`): đặt balance và effective balance về 0, rồi chuyển toàn bộ số dư đó vào hàng đợi `pending_deposits` (sắp xếp theo `activation_eligibility_epoch`, rồi theo index). Như vậy các validator này sẽ được xử lý lại theo cơ chế deposit mới của Electra.
> - Với các validator đã dùng compounding withdrawal credential từ trước, phần balance vượt quá mức tối thiểu được đưa vào hàng đợi để đi qua activation churn.

```python
def upgrade_to_electra(pre: deneb.BeaconState) -> BeaconState:
    epoch = deneb.get_current_epoch(pre)

    earliest_exit_epoch = compute_activation_exit_epoch(epoch)
    for validator in pre.validators:
        if validator.exit_epoch != FAR_FUTURE_EPOCH:
            earliest_exit_epoch = max(earliest_exit_epoch, validator.exit_epoch)
    earliest_exit_epoch += 1

    post = BeaconState(
        genesis_time=pre.genesis_time,
        genesis_validators_root=pre.genesis_validators_root,
        slot=pre.slot,
        fork=Fork(
            previous_version=pre.fork.current_version,
            # [Modified in Electra]
            current_version=ELECTRA_FORK_VERSION,
            epoch=epoch,
        ),
        latest_block_header=pre.latest_block_header,
        block_roots=pre.block_roots,
        state_roots=pre.state_roots,
        historical_roots=pre.historical_roots,
        eth1_data=pre.eth1_data,
        eth1_data_votes=pre.eth1_data_votes,
        eth1_deposit_index=pre.eth1_deposit_index,
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
        latest_execution_payload_header=pre.latest_execution_payload_header,
        next_withdrawal_index=pre.next_withdrawal_index,
        next_withdrawal_validator_index=pre.next_withdrawal_validator_index,
        historical_summaries=pre.historical_summaries,
        # [New in Electra:EIP6110]
        deposit_requests_start_index=UNSET_DEPOSIT_REQUESTS_START_INDEX,
        # [New in Electra:EIP7251]
        deposit_balance_to_consume=Gwei(0),
        # [New in Electra:EIP7251]
        exit_balance_to_consume=Gwei(0),
        # [New in Electra:EIP7251]
        earliest_exit_epoch=earliest_exit_epoch,
        # [New in Electra:EIP7251]
        consolidation_balance_to_consume=Gwei(0),
        # [New in Electra:EIP7251]
        earliest_consolidation_epoch=compute_activation_exit_epoch(epoch),
        # [New in Electra:EIP7251]
        pending_deposits=PendingDeposits(),
        # [New in Electra:EIP7251]
        pending_partial_withdrawals=PendingPartialWithdrawals(),
        # [New in Electra:EIP7251]
        pending_consolidations=PendingConsolidations(),
    )

    post.exit_balance_to_consume = get_activation_exit_churn_limit(post)
    post.consolidation_balance_to_consume = get_consolidation_churn_limit(post)

    # [New in Electra:EIP7251]
    # thêm các validator chưa được kích hoạt vào hàng đợi pending balance deposit
    pre_activation = sorted(
        [
            index
            for index, validator in enumerate(post.validators)
            if validator.activation_epoch == FAR_FUTURE_EPOCH
        ],
        key=lambda index: (post.validators[index].activation_eligibility_epoch, index),
    )

    for index in pre_activation:
        balance = post.balances[index]
        post.balances[index] = Gwei(0)
        validator = post.validators[index]
        validator.effective_balance = Gwei(0)
        validator.activation_eligibility_epoch = FAR_FUTURE_EPOCH
        # Dùng G2_POINT_AT_INFINITY làm giá trị giữ chỗ cho trường signature
        # và GENESIS_SLOT để phân biệt với một pending deposit đến từ deposit request
        post.pending_deposits.append(
            PendingDeposit(
                pubkey=validator.pubkey,
                withdrawal_credentials=validator.withdrawal_credentials,
                amount=balance,
                signature=G2_POINT_AT_INFINITY,
                slot=GENESIS_SLOT,
            )
        )

    # Đảm bảo các validator đã sớm dùng compounding credential vẫn phải đi qua activation churn
    for index, validator in enumerate(post.validators):
        if has_compounding_withdrawal_credential(validator):
            queue_excess_active_balance(post, ValidatorIndex(index))

    return post
```
