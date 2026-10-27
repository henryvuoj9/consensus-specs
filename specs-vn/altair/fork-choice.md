# Altair -- Fork Choice

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Helpers](#helpers)
  - [New `get_sync_message_due_ms`](#new-get_sync_message_due_ms)
  - [New `get_contribution_due_ms`](#new-get_contribution_due_ms)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả các thay đổi của fork choice trong bản nâng cấp Altair.

Trừ khi được nêu rõ, mọi chức năng trước đó từ
[Phase0](../phase0/fork-choice.md) đều được kế thừa nguyên vẹn.

## Helpers

### New `get_sync_message_due_ms`

Trả về thời điểm (tính bằng mili-giây kể từ đầu slot) mà thành viên sync
committee cần gửi sync committee message, được tính từ tỷ lệ
`SYNC_MESSAGE_DUE_BPS` (basis points, 1 bps = 1/10000) của độ dài slot.

```python
def get_sync_message_due_ms() -> Uint64:
    return get_slot_component_duration_ms(SYNC_MESSAGE_DUE_BPS)
```

### New `get_contribution_due_ms`

Trả về thời điểm (tính bằng mili-giây kể từ đầu slot) mà aggregator của sync
committee cần gửi sync committee contribution, tính theo tỷ lệ
`CONTRIBUTION_DUE_BPS` của độ dài slot.

```python
def get_contribution_due_ms() -> Uint64:
    return get_slot_component_duration_ms(CONTRIBUTION_DUE_BPS)
```
