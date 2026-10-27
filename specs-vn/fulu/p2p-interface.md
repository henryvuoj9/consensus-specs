# Fulu -- Networking

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Presets](#presets)
- [Configs](#configs)
- [Types](#types)
  - [New `DataColumnIndices`](#new-datacolumnindices)
  - [New `DataColumnsByRootIdentifiers`](#new-datacolumnsbyrootidentifiers)
  - [New `DataColumnSidecars`](#new-datacolumnsidecars)
- [Containers](#containers)
  - [New `DataColumnsByRootIdentifier`](#new-datacolumnsbyrootidentifier)
- [Helpers](#helpers)
  - [Modified `Seen`](#modified-seen)
  - [Modified `compute_fork_version`](#modified-compute_fork_version)
  - [New `compute_max_request_data_column_sidecars`](#new-compute_max_request_data_column_sidecars)
  - [New `verify_data_column_sidecar`](#new-verify_data_column_sidecar)
  - [New `verify_data_column_sidecar_kzg_proofs`](#new-verify_data_column_sidecar_kzg_proofs)
  - [New `verify_data_column_sidecar_inclusion_proof`](#new-verify_data_column_sidecar_inclusion_proof)
  - [New `compute_subnet_for_data_column_sidecar`](#new-compute_subnet_for_data_column_sidecar)
- [MetaData](#metadata)
- [The gossip domain: gossipsub](#the-gossip-domain-gossipsub)
  - [Topics and messages](#topics-and-messages)
    - [Global topics](#global-topics)
      - [Modified `beacon_block`](#modified-beacon_block)
    - [Blob subnets](#blob-subnets)
      - [Deprecated `blob_sidecar_{subnet_id}`](#deprecated-blob_sidecar_subnet_id)
      - [New `data_column_sidecar_{subnet_id}`](#new-data_column_sidecar_subnet_id)
      - [Distributed blob publishing using blobs retrieved from local execution-layer client](#distributed-blob-publishing-using-blobs-retrieved-from-local-execution-layer-client)
- [The Req/Resp domain](#the-reqresp-domain)
  - [Messages](#messages)
    - [Status v2](#status-v2)
    - [BlobSidecarsByRange v1](#blobsidecarsbyrange-v1)
    - [BlobSidecarsByRoot v1](#blobsidecarsbyroot-v1)
    - [DataColumnSidecarsByRange v1](#datacolumnsidecarsbyrange-v1)
    - [DataColumnSidecarsByRoot v1](#datacolumnsidecarsbyroot-v1)
    - [GetMetaData v3](#getmetadata-v3)
    - [BeaconBlocksByHead v1](#beaconblocksbyhead-v1)
- [The discovery domain: discv5](#the-discovery-domain-discv5)
  - [ENR structure](#enr-structure)
    - [`eth2` field](#eth2-field)
    - [Custody group count](#custody-group-count)
    - [Next fork digest](#next-fork-digest)
- [Peer scoring](#peer-scoring)
- [Supernodes](#supernodes)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả các đặc tả networking (mạng P2P) của consensus layer cho bản
nâng cấp Fulu.

Các thay đổi được trình bày theo cùng định dạng với các đặc tả networking của
những lần nâng cấp trước, và giả định người đọc đã nắm các tài liệu đó (chúng là
điều kiện tiên quyết). Nói cách khác: tài liệu này chỉ nêu những gì thay đổi;
mọi thứ không được nhắc tới ở đây được kế thừa nguyên vẹn từ các fork trước.

## Presets

| Name                                    | Value                                                                                     | Description                                                       |
| --------------------------------------- | ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `KZG_COMMITMENTS_INCLUSION_PROOF_DEPTH` | `Uint64(floorlog2(get_generalized_index(BeaconBlockBody, "blob_kzg_commitments")))` (= 4) | <!-- predefined --> Chỉ số Merkle proof cho `blob_kzg_commitments` |

## Configs

*[New in Fulu:EIP7594]*

| Name                                           | Value                    | Description                                                           |
| ---------------------------------------------- | ------------------------ | --------------------------------------------------------------------- |
| `DATA_COLUMN_SIDECAR_SUBNET_COUNT`             | `Uint64(2**7)` (= 128)   | Số lượng subnet dành cho data column sidecar trong giao thức gossipsub |
| `MIN_EPOCHS_FOR_DATA_COLUMN_SIDECARS_REQUESTS` | `Epoch(2**12)` (= 4,096) | Khoảng epoch tối thiểu mà một node phải phục vụ (serve) data column sidecar |

## Types

### New `DataColumnIndices`

```python
class DataColumnIndices(List[ColumnIndex]):
    """
    The indices of the data columns being requested.
    """

    LIMIT = NUMBER_OF_COLUMNS
```

### New `DataColumnsByRootIdentifiers`

```python
class DataColumnsByRootIdentifiers(List[DataColumnsByRootIdentifier]):
    """
    The identifiers of the data column sidecars requested in a
    ``DataColumnSidecarsByRoot`` request.
    """

    LIMIT = MAX_REQUEST_BLOCKS_DENEB
```

### New `DataColumnSidecars`

```python
class DataColumnSidecars(List[DataColumnSidecar]):
    """
    Data column sidecars returned in a ``DataColumnSidecarsByRange`` or
    ``DataColumnSidecarsByRoot`` response.
    """

    LIMIT = compute_max_request_data_column_sidecars()
```

## Containers

### New `DataColumnsByRootIdentifier`

```python
class DataColumnsByRootIdentifier(Container):
    block_root: Root
    columns: DataColumnIndices
```

## Helpers

### Modified `Seen`

*(Cấu trúc lưu các message đã thấy trên gossip, dùng để chống trùng lặp/equivocation)*

```python
@dataclass
class Seen:
    proposer_slots: set[tuple[Slot, ValidatorIndex]]
    aggregator_epochs: set[tuple[Epoch, ValidatorIndex]]
    aggregate_data_roots: dict[tuple[Root, CommitteeIndex], set[tuple[bool, ...]]]
    voluntary_exit_indices: set[ValidatorIndex]
    proposer_slashing_indices: set[ValidatorIndex]
    attester_slashing_indices: set[ValidatorIndex]
    attestation_validator_epochs: set[tuple[Epoch, ValidatorIndex]]
    sync_contribution_aggregator_slots: set[tuple[Slot, ValidatorIndex, Uint64]]
    sync_contribution_data: dict[tuple[Slot, Root, Uint64], set[tuple[bool, ...]]]
    sync_message_validator_slots: set[tuple[Slot, ValidatorIndex, Uint64]]
    bls_to_execution_change_indices: set[ValidatorIndex]
    # [Modified in Fulu:EIP7594]
    # Đã loại bỏ `blob_sidecar_tuples`
    # [New in Fulu:EIP7594]
    data_column_sidecar_tuples: set[tuple[Slot, ValidatorIndex, ColumnIndex]]
    # [New in Fulu]
    partial_data_column_headers: dict[Root, PartialDataColumnHeader]
```

### Modified `compute_fork_version`

```python
def compute_fork_version(epoch: Epoch) -> Version:
    """
    Return the fork version at the given ``epoch``.
    """
    if epoch >= FULU_FORK_EPOCH:
        return FULU_FORK_VERSION
    if epoch >= ELECTRA_FORK_EPOCH:
        return ELECTRA_FORK_VERSION
    if epoch >= DENEB_FORK_EPOCH:
        return DENEB_FORK_VERSION
    if epoch >= CAPELLA_FORK_EPOCH:
        return CAPELLA_FORK_VERSION
    if epoch >= BELLATRIX_FORK_EPOCH:
        return BELLATRIX_FORK_VERSION
    if epoch >= ALTAIR_FORK_EPOCH:
        return ALTAIR_FORK_VERSION
    return GENESIS_FORK_VERSION
```

### New `compute_max_request_data_column_sidecars`

```python
def compute_max_request_data_column_sidecars() -> Uint64:
    """
    Return the maximum number of data column sidecars in a single request.
    """
    return MAX_REQUEST_BLOCKS_DENEB * NUMBER_OF_COLUMNS
```

### New `verify_data_column_sidecar`

```python
def verify_data_column_sidecar(sidecar: DataColumnSidecar) -> bool:
    """
    Verify if the data column sidecar is valid.
    """
    # Index của sidecar phải nằm trong khoảng hợp lệ
    if sidecar.index >= NUMBER_OF_COLUMNS:
        return False

    # Sidecar ứng với 0 blob là không hợp lệ
    if len(sidecar.kzg_commitments) == 0:
        return False

    # Kiểm tra sidecar tuân thủ giới hạn số blob
    epoch = compute_epoch_at_slot(sidecar.signed_block_header.message.slot)
    if len(sidecar.kzg_commitments) > get_blob_parameters(epoch).max_blobs_per_block:
        return False

    # Độ dài column phải bằng số commitment
    if len(sidecar.column) != len(sidecar.kzg_commitments):
        return False

    # Độ dài column phải bằng số proof
    if len(sidecar.column) != len(sidecar.kzg_proofs):
        return False

    return True
```

### New `verify_data_column_sidecar_kzg_proofs`

```python
def verify_data_column_sidecar_kzg_proofs(sidecar: DataColumnSidecar) -> bool:
    """
    Verify if the KZG proofs are correct.
    """
    # Column index cũng chính là cell index
    cell_indices = [CellIndex(sidecar.index)] * len(sidecar.column)

    # Kiểm tra theo lô (batch verify) rằng các cell khớp với commitment và proof tương ứng
    return kzg.verify_cell_kzg_proof_batch(
        commitments_bytes=sidecar.kzg_commitments,
        cell_indices=cell_indices,
        cells=sidecar.column,
        proofs_bytes=sidecar.kzg_proofs,
    )
```

*Ghi chú*: Hàm `kzg.verify_cell_kzg_proof_batch` được định nghĩa trong
[cryptography-specs](https://github.com/ethereum/cryptography-specs) với
signature như sau:

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

### New `verify_data_column_sidecar_inclusion_proof`

```python
def verify_data_column_sidecar_inclusion_proof(sidecar: DataColumnSidecar) -> bool:
    """
    Verify if the given KZG commitments included in the given beacon block.
    """
    return is_valid_merkle_branch(
        leaf=hash_tree_root(sidecar.kzg_commitments),
        branch=sidecar.kzg_commitments_inclusion_proof,
        depth=KZG_COMMITMENTS_INCLUSION_PROOF_DEPTH,
        index=get_subtree_index(get_generalized_index(BeaconBlockBody, "blob_kzg_commitments")),
        root=sidecar.signed_block_header.message.body_root,
    )
```

> 💡 Ghi chú: Hàm này chứng minh rằng danh sách `kzg_commitments` trong sidecar
> thực sự nằm trong body của block (thông qua Merkle proof tới `body_root` của
> block header đã được proposer ký), nhờ đó sidecar không thể bị gắn commitment
> giả mạo.

### New `compute_subnet_for_data_column_sidecar`

```python
def compute_subnet_for_data_column_sidecar(column_index: ColumnIndex) -> SubnetID:
    return SubnetID(column_index % DATA_COLUMN_SIDECAR_SUBNET_COUNT)
```

## MetaData

`MetaData` mà client lưu cục bộ được bổ sung thêm một trường để thông báo
custody group count (số custody group mà node đảm nhận lưu giữ).

```
(
  seq_number: Uint64
  attnets: Attnets
  syncnets: Syncnets
  custody_group_count: Uint64 # cgc
)
```

Trong đó

- `seq_number`, `attnets` và `syncnets` có cùng ý nghĩa như được định nghĩa
  trong tài liệu Altair.
- `custody_group_count` là custody group count của node. Client MAY (có thể) từ
  chối các peer có giá trị này nhỏ hơn `CUSTODY_REQUIREMENT`.

## The gossip domain: gossipsub

Một số gossip mesh được nâng cấp trong Fulu để hỗ trợ các kiểu dữ liệu mới.

### Topics and messages

#### Global topics

##### Modified `beacon_block`

*Ghi chú*: Hàm này được sửa đổi theo EIP-7892. Số lượng KZG commitment trong
block bị giới hạn bởi
`get_blob_parameters(compute_epoch_at_slot(block.slot)).max_blobs_per_block`
(tức giới hạn số blob giờ phụ thuộc vào epoch, thay vì một hằng số cố định).

```python
def validate_beacon_block_gossip(
    seen: Seen,
    store: Store,
    signed_beacon_block: SignedBeaconBlock,
    current_time_ms: Uint64,
    block_payload_statuses: dict[Root, PayloadValidationStatus],
) -> None:
    """
    Validate a SignedBeaconBlock for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    block = signed_beacon_block.message
    execution_payload = block.body.execution_payload

    # [IGNORE] Block là block đầu tiên có signature hợp lệ nhận được cho cặp (slot, proposer) này
    proposer_slot_key = (block.slot, block.proposer_index)
    if proposer_slot_key in seen.proposer_slots:
        raise GossipIgnore("block is not the first valid block for this slot and proposer")

    # [IGNORE] Block không thuộc slot trong tương lai
    # (MAY đưa vào hàng đợi để xử lý khi tới đúng slot)
    if is_future_slot(store, block.slot, current_time_ms):
        raise GossipIgnore("block is from a future slot")

    # [IGNORE] Block thuộc slot lớn hơn finalized slot mới nhất
    # (MAY chọn validate và lưu các block như vậy cho mục đích khác
    # -- ví dụ: phát hiện slashing, archive node, v.v.)
    finalized_slot = compute_start_slot_at_epoch(store.finalized_checkpoint.epoch)
    if block.slot <= finalized_slot:
        raise GossipIgnore("block is not from a slot greater than the latest finalized slot")

    # [IGNORE] Block cha đã được thấy (qua gossip hoặc nguồn khác ngoài gossip)
    # (MAY đưa vào hàng đợi cho tới khi lấy được block cha)
    if block.parent_root not in store.blocks:
        raise GossipIgnore("block's parent has not been seen")

    parent_payload_status = PAYLOAD_STATUS_NOT_VALIDATED
    if block.parent_root in block_payload_statuses:
        parent_payload_status = block_payload_statuses[block.parent_root]

    if block.parent_root not in store.block_states:
        if parent_payload_status == PAYLOAD_STATUS_NOT_VALIDATED:
            # [REJECT] Block cha không qua được validation và execution payload của nó là optimistic
            raise GossipReject("block's parent is invalid and its payload is optimistic")

        # [IGNORE] Block cha không qua được validation và execution payload của nó đã được xử lý
        raise GossipIgnore("block's parent is invalid and its payload is processed")

    # [IGNORE] Block cha qua được validation nhưng execution payload của nó không hợp lệ
    if parent_payload_status == PAYLOAD_STATUS_INVALIDATED:
        raise GossipIgnore("block's parent is valid and its payload is invalid")

    state = store.block_states[get_head(store).root]

    # [REJECT] Proposer index là một validator index hợp lệ
    if block.proposer_index >= len(state.validators):
        raise GossipReject("proposer index out of range")

    # [REJECT] Signature của proposer hợp lệ
    proposer = state.validators[block.proposer_index]
    domain = get_domain(state, DOMAIN_BEACON_PROPOSER, compute_epoch_at_slot(block.slot))
    signing_root = compute_signing_root(block, domain)
    if not bls.Verify(proposer.pubkey, signing_root, signed_beacon_block.signature):
        raise GossipReject("invalid proposer signature")

    # [REJECT] Timestamp của execution payload trong block khớp với slot
    if execution_payload.timestamp != compute_time_at_slot(state.genesis_time, block.slot):
        raise GossipReject("incorrect execution payload timestamp")

    # [REJECT] Block thuộc slot cao hơn block cha
    if block.slot <= store.blocks[block.parent_root].slot:
        raise GossipReject("block is not from a higher slot than its parent")

    # [REJECT] Finalized checkpoint hiện tại là tổ tiên (ancestor) của block
    finalized_epoch = store.finalized_checkpoint.epoch
    finalized_checkpoint_block = get_checkpoint_block(store, block.parent_root, finalized_epoch)
    if finalized_checkpoint_block != store.finalized_checkpoint.root:
        raise GossipReject("finalized checkpoint is not an ancestor of block")

    # [Modified in Fulu:EIP7892]
    # [REJECT] Số lượng KZG commitment nhỏ hơn hoặc bằng giới hạn
    max_blobs = get_blob_parameters(compute_epoch_at_slot(block.slot)).max_blobs_per_block
    if len(block.body.blob_kzg_commitments) > max_blobs:
        raise GossipReject("too many blob kzg commitments")

    # [REJECT] Block được đề xuất bởi đúng proposer dự kiến cho slot đó
    # (nếu chưa có shuffling, thay vào đó IGNORE và MAY đưa vào hàng đợi để xử lý sau)
    parent_state = store.block_states[block.parent_root].copy()
    process_slots(parent_state, block.slot)
    expected_proposer = get_beacon_proposer_index(parent_state)
    if block.proposer_index != expected_proposer:
        raise GossipReject("block proposer_index does not match expected proposer")

    # Đánh dấu block này là đã thấy
    seen.proposer_slots.add(proposer_slot_key)
```

#### Blob subnets

##### Deprecated `blob_sidecar_{subnet_id}`

`blob_sidecar_{subnet_id}` bị deprecated (không còn được dùng) kể từ Fulu; blob
giờ được truyền dưới dạng data column thông qua topic mới bên dưới.

##### New `data_column_sidecar_{subnet_id}`

Các topic `data_column_sidecar_{subnet_id}`, trong đó mỗi column index được ánh
xạ tới một `subnet_id` nào đó, được dùng để lan truyền các data column sidecar
mới tới các node trong mạng. Mỗi sidecar được gửi đi nguyên vẹn (không bị chia
nhỏ).

```python
def validate_data_column_sidecar_gossip(
    seen: Seen,
    store: Store,
    sidecar: DataColumnSidecar,
    current_time_ms: Uint64,
    subnet_id: SubnetID,
) -> None:
    """
    Validate a DataColumnSidecar for gossip propagation on a subnet.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    block_header = sidecar.signed_block_header.message

    # [IGNORE] Sidecar là sidecar đầu tiên cho bộ
    # (block_header.slot, block_header.proposer_index, sidecar.index)
    sidecar_key = (block_header.slot, block_header.proposer_index, sidecar.index)
    if sidecar_key in seen.data_column_sidecar_tuples:
        raise GossipIgnore("already seen sidecar from this proposer for this slot and index")

    # [REJECT] Sidecar hợp lệ theo verify_data_column_sidecar
    if not verify_data_column_sidecar(sidecar):
        raise GossipReject("invalid sidecar")

    # [REJECT] Sidecar được gửi trên đúng subnet
    if compute_subnet_for_data_column_sidecar(sidecar.index) != subnet_id:
        raise GossipReject("sidecar is for wrong subnet")

    # [IGNORE] Sidecar không thuộc slot trong tương lai
    # (MAY đưa vào hàng đợi để xử lý khi tới đúng slot)
    if is_future_slot(store, block_header.slot, current_time_ms):
        raise GossipIgnore("sidecar is from a future slot")

    # [IGNORE] Sidecar thuộc slot lớn hơn finalized slot mới nhất
    finalized_slot = compute_start_slot_at_epoch(store.finalized_checkpoint.epoch)
    if block_header.slot <= finalized_slot:
        raise GossipIgnore("sidecar is not from a slot greater than the latest finalized slot")

    # [IGNORE] Block cha của block chứa sidecar đã được thấy
    # (MAY đưa vào hàng đợi để xử lý khi đã lấy được block cha)
    parent_root = block_header.parent_root
    if parent_root not in store.blocks:
        raise GossipIgnore("sidecar's parent has not been seen")

    # [REJECT] Block cha của block chứa sidecar qua được validation
    if parent_root not in store.block_states:
        raise GossipReject("sidecar's parent failed validation")

    state = store.block_states[get_head(store).root]

    # [REJECT] Proposer index là một validator index hợp lệ
    if block_header.proposer_index >= len(state.validators):
        raise GossipReject("proposer index out of range")

    # [REJECT] Signature của proposer trên sidecar.signed_block_header hợp lệ
    proposer = state.validators[block_header.proposer_index]
    domain = get_domain(state, DOMAIN_BEACON_PROPOSER, compute_epoch_at_slot(block_header.slot))
    signing_root = compute_signing_root(block_header, domain)
    if not bls.Verify(proposer.pubkey, signing_root, sidecar.signed_block_header.signature):
        raise GossipReject("invalid proposer signature on sidecar block header")

    # [REJECT] Sidecar thuộc slot cao hơn block cha của block chứa sidecar
    if block_header.slot <= store.blocks[parent_root].slot:
        raise GossipReject("sidecar is not from a higher slot than its parent")

    # [REJECT] finalized_checkpoint hiện tại là tổ tiên (ancestor) của block chứa sidecar
    finalized_epoch = store.finalized_checkpoint.epoch
    finalized_checkpoint_block = get_checkpoint_block(store, parent_root, finalized_epoch)
    if finalized_checkpoint_block != store.finalized_checkpoint.root:
        raise GossipReject("finalized checkpoint is not an ancestor of sidecar's block")

    # [REJECT] Sidecar hợp lệ theo verify_data_column_sidecar_inclusion_proof
    if not verify_data_column_sidecar_inclusion_proof(sidecar):
        raise GossipReject("invalid sidecar inclusion proof")

    # [REJECT] Sidecar hợp lệ theo verify_data_column_sidecar_kzg_proofs
    if not verify_data_column_sidecar_kzg_proofs(sidecar):
        raise GossipReject("invalid sidecar kzg proofs")

    # [REJECT] Sidecar được đề xuất bởi đúng proposer_index dự kiến
    # (nếu chưa có shuffling, thay vào đó IGNORE và MAY đưa vào hàng đợi để xử lý sau)
    parent_state = store.block_states[parent_root].copy()
    process_slots(parent_state, block_header.slot)
    expected_proposer = get_beacon_proposer_index(parent_state)
    if block_header.proposer_index != expected_proposer:
        raise GossipReject("sidecar proposer_index does not match expected proposer")

    # Đánh dấu data column sidecar này là đã thấy
    seen.data_column_sidecar_tuples.add(sidecar_key)
```

*Ghi chú*: Trong bước kiểm tra `verify_data_column_sidecar_inclusion_proof(sidecar)`,
mọi sidecar của cùng một block đều được kiểm tra với cùng một tập
`kzg_commitments` của beacon block đó. Vì vậy client có thể cache kết quả theo bộ
tham số
`(sidecar.kzg_commitments, sidecar.kzg_commitments_inclusion_proof, sidecar.signed_block_header)`
để tránh kiểm tra lặp lại cho từng column.

##### Distributed blob publishing using blobs retrieved from local execution-layer client

*(Phát tán blob theo kiểu phân tán, dùng blob lấy từ execution-layer client cục bộ)*

Các node trung thực SHOULD gọi `engine_getBlobsV2` ngay khi nhận được một
`beacon_block` hoặc `data_column_sidecar` hợp lệ từ gossip. Nếu lấy được TẤT CẢ
các blob khớp với `kzg_commitments`, node nên chuyển đổi kết quả trả về thành các
data column và import kết quả đó.

> 💡 Ghi chú: Blob thường đã có sẵn trong mempool của execution client cục bộ
> (do các blob transaction được lan truyền ở execution layer). Vì vậy node có thể
> tự dựng lại các data column mà không cần chờ nhận từ gossip.

Người triển khai (implementer) được khuyến khích tận dụng cơ chế này để tăng khả
năng import và attest cho block mới nhất trong trường hợp proposer của block đó
không kịp publish các data column đúng hạn.

Khi client dùng execution layer cục bộ để lấy blob, chúng SHOULD bỏ qua bước
verify các blob đó. Khi sau đó import các blob này dưới dạng data column, chúng
MUST hành xử như thể `data_column_sidecar` đã được nhận qua gossip. Cụ thể,
client MUST:

- Publish `data_column_sidecar` tương ứng lên topic
  `data_column_sidecar_{subnet_id}` **khi và chỉ khi** chúng **đã subscribe**
  topic đó, dù là do yêu cầu custody hay do sampling bổ sung.
- Cập nhật các cấu trúc dữ liệu liên quan tới gossip rule (tức là cập nhật cache
  chống equivocation).

## The Req/Resp domain

### Messages

#### Status v2

**Protocol ID:** `/eth2/beacon_chain/req/status/2/`

Nội dung Request và Response:

```
(
  fork_digest: ForkDigest
  finalized_root: Root
  finalized_epoch: Epoch
  head_root: Root
  head_slot: Slot
  # [New in Fulu:EIP7594]
  earliest_available_slot: Slot
)
```

Theo góc nhìn của client tại thời điểm gửi message:

- `earliest_available_slot`: slot của block (`SignedBeaconBlock`) sớm nhất mà
  node hiện có.

*Ghi chú*: Theo định nghĩa của `earliest_available_slot`:

- Nếu node có thể phục vụ toàn bộ block trong suốt khoảng thời gian lưu giữ
  sidecar (retention period, được xác định bởi cả
  `MIN_EPOCHS_FOR_BLOB_SIDECARS_REQUESTS` và
  `MIN_EPOCHS_FOR_DATA_COLUMN_SIDECARS_REQUESTS`), nhưng KHÔNG thể phục vụ toàn
  bộ sidecar trong khoảng đó, thì node nên quảng bá slot sớm nhất mà từ đó nó có
  thể phục vụ toàn bộ sidecar.
- Nếu node có thể phục vụ toàn bộ sidecar trong suốt khoảng thời gian lưu giữ
  sidecar (được xác định bởi cả `MIN_EPOCHS_FOR_BLOB_SIDECARS_REQUESTS` và
  `MIN_EPOCHS_FOR_DATA_COLUMN_SIDECARS_REQUESTS`), thì node nên quảng bá slot
  sớm nhất mà từ đó nó có thể phục vụ toàn bộ block.

> 💡 Ghi chú: Nói cách khác, `earliest_available_slot` là slot sớm nhất mà từ đó
> trở đi node có đầy đủ dữ liệu (cả block lẫn sidecar trong phạm vi retention).
> Peer dựa vào giá trị này để biết có thể yêu cầu dữ liệu nào từ node.

#### BlobSidecarsByRange v1

**Protocol ID:** `/eth2/beacon_chain/req/blob_sidecars_by_range/1/`

Bị deprecated kể từ `FULU_FORK_EPOCH + MIN_EPOCHS_FOR_BLOB_SIDECARS_REQUESTS`.

Trong giai đoạn chuyển tiếp trước khi bị loại bỏ hẳn:

- Client MUST trả về danh sách blob sidecar trong khoảng
  `[min(current_epoch - MIN_EPOCHS_FOR_BLOB_SIDECARS_REQUESTS, FULU_FORK_EPOCH), FULU_FORK_EPOCH)`
  nếu khoảng được yêu cầu có bao gồm bất kỳ epoch nào trong khoảng này.
- Client MAY trả về danh sách rỗng nếu toàn bộ khoảng được yêu cầu nằm tại hoặc
  sau `FULU_FORK_EPOCH`.
- Client SHOULD NOT phạt (penalize) peer vì đã yêu cầu blob sidecar từ
  `FULU_FORK_EPOCH` trở đi.

#### BlobSidecarsByRoot v1

**Protocol ID:** `/eth2/beacon_chain/req/blob_sidecars_by_root/1/`

Bị deprecated kể từ `FULU_FORK_EPOCH + MIN_EPOCHS_FOR_BLOB_SIDECARS_REQUESTS`.

Trong giai đoạn chuyển tiếp trước khi bị loại bỏ hẳn:

- Client MUST trả về các blob sidecar ứng với các block root thuộc khoảng
  `[min(current_epoch - MIN_EPOCHS_FOR_BLOB_SIDECARS_REQUESTS, FULU_FORK_EPOCH), FULU_FORK_EPOCH)`
  nếu bất kỳ root nào được yêu cầu ứng với block trong khoảng này.
- Client MAY trả về danh sách rỗng nếu tất cả các root được yêu cầu đều ứng với
  block tại hoặc sau `FULU_FORK_EPOCH`.
- Client SHOULD NOT phạt (penalize) peer vì đã yêu cầu blob sidecar từ
  `FULU_FORK_EPOCH` trở đi.

#### DataColumnSidecarsByRange v1

**Protocol ID:** `/eth2/beacon_chain/req/data_column_sidecars_by_range/1/`

Nội dung Request:

```
(
  start_slot: Slot
  count: Uint64
  columns: DataColumnIndices
)
```

Nội dung Response:

```
(
  DataColumnSidecars
)
```

Yêu cầu các data column sidecar thuộc các `columns` được chỉ định, trong khoảng
slot `[start_slot, start_slot + count)`, dọc theo chain dẫn tới head block hiện
tại do fork choice lựa chọn.

Trước khi xử lý response chunk tiếp theo, bên đọc response SHOULD kiểm tra rằng
data column sidecar có định dạng đúng (qua `verify_data_column_sidecar`), có
inclusion proof hợp lệ (qua `verify_data_column_sidecar_inclusion_proof`), và
khớp với các KZG commitment mong đợi (qua
`verify_data_column_sidecar_kzg_proofs`).

`DataColumnSidecarsByRange` chủ yếu được dùng để sync các data column có thể đã
bị bỏ lỡ trên gossip, và để sync trong cửa sổ
`MIN_EPOCHS_FOR_DATA_COLUMN_SIDECARS_REQUESTS`.

Request MUST được encode dưới dạng SSZ container.

Response MUST gồm không hoặc nhiều `response_chunk`. Mỗi `response_chunk`
_thành công_ MUST chứa đúng một payload `DataColumnSidecar`.

Đặt `data_column_serve_range` là
`[max(current_epoch - MIN_EPOCHS_FOR_DATA_COLUMN_SIDECARS_REQUESTS, FULU_FORK_EPOCH), current_epoch]`.
Client MUST lưu lại các data column sidecar đã thấy trong khoảng epoch
`data_column_serve_range`, trong đó `current_epoch` được xác định theo thời gian
thực (wall-clock time), và client MUST hỗ trợ phục vụ các request data column
trong khoảng này.

Các peer không thể trả lời request data column sidecar trong khoảng
`data_column_serve_range` SHOULD trả về mã lỗi `3: ResourceUnavailable`. Những
peer không thể trả lời thành công các request trong khoảng này MAY bị hạ điểm
(descore) hoặc bị ngắt kết nối bất cứ lúc nào.

*Ghi chú*: Yêu cầu trên ngụ ý rằng các node khởi động từ một weak subjectivity
checkpoint gần đây MUST backfill (tải bổ sung ngược về quá khứ) cơ sở dữ liệu data
column cục bộ, ít nhất tới hết khoảng `data_column_serve_range`, thì mới tuân thủ
đầy đủ với các request `DataColumnSidecarsByRange`.

*Ghi chú*: Mặc dù client bootstrap từ một weak subjectivity checkpoint có thể bắt
đầu tham gia mạng ngay lập tức, các peer khác MAY ngắt kết nối và/hoặc tạm thời
ban những client chưa sync hoặc mới sync một phần như vậy.

Client MUST trả về ít nhất các data column sidecar của block mang blob đầu tiên
tồn tại trong khoảng được yêu cầu (nếu client có chúng), và không quá
`compute_max_request_data_column_sidecars()` sidecar.

Với mỗi block mà client đưa data column sidecar vào response, client MUST đưa vào
tất cả data column sidecar (được yêu cầu) của block đó.

Các data column sidecar sau đây, nếu tồn tại, MUST được gửi theo thứ tự
`(slot, column_index)`.

Các slot không chứa data column đã biết MUST được bỏ qua, giống hành vi của
request `BlocksByRange`. Do đó chỉ nên gửi các response chunk có data column đã
biết.

Client MAY giới hạn số lượng data column sidecar trong response.

Response MUST chứa không quá `count * NUMBER_OF_COLUMNS` data column sidecar.

Client MUST trả về các data column sidecar theo góc nhìn fork choice hiện tại
của mình -- tức là các data column sidecar thuộc các block nằm trên chain duy
nhất được xác định bởi head hiện tại. Lưu ý rằng các block ở các slot trước
finalization MUST dẫn tới finalized block đã được báo trong handshake `Status`.

Client MUST trả về các data column sidecar nhất quán, thuộc cùng một chain duy
nhất trong phạm vi của request.

Sau data column sidecar đầu tiên, client MAY dừng giữa chừng quá trình trả lời
nếu fork choice của nó thay đổi góc nhìn về chain trong phạm vi request.

Với mỗi `response_chunk` thành công, epoch dùng làm context cho `ForkDigest`
được xác định bởi
`compute_epoch_at_slot(data_column_sidecar.signed_block_header.message.slot)`.

Theo `fork_version = compute_fork_version(epoch)`:

<!-- eth_consensus_specs: skip -->

| `epoch`                     | Chunk SSZ type           |
| --------------------------- | ------------------------ |
| `FULU_FORK_EPOCH` and later | `fulu.DataColumnSidecar` |

#### DataColumnSidecarsByRoot v1

**Protocol ID:** `/eth2/beacon_chain/req/data_column_sidecars_by_root/1/`

*[New in Fulu:EIP7594]*

Nội dung Request:

```
(
  DataColumnsByRootIdentifiers
)
```

Nội dung Response:

```
(
  DataColumnSidecars
)
```

Yêu cầu các data column sidecar theo block root và column index. Response là
một danh sách `DataColumnSidecar` có độ dài nhỏ hơn hoặc bằng
`requested_columns_count`, trong đó
`requested_columns_count = sum(len(r.columns) for r in request)`. Danh sách có
thể ngắn hơn trong trường hợp peer trả lời bị thiếu block hoặc sidecar.

Trước khi xử lý response chunk tiếp theo, bên đọc response SHOULD kiểm tra rằng
data column sidecar có định dạng đúng (qua `verify_data_column_sidecar`), có
inclusion proof hợp lệ (qua `verify_data_column_sidecar_inclusion_proof`), và
khớp với các KZG commitment mong đợi (qua
`verify_data_column_sidecar_kzg_proofs`).

Không được yêu cầu quá `compute_max_request_data_column_sidecars()` sidecar
trong một lần.

Response MUST gồm không hoặc nhiều `response_chunk`. Mỗi `response_chunk`
_thành công_ MUST chứa đúng một payload `DataColumnSidecar`.

Client MUST hỗ trợ request sidecar kể từ `minimum_request_epoch`, trong đó
`minimum_request_epoch = max(current_epoch - MIN_EPOCHS_FOR_DATA_COLUMN_SIDECARS_REQUESTS, FULU_FORK_EPOCH)`.
Nếu bất kỳ root nào trong request trỏ tới block sớm hơn `minimum_request_epoch`,
peer MAY trả về mã lỗi `3: ResourceUnavailable` hoặc không đưa data column
sidecar đó vào response.

Client MUST trả về ít nhất một sidecar, nếu có. Client MAY giới hạn số lượng
block và sidecar trong response.

Client SHOULD đưa một sidecar vào response ngay khi nó qua được các gossip
validation rule. Client SHOULD NOT trả về sidecar thuộc các block không qua được
gossip validation rule. Client SHOULD NOT trả về sidecar thuộc các block không
qua được state transition của beacon chain.

Với mỗi `response_chunk` thành công, epoch dùng làm context cho `ForkDigest`
được xác định bởi
`compute_epoch_at_slot(data_column_sidecar.signed_block_header.message.slot)`.

Theo `fork_version = compute_fork_version(epoch)`:

<!-- eth_consensus_specs: skip -->

| `epoch`                     | Chunk SSZ type           |
| --------------------------- | ------------------------ |
| `FULU_FORK_EPOCH` and later | `fulu.DataColumnSidecar` |

#### GetMetaData v3

**Protocol ID:** `/eth2/beacon_chain/req/metadata/3/`

Không có nội dung Request.

Nội dung Response:

```
(
  MetaData
)
```

Yêu cầu MetaData của một peer, sử dụng định nghĩa `MetaData` mới ở trên (mở rộng
từ Altair). Các điều kiện khác của giao thức `GetMetaData` không thay đổi so với
tài liệu p2p networking của Altair.

#### BeaconBlocksByHead v1

**Protocol ID:** `/eth2/beacon_chain/req/beacon_blocks_by_head/1/`

*[New in Fulu]*

Nội dung Request:

```
(
  beacon_root: Root
  count: Uint64
)
```

Nội dung Response:

```
(
  SignedBeaconBlocks
)
```

Yêu cầu các beacon block dọc theo chuỗi tổ tiên của `beacon_root`, bao gồm cả
block tại `beacon_root`, theo thứ tự slot giảm dần. Quá trình duyệt dừng lại ngay
khi response đã chứa `min(count, MAX_REQUEST_BLOCKS_DENEB)` block, hoặc khi tổ
tiên kế tiếp nằm ngoài khoảng epoch mà client bắt buộc phải phục vụ (xem bên
dưới).

`BeaconBlocksByHead` chủ yếu được dùng để backfill một dải block liên tục tính
từ một head đã biết.

Không được yêu cầu quá `MAX_REQUEST_BLOCKS_DENEB` block trong một lần.

Request MUST được encode dưới dạng SSZ container.

Response MUST gồm không hoặc nhiều `response_chunk`. Mỗi `response_chunk` thành
công MUST chứa đúng một payload `SignedBeaconBlock`.

Client MUST hỗ trợ request block trong khoảng epoch
`[current_epoch - compute_min_epochs_for_block_requests(), current_epoch]`. Nếu
`beacon_root` trỏ tới block sớm hơn khoảng này, peer MAY trả về mã lỗi
`3: ResourceUnavailable` hoặc trả về response không có block nào.

Client MUST trả về ít nhất một block, nếu nó có block tại `beacon_root`. Client
MAY giới hạn số lượng block trong response.

Client SHOULD đưa một block vào response ngay khi nó qua được các gossip
validation rule. Client SHOULD NOT trả về các block không qua được state
transition của beacon chain.

Với mỗi `response_chunk` thành công, epoch dùng làm context cho `ForkDigest`
được xác định bởi `compute_epoch_at_slot(signed_beacon_block.message.slot)`.

Theo `fork_version = compute_fork_version(epoch)`:

<!-- eth_consensus_specs: skip -->

| `fork_version`           | Chunk SSZ type                |
| ------------------------ | ----------------------------- |
| `GENESIS_FORK_VERSION`   | `phase0.SignedBeaconBlock`    |
| `ALTAIR_FORK_VERSION`    | `altair.SignedBeaconBlock`    |
| `BELLATRIX_FORK_VERSION` | `bellatrix.SignedBeaconBlock` |
| `CAPELLA_FORK_VERSION`   | `capella.SignedBeaconBlock`   |
| `DENEB_FORK_VERSION`     | `deneb.SignedBeaconBlock`     |
| `ELECTRA_FORK_VERSION`   | `electra.SignedBeaconBlock`   |
| `FULU_FORK_VERSION`      | `fulu.SignedBeaconBlock`      |
| `GLOAS_FORK_VERSION`     | `gloas.SignedBeaconBlock`     |

## The discovery domain: discv5

### ENR structure

#### `eth2` field

*[Modified in Fulu:EIP7892]*

*Ghi chú*: Cấu trúc của `ENRForkID` không thay đổi, nhưng cách tính giá trị các
trường thì đã thay đổi. Trừ khi được nêu rõ ở đây, mọi đặc tả trong
[phase0/p2p-interface.md#eth2-field](../phase0/p2p-interface.md#eth2-field)
vẫn được giữ nguyên.

ENR MUST mang một key chung `eth2` với giá trị 16 byte, gồm fork digest hiện tại,
next fork version và next fork epoch của node, để đảm bảo kết nối được thiết lập
với các peer trên đúng mạng Ethereum mong muốn.

| Key    | Value       |
| ------ | ----------- |
| `eth2` | `ENRForkID` |

Cụ thể, giá trị của key `eth2` MUST là object được encode SSZ sau đây
(`ENRForkID`):

```
(
  fork_digest: ForkDigest
  next_fork_version: Version
  next_fork_epoch: Epoch
)
```

Các trường của `ENRForkID` được định nghĩa như sau:

- `fork_digest` là
  `compute_fork_digest(genesis_validators_root, current_epoch)`.
- `next_fork_version` là fork version sẽ có hiệu lực tại `next_fork_epoch`:
  bằng `compute_fork_version(current_epoch)` nếu
  `next_fork_epoch == FAR_FUTURE_EPOCH`, ngược lại bằng
  `compute_fork_version(next_fork_epoch)`.
- `next_fork_epoch` là epoch mà tại đó fork tiếp theo (dù là fork thông thường
  _hay BPO fork_) được lên lịch. Nếu không có fork nào được lên lịch trong tương
  lai, đặt `next_fork_epoch = FAR_FUTURE_EPOCH` để báo hiệu điều này.

*Ghi chú*: Trong các định nghĩa trên, `genesis_validators_root` là `Root` tĩnh
nằm trong `state.genesis_validators_root`, còn `current_epoch` là epoch hiện tại
của node tính theo thời gian thực (wall-clock time) — không nhất thiết là epoch
mà node đã sync tới.

*Ghi chú*: Vì `next_fork_epoch` có tính cả BPO fork (Blob-Parameters-Only fork —
fork chỉ thay đổi tham số blob, không đổi fork version), nên có thể xảy ra trường
hợp `next_fork_version` bằng fork version hiện tại dù vẫn có một fork được lên
lịch trong tương lai.

#### Custody group count

Một trường mới được thêm vào ENR với key `cgc` để hỗ trợ việc tìm kiếm (discovery)
peer theo các data column mà chúng custody. Trường mới này MUST được thêm vào ngay
khi `FULU_FORK_EPOCH` được gán bất kỳ giá trị nào khác `FAR_FUTURE_EPOCH`.

| Key   | Value                                                                                                             |
| ----- | ----------------------------------------------------------------------------------------------------------------- |
| `cgc` | Custody group count, số nguyên `Uint64` dạng big endian, không có byte 0 ở đầu (`0` được encode thành chuỗi byte rỗng) |

#### Next fork digest

Một entry mới được thêm vào ENR với key `nfd`, viết tắt của _next fork digest_.
Entry này thông báo digest của fork được lên lịch tiếp theo, bất kể đó là fork
thông thường hay fork Blob-Parameters-Only. Entry mới này MUST được thêm vào ngay
khi `FULU_FORK_EPOCH` được gán bất kỳ giá trị nào khác `FAR_FUTURE_EPOCH`. Việc
thêm entry này trước khi nâng cấp Fulu sẽ không ảnh hưởng tới việc kết nối peer,
vì các node sẽ bỏ qua các entry ENR không biết, và việc `nfd` không khớp cũng
không gây ngắt kết nối.

Nếu không có fork tiếp theo nào được lên lịch, entry `nfd` chứa giá trị mặc định
của kiểu dữ liệu (tức là biểu diễn SSZ của một mảng toàn số 0).

| Key   | Value        |
| ----- | ------------ |
| `nfd` | `ForkDigest` |

Khi tìm kiếm và giao tiếp với peer, node MUST đánh giá `nfd` cùng với việc xem xét
các trường `ENRForkID::next_*` dưới key `eth2` như hiện có, để có cái nhìn chính
xác hơn về fork tiếp theo mà peer dự định theo, phục vụ việc duy trì kết nối lâu
dài. Nếu có sai khác, node MUST NOT ngắt kết nối trước ranh giới fork (fork
boundary), nhưng MAY ngắt kết nối tại hoặc sau ranh giới fork.

Các node chưa sẵn sàng theo bản nâng cấp Fulu sẽ không biết tới entry `nfd`. Tuy
nhiên, việc so sánh entry `eth2` hiện có của chúng (cụ thể là `next_fork_epoch`)
là đủ để phát hiện sự phân tách (divergence) sắp xảy ra.

## Peer scoring

Do các hàm custody là tất định (deterministic), một node biết chính xác một peer
phải có khả năng trả lời những gì. Trong trường hợp peer không trả lời các yêu
cầu sample đối với các row/column mà nó custody, node có thể hạ điểm (downscore)
hoặc ngắt kết nối với peer đó.

## Supernodes

Supernode là node subscribe tất cả các subnet data column sidecar, custody tất cả
data column sidecar, và thực hiện
[reconstruction and cross-seeding](./das-core.md#reconstruction-and-cross-seeding)
(tái tạo dữ liệu và phát lại chéo các column còn thiếu). Làm supernode đòi hỏi
băng thông, dung lượng lưu trữ và tài nguyên tính toán cao hơn đáng kể. Để có thể
tái tạo dữ liệu bị thiếu, trên mạng phải có ít nhất một supernode. Do
[validator custody requirements](./validator.md#validator-custody), một node kết
nối với (các) validator có tổng balance lớn hơn hoặc bằng 4096 ETH bắt buộc phải
là supernode. Ngoài ra, bất kỳ node nào có đủ tài nguyên đều có thể tự nguyện làm
supernode. Vì vậy, dự kiến sẽ có nhiều (hàng trăm) supernode trên mainnet, và
nhiều khả năng (dù không bắt buộc) một node sẽ tình cờ kết nối với một vài
supernode trong số đó.
