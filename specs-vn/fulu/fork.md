# Fulu -- Fork Logic

*(Logic chuyển fork sang Fulu)*

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Configs](#configs)
- [Helpers](#helpers)
  - [New `initialize_proposer_lookahead`](#new-initialize_proposer_lookahead)
- [Fork to Fulu](#fork-to-fulu)
  - [Fork trigger](#fork-trigger)
  - [Upgrading the state](#upgrading-the-state)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả quy trình nâng cấp (upgrade) lên Fulu.

## Configs

Cảnh báo: cấu hình này chưa phải là bản cuối cùng.

| Name                | Value                                              |
| ------------------- | -------------------------------------------------- |
| `FULU_FORK_VERSION` | `Version("0x06000000")`                            |
| `FULU_FORK_EPOCH`   | `Epoch(411392)` (December 3, 2025, 09:49:11pm UTC) |

## Helpers

### New `initialize_proposer_lookahead`

> 💡 Ghi chú: Hàm này tính trước danh sách proposer index cho toàn bộ khoảng lookahead khả dụng, tức là epoch hiện tại cộng thêm `MIN_SEED_LOOKAHEAD` epoch tiếp theo (tổng cộng `MIN_SEED_LOOKAHEAD + 1` epoch). Kết quả được dùng để khởi tạo trường `proposer_lookahead` (EIP-7917) trong beacon state tại genesis và ngay sau khi fork.

```python
def initialize_proposer_lookahead(
    state: BeaconState,
) -> ProposerLookahead:
    """
    Return the proposer indices for the full available lookahead starting from current epoch.
    Used to initialize the ``proposer_lookahead`` field in the beacon state at genesis and after forks.
    """
    current_epoch = get_current_epoch(state)
    lookahead: list[ValidatorIndex] = []
    for i in range(MIN_SEED_LOOKAHEAD + 1):
        lookahead.extend(get_beacon_proposer_indices(state, current_epoch + i))
    return ProposerLookahead(data=lookahead)
```

## Fork to Fulu

### Fork trigger

Fork được kích hoạt tại epoch `FULU_FORK_EPOCH`.

*Lưu ý*: Với các mạng chạy Fulu thuần túy (tức là khởi chạy trực tiếp từ Fulu
ngay từ genesis), hàm `upgrade_to_fulu` được áp dụng để chuyển genesis state
sang fork này.

### Upgrading the state

Nếu `state.slot % SLOTS_PER_EPOCH == 0` và
`compute_epoch_at_slot(state.slot) == FULU_FORK_EPOCH`, một thay đổi state bất
thường (irregular state change — không đi qua state transition thông thường)
được thực hiện để nâng cấp lên Fulu.

> 💡 Ghi chú: Hàm `upgrade_to_fulu` sao chép nguyên vẹn mọi trường từ Electra
> `BeaconState`, chỉ cập nhật `fork` (`current_version` thành
> `FULU_FORK_VERSION`, `previous_version` là phiên bản hiện tại trước đó) và thêm
> trường mới `proposer_lookahead`. Trường này trước tiên được khởi tạo rỗng, sau
> đó được điền bằng `initialize_proposer_lookahead(post)` dựa trên state đã nâng
> cấp.

```python
def upgrade_to_fulu(pre: electra.BeaconState) -> BeaconState:
    epoch = electra.get_current_epoch(pre)
    post = BeaconState(
        genesis_time=pre.genesis_time,
        genesis_validators_root=pre.genesis_validators_root,
        slot=pre.slot,
        fork=Fork(
            previous_version=pre.fork.current_version,
            # [Modified in Fulu]
            current_version=FULU_FORK_VERSION,
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
        latest_execution_payload_header=pre.latest_execution_payload_header,
        next_withdrawal_index=pre.next_withdrawal_index,
        next_withdrawal_validator_index=pre.next_withdrawal_validator_index,
        historical_summaries=pre.historical_summaries,
        deposit_requests_start_index=pre.deposit_requests_start_index,
        deposit_balance_to_consume=pre.deposit_balance_to_consume,
        exit_balance_to_consume=pre.exit_balance_to_consume,
        earliest_exit_epoch=pre.earliest_exit_epoch,
        consolidation_balance_to_consume=pre.consolidation_balance_to_consume,
        earliest_consolidation_epoch=pre.earliest_consolidation_epoch,
        pending_deposits=pre.pending_deposits,
        pending_partial_withdrawals=pre.pending_partial_withdrawals,
        pending_consolidations=pre.pending_consolidations,
        # [New in Fulu:EIP7917]
        proposer_lookahead=ProposerLookahead(),
    )

    # [New in Fulu:EIP7917]
    post.proposer_lookahead = initialize_proposer_lookahead(post)

    return post
```
