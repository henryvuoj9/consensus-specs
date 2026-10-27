# Report: `process_withdrawals` Input/Output Space

*Lưu ý*: Báo cáo này do AI tạo ra và không phải là nguồn tham chiếu chính thức (authoritative source of truth).

## Function Signature

```python
def process_withdrawals(state: BeaconState) -> None: ...
```

Vị trí định nghĩa:
[specs/gloas/beacon-chain.md](../../../../../../../specs/gloas/beacon-chain.md)

______________________________________________________________________

## Input Space (State Fields Read)

*(Các trường của beacon state mà hàm đọc vào)*

| Field | Type | Không gian giá trị (Value Space) | Mục đích (Purpose) |
| ----- | ---- | -------------------------------- | ------------------ |
| `state.slot` | `Slot` | `Uint64` trong [0, 2^64-1]. Dùng để suy ra `epoch = slot // SLOTS_PER_EPOCH`. Được so sánh với các trường `withdrawable_epoch`. | Tính epoch hiện tại |
| `state.latest_execution_payload_bid.block_hash` | `Hash32` | `Bytes32`. **Ràng buộc với** `latest_block_hash`: phải bằng nhau thì hàm mới thực thi (thoát sớm nếu khác nhau). | Kiểm tra block cha có "full" (có payload) hay không |
| `state.latest_block_hash` | `Hash32` | `Bytes32`. **Ràng buộc với** `latest_execution_payload_bid.block_hash` trong phép kiểm tra `is_parent_block_full()`. | So sánh với bid đã cam kết |
| `state.next_withdrawal_index` | `WithdrawalIndex` | `Uint64` trong [0, 2^64-1]. Tăng đơn điệu. Được gán cho từng withdrawal được tạo ra. | Withdrawal index bắt đầu |
| `state.next_withdrawal_validator_index` | `ValidatorIndex` | `Uint64` trong \[0, `len(validators)`-1\]. **Ràng buộc với** `len(validators)`: quay vòng bằng phép modulo. | Vị trí bắt đầu quét (sweep) validator |
| `state.next_withdrawal_builder_index` | `BuilderIndex` | `Uint64` trong \[0, `len(builders)`-1\]. **Ràng buộc với** `len(builders)`: quay vòng bằng phép modulo. | Vị trí bắt đầu quét (sweep) builder |
| `state.builders` | `List[Builder, BUILDER_REGISTRY_LIMIT]` | Độ dài trong [0, 2^40]. Là các tác nhân có stake riêng biệt, không làm nhiệm vụ validator. | Registry của builder |
| (in `builders`) `.pubkey` | `BLSPubkey` | `Bytes48`. Public key của builder. | Định danh builder |
| (in `builders`) `.execution_address` | `ExecutionAddress` | `Bytes20`. Địa chỉ nhận cho các withdrawal từ builder sweep. | Đích của sweep withdrawal |
| (in `builders`) `.balance` | `Gwei` | `Uint64`. Số dư stake của builder. Bị giảm theo số tiền rút. | Balance của builder dùng cho withdrawal |
| (in `builders`) `.withdrawable_epoch` | `Epoch` | `Uint64`. **Ràng buộc với** `state.slot`: builder sweep withdrawal sẵn sàng khi `<= current_epoch`. | Kiểm tra builder có đủ điều kiện sweep không |
| `state.builder_pending_withdrawals` | `List[BuilderPendingWithdrawal, BUILDER_PENDING_WITHDRAWALS_LIMIT]` | Độ dài trong [0, 2^20]. Được xử lý đầu tiên. Tối đa `MAX_WITHDRAWALS_PER_PAYLOAD - 1` phần tử có thể tạo ra withdrawal. | Duyệt các builder pending withdrawal |
| (in `builder_pending_withdrawals`) `.builder_index` | `BuilderIndex` | `Uint64` trong \[0, `len(builders)`-1\]. **Là chỉ số vào** `builders[]`. | Xác định builder trong registry |
| (in `builder_pending_withdrawals`) `.fee_recipient` | `ExecutionAddress` | `Bytes20`. Địa chỉ nhận withdrawal. Độc lập với `execution_address` của chính builder. | Đích của withdrawal |
| (in `builder_pending_withdrawals`) `.amount` | `Gwei` | `Uint64`. Số tiền yêu cầu. Thực tế = `min(amount, builder.balance)`. | Số tiền rút |
| `state.pending_partial_withdrawals` | `List[PendingPartialWithdrawal, PENDING_PARTIAL_WITHDRAWALS_LIMIT]` | Độ dài trong [0, 2^27]. Được xử lý thứ hai. Mỗi block xử lý tối đa `MAX_PENDING_PARTIALS_PER_WITHDRAWALS_SWEEP` (8) phần tử. | Duyệt các partial withdrawal |
| (in `pending_partial_withdrawals`) `.withdrawable_epoch` | `Epoch` | `Uint64`. **Ràng buộc với** `state.slot`: sẵn sàng khi `<= current_epoch`. Nếu `>`, vòng lặp xử lý dừng lại (break). | Kiểm tra withdrawal đã sẵn sàng chưa |
| (in `pending_partial_withdrawals`) `.validator_index` | `ValidatorIndex` | `Uint64` trong \[0, `len(validators)`-1\]. **Là chỉ số vào** `validators[]` và `balances[]`. | Xác định validator |
| (in `pending_partial_withdrawals`) `.amount` | `Gwei` | `Uint64`. Số tiền yêu cầu. Thực tế = `min(balance - MIN_ACTIVATION_BALANCE, amount)`. | Số tiền rút |
| `state.balances[*]` | `Gwei` | `Uint64` trong [0, 2^64-1]. **Cùng độ dài với** `validators[]`. Với partial withdrawal, phải có phần dư vượt quá `MIN_ACTIVATION_BALANCE` (32 ETH). | Kiểm tra balance khả dụng |
| `state.validators` | `List[Validator, VALIDATOR_REGISTRY_LIMIT]` | Độ dài trong [0, 2^40]. **Cùng độ dài với** `balances[]`. Mọi chỉ số tham chiếu phải < len. | Dữ liệu validator |
| (in `validators`) `[*].effective_balance` | `Gwei` | `Uint64` trong [0, 2048 ETH]. **Ràng buộc**: partial withdrawal yêu cầu `>= MIN_ACTIVATION_BALANCE` (32 ETH). | Kiểm tra balance đủ hay không |
| (in `validators`) `[*].exit_epoch` | `Epoch` | `Uint64`. **Ràng buộc**: partial withdrawal yêu cầu `== FAR_FUTURE_EPOCH`. Nếu đã được đặt, validator đang exit và không đủ điều kiện. | Kiểm tra validator có đang exit không |
| (in `validators`) `[*].withdrawable_epoch` | `Epoch` | `Uint64`. **Ràng buộc với** `state.slot` để xét điều kiện full withdrawal. Thường là `FAR_FUTURE_EPOCH` nếu validator không exit. | Dùng cho kiểm tra full withdrawal |
| (in `validators`) `[*].withdrawal_credentials` | `Bytes32` | `Bytes32`. **Byte tiền tố**: `0x01`=ETH1, `0x02`=compounding. **Bytes [12:32]** = execution address. Validator cần tiền tố `0x01`/`0x02` mới đủ điều kiện withdrawal. | Trích xuất địa chỉ rút tiền |

______________________________________________________________________

## Output Space (State Fields Modified)

*(Các trường của beacon state bị hàm thay đổi)*

| Field | Type | Không gian giá trị (Value Space) | Thay đổi (Modification) |
| ----- | ---- | -------------------------------- | ----------------------- |
| `state.payload_expected_withdrawals` | `List[Withdrawal, MAX_WITHDRAWALS_PER_PAYLOAD]` | Độ dài trong \[0, `MAX_WITHDRAWALS_PER_PAYLOAD`\]. **Suy ra từ** `next_withdrawal_index` đầu vào (tuần tự), các danh sách pending, và các lượt sweep. | **Gán** bằng danh sách withdrawal đã tính |
| `state.balances[*]` | `Gwei` | `Uint64`. **Bị giảm** theo số tiền rút của từng validator withdrawal. | **Giảm** theo số tiền rút của validator |
| `state.builders[*].balance` | `Gwei` | `Uint64`. **Bị giảm** theo số tiền rút của từng builder withdrawal. Giá trị mới = cũ - min(withdrawal.amount, balance). | **Giảm** theo số tiền rút của builder |
| `state.builder_pending_withdrawals` | `List[BuilderPendingWithdrawal, BUILDER_PENDING_WITHDRAWALS_LIMIT]` | Độ dài mới = độ dài cũ - `processed_builder_withdrawals_count`. **Cắt (slice)** để loại bỏ các phần tử đã xử lý. | **Cắt** - loại bỏ N phần tử đầu đã xử lý |
| `state.pending_partial_withdrawals` | `List[PendingPartialWithdrawal, PENDING_PARTIAL_WITHDRAWALS_LIMIT]` | Độ dài mới = độ dài cũ - `processed_partial_withdrawals_count`. | **Cắt** - loại bỏ N phần tử đầu đã xử lý |
| `state.next_withdrawal_index` | `WithdrawalIndex` | Giá trị mới = `payload_expected_withdrawals[-1].index + 1` nếu có withdrawal, ngược lại giữ nguyên. | **Tăng** thêm đúng bằng số withdrawal |
| `state.next_withdrawal_builder_index` | `BuilderIndex` | **Ràng buộc với** `len(builders)` (quay vòng bằng modulo). Cập nhật theo tiến độ builder sweep. | **Cập nhật** theo tiến độ builder sweep |
| `state.next_withdrawal_validator_index` | `ValidatorIndex` | **Ràng buộc với** `len(validators)` (quay vòng bằng modulo). Cập nhật theo tiến độ validator sweep. | **Cập nhật** theo tiến độ validator sweep |

______________________________________________________________________

## Early Exit Condition

Nếu `is_parent_block_full(state)` trả về `False` (tức là
`latest_execution_payload_bid.block_hash != latest_block_hash`), hàm sẽ
return ngay lập tức và **không thay đổi state**.

> 💡 Ghi chú: Nói cách khác, withdrawal chỉ được xử lý khi execution payload
> của block cha thực sự đã được công bố (block cha "full"); nếu block cha
> "empty" thì không có withdrawal nào được tính ở bước này.

______________________________________________________________________

## Key Constants

| Constant | Value | Mô tả (Description) |
| -------------------------------------------- | --------------------- | ------------------------------------- |
| `MAX_WITHDRAWALS_PER_PAYLOAD`                | 16                    | Số withdrawal tối đa mỗi execution payload |
| `MAX_VALIDATORS_PER_WITHDRAWALS_SWEEP`       | 16,384                | Số validator tối đa được kiểm tra mỗi lượt sweep |
| `MAX_BUILDERS_PER_WITHDRAWALS_SWEEP`         | 16,384                | Số builder tối đa được kiểm tra mỗi lượt sweep |
| `MAX_PENDING_PARTIALS_PER_WITHDRAWALS_SWEEP` | 8                     | Số partial withdrawal tối đa được xử lý |
| `VALIDATOR_REGISTRY_LIMIT`                   | 2^40                  | Số validator tối đa trong registry |
| `BUILDER_REGISTRY_LIMIT`                     | 2^40                  | Số builder tối đa trong registry |
| `BUILDER_PENDING_WITHDRAWALS_LIMIT`          | 2^20 (1,048,576)      | Số builder pending withdrawal tối đa |
| `PENDING_PARTIAL_WITHDRAWALS_LIMIT`          | 2^27 (134,217,728)    | Số pending partial withdrawal tối đa |
| `MIN_ACTIVATION_BALANCE`                     | 32 ETH (32x10^9 Gwei) | Balance tối thiểu của một validator active |
| `FAR_FUTURE_EPOCH`                           | 2^64-1                | Giá trị đánh dấu (sentinel) cho epoch "chưa được đặt" |

______________________________________________________________________

## Key Cross-Field Constraints

*(Các ràng buộc quan trọng giữa nhiều trường)*

1. **Căn chỉnh chỉ số (Index Alignment)**:

   - `len(validators) == len(balances)` luôn đúng
   - Mọi validator index phải `< len(validators)`
   - Mọi builder index phải `< len(builders)`

2. **Kiểm soát theo epoch (Epoch Gating)**: Mọi trường `withdrawable_epoch` đều
   được so sánh với `current_epoch = compute_epoch_at_slot(state.slot)`.

3. **Ngưỡng balance theo loại withdrawal**:

   - **Builder pending**:
     `actual_amount = min(requested_amount, builder.balance)` (balance của
     builder có thể giảm về 0)
   - **Builder sweep**: yêu cầu `builder.withdrawable_epoch <= epoch` VÀ
     `builder.balance > 0`; rút toàn bộ `builder.balance`
   - **Partial**: yêu cầu `effective_balance >= MIN_ACTIVATION_BALANCE` VÀ
     `balance > MIN_ACTIVATION_BALANCE` VÀ `exit_epoch == FAR_FUTURE_EPOCH`
   - **Full**: yêu cầu `has_execution_withdrawal_credential` VÀ
     `withdrawable_epoch <= epoch` VÀ `balance > 0`

4. **Thứ tự xử lý và giới hạn (Processing Order & Caps)** (ràng buộc kết hợp
   lên output):

   Tất cả các loại withdrawal, trừ validator sweep, bị giới hạn tổng cộng ở
   `MAX_WITHDRAWALS_PER_PAYLOAD - 1`, để dành 1 chỗ cho validator sweep. Mỗi
   hàm nhận vào `prior_withdrawals` (các withdrawal đã được tạo ở bước trước)
   và chỉ có thể lấp đầy tới giới hạn này.

   - **Builder pending** (`get_builder_withdrawals`): xử lý đầu tiên, giới hạn
     ở `MAX_WITHDRAWALS_PER_PAYLOAD - 1`
   - **Pending partial** (`get_pending_partial_withdrawals`): xử lý thứ hai,
     giới hạn ở
     `min(prior + MAX_PENDING_PARTIALS_PER_WITHDRAWALS_SWEEP, MAX - 1)`. Điều
     này có nghĩa là nếu builder đã chiếm N chỗ, partial withdrawal được tối đa
     `MAX - 1 - N` chỗ.
   - **Builder sweep** (`get_builders_sweep_withdrawals`): xử lý thứ ba, giới
     hạn tổng cộng ở `MAX_WITHDRAWALS_PER_PAYLOAD - 1` (tính cả các withdrawal
     trước đó)
   - **Validator sweep** (`get_validators_sweep_withdrawals`): xử lý cuối cùng,
     nhận các chỗ còn lại, bị giới hạn bởi `MAX_VALIDATORS_PER_WITHDRAWALS_SWEEP`
   - **Tổng output**: tối đa `MAX_WITHDRAWALS_PER_PAYLOAD`

5. **Ràng buộc thoát sớm (Early Exit Binding)**: Hàm chỉ thực thi khi
   `latest_execution_payload_bid.block_hash == latest_block_hash`.

______________________________________________________________________

## Builder Model (PR #4788)

Builder là **các tác nhân có stake riêng biệt, không làm nhiệm vụ validator**,
được lưu trong `state.builders[]`. Họ KHÔNG phải là validator có credential
đặc biệt.

**Các khác biệt chính so với validator**:

- Builder có registry riêng (`state.builders`), tách biệt với
  `state.validators`
- Balance của builder nằm trong `Builder.balance`, không nằm trong
  `state.balances[]`
- Builder không thể bị slashing
- Builder dùng kiểu `BuilderIndex`, được chuyển đổi qua lại với
  `ValidatorIndex` bằng `convert_builder_index_to_validator_index()` và
  `convert_validator_index_to_builder_index()`
- Trong output `Withdrawal`, builder withdrawal dùng validator index đã được
  chuyển đổi (có bật bit `BUILDER_INDEX_FLAG`)

**Các loại builder withdrawal**:

1. **Builder Pending Withdrawals**: Các builder withdrawal đang chờ, lưu trong
   `state.builder_pending_withdrawals`. Dùng `fee_recipient` làm địa chỉ nhận.
2. **Builder Sweep Withdrawals**: Withdrawal tự động khi
   `builder.withdrawable_epoch <= current_epoch`. Dùng
   `builder.execution_address` làm địa chỉ nhận và rút toàn bộ balance.

______________________________________________________________________

## Functions Called

Call stack của `process_withdrawals`. Nguồn: các hàm gloas được định nghĩa
trong [gloas/beacon-chain.md](../../../../../../../specs/gloas/beacon-chain.md);
các hàm kế thừa đến từ các fork trước (capella, electra, phase0).

- `process_withdrawals(state)` — gloas
  - `is_parent_block_full(state)` — gloas
  - `get_expected_withdrawals(state)` — gloas
    - `get_builder_withdrawals(state, ...)` — gloas
      - `convert_builder_index_to_validator_index(index)` — gloas
    - `get_pending_partial_withdrawals(state, ...)` — electra
    - `get_builders_sweep_withdrawals(state, ...)` — gloas
      - `get_current_epoch(state)` — phase0
      - `convert_builder_index_to_validator_index(index)` — gloas
    - `get_validators_sweep_withdrawals(state, ...)` — electra
  - `apply_withdrawals(state, withdrawals)` — gloas
    - `is_builder_index(validator_index)` — gloas
    - `convert_validator_index_to_builder_index(index)` — gloas
    - `decrease_balance(state, index, amount)` — phase0
  - `update_next_withdrawal_index(state, withdrawals)` — capella
  - `update_payload_expected_withdrawals(state, withdrawals)` — gloas
  - `update_builder_pending_withdrawals(state, count)` — gloas
  - `update_pending_partial_withdrawals(state, count)` — electra
  - `update_next_withdrawal_builder_index(state, count)` — gloas
  - `update_next_withdrawal_validator_index(state, withdrawals)` — capella

______________________________________________________________________

## Summary Diagram

```text
                    +-----------------------------------------------------------+
                    |                    INPUT (Read)                           |
                    +-----------------------------------------------------------+
                    | latest_execution_payload_bid.block_hash : Bytes32         |
                    | latest_block_hash                       : Bytes32         |
                    | slot                                    : Uint64          |
                    | next_withdrawal_index                   : Uint64          |
                    | next_withdrawal_validator_index         : Uint64          |
                    | next_withdrawal_builder_index           : Uint64          |
                    | builders[0..2^40]                       : Container[]     |
                    |   .balance, .execution_address, .withdrawable_epoch       |
                    | builder_pending_withdrawals[0..2^20]    : Container[]     |
                    |   .builder_index, .fee_recipient, .amount                 |
                    | pending_partial_withdrawals[0..2^27]    : Container[]     |
                    |   .withdrawable_epoch, .validator_index, .amount          |
                    | balances[0..2^40]                       : Uint64[]        |
                    | validators[0..2^40]                     : Container[]     |
                    |   .effective_balance, .exit_epoch, .withdrawable_epoch,   |
                    |   .withdrawal_credentials                                 |
                    +---------------------------+-------------------------------+
                                                |
                                                v
                    +-----------------------------------------------------------+
                    |                process_withdrawals()                      |
                    |                                                           |
                    | 1. Builder pending withdrawals (from fee_recipient)       |
                    | 2. Partial validator withdrawals                          |
                    | 3. Builder sweep withdrawals (from execution_address)     |
                    | 4. Validator sweep withdrawals                            |
                    +---------------------------+-------------------------------+
                                                |
                                                v
                    +-----------------------------------------------------------+
                    |                   OUTPUT (Modified)                       |
                    +-----------------------------------------------------------+
                    | payload_expected_withdrawals[0..16]     : Container[]     |
                    |   .index, .validator_index, .address, .amount             |
                    | builders[*].balance                     : Uint64          |
                    | balances[*]                             : Uint64          |
                    | builder_pending_withdrawals             : Container[]     |
                    | pending_partial_withdrawals             : Container[]     |
                    | next_withdrawal_index                   : Uint64          |
                    | next_withdrawal_builder_index           : Uint64          |
                    | next_withdrawal_validator_index         : Uint64          |
                    +-----------------------------------------------------------+
```
