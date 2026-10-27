# Test format: SSZ static types

Mục tiêu của loại test này là cung cấp cho các client một tham chiếu vững chắc
về cách các đối tượng SSZ đã biết cần được mã hóa. Mọi đối tượng được mô tả
trong spec Phase 0 đều được bao phủ. Điều này quan trọng, vì nhiều client
serialize/deserialize đối tượng trực tiếp vào struct/class và không hỗ trợ (hoặc
có cách thay thế cho) việc mã hóa/giải mã SSZ tổng quát (generic).

Test-format này đảm bảo các phép serialize trực tiếp như vậy đều được bao phủ.

Lưu ý rằng bộ test này không bao phủ trường hợp mã hóa không hợp lệ: các hiện
thực SSZ nên được gia cố trước các đầu vào không hợp lệ, dựa theo các SSZ test
khác cùng với fuzzing.

## Test case format

Mỗi kiểu SSZ là một `handler`, vì format khác nhau về mặt ngữ nghĩa: kiểu dữ
liệu là khác nhau.

Có thể duyệt qua các handler và chọn kiểu dựa theo tên handler. Các suite sau đó
có cùng format, nhưng mỗi suite chuyên về một chế độ ngẫu nhiên hóa
(randomization mode). Một số chế độ ngẫu nhiên hóa có thể chỉ sinh ra một test
case duy nhất (ví dụ trường hợp toàn số 0).

Các phần đầu ra gồm: `roots.yaml`, `serialized.ssz_snappy`, `value.yaml`

### `roots.yaml`

```yaml
root: bytes32         -- string, hash-tree-root of the value, hex encoded, with prefix 0x
```

> 💡 Ghi chú: `root` là chuỗi chứa hash-tree-root của giá trị, mã hóa hex, có
> tiền tố `0x`.

### `serialized.ssz_snappy`

Các byte đã được mã hóa SSZ-snappy.

### `value.yaml`

Cùng giá trị với `serialized.ssz_snappy`, nhưng biểu diễn dưới dạng YAML.

## Condition

Một test-runner có thể hiện thực các assertion sau:

- Nếu hiện thực hỗ trợ giải mã YAML cho đối tượng SSZ:
  - Serialization: sau khi parse `value`, SSZ-serialize nó: đầu ra phải khớp với
    `serialized`
  - Deserialization: SSZ-deserialize giá trị `serialized`, và kiểm tra xem nó có
    khớp với `value` đã parse hay không
- Nếu hiện thực không hỗ trợ giải mã YAML cho đối tượng SSZ:
  - Serialization theo 2 bước: deserialize `serialized`, rồi serialize lại kết
    quả, và kiểm tra các byte có khớp với `serialized` ban đầu hay không.
- Hash-tree-root: sau khi parse `value` (hoặc deserialize `serialized`), tính
  hash-tree-root của nó: đầu ra phải khớp với `root`
