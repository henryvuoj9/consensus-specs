# Electra Light Client -- Sync Protocol

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Types](#types)
  - [Modified `CurrentSyncCommitteeBranch`](#modified-currentsynccommitteebranch)
  - [Modified `FinalityBranch`](#modified-finalitybranch)
  - [Modified `NextSyncCommitteeBranch`](#modified-nextsynccommitteebranch)
- [Constants](#constants)
  - [Frozen constants](#frozen-constants)
  - [New constants](#new-constants)
- [Helpers](#helpers)
  - [Modified `finalized_root_gindex_at_slot`](#modified-finalized_root_gindex_at_slot)
  - [Modified `current_sync_committee_gindex_at_slot`](#modified-current_sync_committee_gindex_at_slot)
  - [Modified `next_sync_committee_gindex_at_slot`](#modified-next_sync_committee_gindex_at_slot)

<!-- mdformat-toc end -->

## Introduction

Bản nâng cấp này cập nhật light client data để phản ánh những thay đổi của Electra đối với các generalized index (gindex — chỉ số tổng quát của một node trong cây Merkle) của [`BeaconState`](../beacon-chain.md). Tài liệu này mở rộng
[Deneb Light Client specifications](../../deneb/light-client/sync-protocol.md).
[Fork document](./fork.md) giải thích cách nâng cấp các triển khai hiện có dựa trên Deneb lên Electra.

> 💡 Ghi chú: Electra thêm nhiều trường mới vào `BeaconState`, khiến số trường vượt quá 32 nên cây Merkle của state sâu thêm một tầng. Vì vậy gindex của `finalized_checkpoint.root`, `current_sync_committee` và `next_sync_committee` đều thay đổi, và độ dài các Merkle branch tương ứng tăng thêm 1.

Các tài liệu bổ sung mô tả tác động của bản nâng cấp đối với một số vai trò cụ thể:

- [Networking](./p2p-interface.md)

## Types

### Modified `CurrentSyncCommitteeBranch`

```python
# [Modified in Electra]
class CurrentSyncCommitteeBranch(Vector[Bytes32]):
    """
    A Merkle branch proving ``current_sync_committee`` within ``BeaconState``.
    """

    LENGTH = floorlog2(CURRENT_SYNC_COMMITTEE_GINDEX_ELECTRA)
```

### Modified `FinalityBranch`

```python
# [Modified in Electra]
class FinalityBranch(Vector[Bytes32]):
    """
    A Merkle branch proving ``finalized_checkpoint.root`` within
    ``BeaconState``.
    """

    LENGTH = floorlog2(FINALIZED_ROOT_GINDEX_ELECTRA)
```

### Modified `NextSyncCommitteeBranch`

```python
# [Modified in Electra]
class NextSyncCommitteeBranch(Vector[Bytes32]):
    """
    A Merkle branch proving ``next_sync_committee`` within ``BeaconState``.
    """

    LENGTH = floorlog2(NEXT_SYNC_COMMITTEE_GINDEX_ELECTRA)
```

## Constants

### Frozen constants

Các hằng số `GeneralizedIndex` hiện có được "đóng băng" (frozen) ở giá trị của
[Altair](../../altair/light-client/sync-protocol.md#constants), để vẫn dùng được khi xác minh data từ các fork trước Electra.

| Name                            | Value                                                                               |
| ------------------------------- | ----------------------------------------------------------------------------------- |
| `FINALIZED_ROOT_GINDEX`         | `get_generalized_index(altair.BeaconState, "finalized_checkpoint", "root")` (= 105) |
| `CURRENT_SYNC_COMMITTEE_GINDEX` | `get_generalized_index(altair.BeaconState, "current_sync_committee")` (= 54)        |
| `NEXT_SYNC_COMMITTEE_GINDEX`    | `get_generalized_index(altair.BeaconState, "next_sync_committee")` (= 55)           |

### New constants

| Name                                    | Value                                                                        |
| --------------------------------------- | ---------------------------------------------------------------------------- |
| `FINALIZED_ROOT_GINDEX_ELECTRA`         | `get_generalized_index(BeaconState, "finalized_checkpoint", "root")` (= 169) |
| `CURRENT_SYNC_COMMITTEE_GINDEX_ELECTRA` | `get_generalized_index(BeaconState, "current_sync_committee")` (= 86)        |
| `NEXT_SYNC_COMMITTEE_GINDEX_ELECTRA`    | `get_generalized_index(BeaconState, "next_sync_committee")` (= 87)           |

## Helpers

> 💡 Ghi chú: Các hàm helper dưới đây chọn gindex phù hợp dựa trên epoch của slot đầu vào: từ `ELECTRA_FORK_EPOCH` trở đi dùng gindex mới của Electra, còn trước đó dùng gindex đã đóng băng (giá trị Altair).

### Modified `finalized_root_gindex_at_slot`

```python
def finalized_root_gindex_at_slot(slot: Slot) -> GeneralizedIndex:
    epoch = compute_epoch_at_slot(slot)

    # [Modified in Electra]
    if epoch >= ELECTRA_FORK_EPOCH:
        return FINALIZED_ROOT_GINDEX_ELECTRA
    return FINALIZED_ROOT_GINDEX
```

### Modified `current_sync_committee_gindex_at_slot`

```python
def current_sync_committee_gindex_at_slot(slot: Slot) -> GeneralizedIndex:
    epoch = compute_epoch_at_slot(slot)

    # [Modified in Electra]
    if epoch >= ELECTRA_FORK_EPOCH:
        return CURRENT_SYNC_COMMITTEE_GINDEX_ELECTRA
    return CURRENT_SYNC_COMMITTEE_GINDEX
```

### Modified `next_sync_committee_gindex_at_slot`

```python
def next_sync_committee_gindex_at_slot(slot: Slot) -> GeneralizedIndex:
    epoch = compute_epoch_at_slot(slot)

    # [Modified in Electra]
    if epoch >= ELECTRA_FORK_EPOCH:
        return NEXT_SYNC_COMMITTEE_GINDEX_ELECTRA
    return NEXT_SYNC_COMMITTEE_GINDEX
```
