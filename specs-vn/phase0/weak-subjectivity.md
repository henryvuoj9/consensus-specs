# Phase 0 -- Weak Subjectivity Guide

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Types](#types)
  - [`Ether`](#ether)
- [Constants](#constants)
- [Configs](#configs)
- [Weak Subjectivity Checkpoint](#weak-subjectivity-checkpoint)
- [Weak Subjectivity Period](#weak-subjectivity-period)
  - [Calculating the Weak Subjectivity Period](#calculating-the-weak-subjectivity-period)
    - [`compute_weak_subjectivity_period`](#compute_weak_subjectivity_period)
- [Weak Subjectivity Sync](#weak-subjectivity-sync)
  - [Weak Subjectivity Sync Procedure](#weak-subjectivity-sync-procedure)
  - [Checking for Stale Weak Subjectivity Checkpoint](#checking-for-stale-weak-subjectivity-checkpoint)
    - [`is_within_weak_subjectivity_period`](#is_within_weak_subjectivity_period)
- [Distributing Weak Subjectivity Checkpoints](#distributing-weak-subjectivity-checkpoints)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này hướng dẫn cách hiện thực các cơ chế bảo vệ weak subjectivity (tính
chủ quan yếu) trong Phase 0. Tài liệu vẫn đang trong quá trình hoàn thiện và có
thể thay đổi lớn. Để tìm hiểu thêm về weak subjectivity và lý do vì sao cần nó,
hãy tham khảo:

- [Weak Subjectivity in Ethereum Proof-of-Stake](https://notes.ethereum.org/@adiasg/weak-subjectvity-eth2)
- [Proof of Stake: How I Learned to Love Weak Subjectivity](https://blog.ethereum.org/2014/11/25/proof-stake-learned-love-weak-subjectivity/)

> 💡 Ghi chú: Trong proof-of-stake, một node mới (hoặc offline quá lâu) không
> thể chỉ dựa vào dữ liệu on-chain để phân biệt chain thật với một chain giả do
> các validator cũ (đã rút stake, không còn bị slashing đe dọa) dựng lại từ quá
> khứ (long-range attack). Vì vậy node cần một "điểm tin cậy" gần đây lấy từ
> nguồn bên ngoài — đó chính là weak subjectivity checkpoint.

## Prerequisites

Tài liệu này sử dụng các cấu trúc dữ liệu, hằng số, hàm và thuật ngữ từ
[Phase 0 -- The Beacon Chain](./beacon-chain.md) và
[Phase 0 -- Beacon Chain Fork Choice](./fork-choice.md).

## Types

### `Ether`

```python
class Ether(Uint64):
    """
    An amount in Ether, the standard unit of currency on Ethereum.
    """
```

*(Một lượng tính bằng Ether — đơn vị tiền tệ chuẩn trên Ethereum.)*

## Constants

| Name          | Value           |
| ------------- | --------------- |
| `ETH_TO_GWEI` | `Uint64(10**9)` |

## Configs

| Name           | Value        |
| -------------- | ------------ |
| `SAFETY_DECAY` | `Uint64(10)` |

## Weak Subjectivity Checkpoint

Bất kỳ object `Checkpoint` nào cũng có thể được dùng làm Weak Subjectivity
Checkpoint. Các Weak Subjectivity Checkpoint này được các nhà cung cấp phân
phối, được người dùng tải về và/hoặc được đóng gói sẵn trong client, rồi được
dùng làm đầu vào khi sync một client.

## Weak Subjectivity Period

Weak Subjectivity Period là số epoch gần nhất mà trong khoảng đó PHẢI có một
Weak Subjectivity Checkpoint, nhằm đảm bảo rằng: nếu một kẻ tấn công nắm quyền
kiểm soát tập validator ngay đầu khoảng thời gian đó và làm cho một `Checkpoint`
xung đột được finalized, thì kẻ tấn công sẽ bị slashing ít nhất một ngưỡng tối
thiểu.

`SAFETY_DECAY` được định nghĩa là tỷ lệ phần trăm tối đa có thể chấp nhận bị mất
trong biên an toàn một phần ba (one-third safety margin) của FFG finality. Do
đó, bất kỳ cuộc tấn công nào lợi dụng Weak Subjectivity Period vẫn có biên an
toàn ít nhất là `1/3 - SAFETY_DECAY/100`.

> 💡 Ghi chú: Với `SAFETY_DECAY = 10`, biên an toàn tối thiểu là
> `1/3 - 0.1 ≈ 23.3%` tổng stake — tức kẻ tấn công vẫn phải chịu bị slashing ít
> nhất khoảng chừng đó stake nếu muốn finalize một checkpoint xung đột.

### Calculating the Weak Subjectivity Period

Phân tích chi tiết về cách tính weak subjectivity period có trong
[báo cáo này](https://github.com/runtimeverification/beacon-chain-verification/blob/master/weak-subjectivity/weak-subjectivity-analysis.pdf).

*Lưu ý*: Các biểu thức trong báo cáo dùng phân số, trong khi consensus-specs chỉ
dùng phép tính số học `Uint64`. Các biểu thức đã được biến đổi để tránh phải
tính phân số; chi tiết có thể xem
[tại đây](https://www.overleaf.com/read/wgjzjdjpvpsd).

*Lưu ý*: Các phép tính ở đây dùng `Ether` thay vì `Gwei`, vì balance tính bằng
`Gwei` có độ lớn rất cao, có thể gây tràn số (overflow) khi tính toán bằng các
phép toán `Uint64`. Dùng `Ether` giúp giảm độ lớn của các thừa số nhân đi một
bậc `ETH_TO_GWEI` (`= 10**9`) và loại bỏ khả năng overflow trong `Uint64`.

#### `compute_weak_subjectivity_period`

```python
def compute_weak_subjectivity_period(state: BeaconState) -> Epoch:
    """
    Returns the weak subjectivity period for the current ``state``.
    This computation takes into account the effect of:
        - validator set churn (bounded by ``get_validator_churn_limit()`` per epoch), and
        - validator balance top-ups (bounded by ``MAX_DEPOSITS * SLOTS_PER_EPOCH`` per epoch).
    A detailed calculation can be found at:
    https://github.com/runtimeverification/beacon-chain-verification/blob/master/weak-subjectivity/weak-subjectivity-analysis.pdf
    """
    ws_period = MIN_VALIDATOR_WITHDRAWABILITY_DELAY
    N = len(get_active_validator_indices(state, get_current_epoch(state)))
    t = get_total_active_balance(state) // N // ETH_TO_GWEI
    T = MAX_EFFECTIVE_BALANCE // ETH_TO_GWEI
    delta = get_validator_churn_limit(state)
    Delta = MAX_DEPOSITS * SLOTS_PER_EPOCH
    D = SAFETY_DECAY

    if t * (200 + 12 * D) > T * (200 + 3 * D):
        epochs_for_validator_set_churn = (
            N * (t * (200 + 12 * D) - T * (200 + 3 * D)) // (600 * delta * (2 * t + T))
        )
        epochs_for_balance_top_ups = N * (200 + 3 * D) // (600 * Delta)
        ws_period += max(epochs_for_validator_set_churn, epochs_for_balance_top_ups)
    else:
        ws_period += 3 * N * D * t // (200 * Delta * (T - t))

    return ws_period
```

> 💡 Ghi chú: Hàm trả về weak subjectivity period cho `state` hiện tại, có tính
> đến hai yếu tố: (1) validator set churn — số validator vào/ra mỗi epoch, bị
> giới hạn bởi `get_validator_churn_limit()`; và (2) việc nạp thêm balance
> (top-up) cho validator — bị giới hạn bởi `MAX_DEPOSITS * SLOTS_PER_EPOCH` mỗi
> epoch. Giá trị khởi điểm là `MIN_VALIDATOR_WITHDRAWABILITY_DELAY`; ý nghĩa
> các biến: `N` là số validator đang active, `t` là balance trung bình (ETH),
> `T` là effective balance tối đa (ETH), `delta` là churn limit, `Delta` là số
> deposit tối đa mỗi epoch, `D` là `SAFETY_DECAY`.

Bảng tham khảo nhanh cho thấy các giá trị này trên thực tế
([script tham khảo](https://gist.github.com/adiasg/3aceab409b36aa9a9d9156c1baa3c248)):

| Safety Decay | Avg. Val. Balance (ETH) | Val. Count | Weak Sub. Period (Epochs) |
| ------------ | ----------------------- | ---------- | ------------------------- |
| 10           | 28                      | 32768      | 504                       |
| 10           | 28                      | 65536      | 752                       |
| 10           | 28                      | 131072     | 1248                      |
| 10           | 28                      | 262144     | 2241                      |
| 10           | 28                      | 524288     | 2241                      |
| 10           | 28                      | 1048576    | 2241                      |
| 10           | 32                      | 32768      | 665                       |
| 10           | 32                      | 65536      | 1075                      |
| 10           | 32                      | 131072     | 1894                      |
| 10           | 32                      | 262144     | 3532                      |
| 10           | 32                      | 524288     | 3532                      |
| 10           | 32                      | 1048576    | 3532                      |

## Weak Subjectivity Sync

Client SHOULD (nên) cho phép người dùng nhập một Weak Subjectivity Checkpoint
khi khởi động, và đảm bảo rằng mọi lần sync thành công đều dẫn tới Weak
Subjectivity Checkpoint đã cho, nằm trên canonical chain (chain chính thức).
Nếu không thể sync như vậy, client SHOULD coi đây là lỗi nghiêm trọng và không
thể khôi phục.

### Weak Subjectivity Sync Procedure

1. Nhập Weak Subjectivity Checkpoint dưới dạng tham số CLI theo định dạng
   `block_root:epoch_number`, trong đó `block_root` (chuỗi hex 32 byte có tiền
   tố "0x") và `epoch_number` (số nguyên) biểu diễn một `Checkpoint` hợp lệ. Ví
   dụ về định dạng:

   ```
   0x8584188b86a9296932785cc2827b925f9deebacce6d72ad8d53171fa046b43d9:9544
   ```

2. Kiểm tra các yêu cầu về weak subjectivity:

   - *NẾU* `epoch_number > store.finalized_checkpoint.epoch` (checkpoint nằm
     phía trước điểm đã finalized cục bộ), thì trong quá trình sync block phải
     *ASSERT* rằng block có root `block_root` nằm trên đường sync tại epoch
     `epoch_number`. Nếu assert này thất bại, phát ra lỗi nghiêm trọng có mô tả
     rõ ràng, rồi thoát process của client.
   - *NẾU* `epoch_number <= store.finalized_checkpoint.epoch` (checkpoint đã
     nằm trong phần chain đã finalized), thì *ASSERT* rằng block trên canonical
     chain tại epoch `epoch_number` có root là `block_root`. Nếu assert này thất
     bại, phát ra lỗi nghiêm trọng có mô tả rõ ràng, rồi thoát process của
     client.

### Checking for Stale Weak Subjectivity Checkpoint

Client MAY (có thể) chọn kiểm tra xem Weak Subjectivity Checkpoint đầu vào có bị
cũ (stale) tại thời điểm khởi động hay không. Để hỗ trợ cơ chế này, client cần
nhận state tại Weak Subjectivity Checkpoint dưới dạng tham số CLI (hoặc tải
state tương ứng với Weak Subjectivity Checkpoint đầu vào từ một nguồn nào đó).
Việc kiểm tra có thể được hiện thực như sau:

#### `is_within_weak_subjectivity_period`

```python
def is_within_weak_subjectivity_period(
    store: Store, ws_state: BeaconState, ws_checkpoint: Checkpoint
) -> bool:
    # Client có thể chọn kiểm tra state đầu vào có khớp với Weak Subjectivity Checkpoint đầu vào hay không
    assert get_block_root(ws_state, ws_checkpoint.epoch) == ws_checkpoint.root
    assert compute_epoch_at_slot(ws_state.slot) == ws_checkpoint.epoch

    ws_period = compute_weak_subjectivity_period(ws_state)
    ws_state_epoch = compute_epoch_at_slot(ws_state.slot)
    current_epoch = compute_epoch_at_slot(get_current_slot(store))
    return current_epoch <= ws_state_epoch + ws_period
```

> 💡 Ghi chú: Nói cách khác, checkpoint được coi là còn hiệu lực nếu epoch hiện
> tại chưa vượt quá epoch của `ws_state` cộng với weak subjectivity period tính
> từ chính `ws_state` đó.

## Distributing Weak Subjectivity Checkpoints

Phần này sẽ sớm được cập nhật.
