# Capella -- Fork Choice

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Protocols](#protocols)
  - [`ExecutionEngine`](#executionengine)
    - [Modified `notify_forkchoice_updated`](#modified-notify_forkchoice_updated)
- [Helpers](#helpers)
  - [Modified `PayloadAttributes`](#modified-payloadattributes)
- [Handlers](#handlers)
  - [Modified `on_block`](#modified-on_block)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả các thay đổi của fork choice theo bản nâng cấp Capella.

Trừ khi được nêu rõ, toàn bộ chức năng trước đó từ
[Bellatrix](../bellatrix/fork-choice.md) đều được kế thừa.

## Protocols

### `ExecutionEngine`

#### Modified `notify_forkchoice_updated`

Thay đổi duy nhất nằm ở container `PayloadAttributes`, được bổ sung thêm trường
`withdrawals`. Ngoài ra, `notify_forkchoice_updated` kế thừa toàn bộ chức năng
trước đó.

```python
def notify_forkchoice_updated(
    self: ExecutionEngine,
    head_block_hash: Hash32,
    safe_block_hash: Hash32,
    finalized_block_hash: Hash32,
    payload_attributes: PayloadAttributes | None,
) -> PayloadId | None: ...
```

## Helpers

### Modified `PayloadAttributes`

`PayloadAttributes` được mở rộng thêm trường `withdrawals`.

> 💡 Ghi chú: Khi yêu cầu execution engine xây dựng payload mới, consensus client
> phải truyền danh sách withdrawal kỳ vọng (tính bằng `get_expected_withdrawals`)
> để execution engine đưa chúng vào payload.

```python
@dataclass
class PayloadAttributes:
    timestamp: Uint64
    prev_randao: Bytes32
    suggested_fee_recipient: ExecutionAddress
    # [New in Capella]
    withdrawals: Sequence[Withdrawal]
```

## Handlers

### Modified `on_block`

*Lưu ý*: Thay đổi duy nhất là loại bỏ bước kiểm tra các điều kiện của merge
transition block (block chuyển tiếp lúc merge), vì quá trình merge đã hoàn tất
trước Capella.

```python
def on_block(store: Store, signed_block: SignedBeaconBlock) -> None:
    """
    Run ``on_block`` upon receiving a new block.
    """
    block = signed_block.message
    block_root = hash_tree_root(block)

    # Trả về sớm nếu block đã được biết đến
    if block_root in store.blocks:
        return

    # Block cha phải đã được biết đến
    assert block.parent_root in store.block_states
    # Block không được thuộc về tương lai. Nếu có, phải trì hoãn xem xét nó cho đến khi thời điểm của nó đã qua.
    assert get_current_slot(store) >= block.slot

    # Kiểm tra block nằm sau slot của finalized epoch (tối ưu để giảm số lần gọi get_ancestor)
    finalized_slot = compute_start_slot_at_epoch(store.finalized_checkpoint.epoch)
    assert block.slot > finalized_slot
    # Kiểm tra block là hậu duệ của finalized block tại slot của finalized checkpoint
    finalized_checkpoint_block = get_checkpoint_block(
        store,
        block.parent_root,
        store.finalized_checkpoint.epoch,
    )
    assert store.finalized_checkpoint.root == finalized_checkpoint_block

    # Kiểm tra block hợp lệ và tính post-state
    # Tạo bản sao của state để tránh vấn đề về tính khả biến (mutability)
    state = store.block_states[block.parent_root].copy()
    state_transition(state, signed_block, validate_result=True)

    # Tính head trước khi áp dụng block
    head = get_head(store)
    # Thêm block mới vào store
    store.blocks[block_root] = block
    # Thêm state mới ứng với block này vào store
    store.block_states[block_root] = state

    record_block_timeliness(store, block_root)
    update_proposer_boost_root(store, head.root, block_root)

    # Cập nhật các checkpoint trong store nếu cần
    update_checkpoints(store, state.current_justified_checkpoint, state.finalized_checkpoint)

    # Tính trước (eager) justification và finality chưa hiện thực hóa (unrealized).
    compute_pulled_up_tip(store, block_root)
```
