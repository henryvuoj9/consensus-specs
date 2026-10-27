# Gloas -- Weak Subjectivity Guide

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Weak Subjectivity Period](#weak-subjectivity-period)
  - [Calculating the Weak Subjectivity Period](#calculating-the-weak-subjectivity-period)
    - [Modified `compute_weak_subjectivity_period`](#modified-compute_weak_subjectivity_period)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này là phần mở rộng của
[Electra -- Weak Subjectivity Guide](../electra/weak-subjectivity.md). Mọi hành vi
và định nghĩa trong tài liệu này, cũng như trong các tài liệu mà nó mở rộng, đều
được giữ nguyên trừ khi được ghi chú rõ hoặc bị ghi đè.

Tài liệu này hướng dẫn cách triển khai các cơ chế bảo vệ Weak Subjectivity
(tính chủ quan yếu) trong Gloas. Cách tính Weak Subjectivity Period (WSP) đã thay
đổi trong Gloas do EIP-8061, vốn tách churn cho activation, exit và consolidation
thành các tham số có thể điều chỉnh độc lập với nhau.

> 💡 Ghi chú: WSP là khoảng thời gian (tính bằng epoch) mà trong đó tập validator
> không thể thay đổi đủ nhiều để một checkpoint cũ trở nên không an toàn. Một node
> sync từ checkpoint cũ hơn WSP có thể bị lừa đi theo một chuỗi khác, nên cần lấy
> một weak subjectivity checkpoint đáng tin cậy gần đây hơn.

## Weak Subjectivity Period

### Calculating the Weak Subjectivity Period

#### Modified `compute_weak_subjectivity_period`

```python
def compute_weak_subjectivity_period(state: BeaconState) -> Epoch:
    """
    Returns the weak subjectivity period for the current ``state``.
    This computation takes into account the effect of:
        - exit churn (weighted 2/3)
        - activation churn (weighted 1/3)
        - consolidation churn (weighted 1)
    """
    t = get_total_active_balance(state)
    # [Modified in Gloas:EIP8061]
    delta = (
        2 * get_exit_churn_limit(state) // 3
        + get_activation_churn_limit(state) // 3
        + get_consolidation_churn_limit(state)
    )
    epochs_for_validator_set_churn = Epoch(SAFETY_DECAY * t // (2 * delta * 100))
    return MIN_VALIDATOR_WITHDRAWABILITY_DELAY + epochs_for_validator_set_churn
```

Bảng tham khảo ngắn dưới đây cho thấy các giá trị này trong thực tế
([script tham khảo](https://gist.github.com/jtraglia/2f9cf5c6f99a9cdf0dd1996ba3d14caf)):

| Safety Decay | Total Active Balance (ETH) | Weak Sub. Period (Epochs) |
| -----------: | -------------------------: | ------------------------: |
|           10 |                  1,048,576 |                       620 |
|           10 |                  2,097,152 |                       911 |
|           10 |                  4,194,304 |                     1,348 |
|           10 |                  8,388,608 |                     1,348 |
|           10 |                 16,777,216 |                     1,484 |
|           10 |                 33,554,432 |                     1,566 |
|           10 |                 67,108,864 |                     1,611 |
|           10 |                134,217,728 |                     1,635 |
