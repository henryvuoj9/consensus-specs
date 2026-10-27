# Capella Light Client -- Sync Protocol

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Types](#types)
  - [New `ExecutionBranch`](#new-executionbranch)
- [Constants](#constants)
- [Containers](#containers)
  - [Modified `LightClientHeader`](#modified-lightclientheader)
  - [Modified `LightClientBootstrap`](#modified-lightclientbootstrap)
  - [Modified `LightClientUpdate`](#modified-lightclientupdate)
  - [Modified `LightClientFinalityUpdate`](#modified-lightclientfinalityupdate)
  - [Modified `LightClientOptimisticUpdate`](#modified-lightclientoptimisticupdate)
  - [Modified `LightClientStore`](#modified-lightclientstore)
- [Helpers](#helpers)
  - [`get_lc_execution_root`](#get_lc_execution_root)
  - [Modified `is_valid_light_client_header`](#modified-is_valid_light_client_header)

<!-- mdformat-toc end -->

## Introduction

Bản nâng cấp này bổ sung thông tin về execution payload vào dữ liệu light client
(client nhẹ, chỉ theo dõi header thay vì toàn bộ chain) trong khuôn khổ bản nâng
cấp Capella. Tài liệu này mở rộng
[Altair Light Client specifications](../../altair/light-client/sync-protocol.md).
[Tài liệu fork](./fork.md) giải thích cách nâng cấp các triển khai hiện có dựa
trên Altair lên Capella.

Các tài liệu bổ sung mô tả ảnh hưởng của bản nâng cấp đối với một số vai trò cụ
thể:

- [Full node](./full-node.md)
- [Networking](./p2p-interface.md)

## Types

### New `ExecutionBranch`

```python
class ExecutionBranch(Vector[Bytes32]):
    """
    A Merkle branch proving ``execution_payload`` within ``BeaconBlockBody``.
    """

    LENGTH = floorlog2(EXECUTION_PAYLOAD_GINDEX)
```

> 💡 Ghi chú: `ExecutionBranch` là một Merkle proof (nhánh Merkle) chứng minh
> rằng `execution_payload` (dưới dạng header) thực sự nằm trong
> `BeaconBlockBody` có `body_root` tương ứng. Độ dài nhánh bằng độ sâu của
> generalized index `EXECUTION_PAYLOAD_GINDEX`.

## Constants

| Name                       | Value                                                                |
| -------------------------- | -------------------------------------------------------------------- |
| `EXECUTION_PAYLOAD_GINDEX` | `get_generalized_index(BeaconBlockBody, "execution_payload")` (= 25) |

## Containers

### Modified `LightClientHeader`

```python
class LightClientHeader(Container):
    beacon: BeaconBlockHeader
    # [New in Capella]
    execution: ExecutionPayloadHeader
    # [New in Capella]
    execution_branch: ExecutionBranch
```

> 💡 Ghi chú: Từ Capella, `LightClientHeader` không chỉ chứa `BeaconBlockHeader`
> mà còn chứa `ExecutionPayloadHeader` cùng với Merkle proof
> (`execution_branch`) để light client có thể xác minh thông tin của execution
> layer (ví dụ: block hash, state root của execution) mà không cần tải toàn bộ
> block.

### Modified `LightClientBootstrap`

```python
class LightClientBootstrap(Container):
    # [Modified in Capella]
    header: LightClientHeader
    current_sync_committee: SyncCommittee
    current_sync_committee_branch: CurrentSyncCommitteeBranch
```

### Modified `LightClientUpdate`

```python
class LightClientUpdate(Container):
    # [Modified in Capella]
    attested_header: LightClientHeader
    next_sync_committee: SyncCommittee
    next_sync_committee_branch: NextSyncCommitteeBranch
    # [Modified in Capella]
    finalized_header: LightClientHeader
    finality_branch: FinalityBranch
    sync_aggregate: SyncAggregate
    signature_slot: Slot
```

### Modified `LightClientFinalityUpdate`

```python
class LightClientFinalityUpdate(Container):
    # [Modified in Capella]
    attested_header: LightClientHeader
    # [Modified in Capella]
    finalized_header: LightClientHeader
    finality_branch: FinalityBranch
    sync_aggregate: SyncAggregate
    signature_slot: Slot
```

### Modified `LightClientOptimisticUpdate`

```python
class LightClientOptimisticUpdate(Container):
    # [Modified in Capella]
    attested_header: LightClientHeader
    sync_aggregate: SyncAggregate
    signature_slot: Slot
```

### Modified `LightClientStore`

```python
@dataclass
class LightClientStore:
    # [Modified in Capella]
    finalized_header: LightClientHeader
    current_sync_committee: SyncCommittee
    next_sync_committee: SyncCommittee
    # [Modified in Capella]
    best_valid_update: LightClientUpdate | None
    # [Modified in Capella]
    optimistic_header: LightClientHeader
    previous_max_active_participants: Uint64
    current_max_active_participants: Uint64
```

## Helpers

### `get_lc_execution_root`

*(Trả về hash tree root của phần execution trong header; với các header trước
Capella thì trả về `Root()` rỗng)*

```python
def get_lc_execution_root(header: LightClientHeader) -> Root:
    epoch = compute_epoch_at_slot(header.beacon.slot)

    if epoch >= CAPELLA_FORK_EPOCH:
        return hash_tree_root(header.execution)

    return Root()
```

### Modified `is_valid_light_client_header`

```python
def is_valid_light_client_header(header: LightClientHeader) -> bool:
    epoch = compute_epoch_at_slot(header.beacon.slot)

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

> 💡 Ghi chú: Nói cách khác, với header thuộc epoch trước Capella, các trường
> `execution` và `execution_branch` bắt buộc phải rỗng (giá trị mặc định). Từ
> Capella trở đi, header hợp lệ khi và chỉ khi Merkle proof `execution_branch`
> chứng minh được rằng `execution` nằm trong `body_root` của beacon block header.
