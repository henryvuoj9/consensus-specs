# Genesis validity testing

Kiểm tra một genesis state có hợp lệ hay không, tức là nó có đủ điều kiện để
kích hoạt khởi chạy chain hay không.

## Test case format

### `meta.yaml`

Một file yaml giúp đọc số lượng deposit:

```yaml
description: string    -- Optional. Description of test case, purely for debugging purposes.
```

### `genesis.ssz_snappy`

Một `BeaconState` được mã hóa SSZ-snappy: state cần được xác thực như một ứng
viên genesis.

### `is_valid.yaml`

Một giá trị boolean: true nếu genesis state được coi là hợp lệ để khởi chạy,
false nếu ngược lại.

## Processing

Để xử lý dữ liệu, gọi `is_valid_genesis_state(genesis)`.

## Condition

Kết quả của lời gọi `is_valid_genesis_state(genesis)` phải khớp với giá trị
boolean `is_valid` mong đợi.
