# Sanity blocks testing

Các sanity test bao phủ việc xử lý một chuỗi gồm một hoặc nhiều block, nhằm kiểm
tra các thay đổi phổ biến.

## Test case format

### `meta.yaml`

```yaml
description: string            -- Optional. Description of test case, purely for debugging purposes.
bls_setting: int               -- see general test-format spec.
reveal_deadlines_setting: int  -- see general test-format spec.
blocks_count: int              -- the number of blocks processed in this test.
```

> 💡 Ghi chú: `description` là mô tả tùy chọn, chỉ phục vụ debug;
> `bls_setting` và `reveal_deadlines_setting` xem trong spec test-format chung;
> `blocks_count` là số block được xử lý trong test này.

### `pre.ssz_snappy`

Một `BeaconState` mã hóa SSZ-snappy: state trước khi chạy các block transition.

### `blocks_<index>.ssz_snappy`

Một chuỗi file, với `<index>` nằm trong khoảng `[0, blocks_count)`. Các block
phải được xử lý theo thứ tự, theo đúng hàm transition chính (tức là vẫn xử lý
slot transition và epoch transition giữa các block như bình thường).

Mỗi file là một `SignedBeaconBlock` mã hóa SSZ-snappy.

### `post.ssz_snappy`

Một `BeaconState` mã hóa SSZ-snappy: state sau khi áp dụng các block transition.

## Condition

State thu được phải khớp với state `post` mong đợi; hoặc nếu state `post` bị để
trống, handler phải reject chuỗi block này vì không hợp lệ.
