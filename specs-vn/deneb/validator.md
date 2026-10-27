# Deneb -- Honest Validator

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Types](#types)
  - [`Blobs`](#blobs)
  - [`KZGProofs`](#kzgproofs)
- [Helpers](#helpers)
  - [`BlobsBundle`](#blobsbundle)
  - [Modified `GetPayloadResponse`](#modified-getpayloadresponse)
- [Protocols](#protocols)
  - [`ExecutionEngine`](#executionengine)
    - [Modified `get_payload`](#modified-get_payload)
- [Beacon chain responsibilities](#beacon-chain-responsibilities)
  - [Block and sidecar proposal](#block-and-sidecar-proposal)
    - [Constructing the `BeaconBlockBody`](#constructing-the-beaconblockbody)
      - [ExecutionPayload](#executionpayload)
      - [Blob KZG commitments](#blob-kzg-commitments)
    - [Constructing the `BlobSidecar`s](#constructing-the-blobsidecars)
      - [Sidecar](#sidecar)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả những thay đổi cần thực hiện trong code của một "honest
validator" (validator trung thực, tức validator tuân thủ đúng giao thức) để triển
khai bản nâng cấp Deneb.

## Prerequisites

Tài liệu này là phần mở rộng của hướng dẫn
[Capella -- Honest Validator](../capella/validator.md). Mọi hành vi và định nghĩa
trong tài liệu này, cũng như trong các tài liệu mà nó mở rộng, đều được giữ
nguyên trừ khi được ghi chú rõ hoặc bị ghi đè.

Toàn bộ thuật ngữ, hằng số, hàm và cơ chế giao thức được định nghĩa trong
[beacon-chain specifications của Deneb](./beacon-chain.md) (bản cập nhật) là kiến
thức bắt buộc cho tài liệu này và được dùng xuyên suốt. Vui lòng đọc các spec
beacon-chain liên quan trước khi tiếp tục và dùng chúng làm tài liệu tham chiếu
trong suốt quá trình đọc.

## Types

### `Blobs`

```python
class Blobs(List[Blob]):
    """
    The blobs of a single beacon block.
    """

    LIMIT = MAX_BLOB_COMMITMENTS_PER_BLOCK
```

### `KZGProofs`

```python
class KZGProofs(List[KZGProof]):
    """
    A list of KZG proofs, one for each blob or cell being proven.
    """

    LIMIT = MAX_BLOB_COMMITMENTS_PER_BLOCK
```

## Helpers

### `BlobsBundle`

*[New in Deneb:EIP4844]*

```python
@dataclass
class BlobsBundle:
    commitments: BlobKZGCommitments
    proofs: KZGProofs
    blobs: Blobs
```

### Modified `GetPayloadResponse`

```python
@dataclass
class GetPayloadResponse:
    execution_payload: ExecutionPayload
    block_value: Uint256
    # [New in Deneb:EIP4844]
    blobs_bundle: BlobsBundle
```

```python
def compute_signed_block_header(signed_block: SignedBeaconBlock) -> SignedBeaconBlockHeader:
    block = signed_block.message
    block_header = BeaconBlockHeader(
        slot=block.slot,
        proposer_index=block.proposer_index,
        parent_root=block.parent_root,
        state_root=block.state_root,
        body_root=hash_tree_root(block.body),
    )
    return SignedBeaconBlockHeader(message=block_header, signature=signed_block.signature)
```

## Protocols

### `ExecutionEngine`

#### Modified `get_payload`

*Ghi chú*: Hàm `get_payload` giờ trả về object `GetPayloadResponse` đã được cập
nhật (có thêm trường `blobs_bundle`).

```python
def get_payload(self: ExecutionEngine, payload_id: PayloadId) -> GetPayloadResponse:
    """
    Return ExecutionPayload, Uint256, and BlobsBundle objects.
    """
```

## Beacon chain responsibilities

Mọi trách nhiệm của validator đều giữ nguyên, ngoại trừ những điểm được nêu dưới
đây.

### Block and sidecar proposal

#### Constructing the `BeaconBlockBody`

##### ExecutionPayload

`prepare_execution_payload` được cập nhật so với spec Capella để truyền thêm root
của parent beacon block.

*Ghi chú*: Trong phần này, `state` là state tại slot đề xuất block, _chưa_ áp
dụng block đó. Tức là `state` chính là `previous_state` sau khi đã được xử lý qua
mọi slot trống cho tới slot được giao, bằng
`process_slots(previous_state, slot)`.

*Ghi chú*: Thay đổi duy nhất đối với `prepare_execution_payload` là thêm root của
parent beacon block làm một tham số bổ sung trong `PayloadAttributes`.

```python
def prepare_execution_payload(
    state: BeaconState,
    safe_block_hash: Hash32,
    finalized_block_hash: Hash32,
    suggested_fee_recipient: ExecutionAddress,
    execution_engine: ExecutionEngine,
) -> PayloadId | None:
    # Kiểm tra tính nhất quán của parent hash so với execution payload header trước đó
    parent_hash = state.latest_execution_payload_header.block_hash

    # Thiết lập head cho forkchoice và khởi động quá trình build payload
    payload_attributes = PayloadAttributes(
        timestamp=compute_time_at_slot(state.genesis_time, state.slot),
        prev_randao=get_randao_mix(state, get_current_epoch(state)),
        suggested_fee_recipient=suggested_fee_recipient,
        withdrawals=get_expected_withdrawals(state).withdrawals,
        # [New in Deneb:EIP4788]
        parent_beacon_block_root=hash_tree_root(state.latest_block_header),
    )
    return execution_engine.notify_forkchoice_updated(
        head_block_hash=parent_hash,
        safe_block_hash=safe_block_hash,
        finalized_block_hash=finalized_block_hash,
        payload_attributes=payload_attributes,
    )
```

> 💡 Ghi chú: `hash_tree_root(state.latest_block_header)` chính là root của
> parent beacon block, vì tại thời điểm này `state` đã được xử lý tới slot mới
> nhưng block mới chưa được áp dụng (và `state_root` trong header đã được điền
> trong `process_slot`).

##### Blob KZG commitments

*[New in Deneb:EIP4844]*

1. Execution payload được lấy từ execution engine như đã định nghĩa ở trên, bằng
   `payload_id`. Response cũng chứa một trường `blobs_bundle` gồm các `blobs`,
   `commitments` và `proofs` tương ứng.
2. Gán `block.body.blob_kzg_commitments = commitments`.

#### Constructing the `BlobSidecar`s

*[New in Deneb:EIP4844]*

Để tạo một `BlobSidecar`, ta định nghĩa một `blob_sidecar` chứa đủ ngữ cảnh cần
thiết cho việc đề xuất block và sidecar.

##### Sidecar

Các blob gắn với một block được đóng gói thành các object sidecar để phát tán lên
topic sidecar tương ứng, tức pubsub topic `blob_sidecar_{subnet_id}`.

Mỗi `sidecar` được tạo bởi:

```python
def get_blob_sidecars(
    signed_block: SignedBeaconBlock, blobs: Sequence[Blob], blob_kzg_proofs: Sequence[KZGProof]
) -> Sequence[BlobSidecar]:
    block = signed_block.message
    signed_block_header = compute_signed_block_header(signed_block)
    return [
        BlobSidecar(
            index=BlobIndex(index),
            blob=blob,
            kzg_commitment=block.body.blob_kzg_commitments[index],
            kzg_proof=blob_kzg_proofs[index],
            signed_block_header=signed_block_header,
            kzg_commitment_inclusion_proof=KZGCommitmentInclusionProof(
                data=compute_merkle_proof(
                    block.body,
                    get_generalized_index(BeaconBlockBody, "blob_kzg_commitments", index),
                )
            ),
        )
        for index, blob in enumerate(blobs)
    ]
```

> 💡 Ghi chú: Mỗi sidecar mang theo signed block header (để kiểm tra chữ ký của
> proposer) và một Merkle proof (`kzg_commitment_inclusion_proof`) chứng minh
> rằng `kzg_commitment` của nó thực sự nằm trong `blob_kzg_commitments` của block
> body. Nhờ vậy, node nhận có thể xác thực sidecar mà không cần có toàn bộ block.

`subnet_id` cho `blob_sidecar` được tính như sau:

- Đặt `blob_index = blob_sidecar.index`.
- Đặt `subnet_id = compute_subnet_for_blob_sidecar(blob_index)`.

```python
def compute_subnet_for_blob_sidecar(blob_index: BlobIndex) -> SubnetID:
    return SubnetID(blob_index % BLOB_SIDECAR_SUBNET_COUNT)
```

Sau khi publish, các peer trong mạng có thể yêu cầu sidecar thông qua các
sync-request, hoặc một người dùng cục bộ cũng có thể cần đến nó.

Validator MUST lưu giữ các sidecar trong `MIN_EPOCHS_FOR_BLOB_SIDECARS_REQUESTS`
epoch và phục vụ chúng khi có khả năng, nhằm đảm bảo tính sẵn có của dữ liệu
(data-availability) của các blob này trên toàn mạng.

Sau `MIN_EPOCHS_FOR_BLOB_SIDECARS_REQUESTS` epoch, node MAY xoá bỏ (prune) các
sidecar và/hoặc ngừng phục vụ chúng.
