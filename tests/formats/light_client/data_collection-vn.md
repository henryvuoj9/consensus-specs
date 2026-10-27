# Light client data collection tests

Loạt test này cung cấp các test vector tham chiếu để xác minh rằng một full node
thu thập đúng dữ liệu canonical (dữ liệu thuộc chain chính tắc) để phục vụ cho
các light client — những light client triển khai light client sync protocol để
đồng bộ tới block header mới nhất.

## Test case format

### `initial_state.ssz_snappy`

Một object kiểu `BeaconState` được mã hóa SSZ-snappy, dùng để khởi tạo
blockchain. `slot` của state này được căn theo epoch (tức là slot đầu tiên của
một epoch).

### `steps.yaml`

Các bước cần thực thi theo thứ tự.

#### `new_block` execution step

Block mới được mô tả trong bước test này cần được import, nhưng chưa trở thành
head.

```yaml
{
    fork_digest: string                -- encoded `ForkDigest`-context of `block`
    data: string                       -- name of the `*.ssz_snappy` file to load
                                          as a `SignedBeaconBlock` object
}
```

#### `new_head` execution step

Block được chỉ định (đã được import trước đó) cần trở thành head, điều này có
thể dẫn tới việc cập nhật:

- `LightClientUpdate` tốt nhất cho các sync committee period chưa được finalized.
- `LightClientFinalityUpdate` và `LightClientOptimisticUpdate` mới nhất.
- `Checkpoint` finalized mới nhất (xét trên tất cả các nhánh).
- Các instance `LightClientBootstrap` có sẵn cho các `Checkpoint` vừa được
  finalized.

```yaml
{
    head_block_root: Bytes32           -- string, hex encoded, with 0x prefix
    checks: {
        latest_finalized_checkpoint: { -- tracked across all branches
            epoch: int                 -- integer, decimal
            root: Bytes32              -- string, hex encoded, with 0x prefix
        }
        bootstraps: [                  -- one entry per `LightClientBootstrap`
            block_root: Bytes32        -- string, hex encoded, with 0x prefix
            bootstrap: {               -- only exists if a `LightClientBootstrap` is available
                fork_digest: string    -- encoded `ForkDigest`-context of `data`
                data: string           -- name of the `*.ssz_snappy` file to load
                                          as a `LightClientBootstrap` object
            }
        ]
        best_updates: [                -- one entry per sync committee period
            period: int                -- integer, decimal
            update: {                  -- only exists if a best `LightClientUpdate` is available
                fork_digest: string    -- encoded `ForkDigest`-context of `data`
                data: string           -- name of the `*.ssz_snappy` file to load
                                          as a `LightClientUpdate` object
            }
        ]
        latest_finality_update: {      -- only exists if a `LightClientFinalityUpdate` is available
            fork_digest: string        -- encoded `ForkDigest`-context of `data`
            data: string               -- name of the `*.ssz_snappy` file to load
                                          as a `LightClientFinalityUpdate` object
        }
        latest_optimistic_update: {    -- only exists if a `LightClientOptimisticUpdate` is available
            fork_digest: string        -- encoded `ForkDigest`-context of `data`
            data: string               -- name of the `*.ssz_snappy` file to load
                                          as a `LightClientOptimisticUpdate` object
        }
    }
}
```

## Condition

Test runner cần khởi tạo một blockchain đơn giản hóa từ `initial_state`. Một tín
hiệu bên ngoài (chính là các bước `new_head`) được dùng để điều khiển fork
choice, thay vì chạy thuật toán fork choice thật. Sau đó test runner thực thi
lần lượt tất cả các bước test, đồng thời thu thập light client data trong quá
trình thực thi. Sau mỗi bước `new_head`, test runner cần xác minh rằng light
client data đã thu thập khớp với các `checks` được cung cấp.
