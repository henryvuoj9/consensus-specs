# Electra Light Client -- Fork Logic

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Helpers](#helpers)
  - [`normalize_merkle_branch`](#normalize_merkle_branch)
- [Upgrading light client data](#upgrading-light-client-data)
- [Upgrading the store](#upgrading-the-store)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả cách nâng cấp các đối tượng light client hiện có (được xây dựng theo
[Deneb specification](../../deneb/light-client/sync-protocol.md)) lên Electra.
Việc này là cần thiết khi một `LightClientStore` đã ở phiên bản sau Electra phải xử lý data có từ trước Electra.
Lưu ý rằng data được trao đổi qua các giao thức mạng vẫn dùng định dạng gốc (tức là định dạng của fork tương ứng với data đó); việc nâng cấp chỉ diễn ra cục bộ ở phía light client.

## Helpers

### `normalize_merkle_branch`

```python
def normalize_merkle_branch(
    branch: Sequence[Bytes32], gindex: GeneralizedIndex
) -> Sequence[Bytes32]:
    depth = floorlog2(gindex)
    num_extra = depth - len(branch)
    return [Bytes32()] * num_extra + [*branch]
```

> 💡 Ghi chú: Ở Electra, `BeaconState` có thêm nhiều trường mới nên cây Merkle của nó sâu hơn, làm các generalized index (gindex) thay đổi và các Merkle branch (nhánh Merkle proof) cần dài hơn. Hàm `normalize_merkle_branch` tính độ sâu `depth = floorlog2(gindex)` ứng với gindex mới, rồi chèn thêm các phần tử `Bytes32()` rỗng (toàn số 0) vào **đầu** branch cũ cho đủ độ dài `depth`. Branch sau khi chuẩn hóa có độ dài khớp với kiểu dữ liệu Electra; các phần tử thêm vào chỉ là giá trị đệm.

## Upgrading light client data

Một `LightClientStore` của Electra vẫn có thể xử lý light client data của các fork trước đó. Để làm được vậy, data trước Electra cần được nâng cấp cục bộ lên Electra trước khi xử lý.

```python
def upgrade_lc_header_to_electra(pre: deneb.LightClientHeader) -> LightClientHeader:
    return LightClientHeader(
        beacon=pre.beacon,
        execution=pre.execution,
        execution_branch=pre.execution_branch,
    )
```

```python
def upgrade_lc_bootstrap_to_electra(pre: deneb.LightClientBootstrap) -> LightClientBootstrap:
    return LightClientBootstrap(
        header=upgrade_lc_header_to_electra(pre.header),
        current_sync_committee=pre.current_sync_committee,
        current_sync_committee_branch=CurrentSyncCommitteeBranch(
            data=normalize_merkle_branch(
                pre.current_sync_committee_branch, CURRENT_SYNC_COMMITTEE_GINDEX_ELECTRA
            )
        ),
    )
```

```python
def upgrade_lc_update_to_electra(pre: deneb.LightClientUpdate) -> LightClientUpdate:
    return LightClientUpdate(
        attested_header=upgrade_lc_header_to_electra(pre.attested_header),
        next_sync_committee=pre.next_sync_committee,
        next_sync_committee_branch=NextSyncCommitteeBranch(
            data=normalize_merkle_branch(
                pre.next_sync_committee_branch, NEXT_SYNC_COMMITTEE_GINDEX_ELECTRA
            )
        ),
        finalized_header=upgrade_lc_header_to_electra(pre.finalized_header),
        finality_branch=FinalityBranch(
            data=normalize_merkle_branch(pre.finality_branch, FINALIZED_ROOT_GINDEX_ELECTRA)
        ),
        sync_aggregate=pre.sync_aggregate,
        signature_slot=pre.signature_slot,
    )
```

```python
def upgrade_lc_finality_update_to_electra(
    pre: deneb.LightClientFinalityUpdate,
) -> LightClientFinalityUpdate:
    return LightClientFinalityUpdate(
        attested_header=upgrade_lc_header_to_electra(pre.attested_header),
        finalized_header=upgrade_lc_header_to_electra(pre.finalized_header),
        finality_branch=FinalityBranch(
            data=normalize_merkle_branch(pre.finality_branch, FINALIZED_ROOT_GINDEX_ELECTRA)
        ),
        sync_aggregate=pre.sync_aggregate,
        signature_slot=pre.signature_slot,
    )
```

```python
def upgrade_lc_optimistic_update_to_electra(
    pre: deneb.LightClientOptimisticUpdate,
) -> LightClientOptimisticUpdate:
    return LightClientOptimisticUpdate(
        attested_header=upgrade_lc_header_to_electra(pre.attested_header),
        sync_aggregate=pre.sync_aggregate,
        signature_slot=pre.signature_slot,
    )
```

## Upgrading the store

Các đối tượng `LightClientStore` hiện có dựa trên Deneb MUST được nâng cấp lên Electra
trước khi có thể xử lý light client data dựa trên Electra. Việc nâng cấp `LightClientStore`
MAY được thực hiện trước `ELECTRA_FORK_EPOCH` (tức là không bắt buộc phải chờ đến đúng thời điểm fork).

```python
def upgrade_lc_store_to_electra(pre: deneb.LightClientStore) -> LightClientStore:
    if pre.best_valid_update is None:
        best_valid_update = None
    else:
        best_valid_update = upgrade_lc_update_to_electra(pre.best_valid_update)
    return LightClientStore(
        finalized_header=upgrade_lc_header_to_electra(pre.finalized_header),
        current_sync_committee=pre.current_sync_committee,
        next_sync_committee=pre.next_sync_committee,
        best_valid_update=best_valid_update,
        optimistic_header=upgrade_lc_header_to_electra(pre.optimistic_header),
        previous_max_active_participants=pre.previous_max_active_participants,
        current_max_active_participants=pre.current_max_active_participants,
    )
```
