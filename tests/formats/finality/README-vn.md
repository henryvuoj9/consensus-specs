# Finality tests

Mục đích của các test này là kiểm thử các quy tắc finality (tính chung cuộc).

- `finality`: các transition được kích hoạt bởi một hoặc nhiều block.

## Test case format

### `meta.yaml`

```yaml
description: string    -- Optional. Description of test case, purely for debugging purposes.
bls_setting: int       -- see general test-format spec.
blocks_count: int      -- the number of blocks processed in this test.
```

### `pre.ssz_snappy`

Một `BeaconState` được mã hóa SSZ-snappy: state trước khi chạy các block
transition.

Cũng có sẵn dưới dạng `pre.ssz_snappy`.

### `blocks_<index>.yaml`

Một chuỗi các file, với `<index>` nằm trong khoảng `[0, blocks_count)`. Các block
cần được xử lý theo đúng thứ tự, tuân theo hàm state transition chính (tức là
vẫn xử lý các slot transition và epoch transition giữa các block như bình
thường).

Mỗi file là một `SignedBeaconBlock` được mã hóa YAML.

Mỗi block cũng có sẵn dưới dạng `blocks_<index>.ssz_snappy`

### `post.ssz_snappy`

Một `BeaconState` được mã hóa SSZ-snappy: state sau khi áp dụng các block
transition.

## Condition

State thu được phải khớp với `post` state mong đợi; hoặc nếu `post` state bị để
trống (không có file), handler phải từ chối chuỗi block đó vì không hợp lệ.
