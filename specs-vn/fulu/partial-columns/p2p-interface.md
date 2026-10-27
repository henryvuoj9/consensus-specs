# Fulu Partial Columns -- Networking

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Types](#types)
  - [New `CellsBitList`](#new-cellsbitlist)
  - [New `OptionalPartialDataColumnHeader`](#new-optionalpartialdatacolumnheader)
- [Containers](#containers)
  - [New `PartialDataColumnSidecar`](#new-partialdatacolumnsidecar)
  - [New `PartialDataColumnPartsMetadata`](#new-partialdatacolumnpartsmetadata)
  - [New `PartialDataColumnHeader`](#new-partialdatacolumnheader)
  - [New `PartialDataColumnGroupID`](#new-partialdatacolumngroupid)
- [Helpers](#helpers)
  - [New `verify_partial_data_column_header_inclusion_proof`](#new-verify_partial_data_column_header_inclusion_proof)
  - [New `verify_partial_data_column_sidecar_kzg_proofs`](#new-verify_partial_data_column_sidecar_kzg_proofs)
- [The gossip domain: gossipsub](#the-gossip-domain-gossipsub)
  - [Blob subnets](#blob-subnets)
    - [New `data_column_sidecar_{subnet_id}` (partial messages)](#new-data_column_sidecar_subnet_id-partial-messages)
  - [Partial columns for Cell Dissemination](#partial-columns-for-cell-dissemination)
    - [Partial message group ID](#partial-message-group-id)
    - [Parts metadata](#parts-metadata)
    - [Encoding and decoding responses](#encoding-and-decoding-responses)
    - [Eager pushing](#eager-pushing)
    - [Interaction with standard gossipsub](#interaction-with-standard-gossipsub)
      - [Requesting partial messages](#requesting-partial-messages)
      - [Mesh](#mesh)
      - [Fanout](#fanout)
      - [Scoring](#scoring)
      - [Forwarding](#forwarding)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này đặc tả cách các data column được phát tán dưới dạng *partial
column* (cột từng phần) trong Fulu, sử dụng
[Partial Message Extension](https://github.com/libp2p/specs/pull/685) của
gossipsub để trao đổi từng cell riêng lẻ cùng với proof của chúng.

Đặc tả các thay đổi này tiếp nối cùng định dạng với các network spec của những
lần nâng cấp trước, và coi chúng là điều kiện tiên quyết. Cụ thể, tài liệu này
được xây dựng dựa trên
[Fulu networking specification](../p2p-interface.md).

> 💡 Ghi chú: Thay vì luôn gửi nguyên một `DataColumnSidecar` (toàn bộ cell của
> một cột cho mọi blob trong block), node có thể chỉ gửi/nhận những cell mà
> peer còn thiếu. Điều này giảm băng thông và độ trễ, đặc biệt khi nhiều node đã
> có sẵn phần lớn blob trong mempool của mình.

## Types

### New `CellsBitList`

```python
class CellsBitList(BitList):
    """
    A bitfield over the cells of a column, one bit per blob.
    """

    LIMIT = MAX_BLOB_COMMITMENTS_PER_BLOCK
```

### New `OptionalPartialDataColumnHeader`

```python
class OptionalPartialDataColumnHeader(List[PartialDataColumnHeader]):
    """
    A header that may or may not be present, encoded as a list of length zero
    or one.
    """

    LIMIT = 1
```

## Containers

### New `PartialDataColumnSidecar`

`PartialDataColumnSidecar` tương tự container `DataColumnSidecar`, chỉ khác là
nó chỉ chứa những cell và proof được đánh dấu trong bitmap.

*Lưu ý*: Column index được suy ra từ subnet của gossipsub topic (nên không cần
nằm trong container).

```python
class PartialDataColumnSidecar(Container):
    cells_present_bitmap: CellsBitList
    partial_column: DataColumn
    kzg_proofs: KZGProofs
    # Header tùy chọn, chỉ được gửi khi eager push
    header: OptionalPartialDataColumnHeader
```

### New `PartialDataColumnPartsMetadata`

Các peer thông báo cho nhau những cell mình đang có bằng một bitmap. Một bit
được bật (`1`) tại index `i` nghĩa là peer có cell tại index `i`. Các peer yêu
cầu cell một cách tường minh bằng một bitmap thứ hai (bitmap request) có cùng
độ dài, trong đó bit được đặt là `1` nếu peer muốn nhận hoặc cung cấp cell đó.

Nếu một cell có sẵn thì proof tương ứng của nó MUST cũng có sẵn.

Dữ liệu này được mã hóa bằng SSZ container sau:

```python
class PartialDataColumnPartsMetadata(Container):
    available: CellsBitList
    requests: CellsBitList
```

Như vậy, với mỗi cell có hai bit trạng thái: bit thứ nhất lấy từ bitlist
`available`, bit thứ hai lấy từ bitlist `requests`.

| Bits | Description                                          |
| ---- | ---------------------------------------------------- |
| 00   | Peer không có cell và cũng không muốn nhận nó        |
| 01   | Peer không có cell và muốn nhận nó                   |
| 1X   | Peer có cell và sẵn sàng cung cấp nó                 |

Việc có cell nhưng không sẵn lòng cung cấp về mặt chức năng tương đương với
việc không có cell và không muốn nhận nó, nên không cần một trạng thái riêng.

### New `PartialDataColumnHeader`

`PartialDataColumnHeader` là phần header chung cho mọi column của một block cụ
thể. Nó cho phép peer xác định những blob nào được đưa vào block, đồng thời dùng
để xác thực các cell và proof. Header này chỉ được gửi khi eager push (đẩy chủ
động), vì một peer chỉ có thể gửi request sau khi đã có dữ liệu trong header
này. Header có thể được suy ra từ một beacon block hoặc từ một
`DataColumnSidecar`.

```python
class PartialDataColumnHeader(Container):
    kzg_commitments: BlobKZGCommitments
    signed_block_header: SignedBeaconBlockHeader
    kzg_commitments_inclusion_proof: KZGCommitmentsInclusionProof
```

### New `PartialDataColumnGroupID`

```python
class PartialDataColumnGroupID(Container):
    beacon_block_root: Root
```

## Helpers

### New `verify_partial_data_column_header_inclusion_proof`

```python
def verify_partial_data_column_header_inclusion_proof(header: PartialDataColumnHeader) -> bool:
    """
    Verify if the given KZG commitments are included in the given beacon block.
    """
    return is_valid_merkle_branch(
        leaf=hash_tree_root(header.kzg_commitments),
        branch=header.kzg_commitments_inclusion_proof,
        depth=KZG_COMMITMENTS_INCLUSION_PROOF_DEPTH,
        index=get_subtree_index(get_generalized_index(BeaconBlockBody, "blob_kzg_commitments")),
        root=header.signed_block_header.message.body_root,
    )
```

### New `verify_partial_data_column_sidecar_kzg_proofs`

```python
def verify_partial_data_column_sidecar_kzg_proofs(
    sidecar: PartialDataColumnSidecar,
    all_commitments: BlobKZGCommitments,
    column_index: ColumnIndex,
) -> bool:
    """
    Verify the KZG proofs.
    """
    # Lấy các blob index từ bitmap
    blob_indices = [index for index, bit in enumerate(sidecar.cells_present_bitmap) if bit]

    # Cell index chính là column index với mọi cell trong column này
    cell_indices = [CellIndex(column_index)] * len(blob_indices)

    # Batch verify rằng các cell khớp với commitment và proof tương ứng
    return kzg.verify_cell_kzg_proof_batch(
        commitments_bytes=[all_commitments[index] for index in blob_indices],
        cell_indices=cell_indices,
        cells=sidecar.partial_column,
        proofs_bytes=sidecar.kzg_proofs,
    )
```

*Lưu ý*: Hàm `kzg.verify_cell_kzg_proof_batch` được định nghĩa trong
[cryptography-specs](https://github.com/ethereum/cryptography-specs) với
signature sau:

<!-- eth_consensus_specs: skip -->

```python
def verify_cell_kzg_proof_batch(
    commitments_bytes: Sequence[Bytes48],
    cell_indices: Sequence[CellIndex],
    cells: Sequence[Cell],
    proofs_bytes: Sequence[Bytes48],
) -> bool:
    """
    Return ``True`` if and only if all cells and their proofs match the
    commitments.
    """
```

## The gossip domain: gossipsub

### Blob subnets

#### New `data_column_sidecar_{subnet_id}` (partial messages)

*Lưu ý*: Việc xác thực partial message diễn ra theo hai phần. Trước tiên cần
xác thực `PartialDataColumnHeader`, sau đó mới đến dữ liệu cell và proof. Một
khi `PartialDataColumnHeader` của một block đã được xác thực trên bất kỳ subnet
nào (gossipsub topic), nó có thể được dùng lại cho mọi subnet. Do bản chất của
partial message, hoàn toàn có thể nhận được `PartialDataColumnHeader` mà không
kèm cell nào, rồi nhận các cell trong một response sau đó.

*Lưu ý*: Partial Message Group ID là `PartialDataColumnGroupID` đã được mã hóa
SSZ, có thêm tiền tố là version byte `0x00`. Các implementation MUST bỏ qua các
version không xác định.

*Lưu ý*: Điều kiện kiểm tra tùy chọn "với những cell mà bên nhận đã có, dữ liệu
cell và proof trong sidecar phải bằng với bản sao cục bộ" không được mã hóa
trong code bên dưới. Bên gửi MUST luôn gửi dữ liệu cell và proof hợp lệ; bên
nhận MAY thực hiện phép so sánh bằng này với bản sao cục bộ như một lớp bảo vệ
bổ sung.

> 💡 Ghi chú: Trong hàm dưới đây, `GossipReject` tương ứng với [REJECT] (message
> không hợp lệ, peer gửi có thể bị trừ điểm), còn `GossipIgnore` tương ứng với
> [IGNORE] (bỏ qua message, không phạt peer — thường vì node chưa đủ thông tin để
> quyết định).

```python
def validate_partial_data_column_sidecar_gossip(
    seen: Seen,
    store: Store,
    sidecar: PartialDataColumnSidecar,
    current_time_ms: Uint64,
    group_id: PartialDataColumnGroupID,
    column_index: ColumnIndex,
) -> None:
    """
    Validate a PartialDataColumnSidecar for gossip propagation on a subnet.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    has_header = len(sidecar.header) == 1
    num_cells_present = get_set_bit_count(sidecar.cells_present_bitmap)
    has_cells = num_cells_present > 0

    # [REJECT] Message có chứa header và/hoặc cell
    if not (has_header or has_cells):
        raise GossipReject("partial message is semantically empty")

    # [REJECT] Số lượng cell bằng số bit được bật trong bitmap
    if len(sidecar.partial_column) != num_cells_present:
        raise GossipReject("number of cells does not match number of set bits")

    # [REJECT] Số lượng proof bằng số bit được bật trong bitmap
    if len(sidecar.kzg_proofs) != num_cells_present:
        raise GossipReject("number of proofs does not match number of set bits")

    if has_header:
        header = sidecar.header[0]
        block_header = header.signed_block_header.message

        # [REJECT] Header nhận được MUST bằng mọi header đã được xác thực trước đó cho block này
        prior_header = seen.partial_data_column_headers.get(group_id.beacon_block_root)
        if prior_header is not None and prior_header != header:
            raise GossipReject("header differs from previously validated header")

        # [REJECT] Hash của signed_block_header khớp với group id của partial message
        if hash_tree_root(block_header) != group_id.beacon_block_root:
            raise GossipReject("header's block root does not match group id's block root")

        # [REJECT] Danh sách kzg_commitments của header không rỗng
        if len(header.kzg_commitments) == 0:
            raise GossipReject("header's kzg_commitments is empty")

        # [IGNORE] Header không thuộc một slot trong tương lai
        # (MAY được đưa vào hàng đợi để xử lý khi đến slot tương ứng)
        if is_future_slot(store, block_header.slot, current_time_ms):
            raise GossipIgnore("header is from a future slot")

        # [IGNORE] Header thuộc slot lớn hơn slot finalized gần nhất
        finalized_slot = compute_start_slot_at_epoch(store.finalized_checkpoint.epoch)
        if block_header.slot <= finalized_slot:
            raise GossipIgnore("header is not from a slot greater than the latest finalized slot")

        # [IGNORE] Block cha của block trong header đã được thấy
        # (MAY được đưa vào hàng đợi để xử lý khi đã lấy được block cha)
        parent_root = block_header.parent_root
        if parent_root not in store.blocks:
            raise GossipIgnore("header's parent has not been seen")

        # [REJECT] Block cha của block trong header vượt qua xác thực
        if parent_root not in store.block_states:
            raise GossipReject("header's parent failed validation")

        state = store.block_states[get_head(store).root]

        # [REJECT] Proposer index là một validator index hợp lệ
        if block_header.proposer_index >= len(state.validators):
            raise GossipReject("proposer index out of range")

        # [REJECT] Chữ ký của proposer trên signed_block_header hợp lệ
        proposer = state.validators[block_header.proposer_index]
        domain = get_domain(state, DOMAIN_BEACON_PROPOSER, compute_epoch_at_slot(block_header.slot))
        signing_root = compute_signing_root(block_header, domain)
        if not bls.Verify(proposer.pubkey, signing_root, header.signed_block_header.signature):
            raise GossipReject("invalid proposer signature on header")

        # [REJECT] Header thuộc slot cao hơn slot của block cha
        if block_header.slot <= store.blocks[parent_root].slot:
            raise GossipReject("header is not from a higher slot than its parent")

        # [REJECT] finalized_checkpoint hiện tại là tổ tiên của block trong header
        finalized_epoch = store.finalized_checkpoint.epoch
        finalized_checkpoint_block = get_checkpoint_block(store, parent_root, finalized_epoch)
        if finalized_checkpoint_block != store.finalized_checkpoint.root:
            raise GossipReject("finalized checkpoint is not an ancestor of header's block")

        # [REJECT] Inclusion proof cho kzg_commitments của header hợp lệ
        if not verify_partial_data_column_header_inclusion_proof(header):
            raise GossipReject("invalid header inclusion proof")

        # [REJECT] Header được đề xuất bởi đúng proposer_index mong đợi
        # (nếu chưa có shuffling, thì IGNORE thay vì REJECT và MAY đưa vào hàng đợi để xử lý sau)
        parent_state = store.block_states[parent_root].copy()
        process_slots(parent_state, block_header.slot)
        expected_proposer = get_beacon_proposer_index(parent_state)
        if block_header.proposer_index != expected_proposer:
            raise GossipReject("header proposer_index does not match expected proposer")

        # Đánh dấu header này là đã thấy
        seen.partial_data_column_headers[group_id.beacon_block_root] = header

    if has_cells:
        # [IGNORE] Đã thấy một PartialDataColumnHeader hợp lệ tương ứng
        header = seen.partial_data_column_headers.get(group_id.beacon_block_root)
        if header is None:
            raise GossipIgnore("valid corresponding header has not been seen")

        block_header = header.signed_block_header.message

        # [IGNORE] Header tương ứng không thuộc một slot trong tương lai
        # (MAY được đưa vào hàng đợi để xử lý khi đến slot tương ứng)
        if is_future_slot(store, block_header.slot, current_time_ms):
            raise GossipIgnore("corresponding header is from a future slot")

        # [IGNORE] Header tương ứng thuộc slot lớn hơn slot finalized gần nhất
        finalized_slot = compute_start_slot_at_epoch(store.finalized_checkpoint.epoch)
        if block_header.slot <= finalized_slot:
            raise GossipIgnore(
                "corresponding header is not from a slot greater than the latest finalized slot"
            )

        # [REJECT] Độ dài bitmap cells_present bằng số commitment trong header
        if len(sidecar.cells_present_bitmap) != len(header.kzg_commitments):
            raise GossipReject("bitmap length does not match commitments length")

        # [REJECT] Dữ liệu cell và proof của sidecar vượt qua KZG verification
        if not verify_partial_data_column_sidecar_kzg_proofs(
            sidecar, header.kzg_commitments, column_index
        ):
            raise GossipReject("invalid sidecar kzg proofs")
```

### Partial columns for Cell Dissemination

[Partial Message Extension](https://github.com/libp2p/specs/pull/685) của
gossipsub cho phép trao đổi một số phần được chọn của message thay vì toàn bộ
message. Đặc tả ở đây mô tả cách các client tầng consensus sử dụng Partial
Message để phát tán các cell cùng với proof của chúng.

#### Partial message group ID

Khi gửi một partial message, gossipsub group ID MUST là
`PartialDataColumnGroupID` đã mã hóa SSZ, có thêm tiền tố là một version byte.
Version byte MUST là `0x00`. Các implementation MUST bỏ qua các version không
xác định. Các version khác có thể được định nghĩa sau này.

#### Parts metadata

Parts metadata được mã hóa bằng container `PartialDataColumnPartsMetadata`.

#### Encoding and decoding responses

Mọi response MUST được mã hóa và giải mã bằng container
`PartialDataColumnSidecar`.

#### Eager pushing

Khác với gossipsub tiêu chuẩn, ở đây client yêu cầu tường minh những phần còn
thiếu từ một peer. Client có thể gửi request trước cả khi nhận được parts
metadata của peer. Việc này giúp đăng ký nhu cầu với một số phần nhất định, kể
cả khi peer chưa có những phần đó.

Bước request này có thể làm tăng thêm độ trễ so với việc peer đẩy message vô
điều kiện, đặc biệt ở hop đầu tiên của quá trình phát tán.

Để cân bằng sự đánh đổi này, client MAY chọn eager push (chủ động đẩy) một số
(hoặc toàn bộ) cell mà nó có. Client SHOULD chỉ làm vậy khi khá chắc chắn rằng
peer chưa có các cell được gửi. Ví dụ, một proposer đưa vào block các blob
private (không được phát tán qua mempool công khai) SHOULD eager push các cell
tương ứng với các blob private đó.

Mặc định, client SHOULD NOT eager push cell khi propose một block. Client
SHOULD cung cấp một flag để người vận hành có thể chủ động bật (opt-in) việc
eager push toàn bộ cell khi propose block.

Client SHOULD eager push `PartialDataColumnHeader` để báo cho peer biết những
blob nào được đưa vào block này, và do đó họ đang thiếu những cell nào. Client
SHOULD NOT gửi `PartialDataColumnHeader` tới một peer đã từng gửi message cho
client, vì peer đó chắc chắn đã có header (có header là điều kiện tiên quyết để
gửi message).

Client MAY chọn không eager push `PartialDataColumnHeader` nếu trước đó đã gửi
header cho peer đó trên một topic khác.

Client SHOULD request cell từ các peer sau khi đã xác thực một
`PartialDataColumnHeader`, kể cả khi chưa thấy block tương ứng.

#### Interaction with standard gossipsub

##### Requesting partial messages

Một peer yêu cầu nhận partial message cho một topic bằng cách đặt trường
`partial` trong RPC message `SubOpts` của gossipsub thành `true`.

##### Mesh

Partial Message Extension dùng cùng tập mesh peer cho một topic như các
gossipsub topic tiêu chuẩn dành cho `DataColumnSidecar`.

##### Fanout

Partial Message Extension dùng cùng tập fanout peer cho một topic như các
gossipsub topic tiêu chuẩn dành cho `DataColumnSidecar`.

##### Scoring

Khi nhận được dữ liệu mới và hữu ích từ một peer, client nên báo cho gossipsub
một sự kiện first message delivery tích cực (để cộng điểm cho peer).

Client SHOULD giới hạn tần suất một peer nhận được phần thưởng first message
delivery, để tránh trường hợp peer đạt điểm cao hơn chỉ bằng cách cung cấp từng
cell một thay vì nhiều cell cùng lúc.

Khi nhận được dữ liệu không hợp lệ, client nên báo cho gossipsub một sự kiện
invalid message delivery.

##### Forwarding

Khi client có thể dựng lại được `DataColumnSidecar` đầy đủ sau khi nhận được
các cell còn thiếu, nó nên forward `DataColumnSidecar` đầy đủ qua gossipsub
tiêu chuẩn tới những peer không hỗ trợ partial message. Điều này đảm bảo tương
thích ngược với các node chưa hỗ trợ partial message.

Tránh forward toàn bộ message `DataColumnSidecar` tới những peer đã yêu cầu
partial message cho topic đó. Việc này chỉ tạo ra thông tin dư thừa.
