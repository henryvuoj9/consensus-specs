# Forks

Mục đích của các fork test là đảm bảo một state trước fork (pre-fork) có thể
được chuyển đổi thành một state hợp lệ sau fork (post-fork), bằng cách dùng hàm
`upgrade` có trong spec `fork.md` tương ứng.

Chỉ có một handler duy nhất: `fork`. Mọi fork (sau genesis) đều được xử lý với
cùng một format, và ranh giới fork (fork boundary) cụ thể đang được kiểm thử
được ghi trong `meta.yaml`.

## Test case format

### `meta.yaml`

Một file yaml cho biết ranh giới fork nào đang được kiểm thử.

```yaml
fork: str    -- Fork being transitioned to
```

#### Fork strings

Bảng tra các chuỗi `fork` hợp lệ có thể xuất hiện trong `meta.yaml`

| String ID   | Pre-fork | Post-fork | Function               |
| ----------- | -------- | --------- | ---------------------- |
| `altair`    | Phase 0  | Altair    | `upgrade_to_altair`    |
| `bellatrix` | Altair   | Bellatrix | `upgrade_to_bellatrix` |

### `pre.ssz_snappy`

Một `BeaconState` được mã hóa SSZ-snappy: state trước khi chạy fork transition.

### `post.ssz_snappy`

Một `BeaconState` được mã hóa SSZ-snappy: state sau khi áp dụng fork transition.

*Lưu ý*: Kiểu dữ liệu này là `BeaconState` của fork mới và *không* cùng kiểu với
`pre`.

## Processing

Để xử lý test này, truyền `pre` vào hàm upgrade được xác định bởi giá trị `fork`
trong `meta.yaml`.

## Condition

State thu được phải khớp với `post` mong đợi.
