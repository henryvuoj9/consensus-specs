# Gloas -- Fast Confirmation

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Fast Confirmation Rule](#fast-confirmation-rule)
  - [Helpers](#helpers)
    - [Modified `get_node_for_root`](#modified-get_node_for_root)
- [Safe execution block](#safe-execution-block)
  - [Modified `get_safe_execution_block_hash`](#modified-get_safe_execution_block_hash)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả các thay đổi đối với spec của fast confirmation rule (quy tắc
xác nhận nhanh) đi kèm bản nâng cấp Gloas.

> 💡 Ghi chú: Trong Gloas (EIP-7732, ePBS), beacon block và execution payload
> được tách rời; vì vậy mỗi node trong fork choice được định danh bởi cả block
> root lẫn trạng thái payload (`payload_status`). Các thay đổi dưới đây điều
> chỉnh fast confirmation rule cho phù hợp với mô hình này.

## Fast Confirmation Rule

### Helpers

#### Modified `get_node_for_root`

Hàm trả về `ForkChoiceNode` tương ứng với một block root. Trong Gloas, node được
tạo với `payload_status = PAYLOAD_STATUS_PENDING`, tức là chưa xét payload của
block đó là *empty* hay *full*.

```python
def get_node_for_root(block_root: Root) -> ForkChoiceNode:
    # [Modified in Gloas:EIP7732]
    return ForkChoiceNode(root=block_root, payload_status=PAYLOAD_STATUS_PENDING)
```

## Safe execution block

### Modified `get_safe_execution_block_hash`

*Ghi chú*: Trong Gloas, chỉ có payload cha (parent payload) của một beacon block
đã được xác nhận mới được coi là safe.

> 💡 Ghi chú: Beacon block đã xác nhận chỉ cam kết tới payload cha của nó (qua
> `parent_block_hash` trong bid); payload của chính block đó có thể chưa được
> công bố hoặc chưa được xác nhận. Do đó safe execution block hash là
> `parent_block_hash` trong execution payload bid của block đã xác nhận.

```python
def get_safe_execution_block_hash(fcr_store: FastConfirmationStore) -> Hash32:
    safe_block = fcr_store.store.blocks[fcr_store.confirmed_root]
    # [Modified in Gloas:EIP7732]
    return safe_block.body.signed_execution_payload_bid.message.parent_block_hash
```
