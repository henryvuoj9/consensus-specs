# Deneb -- Networking

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Presets](#presets)
- [Configs](#configs)
- [Types](#types)
  - [Modified `BeaconBlockRoots`](#modified-beaconblockroots)
  - [Modified `SignedBeaconBlocks`](#modified-signedbeaconblocks)
  - [New `BlobIdentifiers`](#new-blobidentifiers)
  - [New `BlobSidecars`](#new-blobsidecars)
  - [New `KZGCommitmentInclusionProof`](#new-kzgcommitmentinclusionproof)
- [Containers](#containers)
  - [New `BlobSidecar`](#new-blobsidecar)
  - [New `BlobIdentifier`](#new-blobidentifier)
- [Helpers](#helpers)
  - [Modified `Seen`](#modified-seen)
  - [Modified `compute_fork_version`](#modified-compute_fork_version)
  - [New `is_within_epoch`](#new-is_within_epoch)
  - [New `is_current_or_previous_epoch`](#new-is_current_or_previous_epoch)
  - [New `compute_max_request_blob_sidecars`](#new-compute_max_request_blob_sidecars)
  - [New `verify_blob_sidecar_inclusion_proof`](#new-verify_blob_sidecar_inclusion_proof)
- [The gossip domain: gossipsub](#the-gossip-domain-gossipsub)
  - [Topics and messages](#topics-and-messages)
    - [Global topics](#global-topics)
      - [Modified `beacon_block`](#modified-beacon_block)
      - [Modified `beacon_aggregate_and_proof`](#modified-beacon_aggregate_and_proof)
      - [Modified `voluntary_exit`](#modified-voluntary_exit)
    - [Attestation subnets](#attestation-subnets)
      - [Modified `beacon_attestation_{subnet_id}`](#modified-beacon_attestation_subnet_id)
    - [Blob subnets](#blob-subnets)
      - [New `blob_sidecar_{subnet_id}`](#new-blob_sidecar_subnet_id)
      - [Blob retrieval via local execution-layer client](#blob-retrieval-via-local-execution-layer-client)
  - [Transitioning the gossip](#transitioning-the-gossip)
- [The Req/Resp domain](#the-reqresp-domain)
  - [Messages](#messages)
    - [BeaconBlocksByRange v2](#beaconblocksbyrange-v2)
    - [BeaconBlocksByRoot v2](#beaconblocksbyroot-v2)
    - [BlobSidecarsByRange v1](#blobsidecarsbyrange-v1)
    - [BlobSidecarsByRoot v1](#blobsidecarsbyroot-v1)
- [Design decision rationale](#design-decision-rationale)
  - [Why are blobs relayed as a sidecar, separate from beacon blocks?](#why-are-blobs-relayed-as-a-sidecar-separate-from-beacon-blocks)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này chứa đặc tả networking của consensus layer cho Deneb.

Đặc tả các thay đổi này tiếp tục theo cùng định dạng với đặc tả networking của các
bản nâng cấp trước, và coi các đặc tả đó là điều kiện tiên quyết (tức là bạn cần
nắm phần networking của Phase0, Altair, Bellatrix và Capella trước; ở đây chỉ mô tả
những gì thay đổi hoặc được bổ sung).

> 💡 Ghi chú: Thay đổi chính về networking của Deneb đến từ EIP-4844 (proto-danksharding):
> blob được truyền đi dưới dạng `BlobSidecar` tách riêng khỏi beacon block, qua các
> subnet gossip mới và các message Req/Resp mới. Ngoài ra còn có EIP-7044 (chữ ký
> voluntary exit cố định theo `CAPELLA_FORK_VERSION`) và EIP-7045 (mở rộng cửa sổ
> lan truyền attestation).

## Presets

*[New in Deneb:EIP4844]*

| Name                                   | Value                                                                                                                                     | Description                                                                 |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `KZG_COMMITMENT_INCLUSION_PROOF_DEPTH` | `Uint64(floorlog2(get_generalized_index(BeaconBlockBody, "blob_kzg_commitments")) + 1 + ceillog2(MAX_BLOB_COMMITMENTS_PER_BLOCK))` (= 17) | <!-- predefined --> Độ sâu Merkle proof cho một phần tử của list `blob_kzg_commitments` |

## Configs

*[New in Deneb:EIP4844]*

| Name                                    | Value                    | Description                                                    |
| --------------------------------------- | ------------------------ | -------------------------------------------------------------- |
| `MAX_REQUEST_BLOCKS_DENEB`              | `Uint64(2**7)` (= 128)   | Số block tối đa trong một request                              |
| `MIN_EPOCHS_FOR_BLOB_SIDECARS_REQUESTS` | `Epoch(2**12)` (= 4,096) | Khoảng epoch tối thiểu mà node phải phục vụ blob sidecar       |
| `BLOB_SIDECAR_SUBNET_COUNT`             | `Uint64(6)`              | Số subnet blob sidecar được dùng trong giao thức gossipsub     |

## Types

### Modified `BeaconBlockRoots`

```python
# [Modified in Deneb:EIP4844]
class BeaconBlockRoots(List[Root]):
    """
    Beacon block roots requested in a ``BeaconBlocksByRoot`` request.
    """

    LIMIT = MAX_REQUEST_BLOCKS_DENEB
```

### Modified `SignedBeaconBlocks`

```python
# [Modified in Deneb:EIP4844]
class SignedBeaconBlocks(List[SignedBeaconBlock]):
    """
    Signed beacon blocks returned in a ``BeaconBlocksByRange`` or
    ``BeaconBlocksByRoot`` response.
    """

    LIMIT = MAX_REQUEST_BLOCKS_DENEB
```

### New `BlobIdentifiers`

```python
class BlobIdentifiers(List[BlobIdentifier]):
    """
    The identifiers of the blob sidecars requested in a
    ``BlobSidecarsByRoot`` request.
    """

    LIMIT = compute_max_request_blob_sidecars()
```

### New `BlobSidecars`

```python
class BlobSidecars(List[BlobSidecar]):
    """
    Blob sidecars returned in a ``BlobSidecarsByRange`` or
    ``BlobSidecarsByRoot`` response.
    """

    LIMIT = compute_max_request_blob_sidecars()
```

### New `KZGCommitmentInclusionProof`

```python
class KZGCommitmentInclusionProof(Vector[Bytes32]):
    """
    A Merkle branch proving a blob's KZG commitment within
    ``BeaconBlockBody``.
    """

    LENGTH = KZG_COMMITMENT_INCLUSION_PROOF_DEPTH
```

## Containers

### New `BlobSidecar`

*[New in Deneb:EIP4844]*

*Ghi chú*: `index` là chỉ số (vị trí) của blob trong block.

> 💡 Ghi chú: Mỗi `BlobSidecar` mang theo một blob, KZG commitment và KZG proof của
> blob đó, cùng với `signed_block_header` của block chứa nó và
> `kzg_commitment_inclusion_proof` — Merkle proof chứng minh commitment này nằm
> trong `body_root` của block header. Nhờ vậy node nhận có thể kiểm tra sidecar mà
> không cần có toàn bộ block.

```python
class BlobSidecar(Container):
    index: BlobIndex
    blob: Blob
    kzg_commitment: KZGCommitment
    kzg_proof: KZGProof
    signed_block_header: SignedBeaconBlockHeader
    kzg_commitment_inclusion_proof: KZGCommitmentInclusionProof
```

### New `BlobIdentifier`

*[New in Deneb:EIP4844]*

*(Định danh một blob sidecar bằng root của block chứa nó và chỉ số blob trong block đó.)*

```python
class BlobIdentifier(Container):
    block_root: Root
    index: BlobIndex
```

## Helpers

### Modified `Seen`

*(Thêm `blob_sidecar_tuples` để theo dõi các blob sidecar đã thấy theo bộ
`(slot, proposer_index, blob index)`, phục vụ điều kiện IGNORE trùng lặp trên topic blob.)*

```python
@dataclass
class Seen:
    proposer_slots: set[tuple[Slot, ValidatorIndex]]
    aggregator_epochs: set[tuple[Epoch, ValidatorIndex]]
    aggregate_data_roots: dict[Root, set[tuple[bool, ...]]]
    voluntary_exit_indices: set[ValidatorIndex]
    proposer_slashing_indices: set[ValidatorIndex]
    attester_slashing_indices: set[ValidatorIndex]
    attestation_validator_epochs: set[tuple[Epoch, ValidatorIndex]]
    sync_contribution_aggregator_slots: set[tuple[Slot, ValidatorIndex, Uint64]]
    sync_contribution_data: dict[tuple[Slot, Root, Uint64], set[tuple[bool, ...]]]
    sync_message_validator_slots: set[tuple[Slot, ValidatorIndex, Uint64]]
    bls_to_execution_change_indices: set[ValidatorIndex]
    # [New in Deneb]
    blob_sidecar_tuples: set[tuple[Slot, ValidatorIndex, BlobIndex]]
```

### Modified `compute_fork_version`

*(Bổ sung nhánh trả về `DENEB_FORK_VERSION` cho các epoch từ `DENEB_FORK_EPOCH` trở đi.)*

```python
def compute_fork_version(epoch: Epoch) -> Version:
    """
    Return the fork version at the given ``epoch``.
    """
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

### New `is_within_epoch`

*(Kiểm tra thời điểm hiện tại có nằm trong epoch cho trước hay không, có tính dung sai
`MAXIMUM_GOSSIP_CLOCK_DISPARITY` ở cả hai đầu.)*

```python
def is_within_epoch(
    store: Store,
    epoch: Epoch,
    current_time_ms: Uint64,
) -> bool:
    """
    Check if the current time is within the given epoch
    (with MAXIMUM_GOSSIP_CLOCK_DISPARITY allowance on both ends).
    """
    return is_within_slot_range(
        store,
        compute_start_slot_at_epoch(epoch),
        SLOTS_PER_EPOCH - 1,
        current_time_ms,
    )
```

### New `is_current_or_previous_epoch`

*(Kiểm tra epoch cho trước là epoch hiện tại hoặc epoch liền trước. Lưu ý: "epoch là
epoch trước" tương đương với "thời điểm hiện tại nằm trong `epoch + 1`".)*

```python
def is_current_or_previous_epoch(
    store: Store,
    epoch: Epoch,
    current_time_ms: Uint64,
) -> bool:
    """
    Check if the given epoch is the current or previous epoch
    (with MAXIMUM_GOSSIP_CLOCK_DISPARITY allowance).
    """
    is_current = is_within_epoch(store, epoch, current_time_ms)
    is_previous = is_within_epoch(store, epoch + 1, current_time_ms)
    return is_current or is_previous
```

### New `compute_max_request_blob_sidecars`

*(Số blob sidecar tối đa trong một request = số block tối đa mỗi request × số blob
tối đa mỗi block.)*

```python
def compute_max_request_blob_sidecars() -> Uint64:
    """
    Return the maximum number of blob sidecars in a single request.
    """
    return MAX_REQUEST_BLOCKS_DENEB * MAX_BLOBS_PER_BLOCK
```

### New `verify_blob_sidecar_inclusion_proof`

*(Kiểm tra `kzg_commitment_inclusion_proof` của sidecar: chứng minh rằng
`kzg_commitment` nằm đúng ở vị trí `index` trong list `blob_kzg_commitments` của
`BeaconBlockBody`, có root là `body_root` trong block header đã ký.)*

```python
def verify_blob_sidecar_inclusion_proof(blob_sidecar: BlobSidecar) -> bool:
    gindex = get_subtree_index(
        get_generalized_index(BeaconBlockBody, "blob_kzg_commitments", blob_sidecar.index)
    )
    return is_valid_merkle_branch(
        leaf=hash_tree_root(blob_sidecar.kzg_commitment),
        branch=blob_sidecar.kzg_commitment_inclusion_proof,
        depth=KZG_COMMITMENT_INCLUSION_PROOF_DEPTH,
        index=gindex,
        root=blob_sidecar.signed_block_header.message.body_root,
    )
```

## The gossip domain: gossipsub

Một số gossip mesh được nâng cấp trong Deneb để hỗ trợ các kiểu dữ liệu đã được cập nhật.

### Topics and messages

Các topic tuân theo cùng đặc tả như ở các bản nâng cấp trước.

Topic `beacon_block` được sửa đổi để hỗ trợ cả block Deneb, và các topic mới được
bổ sung theo bảng bên dưới.

Topic `voluntary_exit` được sửa đổi một cách ngầm định (implicit), dù việc kiểm tra
chữ ký của message này được cố định (lock-in) dùng `CAPELLA_FORK_VERSION` theo
EIP-7044. Nói cách khác: tên topic/fork digest vẫn đổi theo Deneb, nhưng domain dùng
để kiểm tra chữ ký voluntary exit luôn tính bằng `CAPELLA_FORK_VERSION`, nên một
voluntary exit đã ký sẽ còn hợp lệ vĩnh viễn qua các fork sau.

Các topic `beacon_aggregate_and_proof` và `beacon_attestation_{subnet_id}` được sửa
đổi để cho phép gossip các attestation được tạo trong epoch `N` trong suốt toàn bộ
epoch `N+1`, thay vì chỉ trong vòng `ATTESTATION_PROPAGATION_SLOT_RANGE` slot, theo
EIP-7045.

Đặc tả về việc tạo, kiểm tra (validation) và lan truyền message không thay đổi so
với tài liệu Capella, trừ khi được ghi chú rõ ở đây.

Cách tính `message-id` vẫn giữ nguyên.

Các topic mới cùng với kiểu của trường `data` trong gossipsub message được liệt kê
trong bảng sau:

| Name                       | Message Type                         |
| -------------------------- | ------------------------------------ |
| `blob_sidecar_{subnet_id}` | `BlobSidecar` [New in Deneb:EIP4844] |

#### Global topics

##### Modified `beacon_block`

*Ghi chú*: Hàm này được sửa đổi để kiểm tra số lượng blob KZG commitment có trong
beacon block body (không được vượt quá `MAX_BLOBS_PER_BLOCK`).

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

    # [IGNORE] Block là block đầu tiên có chữ ký hợp lệ nhận được cho cặp (slot, proposer) này
    proposer_slot_key = (block.slot, block.proposer_index)
    if proposer_slot_key in seen.proposer_slots:
        raise GossipIgnore("block is not the first valid block for this slot and proposer")

    # [IGNORE] Block không thuộc một slot trong tương lai
    # (MAY đưa vào hàng đợi để xử lý khi đến đúng slot)
    if is_future_slot(store, block.slot, current_time_ms):
        raise GossipIgnore("block is from a future slot")

    # [IGNORE] Block thuộc slot lớn hơn slot finalized gần nhất
    # (MAY vẫn chọn kiểm tra và lưu những block như vậy cho mục đích khác
    # -- ví dụ: phát hiện slashing, archive node, v.v.)
    finalized_slot = compute_start_slot_at_epoch(store.finalized_checkpoint.epoch)
    if block.slot <= finalized_slot:
        raise GossipIgnore("block is not from a slot greater than the latest finalized slot")

    # [IGNORE] Block cha đã được thấy (qua gossip hoặc nguồn khác ngoài gossip)
    # (MAY đưa vào hàng đợi cho đến khi lấy được block cha)
    if block.parent_root not in store.blocks:
        raise GossipIgnore("block's parent has not been seen")

    parent_payload_status = PAYLOAD_STATUS_NOT_VALIDATED
    if block.parent_root in block_payload_statuses:
        parent_payload_status = block_payload_statuses[block.parent_root]

    if block.parent_root not in store.block_states:
        if parent_payload_status == PAYLOAD_STATUS_NOT_VALIDATED:
            # [REJECT] Block cha không qua được validation và execution payload của nó đang ở trạng thái optimistic (chưa được EL xác thực)
            raise GossipReject("block's parent is invalid and its payload is optimistic")

        # [IGNORE] Block cha không qua được validation và execution payload của nó đã được xử lý
        raise GossipIgnore("block's parent is invalid and its payload is processed")

    # [IGNORE] Block cha qua được validation nhưng execution payload của nó không hợp lệ
    if parent_payload_status == PAYLOAD_STATUS_INVALIDATED:
        raise GossipIgnore("block's parent is valid and its payload is invalid")

    state = store.block_states[get_head(store).root]

    # [REJECT] Proposer index phải là một validator index hợp lệ
    if block.proposer_index >= len(state.validators):
        raise GossipReject("proposer index out of range")

    # [REJECT] Chữ ký của proposer phải hợp lệ
    proposer = state.validators[block.proposer_index]
    domain = get_domain(state, DOMAIN_BEACON_PROPOSER, compute_epoch_at_slot(block.slot))
    signing_root = compute_signing_root(block, domain)
    if not bls.Verify(proposer.pubkey, signing_root, signed_beacon_block.signature):
        raise GossipReject("invalid proposer signature")

    # [REJECT] Timestamp của execution payload phải khớp với thời điểm của slot
    if execution_payload.timestamp != compute_time_at_slot(state.genesis_time, block.slot):
        raise GossipReject("incorrect execution payload timestamp")

    # [REJECT] Slot của block phải lớn hơn slot của block cha
    if block.slot <= store.blocks[block.parent_root].slot:
        raise GossipReject("block is not from a higher slot than its parent")

    # [REJECT] Finalized checkpoint hiện tại phải là tổ tiên (ancestor) của block
    finalized_epoch = store.finalized_checkpoint.epoch
    finalized_checkpoint_block = get_checkpoint_block(store, block.parent_root, finalized_epoch)
    if finalized_checkpoint_block != store.finalized_checkpoint.root:
        raise GossipReject("finalized checkpoint is not an ancestor of block")

    # [New in Deneb:EIP4844]
    # [REJECT] Số lượng KZG commitment phải nhỏ hơn hoặc bằng giới hạn
    if len(block.body.blob_kzg_commitments) > MAX_BLOBS_PER_BLOCK:
        raise GossipReject("too many blob kzg commitments")

    # [REJECT] Block phải được đề xuất bởi đúng proposer dự kiến của slot
    # (nếu chưa có dữ liệu shuffling thì IGNORE thay vì REJECT, và MAY đưa vào hàng đợi để xử lý sau)
    parent_state = store.block_states[block.parent_root].copy()
    process_slots(parent_state, block.slot)
    expected_proposer = get_beacon_proposer_index(parent_state)
    if block.proposer_index != expected_proposer:
        raise GossipReject("block proposer_index does not match expected proposer")

    # Đánh dấu block này là đã thấy
    seen.proposer_slots.add(proposer_slot_key)
```

##### Modified `beacon_aggregate_and_proof`

*Ghi chú*: Hàm này được sửa đổi để IGNORE các aggregate attestation thuộc slot
tương lai, và IGNORE các aggregate attestation có epoch không phải epoch hiện tại
hoặc epoch trước đó (tính theo `current_time_ms`).

> 💡 Ghi chú: Trước Deneb, điều kiện là slot của attestation phải nằm trong
> `ATTESTATION_PROPAGATION_SLOT_RANGE` (32 slot) gần nhất. Với EIP-7045, attestation
> của epoch `N` được chấp nhận cho đến hết epoch `N+1`, phù hợp với việc attestation
> giờ có thể được đưa vào block trong khoảng thời gian dài hơn.

```python
def validate_beacon_aggregate_and_proof_gossip(
    seen: Seen,
    store: Store,
    signed_aggregate_and_proof: SignedAggregateAndProof,
    current_time_ms: Uint64,
) -> None:
    """
    Validate a SignedAggregateAndProof for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    aggregate_and_proof = signed_aggregate_and_proof.message
    aggregate = aggregate_and_proof.aggregate
    index = aggregate.data.index
    aggregation_bits = aggregate.aggregation_bits

    # [IGNORE] Chưa từng thấy một aggregate hợp lệ có tập aggregation bits là tập cha (superset) của aggregate này
    aggregate_data_root = hash_tree_root(aggregate.data)
    aggregate_bits = tuple(bool(bit) for bit in aggregation_bits)
    seen_bits = seen.aggregate_data_roots.get(aggregate_data_root, set())
    if is_non_strict_superset(seen_bits, aggregate_bits):
        raise GossipIgnore("already seen aggregate for this data")

    # [IGNORE] Đây là aggregate hợp lệ đầu tiên cho cặp (epoch, aggregator) này
    aggregator_index = aggregate_and_proof.aggregator_index
    target_epoch = aggregate.data.target.epoch
    aggregator_epoch_key = (target_epoch, aggregator_index)
    if aggregator_epoch_key in seen.aggregator_epochs:
        raise GossipIgnore("already seen aggregate for this epoch and aggregator")

    # [IGNORE] Block được bỏ phiếu đã được thấy (qua gossip hoặc nguồn khác ngoài gossip)
    # (MAY đưa vào hàng đợi cho đến khi lấy được block)
    block_root = aggregate.data.beacon_block_root
    if block_root not in store.blocks:
        raise GossipIgnore("block being voted for has not been seen")

    # [REJECT] Block được bỏ phiếu phải qua được validation
    if block_root not in store.block_states:
        raise GossipReject("block being voted for failed validation")

    state = store.block_states[get_head(store).root]

    # [REJECT] Committee index phải nằm trong khoảng hợp lệ
    committee_count = get_committee_count_per_slot(state, aggregate.data.target.epoch)
    if index >= committee_count:
        raise GossipReject("committee index out of range")

    # [New in Deneb:EIP7045]
    # [IGNORE] Slot của aggregate attestation không thuộc tương lai
    # (MAY đưa vào hàng đợi để xử lý khi đến đúng slot)
    if is_future_slot(store, aggregate.data.slot, current_time_ms):
        raise GossipIgnore("aggregate slot is from a future slot")

    # [Modified in Deneb:EIP7045]
    # [IGNORE] Epoch của aggregate attestation phải là epoch hiện tại hoặc epoch trước đó
    attestation_epoch = compute_epoch_at_slot(aggregate.data.slot)
    if not is_current_or_previous_epoch(store, attestation_epoch, current_time_ms):
        raise GossipIgnore("aggregate epoch is not current or previous epoch")

    # [REJECT] Epoch của aggregate attestation phải khớp với epoch của target
    if aggregate.data.target.epoch != compute_epoch_at_slot(aggregate.data.slot):
        raise GossipReject("attestation epoch does not match target epoch")

    # [REJECT] Số aggregation bits phải bằng kích thước committee
    committee = get_beacon_committee(state, aggregate.data.slot, index)
    if len(aggregation_bits) != len(committee):
        raise GossipReject("aggregation bits length does not match committee size")

    # [REJECT] Aggregate attestation phải có ít nhất một người tham gia
    attesting_indices = get_attesting_indices(state, aggregate)
    if len(attesting_indices) < 1:
        raise GossipReject("aggregate has no participants")

    # [REJECT] Selection proof phải chọn validator này làm aggregator
    if not is_aggregator(state, aggregate.data.slot, index, aggregate_and_proof.selection_proof):
        raise GossipReject("validator is not selected as aggregator")

    # [REJECT] Aggregator phải là thành viên của committee
    if aggregator_index not in committee:
        raise GossipReject("aggregator is not a member of the committee")

    # [REJECT] Chữ ký selection proof phải hợp lệ
    aggregator = state.validators[aggregator_index]
    domain = get_domain(state, DOMAIN_SELECTION_PROOF, target_epoch)
    signing_root = compute_signing_root(aggregate.data.slot, domain)
    if not bls.Verify(aggregator.pubkey, signing_root, aggregate_and_proof.selection_proof):
        raise GossipReject("invalid selection proof signature")

    # [REJECT] Chữ ký của aggregator phải hợp lệ
    domain = get_domain(state, DOMAIN_AGGREGATE_AND_PROOF, target_epoch)
    signing_root = compute_signing_root(aggregate_and_proof, domain)
    if not bls.Verify(aggregator.pubkey, signing_root, signed_aggregate_and_proof.signature):
        raise GossipReject("invalid aggregator signature")

    # [REJECT] Chữ ký aggregate phải hợp lệ
    if not is_valid_indexed_attestation(state, get_indexed_attestation(state, aggregate)):
        raise GossipReject("invalid aggregate signature")

    # [REJECT] Target block phải là tổ tiên của block được bỏ phiếu LMD
    checkpoint_block = get_checkpoint_block(store, block_root, aggregate.data.target.epoch)
    if checkpoint_block != aggregate.data.target.root:
        raise GossipReject("target block is not an ancestor of LMD vote block")

    # [IGNORE] Finalized checkpoint phải là tổ tiên của block
    finalized_epoch = store.finalized_checkpoint.epoch
    finalized_checkpoint_block = get_checkpoint_block(store, block_root, finalized_epoch)
    if finalized_checkpoint_block != store.finalized_checkpoint.root:
        raise GossipIgnore("finalized checkpoint is not an ancestor of block")

    # Đánh dấu aggregate này là đã thấy
    seen.aggregator_epochs.add(aggregator_epoch_key)
    if aggregate_data_root not in seen.aggregate_data_roots:
        seen.aggregate_data_roots[aggregate_data_root] = set()
    seen.aggregate_data_roots[aggregate_data_root].add(aggregate_bits)
```

##### Modified `voluntary_exit`

*Ghi chú*: Hàm này được sửa đổi để dùng `CAPELLA_FORK_VERSION` khi tính domain của
chữ ký, nhờ đó voluntary exit vẫn hợp lệ khi đi qua ranh giới các fork.

```python
def validate_voluntary_exit_gossip(
    seen: Seen,
    store: Store,
    signed_voluntary_exit: SignedVoluntaryExit,
    current_time_ms: Uint64,
) -> None:
    """
    Validate a SignedVoluntaryExit for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    voluntary_exit = signed_voluntary_exit.message
    validator_index = voluntary_exit.validator_index

    # [IGNORE] Đây là voluntary exit hợp lệ đầu tiên nhận được cho validator này
    if validator_index in seen.voluntary_exit_indices:
        raise GossipIgnore("already seen voluntary exit for this validator")

    # [IGNORE] Epoch của voluntary exit không nằm trong tương lai
    if is_future_epoch(store, voluntary_exit.epoch, current_time_ms):
        raise GossipIgnore("voluntary exit epoch is in the future")

    state = store.block_states[get_head(store).root]

    # [REJECT] Validator index phải hợp lệ
    if validator_index >= len(state.validators):
        raise GossipReject("validator index out of range")

    validator = state.validators[validator_index]
    current_epoch = get_current_epoch(state)

    # [IGNORE] Validator chưa từng khởi tạo exit
    if validator.exit_epoch != FAR_FUTURE_EPOCH:
        raise GossipIgnore("validator has already initiated exit")

    # [REJECT] Validator phải đang active
    if not is_active_validator(validator, current_epoch):
        raise GossipReject("validator is not active")

    # [REJECT] Validator phải đã active đủ lâu
    if current_epoch < validator.activation_epoch + SHARD_COMMITTEE_PERIOD:
        raise GossipReject("validator has not been active long enough")

    # [Modified in Deneb:EIP7044]
    # [REJECT] Chữ ký phải hợp lệ
    domain = compute_domain(
        DOMAIN_VOLUNTARY_EXIT, CAPELLA_FORK_VERSION, state.genesis_validators_root
    )
    signing_root = compute_signing_root(voluntary_exit, domain)
    if not bls.Verify(validator.pubkey, signing_root, signed_voluntary_exit.signature):
        raise GossipReject("invalid voluntary exit signature")

    # Đánh dấu voluntary exit này là đã thấy
    seen.voluntary_exit_indices.add(validator_index)
```

#### Attestation subnets

##### Modified `beacon_attestation_{subnet_id}`

*[Modified in Deneb:EIP7045]* Attestation của epoch trước giờ được lan truyền
(propagate) trong suốt toàn bộ epoch hiện tại, thay vì chỉ trong
`ATTESTATION_PROPAGATION_SLOT_RANGE` slot kế tiếp như trước.

*Ghi chú*: Hàm này được sửa đổi để bỏ qua (ignore) attestation thuộc các slot
trong tương lai, và bỏ qua attestation có epoch không phải là epoch hiện tại hoặc
epoch trước đó, tính theo `current_time_ms`.

```python
def validate_beacon_attestation_gossip(
    seen: Seen,
    store: Store,
    attestation: Attestation,
    current_time_ms: Uint64,
    subnet_id: SubnetID,
) -> None:
    """
    Validate an Attestation for gossip propagation on a subnet.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    data = attestation.data
    committee_index = data.index
    target_epoch = data.target.epoch
    aggregation_bits = attestation.aggregation_bits

    # [IGNORE] Block được bỏ phiếu đã được nhìn thấy (qua gossip hoặc nguồn khác)
    # (MAY đưa vào hàng đợi cho tới khi lấy được block)
    block_root = data.beacon_block_root
    if block_root not in store.blocks:
        raise GossipIgnore("block being voted for has not been seen")

    # [REJECT] Block được bỏ phiếu phải vượt qua validation
    if block_root not in store.block_states:
        raise GossipReject("block being voted for failed validation")

    state = store.block_states[get_head(store).root]

    # [REJECT] Committee index nằm trong khoảng hợp lệ
    committees_per_slot = get_committee_count_per_slot(state, target_epoch)
    if committee_index >= committees_per_slot:
        raise GossipReject("committee index out of range")

    # [REJECT] Attestation được gửi đúng subnet
    expected_subnet = compute_subnet_for_attestation(
        committees_per_slot, data.slot, committee_index
    )
    if expected_subnet != subnet_id:
        raise GossipReject("attestation is for wrong subnet")

    # [Modified in Deneb:EIP7045]
    # [IGNORE] Slot của attestation không phải là slot trong tương lai
    # (MAY đưa vào hàng đợi để xử lý khi tới slot phù hợp)
    if is_future_slot(store, data.slot, current_time_ms):
        raise GossipIgnore("attestation slot is from a future slot")

    # [Modified in Deneb:EIP7045]
    # [IGNORE] Epoch của attestation là epoch hiện tại hoặc epoch trước đó
    attestation_epoch = compute_epoch_at_slot(data.slot)
    if not is_current_or_previous_epoch(store, attestation_epoch, current_time_ms):
        raise GossipIgnore("attestation epoch is not current or previous epoch")

    # [REJECT] Epoch của attestation khớp với target của nó
    if target_epoch != compute_epoch_at_slot(data.slot):
        raise GossipReject("attestation epoch does not match target epoch")

    # [REJECT] Attestation chưa được aggregate (có đúng một bit được bật)
    num_bits_set = get_set_bit_count(aggregation_bits)
    if num_bits_set != 1:
        raise GossipReject("attestation is not unaggregated")

    # [REJECT] Số aggregation bit bằng kích thước committee
    committee = get_beacon_committee(state, data.slot, committee_index)
    if len(aggregation_bits) != len(committee):
        raise GossipReject("aggregation bits length does not match committee size")

    # [IGNORE] Chưa thấy attestation hợp lệ nào khác cho cặp (target epoch, validator) này
    set_bit_indices = [index for index, bit in enumerate(aggregation_bits) if bit]
    participant_index = committee[set_bit_indices[0]]
    attestation_epoch_key = (target_epoch, participant_index)
    if attestation_epoch_key in seen.attestation_validator_epochs:
        raise GossipIgnore("already seen attestation for this epoch and validator")

    # [REJECT] Chữ ký của attestation hợp lệ
    indexed_attestation = get_indexed_attestation(state, attestation)
    if not is_valid_indexed_attestation(state, indexed_attestation):
        raise GossipReject("invalid attestation signature")

    # [REJECT] Target block của attestation là tổ tiên (ancestor) của block được bỏ phiếu LMD
    target_checkpoint_block = get_checkpoint_block(store, block_root, target_epoch)
    if target_checkpoint_block != data.target.root:
        raise GossipReject("target block is not an ancestor of LMD vote block")

    # [IGNORE] finalized_checkpoint hiện tại là tổ tiên của block
    finalized_epoch = store.finalized_checkpoint.epoch
    finalized_checkpoint_block = get_checkpoint_block(store, block_root, finalized_epoch)
    if finalized_checkpoint_block != store.finalized_checkpoint.root:
        raise GossipIgnore("finalized checkpoint is not an ancestor of block")

    # Đánh dấu attestation này là đã thấy
    seen.attestation_validator_epochs.add(attestation_epoch_key)
```

> 💡 Ghi chú: Khác biệt chính so với Phase0 là điều kiện thời gian. Trước Deneb,
> attestation chỉ được chấp nhận trong cửa sổ `ATTESTATION_PROPAGATION_SLOT_RANGE`
> slot (32 slot) kể từ slot của nó. Từ Deneb (EIP-7045), mọi attestation thuộc
> epoch hiện tại hoặc epoch trước đều được lan truyền, miễn là không thuộc slot
> trong tương lai.

#### Blob subnets

##### New `blob_sidecar_{subnet_id}`

Các topic `blob_sidecar_{subnet_id}` — trong đó mỗi blob index được ánh xạ tới
một `subnet_id` nào đó — chỉ được dùng để lan truyền các blob sidecar mới tới mọi
node trong mạng. Mỗi BlobSidecar được gửi đi nguyên vẹn (không chia nhỏ).

```python
def validate_blob_sidecar_gossip(
    seen: Seen,
    store: Store,
    blob_sidecar: BlobSidecar,
    current_time_ms: Uint64,
    subnet_id: SubnetID,
) -> None:
    """
    Validate a BlobSidecar for gossip propagation on a subnet.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    block_header = blob_sidecar.signed_block_header.message

    # [IGNORE] Sidecar là sidecar đầu tiên nhận được cho bộ
    # (block_header.slot, block_header.proposer_index, blob_sidecar.index)
    sidecar_tuple = (block_header.slot, block_header.proposer_index, blob_sidecar.index)
    if sidecar_tuple in seen.blob_sidecar_tuples:
        raise GossipIgnore("already seen blob sidecar from this proposer for this slot and index")

    # [REJECT] Index của sidecar phù hợp với MAX_BLOBS_PER_BLOCK
    if blob_sidecar.index >= MAX_BLOBS_PER_BLOCK:
        raise GossipReject("blob index out of range")

    # [REJECT] Sidecar được gửi đúng subnet
    if compute_subnet_for_blob_sidecar(blob_sidecar.index) != subnet_id:
        raise GossipReject("blob sidecar is for wrong subnet")

    # [IGNORE] Sidecar không thuộc slot trong tương lai
    # (MAY đưa vào hàng đợi để xử lý khi tới slot phù hợp)
    if is_future_slot(store, block_header.slot, current_time_ms):
        raise GossipIgnore("blob sidecar is from a future slot")

    # [IGNORE] Sidecar thuộc slot lớn hơn slot finalized gần nhất
    finalized_slot = compute_start_slot_at_epoch(store.finalized_checkpoint.epoch)
    if block_header.slot <= finalized_slot:
        raise GossipIgnore("blob sidecar is not from a slot greater than the latest finalized slot")

    # [IGNORE] Parent của block chứa sidecar đã được nhìn thấy
    # (MAY đưa vào hàng đợi để xử lý khi đã lấy được parent block)
    parent_root = block_header.parent_root
    if parent_root not in store.blocks:
        raise GossipIgnore("blob sidecar's parent has not been seen")

    # [REJECT] Parent của block chứa sidecar vượt qua validation
    if parent_root not in store.block_states:
        raise GossipReject("blob sidecar's parent failed validation")

    state = store.block_states[get_head(store).root]

    # [REJECT] Proposer index là một validator index hợp lệ
    if block_header.proposer_index >= len(state.validators):
        raise GossipReject("proposer index out of range")

    # [REJECT] Chữ ký proposer trên blob_sidecar.signed_block_header hợp lệ
    proposer = state.validators[block_header.proposer_index]
    domain = get_domain(state, DOMAIN_BEACON_PROPOSER, compute_epoch_at_slot(block_header.slot))
    signing_root = compute_signing_root(block_header, domain)
    if not bls.Verify(proposer.pubkey, signing_root, blob_sidecar.signed_block_header.signature):
        raise GossipReject("invalid proposer signature on blob sidecar block header")

    # [REJECT] Sidecar thuộc slot cao hơn slot của parent block
    if block_header.slot <= store.blocks[parent_root].slot:
        raise GossipReject("blob sidecar is not from a higher slot than its parent")

    # [REJECT] finalized_checkpoint hiện tại là tổ tiên của block chứa sidecar
    finalized_epoch = store.finalized_checkpoint.epoch
    finalized_checkpoint_block = get_checkpoint_block(store, parent_root, finalized_epoch)
    if finalized_checkpoint_block != store.finalized_checkpoint.root:
        raise GossipReject("finalized checkpoint is not an ancestor of blob sidecar's block")

    # [REJECT] Inclusion proof của sidecar hợp lệ theo verify_blob_sidecar_inclusion_proof
    if not verify_blob_sidecar_inclusion_proof(blob_sidecar):
        raise GossipReject("invalid blob sidecar inclusion proof")

    # [REJECT] Blob của sidecar hợp lệ theo verify_blob_kzg_proof
    if not kzg.verify_blob_kzg_proof(
        blob_sidecar.blob, blob_sidecar.kzg_commitment, blob_sidecar.kzg_proof
    ):
        raise GossipReject("invalid blob kzg proof")

    # [REJECT] Sidecar được đề xuất bởi đúng proposer_index mong đợi
    # (nếu chưa có shuffling, thì IGNORE thay vì REJECT và MAY đưa vào hàng đợi để xử lý sau)
    parent_state = store.block_states[parent_root].copy()
    process_slots(parent_state, block_header.slot)
    expected_proposer = get_beacon_proposer_index(parent_state)
    if block_header.proposer_index != expected_proposer:
        raise GossipReject("blob sidecar proposer_index does not match expected proposer")

    # Đánh dấu blob sidecar này là đã thấy
    seen.blob_sidecar_tuples.add(sidecar_tuple)
```

> 💡 Ghi chú: Sidecar có thể được xác thực độc lập với block chứa nó: chữ ký
> proposer trên header chứng minh nguồn gốc, inclusion proof chứng minh
> `kzg_commitment` thuộc block body, và KZG proof chứng minh blob khớp với
> commitment. Bộ `(slot, proposer_index, index)` được dùng để chống equivocation
> (proposer gửi nhiều sidecar khác nhau cho cùng một vị trí).

*Ghi chú*: Hàm `kzg.verify_blob_kzg_proof` được định nghĩa trong
[cryptography-specs](https://github.com/ethereum/cryptography-specs) với
signature như sau:

<!-- eth_consensus_specs: skip -->

```python
def verify_blob_kzg_proof(blob: Blob, commitment_bytes: Bytes48, proof_bytes: Bytes48) -> bool:
    """
    Return ``True`` if and only if ``blob`` and its proof match the commitment.
    """
```

Epoch ngữ cảnh của `ForkDigest` được xác định bởi
`compute_epoch_at_slot(blob_sidecar.signed_block_header.message.slot)`.

Theo `fork_version = compute_fork_version(epoch)`:

<!-- eth_consensus_specs: skip -->

| `fork_version`                 | Chunk SSZ type      |
| ------------------------------ | ------------------- |
| `DENEB_FORK_VERSION` and later | `deneb.BlobSidecar` |

##### Blob retrieval via local execution-layer client

Ngoài các request `BlobSidecarsByRoot`, các blob gần đây MAY được lấy bằng cách
truy vấn execution layer (cụ thể là qua `engine_getBlobsV1`). Node trung thực
SHOULD gọi `engine_getBlobsV1` ngay khi nhận được một gossip block hợp lệ có chứa
dữ liệu (blob), rồi import các blob được trả về.

> 💡 Ghi chú: Các blob thường đã có sẵn trong mempool của execution client (do
> các blob transaction được lan truyền ở tầng execution), nên lấy trực tiếp từ đó
> thường nhanh hơn chờ sidecar qua gossip.

Khi client dùng execution layer cục bộ để lấy blob, chúng MUST hành xử như thể
`blob_sidecar` tương ứng đã được nhận qua gossip. Cụ thể, chúng MUST:

- Publish `blob_sidecar` tương ứng lên subnet `blob_sidecar_{subnet_id}`.
- Cập nhật các cấu trúc dữ liệu liên quan tới gossip rule (tức là cập nhật cache
  chống equivocation).

### Transitioning the gossip

Xem chi tiết về việc chuyển đổi gossip trong
[tài liệu Altair](../altair/p2p-interface.md#transitioning-the-gossip) để biết
cách xử lý việc chuyển đổi các gossip topic cho bản nâng cấp này.

## The Req/Resp domain

### Messages

#### BeaconBlocksByRange v2

**Protocol ID:** `/eth2/beacon_chain/req/beacon_blocks_by_range/2/`

Nội dung request:

```
(
  start_slot: Slot
  count: Uint64
  step: Uint64 # Deprecated, must be set to 1
)
```

Nội dung response:

```
(
  SignedBeaconBlocks
)
```

Fork-digest của Deneb được thêm vào enum `context` để chỉ định kiểu beacon block
của Deneb.

<!-- eth_consensus_specs: skip -->

| `fork_version`           | Chunk SSZ type                |
| ------------------------ | ----------------------------- |
| `GENESIS_FORK_VERSION`   | `phase0.SignedBeaconBlock`    |
| `ALTAIR_FORK_VERSION`    | `altair.SignedBeaconBlock`    |
| `BELLATRIX_FORK_VERSION` | `bellatrix.SignedBeaconBlock` |
| `CAPELLA_FORK_VERSION`   | `capella.SignedBeaconBlock`   |
| `DENEB_FORK_VERSION`     | `deneb.SignedBeaconBlock`     |

Mỗi lần request không được yêu cầu quá `MAX_REQUEST_BLOCKS_DENEB` block.

#### BeaconBlocksByRoot v2

**Protocol ID:** `/eth2/beacon_chain/req/beacon_blocks_by_root/2/`

Nội dung request:

```
(
  BeaconBlockRoots
)
```

Nội dung response:

```
(
  SignedBeaconBlocks
)
```

Fork-digest của Deneb được thêm vào enum `context` để chỉ định kiểu beacon block
của Deneb.

<!-- eth_consensus_specs: skip -->

| `fork_version`           | Chunk SSZ type                |
| ------------------------ | ----------------------------- |
| `GENESIS_FORK_VERSION`   | `phase0.SignedBeaconBlock`    |
| `ALTAIR_FORK_VERSION`    | `altair.SignedBeaconBlock`    |
| `BELLATRIX_FORK_VERSION` | `bellatrix.SignedBeaconBlock` |
| `CAPELLA_FORK_VERSION`   | `capella.SignedBeaconBlock`   |
| `DENEB_FORK_VERSION`     | `deneb.SignedBeaconBlock`     |

Mỗi lần request không được yêu cầu quá `MAX_REQUEST_BLOCKS_DENEB` block.

*[Modified in Deneb:EIP4844]* Client SHOULD đưa một block vào response ngay khi
block đó vượt qua các gossip validation rule. Client SHOULD NOT trả về các block
không vượt qua được state transition của beacon chain.

#### BlobSidecarsByRange v1

**Protocol ID:** `/eth2/beacon_chain/req/blob_sidecars_by_range/1/`

*[New in Deneb:EIP4844]*

Nội dung request:

```
(
  start_slot: Slot
  count: Uint64
)
```

Nội dung response:

```
(
  BlobSidecars
)
```

Yêu cầu các blob sidecar trong khoảng slot `[start_slot, start_slot + count)`,
dẫn tới head block hiện tại do fork choice chọn.

Trước khi xử lý response chunk tiếp theo, bên đọc response SHOULD kiểm tra rằng
blob sidecar có định dạng đúng, có inclusion proof hợp lệ, và khớp với các KZG
commitment mong đợi thông qua `kzg.verify_blob_kzg_proof`.

`BlobSidecarsByRange` chủ yếu được dùng để sync các blob có thể đã bị lỡ trên
gossip, và để sync trong cửa sổ `MIN_EPOCHS_FOR_BLOB_SIDECARS_REQUESTS`.

Request MUST được encode dưới dạng một SSZ-container.

Response MUST gồm không hoặc nhiều `response_chunk`. Mỗi `response_chunk`
_thành công_ MUST chứa đúng một payload `BlobSidecar`.

Đặt `blob_serve_range` là
`[max(current_epoch - MIN_EPOCHS_FOR_BLOB_SIDECARS_REQUESTS, DENEB_FORK_EPOCH), current_epoch]`.
Client MUST lưu giữ các blob sidecar đã thấy trong khoảng epoch
`blob_serve_range`, trong đó `current_epoch` được xác định theo thời gian thực
(wall-clock) hiện tại, và client MUST hỗ trợ phục vụ các request blob trong
khoảng này.

Các peer không thể trả lời request blob sidecar trong khoảng `blob_serve_range`
SHOULD phản hồi bằng mã lỗi `3: ResourceUnavailable`. Những peer như vậy, do
không thể phục vụ thành công các request trong khoảng này, MAY bị trừ điểm
(descore) hoặc bị ngắt kết nối bất cứ lúc nào.

*Ghi chú*: Yêu cầu trên ngụ ý rằng các node khởi động từ một weak subjectivity
checkpoint gần đây MUST backfill (tải bù ngược về quá khứ) cơ sở dữ liệu blob cục
bộ ít nhất tới hết khoảng `blob_serve_range` để tuân thủ đầy đủ các request
`BlobSidecarsByRange`.

*Ghi chú*: Mặc dù các client bootstrap từ một weak subjectivity checkpoint có thể
bắt đầu tham gia mạng ngay lập tức, các peer khác MAY ngắt kết nối và/hoặc tạm
thời cấm (ban) những client chưa sync hoặc mới sync một phần như vậy.

Client MUST trả về ít nhất các blob sidecar của block đầu tiên có chứa blob trong
khoảng được yêu cầu (nếu client có chúng), và không quá
`compute_max_request_blob_sidecars()` sidecar.

Với mỗi block mà client đưa blob sidecar vào response, client MUST đưa vào tất cả
blob sidecar của block đó.

Các blob sidecar tiếp theo, nếu tồn tại, MUST được gửi theo thứ tự `(slot, index)`
liên tiếp.

Các slot không chứa blob đã biết MUST được bỏ qua, giống hành vi của request
`BlocksByRange`. Do đó chỉ nên gửi các response chunk có chứa blob đã biết.

Client MAY giới hạn số lượng blob sidecar trong response.

Response MUST chứa không quá `count * MAX_BLOBS_PER_BLOCK` blob sidecar.

Client MUST trả về blob sidecar theo góc nhìn fork choice hiện tại của mình — tức
là các blob sidecar được bao gồm bởi các block thuộc chuỗi duy nhất xác định bởi
head hiện tại. Đáng chú ý, các block ở các slot trước thời điểm finalization MUST
dẫn tới finalized block đã được báo cáo trong handshake `Status`.

Client MUST trả về các blob sidecar nhất quán, thuộc cùng một chuỗi duy nhất
trong phạm vi của request.

Sau blob sidecar đầu tiên, client MAY dừng việc trả lời giữa chừng nếu fork
choice của nó thay đổi góc nhìn về chuỗi trong phạm vi của request.

Với mỗi `response_chunk` thành công, epoch ngữ cảnh của `ForkDigest` được xác
định bởi
`compute_epoch_at_slot(blob_sidecar.signed_block_header.message.slot)`.

Theo `fork_version = compute_fork_version(epoch)`:

<!-- eth_consensus_specs: skip -->

| `fork_version`                 | Chunk SSZ type      |
| ------------------------------ | ------------------- |
| `DENEB_FORK_VERSION` and later | `deneb.BlobSidecar` |

#### BlobSidecarsByRoot v1

**Protocol ID:** `/eth2/beacon_chain/req/blob_sidecars_by_root/1/`

*[New in Deneb:EIP4844]*

Nội dung request:

```
(
  BlobIdentifiers
)
```

Nội dung response:

```
(
  BlobSidecars
)
```

Yêu cầu các sidecar theo block root và index. Response là một danh sách
`BlobSidecar` có độ dài nhỏ hơn hoặc bằng số lượng yêu cầu. Danh sách có thể ngắn
hơn trong trường hợp peer trả lời đang thiếu block hoặc sidecar.

Trước khi xử lý response chunk tiếp theo, bên đọc response SHOULD kiểm tra rằng
blob sidecar có định dạng đúng, có inclusion proof hợp lệ, và khớp với các KZG
commitment mong đợi thông qua `kzg.verify_blob_kzg_proof`.

Mỗi lần request không được yêu cầu quá `compute_max_request_blob_sidecars()`
sidecar.

`BlobSidecarsByRoot` chủ yếu được dùng để khôi phục các blob gần đây (ví dụ khi
nhận được một block chứa transaction mà blob tương ứng bị thiếu).

Response MUST gồm không hoặc nhiều `response_chunk`. Mỗi `response_chunk`
_thành công_ MUST chứa đúng một payload `BlobSidecar`.

Client MUST hỗ trợ việc yêu cầu sidecar kể từ `minimum_request_epoch`, trong đó
`minimum_request_epoch = max(current_epoch - MIN_EPOCHS_FOR_BLOB_SIDECARS_REQUESTS, DENEB_FORK_EPOCH)`.
Nếu bất kỳ root nào trong request tham chiếu tới một block sớm hơn
`minimum_request_epoch`, peer MAY phản hồi bằng mã lỗi `3: ResourceUnavailable`
hoặc không đưa blob sidecar đó vào response.

Client MUST trả về ít nhất một sidecar, nếu có. Client MAY giới hạn số lượng
block và sidecar trong response.

Client SHOULD đưa một sidecar vào response ngay khi nó vượt qua các gossip
validation rule. Client SHOULD NOT trả về sidecar liên quan tới các block không
vượt qua gossip validation rule. Client SHOULD NOT trả về sidecar liên quan tới
các block không vượt qua state transition của beacon chain.

Với mỗi `response_chunk` thành công, epoch ngữ cảnh của `ForkDigest` được xác
định bởi
`compute_epoch_at_slot(blob_sidecar.signed_block_header.message.slot)`.

Theo `fork_version = compute_fork_version(epoch)`:

<!-- eth_consensus_specs: skip -->

| `fork_version`                 | Chunk SSZ type      |
| ------------------------------ | ------------------- |
| `DENEB_FORK_VERSION` and later | `deneb.BlobSidecar` |

## Design decision rationale

### Why are blobs relayed as a sidecar, separate from beacon blocks?

Thiết kế "sidecar" này đảm bảo khả năng tương thích về sau (forward
compatibility) cho việc tăng lượng dữ liệu hơn nữa, bằng cách coi
`is_data_available()` như một hộp đen: khi có full sharding,
`is_data_available()` có thể được thay bằng data-availability-sampling (DAS),
nhờ đó tránh việc mọi beacon node trong mạng đều phải tải toàn bộ blob.

Thiết kế sharding như vậy có thể đưa vào một phiên bản `BlobSidecar` cập nhật để
xác định shard, nhưng không ảnh hưởng tới cấu trúc của `BeaconBlock`.
