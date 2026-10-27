# Capella -- Honest Validator

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Helpers](#helpers)
  - [Modified `GetPayloadResponse`](#modified-getpayloadresponse)
- [Protocols](#protocols)
  - [`ExecutionEngine`](#executionengine)
    - [Modified `get_payload`](#modified-get_payload)
- [Beacon chain responsibilities](#beacon-chain-responsibilities)
  - [Block proposal](#block-proposal)
    - [Constructing the `BeaconBlockBody`](#constructing-the-beaconblockbody)
      - [ExecutionPayload](#executionpayload)
      - [BLS to execution changes](#bls-to-execution-changes)
- [Enabling validator withdrawals](#enabling-validator-withdrawals)
  - [Changing from BLS to execution withdrawal credentials](#changing-from-bls-to-execution-withdrawal-credentials)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả những thay đổi cần thực hiện trong code của một "honest
validator" (validator trung thực) để triển khai bản nâng cấp Capella.

## Prerequisites

Tài liệu này là phần mở rộng của hướng dẫn
[Bellatrix -- Honest Validator](../bellatrix/validator.md). Mọi hành vi và định
nghĩa trong tài liệu này, cũng như trong các tài liệu mà nó mở rộng, đều được
giữ nguyên trừ khi được ghi chú hoặc ghi đè một cách rõ ràng.

Toàn bộ thuật ngữ, hằng số, hàm và cơ chế giao thức được định nghĩa trong đặc tả
beacon-chain đã cập nhật của [Capella](./beacon-chain.md) là kiến thức bắt buộc
cho tài liệu này và được sử dụng xuyên suốt. Hãy đọc các đặc tả beacon-chain liên
quan trước khi tiếp tục và dùng chúng làm tài liệu tham chiếu trong suốt quá
trình đọc.

## Helpers

### Modified `GetPayloadResponse`

```python
@dataclass
class GetPayloadResponse:
    execution_payload: ExecutionPayload
    block_value: Uint256
```

> 💡 Ghi chú: Ngoài `execution_payload`, response giờ có thêm `block_value` —
> giá trị (tính bằng Wei) mà payload mang lại cho fee recipient. Giá trị này có
> thể được dùng để so sánh payload do execution engine cục bộ dựng với payload từ
> nguồn bên ngoài (ví dụ builder).

## Protocols

### `ExecutionEngine`

#### Modified `get_payload`

*Lưu ý*: Hàm `get_payload` trả về object `GetPayloadResponse` đã được cập nhật.

```python
def get_payload(self: ExecutionEngine, payload_id: PayloadId) -> GetPayloadResponse:
    """
    Return ExecutionPayload and Uint256 objects.
    """
```

## Beacon chain responsibilities

Mọi trách nhiệm của validator giữ nguyên, ngoại trừ những điểm được nêu dưới
đây.

### Block proposal

#### Constructing the `BeaconBlockBody`

##### ExecutionPayload

Các `ExecutionPayload` được dựng giống như ở Bellatrix, chỉ khác ở chỗ danh sách
withdrawal dự kiến cho slot phải được thu thập từ `state` (sử dụng hàm helper
`get_expected_withdrawals`) và được truyền vào `ExecutionEngine` bên trong
`prepare_execution_payload`.

*Lưu ý*: Trong phần này, `state` là state của slot dùng để đề xuất block, _chưa_
áp dụng block đó. Tức là, `state` chính là `previous_state` đã được xử lý qua mọi
slot trống cho đến slot được phân công, bằng cách gọi
`process_slots(previous_state, slot)`.

*Lưu ý*: Thay đổi duy nhất đối với `prepare_execution_payload` là gọi
`get_expected_withdrawals()` để gán giá trị cho trường mới `withdrawals` của
`PayloadAttributes`.

```python
def prepare_execution_payload(
    state: BeaconState,
    safe_block_hash: Hash32,
    finalized_block_hash: Hash32,
    suggested_fee_recipient: ExecutionAddress,
    execution_engine: ExecutionEngine,
    # [Modified in Capella]
    # Removed `pow_chain`
) -> PayloadId | None:
    # [Modified in Capella]
    # Removed `is_merge_transition_complete` check
    parent_hash = state.latest_execution_payload_header.block_hash

    # Thiết lập forkchoice head và khởi động quá trình build payload
    payload_attributes = PayloadAttributes(
        timestamp=compute_time_at_slot(state.genesis_time, state.slot),
        prev_randao=get_randao_mix(state, get_current_epoch(state)),
        suggested_fee_recipient=suggested_fee_recipient,
        # [New in Capella]
        withdrawals=get_expected_withdrawals(state).withdrawals,
    )
    return execution_engine.notify_forkchoice_updated(
        head_block_hash=parent_hash,
        safe_block_hash=safe_block_hash,
        finalized_block_hash=finalized_block_hash,
        payload_attributes=payload_attributes,
    )
```

> 💡 Ghi chú: Vì The Merge đã hoàn tất trước Capella, hàm không còn cần tham số
> `pow_chain` và không cần kiểm tra `is_merge_transition_complete`: block cha
> luôn có execution payload, nên `parent_hash` được lấy trực tiếp từ
> `state.latest_execution_payload_header.block_hash`. Danh sách `withdrawals`
> truyền cho execution engine phải khớp chính xác với những gì
> `process_withdrawals` sẽ kiểm tra khi xử lý block, nếu không block sẽ không hợp
> lệ.

##### BLS to execution changes

Tối đa `MAX_BLS_TO_EXECUTION_CHANGES` object
[`BLSToExecutionChange`](./beacon-chain.md#blstoexecutionchange) có thể được đưa
vào `block`. Các BLS to execution change này phải thỏa mãn các điều kiện kiểm
tra trong
[BLS to execution change processing](./beacon-chain.md#new-process_bls_to_execution_change).

## Enabling validator withdrawals

Balance của validator được rút định kỳ thông qua một quy trình tự động. Với các
validator đã exit, toàn bộ balance được rút. Với các validator đang active, phần
balance vượt quá `MAX_EFFECTIVE_BALANCE` được rút.

Quy trình tự động này có một điều kiện tiên quyết: withdrawal credentials của
validator phải trỏ đến một địa chỉ trên execution layer, tức là có tiền tố
`ETH1_ADDRESS_WITHDRAWAL_PREFIX`.

Nếu validator có withdrawal credential với tiền tố `BLS_WITHDRAWAL_PREFIX`, thì
để tham gia withdrawal, validator phải tạo một message dùng một lần để đổi
withdrawal credential từ phiên bản được xác thực bằng BLS key sang phiên bản
tương thích với execution layer. Message này -- một `BLSToExecutionChange` -- khả
dụng kể từ Capella.

Validator muốn bật withdrawal **MUST** tạo, ký và broadcast message này để nó
được chấp nhận trên beacon chain. Validator không muốn bật withdrawal và đang có
withdrawal credentials dạng `BLS_WITHDRAWAL_PREFIX` có thể trì hoãn việc tạo
message này cho đến khi sẵn sàng bật withdrawal.

### Changing from BLS to execution withdrawal credentials

Đầu tiên, validator phải dựng một `message`
[`BLSToExecutionChange`](./beacon-chain.md#blstoexecutionchange) hợp lệ.
`message` này chứa `validator_index` của validator muốn đổi credentials,
`from_bls_pubkey` -- BLS public key tương ứng với **withdrawal BLS secret key**
đã được dùng để tạo withdrawal credential dạng `BLS_WITHDRAWAL_PREFIX`, và
`to_execution_address` -- địa chỉ trên execution layer mà balance của validator
sẽ được rút về.

*Lưu ý*: Cặp khóa withdrawal dùng để tạo withdrawal credential dạng
`BLS_WITHDRAWAL_PREFIX` nên khác với cặp khóa ký (signing key) dùng để vận hành
validator trong các tình huống thông thường. Hãy tham khảo tài liệu của công cụ
deposit validator mà bạn dùng để biết thêm chi tiết nếu chưa rõ sự khác biệt này.

*Cảnh báo*: Message này chỉ có thể được đưa lên chain một lần duy nhất và không
thể đảo ngược, vì vậy hãy đảm bảo `to_execution_address` là chính xác và bạn có
quyền truy cập vào địa chỉ đó.

Tiếp theo, validator ký `message: BLSToExecutionChange` đã dựng bằng
**withdrawal BLS secret key**, và `signature` này được đặt vào một message
`SignedBLSToExecutionChange` cùng với `message` `BLSToExecutionChange` bên
trong. Lưu ý rằng message `SignedBLSToExecutionChange` phải vượt qua tất cả các
bước kiểm tra trong
[`process_bls_to_execution_change`](./beacon-chain.md#new-process_bls_to_execution_change).

Sau đó, message `SignedBLSToExecutionChange` cần được gửi lên mạng của consensus
layer. Khi đã được đưa lên chain, thay đổi withdrawal credential có hiệu lực.
Validator không cần làm thêm gì nữa để tham gia vào quy trình withdrawal tự động.

*Lưu ý*: Node *should* ưu tiên các operation `BLSToExecutionChange` nhận được
cục bộ, để đảm bảo các thay đổi này được đưa lên chain thông qua các block do
chính node đó đề xuất, kể cả khi phần còn lại của mạng kiểm duyệt (censor) chúng.
