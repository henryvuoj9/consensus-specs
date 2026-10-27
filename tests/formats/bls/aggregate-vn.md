# Test format: BLS signature aggregation

Việc aggregate (gộp) BLS signature kết hợp một chuỗi các signature thành một
signature duy nhất.

## Test case format

Dữ liệu test được khai báo trong file `data.yaml`:

```yaml
input: List[BLS Signature] -- list of input BLS signatures
output: BLS Signature -- expected output, single BLS signature or `null`.
```

- `input`: danh sách các BLS signature đầu vào; `output`: kết quả mong đợi, là
  một BLS signature duy nhất hoặc `null`.
- `BLS Signature` ở đây được mã hoá dưới dạng chuỗi: mã hoá hexa của 96 byte
  (192 nibble), có tiền tố `0x`.
- Giá trị output là `null` nếu input không hợp lệ.

Mọi trường kiểu byte(s) đều được mã hoá thành chuỗi, dạng hexa, có tiền tố
`0x`.

## Condition

Handler `aggregate` cần aggregate các signature trong `input`, và kết quả phải
khớp với `output` mong đợi.
