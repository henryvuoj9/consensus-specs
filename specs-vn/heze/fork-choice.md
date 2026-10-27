# Heze -- Fork Choice

*Lưu ý*: Tài liệu này vẫn đang trong quá trình hoàn thiện, dành cho các nhà nghiên cứu và người triển khai client.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Configs](#configs)
  - [Time parameters](#time-parameters)
- [Protocols](#protocols)
  - [`ExecutionEngine`](#executionengine)
    - [New `is_inclusion_list_satisfied`](#new-is_inclusion_list_satisfied)
    - [Modified `notify_forkchoice_updated`](#modified-notify_forkchoice_updated)
- [Helpers](#helpers)
  - [Modified `PayloadAttributes`](#modified-payloadattributes)
  - [Modified `Store`](#modified-store)
  - [Modified `get_forkchoice_store`](#modified-get_forkchoice_store)
  - [New `record_payload_inclusion_list_satisfaction`](#new-record_payload_inclusion_list_satisfaction)
  - [New `is_payload_inclusion_list_satisfied`](#new-is_payload_inclusion_list_satisfied)
  - [Modified `should_extend_payload`](#modified-should_extend_payload)
  - [New `get_inclusion_list_due_ms`](#new-get_inclusion_list_due_ms)
- [Handlers](#handlers)
  - [New `on_inclusion_list`](#new-on_inclusion_list)
  - [Modified `on_execution_payload_envelope`](#modified-on_execution_payload_envelope)

<!-- mdformat-toc end -->

## Introduction

Đây là phần sửa đổi fork choice đi kèm với bản nâng cấp Heze.

> 💡 Ghi chú: Điểm chính của Heze ở tầng fork choice là: một execution payload
> không thỏa mãn inclusion list (không chứa các giao dịch mà inclusion list
> committee yêu cầu) vẫn hợp lệ, nhưng fork choice sẽ không xây tiếp (extend)
> trên payload đó.

## Configs

### Time parameters

| Name                     | Value          | Duration                         |
| ------------------------ | -------------- | -------------------------------- |
| `INCLUSION_LIST_DUE_BPS` | `Uint64(6667)` | ~67% của `SLOT_DURATION_MS`      |

## Protocols

### `ExecutionEngine`

*Lưu ý*: Hàm `is_inclusion_list_satisfied` được thêm vào protocol
`ExecutionEngine` để thực hiện việc kiểm tra các ràng buộc của inclusion list.

Phần thân của hàm này phụ thuộc vào cách triển khai (implementation dependent).
Có thể dùng Engine API để triển khai hàm này với một execution engine bên ngoài.

#### New `is_inclusion_list_satisfied`

```python
def is_inclusion_list_satisfied(
    self: ExecutionEngine,
    execution_payload: ExecutionPayload,
    inclusion_list_transactions: Sequence[Transaction],
) -> bool:
    """
    Return ``True`` if and only if ``execution_payload`` satisfies the inclusion
    list constraints with respect to ``inclusion_list_transactions``.
    """
```

Trả về `True` khi và chỉ khi `execution_payload` thỏa mãn các ràng buộc inclusion
list đối với `inclusion_list_transactions`.

#### Modified `notify_forkchoice_updated`

*Lưu ý*: Thay đổi duy nhất nằm ở container `PayloadAttributes`, thông qua việc
thêm trường `inclusion_list_transactions`. Ngoài ra, `notify_forkchoice_updated`
kế thừa toàn bộ chức năng trước đó.

*Lưu ý*: Nếu trường `inclusion_list_transactions` của `payload_attributes` không
rỗng, quá trình xây dựng payload MUST tạo ra một execution payload thỏa mãn các
ràng buộc inclusion list đối với `inclusion_list_transactions`.

```python
def notify_forkchoice_updated(
    self: ExecutionEngine,
    head_block_hash: Hash32,
    safe_block_hash: Hash32,
    finalized_block_hash: Hash32,
    payload_attributes: PayloadAttributes | None,
    custody_columns: CustodyColumnBits | None,
) -> PayloadId | None: ...
```

## Helpers

### Modified `PayloadAttributes`

`PayloadAttributes` được mở rộng thêm trường `inclusion_list_transactions`.

```python
@dataclass
class PayloadAttributes:
    timestamp: Uint64
    prev_randao: Bytes32
    suggested_fee_recipient: ExecutionAddress
    withdrawals: Sequence[Withdrawal]
    parent_beacon_block_root: Root
    slot_number: Uint64
    target_gas_limit: Uint64
    # [New in Heze:EIP7805]
    inclusion_list_transactions: Sequence[Transaction]
```

### Modified `Store`

*Lưu ý*: `Store` được sửa đổi để theo dõi việc các execution payload có thỏa mãn
ràng buộc inclusion list hay không.

```python
@dataclass
class Store:
    time_ms: Uint64
    genesis_time_ms: Uint64
    justified_checkpoint: Checkpoint
    finalized_checkpoint: Checkpoint
    unrealized_justified_checkpoint: Checkpoint
    unrealized_finalized_checkpoint: Checkpoint
    proposer_boost_root: Root
    equivocating_indices: set[ValidatorIndex]
    blocks: dict[Root, BeaconBlock]
    block_states: dict[Root, BeaconState]
    block_timeliness: dict[Root, list[bool]]
    checkpoint_states: dict[Checkpoint, BeaconState]
    latest_messages: dict[ValidatorIndex, LatestMessage]
    unrealized_justifications: dict[Root, Checkpoint]
    payloads: dict[Root, ExecutionPayloadEnvelope]
    payload_timeliness_vote: dict[Root, list[Boolean | None]]
    payload_data_availability_vote: dict[Root, list[Boolean | None]]
    # [New in Heze:EIP7805]
    payload_inclusion_list_satisfaction: dict[Root, bool]
```

### Modified `get_forkchoice_store`

```python
def get_forkchoice_store(anchor_state: BeaconState, anchor_block: BeaconBlock) -> Store:
    assert anchor_block.state_root == hash_tree_root(anchor_state)
    anchor_root = hash_tree_root(anchor_block)
    anchor_epoch = get_current_epoch(anchor_state)
    justified_checkpoint = Checkpoint(epoch=anchor_epoch, root=anchor_root)
    finalized_checkpoint = Checkpoint(epoch=anchor_epoch, root=anchor_root)
    genesis_time_ms = seconds_to_milliseconds(anchor_state.genesis_time)
    return Store(
        time_ms=compute_time_at_slot_ms(genesis_time_ms, anchor_state.slot),
        genesis_time_ms=genesis_time_ms,
        justified_checkpoint=justified_checkpoint,
        finalized_checkpoint=finalized_checkpoint,
        unrealized_justified_checkpoint=justified_checkpoint,
        unrealized_finalized_checkpoint=finalized_checkpoint,
        proposer_boost_root=Root(),
        equivocating_indices=set(),
        blocks={anchor_root: anchor_block.copy()},
        block_states={anchor_root: anchor_state.copy()},
        block_timeliness={anchor_root: [True, True]},
        checkpoint_states={justified_checkpoint: anchor_state.copy()},
        latest_messages={},
        unrealized_justifications={anchor_root: justified_checkpoint},
        payloads={},
        payload_timeliness_vote={anchor_root: [None] * PTC_SIZE},
        payload_data_availability_vote={anchor_root: [None] * PTC_SIZE},
        # [New in Heze:EIP7805]
        payload_inclusion_list_satisfaction={},
    )
```

### New `record_payload_inclusion_list_satisfaction`

*Lưu ý*: Các payload đã được execution engine xác nhận là `VALID` và đã được ghi
nhận là thỏa mãn ràng buộc inclusion list thì SHOULD NOT bị đánh dấu lại là
không thỏa mãn, kể cả khi các `InclusionList` liên quan sau đó đã bị dọn bỏ
(pruned).

*Lưu ý*: Một payload ở trạng thái `NOT_VALIDATED` được ghi nhận một cách lạc quan
(optimistic) là thỏa mãn ràng buộc inclusion list. Khi payload `NOT_VALIDATED`
chuyển sang `VALID`, việc payload đó có thỏa mãn ràng buộc inclusion list hay
không MUST được ghi nhận theo đặc tả
[Optimistic sync](./optimistic-sync.md#new-how-to-track-inclusion-list-satisfaction).

*Lưu ý*: Việc một payload có thỏa mãn ràng buộc inclusion list hay không MUST
NOT ảnh hưởng đến việc xác thực (validation) payload. Một payload hợp lệ nhưng
không thỏa mãn các ràng buộc đó vẫn là hợp lệ, chỉ là fork choice sẽ không xây
tiếp (extend) trên nó.

```python
def record_payload_inclusion_list_satisfaction(
    store: Store,
    root: Root,
    payload: ExecutionPayload,
    execution_engine: ExecutionEngine,
) -> None:
    slot = store.blocks[root].slot - 1
    dependent_root = get_shuffling_dependent_root(store, root, compute_epoch_at_slot(slot))
    inclusion_list_transactions = get_inclusion_list_transactions(
        get_inclusion_list_store(), slot, dependent_root, only_timely=True
    )
    is_inclusion_list_satisfied = execution_engine.is_inclusion_list_satisfied(
        payload, inclusion_list_transactions
    )
    store.payload_inclusion_list_satisfaction[root] = is_inclusion_list_satisfied
```

> 💡 Ghi chú: Hàm lấy các giao dịch từ những inclusion list đến đúng hạn
> (`only_timely=True`) của slot liền trước block, nhờ execution engine kiểm tra
> payload có thỏa mãn hay không, rồi lưu kết quả vào
> `store.payload_inclusion_list_satisfaction` theo root của beacon block.

### New `is_payload_inclusion_list_satisfied`

```python
def is_payload_inclusion_list_satisfied(store: Store, root: Root) -> bool:
    """
    Return whether the execution payload for the beacon block with root ``root``
    satisfied the inclusion list constraints, and was locally determined to be available.
    """
    # Beacon block root phải là đã biết
    assert root in store.payload_inclusion_list_satisfaction

    # Nếu payload không có sẵn ở local thì payload
    # không được coi là thỏa mãn ràng buộc inclusion list
    if not is_payload_verified(store, root):
        return False

    return store.payload_inclusion_list_satisfaction[root]
```

Trả về việc execution payload của beacon block có root `root` có thỏa mãn ràng
buộc inclusion list hay không, đồng thời payload phải được xác định là có sẵn
(available) ở local.

### Modified `should_extend_payload`

*Lưu ý*: `should_extend_payload` được sửa đổi để không xây tiếp trên một payload
nếu payload đó không thỏa mãn ràng buộc inclusion list.

```python
def should_extend_payload(store: Store, root: Root) -> bool:
    assert store.blocks[root].slot + 1 == get_current_slot(store)
    if not is_payload_verified(store, root):
        return False
    # [New in Heze:EIP7805]
    if not is_payload_inclusion_list_satisfied(store, root):
        return False
    proposer_root = store.proposer_boost_root
    payload_is_timely = payload_timeliness(store, root, timely=True)
    payload_data_is_available = payload_data_availability(store, root, available=True)
    return (
        (payload_is_timely and payload_data_is_available)
        or proposer_root == Root()
        or store.blocks[proposer_root].parent_root != root
        or is_parent_node_full(store, store.blocks[proposer_root])
    )
```

### New `get_inclusion_list_due_ms`

```python
def get_inclusion_list_due_ms() -> Uint64:
    return get_slot_component_duration_ms(INCLUSION_LIST_DUE_BPS)
```

Trả về mốc thời gian (tính bằng mili giây kể từ đầu slot) mà inclusion list phải
đến trước đó để được coi là đúng hạn (timely).

## Handlers

### New `on_inclusion_list`

*Lưu ý*: Một handler mới `on_inclusion_list` được gọi mỗi khi nhận được một
inclusion list. Bất kỳ lời gọi nào tới handler này mà gây ra exception không được
xử lý (ví dụ: một assert thất bại hoặc truy cập list ngoài phạm vi) đều được coi
là không hợp lệ và MUST NOT làm thay đổi `store`.

```python
def on_inclusion_list(store: Store, signed_inclusion_list: SignedInclusionList) -> None:
    """
    Run ``on_inclusion_list`` upon receiving a new inclusion list.
    """
    inclusion_list = signed_inclusion_list.message
    current_slot = get_current_slot(store)

    # Slot phải nằm trong cửa sổ lưu giữ (retention window)
    assert inclusion_list.slot <= current_slot
    assert inclusion_list.slot + MIN_SLOTS_FOR_INCLUSION_LISTS_REQUESTS >= current_slot

    # Danh sách giao dịch phải khác rỗng và không vượt quá kích thước tối đa
    transactions_size = sum(len(transaction) for transaction in inclusion_list.transactions)
    assert transactions_size > 0
    assert transactions_size <= MAX_TRANSACTIONS_BYTES_PER_INCLUSION_LIST

    # Mỗi giao dịch đều phải khác rỗng
    assert all(len(transaction) > 0 for transaction in inclusion_list.transactions)

    # Dependent block phải là đã biết
    assert inclusion_list.dependent_root in store.blocks
    assert inclusion_list.dependent_root in store.block_states

    # Slot của dependent block không được muộn hơn shuffling dependent slot
    epoch = compute_epoch_at_slot(inclusion_list.slot)
    dependent_slot = compute_shuffling_dependent_slot(epoch)
    assert store.blocks[inclusion_list.dependent_root].slot <= dependent_slot

    # Dependent block phải là một dependent block khả dĩ cho committee lookahead
    assert is_valid_dependent_root(store, inclusion_list.dependent_root, dependent_slot)

    # Xác minh validator thuộc inclusion list committee
    state = store.block_states[inclusion_list.dependent_root].copy()
    lookahead_start_slot = compute_shuffling_lookahead_start_slot(epoch)
    if state.slot < lookahead_start_slot:
        process_slots(state, lookahead_start_slot)
    committee = get_inclusion_list_committee(state, inclusion_list.slot)
    assert inclusion_list.validator_index in committee

    # Xác minh signature
    assert is_valid_inclusion_list_signature(state, signed_inclusion_list)

    # Inclusion list là đúng hạn (timely) nếu đến trong chính slot của nó và trước deadline
    is_current_slot = inclusion_list.slot == current_slot
    is_timely = is_current_slot and get_time_into_slot_ms(store) < get_inclusion_list_due_ms()

    # Xử lý inclusion list
    process_inclusion_list(get_inclusion_list_store(), signed_inclusion_list, is_timely)
```

> 💡 Ghi chú: Tóm tắt các bước kiểm tra: (1) slot nằm trong cửa sổ cho phép;
> (2) danh sách giao dịch khác rỗng, không quá lớn, không có giao dịch rỗng;
> (3) `dependent_root` trỏ tới một block đã biết và hợp lệ để xác định shuffling;
> (4) người ký thuộc inclusion list committee; (5) signature hợp lệ. Cuối cùng
> inclusion list được lưu vào inclusion list store kèm cờ `is_timely`.

### Modified `on_execution_payload_envelope`

```python
def on_execution_payload_envelope(
    store: Store, signed_envelope: SignedExecutionPayloadEnvelope
) -> None:
    """
    Run ``on_execution_payload_envelope`` upon receiving a new execution payload envelope.
    """
    envelope = signed_envelope.message
    # Beacon block root tương ứng phải là đã biết
    assert envelope.beacon_block_root in store.block_states

    # Kiểm tra blob data có sẵn (available) hay không
    # Nếu chưa, payload này MAY được đưa vào hàng đợi và xét lại khi blob data có sẵn
    assert is_data_available(envelope.beacon_block_root)

    state = store.block_states[envelope.beacon_block_root]

    # Xác minh execution payload envelope
    verify_execution_payload_envelope(state, signed_envelope, EXECUTION_ENGINE)

    # [New in Heze:EIP7805]
    # Kiểm tra payload này có thỏa mãn ràng buộc inclusion list hay không
    # Nếu không, thêm payload vào store với trạng thái không thỏa mãn ràng buộc inclusion list
    record_payload_inclusion_list_satisfaction(
        store, envelope.beacon_block_root, envelope.payload, EXECUTION_ENGINE
    )

    # Thêm execution payload envelope vào store
    store.payloads[envelope.beacon_block_root] = envelope
```
