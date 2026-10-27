# `LightClientUpdate` ranking tests

Loạt test này cung cấp các test vector tham chiếu để xác minh rằng các instance
`LightClientUpdate` được xếp hạng theo một thứ tự canonical (chuẩn, thống nhất
giữa các client).

## Test case format

### `meta.yaml`

```yaml
updates_count: int  -- integer, decimal
```

### `updates_<index>.ssz_snappy`

Một chuỗi các file, với `<index>` nằm trong khoảng `[0, updates_count)`, được
sắp xếp theo mức độ ưu tiên giảm dần theo `is_better_update` (update tốt nhất ở
index 0).

Mỗi file là một `LightClientUpdate` được mã hóa SSZ-snappy.

## Condition

Test runner cần load các object `update` được cung cấp và xác minh rằng
implementation cục bộ xếp hạng chúng theo đúng cùng thứ tự đó. Lưu ý rằng trong
phạm vi test này, các object `update` không bị giới hạn trong một sync committee
period duy nhất.
