# Fulu -- Data Availability Sampling Core

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Types](#types)
  - [`Cell`](#cell)
  - [`CellIndex`](#cellindex)
  - [`Cells`](#cells)
  - [`ColumnIndex`](#columnindex)
  - [`CustodyIndex`](#custodyindex)
  - [`DataColumn`](#datacolumn)
  - [`KZGCommitmentsInclusionProof`](#kzgcommitmentsinclusionproof)
  - [`Proofs`](#proofs)
  - [`RowIndex`](#rowindex)
- [Constants](#constants)
  - [Misc](#misc)
- [Presets](#presets)
  - [Blob](#blob)
  - [Size parameters](#size-parameters)
- [Configs](#configs)
  - [Custody setting](#custody-setting)
- [Containers](#containers)
  - [`DataColumnSidecar`](#datacolumnsidecar)
  - [`MatrixEntry`](#matrixentry)
- [Helpers](#helpers)
  - [`get_custody_groups`](#get_custody_groups)
  - [`compute_columns_for_custody_group`](#compute_columns_for_custody_group)
  - [`compute_matrix`](#compute_matrix)
  - [`recover_matrix`](#recover_matrix)
- [Custody](#custody)
  - [Custody requirement](#custody-requirement)
  - [Public, deterministic selection](#public-deterministic-selection)
- [Custody sampling](#custody-sampling)
- [Extended data](#extended-data)
- [Column gossip](#column-gossip)
  - [Parameters](#parameters)
- [Reconstruction and cross-seeding](#reconstruction-and-cross-seeding)
- [FAQs](#faqs)
  - [Why don't nodes custody rows?](#why-dont-nodes-custody-rows)
  - [Why don't we rotate custody over time?](#why-dont-we-rotate-custody-over-time)
  - [Does having a lot of column subnets make the network unstable?](#does-having-a-lot-of-column-subnets-make-the-network-unstable)

<!-- mdformat-toc end -->

> 💡 Ghi chú: Tài liệu này mô tả phần lõi của PeerDAS (Data Availability
> Sampling — lấy mẫu để kiểm tra tính sẵn có của dữ liệu). Ý tưởng chính: các
> blob trong một block được mở rộng bằng erasure coding và xếp thành một ma trận
> (mỗi hàng là một blob đã mở rộng, mỗi cột gồm các cell cùng vị trí của mọi
> blob). Mỗi node chỉ cần lưu giữ (custody) và lấy mẫu (sampling) một số cột,
> thay vì tải toàn bộ blob.

## Types

### `Cell`

```python
class Cell(ByteVector):
    """
    The unit of extended blob data that has its own ``KZGProof``.
    """

    LENGTH = BYTES_PER_FIELD_ELEMENT * FIELD_ELEMENTS_PER_CELL
```

### `CellIndex`

```python
class CellIndex(Uint64):
    """
    The index of a cell within an extended blob.
    """
```

### `Cells`

```python
class Cells(Vector[Cell]):
    """
    The cells of a single extended blob.
    """

    LENGTH = CELLS_PER_EXT_BLOB
```

### `ColumnIndex`

```python
class ColumnIndex(Uint64):
    """
    The index of a column in the matrix of extended blob data.
    """
```

### `CustodyIndex`

```python
class CustodyIndex(Uint64):
    """
    The index of a custody group.
    """
```

### `DataColumn`

```python
class DataColumn(List[Cell]):
    """
    A column of the extended blob data matrix, with at most one cell per blob.
    """

    LIMIT = MAX_BLOB_COMMITMENTS_PER_BLOCK
```

### `KZGCommitmentsInclusionProof`

```python
class KZGCommitmentsInclusionProof(Vector[Bytes32]):
    """
    A Merkle branch proving a block's blob KZG commitments within
    ``BeaconBlockBody``.
    """

    LENGTH = KZG_COMMITMENTS_INCLUSION_PROOF_DEPTH
```

### `Proofs`

```python
class Proofs(Vector[KZGProof]):
    """
    The KZG proofs for the cells of a single extended blob.
    """

    LENGTH = CELLS_PER_EXT_BLOB
```

### `RowIndex`

```python
class RowIndex(Uint64):
    """
    The index of a row in the matrix of extended blob data.
    """
```

## Constants

Các giá trị sau là hằng số (không thể cấu hình) được dùng xuyên suốt spec.

### Misc

| Name          | Value                 |
| ------------- | --------------------- |
| `UINT256_MAX` | `Uint256(2**256 - 1)` |

## Presets

### Blob

| Name                          | Value                                                    | Description                                                              |
| ----------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------ |
| `FIELD_ELEMENTS_PER_EXT_BLOB` | `2 * FIELD_ELEMENTS_PER_BLOB`                            | Số field element trong một blob đã được mở rộng bằng Reed-Solomon        |
| `FIELD_ELEMENTS_PER_CELL`     | `Uint64(64)`                                             | Số field element trong một cell                                          |
| `CELLS_PER_EXT_BLOB`          | `FIELD_ELEMENTS_PER_EXT_BLOB // FIELD_ELEMENTS_PER_CELL` | Số cell trong một blob đã mở rộng                                        |

### Size parameters

| Name                | Value                                | Description                                    |
| ------------------- | ------------------------------------ | ---------------------------------------------- |
| `NUMBER_OF_COLUMNS` | `Uint64(CELLS_PER_EXT_BLOB)` (= 128) | Số cột trong ma trận dữ liệu đã mở rộng        |

## Configs

### Custody setting

| Name                       | Value         | Description                                                                              |
| -------------------------- | ------------- | ---------------------------------------------------------------------------------------- |
| `SAMPLES_PER_SLOT`         | `Uint64(8)`   | Số mẫu tối thiểu mà một node trung thực phải lấy                                         |
| `NUMBER_OF_CUSTODY_GROUPS` | `Uint64(128)` | Số custody group có sẵn để các node custody                                              |
| `CUSTODY_REQUIREMENT`      | `Uint64(4)`   | Số custody group tối thiểu mà một node trung thực phải custody và phục vụ mẫu từ đó      |

## Containers

### `DataColumnSidecar`

```python
class DataColumnSidecar(Container):
    index: ColumnIndex
    column: DataColumn
    kzg_commitments: BlobKZGCommitments
    kzg_proofs: KZGProofs
    signed_block_header: SignedBeaconBlockHeader
    kzg_commitments_inclusion_proof: KZGCommitmentsInclusionProof
```

> 💡 Ghi chú: Một `DataColumnSidecar` chứa một cột của ma trận (một cell từ mỗi
> blob) cùng KZG proof của từng cell, toàn bộ KZG commitment của các blob, block
> header đã ký và Merkle proof chứng minh các commitment đó nằm trong
> `BeaconBlockBody`. Nhờ vậy sidecar có thể được kiểm tra độc lập mà không cần
> toàn bộ block.

### `MatrixEntry`

```python
class MatrixEntry(Container):
    cell: Cell
    kzg_proof: KZGProof
    column_index: ColumnIndex
    row_index: RowIndex
```

## Helpers

### `get_custody_groups`

> 💡 Ghi chú: Từ `node_id`, hàm lặp lại việc hash `current_id` (tăng dần 1 sau
> mỗi lần) và lấy kết quả modulo `NUMBER_OF_CUSTODY_GROUPS` cho đến khi thu được
> đủ `custody_group_count` group khác nhau. Kết quả được sắp xếp tăng dần.

```python
def get_custody_groups(node_id: NodeID, custody_group_count: Uint64) -> Sequence[CustodyIndex]:
    assert custody_group_count <= NUMBER_OF_CUSTODY_GROUPS

    # Bỏ qua việc tính toán nếu custody tất cả các group
    if custody_group_count == NUMBER_OF_CUSTODY_GROUPS:
        return [CustodyIndex(index) for index in range(NUMBER_OF_CUSTODY_GROUPS)]

    current_id = Uint256(node_id)
    custody_groups: list[CustodyIndex] = []
    while len(custody_groups) < custody_group_count:
        custody_group = CustodyIndex(
            bytes_to_uint64(sha256(uint_to_bytes(current_id))[0:8]) % NUMBER_OF_CUSTODY_GROUPS
        )
        if custody_group not in custody_groups:
            custody_groups.append(custody_group)
        if current_id == UINT256_MAX:
            # Chống tràn số
            current_id = Uint256(0)
        else:
            current_id += 1

    assert len(custody_groups) == len(set(custody_groups))
    return sorted(custody_groups)
```

### `compute_columns_for_custody_group`

```python
def compute_columns_for_custody_group(custody_group: CustodyIndex) -> Sequence[ColumnIndex]:
    assert custody_group < NUMBER_OF_CUSTODY_GROUPS
    columns_per_group = NUMBER_OF_COLUMNS // NUMBER_OF_CUSTODY_GROUPS
    return [
        ColumnIndex(NUMBER_OF_CUSTODY_GROUPS * index + custody_group)
        for index in range(columns_per_group)
    ]
```

### `compute_matrix`

```python
def compute_matrix(blobs: Sequence[Blob]) -> Sequence[MatrixEntry]:
    """
    Return the full, flattened sequence of matrix entries.

    This helper demonstrates the relationship between blobs and the matrix of cells/proofs.
    The data structure for storing cells/proofs is implementation-dependent.
    """
    matrix = []
    for blob_index, blob in enumerate(blobs):
        cells, proofs = kzg.compute_cells_and_kzg_proofs(blob)
        for cell_index, (cell, proof) in enumerate(zip(cells, proofs, strict=True)):
            matrix.append(
                MatrixEntry(
                    cell=cell,
                    kzg_proof=proof,
                    column_index=ColumnIndex(cell_index),
                    row_index=RowIndex(blob_index),
                )
            )
    return matrix
```

*Ghi chú*: Hàm `kzg.compute_cells_and_kzg_proofs` được định nghĩa trong
[cryptography-specs](https://github.com/ethereum/cryptography-specs) với chữ ký
(signature) như sau:

<!-- eth_consensus_specs: skip -->

```python
def compute_cells_and_kzg_proofs(blob: Blob) -> tuple[Cells, Proofs]:
    """
    Extend ``blob`` and return all the cells and proofs of the extended blob.
    """
```

### `recover_matrix`

```python
def recover_matrix(
    partial_matrix: Sequence[MatrixEntry], blob_count: Uint64
) -> Sequence[MatrixEntry]:
    """
    Recover the full, flattened sequence of matrix entries.

    This helper demonstrates how to apply ``kzg.recover_cells_and_kzg_proofs``.
    The data structure for storing cells/proofs is implementation-dependent.
    """
    matrix = []
    for blob_index in range(blob_count):
        cell_indices = [e.column_index for e in partial_matrix if e.row_index == blob_index]
        cells = [e.cell for e in partial_matrix if e.row_index == blob_index]
        recovered_cells, recovered_proofs = kzg.recover_cells_and_kzg_proofs(cell_indices, cells)
        for cell_index, (cell, proof) in enumerate(
            zip(recovered_cells, recovered_proofs, strict=True)
        ):
            matrix.append(
                MatrixEntry(
                    cell=cell,
                    kzg_proof=proof,
                    column_index=ColumnIndex(cell_index),
                    row_index=RowIndex(blob_index),
                )
            )
    return matrix
```

*Ghi chú*: Hàm `kzg.recover_cells_and_kzg_proofs` được định nghĩa trong
[cryptography-specs](https://github.com/ethereum/cryptography-specs) với chữ ký
như sau:

<!-- eth_consensus_specs: skip -->

```python
def recover_cells_and_kzg_proofs(
    cell_indices: Sequence[CellIndex], cells: Sequence[Cell]
) -> tuple[Cells, Proofs]:
    """
    Recover all the cells and proofs of an extended blob given at least half of
    its cells.
    """
```

## Custody

### Custody requirement

Các cột được gom thành các custody group (nhóm lưu giữ). Node custody (lưu giữ
và chịu trách nhiệm phục vụ) một custody group PHẢI (MUST) custody tất cả các cột
trong group đó. Khi sync, node PHẢI (MUST) backfill (tải bù dữ liệu quá khứ) các
cột thuộc tất cả custody group của mình.

Một node *có thể* chọn custody và phục vụ nhiều hơn mức tối thiểu cần thiết của
một node trung thực. Node như vậy công bố rõ ràng một con số lớn hơn
`CUSTODY_REQUIREMENT` thông qua cơ chế peer discovery, cụ thể là đặt giá trị cao
hơn ở trường `custody_group_count` trong ENR của mình. Giá trị này có thể tăng
tới tối đa `NUMBER_OF_CUSTODY_GROUPS`, khi đó node được gọi là super-full node
(node lưu giữ toàn bộ dữ liệu).

Node lưu trữ các cột mình custody trong suốt khoảng thời gian trước khi được
prune (xóa bớt) và trả lời các yêu cầu lấy mẫu từ peer đối với các cột đó.

### Public, deterministic selection

Các cột/group cụ thể mà một node custody được chọn một cách giả ngẫu nhiên, như
một hàm (`get_custody_groups`) của node-id và custody size. Điểm quan trọng là
bất kỳ ai cũng chạy được hàm này, vì mọi đầu vào đều công khai.

> 💡 Ghi chú: Nói cách khác, chỉ cần biết node-id và `custody_group_count` (lấy
> từ ENR) của một peer, ta tính được chính xác peer đó đang giữ những cột nào để
> hỏi đúng chỗ.

*Ghi chú*: Tăng tham số `custody_size` cho một `node_id` cho trước sẽ mở rộng
danh sách trả về (chứ không tạo ra một hoán vị hoàn toàn mới). Nhờ đó, nếu không
biết `custody_size`, giá trị mặc định `CUSTODY_REQUIREMENT` vẫn cho kết quả đúng
với một tập con các group mà node custody.

## Custody sampling

Ở mỗi slot, một node công bố `custody_group_count` sẽ tải tối thiểu
`sampling_size = max(SAMPLES_PER_SLOT, custody_group_count)` custody group,
được chọn bởi `groups = get_custody_groups(node_id, sampling_size)`, tương ứng
với các cột
`compute_columns_for_custody_group(group) for group in groups`. Các custody
group cần custody, được chọn bởi
`get_custody_groups(node_id, custody_group_count)`, do đó là một tập con của các
group cần lấy mẫu. Việc lấy mẫu được coi là thành công nếu node lấy được tất cả
các cột đã chọn.

> 💡 Ghi chú: Ví dụ, với `CUSTODY_REQUIREMENT = 4` và `SAMPLES_PER_SLOT = 8`, một
> node chỉ custody 4 group vẫn phải tải 8 group mỗi slot; 4 group đầu chính là
> các group nó custody (nhờ tính chất "mở rộng danh sách" ở trên).

## Extended data

Trong cách xây dựng này, chúng ta mở rộng các blob bằng erasure coding một chiều.
Ma trận gồm tối đa `MAX_BLOBS_PER_BLOCK` hàng và cố định `NUMBER_OF_COLUMNS`
cột, trong đó mỗi hàng chứa một `Blob` cùng phần mở rộng tương ứng của nó.
`compute_matrix` minh họa mối quan hệ giữa các blob và ma trận, đồng thời là một
cách có thể dùng để lưu trữ cell/proof.

> 💡 Ghi chú: Vì là mã Reed-Solomon với hệ số mở rộng 2, chỉ cần có bất kỳ 50%
> số cell của một hàng là khôi phục được toàn bộ hàng (tức là blob gốc).

## Column gossip

### Parameters

Các mẫu có thể kiểm chứng của từng cột được phân phối trên subnet được gán cho
cột đó. Để custody các cột thuộc một custody group cụ thể, node tham gia các
gossipsub subnet tương ứng. Nếu node không nhận được cột trên các column subnet,
node cũng có thể dùng giao thức Req/Resp để hỏi các cột còn thiếu từ peer khác.

## Reconstruction and cross-seeding

Nếu node có được từ 50% trở lên tổng số cột, nó NÊN (SHOULD) tái tạo
(reconstruct) toàn bộ ma trận dữ liệu bằng helper `recover_matrix`. Node CÓ THỂ
(MAY) trì hoãn việc tái tạo để chờ các cột khác đến qua mạng. Nếu trì hoãn, node
có thể dùng một độ trễ ngẫu nhiên để các node không cùng tái tạo một lúc, qua đó
giảm tổng tải CPU.

Khi node có được một cột qua việc tái tạo, node PHẢI (MUST) công bố cột mới đó
như thể đã nhận được nó qua mạng. Nếu node đang subscribe subnet tương ứng với
cột, nó PHẢI (MUST) gửi `DataColumnSidecar` đã tái tạo tới các peer láng giềng
trong mesh của topic. Nếu node không subscribe subnet tương ứng, nó vẫn NÊN
(SHOULD) công bố việc mình có `DataColumnSidecar` đó như một phần của quá trình
phát gossip (gossip emission). Sau khi đã công bố `DataColumnSidecar` tái tạo
cho mạng, node CÓ THỂ (MAY) xóa `DataColumnSidecar` đó nếu nó không thuộc yêu
cầu custody của node.

> 💡 Ghi chú: "Cross-seeding" ở đây nghĩa là node dùng dữ liệu đã tái tạo để
> bơm ngược các cột còn thiếu vào mạng, giúp các node khác cũng có đủ dữ liệu.

*Ghi chú*: Node luôn duy trì một góc nhìn dạng ma trận về các hàng và cột mà nó
đang theo dõi, nhờ đó có thể đối chiếu chéo và cross-seed theo cả hai chiều.

*Ghi chú*: Còn các vấn đề về thời gian cần phân tích -- tại thời điểm nào node
coi các mẫu là bị thiếu và quyết định tái tạo và cross-seed.

*Ghi chú*: Có thể có các cân nhắc về chống DoS và chất lượng dịch vụ liên quan
đến cách gửi và xử lý các mẫu -- mỗi mẫu là một message riêng hay chúng được gửi
dưới dạng gộp.

## FAQs

### Why don't nodes custody rows?

*(Tại sao node không custody theo hàng?)*

Trong cách xây dựng một chiều, node lấy mẫu từ peer bằng cách yêu cầu toàn bộ
`DataColumnSidecar`. Khi tái tạo, node có thể tái tạo toàn bộ các blob từ 50%
số cột. Lưu ý rằng node vẫn có thể tải về một hàng qua các subnet
`blob_sidecar_{subnet_id}`.

Những lợi ích tiềm năng của việc custody theo hàng có thể gồm:

1. Cho phép phân phối dữ liệu "tự nhiên" hơn tới bên sử dụng -- ví dụ các
   roll-up -- nhưng thực tế họ sẽ không biết trước blob của mình sẽ nằm ở hàng
   nào trong block, nên họ hoặc phải lắng nghe tất cả các hàng, hoặc phải tải
   một hàng cụ thể sau khi thấy block. Cách thứ nhất không khác gì lắng nghe các
   cột \[0, N), còn cách thứ hai là dùng req/resp thay vì gossip.
2. Hỗ trợ một dạng tái tạo phân tán. Những node có đủ hàng có thể tính phần mở
   rộng và seed các mẫu còn thiếu vào mạng. Điều này sẽ đòi hỏi hoặc khả năng gửi
   từng điểm riêng lẻ qua gossip, hoặc một cơ chế req/resp nào đó, có thể tương
   tự `IHAVEPOINTBITFIELD` và `IWANTSAMPLE`.

Tuy nhiên, để đơn giản, thiết kế hiện tại không gán custody theo hàng cho các
node.

### Why don't we rotate custody over time?

*(Tại sao không luân chuyển custody theo thời gian?)*

Để bắt đầu với một nền tảng (backbone) đơn giản và ổn định, hiện tại chúng ta
không xáo trộn việc phân công custody thông qua helper chọn custody tất định
`get_custody_groups`. Tuy nhiên, việc luân chuyển so le (staggered rotation)
nhiều khả năng sẽ cần diễn ra với chu kỳ cỡ khoảng thời gian prune, để đảm bảo
các subnet vẫn dùng được cho việc khôi phục. Ví dụ, thêm một tham số `epoch` cho
phép hàm giữ ổn định qua nhiều epoch.

### Does having a lot of column subnets make the network unstable?

*(Có nhiều column subnet có làm mạng mất ổn định không?)*

Không, số lượng subnet thực ra không quan trọng. Điều quan trọng với độ ổn định
của mạng là số lượng node và tốc độ biến động (churn rate) của mạng. Nếu số node
quá ít, khi một số node ngừng hoạt động thì dễ xảy ra phân mảnh mạng (network
partition). Về churn rate, nếu churn rate cao, ta thậm chí còn cần số node nhiều
hơn, vì các node có khả năng bị tắt thường xuyên hơn.
