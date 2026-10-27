# Deneb Light Client -- Sync Protocol

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Helpers](#helpers)
  - [Modified `get_lc_execution_root`](#modified-get_lc_execution_root)
  - [Modified `is_valid_light_client_header`](#modified-is_valid_light_client_header)

<!-- mdformat-toc end -->

## Introduction

Bản nâng cấp này cập nhật dữ liệu light client để phản ánh các thay đổi của Deneb
đối với cấu trúc [`ExecutionPayload`](../beacon-chain.md) (cụ thể là hai trường mới
`blob_gas_used` và `excess_blob_gas` trong execution payload header). Tài liệu này
mở rộng [Capella Light Client specifications](../../capella/light-client/sync-protocol.md).
[Tài liệu fork](./fork.md) giải thích cách nâng cấp các triển khai hiện có dựa trên
Capella lên Deneb.

Các tài liệu bổ sung mô tả tác động của bản nâng cấp đối với từng vai trò cụ thể:

- [Full node](./full-node.md)
- [Networking](./p2p-interface.md)

## Helpers

### Modified `get_lc_execution_root`

Hàm này tính root của execution header chứa trong `LightClientHeader`. Từ Deneb trở
đi, root được tính trực tiếp trên `header.execution` (kiểu Deneb). Với header thuộc
các epoch Capella (trước `DENEB_FORK_EPOCH`), hàm dựng lại một
`capella.ExecutionPayloadHeader` (bỏ các trường blob mới) để root khớp với root
gốc đã được commit trong beacon block của Capella. Trước Capella, không có
execution header nên trả về `Root()` rỗng.

```python
def get_lc_execution_root(header: LightClientHeader) -> Root:
    epoch = compute_epoch_at_slot(header.beacon.slot)

    # [New in Deneb] Từ Deneb trở đi: hash trực tiếp execution header kiểu Deneb
    if epoch >= DENEB_FORK_EPOCH:
        return hash_tree_root(header.execution)

    # [Modified in Deneb] Header thời Capella: dựng lại header kiểu Capella (không có trường blob)
    if epoch >= CAPELLA_FORK_EPOCH:
        execution_header = capella.ExecutionPayloadHeader(
            parent_hash=header.execution.parent_hash,
            fee_recipient=header.execution.fee_recipient,
            state_root=header.execution.state_root,
            receipts_root=header.execution.receipts_root,
            logs_bloom=header.execution.logs_bloom,
            prev_randao=header.execution.prev_randao,
            block_number=header.execution.block_number,
            gas_limit=header.execution.gas_limit,
            gas_used=header.execution.gas_used,
            timestamp=header.execution.timestamp,
            extra_data=header.execution.extra_data,
            base_fee_per_gas=header.execution.base_fee_per_gas,
            block_hash=header.execution.block_hash,
            transactions_root=header.execution.transactions_root,
            withdrawals_root=header.execution.withdrawals_root,
        )
        return hash_tree_root(execution_header)

    return Root()
```

### Modified `is_valid_light_client_header`

Hàm này kiểm tra tính hợp lệ của một `LightClientHeader`. Thay đổi trong Deneb: với
header thuộc epoch trước `DENEB_FORK_EPOCH`, các trường `blob_gas_used` và
`excess_blob_gas` PHẢI (MUST) bằng 0, vì chúng chưa tồn tại trước Deneb. Phần còn
lại giữ nguyên như Capella: trước Capella thì execution header và
`execution_branch` phải rỗng; từ Capella trở đi, `execution_branch` phải là Merkle
proof hợp lệ chứng minh execution root nằm trong `body_root` của beacon block header.

```python
def is_valid_light_client_header(header: LightClientHeader) -> bool:
    epoch = compute_epoch_at_slot(header.beacon.slot)

    # [New in Deneb:EIP4844] Trước Deneb, các trường blob gas phải bằng 0
    if epoch < DENEB_FORK_EPOCH:
        if header.execution.blob_gas_used != 0:
            return False
        if header.execution.excess_blob_gas != 0:
            return False

    if epoch < CAPELLA_FORK_EPOCH:
        return (
            header.execution == ExecutionPayloadHeader.empty()
            and header.execution_branch == ExecutionBranch()
        )

    return is_valid_merkle_branch(
        leaf=get_lc_execution_root(header),
        branch=header.execution_branch,
        depth=floorlog2(EXECUTION_PAYLOAD_GINDEX),
        index=get_subtree_index(EXECUTION_PAYLOAD_GINDEX),
        root=header.beacon.body_root,
    )
```
