# Gloas Light Client -- Fork Logic

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Upgrading light client data](#upgrading-light-client-data)
- [Upgrading the store](#upgrading-the-store)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả cách nâng cấp các đối tượng light client hiện có, vốn dựa
trên [Electra specification](../../electra/light-client/sync-protocol.md), lên
Gloas. Việc này cần thiết khi xử lý dữ liệu trước Gloas bằng một
`LightClientStore` sau Gloas. Lưu ý rằng dữ liệu trao đổi qua các giao thức mạng
vẫn dùng định dạng gốc (định dạng của fork tạo ra dữ liệu đó).

## Upgrading light client data

Một `LightClientStore` của Gloas vẫn có thể xử lý dữ liệu light client cũ hơn.
Để làm được điều đó, dữ liệu trước Gloas cần được nâng cấp cục bộ lên Gloas
trước khi xử lý.

> 💡 Ghi chú: Trong Gloas, `LightClientHeader` không còn chứa toàn bộ execution
> payload header mà chỉ giữ `execution_block_hash` cùng Merkle proof
> (`execution_branch`). Vì vậy `upgrade_lc_header_to_gloas` tính proof cho trường
> `block_hash` bên trong execution header cũ, nối với `execution_branch` cũ, rồi
> chuẩn hóa độ dài branch theo `EXECUTION_BLOCK_HASH_GINDEX_GLOAS`. Header trước
> Capella không có execution data nên dùng giá trị rỗng. Các branch khác (sync
> committee, finality) chỉ cần chuẩn hóa lại theo gindex mới.

```python
def upgrade_lc_header_to_gloas(pre: electra.LightClientHeader) -> LightClientHeader:
    if pre == electra.LightClientHeader.empty():
        return LightClientHeader.empty()

    epoch = compute_epoch_at_slot(pre.beacon.slot)

    if epoch >= DENEB_FORK_EPOCH:
        BLOCK_HASH_GINDEX = get_generalized_index(deneb.ExecutionPayloadHeader, "block_hash")
        return LightClientHeader(
            beacon=pre.beacon,
            execution_block_hash=pre.execution.block_hash,
            execution_branch=ExecutionBranch(
                data=normalize_merkle_branch(
                    list(compute_merkle_proof(pre.execution, BLOCK_HASH_GINDEX))
                    + list(pre.execution_branch),
                    EXECUTION_BLOCK_HASH_GINDEX_GLOAS,
                )
            ),
        )

    if epoch >= CAPELLA_FORK_EPOCH:
        execution_header = capella.ExecutionPayloadHeader(
            parent_hash=pre.execution.parent_hash,
            fee_recipient=pre.execution.fee_recipient,
            state_root=pre.execution.state_root,
            receipts_root=pre.execution.receipts_root,
            logs_bloom=pre.execution.logs_bloom,
            prev_randao=pre.execution.prev_randao,
            block_number=pre.execution.block_number,
            gas_limit=pre.execution.gas_limit,
            gas_used=pre.execution.gas_used,
            timestamp=pre.execution.timestamp,
            extra_data=pre.execution.extra_data,
            base_fee_per_gas=pre.execution.base_fee_per_gas,
            block_hash=pre.execution.block_hash,
            transactions_root=pre.execution.transactions_root,
            withdrawals_root=pre.execution.withdrawals_root,
        )
        BLOCK_HASH_GINDEX = get_generalized_index(capella.ExecutionPayloadHeader, "block_hash")
        return LightClientHeader(
            beacon=pre.beacon,
            execution_block_hash=pre.execution.block_hash,
            execution_branch=ExecutionBranch(
                data=normalize_merkle_branch(
                    list(compute_merkle_proof(execution_header, BLOCK_HASH_GINDEX))
                    + list(pre.execution_branch),
                    EXECUTION_BLOCK_HASH_GINDEX_GLOAS,
                )
            ),
        )

    return LightClientHeader(
        beacon=pre.beacon,
        execution_block_hash=Hash32(),
        execution_branch=ExecutionBranch(),
    )
```

```python
def upgrade_lc_bootstrap_to_gloas(pre: electra.LightClientBootstrap) -> LightClientBootstrap:
    return LightClientBootstrap(
        header=upgrade_lc_header_to_gloas(pre.header),
        current_sync_committee=pre.current_sync_committee,
        current_sync_committee_branch=CurrentSyncCommitteeBranch(
            data=normalize_merkle_branch(
                pre.current_sync_committee_branch, CURRENT_SYNC_COMMITTEE_GINDEX_GLOAS
            )
        ),
    )
```

```python
def upgrade_lc_update_to_gloas(pre: electra.LightClientUpdate) -> LightClientUpdate:
    return LightClientUpdate(
        attested_header=upgrade_lc_header_to_gloas(pre.attested_header),
        next_sync_committee=pre.next_sync_committee,
        next_sync_committee_branch=NextSyncCommitteeBranch(
            data=normalize_merkle_branch(
                pre.next_sync_committee_branch, NEXT_SYNC_COMMITTEE_GINDEX_GLOAS
            )
        ),
        finalized_header=upgrade_lc_header_to_gloas(pre.finalized_header),
        finality_branch=FinalityBranch(
            data=normalize_merkle_branch(pre.finality_branch, FINALIZED_ROOT_GINDEX_GLOAS)
        ),
        sync_aggregate=pre.sync_aggregate,
        signature_slot=pre.signature_slot,
    )
```

```python
def upgrade_lc_finality_update_to_gloas(
    pre: electra.LightClientFinalityUpdate,
) -> LightClientFinalityUpdate:
    return LightClientFinalityUpdate(
        attested_header=upgrade_lc_header_to_gloas(pre.attested_header),
        finalized_header=upgrade_lc_header_to_gloas(pre.finalized_header),
        finality_branch=FinalityBranch(
            data=normalize_merkle_branch(pre.finality_branch, FINALIZED_ROOT_GINDEX_GLOAS)
        ),
        sync_aggregate=pre.sync_aggregate,
        signature_slot=pre.signature_slot,
    )
```

```python
def upgrade_lc_optimistic_update_to_gloas(
    pre: electra.LightClientOptimisticUpdate,
) -> LightClientOptimisticUpdate:
    return LightClientOptimisticUpdate(
        attested_header=upgrade_lc_header_to_gloas(pre.attested_header),
        sync_aggregate=pre.sync_aggregate,
        signature_slot=pre.signature_slot,
    )
```

## Upgrading the store

Các đối tượng `LightClientStore` hiện có dựa trên Electra MUST được nâng cấp lên
Gloas trước khi có thể xử lý dữ liệu light client dựa trên Gloas. Việc nâng cấp
`LightClientStore` MAY được thực hiện trước `GLOAS_FORK_EPOCH`.

```python
def upgrade_lc_store_to_gloas(pre: electra.LightClientStore) -> LightClientStore:
    if pre.best_valid_update is None:
        best_valid_update = None
    else:
        best_valid_update = upgrade_lc_update_to_gloas(pre.best_valid_update)
    return LightClientStore(
        finalized_header=upgrade_lc_header_to_gloas(pre.finalized_header),
        current_sync_committee=pre.current_sync_committee,
        next_sync_committee=pre.next_sync_committee,
        best_valid_update=best_valid_update,
        optimistic_header=upgrade_lc_header_to_gloas(pre.optimistic_header),
        previous_max_active_participants=pre.previous_max_active_participants,
        current_max_active_participants=pre.current_max_active_participants,
    )
```
