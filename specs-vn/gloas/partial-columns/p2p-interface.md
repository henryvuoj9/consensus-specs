# Gloas Partial Columns -- Networking

*Lưu ý*: Tài liệu này vẫn đang trong quá trình hoàn thiện, dành cho các nhà
nghiên cứu và đội ngũ triển khai client.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Types](#types)
  - [Modified `CellsBitList`](#modified-cellsbitlist)
- [Containers](#containers)
  - [Modified `PartialDataColumnSidecar`](#modified-partialdatacolumnsidecar)
  - [Modified `PartialDataColumnPartsMetadata`](#modified-partialdatacolumnpartsmetadata)
  - [Modified `PartialDataColumnGroupID`](#modified-partialdatacolumngroupid)
- [Helpers](#helpers)
  - [New `compute_max_partial_data_column_sidecar_size`](#new-compute_max_partial_data_column_sidecar_size)
- [The gossip domain: gossipsub](#the-gossip-domain-gossipsub)
  - [Blob subnets](#blob-subnets)
    - [Modified `data_column_sidecar_{subnet_id}` (partial messages)](#modified-data_column_sidecar_subnet_id-partial-messages)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này đặc tả các thay đổi của Gloas đối với việc phát tán partial column
(cột dữ liệu từng phần) thông qua Partial Message Extension của gossipsub.

Đặc tả các thay đổi này được trình bày theo cùng định dạng với các đặc tả mạng
của những lần nâng cấp trước, và coi chúng là điều kiện tiên quyết. Cụ thể, tài
liệu này được xây dựng dựa trên
[Fulu partial columns networking specification](../../fulu/partial-columns/p2p-interface.md)
và [Gloas networking specification](../p2p-interface.md).

> 💡 Ghi chú: Trong Gloas (EIP-7732, ePBS), execution payload và danh sách blob
> KZG commitment được tách khỏi beacon block và được cam kết qua bid của builder
> (`signed_execution_payload_bid`). Vì vậy partial sidecar không còn mang
> `header` riêng nữa, mà được xác định thông qua block root và slot trong
> `PartialDataColumnGroupID`.

## Types

### Modified `CellsBitList`

```python
# [Modified in Gloas:EIP7688]
class CellsBitList(ProgressiveBitList):
    """
    A bitfield over the cells of a column, one bit per blob.
    """
```

## Containers

### Modified `PartialDataColumnSidecar`

```python
class PartialDataColumnSidecar(Container):
    cells_present_bitmap: CellsBitList
    partial_column: DataColumn
    kzg_proofs: KZGProofs
    # [Modified in Gloas:EIP7732]
    # Removed `header`
```

### Modified `PartialDataColumnPartsMetadata`

```python
class PartialDataColumnPartsMetadata(Container):
    # [Modified in Gloas:EIP7688]
    available: CellsBitList
    # [Modified in Gloas:EIP7688]
    requests: CellsBitList
```

### Modified `PartialDataColumnGroupID`

```python
class PartialDataColumnGroupID(Container):
    beacon_block_root: Root
    # [New in Gloas:EIP7732]
    slot: Slot
```

## Helpers

### New `compute_max_partial_data_column_sidecar_size`

```python
def compute_max_partial_data_column_sidecar_size() -> Uint64:
    """
    Return the maximum size of a serialized ``PartialDataColumnSidecar``
    computed using the largest ``max_blobs_per_block`` value from the blob
    schedule, regardless of whether or not that is the current
    ``max_blobs_per_block``.
    """
    max_blobs = MAX_BLOBS_PER_BLOCK_ELECTRA
    for entry in BLOB_SCHEDULE:
        max_blobs = max(max_blobs, entry["MAX_BLOBS_PER_BLOCK"])

    sidecar = PartialDataColumnSidecar(
        cells_present_bitmap=CellsBitList(data=[Boolean()] * max_blobs),
        partial_column=DataColumn(data=[Cell()] * max_blobs),
        kzg_proofs=KZGProofs(data=[KZGProof()] * max_blobs),
    )
    return Uint64(len(ssz_serialize(sidecar)))
```

## The gossip domain: gossipsub

### Blob subnets

#### Modified `data_column_sidecar_{subnet_id}` (partial messages)

*Lưu ý*: Các KZG commitment cần thiết để xác minh một partial sidecar giờ đây
được mang trong bid, tại
`block.body.signed_execution_payload_bid.message.blob_kzg_commitments`, trong đó
`block` là `BeaconBlock` có root bằng `group_id.beacon_block_root`. Mọi bước kiểm
tra liên quan đến header từ Fulu đều bị loại bỏ; vai trò của chúng được thay thế
bởi các commitment trong bid cùng với việc validation block tương ứng.

*Lưu ý*: Bước kiểm tra tùy chọn "với các cell mà bên nhận đã có, dữ liệu cell và
proof trong sidecar phải bằng với bản sao cục bộ" không được thể hiện trong code
bên dưới. Bên gửi MUST luôn gửi dữ liệu cell và proof hợp lệ; bên nhận MAY thực
hiện phép so sánh bằng này với bản sao cục bộ của mình như một biện pháp bảo vệ
bổ sung.

```python
def validate_partial_data_column_sidecar_gossip(
    # [Modified in Gloas:EIP7732]
    # Removed `seen`
    store: Store,
    sidecar: PartialDataColumnSidecar,
    # [Modified in Gloas:EIP7732]
    # Removed `current_time_ms`
    group_id: PartialDataColumnGroupID,
    column_index: ColumnIndex,
) -> None:
    """
    Validate a PartialDataColumnSidecar for gossip propagation on a subnet.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    num_cells_present = get_set_bit_count(sidecar.cells_present_bitmap)

    # [Modified in Gloas:EIP7732]
    # [REJECT] Message chứa ít nhất một cell
    if num_cells_present == 0:
        raise GossipReject("partial message is semantically empty")

    # [REJECT] Số lượng cell bằng số bit được bật trong bitmap
    if len(sidecar.partial_column) != num_cells_present:
        raise GossipReject("number of cells does not match number of set bits")

    # [REJECT] Số lượng proof bằng số bit được bật trong bitmap
    if len(sidecar.kzg_proofs) != num_cells_present:
        raise GossipReject("number of proofs does not match number of set bits")

    # [New in Gloas:EIP7732]
    # [IGNORE] Block của group ID đã được thấy (qua gossip hoặc nguồn không phải gossip)
    # (MAY đưa vào hàng đợi cho đến khi block được truy xuất)
    # (SHOULD đưa vào hàng đợi ít nhất một sidecar cho mỗi peer trên mỗi subnet)
    if group_id.beacon_block_root not in store.blocks:
        raise GossipIgnore("group id's block has not been seen")

    # [New in Gloas:EIP7732]
    # [REJECT] Block của group ID qua được validation
    if group_id.beacon_block_root not in store.block_states:
        raise GossipReject("group id's block failed validation")

    block = store.blocks[group_id.beacon_block_root]

    # [New in Gloas:EIP7732]
    # [REJECT] Slot của group ID khớp với slot của block
    if group_id.slot != block.slot:
        raise GossipReject("group id's slot does not match the block's slot")

    bid = block.body.signed_execution_payload_bid.message

    # [Modified in Gloas:EIP7732]
    # [REJECT] Độ dài bitmap cells present bằng số lượng commitment của bid
    if len(sidecar.cells_present_bitmap) != len(bid.blob_kzg_commitments):
        raise GossipReject("bitmap length does not match commitments length")

    # [Modified in Gloas:EIP7732]
    # [REJECT] Dữ liệu cell và proof của sidecar qua được KZG verification
    if not verify_partial_data_column_sidecar_kzg_proofs(
        sidecar, bid.blob_kzg_commitments, column_index
    ):
        raise GossipReject("invalid sidecar kzg proofs")
```
