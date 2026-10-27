# Capella Light Client -- Fork Logic

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Upgrading light client data](#upgrading-light-client-data)
- [Upgrading the store](#upgrading-the-store)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả cách nâng cấp các đối tượng light client hiện có, vốn dựa trên
[Altair specification](../../altair/light-client/sync-protocol.md), lên Capella.
Việc này là cần thiết khi xử lý dữ liệu trước Capella bằng một
`LightClientStore` sau Capella. Lưu ý rằng dữ liệu trao đổi qua các giao thức
mạng vẫn dùng định dạng gốc (định dạng của fork tương ứng).

## Upgrading light client data

Một `LightClientStore` của Capella vẫn có thể xử lý light client data cũ hơn. Để
làm được điều đó, dữ liệu trước Capella cần được nâng cấp cục bộ lên Capella
trước khi xử lý.

> 💡 Ghi chú: Vì header trước Capella không có thông tin execution, khi nâng cấp,
> trường `execution` được đặt thành `ExecutionPayloadHeader` rỗng và
> `execution_branch` là branch rỗng. Các trường còn lại được giữ nguyên.

```python
def upgrade_lc_header_to_capella(pre: altair.LightClientHeader) -> LightClientHeader:
    return LightClientHeader(
        beacon=pre.beacon,
        execution=ExecutionPayloadHeader.empty(),
        execution_branch=ExecutionBranch(),
    )
```

```python
def upgrade_lc_bootstrap_to_capella(pre: altair.LightClientBootstrap) -> LightClientBootstrap:
    return LightClientBootstrap(
        header=upgrade_lc_header_to_capella(pre.header),
        current_sync_committee=pre.current_sync_committee,
        current_sync_committee_branch=pre.current_sync_committee_branch,
    )
```

```python
def upgrade_lc_update_to_capella(pre: altair.LightClientUpdate) -> LightClientUpdate:
    return LightClientUpdate(
        attested_header=upgrade_lc_header_to_capella(pre.attested_header),
        next_sync_committee=pre.next_sync_committee,
        next_sync_committee_branch=pre.next_sync_committee_branch,
        finalized_header=upgrade_lc_header_to_capella(pre.finalized_header),
        finality_branch=pre.finality_branch,
        sync_aggregate=pre.sync_aggregate,
        signature_slot=pre.signature_slot,
    )
```

```python
def upgrade_lc_finality_update_to_capella(
    pre: altair.LightClientFinalityUpdate,
) -> LightClientFinalityUpdate:
    return LightClientFinalityUpdate(
        attested_header=upgrade_lc_header_to_capella(pre.attested_header),
        finalized_header=upgrade_lc_header_to_capella(pre.finalized_header),
        finality_branch=pre.finality_branch,
        sync_aggregate=pre.sync_aggregate,
        signature_slot=pre.signature_slot,
    )
```

```python
def upgrade_lc_optimistic_update_to_capella(
    pre: altair.LightClientOptimisticUpdate,
) -> LightClientOptimisticUpdate:
    return LightClientOptimisticUpdate(
        attested_header=upgrade_lc_header_to_capella(pre.attested_header),
        sync_aggregate=pre.sync_aggregate,
        signature_slot=pre.signature_slot,
    )
```

## Upgrading the store

Các đối tượng `LightClientStore` hiện có dựa trên Altair MUST được nâng cấp lên
Capella trước khi có thể xử lý light client data dựa trên Capella. Việc nâng cấp
`LightClientStore` MAY được thực hiện trước `CAPELLA_FORK_EPOCH`.

```python
def upgrade_lc_store_to_capella(pre: altair.LightClientStore) -> LightClientStore:
    if pre.best_valid_update is None:
        best_valid_update = None
    else:
        best_valid_update = upgrade_lc_update_to_capella(pre.best_valid_update)
    return LightClientStore(
        finalized_header=upgrade_lc_header_to_capella(pre.finalized_header),
        current_sync_committee=pre.current_sync_committee,
        next_sync_committee=pre.next_sync_committee,
        best_valid_update=best_valid_update,
        optimistic_header=upgrade_lc_header_to_capella(pre.optimistic_header),
        previous_max_active_participants=pre.previous_max_active_participants,
        current_max_active_participants=pre.current_max_active_participants,
    )
```
