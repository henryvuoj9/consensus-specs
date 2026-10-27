# Gloas -- Networking

*Lưu ý*: Tài liệu này vẫn đang trong quá trình hoàn thiện (work-in-progress), dành cho các nhà nghiên cứu và người triển khai client.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Presets](#presets)
  - [Type-specific SSZ bounds](#type-specific-ssz-bounds)
- [Configs](#configs)
- [Types](#types)
  - [Modified `DataColumn`](#modified-datacolumn)
  - [Modified `KZGProofs`](#modified-kzgproofs)
  - [New `ExecutionPayloadEnvelopeRoots`](#new-executionpayloadenveloperoots)
  - [New `SignedExecutionPayloadEnvelopes`](#new-signedexecutionpayloadenvelopes)
- [Containers](#containers)
  - [Modified `DataColumnSidecar`](#modified-datacolumnsidecar)
  - [New `ProposerPreferences`](#new-proposerpreferences)
  - [New `SignedProposerPreferences`](#new-signedproposerpreferences)
- [Helpers](#helpers)
  - [Modified `Seen`](#modified-seen)
  - [Modified `compute_fork_version`](#modified-compute_fork_version)
  - [Modified `compute_min_epochs_for_block_requests`](#modified-compute_min_epochs_for_block_requests)
  - [Modified `verify_data_column_sidecar_kzg_proofs`](#modified-verify_data_column_sidecar_kzg_proofs)
  - [Modified `verify_data_column_sidecar`](#modified-verify_data_column_sidecar)
  - [New `compute_max_data_column_sidecar_size`](#new-compute_max_data_column_sidecar_size)
  - [New `is_current_or_next_slot`](#new-is_current_or_next_slot)
  - [New `is_past_slot`](#new-is_past_slot)
  - [New `is_gas_limit_target_compatible`](#new-is_gas_limit_target_compatible)
  - [New `is_bid_compatible_with_head`](#new-is_bid_compatible_with_head)
  - [New `verify_attestation_payload_status`](#new-verify_attestation_payload_status)
  - [New `verify_block_body_operation_limits`](#new-verify_block_body_operation_limits)
  - [New `verify_execution_requests_limits`](#new-verify_execution_requests_limits)
- [The gossip domain: gossipsub](#the-gossip-domain-gossipsub)
  - [Topics and messages](#topics-and-messages)
    - [Global topics](#global-topics)
      - [Modified `beacon_block`](#modified-beacon_block)
      - [Modified `beacon_aggregate_and_proof`](#modified-beacon_aggregate_and_proof)
      - [New `execution_payload`](#new-execution_payload)
      - [New `payload_attestation_message`](#new-payload_attestation_message)
      - [New `execution_payload_bid`](#new-execution_payload_bid)
      - [New `proposer_preferences`](#new-proposer_preferences)
    - [Attestation subnets](#attestation-subnets)
      - [Modified `beacon_attestation_{subnet_id}`](#modified-beacon_attestation_subnet_id)
    - [Blob subnets](#blob-subnets)
      - [Modified `data_column_sidecar_{subnet_id}`](#modified-data_column_sidecar_subnet_id)
- [The Req/Resp domain](#the-reqresp-domain)
  - [Messages](#messages)
    - [BeaconBlocksByRange v2](#beaconblocksbyrange-v2)
    - [BeaconBlocksByRoot v2](#beaconblocksbyroot-v2)
    - [ExecutionPayloadEnvelopesByRange v1](#executionpayloadenvelopesbyrange-v1)
    - [ExecutionPayloadEnvelopesByRoot v1](#executionpayloadenvelopesbyroot-v1)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này chứa đặc tả networking của consensus layer cho bản nâng cấp Gloas.

Đặc tả các thay đổi được trình bày theo cùng định dạng với đặc tả network của các
bản nâng cấp trước, và mặc định người đọc đã nắm các đặc tả đó (chúng là điều
kiện tiên quyết).

> 💡 Ghi chú: Thay đổi trọng tâm của Gloas là EIP-7732 (ePBS - enshrined
> Proposer-Builder Separation): execution payload được tách khỏi beacon block và
> được builder công bố riêng dưới dạng `SignedExecutionPayloadEnvelope`. Do đó
> xuất hiện thêm các topic gossip mới (bid, envelope, payload attestation,
> proposer preferences) và các message Req/Resp mới để tải envelope.

## Presets

### Type-specific SSZ bounds

*[New in Gloas:EIP7688]*

Các hằng số dưới đây thay thế
[giới hạn kích thước SSZ theo từng kiểu](../phase0/p2p-interface.md#what-are-ssz-type-size-bounds)
cho các message libp2p có kích thước thay đổi tương ứng. Giới hạn cho
`DataColumnSidecar` được tính bởi hàm `compute_max_data_column_sidecar_size()`.

> 💡 Ghi chú: Với EIP-7688, một số kiểu chuyển sang dùng `ProgressiveList` (không
> có giới hạn độ dài cố định trong kiểu), nên không thể suy ra kích thước tối đa
> từ định nghĩa SSZ. Vì vậy spec định nghĩa tường minh các giới hạn này để client
> dùng khi kiểm tra kích thước message trên mạng.

| Name                                    | Value                         |
| --------------------------------------- | ----------------------------- |
| `MAX_SIGNED_AGGREGATE_AND_PROOF_SIZE`   | `Uint64(16829)` (= ~16 KiB)   |
| `MAX_ATTESTER_SLASHING_SIZE`            | `Uint64(2097616)` (= ~2 MiB)  |
| `MAX_SIGNED_EXECUTION_PAYLOAD_BID_SIZE` | `Uint64(196932)` (= ~192 KiB) |

## Configs

| Name                   | Value                  |
| ---------------------- | ---------------------- |
| `MAX_REQUEST_PAYLOADS` | `Uint64(2**7)` (= 128) |

## Types

### Modified `DataColumn`

```python
# [Modified in Gloas:EIP7688]
class DataColumn(ProgressiveList[Cell]):
    """
    A column of the extended blob data matrix, with at most one cell per blob.
    """
```

### Modified `KZGProofs`

```python
# [Modified in Gloas:EIP7688]
class KZGProofs(ProgressiveList[KZGProof]):
    """
    The KZG cell proofs of the cells held by a data column.
    """
```

### New `ExecutionPayloadEnvelopeRoots`

```python
class ExecutionPayloadEnvelopeRoots(List[Root]):
    """
    The beacon block roots of the payload envelopes requested in an
    ``ExecutionPayloadEnvelopesByRoot`` request.
    """

    LIMIT = MAX_REQUEST_PAYLOADS
```

### New `SignedExecutionPayloadEnvelopes`

```python
class SignedExecutionPayloadEnvelopes(List[SignedExecutionPayloadEnvelope]):
    """
    Signed execution payload envelopes returned in an
    ``ExecutionPayloadEnvelopesByRange`` or
    ``ExecutionPayloadEnvelopesByRoot`` response.
    """

    LIMIT = MAX_REQUEST_PAYLOADS
```

## Containers

### Modified `DataColumnSidecar`

*Lưu ý*: Các field `signed_block_header`, `kzg_commitments` và
`kzg_commitments_inclusion_proof` đã bị loại bỏ khỏi `DataColumnSidecar` trong
Gloas, vì việc xác minh header và inclusion proof không còn cần thiết nữa. Các
KZG commitment giờ nằm tại
`block.body.signed_execution_payload_bid.message.blob_kzg_commitments`, trong đó
`block` là `BeaconBlock` ứng với `beacon_block_root`.

> 💡 Ghi chú: Nói cách khác, sidecar giờ chỉ tham chiếu tới block qua `slot` và
> `beacon_block_root`; để xác minh KZG proof, client phải lấy danh sách
> commitment từ bid trong block tương ứng (xem các hàm
> `verify_data_column_sidecar*` bên dưới, nhận thêm tham số `kzg_commitments`).

```python
class DataColumnSidecar(Container):
    index: ColumnIndex
    # [Modified in Gloas:EIP7688]
    column: DataColumn
    # [Modified in Gloas:EIP7732]
    # Đã loại bỏ `kzg_commitments`
    # [Modified in Gloas:EIP7688]
    kzg_proofs: KZGProofs
    # [Modified in Gloas:EIP7732]
    # Đã loại bỏ `signed_block_header`
    # [Modified in Gloas:EIP7732]
    # Đã loại bỏ `kzg_commitments_inclusion_proof`
    # [New in Gloas:EIP7732]
    slot: Slot
    # [New in Gloas:EIP7732]
    beacon_block_root: Root
```

### New `ProposerPreferences`

*[New in Gloas:EIP7732]*

```python
class ProposerPreferences(Container):
    dependent_root: Root
    proposal_slot: Slot
    validator_index: ValidatorIndex
    fee_recipient: ExecutionAddress
    target_gas_limit: Uint64
```

### New `SignedProposerPreferences`

*[New in Gloas:EIP7732]*

```python
class SignedProposerPreferences(Container):
    message: ProposerPreferences
    signature: BLSSignature
```

## Helpers

### Modified `Seen`

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
    # [Modified in Gloas:EIP7732]
    data_column_sidecar_tuples: set[tuple[Root, ColumnIndex]]
    # [Modified in Gloas:EIP7732]
    # Đã loại bỏ `partial_data_column_headers`
    # [New in Gloas:EIP7732]
    execution_payloads: dict[Hash32, ExecutionPayload]
    # [New in Gloas:EIP7732]
    execution_payload_envelopes: set[tuple[Root, BuilderIndex]]
    # [New in Gloas:EIP7732]
    payload_attestation_validators: set[tuple[Slot, ValidatorIndex]]
    # [New in Gloas:EIP7732]
    execution_payload_bids: set[tuple[Slot, Hash32, Root, BuilderIndex]]
    # [New in Gloas:EIP7732]
    best_execution_payload_bid: dict[tuple[Slot, Hash32, Root], Gwei]
    # [New in Gloas:EIP7732]
    proposer_preferences: dict[tuple[Slot, Root], ProposerPreferences]
```

### Modified `compute_fork_version`

```python
def compute_fork_version(epoch: Epoch) -> Version:
    """
    Return the fork version at the given ``epoch``.
    """
    if epoch >= GLOAS_FORK_EPOCH:
        return GLOAS_FORK_VERSION
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

### Modified `compute_min_epochs_for_block_requests`

*Lưu ý*: `compute_min_epochs_for_block_requests` được sửa đổi để dùng cùng công
thức số học với `compute_weak_subjectivity_period` trong
[hướng dẫn weak subjectivity](./weak-subjectivity.md). Trong trường hợp xấu nhất
khi tập validator rất lớn, activation churn (đã bị giới hạn trần) là không đáng
kể, nên chỉ còn lại exit churn (trọng số 2/3) và consolidation churn (trọng số
1).

> 💡 Ghi chú: Kết quả là số epoch tối thiểu mà một node phải phục vụ block cho
> peer: bằng `MIN_VALIDATOR_WITHDRAWABILITY_DELAY` cộng một nửa của "trung bình
> điều hòa có trọng số" giữa hai quotient churn ở trên.

```python
def compute_min_epochs_for_block_requests() -> Epoch:
    """
    Return the minimum epoch range over which a node must serve blocks.
    """
    # [Modified in Gloas:EIP8061]
    numerator = 3 * CHURN_LIMIT_QUOTIENT_GLOAS * CONSOLIDATION_CHURN_LIMIT_QUOTIENT
    denominator = 2 * CONSOLIDATION_CHURN_LIMIT_QUOTIENT + 3 * CHURN_LIMIT_QUOTIENT_GLOAS
    return MIN_VALIDATOR_WITHDRAWABILITY_DELAY + (numerator // denominator) // 2
```

### Modified `verify_data_column_sidecar_kzg_proofs`

```python
def verify_data_column_sidecar_kzg_proofs(
    sidecar: DataColumnSidecar,
    # [New in Gloas:EIP7732]
    kzg_commitments: BlobKZGCommitments,
) -> bool:
    """
    Verify if the KZG proofs are correct.
    """
    # Chỉ số column đồng thời cũng là chỉ số cell
    cell_indices = [CellIndex(sidecar.index)] * len(sidecar.column)

    # Xác minh theo lô (batch) rằng các cell khớp với commitment và proof tương ứng
    return kzg.verify_cell_kzg_proof_batch(
        # [Modified in Gloas:EIP7732]
        commitments_bytes=kzg_commitments,
        cell_indices=cell_indices,
        cells=sidecar.column,
        proofs_bytes=sidecar.kzg_proofs,
    )
```

### Modified `verify_data_column_sidecar`

```python
def verify_data_column_sidecar(
    sidecar: DataColumnSidecar,
    # [New in Gloas:EIP7732]
    kzg_commitments: BlobKZGCommitments,
) -> bool:
    """
    Verify if the data column sidecar is valid.
    """
    # Chỉ số của sidecar phải nằm trong khoảng hợp lệ
    if sidecar.index >= NUMBER_OF_COLUMNS:
        return False

    # [Modified in Gloas:EIP7732]
    # Sidecar ứng với 0 blob là không hợp lệ
    if len(sidecar.column) == 0:
        return False

    # [Modified in Gloas:EIP7732]
    # Độ dài column phải bằng số lượng commitment
    if len(sidecar.column) != len(kzg_commitments):
        return False

    # Độ dài column phải bằng số lượng proof
    if len(sidecar.column) != len(sidecar.kzg_proofs):
        return False

    return True
```

### New `compute_max_data_column_sidecar_size`

```python
def compute_max_data_column_sidecar_size() -> Uint64:
    """
    Return the maximum size of a serialized ``DataColumnSidecar`` computed
    using the largest ``max_blobs_per_block`` value from the blob schedule,
    regardless of whether or not that is the current ``max_blobs_per_block``.
    """
    max_blobs = MAX_BLOBS_PER_BLOCK_ELECTRA
    for entry in BLOB_SCHEDULE:
        max_blobs = max(max_blobs, entry["MAX_BLOBS_PER_BLOCK"])

    sidecar = DataColumnSidecar(
        index=ColumnIndex(),
        column=DataColumn(data=[Cell()] * max_blobs),
        kzg_proofs=KZGProofs(data=[KZGProof()] * max_blobs),
        slot=Slot(),
        beacon_block_root=Root(),
    )
    return Uint64(len(ssz_serialize(sidecar)))
```

### New `is_current_or_next_slot`

```python
def is_current_or_next_slot(
    store: Store,
    slot: Slot,
    current_time_ms: Uint64,
) -> bool:
    """
    Check if the given slot is the current slot or the next slot
    (with MAXIMUM_GOSSIP_CLOCK_DISPARITY allowance).
    """
    is_current = is_current_slot(store, slot, current_time_ms)
    is_next = is_current_slot(store, slot - 1, current_time_ms)
    return is_current or is_next
```

### New `is_past_slot`

```python
def is_past_slot(
    store: Store,
    slot: Slot,
    current_time_ms: Uint64,
) -> bool:
    """
    Check if the given slot is in the past
    (with MAXIMUM_GOSSIP_CLOCK_DISPARITY allowance).
    """
    slot_time_ms = compute_time_at_slot_ms(store.genesis_time_ms, slot)
    return current_time_ms > slot_time_ms + MAXIMUM_GOSSIP_CLOCK_DISPARITY
```

### New `is_gas_limit_target_compatible`

```python
def is_gas_limit_target_compatible(
    parent_gas_limit: Uint64, gas_limit: Uint64, target_gas_limit: Uint64
) -> bool:
    """
    Check if ``gas_limit`` is compatible with ``target_gas_limit`` under the
    EIP-1559 transition rule from ``parent_gas_limit``.
    """
    max_gas_limit_difference = saturating_sub(parent_gas_limit // 1024, 1)
    min_gas_limit = parent_gas_limit - max_gas_limit_difference
    max_gas_limit = parent_gas_limit + max_gas_limit_difference

    if target_gas_limit < min_gas_limit:
        return gas_limit == min_gas_limit
    if target_gas_limit > max_gas_limit:
        return gas_limit == max_gas_limit
    return gas_limit == target_gas_limit
```

### New `is_bid_compatible_with_head`

```python
def is_bid_compatible_with_head(store: Store, bid: ExecutionPayloadBid) -> bool:
    """
    Check if ``bid`` is compatible with the head branch.
    """
    head_node = get_head(store)
    head_block = store.blocks[head_node.root]
    head_bid = head_block.body.signed_execution_payload_bid.message

    builds_on_parent_block = bid.parent_block_root == head_block.parent_root
    builds_on_parent_payload = bid.parent_block_hash == head_bid.parent_block_hash

    if builds_on_parent_block and builds_on_parent_payload:
        return True

    if bid.parent_block_root != head_node.root:
        return False

    builds_on_head_payload = bid.parent_block_hash == head_bid.block_hash

    if should_build_on_full(store, head_node, bid.slot):
        return builds_on_head_payload

    return builds_on_parent_payload
```

### New `verify_attestation_payload_status`

```python
def verify_attestation_payload_status(
    store: Store,
    data: AttestationData,
    block_payload_statuses: dict[Root, PayloadValidationStatus],
) -> None:
    """
    Verify that the attested payload status is consistent with the block's payload.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    block_root = data.beacon_block_root
    block = store.blocks[block_root]

    # [REJECT] Với attestation cùng slot với block, payload chưa thể có mặt
    if block.slot == data.slot and data.index != 0:
        raise GossipReject("same-slot attestation must attest with index 0")

    if data.index != 1:
        return

    # [IGNORE] Execution payload envelope tương ứng đã được thấy và xác minh
    # (MAY đưa attestation vào hàng đợi để xử lý khi đã lấy được payload, và
    # SHOULD yêu cầu payload envelope qua ExecutionPayloadEnvelopesByRoot
    # với data.beacon_block_root)
    if not is_payload_verified(store, block_root):
        raise GossipIgnore("execution payload envelope has not been seen")

    # [IGNORE] Execution payload được attest vẫn đang ở trạng thái optimistic (chưa được EL xác thực)
    payload_status = block_payload_statuses.get(block_root, PAYLOAD_STATUS_NOT_VALIDATED)
    if payload_status == PAYLOAD_STATUS_NOT_VALIDATED:
        raise GossipIgnore("attested payload is optimistic")

    # [REJECT] Execution payload được attest đã được xử lý và không hợp lệ
    if payload_status == PAYLOAD_STATUS_INVALIDATED:
        raise GossipReject("attested payload is invalid")
```

### New `verify_block_body_operation_limits`

*Lưu ý*: Các kiểm tra này MAY được thực hiện ngay khi deserialize `BeaconBlockBody`.

```python
def verify_block_body_operation_limits(body: BeaconBlockBody) -> None:
    """
    Verify that each block body operation count is within its limit.
    Raises GossipReject on validation failure.
    """
    # [REJECT] Số lượng proposer slashing nằm trong giới hạn
    if len(body.proposer_slashings) > MAX_PROPOSER_SLASHINGS:
        raise GossipReject("too many proposer slashings")

    # [REJECT] Số lượng attester slashing nằm trong giới hạn
    if len(body.attester_slashings) > MAX_ATTESTER_SLASHINGS_ELECTRA:
        raise GossipReject("too many attester slashings")

    # [REJECT] Số lượng attestation nằm trong giới hạn
    if len(body.attestations) > MAX_ATTESTATIONS_ELECTRA:
        raise GossipReject("too many attestations")

    # [REJECT] Block không chứa deposit nào
    if len(body.deposits) != 0:
        raise GossipReject("block must not contain deposits")

    # [REJECT] Số lượng voluntary exit nằm trong giới hạn
    if len(body.voluntary_exits) > MAX_VOLUNTARY_EXITS:
        raise GossipReject("too many voluntary exits")

    # [REJECT] Số lượng BLS-to-execution change nằm trong giới hạn
    if len(body.bls_to_execution_changes) > MAX_BLS_TO_EXECUTION_CHANGES:
        raise GossipReject("too many bls to execution changes")

    # [REJECT] Số lượng payload attestation nằm trong giới hạn
    if len(body.payload_attestations) > MAX_PAYLOAD_ATTESTATIONS:
        raise GossipReject("too many payload attestations")
```

### New `verify_execution_requests_limits`

*Lưu ý*: Các kiểm tra này MAY được thực hiện ngay khi deserialize `ExecutionRequests`.

```python
def verify_execution_requests_limits(execution_requests: ExecutionRequests) -> None:
    """
    Verify that each execution request count is within its limit.
    Raises GossipReject on validation failure.
    """
    # [REJECT] Số lượng withdrawal request nằm trong giới hạn
    if len(execution_requests.withdrawals) > MAX_WITHDRAWAL_REQUESTS_PER_PAYLOAD:
        raise GossipReject("too many withdrawal requests")

    # [REJECT] Số lượng consolidation request nằm trong giới hạn
    if len(execution_requests.consolidations) > MAX_CONSOLIDATION_REQUESTS_PER_PAYLOAD:
        raise GossipReject("too many consolidation requests")

    # [REJECT] Số lượng builder deposit request nằm trong giới hạn
    if len(execution_requests.builder_deposits) > MAX_BUILDER_DEPOSIT_REQUESTS_PER_PAYLOAD:
        raise GossipReject("too many builder deposit requests")

    # [REJECT] Số lượng builder exit request nằm trong giới hạn
    if len(execution_requests.builder_exits) > MAX_BUILDER_EXIT_REQUESTS_PER_PAYLOAD:
        raise GossipReject("too many builder exit requests")
```

## The gossip domain: gossipsub

Một số gossip mesh được nâng cấp trong Gloas để hỗ trợ các kiểu dữ liệu mới/đã sửa đổi.

### Topics and messages

Các topic tuân theo cùng đặc tả như ở các bản nâng cấp trước.

Topic `beacon_block` được cập nhật để hỗ trợ kiểu message đã sửa đổi:

| Name           | Message Type        |
| -------------- | ------------------- |
| `beacon_block` | `SignedBeaconBlock` |

Các topic mới cùng với kiểu của field `data` trong gossipsub message được liệt
kê trong bảng sau:

| Name                          | Message Type                     |
| ----------------------------- | -------------------------------- |
| `execution_payload_bid`       | `SignedExecutionPayloadBid`      |
| `execution_payload`           | `SignedExecutionPayloadEnvelope` |
| `payload_attestation_message` | `PayloadAttestationMessage`      |
| `proposer_preferences`        | `SignedProposerPreferences`      |

#### Global topics

##### Modified `beacon_block`

*Ghi chú*: Hàm này được sửa đổi theo EIP-7732. Execution payload không còn
nằm bên trong `BeaconBlock` nữa. Do đó, mọi bước kiểm tra liên quan tới
`block.body.execution_payload` đều bị loại bỏ và thay bằng các bước kiểm tra
bid nằm tại `block.body.signed_execution_payload_bid.message`.

> 💡 Ghi chú: Trong Gloas (ePBS), block chỉ chứa bid (cam kết của builder về
> payload), còn bản thân payload được gửi riêng qua topic `execution_payload`.
> Vì vậy khi gossip block, node chỉ kiểm tra tính nhất quán của bid (parent,
> số lượng blob KZG commitment, `parent_block_hash`...), chưa kiểm tra payload.

```python
def validate_beacon_block_gossip(
    seen: Seen,
    store: Store,
    signed_beacon_block: SignedBeaconBlock,
    current_time_ms: Uint64,
    # [Modified in Gloas:EIP7732]
    # Removed `block_payload_statuses`
) -> None:
    """
    Validate a SignedBeaconBlock for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    block = signed_beacon_block.message
    bid = block.body.signed_execution_payload_bid.message

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

    # [New in Gloas:EIP7688]
    # [REJECT] Số lượng các operation trong block body nằm trong giới hạn tương ứng
    verify_block_body_operation_limits(block.body)

    # [New in Gloas:EIP7688]
    # [REJECT] Số lượng parent execution request nằm trong giới hạn tương ứng
    verify_execution_requests_limits(block.body.parent_execution_requests)

    # [IGNORE] Parent của block đã được thấy (qua gossip hoặc nguồn không phải gossip)
    # (MAY đưa vào hàng đợi cho đến khi parent được truy xuất)
    if block.parent_root not in store.blocks:
        raise GossipIgnore("block's parent has not been seen")

    # [REJECT] Parent của block qua được validation
    if block.parent_root not in store.block_states:
        raise GossipReject("block's parent is invalid")

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

    # [New in Gloas:EIP7732]
    # [IGNORE] Nếu parent block là full, parent payload phải hợp lệ
    # (MAY đưa vào hàng đợi cho đến khi parent payload được xác minh)
    if is_parent_node_full(store, block):
        if not is_payload_verified(store, block.parent_root):
            raise GossipIgnore("parent payload is not verified")

    # [REJECT] Block thuộc slot cao hơn parent của nó
    if block.slot <= store.blocks[block.parent_root].slot:
        raise GossipReject("block is not from a higher slot than its parent")

    # [REJECT] Finalized checkpoint hiện tại là tổ tiên (ancestor) của block
    finalized_epoch = store.finalized_checkpoint.epoch
    finalized_checkpoint_block = get_checkpoint_block(store, block.parent_root, finalized_epoch)
    if finalized_checkpoint_block != store.finalized_checkpoint.root:
        raise GossipReject("finalized checkpoint is not an ancestor of block")

    # [Modified in Gloas:EIP7732]
    # [REJECT] Số lượng blob KZG commitment của bid nằm trong giới hạn theo epoch
    max_blobs = get_blob_parameters(compute_epoch_at_slot(block.slot)).max_blobs_per_block
    if len(bid.blob_kzg_commitments) > max_blobs:
        raise GossipReject("too many blob kzg commitments")

    # [Modified in Gloas:EIP7732]
    # [REJECT] Parent của bid trùng với parent của block
    if bid.parent_block_root != block.parent_root:
        raise GossipReject("bid's parent does not equal block's parent")

    # [REJECT] Block được đề xuất bởi đúng proposer dự kiến cho slot
    parent_state = store.block_states[block.parent_root].copy()
    process_slots(parent_state, block.slot)
    expected_proposer = get_beacon_proposer_index(parent_state)
    if block.proposer_index != expected_proposer:
        raise GossipReject("block proposer_index does not match expected proposer")

    # [New in Gloas:EIP7732]
    # [REJECT] Nếu parent không full, bid phải xây dựng trên execution head của parent
    if not is_parent_node_full(store, block):
        if bid.parent_block_hash != parent_state.latest_block_hash:
            raise GossipReject("bid does not build on the parent's execution head")

    # Đánh dấu block này là đã thấy
    seen.proposer_slots.add(proposer_slot_key)
```

##### Modified `beacon_aggregate_and_proof`

*Ghi chú*: Hàm này được sửa đổi theo EIP-7732. `aggregate.data.index` giờ
chỉ được nhận giá trị trong `{0, 1}`, dùng để mã hóa việc execution payload có
xuất hiện ở slot đó hay không. Các aggregate cùng slot (same-slot, tức vote cho
block thuộc chính slot của attestation) MUST attest với `index == 0`. Các
aggregate có `index == 1` yêu cầu execution payload envelope tương ứng đã được
nhận (seen) và đã vượt qua bước kiểm tra của execution layer.

```python
def validate_beacon_aggregate_and_proof_gossip(
    seen: Seen,
    store: Store,
    signed_aggregate_and_proof: SignedAggregateAndProof,
    current_time_ms: Uint64,
    # [New in Gloas:EIP7732]
    block_payload_statuses: dict[Root, PayloadValidationStatus],
) -> None:
    """
    Validate a SignedAggregateAndProof for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    aggregate_and_proof = signed_aggregate_and_proof.message
    aggregate = aggregate_and_proof.aggregate
    aggregation_bits = aggregate.aggregation_bits

    # [New in Gloas:EIP7732]
    # [REJECT] Data index của aggregate attestation là 0 hoặc 1
    if aggregate.data.index > 1:
        raise GossipReject("aggregate data index must be 0 or 1")

    # [REJECT] Committee bits chỉ định đúng một committee
    committee_indices = get_committee_indices(aggregate.committee_bits)
    if len(committee_indices) != 1:
        raise GossipReject("aggregate committee bits must specify exactly one committee")
    index = committee_indices[0]

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

    # [New in Gloas:EIP7732]
    # Trạng thái payload được attest nhất quán với execution payload của block
    verify_attestation_payload_status(store, aggregate.data, block_payload_statuses)

    # Đánh dấu aggregate này là đã thấy
    seen.aggregator_epochs.add(aggregator_epoch_key)
    if aggregate_cache_key not in seen.aggregate_data_roots:
        seen.aggregate_data_roots[aggregate_cache_key] = set()
    seen.aggregate_data_roots[aggregate_cache_key].add(aggregate_bits)
```

##### New `execution_payload`

Topic này được dùng để lan truyền các message execution payload dưới dạng
`SignedExecutionPayloadEnvelope`.

```python
def validate_execution_payload_envelope_gossip(
    seen: Seen,
    store: Store,
    signed_execution_payload_envelope: SignedExecutionPayloadEnvelope,
) -> None:
    """
    Validate a SignedExecutionPayloadEnvelope for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    envelope = signed_execution_payload_envelope.message
    payload = envelope.payload
    block_root = envelope.beacon_block_root

    # [IGNORE] Node chưa thấy envelope hợp lệ nào khác cho block root này từ builder này
    envelope_key = (block_root, envelope.builder_index)
    if envelope_key in seen.execution_payload_envelopes:
        raise GossipIgnore("already seen envelope for this block root from this builder")

    # [IGNORE] Block root của envelope đã được thấy (qua gossip hoặc nguồn không phải gossip)
    # (MAY đưa vào hàng đợi cho đến khi block được truy xuất)
    if block_root not in store.blocks:
        raise GossipIgnore("envelope's block has not been seen")

    # [REJECT] Block của envelope qua được validation
    if block_root not in store.block_states:
        raise GossipReject("envelope's block failed validation")

    state = store.block_states[block_root]

    # [IGNORE] Envelope thuộc slot lớn hơn hoặc bằng finalized slot mới nhất
    finalized_slot = compute_start_slot_at_epoch(store.finalized_checkpoint.epoch)
    if payload.slot_number < finalized_slot:
        raise GossipIgnore("envelope is from a slot before the latest finalized slot")

    block = store.blocks[block_root]
    bid = block.body.signed_execution_payload_bid.message

    # [REJECT] Slot của block khớp với số slot của payload
    if block.slot != payload.slot_number:
        raise GossipReject("block's slot does not match payload's slot number")

    # [REJECT] Envelope đến từ builder đã được cam kết trong bid
    if envelope.builder_index != bid.builder_index:
        raise GossipReject("envelope's builder index does not match the bid's builder index")

    # [REJECT] Block hash của payload khớp với block hash của bid
    if payload.block_hash != bid.block_hash:
        raise GossipReject("payload's block hash does not match the bid's block hash")

    # [REJECT] Execution requests root của envelope khớp với execution requests root của bid
    if hash_tree_root(envelope.execution_requests) != bid.execution_requests_root:
        raise GossipReject("envelope's execution requests root does not match the bid's")

    # [REJECT] Số lượng execution request nằm trong giới hạn tương ứng
    verify_execution_requests_limits(envelope.execution_requests)

    # [REJECT] Số lượng withdrawal nằm trong giới hạn
    if len(payload.withdrawals) > MAX_WITHDRAWALS_PER_PAYLOAD:
        raise GossipReject("too many withdrawals")

    # [REJECT] Signature của envelope hợp lệ
    if not verify_execution_payload_envelope_signature(state, signed_execution_payload_envelope):
        raise GossipReject("invalid envelope signature")

    # Đánh dấu envelope này là đã thấy và lưu trữ payload của nó
    seen.execution_payload_envelopes.add(envelope_key)
    seen.execution_payloads[payload.block_hash] = payload
```

##### New `payload_attestation_message`

Topic này được dùng để lan truyền các payload attestation message đã được ký.

```python
def validate_payload_attestation_message_gossip(
    seen: Seen,
    store: Store,
    payload_attestation_message: PayloadAttestationMessage,
    current_time_ms: Uint64,
) -> None:
    """
    Validate a PayloadAttestationMessage for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    data = payload_attestation_message.data
    validator_index = payload_attestation_message.validator_index

    # [REJECT] Slot của payload attestation nằm tại hoặc sau fork Gloas
    if compute_epoch_at_slot(data.slot) < GLOAS_FORK_EPOCH:
        raise GossipReject("payload attestation's slot is pre-gloas")

    # [IGNORE] Đây là payload attestation hợp lệ đầu tiên từ validator index này
    payload_attestation_key = (data.slot, validator_index)
    if payload_attestation_key in seen.payload_attestation_validators:
        raise GossipIgnore("already seen payload attestation from this validator")

    # [IGNORE] Slot của payload attestation là slot hiện tại
    if not is_current_slot(store, data.slot, current_time_ms):
        raise GossipIgnore("payload attestation is not for the current slot")

    # [IGNORE] Block của payload attestation đã được thấy (qua gossip hoặc nguồn không phải gossip)
    # (MAY đưa vào hàng đợi cho đến khi block được truy xuất)
    if data.beacon_block_root not in store.blocks:
        raise GossipIgnore("payload attestation's block has not been seen")

    # [REJECT] Block của payload attestation qua được validation
    if data.beacon_block_root not in store.block_states:
        raise GossipReject("payload attestation's block failed validation")

    # [IGNORE] Block của payload attestation nằm ở slot được chỉ định
    if store.blocks[data.beacon_block_root].slot != data.slot:
        raise GossipIgnore("payload attestation's block is not at the assigned slot")

    state = store.block_states[get_head(store).root]

    # [REJECT] Validator index hợp lệ
    if validator_index >= len(state.validators):
        raise GossipReject("validator index out of range")

    # [REJECT] Validator là thành viên của payload timeliness committee (PTC)
    if validator_index not in get_ptc(state, data.slot):
        raise GossipReject("validator is not in the payload timeliness committee")

    # [REJECT] Signature hợp lệ
    validator = state.validators[validator_index]
    domain = get_domain(state, DOMAIN_PTC_ATTESTER, compute_epoch_at_slot(data.slot))
    signing_root = compute_signing_root(data, domain)
    if not bls.Verify(validator.pubkey, signing_root, payload_attestation_message.signature):
        raise GossipReject("invalid payload attestation signature")

    # Đánh dấu payload_attestation này là đã thấy
    seen.payload_attestation_validators.add(payload_attestation_key)
```

##### New `execution_payload_bid`

Topic này được dùng để lan truyền các bid đã ký dưới dạng `SignedExecutionPayloadBid`.

```python
def validate_execution_payload_bid_gossip(
    seen: Seen,
    store: Store,
    signed_execution_payload_bid: SignedExecutionPayloadBid,
    current_time_ms: Uint64,
) -> None:
    """
    Validate a SignedExecutionPayloadBid for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    bid = signed_execution_payload_bid.message

    # [IGNORE] Đây là bid đầu tiên cho slot, parent và builder này
    bid_key = (bid.slot, bid.parent_block_hash, bid.parent_block_root, bid.builder_index)
    if bid_key in seen.execution_payload_bids:
        raise GossipIgnore("already seen valid bid for this slot, parent, and builder")

    # [IGNORE] Đây là bid có giá trị cao nhất được thấy cho slot và parent này
    best_bid_key = (bid.slot, bid.parent_block_hash, bid.parent_block_root)
    if best_bid_key in seen.best_execution_payload_bid:
        if bid.value <= seen.best_execution_payload_bid[best_bid_key]:
            raise GossipIgnore("bid is not the highest value bid seen for this slot and parent")

    # [IGNORE] Slot của bid là slot hiện tại hoặc slot kế tiếp
    if not is_current_or_next_slot(store, bid.slot, current_time_ms):
        raise GossipIgnore("bid's slot is not the current or next slot")

    # [REJECT] Execution payment của bid bằng 0
    if bid.execution_payment != 0:
        raise GossipReject("bid's execution payment must be zero")

    # [REJECT] Block hash của bid không bằng parent block hash của nó
    if bid.block_hash == bid.parent_block_hash:
        raise GossipReject("bid's block hash equals its parent block hash")

    # [REJECT] Số lượng blob KZG commitment của bid nằm trong giới hạn theo epoch
    proposal_epoch = compute_epoch_at_slot(bid.slot)
    max_blobs = get_blob_parameters(proposal_epoch).max_blobs_per_block
    if len(bid.blob_kzg_commitments) > max_blobs:
        raise GossipReject("too many blob kzg commitments")

    # [IGNORE] Parent block root của bid là một beacon block đã biết
    # (MAY đưa vào hàng đợi cho đến khi parent được truy xuất)
    if bid.parent_block_root not in store.blocks:
        raise GossipIgnore("bid's parent block root is not a known beacon block")

    # [REJECT] Bid thuộc slot cao hơn parent block của nó
    if bid.slot <= store.blocks[bid.parent_block_root].slot:
        raise GossipReject("bid's slot is not higher than its parent's slot")

    # [IGNORE] Parent block của bid đã được import
    # (MAY đưa vào hàng đợi cho đến khi parent được import)
    if bid.parent_block_root not in store.block_states:
        raise GossipIgnore("bid's parent block post-state is unavailable")

    state = store.block_states[bid.parent_block_root]

    # [IGNORE] Slot của bid nằm trong proposer lookahead của parent
    if proposal_epoch > get_current_epoch(state) + MIN_SEED_LOOKAHEAD:
        raise GossipIgnore("bid's slot is past the parent's proposer lookahead")

    # [IGNORE] Proposer preferences tương ứng đã được thấy
    dependent_root = get_shuffling_dependent_root(store, bid.parent_block_root, proposal_epoch)
    prefs_key = (bid.slot, dependent_root)
    if prefs_key not in seen.proposer_preferences:
        raise GossipIgnore("matching proposer preferences have not been seen")

    proposer_preferences = seen.proposer_preferences[prefs_key]

    # [IGNORE] Fee recipient của bid khớp với preference của proposer
    if bid.fee_recipient != proposer_preferences.fee_recipient:
        raise GossipIgnore("bid's fee recipient does not match the proposer's preference")

    # [IGNORE] Parent block hash của bid là hash của một execution payload đã biết
    if bid.parent_block_hash not in seen.execution_payloads:
        raise GossipIgnore("bid's parent block hash is not a known execution payload")

    # [IGNORE] Gas limit của bid tương thích với target gas limit của proposer
    parent_gas_limit = seen.execution_payloads[bid.parent_block_hash].gas_limit
    if not is_gas_limit_target_compatible(
        parent_gas_limit, bid.gas_limit, proposer_preferences.target_gas_limit
    ):
        raise GossipIgnore("bid's gas limit is not compatible with the proposer's target")

    # [IGNORE] Bid tương thích với nhánh head hiện tại
    if not is_bid_compatible_with_head(store, bid):
        raise GossipIgnore("bid is not compatible with the current head branch")

    # [REJECT] Previous randao của bid là đúng
    if bid.prev_randao != get_randao_mix(state, get_current_epoch(state)):
        raise GossipReject("bid's previous randao is incorrect")

    state = state.copy()
    process_slots(state, bid.slot)

    # [REJECT] Builder index hợp lệ
    if bid.builder_index >= len(state.builders):
        raise GossipReject("builder index out of range")

    builder = state.builders[bid.builder_index]

    # [REJECT] Builder là một payload builder
    if builder.version != PAYLOAD_BUILDER_VERSION:
        raise GossipReject("builder is not a payload builder")

    # [REJECT] Builder đang active
    if not is_active_builder(state, bid.builder_index):
        raise GossipReject("builder is not active")

    # [IGNORE] Builder đủ khả năng chi trả bid
    if not can_builder_cover_bid(state, bid.builder_index, bid.value):
        raise GossipIgnore("builder cannot cover bid value")

    # [IGNORE] Payload của parent không cố gắng exit builder này
    if bid.parent_block_hash == state.latest_execution_payload_bid.block_hash:
        envelope = store.payloads[bid.parent_block_root]
        for request in envelope.execution_requests.builder_exits:
            if request.pubkey == builder.pubkey:
                if request.source_address == builder.execution_address:
                    raise GossipIgnore("builder may exit")

    # [REJECT] Signature của bid hợp lệ
    if not verify_execution_payload_bid_signature(state, signed_execution_payload_bid):
        raise GossipReject("invalid bid signature")

    # Đánh dấu bid này là đã thấy và cập nhật bid có giá trị cao nhất cho slot/parent này
    seen.execution_payload_bids.add(bid_key)
    seen.best_execution_payload_bid[best_bid_key] = bid.value
```

*Ghi chú*: Các implementation SHOULD có biện pháp chống DoS để hạn chế spam từ
các builder độc hại gửi rất nhiều bid với mức tăng giá trị rất nhỏ. Một số chiến
lược khả thi: (1) chỉ chuyển tiếp (forward) những bid vượt bid cao nhất hiện tại
ít nhất một ngưỡng tối thiểu, hoặc (2) chỉ chuyển tiếp bid cao nhất quan sát được
theo từng khoảng thời gian định kỳ.

##### New `proposer_preferences`

Topic này được dùng để lan truyền các proposer preference đã ký dưới dạng
`SignedProposerPreferences`. Các message này cho phép validator thông báo cho
builder biết `fee_recipient` và `target_gas_limit` mà họ mong muốn.

*Ghi chú*: Node SHOULD subscribe topic này ít nhất một epoch trước khi fork được
kích hoạt. Proposer SHOULD broadcast preference của mình trong epoch ngay trước
fork.

```python
def validate_proposer_preferences_gossip(
    seen: Seen,
    store: Store,
    signed_proposer_preferences: SignedProposerPreferences,
    current_time_ms: Uint64,
) -> None:
    """
    Validate a SignedProposerPreferences for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    preferences = signed_proposer_preferences.message

    # [IGNORE] Đây là các preferences hợp lệ đầu tiên được thấy cho dependent root và slot này
    prefs_key = (preferences.proposal_slot, preferences.dependent_root)
    if prefs_key in seen.proposer_preferences:
        raise GossipIgnore("already seen preferences for this dependent root and proposal slot")

    # [IGNORE] Epoch đề xuất (proposal epoch) nằm sau bản nâng cấp Gloas
    proposal_epoch = compute_epoch_at_slot(preferences.proposal_slot)
    if proposal_epoch < GLOAS_FORK_EPOCH:
        raise GossipIgnore("proposal epoch is pre-gloas")

    # [IGNORE] Slot đề xuất (proposal slot) chưa bắt đầu
    if is_past_slot(store, preferences.proposal_slot, current_time_ms):
        raise GossipIgnore("proposal slot has already started")

    # [IGNORE] Proposer của proposal slot đã được biết
    lookahead_start_slot = compute_shuffling_lookahead_start_slot(proposal_epoch)
    if is_future_slot(store, lookahead_start_slot, current_time_ms):
        raise GossipIgnore("proposer for the proposal slot is not yet known")

    # [IGNORE] Dependent block đã được thấy (qua gossip hoặc nguồn không phải gossip)
    # (MAY đưa vào hàng đợi cho đến khi block được truy xuất)
    if preferences.dependent_root not in store.blocks:
        raise GossipIgnore("dependent block has not been seen")

    # [IGNORE] Dependent block qua được validation
    if preferences.dependent_root not in store.block_states:
        raise GossipIgnore("dependent block failed validation")

    # [REJECT] Slot của dependent block không nằm sau shuffling dependent slot
    dependent_slot = compute_shuffling_dependent_slot(proposal_epoch)
    if store.blocks[preferences.dependent_root].slot > dependent_slot:
        raise GossipReject("dependent block is after the shuffling dependent slot")

    # [IGNORE] Dependent block là một dependent block khả dĩ cho proposer lookahead
    if not is_valid_dependent_root(store, preferences.dependent_root, dependent_slot):
        raise GossipIgnore("dependent block is not a possible dependent block")

    state = store.block_states[preferences.dependent_root].copy()
    if state.slot < lookahead_start_slot:
        process_slots(state, lookahead_start_slot)

    # [REJECT] Validator là proposer của slot đã cho trong proposer lookahead
    lookahead_index = preferences.proposal_slot - lookahead_start_slot
    if state.proposer_lookahead[lookahead_index] != preferences.validator_index:
        raise GossipReject("validator is not the proposer for the given slot")

    # [REJECT] Signature hợp lệ
    validator = state.validators[preferences.validator_index]
    domain = compute_domain(
        DOMAIN_PROPOSER_PREFERENCES,
        compute_fork_version(proposal_epoch),
        state.genesis_validators_root,
    )
    signing_root = compute_signing_root(preferences, domain)
    if not bls.Verify(validator.pubkey, signing_root, signed_proposer_preferences.signature):
        raise GossipReject("invalid proposer preferences signature")

    # Đánh dấu các preferences này là đã thấy
    seen.proposer_preferences[prefs_key] = preferences
```

#### Attestation subnets

##### Modified `beacon_attestation_{subnet_id}`

*Ghi chú*: Hàm này được sửa đổi theo EIP-7732. `attestation.data.index` giờ
chỉ được nhận giá trị trong `{0, 1}`, dùng để mã hóa việc execution payload có
xuất hiện ở slot đó hay không. Các attestation cùng slot MUST attest với
`index == 0`. Các attestation có `index == 1` yêu cầu execution payload envelope
tương ứng đã được nhận (seen) và đã vượt qua bước kiểm tra của execution layer.

```python
def validate_beacon_attestation_gossip(
    seen: Seen,
    store: Store,
    attestation: SingleAttestation,
    current_time_ms: Uint64,
    subnet_id: SubnetID,
    # [New in Gloas:EIP7732]
    block_payload_statuses: dict[Root, PayloadValidationStatus],
) -> None:
    """
    Validate a SingleAttestation for gossip propagation on a subnet.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    data = attestation.data
    committee_index = attestation.committee_index
    attester_index = attestation.attester_index
    target_epoch = data.target.epoch

    # [IGNORE] Chưa thấy attestation hợp lệ nào khác cho target epoch và validator này
    attestation_epoch_key = (target_epoch, attester_index)
    if attestation_epoch_key in seen.attestation_validator_epochs:
        raise GossipIgnore("already seen attestation for this epoch and validator")

    # [New in Gloas:EIP7732]
    # [REJECT] Data index của attestation là 0 hoặc 1
    if data.index > 1:
        raise GossipReject("attestation data index must be 0 or 1")

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

    # [REJECT] Attester là thành viên của committee
    committee = get_beacon_committee(state, data.slot, committee_index)
    if attester_index not in committee:
        raise GossipReject("attester is not a member of the committee")

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

    # [IGNORE] Finalized checkpoint hiện tại là tổ tiên (ancestor) của block
    finalized_epoch = store.finalized_checkpoint.epoch
    finalized_checkpoint_block = get_checkpoint_block(store, block_root, finalized_epoch)
    if finalized_checkpoint_block != store.finalized_checkpoint.root:
        raise GossipIgnore("finalized checkpoint is not an ancestor of block")

    # [New in Gloas:EIP7732]
    # Trạng thái payload được attest nhất quán với execution payload của block
    verify_attestation_payload_status(store, data, block_payload_statuses)

    # Đánh dấu attestation này là đã thấy
    seen.attestation_validator_epochs.add(attestation_epoch_key)
```

#### Blob subnets

##### Modified `data_column_sidecar_{subnet_id}`

Các KZG commitment cần thiết để xác minh một sidecar giờ được mang bởi bid tại
`block.body.signed_execution_payload_bid.message.blob_kzg_commitments`, trong đó
`block` là `BeaconBlock` có root bằng `sidecar.beacon_block_root`.

*Ghi chú*: Nếu sidecar không vượt qua bước kiểm tra trì hoãn (deferred
validation — tức kiểm tra chỉ có thể làm sau khi đã nhận được block chứa bid),
các peer đã chuyển tiếp nó MUST bị hạ điểm (downscore) hồi tố. Nếu kiểm tra
thành công, client MUST broadcast lại sidecar.

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
    # [IGNORE] Đây là sidecar đầu tiên được thấy cho block root và column index này
    sidecar_key = (sidecar.beacon_block_root, sidecar.index)
    if sidecar_key in seen.data_column_sidecar_tuples:
        raise GossipIgnore("already seen sidecar for this block root and index")

    # [REJECT] Sidecar thuộc đúng subnet
    if compute_subnet_for_data_column_sidecar(sidecar.index) != subnet_id:
        raise GossipReject("sidecar is for wrong subnet")

    # [IGNORE] Sidecar không thuộc slot tương lai
    # (MAY đưa vào hàng đợi để xử lý tại slot thích hợp)
    if is_future_slot(store, sidecar.slot, current_time_ms):
        raise GossipIgnore("sidecar is from a future slot")

    # [IGNORE] Block của sidecar đã được thấy (qua gossip hoặc nguồn không phải gossip)
    # (MAY đưa vào hàng đợi cho đến khi block được truy xuất)
    # (SHOULD đưa vào hàng đợi ít nhất một sidecar cho mỗi peer trên mỗi subnet)
    if sidecar.beacon_block_root not in store.blocks:
        raise GossipIgnore("block for sidecar's beacon block root has not been seen")

    # [REJECT] Block của sidecar qua được validation
    if sidecar.beacon_block_root not in store.block_states:
        raise GossipReject("block for sidecar's beacon block root failed validation")

    block = store.blocks[sidecar.beacon_block_root]

    # [REJECT] Slot của sidecar khớp với slot của block
    if sidecar.slot != block.slot:
        raise GossipReject("sidecar's slot does not match block's slot")

    bid = block.body.signed_execution_payload_bid.message

    # [REJECT] Sidecar qua được validation về cấu trúc
    if not verify_data_column_sidecar(sidecar, bid.blob_kzg_commitments):
        raise GossipReject("invalid sidecar")

    # [REJECT] Dữ liệu column của sidecar qua được KZG verification
    if not verify_data_column_sidecar_kzg_proofs(sidecar, bid.blob_kzg_commitments):
        raise GossipReject("invalid sidecar kzg proofs")

    # Đánh dấu data column sidecar này là đã thấy
    seen.data_column_sidecar_tuples.add(sidecar_key)
```

## The Req/Resp domain

### Messages

#### BeaconBlocksByRange v2

**Protocol ID:** `/eth2/beacon_chain/req/beacon_blocks_by_range/2/`

Fork digest của Gloas được thêm vào enum `context` để chỉ định kiểu beacon block
của Gloas.

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

#### BeaconBlocksByRoot v2

**Protocol ID:** `/eth2/beacon_chain/req/beacon_blocks_by_root/2/`

Fork digest của Gloas được thêm vào enum `context` để chỉ định kiểu beacon block
của Gloas.

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

#### ExecutionPayloadEnvelopesByRange v1

**Protocol ID:**
`/eth2/beacon_chain/req/execution_payload_envelopes_by_range/1/`

Nội dung request (Request Content):

```
(
  start_slot: Slot
  count: Uint64
)
```

Nội dung response (Response Content):

```
(
  SignedExecutionPayloadEnvelopes
)
```

Đặc tả của phương thức request/response này tương đương với
[BeaconBlocksByRange v2](#beaconblocksbyrange-v2), điểm khác biệt duy nhất là kiểu
nội dung của response.

Client MUST trả về các execution payload envelope theo góc nhìn fork choice hiện
tại của mình -- tức là envelope của những payload thuộc chuỗi duy nhất được xác
định bởi head hiện tại. Một payload thuộc chuỗi đó nếu block kế tiếp trong chuỗi
được xây dựng trên nó, nghĩa là `parent_block_hash` trong execution payload bid
của block đó bằng `block_hash` của payload. Với block head, payload thuộc chuỗi
nếu `ForkChoiceNode` của head có `payload_status` bằng `PAYLOAD_STATUS_FULL`.
Client MUST NOT trả về envelope cho những block mà `ForkChoiceNode` của chúng
trong chuỗi đó có `payload_status` bằng `PAYLOAD_STATUS_EMPTY`. Với các slot
trước finalization, chuỗi đó dẫn tới block finalized được báo trong handshake
`Status`.

> 💡 Ghi chú: Trong Gloas, mỗi block có thể ở trạng thái "full" (payload đã được
> reveal và được chuỗi chấp nhận) hoặc "empty" (không có payload). Chỉ envelope
> của các payload thực sự nằm trên chuỗi canonical mới được trả về.

Với mỗi `response_chunk` thành công, epoch dùng cho context `ForkDigest` được xác
định bằng `compute_epoch_at_slot(beacon_block.slot)`, dựa trên `beacon_block` mà
`signed_execution_payload_envelope.message.beacon_block_root` tham chiếu tới.

Theo `fork_version = compute_fork_version(epoch)`:

For each successful `response_chunk`, the `ForkDigest` context epoch is
determined by `compute_epoch_at_slot(beacon_block.slot)` based on the
`beacon_block` referred to by
`signed_execution_payload_envelope.message.beacon_block_root`.

Per `fork_version = compute_fork_version(epoch)`:

<!-- eth_consensus_specs: skip -->

| `fork_version`       | Chunk SSZ type                         |
| -------------------- | -------------------------------------- |
| `GLOAS_FORK_VERSION` | `gloas.SignedExecutionPayloadEnvelope` |

#### ExecutionPayloadEnvelopesByRoot v1

**Protocol ID:** `/eth2/beacon_chain/req/execution_payload_envelopes_by_root/1/`

Request Content:

```
(
  ExecutionPayloadEnvelopeRoots
)
```

Response Content:

```
(
  SignedExecutionPayloadEnvelopes
)
```

Request các execution payload envelope theo
`signed_execution_payload_envelope.message.beacon_block_root`. Response là một
danh sách `SignedExecutionPayloadEnvelope` có độ dài nhỏ hơn hoặc bằng số
execution payload envelope được yêu cầu. Danh sách có thể ngắn hơn trong trường
hợp peer phản hồi không có đủ payload envelope.

Không được request quá `MAX_REQUEST_PAYLOADS` mỗi lần.

ExecutionPayloadEnvelopesByRoot chủ yếu được dùng để khôi phục các execution
payload envelope và attestation gần đây (ví dụ: khi nhận được một payload
attestation hoặc attestation báo payload đã được reveal (giá trị true) nhưng node
chưa bao giờ nhận được payload đó).

Request MUST được mã hóa dưới dạng một SSZ-field.

Response MUST gồm không hoặc nhiều `response_chunk`. Mỗi `response_chunk` thành
công MUST chứa đúng một payload `SignedExecutionPayloadEnvelope`.

Client MUST hỗ trợ request payload envelope trong khoảng epoch
`[max(GLOAS_FORK_EPOCH, current_epoch - compute_min_epochs_for_block_requests()), current_epoch]`.
Nếu có root nào trong nội dung request tham chiếu tới block sớm hơn khoảng này,
peer MAY phản hồi mã lỗi `3: ResourceUnavailable` hoặc không đưa payload envelope
đó vào response.

*Ghi chú*: Client MUST đồng thời lưu giữ mọi payload envelope mới hơn checkpoint
finalized gần nhất của mình và MUST hỗ trợ phục vụ request cho các payload
envelope này, kể cả khi chúng nằm ngoài khoảng trên.

Client MUST trả về ít nhất một payload envelope, nếu có. Client MAY giới hạn số
payload envelope trong response.

Với mỗi `response_chunk` thành công, epoch dùng cho context `ForkDigest` được xác
định bằng `compute_epoch_at_slot(beacon_block.slot)`, dựa trên `beacon_block` mà
`signed_execution_payload_envelope.message.beacon_block_root` tham chiếu tới.

Theo `fork_version = compute_fork_version(epoch)`:

<!-- eth_consensus_specs: skip -->

| `fork_version`       | Chunk SSZ type                         |
| -------------------- | -------------------------------------- |
| `GLOAS_FORK_VERSION` | `gloas.SignedExecutionPayloadEnvelope` |
