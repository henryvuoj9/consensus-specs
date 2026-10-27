# Electra -- Weak Subjectivity Guide

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Weak Subjectivity Period](#weak-subjectivity-period)
  - [Calculating the Weak Subjectivity Period](#calculating-the-weak-subjectivity-period)
    - [Modified `compute_weak_subjectivity_period`](#modified-compute_weak_subjectivity_period)
    - [Modified `is_within_weak_subjectivity_period`](#modified-is_within_weak_subjectivity_period)

<!-- mdformat-toc end -->

## Introduction

*(Giới thiệu)*

Tài liệu này là phần mở rộng của
[Phase 0 -- Weak Subjectivity Guide](../phase0/weak-subjectivity.md). Mọi hành vi
và định nghĩa trong tài liệu này, cũng như trong các tài liệu mà nó mở rộng, vẫn
được giữ nguyên trừ khi được ghi chú rõ ràng hoặc bị ghi đè.

Tài liệu này hướng dẫn triển khai các cơ chế bảo vệ weak subjectivity trong
Electra. Cách tính Weak Subjectivity Period (WSP) đã thay đổi trong Electra do
EIP-7251, vì EIP này tăng effective balance tối đa của validator và cho phép các
validator hợp nhất (consolidate) với nhau.

> 💡 Ghi chú: Weak Subjectivity Period là khoảng thời gian (tính bằng epoch) mà
> trong đó một checkpoint gần đây vẫn được coi là an toàn để node đồng bộ từ đó.
> Khi effective balance có thể lớn hơn và validator set thay đổi theo balance
> (churn tính theo balance thay vì số lượng validator), công thức tính WSP phải
> được cập nhật tương ứng.

## Weak Subjectivity Period

### Calculating the Weak Subjectivity Period

*(Tính toán Weak Subjectivity Period)*

#### Modified `compute_weak_subjectivity_period`

```python
def compute_weak_subjectivity_period(state: BeaconState) -> Epoch:
    """
    Returns the weak subjectivity period for the current ``state``.
    This computation takes into account the effect of:
        - validator set churn (bounded by ``get_balance_churn_limit()`` per epoch)
    A detailed calculation can be found at:
    https://notes.ethereum.org/@CarlBeek/electra_weak_subjectivity
    """
    t = get_total_active_balance(state)
    delta = get_balance_churn_limit(state)
    epochs_for_validator_set_churn = Epoch(SAFETY_DECAY * t // (2 * delta * 100))
    return MIN_VALIDATOR_WITHDRAWABILITY_DELAY + epochs_for_validator_set_churn
```

Bảng tham khảo nhanh về giá trị thực tế của các đại lượng này
([script tham khảo](https://gist.github.com/jtraglia/457fd9ae7d2080fef1e4034a39b80c46)):

| Safety Decay | Total Active Balance (ETH) | Weak Sub. Period (Epochs) |
| -----------: | -------------------------: | ------------------------: |
|           10 |                  1,048,576 |                       665 |
|           10 |                  2,097,152 |                     1,075 |
|           10 |                  4,194,304 |                     1,894 |
|           10 |                  8,388,608 |                     3,532 |
|           10 |                 16,777,216 |                     3,532 |
|           10 |                 33,554,432 |                     3,532 |

> 💡 Ghi chú: Có thể thấy WSP ngừng tăng khi total active balance đạt khoảng 8
> triệu ETH trở lên. Lý do là `get_balance_churn_limit` cũng tăng tỷ lệ thuận với
> total active balance (sau khi vượt mức tối thiểu), nên tỷ số `t / delta` trong
> công thức không đổi.

#### Modified `is_within_weak_subjectivity_period`

```python
def is_within_weak_subjectivity_period(
    store: Store, ws_state: BeaconState, ws_checkpoint: Checkpoint
) -> bool:
    # Clients may choose to validate the input state against the input Weak Subjectivity Checkpoint
    assert get_block_root(ws_state, ws_checkpoint.epoch) == ws_checkpoint.root
    assert compute_epoch_at_slot(ws_state.slot) == ws_checkpoint.epoch

    # [Modified in Electra]
    ws_period = compute_weak_subjectivity_period(ws_state)
    ws_state_epoch = compute_epoch_at_slot(ws_state.slot)
    current_epoch = compute_epoch_at_slot(get_current_slot(store))
    return current_epoch <= ws_state_epoch + ws_period
```
