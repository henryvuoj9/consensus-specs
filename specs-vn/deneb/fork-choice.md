# Deneb -- Fork Choice

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Helpers](#helpers)
  - [Modified `PayloadAttributes`](#modified-payloadattributes)
  - [New `is_data_available`](#new-is_data_available)
- [Handlers](#handlers)
  - [Modified `on_block`](#modified-on_block)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả các sửa đổi của fork choice đi kèm bản nâng cấp Deneb.

## Helpers

### Modified `PayloadAttributes`

`PayloadAttributes` được mở rộng thêm root của beacon block cha cho EIP-4788.

```python
@dataclass
class PayloadAttributes:
    timestamp: Uint64
    prev_randao: Bytes32
    suggested_fee_recipient: ExecutionAddress
    withdrawals: Sequence[Withdrawal]
    # [New in Deneb:EIP4788]
    parent_beacon_block_root: Root
```

### New `is_data_available`

*[Mới trong Deneb:EIP4844]*

Phần cài đặt của `is_data_available` sẽ trở nên phức tạp hơn trong các bản nâng
cấp mở rộng (scaling) về sau. Ban đầu, việc xác minh yêu cầu mỗi bên xác minh
phải tải về tất cả các `Blob` và `KZGProof` tương ứng, rồi kiểm tra chúng bằng
`kzg.verify_blob_kzg_proof_batch`.

Block MUST NOT được coi là hợp lệ cho đến khi tất cả các `Blob` hợp lệ đã được
tải về. Các block trước đó đã được xác nhận là available (dữ liệu sẵn có) SHOULD
tiếp tục được coi là available, kể cả khi các `Blob` liên quan sau đó đã bị
prune (xóa bớt).

*Ghi chú*: Các Blob thừa hoặc không hợp lệ (ngoài các blob hợp lệ được KZG
commitment tham chiếu/kỳ vọng) nhận được trên mạng p2p MUST NOT làm một block
vốn hợp lệ và available trở thành không hợp lệ.

```python
def is_data_available(
    beacon_block_root: Root, blob_kzg_commitments: Sequence[KZGCommitment]
) -> bool:
    # `retrieve_blobs_and_proofs` is implementation and context dependent
    # It returns all the blobs for the given block root, and raises an exception if not available
    # Note: the p2p network does not guarantee sidecar retrieval outside of
    # `MIN_EPOCHS_FOR_BLOB_SIDECARS_REQUESTS`
    blobs, proofs = retrieve_blobs_and_proofs(beacon_block_root)

    return kzg.verify_blob_kzg_proof_batch(blobs, blob_kzg_commitments, proofs)
```

*Ghi chú*: Hàm `kzg.verify_blob_kzg_proof_batch` được định nghĩa trong
[cryptography-specs](https://github.com/ethereum/cryptography-specs) với chữ ký
hàm như sau:

<!-- eth_consensus_specs: skip -->

```python
def verify_blob_kzg_proof_batch(
    blobs: Sequence[Blob], commitments_bytes: Sequence[Bytes48], proofs_bytes: Sequence[Bytes48]
) -> bool:
    """
    Return ``True`` if and only if all blobs and their proofs match the
    commitments.
    """
```

## Handlers

### Modified `on_block`

*Ghi chú*: Thay đổi duy nhất là bổ sung bước kiểm tra data availability của
blob.

```python
def on_block(store: Store, signed_block: SignedBeaconBlock) -> None:
    """
    Run ``on_block`` upon receiving a new block.
    """
    block = signed_block.message
    block_root = hash_tree_root(block)

    # Return early if the block is already known
    if block_root in store.blocks:
        return

    # Parent block must be known
    assert block.parent_root in store.block_states
    # Blocks cannot be in the future. If they are, their consideration must be delayed until they are in the past.
    assert get_current_slot(store) >= block.slot

    # Check that block is later than the finalized epoch slot (optimization to reduce calls to get_ancestor)
    finalized_slot = compute_start_slot_at_epoch(store.finalized_checkpoint.epoch)
    assert block.slot > finalized_slot
    # Check block is a descendant of the finalized block at the checkpoint finalized slot
    finalized_checkpoint_block = get_checkpoint_block(
        store,
        block.parent_root,
        store.finalized_checkpoint.epoch,
    )
    assert store.finalized_checkpoint.root == finalized_checkpoint_block

    # [New in Deneb:EIP4844]
    # Check if blob data is available
    # If not, this payload MAY be queued and subsequently considered when blob data becomes available
    assert is_data_available(block_root, block.body.blob_kzg_commitments)

    # Check the block is valid and compute the post-state
    # Make a copy of the state to avoid mutability issues
    state = store.block_states[block.parent_root].copy()
    state_transition(state, signed_block, validate_result=True)

    # Compute head before applying the block
    head = get_head(store)
    # Add new block to the store
    store.blocks[block_root] = block
    # Add new state for this block to the store
    store.block_states[block_root] = state

    record_block_timeliness(store, block_root)
    update_proposer_boost_root(store, head.root, block_root)

    # Update checkpoints in store if necessary
    update_checkpoints(store, state.current_justified_checkpoint, state.finalized_checkpoint)

    # Eagerly compute unrealized justification and finality.
    compute_pulled_up_tip(store, block_root)
```
