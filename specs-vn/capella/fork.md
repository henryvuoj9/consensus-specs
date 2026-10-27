# Capella -- Fork Logic

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Configs](#configs)
- [Fork to Capella](#fork-to-capella)
  - [Fork trigger](#fork-trigger)
  - [Upgrading the state](#upgrading-the-state)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả quy trình nâng cấp lên Capella.

## Configs

| Name                   | Value                                            |
| ---------------------- | ------------------------------------------------ |
| `CAPELLA_FORK_VERSION` | `Version("0x03000000")`                          |
| `CAPELLA_FORK_EPOCH`   | `Epoch(194048)` (April 12, 2023, 10:27:35pm UTC) |

## Fork to Capella

### Fork trigger

Fork được kích hoạt tại epoch `CAPELLA_FORK_EPOCH`.

*Lưu ý*: Đối với các mạng thuần Capella (khởi chạy trực tiếp từ Capella), hàm
`upgrade_to_capella` được áp dụng để chuyển genesis state sang fork này.

### Upgrading the state

Nếu `state.slot % SLOTS_PER_EPOCH == 0` và
`compute_epoch_at_slot(state.slot) == CAPELLA_FORK_EPOCH`, một thay đổi state bất
thường (irregular state change) sẽ được thực hiện để nâng cấp lên Capella.

Việc nâng cấp diễn ra sau khi vòng lặp bên trong của `process_slots` hoàn tất —
vòng lặp này đặt `state.slot` bằng `CAPELLA_FORK_EPOCH * SLOTS_PER_EPOCH`. Cần
cẩn thận khi chuyển qua ranh giới fork, vì các implementation sẽ cần một
[state transition function](../phase0/beacon-chain.md#beacon-chain-state-transition-function)
đã được sửa đổi, khác với tài liệu Phase 0. Cụ thể, hàm `state_transition` bên
ngoài được định nghĩa trong tài liệu Phase 0 sẽ không cho biết chính xác slot
fork để thực hiện nâng cấp khi có các slot bị bỏ qua (skipped slot, không có
block) tại ranh giới fork. Thay vào đó, logic này phải nằm bên trong
`process_slots`.

> 💡 Ghi chú: Các trường mới được khởi tạo như sau: `withdrawals_root` trong
> execution payload header được đặt về `Root()` rỗng, `next_withdrawal_index` và
> `next_withdrawal_validator_index` bắt đầu từ 0, còn `historical_summaries` là
> danh sách rỗng. `historical_roots` được giữ nguyên (và từ nay bị đóng băng).

```python
def upgrade_to_capella(pre: bellatrix.BeaconState) -> BeaconState:
    epoch = bellatrix.get_current_epoch(pre)
    latest_execution_payload_header = ExecutionPayloadHeader(
        parent_hash=pre.latest_execution_payload_header.parent_hash,
        fee_recipient=pre.latest_execution_payload_header.fee_recipient,
        state_root=pre.latest_execution_payload_header.state_root,
        receipts_root=pre.latest_execution_payload_header.receipts_root,
        logs_bloom=pre.latest_execution_payload_header.logs_bloom,
        prev_randao=pre.latest_execution_payload_header.prev_randao,
        block_number=pre.latest_execution_payload_header.block_number,
        gas_limit=pre.latest_execution_payload_header.gas_limit,
        gas_used=pre.latest_execution_payload_header.gas_used,
        timestamp=pre.latest_execution_payload_header.timestamp,
        extra_data=pre.latest_execution_payload_header.extra_data,
        base_fee_per_gas=pre.latest_execution_payload_header.base_fee_per_gas,
        block_hash=pre.latest_execution_payload_header.block_hash,
        transactions_root=pre.latest_execution_payload_header.transactions_root,
        # [New in Capella]
        withdrawals_root=Root(),
    )
    post = BeaconState(
        genesis_time=pre.genesis_time,
        genesis_validators_root=pre.genesis_validators_root,
        slot=pre.slot,
        fork=Fork(
            previous_version=pre.fork.current_version,
            # [Modified in Capella]
            current_version=CAPELLA_FORK_VERSION,
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
        latest_execution_payload_header=latest_execution_payload_header,
        # [New in Capella]
        next_withdrawal_index=WithdrawalIndex(0),
        # [New in Capella]
        next_withdrawal_validator_index=ValidatorIndex(0),
        # [New in Capella]
        historical_summaries=HistoricalSummaries(),
    )

    return post
```
