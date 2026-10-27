# Test format: shuffling

Runner của loại test Shuffling chỉ có một handler duy nhất: `core`.

Tuy nhiên, điều này không có nghĩa là phạm vi kiểm thử bị giới hạn. Các client
có thể tiếp cận shuffling theo những cách khác nhau, để tối ưu hóa, cũng như để
hỗ trợ các kiểu tra cứu nâng cao về lại lịch sử cũ.

Với người hiện thực (implementer), các test runner có thể kiểm thử theo những
cách sau:

1. Chỉ test permute-index: chạy nó cho từng index `i` trong `range(count)`, và
   so sánh với `mapping[i]` mong đợi (cách hiện thực mặc định của spec).
2. Test un-permute-index (tra cứu ngược; hiện thực bằng cách chạy các vòng
   shuffling theo thứ tự ngược, từ `round_count-1` về `0`).
3. Test complete shuffle đã tối ưu, trong đó toàn bộ các index được shuffle cùng
   lúc; kiểm tra toàn bộ đầu ra trong một lần.
4. Test complete shuffle theo chiều ngược (đảo thứ tự các vòng, giống #2).

## Test case format

### `mapping.yaml`

```yaml
seed: bytes32
count: int
mapping: List[int]
```

- Giá trị `bytes32` được mã hóa thành chuỗi hexadecimal, có tiền tố `0x`.
- Các số nguyên là validator index. Kiểu của chúng là `Uint64`, nhưng trên thực
  tế không lớn đến vậy.

`count` chỉ định kích thước của validator registry. Cần tính shuffling cho các
index `0, 1, 2, 3, ..., count (không bao gồm count)`.

`seed` là shuffling seed thô, được truyền vào permute-index (hoặc vào cách
shuffling đã tối ưu).

`mapping` là một mảng tra cứu, được xây dựng bằng
`[spec.compute_shuffled_index(i, count, seed) for i in range(count)]`. Tức là
`mapping[i]` là vị trí sau khi shuffle của `i`.

## Condition

Danh sách thu được phải khớp với đầu ra mong đợi sau khi shuffle đầu vào ngầm
định, sử dụng `seed` đã cho. Đầu ra được kiểm tra bằng `mapping`, tùy theo cách
kiểm thử shuffling (ví dụ có thể là shuffling ngược).
