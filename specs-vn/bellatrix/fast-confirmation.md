# Bellatrix -- Fast Confirmation

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Safe execution block](#safe-execution-block)
  - [New `get_safe_execution_block_hash`](#new-get_safe_execution_block_hash)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả phần sửa đổi của đặc tả fast confirmation rule (quy tắc xác
nhận nhanh) đi kèm với Bellatrix.

## Safe execution block

Do Bellatrix đưa execution payload vào beacon block, hàm
`get_safe_execution_block_hash` được bổ sung. Hàm này trả về block hash của
payload nằm trong block được confirm (xác nhận) gần nhất. Block hash này được gửi
tới ExecutionEngine dưới dạng hash của safe block (block "an toàn").

> 💡 Ghi chú: Nói cách khác, consensus layer dùng kết quả của fast confirmation
> rule để báo cho execution layer biết block nào có thể coi là "safe" — mức độ
> tin cậy nằm giữa head (có thể bị reorg) và finalized (không thể đảo ngược).

### New `get_safe_execution_block_hash`

```python
def get_safe_execution_block_hash(fcr_store: FastConfirmationStore) -> Hash32:
    safe_block = fcr_store.store.blocks[fcr_store.confirmed_root]
    return safe_block.body.execution_payload.block_hash
```
