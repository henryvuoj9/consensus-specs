# Genesis creation testing

Kiểm thử việc khởi tạo một genesis state dựa trên Eth1 data.

## Test case format

### `eth1.yaml`

```yaml
eth1_block_hash: Bytes32  -- A `Bytes32` hex encoded, with prefix 0x. The root of the Eth1 block. E.g. "0x4242424242424242424242424242424242424242424242424242424242424242"
eth1_timestamp: int       -- An integer. The timestamp of the block, in seconds.
```

### `meta.yaml`

Một file yaml giúp đọc số lượng deposit:

```yaml
description: string             -- Optional. Description of test case, purely for debugging purposes.
deposits_count: int             -- Amount of deposits.
execution_payload_header: bool  -- `execution_payload_header` field is filled or not. If `true`, `execution_payload_header.ssz_snappy` file exists.
```

### `deposits_<index>.ssz_snappy`

Một chuỗi các file, với `<index>` nằm trong khoảng `[0, deposits_count)`. Các
deposit cần được xử lý theo đúng thứ tự. Mỗi file là một object `Deposit` được
mã hóa SSZ-snappy.

### `execution_payload_header.ssz_snappy`

*Lưu ý*: Tham số này chỉ được thêm vào từ Bellatrix và các fork sau đó.

Execution payload header dùng để khởi tạo state. Một object `BeaconState` được
mã hóa SSZ-snappy.

### `state.ssz_snappy`

Genesis state mong đợi. Một object `BeaconState` được mã hóa SSZ-snappy.

## Processing

Để xử lý test này, hãy xây dựng một genesis state với `eth1_block_hash`,
`eth1_timestamp` và `deposits` được cung cấp:
`initialize_beacon_state_from_eth1(eth1_block_hash, eth1_timestamp, deposits)`,
như được mô tả trong spec beacon-chain.

## Condition

State thu được phải khớp với `state` mong đợi.
