# Sanity slots testing

Các sanity test bao phủ việc xử lý một chuỗi gồm một hoặc nhiều transition qua
slot trống (không có block), nhằm kiểm tra các thay đổi phổ biến.

## Test case format

### `meta.yaml`

```yaml
description: string    -- Optional. Description of test case, purely for debugging purposes.
bls_setting: int       -- see general test-format spec.
```

### `pre.ssz_snappy`

Một `BeaconState` dạng SSZ-snappy: state trước khi chạy các transition.

Cũng có sẵn dưới dạng `pre.ssz_snappy`.

### `slots.yaml`

Một số nguyên: số lượng slot cần xử lý (tức là độ chênh lệch slot giữa pre và
post), luôn là số dương.

### `post.ssz_snappy`

Một `BeaconState` dạng SSZ-snappy: state sau khi áp dụng các transition.

Cũng có sẵn dưới dạng `post.ssz_snappy`.

### Processing

Transition chỉ theo thời gian thuần túy, không có block, được gọi là
`process_slots(state, slot)` trong spec. Nó thực hiện state-caching (slot
transition thuần túy) và epoch processing (cứ mỗi E slot).

Để xử lý dữ liệu, gọi `process_slots(pre, pre.slot + N)`.

## Condition

State thu được phải khớp với state `post` mong đợi.
