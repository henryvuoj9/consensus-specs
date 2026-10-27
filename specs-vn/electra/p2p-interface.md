# Electra -- Networking

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Configs](#configs)
- [Helpers](#helpers)
  - [Modified `Seen`](#modified-seen)
  - [Modified `compute_fork_version`](#modified-compute_fork_version)
  - [Modified `compute_max_request_blob_sidecars`](#modified-compute_max_request_blob_sidecars)
- [The gossip domain: gossipsub](#the-gossip-domain-gossipsub)
  - [Topics and messages](#topics-and-messages)
    - [Global topics](#global-topics)
      - [Modified `beacon_block`](#modified-beacon_block)
      - [Modified `beacon_aggregate_and_proof`](#modified-beacon_aggregate_and_proof)
      - [Modified `attester_slashing`](#modified-attester_slashing)
    - [Attestation subnets](#attestation-subnets)
      - [Modified `beacon_attestation_{subnet_id}`](#modified-beacon_attestation_subnet_id)
    - [Blob subnets](#blob-subnets)
      - [Modified `blob_sidecar_{subnet_id}`](#modified-blob_sidecar_subnet_id)
- [The Req/Resp domain](#the-reqresp-domain)
  - [Messages](#messages)
    - [BeaconBlocksByRange v2](#beaconblocksbyrange-v2)
    - [BeaconBlocksByRoot v2](#beaconblocksbyroot-v2)
    - [BlobSidecarsByRange v1](#blobsidecarsbyrange-v1)
    - [BlobSidecarsByRoot v1](#blobsidecarsbyroot-v1)

<!-- mdformat-toc end -->

## Introduction

*(Giới thiệu)*

Tài liệu này mô tả đặc tả networking (mạng) ở tầng consensus cho bản nâng cấp
Electra.

Đặc tả các thay đổi ở đây được viết theo cùng định dạng với đặc tả mạng của các
bản nâng cấp trước, và giả định rằng người đọc đã nắm các đặc tả đó (chúng là
điều kiện tiên quyết).

## Configs

*[New in Electra:EIP7691]*

| Name                                | Value       | Description                                                   |
| ----------------------------------- | ----------- | ------------------------------------------------------------- |
| `BLOB_SIDECAR_SUBNET_COUNT_ELECTRA` | `Uint64(9)` | Số lượng subnet blob sidecar được dùng trong giao thức gossipsub |

## Helpers

*(Các hàm/cấu trúc hỗ trợ)*

### Modified `Seen`

```python
@dataclass
class Seen:
    proposer_slots: set[tuple[Slot, ValidatorIndex]]
    aggregator_epochs: set[tuple[Epoch, ValidatorIndex]]
    # [Modified in Electra:EIP7549]
    aggregate_data_roots: dict[tuple[Root, CommitteeIndex], set[tuple[bool, ...]]]
    voluntary_exit_indices: set[ValidatorIndex]
    proposer_slashing_indices: set[ValidatorIndex]
    attester_slashing_indices: set[ValidatorIndex]
    attestation_validator_epochs: set[tuple[Epoch, ValidatorIndex]]
    sync_contribution_aggregator_slots: set[tuple[Slot, ValidatorIndex, Uint64]]
    sync_contribution_data: dict[tuple[Slot, Root, Uint64], set[tuple[bool, ...]]]
    sync_message_validator_slots: set[tuple[Slot, ValidatorIndex, Uint64]]
    bls_to_execution_change_indices: set[ValidatorIndex]
    blob_sidecar_tuples: set[tuple[Slot, ValidatorIndex, BlobIndex]]
```

> 💡 Ghi chú: `Seen` là cấu trúc lưu "những gì đã thấy" để node phát hiện và bỏ qua
> các message gossip trùng lặp. Trong Electra, khóa của `aggregate_data_roots`
> được mở rộng thành cặp `(Root, CommitteeIndex)` vì theo EIP-7549, committee
> index không còn nằm trong `AttestationData` nữa.

### Modified `compute_fork_version`

```python
def compute_fork_version(epoch: Epoch) -> Version:
    """
    Return the fork version at the given ``epoch``.
    """
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

### Modified `compute_max_request_blob_sidecars`

```python
def compute_max_request_blob_sidecars() -> Uint64:
    """
    Return the maximum number of blob sidecars in a single request.
    """
    # [Modified in Electra:EIP7691]
    return MAX_REQUEST_BLOCKS_DENEB * MAX_BLOBS_PER_BLOCK_ELECTRA
```

## The gossip domain: gossipsub

*(Miền gossip: gossipsub)*

Một số gossip mesh được nâng cấp trong Electra để hỗ trợ các kiểu dữ liệu mới.

### Topics and messages

Các topic tuân theo cùng đặc tả như ở các bản nâng cấp trước.

Topic `beacon_block` được sửa đổi để hỗ trợ thêm các block Electra.

Các topic `beacon_aggregate_and_proof` và `beacon_attestation_{subnet_id}` được
sửa đổi để hỗ trợ gossip kiểu attestation mới.

Topic `attester_slashing` được sửa đổi để hỗ trợ gossip kiểu `AttesterSlashing`
mới.

Các quy định về việc tạo, kiểm tra hợp lệ (validation) và phát tán message không
thay đổi so với tài liệu Deneb, trừ khi được ghi chú rõ ràng ở đây.

Cách tính `message-id` vẫn giữ nguyên.

#### Global topics

*(Các topic toàn cục)*

##### Modified `beacon_block`

*Ghi chú*: Hàm này được sửa đổi theo EIP-7691. Số lượng KZG commitment trong
block bị giới hạn bởi `MAX_BLOBS_PER_BLOCK_ELECTRA`.

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

    # [IGNORE] Block là block đầu tiên có signature hợp lệ nhận được cho slot và proposer này
    proposer_slot_key = (block.slot, block.proposer_index)
    if proposer_slot_key in seen.proposer_slots:
        raise GossipIgnore("block is not the first valid block for this slot and proposer")

    # [IGNORE] Block không thuộc slot tương lai
    # (MAY đưa vào hàng đợi để xử lý tại slot thích hợp)
    if is_future_slot(store, block.slot, current_time_ms):
        raise GossipIgnore("block is from a future slot")

    # [IGNORE] Block thuộc slot lớn hơn finalized slot mới nhất
    # (MAY chọn validate và lưu trữ các block như vậy cho các mục đích khác
    # -- ví dụ: phát hiện slashing, archive node, v.v.)
    finalized_slot = compute_start_slot_at_epoch(store.finalized_checkpoint.epoch)
    if block.slot <= finalized_slot:
        raise GossipIgnore("block is not from a slot greater than the latest finalized slot")

    # [IGNORE] Parent của block đã được thấy (qua gossip hoặc nguồn không phải gossip)
    # (MAY đưa vào hàng đợi cho đến khi parent được truy xuất)
    if block.parent_root not in store.blocks:
        raise GossipIgnore("block's parent has not been seen")

    parent_payload_status = PAYLOAD_STATUS_NOT_VALIDATED
    if block.parent_root in block_payload_statuses:
        parent_payload_status = block_payload_statuses[block.parent_root]

    if block.parent_root not in store.block_states:
        if parent_payload_status == PAYLOAD_STATUS_NOT_VALIDATED:
            # [REJECT] Parent của block không qua được validation và execution payload của nó ở trạng thái optimistic
            raise GossipReject("block's parent is invalid and its payload is optimistic")

        # [IGNORE] Parent của block không qua được validation và execution payload của nó đã được xử lý
        raise GossipIgnore("block's parent is invalid and its payload is processed")

    # [IGNORE] Parent của block đã qua validation nhưng execution payload của nó không hợp lệ
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

    # [REJECT] Timestamp của execution payload trong block đúng so với slot
    if execution_payload.timestamp != compute_time_at_slot(state.genesis_time, block.slot):
        raise GossipReject("incorrect execution payload timestamp")

    # [REJECT] Block thuộc slot cao hơn parent của nó
    if block.slot <= store.blocks[block.parent_root].slot:
        raise GossipReject("block is not from a higher slot than its parent")

    # [REJECT] Finalized checkpoint hiện tại là tổ tiên (ancestor) của block
    finalized_epoch = store.finalized_checkpoint.epoch
    finalized_checkpoint_block = get_checkpoint_block(store, block.parent_root, finalized_epoch)
    if finalized_checkpoint_block != store.finalized_checkpoint.root:
        raise GossipReject("finalized checkpoint is not an ancestor of block")

    # [Modified in Electra:EIP7691]
    # [REJECT] Độ dài danh sách KZG commitment nhỏ hơn hoặc bằng giới hạn
    if len(block.body.blob_kzg_commitments) > MAX_BLOBS_PER_BLOCK_ELECTRA:
        raise GossipReject("too many blob kzg commitments")

    # [REJECT] Block được đề xuất bởi đúng proposer dự kiến cho slot
    # (nếu shuffling chưa có sẵn, thay vào đó IGNORE và MAY đưa vào hàng đợi để xử lý sau)
    parent_state = store.block_states[block.parent_root].copy()
    process_slots(parent_state, block.slot)
    expected_proposer = get_beacon_proposer_index(parent_state)
    if block.proposer_index != expected_proposer:
        raise GossipReject("block proposer_index does not match expected proposer")

    # Đánh dấu block này là đã thấy
    seen.proposer_slots.add(proposer_slot_key)
```

> 💡 Ghi chú: Thay đổi duy nhất so với Deneb là điều kiện [REJECT] về số lượng
> `blob_kzg_commitments`: nay so với `MAX_BLOBS_PER_BLOCK_ELECTRA` thay vì giới
> hạn cũ của Deneb. Các điều kiện [IGNORE]/[REJECT] khác giữ nguyên.

##### Modified `beacon_aggregate_and_proof`

*Ghi chú*: Hàm này được sửa đổi theo EIP-7549. Committee index nay được mã hóa
trong `aggregate.committee_bits`, `aggregate.data.index` MUST bằng 0, và
seen-cache của gossip (bộ nhớ đệm các message đã thấy) dùng khóa là
`(hash_tree_root(aggregate.data), committee_index)`.

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
    aggregation_bits = aggregate.aggregation_bits

    # [New in Electra:EIP7549]
    # [REJECT] Data index của aggregate attestation bằng 0
    if aggregate.data.index != 0:
        raise GossipReject("aggregate data index is non-zero")

    # [New in Electra:EIP7549]
    # [REJECT] Committee bits chỉ định đúng một committee
    committee_indices = get_committee_indices(aggregate.committee_bits)
    if len(committee_indices) != 1:
        raise GossipReject("aggregate committee bits must specify exactly one committee")
    index = committee_indices[0]

    # [Modified in Electra:EIP7549]
    # [IGNORE] Chưa thấy aggregate hợp lệ nào có aggregation bits là tập cha (superset)
    aggregate_data_root = hash_tree_root(aggregate.data)
    aggregate_cache_key = (aggregate_data_root, index)
    aggregate_bits = tuple(bool(bit) for bit in aggregation_bits)
    seen_bits = seen.aggregate_data_roots.get(aggregate_cache_key, set())
    if is_non_strict_superset(seen_bits, aggregate_bits):
        raise GossipIgnore("already seen aggregate for this data")

    # [IGNORE] Đây là aggregate hợp lệ đầu tiên cho epoch và aggregator này
    aggregator_index = aggregate_and_proof.aggregator_index
    target_epoch = aggregate.data.target.epoch
    aggregator_epoch_key = (target_epoch, aggregator_index)
    if aggregator_epoch_key in seen.aggregator_epochs:
        raise GossipIgnore("already seen aggregate for this epoch and aggregator")

    # [IGNORE] Block được bỏ phiếu đã được thấy (qua gossip hoặc nguồn không phải gossip)
    # (MAY đưa vào hàng đợi cho đến khi block được truy xuất)
    block_root = aggregate.data.beacon_block_root
    if block_root not in store.blocks:
        raise GossipIgnore("block being voted for has not been seen")

    # [REJECT] Block được bỏ phiếu qua được validation
    if block_root not in store.block_states:
        raise GossipReject("block being voted for failed validation")

    state = store.block_states[get_head(store).root]

    # [REJECT] Committee index nằm trong phạm vi dự kiến
    committee_count = get_committee_count_per_slot(state, aggregate.data.target.epoch)
    if index >= committee_count:
        raise GossipReject("committee index out of range")

    # [IGNORE] Slot của aggregate attestation không thuộc slot tương lai
    # (MAY đưa vào hàng đợi để xử lý tại slot thích hợp)
    if is_future_slot(store, aggregate.data.slot, current_time_ms):
        raise GossipIgnore("aggregate slot is from a future slot")

    # [IGNORE] Epoch của aggregate attestation là epoch hiện tại hoặc epoch trước đó
    attestation_epoch = compute_epoch_at_slot(aggregate.data.slot)
    if not is_current_or_previous_epoch(store, attestation_epoch, current_time_ms):
        raise GossipIgnore("aggregate epoch is not current or previous epoch")

    # [REJECT] Epoch của aggregate attestation khớp với target của nó
    if aggregate.data.target.epoch != compute_epoch_at_slot(aggregate.data.slot):
        raise GossipReject("attestation epoch does not match target epoch")

    # [REJECT] Số aggregation bits khớp với kích thước committee
    committee = get_beacon_committee(state, aggregate.data.slot, index)
    if len(aggregation_bits) != len(committee):
        raise GossipReject("aggregation bits length does not match committee size")

    # [REJECT] Aggregate attestation có người tham gia (participants)
    attesting_indices = get_attesting_indices(state, aggregate)
    if len(attesting_indices) < 1:
        raise GossipReject("aggregate has no participants")

    # [REJECT] Selection proof chọn validator làm aggregator
    if not is_aggregator(state, aggregate.data.slot, index, aggregate_and_proof.selection_proof):
        raise GossipReject("validator is not selected as aggregator")

    # [REJECT] Aggregator là thành viên của committee
    if aggregator_index not in committee:
        raise GossipReject("aggregator is not a member of the committee")

    # [REJECT] Signature của selection proof hợp lệ
    aggregator = state.validators[aggregator_index]
    domain = get_domain(state, DOMAIN_SELECTION_PROOF, target_epoch)
    signing_root = compute_signing_root(aggregate.data.slot, domain)
    if not bls.Verify(aggregator.pubkey, signing_root, aggregate_and_proof.selection_proof):
        raise GossipReject("invalid selection proof signature")

    # [REJECT] Signature của aggregator hợp lệ
    domain = get_domain(state, DOMAIN_AGGREGATE_AND_PROOF, target_epoch)
    signing_root = compute_signing_root(aggregate_and_proof, domain)
    if not bls.Verify(aggregator.pubkey, signing_root, signed_aggregate_and_proof.signature):
        raise GossipReject("invalid aggregator signature")

    # [REJECT] Aggregate signature hợp lệ
    if not is_valid_indexed_attestation(state, get_indexed_attestation(state, aggregate)):
        raise GossipReject("invalid aggregate signature")

    # [REJECT] Target block là tổ tiên (ancestor) của LMD vote block
    checkpoint_block = get_checkpoint_block(store, block_root, aggregate.data.target.epoch)
    if checkpoint_block != aggregate.data.target.root:
        raise GossipReject("target block is not an ancestor of LMD vote block")

    # [IGNORE] Finalized checkpoint là tổ tiên (ancestor) của block
    finalized_epoch = store.finalized_checkpoint.epoch
    finalized_checkpoint_block = get_checkpoint_block(store, block_root, finalized_epoch)
    if finalized_checkpoint_block != store.finalized_checkpoint.root:
        raise GossipIgnore("finalized checkpoint is not an ancestor of block")

    # Đánh dấu aggregate này là đã thấy
    seen.aggregator_epochs.add(aggregator_epoch_key)
    if aggregate_cache_key not in seen.aggregate_data_roots:
        seen.aggregate_data_roots[aggregate_cache_key] = set()
    seen.aggregate_data_roots[aggregate_cache_key].add(aggregate_bits)
```

> 💡 Ghi chú: Nói cách khác, một aggregate hợp lệ trong Electra phải có
> `data.index == 0` và `committee_bits` bật đúng một bit (ứng với committee của
> aggregate). Vì nhiều committee khác nhau có thể có cùng `AttestationData`, khóa
> dùng để phát hiện trùng lặp phải gồm cả committee index.

##### Modified `attester_slashing`

*Ghi chú*: Hàm này được sửa đổi theo EIP-7549. Kiểu `AttesterSlashing` mới bọc
một `IndexedAttestation` có kích thước đủ chứa
`MAX_VALIDATORS_PER_COMMITTEE * MAX_COMMITTEES_PER_SLOT` attesting index (chỉ số
các validator tham gia attest); ngoài ra logic validation không thay đổi.

#### Attestation subnets

##### Modified `beacon_attestation_{subnet_id}`

*Ghi chú*: Hàm này được sửa đổi theo EIP-7549. Topic này nay truyền các đối tượng
`SingleAttestation`: index của validator thực hiện attest được mang trực tiếp
trong message, committee index được đọc từ `attestation.committee_index`, và
`attestation.data.index` MUST bằng 0.

```python
def validate_beacon_attestation_gossip(
    seen: Seen,
    store: Store,
    # [Modified in Electra:EIP7549]
    attestation: SingleAttestation,
    current_time_ms: Uint64,
    subnet_id: SubnetID,
) -> None:
    """
    Validate a SingleAttestation for gossip propagation on a subnet.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    data = attestation.data
    # [Modified in Electra:EIP7549]
    committee_index = attestation.committee_index
    attester_index = attestation.attester_index
    target_epoch = data.target.epoch

    # [Modified in Electra:EIP7549]
    # [IGNORE] Chưa thấy attestation hợp lệ nào khác cho target epoch và validator này
    attestation_epoch_key = (target_epoch, attester_index)
    if attestation_epoch_key in seen.attestation_validator_epochs:
        raise GossipIgnore("already seen attestation for this epoch and validator")

    # [New in Electra:EIP7549]
    # [REJECT] Data index của attestation bằng 0
    if data.index != 0:
        raise GossipReject("attestation data index is non-zero")

    # [IGNORE] Block được bỏ phiếu đã được thấy (qua gossip hoặc nguồn không phải gossip)
    # (MAY đưa vào hàng đợi cho đến khi block được truy xuất)
    block_root = data.beacon_block_root
    if block_root not in store.blocks:
        raise GossipIgnore("block being voted for has not been seen")

    # [REJECT] Block được bỏ phiếu qua được validation
    if block_root not in store.block_states:
        raise GossipReject("block being voted for failed validation")

    state = store.block_states[get_head(store).root]

    # [REJECT] Committee index nằm trong phạm vi dự kiến
    committees_per_slot = get_committee_count_per_slot(state, target_epoch)
    if committee_index >= committees_per_slot:
        raise GossipReject("committee index out of range")

    # [REJECT] Attestation thuộc đúng subnet
    expected_subnet = compute_subnet_for_attestation(
        committees_per_slot, data.slot, committee_index
    )
    if expected_subnet != subnet_id:
        raise GossipReject("attestation is for wrong subnet")

    # [IGNORE] Slot của attestation không thuộc slot tương lai
    # (MAY đưa vào hàng đợi để xử lý tại slot thích hợp)
    if is_future_slot(store, data.slot, current_time_ms):
        raise GossipIgnore("attestation slot is from a future slot")

    # [IGNORE] Epoch của attestation là epoch hiện tại hoặc epoch trước đó
    attestation_epoch = compute_epoch_at_slot(data.slot)
    if not is_current_or_previous_epoch(store, attestation_epoch, current_time_ms):
        raise GossipIgnore("attestation epoch is not current or previous epoch")

    # [REJECT] Epoch của attestation khớp với target của nó
    if target_epoch != compute_epoch_at_slot(data.slot):
        raise GossipReject("attestation epoch does not match target epoch")

    # [New in Electra:EIP7549]
    # [REJECT] Attester là thành viên của committee
    committee = get_beacon_committee(state, data.slot, committee_index)
    if attester_index not in committee:
        raise GossipReject("attester is not a member of the committee")

    # [Modified in Electra:EIP7549]
    # [REJECT] Signature của attestation hợp lệ
    attester = state.validators[attester_index]
    domain = get_domain(state, DOMAIN_BEACON_ATTESTER, target_epoch)
    signing_root = compute_signing_root(data, domain)
    if not bls.Verify(attester.pubkey, signing_root, attestation.signature):
        raise GossipReject("invalid attestation signature")

    # [REJECT] Target block của attestation là tổ tiên (ancestor) của LMD vote block
    target_checkpoint_block = get_checkpoint_block(store, block_root, target_epoch)
    if target_checkpoint_block != data.target.root:
        raise GossipReject("target block is not an ancestor of LMD vote block")

    # [IGNORE] finalized_checkpoint hiện tại là tổ tiên (ancestor) của block
    finalized_epoch = store.finalized_checkpoint.epoch
    finalized_checkpoint_block = get_checkpoint_block(store, block_root, finalized_epoch)
    if finalized_checkpoint_block != store.finalized_checkpoint.root:
        raise GossipIgnore("finalized checkpoint is not an ancestor of block")

    # Đánh dấu attestation này là đã thấy
    seen.attestation_validator_epochs.add(attestation_epoch_key)
```

> 💡 Ghi chú: Khác với `Attestation` (dùng bitfield `aggregation_bits`),
> `SingleAttestation` chỉ đại diện cho đúng một validator và mang trực tiếp
> `attester_index`. Vì vậy node nhận dùng `attester_index` để kiểm tra trùng lặp
> theo `(target_epoch, attester_index)`, kiểm tra validator đó có thuộc
> committee hay không, và xác minh chữ ký bằng public key của validator đó.

#### Blob subnets

##### Modified `blob_sidecar_{subnet_id}`

*Ghi chú*: Hàm này được sửa đổi theo EIP-7691. Index của sidecar bị giới hạn bởi
`MAX_BLOBS_PER_BLOCK_ELECTRA`.

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

    # [IGNORE] Sidecar là sidecar đầu tiên cho bộ (tuple)
    # (block_header.slot, block_header.proposer_index, blob_sidecar.index)
    sidecar_tuple = (block_header.slot, block_header.proposer_index, blob_sidecar.index)
    if sidecar_tuple in seen.blob_sidecar_tuples:
        raise GossipIgnore("already seen blob sidecar from this proposer for this slot and index")

    # [Modified in Electra:EIP7691]
    # [REJECT] Index của sidecar nhất quán với MAX_BLOBS_PER_BLOCK_ELECTRA
    if blob_sidecar.index >= MAX_BLOBS_PER_BLOCK_ELECTRA:
        raise GossipReject("blob index out of range")

    # [REJECT] Sidecar thuộc đúng subnet
    if compute_subnet_for_blob_sidecar(blob_sidecar.index) != subnet_id:
        raise GossipReject("blob sidecar is for wrong subnet")

    # [IGNORE] Sidecar không thuộc slot tương lai
    # (MAY đưa vào hàng đợi để xử lý tại slot thích hợp)
    if is_future_slot(store, block_header.slot, current_time_ms):
        raise GossipIgnore("blob sidecar is from a future slot")

    # [IGNORE] Sidecar thuộc slot lớn hơn finalized slot mới nhất
    finalized_slot = compute_start_slot_at_epoch(store.finalized_checkpoint.epoch)
    if block_header.slot <= finalized_slot:
        raise GossipIgnore("blob sidecar is not from a slot greater than the latest finalized slot")

    # [IGNORE] Parent của block của sidecar đã được thấy
    # (MAY đưa vào hàng đợi để xử lý khi parent block được truy xuất)
    parent_root = block_header.parent_root
    if parent_root not in store.blocks:
        raise GossipIgnore("blob sidecar's parent has not been seen")

    # [REJECT] Parent của block của sidecar qua được validation
    if parent_root not in store.block_states:
        raise GossipReject("blob sidecar's parent failed validation")

    state = store.block_states[get_head(store).root]

    # [REJECT] Proposer index là một validator index hợp lệ
    if block_header.proposer_index >= len(state.validators):
        raise GossipReject("proposer index out of range")

    # [REJECT] Signature của proposer trong blob_sidecar.signed_block_header hợp lệ
    proposer = state.validators[block_header.proposer_index]
    domain = get_domain(state, DOMAIN_BEACON_PROPOSER, compute_epoch_at_slot(block_header.slot))
    signing_root = compute_signing_root(block_header, domain)
    if not bls.Verify(proposer.pubkey, signing_root, blob_sidecar.signed_block_header.signature):
        raise GossipReject("invalid proposer signature on blob sidecar block header")

    # [REJECT] Sidecar thuộc slot cao hơn parent của block của sidecar
    if block_header.slot <= store.blocks[parent_root].slot:
        raise GossipReject("blob sidecar is not from a higher slot than its parent")

    # [REJECT] finalized_checkpoint hiện tại là tổ tiên (ancestor) của block của sidecar
    finalized_epoch = store.finalized_checkpoint.epoch
    finalized_checkpoint_block = get_checkpoint_block(store, parent_root, finalized_epoch)
    if finalized_checkpoint_block != store.finalized_checkpoint.root:
        raise GossipReject("finalized checkpoint is not an ancestor of blob sidecar's block")

    # [REJECT] Inclusion proof của sidecar hợp lệ theo kiểm tra của verify_blob_sidecar_inclusion_proof
    if not verify_blob_sidecar_inclusion_proof(blob_sidecar):
        raise GossipReject("invalid blob sidecar inclusion proof")

    # [REJECT] Blob của sidecar hợp lệ theo kiểm tra của verify_blob_kzg_proof
    if not kzg.verify_blob_kzg_proof(
        blob_sidecar.blob, blob_sidecar.kzg_commitment, blob_sidecar.kzg_proof
    ):
        raise GossipReject("invalid blob kzg proof")

    # [REJECT] Sidecar được đề xuất bởi đúng proposer_index dự kiến
    # (nếu shuffling chưa có sẵn, thay vào đó IGNORE và MAY đưa vào hàng đợi để xử lý sau)
    parent_state = store.block_states[parent_root].copy()
    process_slots(parent_state, block_header.slot)
    expected_proposer = get_beacon_proposer_index(parent_state)
    if block_header.proposer_index != expected_proposer:
        raise GossipReject("blob sidecar proposer_index does not match expected proposer")

    # Đánh dấu blob sidecar này là đã thấy
    seen.blob_sidecar_tuples.add(sidecar_tuple)
```

## The Req/Resp domain

*(Miền Req/Resp - yêu cầu/phản hồi)*

### Messages

#### BeaconBlocksByRange v2

**Protocol ID:** `/eth2/beacon_chain/req/beacon_blocks_by_range/2/`

Fork-digest của Electra được bổ sung vào enum `context` để chỉ định kiểu beacon
block của Electra.

<!-- eth_consensus_specs: skip -->

| `fork_version`           | Chunk SSZ type                |
| ------------------------ | ----------------------------- |
| `GENESIS_FORK_VERSION`   | `phase0.SignedBeaconBlock`    |
| `ALTAIR_FORK_VERSION`    | `altair.SignedBeaconBlock`    |
| `BELLATRIX_FORK_VERSION` | `bellatrix.SignedBeaconBlock` |
| `CAPELLA_FORK_VERSION`   | `capella.SignedBeaconBlock`   |
| `DENEB_FORK_VERSION`     | `deneb.SignedBeaconBlock`     |
| `ELECTRA_FORK_VERSION`   | `electra.SignedBeaconBlock`   |

#### BeaconBlocksByRoot v2

**Protocol ID:** `/eth2/beacon_chain/req/beacon_blocks_by_root/2/`

Fork-digest của Electra được bổ sung vào enum `context` để chỉ định kiểu beacon
block của Electra.

<!-- eth_consensus_specs: skip -->

| `fork_version`           | Chunk SSZ type                |
| ------------------------ | ----------------------------- |
| `GENESIS_FORK_VERSION`   | `phase0.SignedBeaconBlock`    |
| `ALTAIR_FORK_VERSION`    | `altair.SignedBeaconBlock`    |
| `BELLATRIX_FORK_VERSION` | `bellatrix.SignedBeaconBlock` |
| `CAPELLA_FORK_VERSION`   | `capella.SignedBeaconBlock`   |
| `DENEB_FORK_VERSION`     | `deneb.SignedBeaconBlock`     |
| `ELECTRA_FORK_VERSION`   | `electra.SignedBeaconBlock`   |

#### BlobSidecarsByRange v1

**Protocol ID:** `/eth2/beacon_chain/req/blob_sidecars_by_range/1/`

*[Modified in Electra:EIP7691]*

*Ghi chú*: Hàm `compute_max_request_blob_sidecars` đã được sửa đổi, điều này ảnh
hưởng đến logic của request, response và validation.

#### BlobSidecarsByRoot v1

**Protocol ID:** `/eth2/beacon_chain/req/blob_sidecars_by_root/1/`

*[Modified in Electra:EIP7691]*

*Ghi chú*: Hàm `compute_max_request_blob_sidecars` đã được sửa đổi, điều này ảnh
hưởng đến logic của request, response và validation.
