# Single leaf merkle proof tests

Loạt test này cung cấp các test vector tham chiếu để xác minh việc tạo và kiểm
tra merkle proof một cách chính xác, dựa trên dữ liệu tĩnh.

## Test case format

Các test cho từng kiểu SSZ được nhóm vào một `suite` mang tên của kiểu SSZ đó.

### `object.ssz_snappy`

Một object được mã hóa SSZ-snappy, từ đó các dữ liệu khác được sinh ra. Kiểu SSZ
có thể được xác định từ tên `suite` của test.

### `proof.yaml`

Một proof cho giá trị leaf (một merkle root) tại generalized index `leaf_index`
trong `object` đã cho.

```yaml
leaf: Bytes32            # string, hex encoded, with 0x prefix
leaf_index: int          # integer, decimal
branch: list of Bytes32  # list, each element is a string, hex encoded, with 0x prefix
```

## Condition

Test runner có thể triển khai các assertion sau:

- Kiểm tra rằng `is_valid_merkle_branch` xác nhận `leaf` tại `leaf_index` là hợp
  lệ khi đối chiếu với `hash_tree_root(object)` và `branch`.
- Nếu implementation hỗ trợ tạo merkle proof, kiểm tra rằng proof do chính nó
  tạo ra khớp với `branch` được cung cấp trong test.
