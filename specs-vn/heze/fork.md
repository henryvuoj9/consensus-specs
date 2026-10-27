# Heze -- Fork Logic

*Lưu ý*: Tài liệu này vẫn đang trong quá trình hoàn thiện, dành cho các nhà nghiên cứu và người triển khai client.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Configs](#configs)
- [Fork to Heze](#fork-to-heze)
  - [Fork trigger](#fork-trigger)
  - [Upgrading the state](#upgrading-the-state)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả quy trình nâng cấp lên Heze.

## Configs

Cảnh báo: cấu hình này chưa phải là bản cuối cùng.

| Name                | Value                                 |
| ------------------- | ------------------------------------- |
| `HEZE_FORK_VERSION` | `Version("0x08000000")`               |
| `HEZE_FORK_EPOCH`   | `Epoch(18446744073709551615)` **TBD** |

## Fork to Heze

### Fork trigger

Fork được kích hoạt tại epoch `HEZE_FORK_EPOCH`.

### Upgrading the state

Nếu `state.slot % SLOTS_PER_EPOCH == 0` và
`compute_epoch_at_slot(state.slot) == HEZE_FORK_EPOCH`, một thay đổi state bất
thường (irregular state change) sẽ được thực hiện để nâng cấp lên Heze.

> 💡 Ghi chú: Nói cách khác, tại slot đầu tiên của epoch `HEZE_FORK_EPOCH`,
> beacon state kiểu Gloas được chuyển đổi sang kiểu Heze bằng hàm
> `upgrade_to_heze` dưới đây: các trường liên quan đến eth1/deposit cũ bị loại
> bỏ, và `latest_execution_payload_bid` được bổ sung trường
> `inclusion_list_bits` (khởi tạo bằng toàn bit 0).

```python
def upgrade_to_heze(pre: gloas.BeaconState) -> BeaconState:
    # [New in Heze:EIP8015]
    # Kiểm tra rằng cơ chế deposit cũ đã bị vô hiệu hóa
    assert pre.eth1_deposit_index == pre.deposit_requests_start_index

    epoch = gloas.get_current_epoch(pre)
    latest_execution_payload_bid = ExecutionPayloadBid(
        parent_block_hash=pre.latest_execution_payload_bid.parent_block_hash,
        parent_block_root=pre.latest_execution_payload_bid.parent_block_root,
        block_hash=pre.latest_execution_payload_bid.block_hash,
        prev_randao=pre.latest_execution_payload_bid.prev_randao,
        fee_recipient=pre.latest_execution_payload_bid.fee_recipient,
        gas_limit=pre.latest_execution_payload_bid.gas_limit,
        builder_index=pre.latest_execution_payload_bid.builder_index,
        slot=pre.latest_execution_payload_bid.slot,
        value=pre.latest_execution_payload_bid.value,
        execution_payment=pre.latest_execution_payload_bid.execution_payment,
        blob_kzg_commitments=pre.latest_execution_payload_bid.blob_kzg_commitments,
        execution_requests_root=pre.latest_execution_payload_bid.execution_requests_root,
        # [New in Heze:EIP7805]
        inclusion_list_bits=InclusionListBits(),
    )

    post = BeaconState(
        genesis_time=pre.genesis_time,
        genesis_validators_root=pre.genesis_validators_root,
        slot=pre.slot,
        fork=Fork(
            previous_version=pre.fork.current_version,
            # [Modified in Heze]
            current_version=HEZE_FORK_VERSION,
            epoch=epoch,
        ),
        latest_block_header=pre.latest_block_header,
        block_roots=pre.block_roots,
        state_roots=pre.state_roots,
        historical_roots=pre.historical_roots,
        # [Modified in Heze:EIP8015]
        # Đã loại bỏ `eth1_data`
        # [Modified in Heze:EIP8015]
        # Đã loại bỏ `eth1_data_votes`
        # [Modified in Heze:EIP8015]
        # Đã loại bỏ `eth1_deposit_index`
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
        # [Modified in Heze:EIP8015]
        # Đã loại bỏ `deposit_requests_start_index`
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
        # [Modified in Heze:EIP7805]
        latest_execution_payload_bid=latest_execution_payload_bid,
        payload_expected_withdrawals=pre.payload_expected_withdrawals,
        ptc_window=pre.ptc_window,
    )

    return post
```

> 💡 Ghi chú: Điều kiện `pre.eth1_deposit_index == pre.deposit_requests_start_index`
> bảo đảm rằng tất cả deposit theo cơ chế cũ (đọc từ eth1 deposit contract) đã
> được xử lý xong trước khi fork, nên có thể loại bỏ an toàn các trường
> `eth1_data`, `eth1_data_votes`, `eth1_deposit_index` và
> `deposit_requests_start_index`.
