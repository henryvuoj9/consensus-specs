# Fulu -- Honest Validator

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Configs](#configs)
  - [Custody setting](#custody-setting)
- [Types](#types)
  - [`CellKZGProofs`](#cellkzgproofs)
- [Helpers](#helpers)
  - [`BlobsBundle`](#blobsbundle)
  - [Modified `GetPayloadResponse`](#modified-getpayloadresponse)
- [Protocols](#protocols)
  - [`ExecutionEngine`](#executionengine)
    - [Modified `get_payload`](#modified-get_payload)
- [Beacon chain responsibilities](#beacon-chain-responsibilities)
  - [Validator custody](#validator-custody)
  - [Block and sidecar proposal](#block-and-sidecar-proposal)
    - [Constructing the `DataColumnSidecar`s](#constructing-the-datacolumnsidecars)
      - [`get_data_column_sidecars`](#get_data_column_sidecars)
      - [`get_data_column_sidecars_from_block`](#get_data_column_sidecars_from_block)
      - [`get_data_column_sidecars_from_column_sidecar`](#get_data_column_sidecars_from_column_sidecar)
    - [Sidecar publishing](#sidecar-publishing)
    - [Sidecar retention](#sidecar-retention)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả những thay đổi cần thực hiện trong code của một "honest
validator" (validator trung thực) để triển khai Fulu.

## Prerequisites

Tài liệu này là phần mở rộng của hướng dẫn
[Electra -- Honest Validator](../electra/validator.md). Mọi hành vi và định
nghĩa trong tài liệu này, cũng như trong các tài liệu mà nó mở rộng, đều được
giữ nguyên trừ khi được ghi chú hoặc ghi đè một cách tường minh.

Mọi thuật ngữ, hằng số, hàm và cơ chế giao thức được định nghĩa trong
[Fulu -- Beacon Chain](./beacon-chain.md) và
[Fulu -- Data Availability Sampling Core](./das-core.md) là kiến thức cần có
trước cho tài liệu này và được sử dụng xuyên suốt.

## Configs

### Custody setting

| Name                                   | Value              | Description                                                                                                |
| -------------------------------------- | ------------------ | ---------------------------------------------------------------------------------------------------------- |
| `VALIDATOR_CUSTODY_REQUIREMENT`        | `Uint64(8)`        | Số custody group tối thiểu mà một honest node có gắn validator phải custody (lưu giữ) và phục vụ sample từ đó |
| `BALANCE_PER_ADDITIONAL_CUSTODY_GROUP` | `Gwei(32 * 10**9)` | Lượng effective balance tương ứng với việc phải custody thêm một group                                     |

## Types

### `CellKZGProofs`

```python
class CellKZGProofs(List[KZGProof]):
    """
    The KZG cell proofs for every blob in a block, one proof per cell.
    """

    LIMIT = FIELD_ELEMENTS_PER_EXT_BLOB * MAX_BLOB_COMMITMENTS_PER_BLOCK
```

## Helpers

### `BlobsBundle`

*[Modified in Fulu:EIP7594]*

Đối tượng `BlobsBundle` được sửa đổi để chứa các cell KZG proof thay vì blob
KZG proof.

> 💡 Ghi chú: Trước Fulu, mỗi blob có một KZG proof duy nhất. Từ Fulu (PeerDAS),
> mỗi blob được mở rộng và chia thành các cell, và mỗi cell có proof riêng, nên
> `proofs` giờ chứa `CELLS_PER_EXT_BLOB` proof cho mỗi blob.

```python
@dataclass
class BlobsBundle:
    commitments: BlobKZGCommitments
    # [Modified in Fulu:EIP7594]
    proofs: CellKZGProofs
    blobs: Blobs
```

### Modified `GetPayloadResponse`

*[Modified in Fulu:EIP7594]*

Đối tượng `GetPayloadResponse` được sửa đổi để dùng đối tượng `BlobsBundle` đã
cập nhật.

```python
@dataclass
class GetPayloadResponse:
    execution_payload: ExecutionPayload
    block_value: Uint256
    # [Modified in Fulu:EIP7594]
    blobs_bundle: BlobsBundle
    execution_requests: Sequence[bytes]
```

## Protocols

### `ExecutionEngine`

#### Modified `get_payload`

*Lưu ý*: Hàm `get_payload` trả về đối tượng `GetPayloadResponse` đã được cập
nhật.

```python
def get_payload(self: ExecutionEngine, payload_id: PayloadId) -> GetPayloadResponse:
    """
    Return ExecutionPayload, Uint256, BlobsBundle, and execution requests (as Sequence[bytes]) objects.
    """
```

## Beacon chain responsibilities

### Validator custody

*[New in Fulu:EIP7594]*

Một node có gắn validator sẽ tải về và custody (lưu giữ) số custody group tối
thiểu cao hơn mỗi slot, được xác định bởi
`get_validators_custody_requirement(state, validator_indices)`. Ở đây, `state`
là `BeaconState` finalized gần nhất, còn `validator_indices` là danh sách index
của các validator gắn với node. Bất kỳ node nào có ít nhất một validator, với
tổng effective balance của tất cả validator gắn kèm là `total_node_balance`, sẽ
tải về và custody
`total_node_balance // BALANCE_PER_ADDITIONAL_CUSTODY_GROUP` custody group mỗi
slot, tối thiểu là `VALIDATOR_CUSTODY_REQUIREMENT` và dĩ nhiên tối đa là
`NUMBER_OF_CUSTODY_GROUPS`.

> 💡 Ghi chú: Ví dụ, một node chạy validator với tổng effective balance 320 ETH
> sẽ có `count = 10`, tức custody 10 group; node chỉ có 1 validator 32 ETH vẫn
> phải custody tối thiểu 8 group. Node càng stake nhiều thì càng gánh nhiều dữ
> liệu hơn.

```python
def get_validators_custody_requirement(
    state: BeaconState, validator_indices: Sequence[ValidatorIndex]
) -> Uint64:
    total_node_balance = sum(
        state.validators[index].effective_balance for index in validator_indices
    )
    count = total_node_balance // BALANCE_PER_ADDITIONAL_CUSTODY_GROUP
    return min(max(count, VALIDATOR_CUSTODY_REQUIREMENT), NUMBER_OF_CUSTODY_GROUPS)
```

Mức custody cao hơn này được công bố trong Metadata của node bằng cách đặt
`custody_group_count` cao hơn, và trong ENR của node cũng bằng cách đặt
`custody_group_count` cao hơn. Giống như custody requirement thông thường, một
node có validator vẫn MAY chọn custody, công bố và phục vụ nhiều hơn mức tối
thiểu này. Cũng giống như custody requirement thông thường, node MUST backfill
(tải bù) các column khi sync.

Node SHOULD tự động điều chỉnh các custody group của mình (không cần người dùng
can thiệp) mỗi khi tổng effective balance của các validator gắn kèm thay đổi.

Nếu custody requirement của node tăng lên, node SHOULD ngay lập tức công bố
`custody_group_count` mới. Node MAY backfill các custody group do thay đổi này.

Nếu custody requirement của node giảm xuống, node SHOULD NOT cập nhật
`custody_group_count` để phản ánh mức giảm đó. Node SHOULD tiếp tục custody và
công bố `custody_group_count` trước đó (cao nhất). Node SHOULD tiếp tục phản hồi
mọi request `DataColumnSidecar` tương ứng với `custody_group_count` trước đó
(cao nhất). Giá trị `custody_group_count` trước đó (cao nhất) SHOULD được lưu
bền vững qua các lần khởi động lại node.

> 💡 Ghi chú: Nói cách khác, `custody_group_count` chỉ tăng chứ không giảm. Điều
> này tránh việc peer khác yêu cầu dữ liệu mà node đã quảng bá là có nhưng sau
> đó lại xóa đi.

Node SHOULD có khả năng xử lý nhiều lần thay đổi custody requirement trong cùng
một retention period (khoảng thời gian lưu giữ dữ liệu), ví dụ tăng ở epoch này
rồi giảm ở epoch kế tiếp.

Khi một giá trị `custody_group_count` được thiết lập, trường
`earliest_available_slot` trong status RPC message SHOULD phản ánh slot mà tại
đó `custody_group_count` được cập nhật.

Nếu node quyết định backfill do thay đổi `custody_group_count`, trường
`earliest_available_slot` trong status RPC message MAY được cập nhật dần với các
giá trị thấp hơn khi quá trình backfill tiến triển.

### Block and sidecar proposal

#### Constructing the `DataColumnSidecar`s

*[New in Fulu:EIP7594]*

Khi propose block, các blob gắn với block được đóng gói thành nhiều đối tượng
`DataColumnSidecar` để phân phối lên sidecar topic tương ứng, tức pubsub topic
`data_column_sidecar_{subnet_id}`. Có thể hình dung một `DataColumnSidecar` như
một lát cắt dọc qua tất cả các blob được xếp chồng lên nhau, kèm theo các trường
bổ sung cung cấp ngữ cảnh cần thiết.

> 💡 Ghi chú: Hãy tưởng tượng một ma trận trong đó mỗi hàng là một blob (đã mở
> rộng) và mỗi cột là một cell index. `DataColumnSidecar` thứ `i` chứa cell thứ
> `i` của mọi blob, cùng proof tương ứng.

##### `get_data_column_sidecars`

Có thể tạo các sidecar gắn với một block bằng cách gọi
[`engine_getPayloadV5`](https://github.com/ethereum/execution-apis/blob/main/src/engine/osaka.md#engine_getpayloadv5),
sau đó dựng danh sách cell và proof cho từng blob (như trong ví dụ bên dưới) từ
blobs bundle trong response, và cuối cùng gọi
`get_data_column_sidecars_from_block(signed_block, cells_and_kzg_proofs)`.

<!-- eth_consensus_specs: skip -->

```python
cells_and_kzg_proofs = []
for i, blob in enumerate(blobs_bundle.blobs):
    start = i * CELLS_PER_EXT_BLOB
    end = (i + 1) * CELLS_PER_EXT_BLOB
    cell_proofs = zip(kzg.compute_cells(blob), blobs_bundle.proofs[start:end], strict=True)
    cells_and_kzg_proofs.extend(cell_proofs)
```

*Lưu ý*: Hàm `kzg.compute_cells` được định nghĩa trong
[cryptography-specs](https://github.com/ethereum/cryptography-specs) với
signature sau:

<!-- eth_consensus_specs: skip -->

```python
def compute_cells(blob: Blob) -> Cells:
    """
    Extend ``blob`` and return all the cells of the extended blob.
    """
```

Ngoài ra, toàn bộ dãy sidecar cũng có thể được tính từ `cells_and_kzg_proofs` và
một `sidecar` bất kỳ bằng cách gọi
`get_data_column_sidecars_from_column_sidecar(sidecar, cells_and_kzg_proofs)`.
Cách này hữu ích trong distributed blob publishing (phát tán blob phân tán), để
dựng lại tất cả sidecar từ bất kỳ sidecar nào nhận được qua mạng, với giả định
là mọi cell và kzg proof đều có thể lấy được từ execution-layer client cục bộ
(ví dụ từ blob mempool).

```python
def get_data_column_sidecars(
    signed_block_header: SignedBeaconBlockHeader,
    kzg_commitments: BlobKZGCommitments,
    kzg_commitments_inclusion_proof: KZGCommitmentsInclusionProof,
    cells_and_kzg_proofs: Sequence[tuple[Cells, Proofs]],
) -> Sequence[DataColumnSidecar]:
    """
    Given a signed block header and the commitments, inclusion proof, cells/proofs associated with
    each blob in the block, assemble the sidecars which can be distributed to peers.
    """
    assert len(cells_and_kzg_proofs) == len(kzg_commitments)

    sidecars = []
    for column_index in range(NUMBER_OF_COLUMNS):
        column_cells = DataColumn()
        column_proofs = KZGProofs()
        for cells, proofs in cells_and_kzg_proofs:
            column_cells.append(cells[column_index])
            column_proofs.append(proofs[column_index])
        sidecars.append(
            DataColumnSidecar(
                index=ColumnIndex(column_index),
                column=column_cells,
                kzg_commitments=kzg_commitments,
                kzg_proofs=column_proofs,
                signed_block_header=signed_block_header,
                kzg_commitments_inclusion_proof=kzg_commitments_inclusion_proof,
            )
        )
    return sidecars
```

##### `get_data_column_sidecars_from_block`

```python
def get_data_column_sidecars_from_block(
    signed_block: SignedBeaconBlock,
    cells_and_kzg_proofs: Sequence[tuple[Cells, Proofs]],
) -> Sequence[DataColumnSidecar]:
    """
    Given a signed block and the cells/proofs associated with each blob in the
    block, assemble the sidecars which can be distributed to peers.
    """
    blob_kzg_commitments = signed_block.message.body.blob_kzg_commitments
    signed_block_header = compute_signed_block_header(signed_block)
    kzg_commitments_inclusion_proof = KZGCommitmentsInclusionProof(
        data=compute_merkle_proof(
            signed_block.message.body,
            get_generalized_index(BeaconBlockBody, "blob_kzg_commitments"),
        )
    )
    return get_data_column_sidecars(
        signed_block_header,
        blob_kzg_commitments,
        kzg_commitments_inclusion_proof,
        cells_and_kzg_proofs,
    )
```

##### `get_data_column_sidecars_from_column_sidecar`

```python
def get_data_column_sidecars_from_column_sidecar(
    sidecar: DataColumnSidecar,
    cells_and_kzg_proofs: Sequence[tuple[Cells, Proofs]],
) -> Sequence[DataColumnSidecar]:
    """
    Given a data column sidecar and the cells/proofs associated with each blob corresponding
    to the commitments it contains, assemble all sidecars for distribution to peers.
    """
    assert len(cells_and_kzg_proofs) == len(sidecar.kzg_commitments)

    return get_data_column_sidecars(
        sidecar.signed_block_header,
        sidecar.kzg_commitments,
        sidecar.kzg_commitments_inclusion_proof,
        cells_and_kzg_proofs,
    )
```

#### Sidecar publishing

`subnet_id` cho `data_column_sidecar` được tính như sau:

- Đặt `column_index = data_column_sidecar.index`.
- Đặt `subnet_id = compute_subnet_for_data_column_sidecar(column_index)`.

Sau khi đã publish tất cả các column lên subnet tương ứng của chúng, các peer
trong mạng có thể yêu cầu sidecar thông qua sync-request, hoặc người dùng cục bộ
cũng có thể cần đến chúng.

#### Sidecar retention

Validator MUST giữ lại các sidecar trong
`MIN_EPOCHS_FOR_DATA_COLUMN_SIDECARS_REQUESTS` epoch và phục vụ chúng khi có
thể, nhằm đảm bảo tính sẵn có của dữ liệu (data availability) của các blob này
trên toàn mạng.

Sau `MIN_EPOCHS_FOR_DATA_COLUMN_SIDECARS_REQUESTS` epoch, node MAY prune (xóa
bớt) các sidecar và/hoặc ngừng phục vụ chúng.
