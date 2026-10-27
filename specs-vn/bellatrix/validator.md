# Bellatrix -- Honest Validator

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Helpers](#helpers)
  - [`GetPayloadResponse`](#getpayloadresponse)
  - [`get_pow_block_at_terminal_total_difficulty`](#get_pow_block_at_terminal_total_difficulty)
  - [`get_terminal_pow_block`](#get_terminal_pow_block)
- [Protocols](#protocols)
  - [`ExecutionEngine`](#executionengine)
    - [`get_payload`](#get_payload)
- [Beacon chain responsibilities](#beacon-chain-responsibilities)
  - [Block proposal](#block-proposal)
    - [Constructing the `BeaconBlockBody`](#constructing-the-beaconblockbody)
      - [ExecutionPayload](#executionpayload)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả những thay đổi cần thực hiện trong code của một "honest
validator" (validator trung thực) để hỗ trợ việc đề xuất (propose) beacon chain
block có khả năng thực thi (executable), tức là block có chứa execution payload.

## Prerequisites

Tài liệu này là phần mở rộng của hướng dẫn
[Altair -- Honest Validator](../altair/validator.md). Mọi hành vi và định nghĩa
trong tài liệu này, cũng như trong các tài liệu mà nó mở rộng, đều được kế thừa
trừ khi được ghi chú rõ ràng hoặc bị ghi đè.

Toàn bộ thuật ngữ, hằng số, hàm và cơ chế giao thức được định nghĩa trong đặc tả
beacon-chain đã cập nhật của [Bellatrix](./beacon-chain.md) là kiến thức bắt buộc
cho tài liệu này và được sử dụng xuyên suốt. Vui lòng đọc các đặc tả beacon-chain
liên quan trước khi tiếp tục và dùng chúng làm tài liệu tham chiếu trong suốt quá
trình đọc.

## Helpers

### `GetPayloadResponse`

```python
@dataclass
class GetPayloadResponse:
    execution_payload: ExecutionPayload
```

### `get_pow_block_at_terminal_total_difficulty`

*(Tìm terminal PoW block dựa trên `TERMINAL_TOTAL_DIFFICULTY` (TTD): block đầu
tiên đạt TTD trong khi block cha của nó chưa đạt.)*

```python
def get_pow_block_at_terminal_total_difficulty(
    pow_chain: dict[Hash32, PowBlock],
) -> PowBlock | None:
    # `pow_chain` biểu diễn một cách trừu tượng tất cả các block trong PoW chain
    for block in pow_chain.values():
        block_reached_ttd = block.total_difficulty >= TERMINAL_TOTAL_DIFFICULTY
        if block_reached_ttd:
            # Nếu là genesis block thì không có block cha, nên chỉ cần đạt TTD là đủ để trở thành terminal block hợp lệ
            if block.parent_hash == Hash32():
                return block
            parent = pow_chain[block.parent_hash]
            parent_reached_ttd = parent.total_difficulty >= TERMINAL_TOTAL_DIFFICULTY
            if not parent_reached_ttd:
                return block

    return None
```

### `get_terminal_pow_block`

```python
def get_terminal_pow_block(pow_chain: dict[Hash32, PowBlock]) -> PowBlock | None:
    if TERMINAL_BLOCK_HASH != EMPTY_BLOCK_HASH:
        # Giá trị ghi đè terminal block hash được ưu tiên hơn terminal total difficulty
        if TERMINAL_BLOCK_HASH in pow_chain:
            return pow_chain[TERMINAL_BLOCK_HASH]
        else:
            return None

    return get_pow_block_at_terminal_total_difficulty(pow_chain)
```

*Lưu ý*: Hàm này *không* dùng `hash_tree_root` của simple serialize (SSZ), nhằm
tránh việc buộc execution layer phải hỗ trợ khả năng hashing theo SSZ.

> 💡 Ghi chú: `TERMINAL_BLOCK_HASH` là cơ chế ghi đè khẩn cấp: nếu được cấu hình
> (khác `EMPTY_BLOCK_HASH`), terminal block được xác định trực tiếp theo hash này
> thay vì theo TTD.

## Protocols

### `ExecutionEngine`

*Lưu ý*: Hàm `get_payload` được bổ sung vào protocol `ExecutionEngine` để
validator sử dụng.

Phần thân của hàm này phụ thuộc vào cách cài đặt (implementation dependent).
Engine API có thể được dùng để cài đặt hàm này với một execution engine bên
ngoài.

#### `get_payload`

*Lưu ý*: Với `payload_id` cho trước, hàm `get_payload` trả về
`GetPayloadResponse` chứa phiên bản mới nhất của execution payload đã được xây
dựng kể từ lời gọi tương ứng tới method `notify_forkchoice_updated`.

```python
def get_payload(self: ExecutionEngine, payload_id: PayloadId) -> GetPayloadResponse:
    """
    Return ExecutionPayload object.
    """
```

## Beacon chain responsibilities

Mọi trách nhiệm của validator đều giữ nguyên, ngoại trừ những điểm được nêu dưới
đây — cụ thể là việc xử lý transition block (block chuyển tiếp sang PoS/merge) và
việc bổ sung `ExecutionPayload`.

*Lưu ý*: Validator không được propose trên, hoặc attest cho, một block chưa được
coi là hợp lệ, tức là block chưa vượt qua state transition của beacon chain và
các bước kiểm tra execution. Trong các bản nâng cấp tương lai, một cơ chế
"execution Proof-of-Custody" sẽ được tích hợp để ngăn validator thuê ngoài
(outsource) việc kiểm tra execution payload.

### Block proposal

#### Constructing the `BeaconBlockBody`

##### ExecutionPayload

Để có được một execution payload, block proposer khi xây dựng block trên một
`state` phải thực hiện các bước sau:

1. Đặt
   `payload_id = prepare_execution_payload(state, safe_block_hash, finalized_block_hash, suggested_fee_recipient, execution_engine, pow_chain)`,
   trong đó:
   - `state` là state object có được sau khi áp dụng transition
     `process_slots(state, slot)` lên state thu được từ việc xử lý block cha
   - `safe_block_hash` là giá trị trả về của lời gọi hàm
     `get_safe_execution_block_hash(fcr_store: FastConfirmationStore)`
   - `finalized_block_hash` là block hash của execution payload finalized mới
     nhất (`Hash32()` nếu chưa có payload nào được finalized)
   - `suggested_fee_recipient` là giá trị được đề xuất dùng cho trường
     `fee_recipient` của execution payload (địa chỉ nhận phí giao dịch)
   - `pow_chain` là một dictionary `dict[Hash32, PowBlock]` biểu diễn một cách
     trừu tượng tất cả các block trong PoW chain, với block hash làm key

```python
def prepare_execution_payload(
    state: BeaconState,
    safe_block_hash: Hash32,
    finalized_block_hash: Hash32,
    suggested_fee_recipient: ExecutionAddress,
    execution_engine: ExecutionEngine,
    pow_chain: dict[Hash32, PowBlock] | None = None,
) -> PayloadId | None:
    if not is_merge_transition_complete(state):
        assert pow_chain is not None
        is_terminal_block_hash_set = TERMINAL_BLOCK_HASH != EMPTY_BLOCK_HASH
        is_activation_epoch_reached = (
            get_current_epoch(state) >= TERMINAL_BLOCK_HASH_ACTIVATION_EPOCH
        )
        if is_terminal_block_hash_set and not is_activation_epoch_reached:
            # Terminal block hash đã được đặt nhưng chưa tới activation epoch, không cần gọi prepare payload
            return None

        terminal_pow_block = get_terminal_pow_block(pow_chain)
        if terminal_pow_block is None:
            # Trước merge, không cần gọi prepare payload
            return None
        # Đánh dấu merge bằng cách xây dựng payload ngay trên terminal PoW block
        parent_hash = terminal_pow_block.block_hash
    else:
        # Sau merge, payload bình thường
        parent_hash = state.latest_execution_payload_header.block_hash

    # Đặt head cho fork choice và khởi động quá trình xây dựng payload
    payload_attributes = PayloadAttributes(
        timestamp=compute_time_at_slot(state.genesis_time, state.slot),
        prev_randao=get_randao_mix(state, get_current_epoch(state)),
        suggested_fee_recipient=suggested_fee_recipient,
    )
    return execution_engine.notify_forkchoice_updated(
        head_block_hash=parent_hash,
        safe_block_hash=safe_block_hash,
        finalized_block_hash=finalized_block_hash,
        payload_attributes=payload_attributes,
    )
```

2. Đặt
   `block.body.execution_payload = get_execution_payload(payload_id, execution_engine)`,
   trong đó:

```python
def get_execution_payload(
    payload_id: PayloadId | None, execution_engine: ExecutionEngine
) -> ExecutionPayload:
    if payload_id is None:
        # Trước merge, payload rỗng
        return ExecutionPayload.empty()
    else:
        return execution_engine.get_payload(payload_id).execution_payload
```

*Lưu ý*: Validator được khuyến nghị gọi `prepare_execution_payload` ngay khi các
tham số đầu vào được biết, và gọi lại hàm này mỗi khi bất kỳ tham số nào được cập
nhật (để execution engine kịp xây dựng payload tốt nhất trước khi tới lượt
propose).
