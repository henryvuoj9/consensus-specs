# Fast confirmation tests

Mục đích của các fast confirmation test là cung cấp độ bao phủ kiểm thử cho Fast
Confirmation Rule (quy tắc xác nhận nhanh). Test format này mở rộng test format
[Fork choice](../fork_choice/README.md) bằng cách bổ sung các bước kiểm tra
(check) để xác minh trạng thái của fast confirmation store.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Test case format](#test-case-format)
  - [`steps.yaml`](#stepsyaml)
    - [`on_fast_confirmation` execution](#on_fast_confirmation-execution)
    - [Checks step](#checks-step)

<!-- mdformat-toc end -->

## Test case format

### `steps.yaml`

#### `on_fast_confirmation` execution

Không có bước thực thi `on_fast_confirmation` tường minh nào trong `steps.yaml`.
Test generator ngầm chạy `on_fast_confirmation` vào đầu mỗi slot, sau khi tất cả
attestation của các slot trước đã được áp dụng vào fork choice `store`. Các bước
kiểm tra fast confirmation được sinh ra (yield) sau mỗi lần gọi
`on_fast_confirmation`.

#### Checks step

Các bước kiểm tra để xác minh trạng thái hiện tại của `fcr_store`:

```yaml
previous_epoch_observed_justified_checkpoint: {
    epoch: int,               -- Integer value from fast_confirmation_store.previous_epoch_observed_justified_checkpoint.epoch
    root: string,             -- Encoded 32-byte value from fast_confirmation_store.previous_epoch_observed_justified_checkpoint.root
}
current_epoch_observed_justified_checkpoint: {
    epoch: int,               -- Integer value from fast_confirmation_store.current_epoch_observed_justified_checkpoint.epoch
    root: string,             -- Encoded 32-byte value from fast_confirmation_store.current_epoch_observed_justified_checkpoint.root
}
previous_epoch_greatest_unrealized_checkpoint: {
    epoch: int,               -- Integer value from fast_confirmation_store.previous_epoch_greatest_unrealized_checkpoint.epoch
    root: string,             -- Encoded 32-byte value from fast_confirmation_store.previous_epoch_greatest_unrealized_checkpoint.root
}
previous_slot_head: string          -- Encoded 32-byte value of fast_confirmation_store.previous_slot_head
current_slot_head: string           -- Encoded 32-byte value of fast_confirmation_store.current_slot_head
confirmed_root: string              -- Encoded 32-byte value of fast_confirmation_store.confirmed_root
safe_execution_block_hash: string   -- [New in Bellatrix]
                                       Encoded 32-byte value of the response to get_safe_execution_block_hash(fast_confirmation_store) call
```

Ví dụ:

```yaml
- checks:
    time: 60
    head:
      slot: 9
      root: '0x74fd665ecd799b1a1a17cb62ff635d9209c77defe98bf1f6c92f9f3306125315'
    justified_checkpoint:
      epoch: 0
      root: '0xeb7ad3d90729a187da87dcf467eace66b12331f9fcbd38c26e9d94c1c5cbc26f'
    finalized_checkpoint:
      epoch: 0
      root: '0xeb7ad3d90729a187da87dcf467eace66b12331f9fcbd38c26e9d94c1c5cbc26f'
    proposer_boost_root: '0x0000000000000000000000000000000000000000000000000000000000000000'
    previous_epoch_observed_justified_checkpoint:
      epoch: 0
      root: '0xeb7ad3d90729a187da87dcf467eace66b12331f9fcbd38c26e9d94c1c5cbc26f'
    current_epoch_observed_justified_checkpoint:
      epoch: 0
      root: '0xeb7ad3d90729a187da87dcf467eace66b12331f9fcbd38c26e9d94c1c5cbc26f'
    previous_epoch_greatest_unrealized_checkpoint:
      epoch: 0
      root: '0xeb7ad3d90729a187da87dcf467eace66b12331f9fcbd38c26e9d94c1c5cbc26f'
    previous_slot_head: '0xc648137aa42ba6bde20090fc1cfb6382f37a8e79f159ca5e8b64870763d13f54'
    current_slot_head: '0x74fd665ecd799b1a1a17cb62ff635d9209c77defe98bf1f6c92f9f3306125315'
    confirmed_root: '0x74fd665ecd799b1a1a17cb62ff635d9209c77defe98bf1f6c92f9f3306125315'
```
