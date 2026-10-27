# Bellatrix -- Fork Choice

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Types](#types)
  - [New `PayloadId`](#new-payloadid)
- [Protocols](#protocols)
  - [`ExecutionEngine`](#executionengine)
    - [`notify_forkchoice_updated`](#notify_forkchoice_updated)
      - [`safe_block_hash`](#safe_block_hash)
- [Helpers](#helpers)
  - [`PayloadAttributes`](#payloadattributes)
  - [`PowBlock`](#powblock)
  - [`get_pow_block`](#get_pow_block)
  - [`is_valid_terminal_pow_block`](#is_valid_terminal_pow_block)
  - [`validate_merge_block`](#validate_merge_block)
- [Handlers](#handlers)
  - [`on_block`](#on_block)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả các sửa đổi đối với fork choice theo đề xuất executable beacon
chain (beacon chain có khả năng thực thi giao dịch, tức là tích hợp execution
payload).

Trừ khi được nêu rõ, toàn bộ chức năng trước đó từ
[Altair](../altair/fork-choice.md) đều được kế thừa.

*Lưu ý*: Tài liệu này đưa vào quy trình chuyển đổi từ block PoW cuối cùng sang
block PoS đầu tiên (sự kiện merge).

## Types

### New `PayloadId`

```python
class PayloadId(Bytes8):
    """
    An identifier of a payload build process on the execution engine.
    """
```

## Protocols

### `ExecutionEngine`

*Lưu ý*: Hàm `notify_forkchoice_updated` được bổ sung vào protocol
`ExecutionEngine` để thông báo các cập nhật của fork choice.

Phần thân của hàm này phụ thuộc vào cách hiện thực (implementation dependent).
Có thể dùng Engine API để hiện thực nó với một execution engine bên ngoài.

#### `notify_forkchoice_updated`

Hàm này thực hiện ba hành động một cách *nguyên tử (atomically)*:

- Tổ chức lại (re-org) chuỗi execution payload và state tương ứng để
  `head_block_hash` trở thành head.
- Cập nhật safe block hash bằng giá trị được truyền qua tham số
  `safe_block_hash`.
- Áp dụng finality cho execution state: lưu trữ vĩnh viễn, không thể đảo ngược,
  chuỗi gồm tất cả execution payload và state tương ứng, tính đến và bao gồm cả
  `finalized_block_hash`.

Ngoài ra, nếu `payload_attributes` được cung cấp, hàm này sẽ khởi động một tiến
trình xây dựng payload (payload build process) trên nền `head_block_hash` và trả
về một định danh (identifier) của tiến trình vừa khởi tạo.

> 💡 Ghi chú: Định danh `PayloadId` trả về được proposer dùng sau đó để lấy
> payload đã được execution engine xây dựng (ví dụ qua `engine_getPayload` trong
> Engine API) khi đến lượt đề xuất block.

```python
def notify_forkchoice_updated(
    self: ExecutionEngine,
    head_block_hash: Hash32,
    safe_block_hash: Hash32,
    finalized_block_hash: Hash32,
    payload_attributes: PayloadAttributes | None,
) -> PayloadId | None: ...
```

*Lưu ý*: Các giá trị `(head_block_hash, finalized_block_hash)` trong lời gọi hàm
`notify_forkchoice_updated` tương ứng với sự kiện `POS_FORKCHOICE_UPDATED` được
định nghĩa trong [EIP-3675](https://eips.ethereum.org/EIPS/eip-3675#definitions).
Theo EIP-3675, trước khi một block sau chuyển đổi (post-transition block) được
finalized, `notify_forkchoice_updated` MUST được gọi với
`finalized_block_hash = Hash32()`.

*Lưu ý*: Phần mềm client MUST NOT gọi hàm này cho tới khi các điều kiện chuyển
đổi được thỏa mãn trên mạng PoW, tức là đã tồn tại một block mà hàm
`is_valid_terminal_pow_block` trả về `True` cho nó.

*Lưu ý*: Phần mềm client MUST gọi hàm này để khởi động tiến trình xây dựng
payload nhằm tạo ra merge transition block (block chuyển đổi merge); trong trường
hợp này, tham số `head_block_hash` MUST được đặt bằng hash của một terminal PoW
block.

##### `safe_block_hash`

Tham số `safe_block_hash` MUST được đặt bằng giá trị trả về của hàm
[`get_safe_execution_block_hash(fcr_store)`](./fast-confirmation.md#new-get_safe_execution_block_hash).

## Helpers

### `PayloadAttributes`

Được dùng để báo hiệu khởi động tiến trình xây dựng payload thông qua
`notify_forkchoice_updated`.

```python
@dataclass
class PayloadAttributes:
    timestamp: Uint64
    prev_randao: Bytes32
    suggested_fee_recipient: ExecutionAddress
```

### `PowBlock`

```python
class PowBlock(Container):
    block_hash: Hash32
    parent_hash: Hash32
    total_difficulty: Uint256
```

### `get_pow_block`

Gọi `get_pow_block(block_hash: Hash32) -> PowBlock | None` là hàm nhận vào hash
của một block PoW và trả về dữ liệu của block đó. Hàm có thể trả về `None` nếu
block được yêu cầu chưa sẵn có.

*Lưu ý*: Có thể dùng phương thức JSON-RPC `eth_getBlockByHash` để lấy thông tin
này từ execution client.

### `is_valid_terminal_pow_block`

Được dùng bởi fork-choice handler `on_block`.

> 💡 Ghi chú: Một block PoW là terminal PoW block hợp lệ khi total difficulty của
> nó đã đạt `TERMINAL_TOTAL_DIFFICULTY`, còn total difficulty của block cha thì
> chưa đạt — tức là đây là block PoW đầu tiên vượt ngưỡng TTD.

```python
def is_valid_terminal_pow_block(block: PowBlock, parent: PowBlock) -> bool:
    is_total_difficulty_reached = block.total_difficulty >= TERMINAL_TOTAL_DIFFICULTY
    is_parent_total_difficulty_valid = parent.total_difficulty < TERMINAL_TOTAL_DIFFICULTY
    return is_total_difficulty_reached and is_parent_total_difficulty_valid
```

### `validate_merge_block`

```python
def validate_merge_block(block: BeaconBlock) -> None:
    """
    Check the parent PoW block of execution payload is a valid terminal PoW block.

    Note: Unavailable PoW block(s) may later become available,
    and a client software MAY delay a call to ``validate_merge_block``
    until the PoW block(s) become available.
    """
    if TERMINAL_BLOCK_HASH != EMPTY_BLOCK_HASH:
        # Nếu `TERMINAL_BLOCK_HASH` được dùng để ghi đè, phải đạt tới activation epoch.
        assert compute_epoch_at_slot(block.slot) >= TERMINAL_BLOCK_HASH_ACTIVATION_EPOCH
        assert block.body.execution_payload.parent_hash == TERMINAL_BLOCK_HASH
        return

    pow_block = get_pow_block(block.body.execution_payload.parent_hash)
    # Kiểm tra `pow_block` có sẵn hay không
    assert pow_block is not None
    pow_parent = get_pow_block(pow_block.parent_hash)
    # Kiểm tra `pow_parent` có sẵn hay không
    assert pow_parent is not None
    # Kiểm tra `pow_block` có phải là terminal PoW block hợp lệ hay không
    assert is_valid_terminal_pow_block(pow_block, pow_parent)
```

## Handlers

### `on_block`

*Lưu ý*: Thay đổi duy nhất là bổ sung bước kiểm tra các điều kiện của transition
block (block chuyển đổi merge).

```python
def on_block(store: Store, signed_block: SignedBeaconBlock) -> None:
    """
    Run ``on_block`` upon receiving a new block.

    A block that is asserted as invalid due to unavailable PoW block may be valid at a later time,
    consider scheduling it for later processing in such case.
    """
    block = signed_block.message
    block_root = hash_tree_root(block)

    # Trả về sớm nếu block đã được biết
    if block_root in store.blocks:
        return

    # Block cha phải đã được biết
    assert block.parent_root in store.block_states
    # Tạo bản sao của state để tránh vấn đề về tính khả biến (mutability)
    pre_state = store.block_states[block.parent_root].copy()
    # Block không được ở tương lai. Nếu có, phải hoãn xem xét cho tới khi chúng thuộc về quá khứ.
    assert get_current_slot(store) >= block.slot

    # Kiểm tra block nằm sau slot của finalized epoch (tối ưu để giảm số lần gọi get_ancestor)
    finalized_slot = compute_start_slot_at_epoch(store.finalized_checkpoint.epoch)
    assert block.slot > finalized_slot
    # Kiểm tra block là hậu duệ của finalized block tại slot của finalized checkpoint
    finalized_checkpoint_block = get_checkpoint_block(
        store,
        block.parent_root,
        store.finalized_checkpoint.epoch,
    )
    assert store.finalized_checkpoint.root == finalized_checkpoint_block

    # Kiểm tra block hợp lệ và tính post-state
    state = pre_state.copy()
    state_transition(state, signed_block, validate_result=True)

    # [New in Bellatrix]
    if is_merge_transition_block(pre_state, block.body):
        validate_merge_block(block)

    # Tính head trước khi áp dụng block
    head = get_head(store)
    # Thêm block mới vào store
    store.blocks[block_root] = block
    # Thêm state mới của block này vào store
    store.block_states[block_root] = state

    record_block_timeliness(store, block_root)
    update_proposer_boost_root(store, head.root, block_root)

    # Cập nhật các checkpoint trong store nếu cần
    update_checkpoints(store, state.current_justified_checkpoint, state.finalized_checkpoint)

    # Tính sớm (eagerly) unrealized justification và finality.
    compute_pulled_up_tip(store, block_root)
```
