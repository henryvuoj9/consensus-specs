# Rewards tests

Với mỗi test case, tất cả các hàm con tính rewards deltas (phần chênh lệch
reward/penalty) đều được kiểm thử. Không có yếu tố "thay đổi" (change) nào: đầu ra
reward/penalty là các hàm thuần túy (pure function), chỉ nhận pre-state làm đầu
vào. (Xem tài liệu về điều kiện test để biết cách chạy các test.)

`Deltas` được định nghĩa như sau:

```python
class Deltas(Container):
    rewards: List[Gwei, VALIDATOR_REGISTRY_LIMIT]
    penalties: List[Gwei, VALIDATOR_REGISTRY_LIMIT]
```

## Test case format

### `meta.yaml`

```yaml
description: string    -- Optional description of test case, purely for debugging purposes.
                          Tests should use the directory name of the test case as identifier, not the description.
```

> 💡 Ghi chú: `description` là mô tả tùy chọn, chỉ phục vụ debug — test nên dùng
> tên thư mục của test case làm định danh, không dùng description.

*Lưu ý*: Không có bước xác minh signature nào bên trong các hàm con tính reward.
Các test này có thể chạy an toàn dù bật hay tắt BLS.

### `pre.ssz_snappy`

Một `BeaconState` mã hóa SSZ-snappy: state trước khi chạy hàm con tính reward.

### `source_deltas.ssz_snappy`

Một `Deltas` mã hóa SSZ-snappy, biểu diễn reward và penalty được trả về bởi hàm
`get_source_deltas`.

### `target_deltas.ssz_snappy`

Một `Deltas` mã hóa SSZ-snappy, biểu diễn reward và penalty được trả về bởi hàm
`get_target_deltas`.

### `head_deltas.ssz_snappy`

Một `Deltas` mã hóa SSZ-snappy, biểu diễn reward và penalty được trả về bởi hàm
`get_head_deltas`.

### `inclusion_delay_deltas.ssz_snappy`

Một `Deltas` mã hóa SSZ-snappy, biểu diễn reward và penalty được trả về bởi hàm
`get_inclusion_delay_deltas`.

### `inactivity_penalty_deltas.ssz_snappy`

Một `Deltas` mã hóa SSZ-snappy, biểu diễn reward và penalty được trả về bởi hàm
`get_inactivity_penalty_deltas`.

## Condition

Một handler của test-runner `rewards` cần xử lý các test case này bằng cách gọi
hàm tính rewards deltas tương ứng cho từng bộ deltas.

Pre-state được cung cấp đã sẵn sàng để đưa trực tiếp vào từng hàm tính rewards
deltas.

Các `deltas` được cung cấp phải khớp với giá trị trả về của hàm deltas. Cụ thể,
điều sau phải đúng với mỗi bộ deltas:

```python
assert deltas.rewards == deltas_function(state)[0]
assert deltas.penalties == deltas_function(state)[1]
```
