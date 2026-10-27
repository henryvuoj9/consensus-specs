# Light client sync tests

Loạt test này cung cấp các test vector tham chiếu để xác minh rằng một light
client triển khai sync protocol có thể đồng bộ tới block header mới nhất.

## Test case format

### `meta.yaml`

```yaml
genesis_validators_root: Bytes32  -- string, hex encoded, with 0x prefix
trusted_block_root: Bytes32       -- string, hex encoded, with 0x prefix
bootstrap_fork_digest: string     -- encoded `ForkDigest`-context of `bootstrap`
store_fork_version: string        -- encoded `Version` identifying the `store` object's fork
```

### `bootstrap.ssz_snappy`

Một object `bootstrap` kiểu `LightClientBootstrap` được mã hóa SSZ-snappy, dùng
để khởi tạo một object `store` cục bộ kiểu `LightClientStore` cho fork
`store_fork_version`, bằng cách gọi
`initialize_light_client_store(trusted_block_rooot, bootstrap)`. Kiểu SSZ có thể
được xác định từ `bootstrap_fork_digest`.

Nếu fork được xác định bởi `store_fork_version` khác với fork được xác định bởi
`bootstrap_fork_digest`, object `bootstrap` có thể cần được upgrade trước khi
khởi tạo store.

### `steps.yaml`

Các bước cần thực thi theo thứ tự.

#### Checks to run after each step

Mỗi bước bao gồm các check để xác minh tác động mong đợi lên object `store`.

```yaml
finalized_header: {
    slot: int,                -- Integer value from store.finalized_header.beacon.slot
    beacon_root: string,      -- Encoded 32-byte value from store.finalized_header.beacon.hash_tree_root()
    execution_root: string,   -- From Capella onward; get_lc_execution_root(store.finalized_header)
}
optimistic_header: {
    slot: int,                -- Integer value from store.optimistic_header.beacon.slot
    beacon_root: string,      -- Encoded 32-byte value from store.optimistic_header.beacon.hash_tree_root()
    execution_root: string,   -- From Capella onward; get_lc_execution_root(store.optimistic_header)
}
```

#### `force_update` execution step

Hàm `process_light_client_store_force_update(store, current_slot)` cần được thực
thi với các tham số đã chỉ định:

```yaml
{
    current_slot: int                   -- integer, decimal
    checks: {<store_attribute>: value}  -- the assertions.
}
```

Sau bước này, object `store` có thể đã được cập nhật.

#### `process_update` execution step

Hàm
`process_light_client_update(store, update, current_slot, genesis_validators_root)`
cần được thực thi với các tham số đã chỉ định:

```yaml
{
    update_fork_digest: string          -- encoded `ForkDigest`-context of `update`
    update: string                      -- name of the `*.ssz_snappy` file to load
                                           as a `LightClientUpdate` object
    current_slot: int                   -- integer, decimal
    checks: {<store_attribute>: value}  -- the assertions.
}
```

Nếu fork được xác định bởi `store_fork_version` khác với fork được xác định bởi
`update_fork_digest`, object `update` có thể cần được upgrade trước khi xử lý
update.

Sau bước này, object `store` có thể đã được cập nhật.

#### `upgrade_store`

`store` cần được upgrade để phản ánh `store_fork_version` mới:

```yaml
{
    store_fork_version: string          -- encoded `Version` identifying the `store` object's fork
    checks: {<store_attribute>: value}  -- the assertions.
}
```

Sau bước này, object `store` có thể đã được cập nhật.

## Condition

Test runner cần khởi tạo một `LightClientStore` cục bộ bằng object `bootstrap`
được cung cấp. Sau đó thực thi lần lượt tất cả các bước test. Sau mỗi bước, test
runner cần xác minh rằng `store` thu được thỏa mãn các `checks` được cung cấp.
