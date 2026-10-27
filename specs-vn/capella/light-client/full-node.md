# Capella Light Client -- Full Node

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Helpers](#helpers)
  - [Modified `block_to_light_client_header`](#modified-block_to_light_client_header)

<!-- mdformat-toc end -->

## Introduction

Như một phần của bản nâng cấp Capella, bản cập nhật này bổ sung thông tin về
execution payload vào light client data.

## Helpers

### Modified `block_to_light_client_header`

*(Full node dùng hàm này để tạo `LightClientHeader` từ một block. Từ
`CAPELLA_FORK_EPOCH` trở đi, header kèm theo `ExecutionPayloadHeader` và một
Merkle proof (`execution_branch`) chứng minh payload nằm trong block body.)*

```python
def block_to_light_client_header(block: SignedBeaconBlock) -> LightClientHeader:
    epoch = compute_epoch_at_slot(block.message.slot)

    if epoch >= CAPELLA_FORK_EPOCH:
        payload = block.message.body.execution_payload
        execution_header = ExecutionPayloadHeader(
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
            withdrawals_root=hash_tree_root(payload.withdrawals),
        )
        execution_branch = ExecutionBranch(
            data=compute_merkle_proof(block.message.body, EXECUTION_PAYLOAD_GINDEX)
        )
    else:
        # Lưu ý rằng trong giai đoạn chuyển fork, `finalized_header` vẫn có thể trỏ tới các fork cũ hơn.
        # Dù block Bellatrix cũng chứa `ExecutionPayload` (không có `withdrawals_root`),
        # nó không được đưa vào light client data tương ứng. Để đảm bảo tương thích
        # với dữ liệu cũ đi qua `upgrade_lc_header_to_capella`, ta bỏ qua dữ liệu execution.
        execution_header = ExecutionPayloadHeader.empty()
        execution_branch = ExecutionBranch()

    return LightClientHeader(
        beacon=BeaconBlockHeader(
            slot=block.message.slot,
            proposer_index=block.message.proposer_index,
            parent_root=block.message.parent_root,
            state_root=block.message.state_root,
            body_root=hash_tree_root(block.message.body),
        ),
        execution=execution_header,
        execution_branch=ExecutionBranch(data=execution_branch),
    )
```
