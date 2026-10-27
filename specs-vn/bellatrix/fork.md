# Bellatrix -- Fork Logic

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Configs](#configs)
- [Fork to Bellatrix](#fork-to-bellatrix)
  - [Fork trigger](#fork-trigger)
  - [Upgrading the state](#upgrading-the-state)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả quy trình nâng cấp (upgrade) lên Bellatrix.

## Configs

| Name                     | Value                                          |
| ------------------------ | ---------------------------------------------- |
| `BELLATRIX_FORK_VERSION` | `Version("0x02000000")`                        |
| `BELLATRIX_FORK_EPOCH`   | `Epoch(144896)` (Sept 6, 2022, 11:34:47am UTC) |

## Fork to Bellatrix

### Fork trigger

TBD (chưa xác định). Đồng thuận xã hội (social consensus), cùng với các điều kiện
của state như ranh giới epoch, finality, deposit, số lượng validator đang hoạt
động, v.v. có thể là một phần của quá trình quyết định kích hoạt fork. Hiện tại
ta giả định điều kiện kích hoạt sẽ xảy ra tại epoch `BELLATRIX_FORK_EPOCH`.

*Lưu ý*: Với các mạng chạy Bellatrix thuần (ngay từ genesis), hàm
`upgrade_to_bellatrix` được áp dụng để chuyển genesis state sang fork này.

### Upgrading the state

Tương tự như khi nâng cấp từ Phase0 lên Altair, hàm `state_transition` được sửa
đổi để nâng cấp `BeaconState`. Việc nâng cấp `BeaconState` được chạy như một phần
của `process_slots`, vì vậy các slot không có block được đề xuất (missing block)
không ảnh hưởng đến thời điểm nâng cấp.

Nếu `state.slot % SLOTS_PER_EPOCH == 0` và
`compute_epoch_at_slot(state.slot) == BELLATRIX_FORK_EPOCH`, một thay đổi state
bất thường (irregular state change) sẽ được thực hiện để nâng cấp lên Bellatrix.
Việc nâng cấp diễn ra sau khi vòng lặp bên trong của `process_slots` hoàn tất và
đã đặt `state.slot` bằng `BELLATRIX_FORK_EPOCH * SLOTS_PER_EPOCH`.

Khi nhiều lần nâng cấp được lên lịch vào cùng một epoch (thường gặp ở các mạng
thử nghiệm), tất cả các nâng cấp sẽ được chạy tuần tự trước khi tiếp tục state
transition thông thường.

```python
def upgrade_to_bellatrix(pre: altair.BeaconState) -> BeaconState:
    epoch = altair.get_current_epoch(pre)
    post = BeaconState(
        genesis_time=pre.genesis_time,
        genesis_validators_root=pre.genesis_validators_root,
        slot=pre.slot,
        fork=Fork(
            previous_version=pre.fork.current_version,
            # [Modified in Bellatrix]
            current_version=BELLATRIX_FORK_VERSION,
            epoch=epoch,
        ),
        latest_block_header=pre.latest_block_header,
        block_roots=pre.block_roots,
        state_roots=pre.state_roots,
        historical_roots=pre.historical_roots,
        eth1_data=pre.eth1_data,
        eth1_data_votes=pre.eth1_data_votes,
        eth1_deposit_index=pre.eth1_deposit_index,
        validators=pre.validators,
        balances=pre.balances,
        randao_mixes=pre.randao_mixes,
        slashings=pre.slashings,
        previous_epoch_participation=pre.previous_epoch_participation,
        current_epoch_participation=pre.current_epoch_participation,
        justification_bits=pre.justification_bits,
        previous_justified_checkpoint=pre.previous_justified_checkpoint,
        current_justified_checkpoint=pre.current_justified_checkpoint,
        finalized_checkpoint=pre.finalized_checkpoint,
        inactivity_scores=pre.inactivity_scores,
        current_sync_committee=pre.current_sync_committee,
        next_sync_committee=pre.next_sync_committee,
        # [New in Bellatrix]
        latest_execution_payload_header=ExecutionPayloadHeader.empty(),
    )

    return post
```
