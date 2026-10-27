# Fulu -- Fork Choice

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Helpers](#helpers)
  - [Modified `get_proposer_head`](#modified-get_proposer_head)
  - [Modified `is_data_available`](#modified-is_data_available)
- [Handlers](#handlers)
  - [Modified `on_block`](#modified-on_block)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả các thay đổi đối với fork choice đi kèm với Fulu.

## Helpers

### Modified `get_proposer_head`

*Ghi chú*: Hàm này được sửa đổi để cho phép proposer re-org (tổ chức lại chuỗi
bằng cách bỏ qua head muộn) tại ranh giới epoch. Proposer lookahead được đưa vào
ở Fulu đã cố định việc phân công proposer từ trước ranh giới epoch, nên việc
re-org một block đến muộn ở cuối epoch trước không thể làm thay đổi proposer của
slot hiện tại.

> 💡 Ghi chú: Trước Fulu, điều kiện `shuffling_stable` cấm re-org ở slot đầu
> tiên của epoch, vì khi đó việc bỏ block cuối epoch trước có thể làm đổi
> shuffling và do đó đổi proposer. Với proposer lookahead (EIP-7917), rủi ro này
> không còn nên điều kiện đó bị loại bỏ.

```python
def get_proposer_head(store: Store, head_node: ForkChoiceNode, slot: Slot) -> ForkChoiceNode:
    head_block = store.blocks[head_node.root]
    parent_root = head_block.parent_root
    parent_block = store.blocks[parent_root]
    parent_node = ForkChoiceNode(root=parent_root)

    # Chỉ re-org head block nếu nó đến muộn hơn hạn chót attestation.
    head_late = is_head_late(store, head_node.root)

    # [Modified in Fulu:EIP7917]
    # Đã loại bỏ `shuffling_stable = is_shuffling_stable(slot)`

    # Đảm bảo thông tin FFG của head mới sẽ cạnh tranh được với head hiện tại.
    ffg_competitive = is_ffg_competitive(store, head_node.root, parent_root)

    # Không re-org nếu chuỗi không finalize với tần suất chấp nhận được.
    finalization_ok = is_finalization_ok(store, slot)

    # Chỉ re-org nếu ta đang propose đúng giờ.
    proposing_on_time = is_proposing_on_time(store)

    # Chỉ re-org tối đa một slot.
    parent_slot_ok = parent_block.slot + 1 == head_block.slot
    current_time_ok = head_block.slot + 1 == slot
    single_slot_reorg = parent_slot_ok and current_time_ok

    # Kiểm tra head có đủ ít vote để bị proposer boost của ta lấn át.
    assert store.proposer_boost_root != head_node.root  # đảm bảo boost đã hết tác dụng
    head_weak = is_head_weak(store, head_node.root)

    # Kiểm tra các vote còn thiếu được dồn cho parent chứ không bị giữ lại (hoarded).
    parent_strong = is_parent_strong(store, head_node.root)

    # Re-org mạnh tay hơn nếu có proposer equivocation ở slot trước.
    proposer_equivocation = is_proposer_equivocation(store, head_node.root)

    if all([
        head_late,
        # [Modified in Fulu:EIP7917]
        # Đã loại bỏ `shuffling_stable`
        ffg_competitive,
        finalization_ok,
        proposing_on_time,
        single_slot_reorg,
        head_weak,
        parent_strong,
    ]):
        # Ta có thể re-org head hiện tại bằng cách xây block trên parent node của nó.
        return parent_node
    elif all([head_weak, current_time_ok, proposer_equivocation]):
        return parent_node
    else:
        return head_node
```

### Modified `is_data_available`

> 💡 Ghi chú: Từ Fulu, tính sẵn có của dữ liệu được kiểm tra qua các data column
> sidecar (theo cơ chế sampling của PeerDAS) thay vì tải toàn bộ blob. Block được
> coi là có dữ liệu sẵn có khi mọi column sidecar mà node cần lấy mẫu đều được
> lấy về và kiểm tra hợp lệ (cả cấu trúc lẫn KZG proof).

```python
def is_data_available(beacon_block_root: Root) -> bool:
    # `retrieve_column_sidecars` phụ thuộc vào cách hiện thực và ngữ cảnh, thay thế cho
    # `retrieve_blobs_and_proofs`. Với block root cho trước, nó trả về mọi column
    # sidecar cần lấy mẫu, hoặc ném exception nếu chúng không sẵn có.
    # Mạng p2p không đảm bảo lấy được sidecar nằm ngoài phạm vi
    # `MIN_EPOCHS_FOR_DATA_COLUMN_SIDECARS_REQUESTS` epoch.
    column_sidecars = retrieve_column_sidecars(beacon_block_root)
    return all(
        verify_data_column_sidecar(column_sidecar)
        and verify_data_column_sidecar_kzg_proofs(column_sidecar)
        for column_sidecar in column_sidecars
    )
```

## Handlers

### Modified `on_block`

*Ghi chú*: Thay đổi duy nhất là `is_data_available` không còn nhận
`blob_kzg_commitments` làm đầu vào.

```python
def on_block(store: Store, signed_block: SignedBeaconBlock) -> None:
    """
    Run ``on_block`` upon receiving a new block.
    """
    block = signed_block.message
    block_root = hash_tree_root(block)

    # Trả về sớm nếu block đã được biết
    if block_root in store.blocks:
        return

    # Parent block phải được biết
    assert block.parent_root in store.block_states
    # Tạo bản sao của state để tránh vấn đề mutability
    state = store.block_states[block.parent_root].copy()
    # Block không được nằm ở tương lai. Nếu có, phải trì hoãn xem xét cho đến khi nó thuộc về quá khứ.
    assert get_current_slot(store) >= block.slot

    # Kiểm tra block muộn hơn slot của finalized epoch (tối ưu để giảm số lần gọi get_ancestor)
    finalized_slot = compute_start_slot_at_epoch(store.finalized_checkpoint.epoch)
    assert block.slot > finalized_slot
    # Kiểm tra block là hậu duệ của finalized block tại slot của finalized checkpoint
    finalized_checkpoint_block = get_checkpoint_block(
        store,
        block.parent_root,
        store.finalized_checkpoint.epoch,
    )
    assert store.finalized_checkpoint.root == finalized_checkpoint_block

    # [Modified in Fulu:EIP7594]
    # Kiểm tra blob data có sẵn có không
    # Nếu không, payload này CÓ THỂ (MAY) được đưa vào hàng đợi và xem xét lại khi blob data sẵn có
    assert is_data_available(block_root)

    # Kiểm tra block hợp lệ và tính post-state
    state_transition(state, signed_block, validate_result=True)

    # Tính head trước khi áp dụng block
    head = get_head(store)
    # Thêm block mới vào store
    store.blocks[block_root] = block
    # Thêm state mới của block này vào store
    store.block_states[block_root] = state

    record_block_timeliness(store, block_root)
    update_proposer_boost_root(store, head.root, block_root)

    # Cập nhật các checkpoint trong store nếu cần
    update_checkpoints(store, state.current_justified_checkpoint, state.finalized_checkpoint)

    # Chủ động tính unrealized justification và finality.
    compute_pulled_up_tip(store, block_root)
```
