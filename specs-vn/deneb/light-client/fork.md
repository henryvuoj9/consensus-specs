# Deneb Light Client -- Fork Logic

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Upgrading light client data](#upgrading-light-client-data)
- [Upgrading the store](#upgrading-the-store)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả cách nâng cấp các đối tượng light client hiện có (dựa trên
[đặc tả Capella](../../capella/light-client/sync-protocol.md)) lên Deneb. Việc
này cần thiết khi xử lý data trước Deneb bằng một `LightClientStore` sau Deneb.
Lưu ý rằng data được trao đổi qua các giao thức mạng vẫn dùng định dạng gốc.

## Upgrading light client data

Một `LightClientStore` Deneb vẫn có thể xử lý light client data cũ hơn. Để làm
được vậy, data trước Deneb cần được nâng cấp cục bộ lên Deneb trước khi xử lý.

```python
def upgrade_lc_header_to_deneb(pre: capella.LightClientHeader) -> LightClientHeader:
    return LightClientHeader(
        beacon=pre.beacon,
        execution=ExecutionPayloadHeader(
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
            # [New in Deneb:EIP4844]
            blob_gas_used=Uint64(0),
            # [New in Deneb:EIP4844]
            excess_blob_gas=Uint64(0),
        ),
        execution_branch=pre.execution_branch,
    )
```

```python
def upgrade_lc_bootstrap_to_deneb(pre: capella.LightClientBootstrap) -> LightClientBootstrap:
    return LightClientBootstrap(
        header=upgrade_lc_header_to_deneb(pre.header),
        current_sync_committee=pre.current_sync_committee,
        current_sync_committee_branch=pre.current_sync_committee_branch,
    )
```

```python
def upgrade_lc_update_to_deneb(pre: capella.LightClientUpdate) -> LightClientUpdate:
    return LightClientUpdate(
        attested_header=upgrade_lc_header_to_deneb(pre.attested_header),
        next_sync_committee=pre.next_sync_committee,
        next_sync_committee_branch=pre.next_sync_committee_branch,
        finalized_header=upgrade_lc_header_to_deneb(pre.finalized_header),
        finality_branch=pre.finality_branch,
        sync_aggregate=pre.sync_aggregate,
        signature_slot=pre.signature_slot,
    )
```

```python
def upgrade_lc_finality_update_to_deneb(
    pre: capella.LightClientFinalityUpdate,
) -> LightClientFinalityUpdate:
    return LightClientFinalityUpdate(
        attested_header=upgrade_lc_header_to_deneb(pre.attested_header),
        finalized_header=upgrade_lc_header_to_deneb(pre.finalized_header),
        finality_branch=pre.finality_branch,
        sync_aggregate=pre.sync_aggregate,
        signature_slot=pre.signature_slot,
    )
```

```python
def upgrade_lc_optimistic_update_to_deneb(
    pre: capella.LightClientOptimisticUpdate,
) -> LightClientOptimisticUpdate:
    return LightClientOptimisticUpdate(
        attested_header=upgrade_lc_header_to_deneb(pre.attested_header),
        sync_aggregate=pre.sync_aggregate,
        signature_slot=pre.signature_slot,
    )
```

## Upgrading the store

Các đối tượng `LightClientStore` hiện có dựa trên Capella MUST được nâng cấp lên
Deneb trước khi có thể xử lý light client data dựa trên Deneb. Việc nâng cấp
`LightClientStore` MAY được thực hiện trước `DENEB_FORK_EPOCH`.

```python
def upgrade_lc_store_to_deneb(pre: capella.LightClientStore) -> LightClientStore:
    if pre.best_valid_update is None:
        best_valid_update = None
    else:
        best_valid_update = upgrade_lc_update_to_deneb(pre.best_valid_update)
    return LightClientStore(
        finalized_header=upgrade_lc_header_to_deneb(pre.finalized_header),
        current_sync_committee=pre.current_sync_committee,
        next_sync_committee=pre.next_sync_committee,
        best_valid_update=best_valid_update,
        optimistic_header=upgrade_lc_header_to_deneb(pre.optimistic_header),
        previous_max_active_participants=pre.previous_max_active_participants,
        current_max_active_participants=pre.current_max_active_participants,
    )
```
