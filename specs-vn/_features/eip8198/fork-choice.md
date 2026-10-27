# EIP-8198 -- Beacon Chain Fork Choice

*Ghi chú*: Tài liệu này đang trong quá trình soạn thảo (work-in-progress), dành cho các nhà nghiên cứu và người triển khai client.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Helpers](#helpers)
  - [Modified `get_slot_component_duration_ms`](#modified-get_slot_component_duration_ms)

<!-- mdformat-toc end -->

## Introduction

EIP-8198 dùng `get_slot_durations` để ánh xạ thời gian thực (wall-clock) sang
slot, có tính đến các độ dài slot khác nhau trong lịch sử. Các hàm helper về
deadline chuyển cấu hình basis-point (phần vạn) được kế thừa thành độ lệch tính
bằng mili giây, dựa trên `SLOT_DURATION_MS_EIP8198`. Các fork sau nếu thay đổi
độ dài slot hoặc thời điểm thực hiện duty thì MUST tự định nghĩa quy tắc deadline
riêng của mình.

*Ghi chú*: Đặc tả này được xây dựng dựa trên [Heze](../../heze/fork-choice.md).

## Helpers

### Modified `get_slot_component_duration_ms`

```python
def get_slot_component_duration_ms(basis_points: Uint64) -> Uint64:
    """
    Calculate a slot component's duration using this fork's slot duration.
    """
    # [Modified in EIP8198]
    return basis_points * SLOT_DURATION_MS_EIP8198 // BASIS_POINTS
```
