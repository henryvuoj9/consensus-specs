# Phase 0 -- Beacon Chain Fork Choice

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Fork choice](#fork-choice)
  - [Constants](#constants)
  - [Configs](#configs)
    - [Time parameters](#time-parameters)
  - [Helpers](#helpers)
    - [`ForkChoiceNode`](#forkchoicenode)
    - [`LatestMessage`](#latestmessage)
    - [`Store`](#store)
    - [`get_forkchoice_store`](#get_forkchoice_store)
    - [`get_time_into_slot_ms`](#get_time_into_slot_ms)
    - [`get_slots_since_genesis`](#get_slots_since_genesis)
    - [`get_current_slot`](#get_current_slot)
    - [`get_current_store_epoch`](#get_current_store_epoch)
    - [`compute_slots_since_epoch_start`](#compute_slots_since_epoch_start)
    - [`get_ancestor`](#get_ancestor)
    - [`is_ancestor`](#is_ancestor)
    - [`calculate_committee_fraction`](#calculate_committee_fraction)
    - [`get_checkpoint_block`](#get_checkpoint_block)
    - [`get_supported_node`](#get_supported_node)
    - [`get_attestation_score`](#get_attestation_score)
    - [`compute_proposer_score`](#compute_proposer_score)
    - [`get_proposer_score`](#get_proposer_score)
    - [`get_weight`](#get_weight)
    - [`get_voting_source`](#get_voting_source)
    - [`get_node_children`](#get_node_children)
    - [`filter_node_tree`](#filter_node_tree)
    - [`get_filtered_node_tree`](#get_filtered_node_tree)
    - [`get_head`](#get_head)
    - [`update_checkpoints`](#update_checkpoints)
    - [`update_unrealized_checkpoints`](#update_unrealized_checkpoints)
    - [`get_latest_message_epoch`](#get_latest_message_epoch)
    - [`seconds_to_milliseconds`](#seconds_to_milliseconds)
    - [`milliseconds_to_seconds`](#milliseconds_to_seconds)
    - [`get_slot_component_duration_ms`](#get_slot_component_duration_ms)
    - [`get_attestation_due_ms`](#get_attestation_due_ms)
    - [`get_proposer_reorg_cutoff_ms`](#get_proposer_reorg_cutoff_ms)
    - [`get_aggregate_due_ms`](#get_aggregate_due_ms)
    - [Proposer head and reorg helpers](#proposer-head-and-reorg-helpers)
      - [`is_head_late`](#is_head_late)
      - [`is_shuffling_stable`](#is_shuffling_stable)
      - [`is_ffg_competitive`](#is_ffg_competitive)
      - [`is_finalization_ok`](#is_finalization_ok)
      - [`is_proposing_on_time`](#is_proposing_on_time)
      - [`is_head_weak`](#is_head_weak)
      - [`is_parent_strong`](#is_parent_strong)
      - [`is_proposer_equivocation`](#is_proposer_equivocation)
      - [`get_proposer_head`](#get_proposer_head)
    - [Pull-up tip helpers](#pull-up-tip-helpers)
      - [`compute_pulled_up_tip`](#compute_pulled_up_tip)
    - [`on_tick` helpers](#on_tick-helpers)
      - [`on_tick_per_slot`](#on_tick_per_slot)
    - [`on_attestation` helpers](#on_attestation-helpers)
      - [`validate_target_epoch_against_current_time`](#validate_target_epoch_against_current_time)
      - [`validate_on_attestation`](#validate_on_attestation)
      - [`store_target_checkpoint_state`](#store_target_checkpoint_state)
      - [`update_latest_messages`](#update_latest_messages)
    - [`on_block` helpers](#on_block-helpers)
      - [`record_block_timeliness`](#record_block_timeliness)
      - [`compute_shuffling_lookahead_start_slot`](#compute_shuffling_lookahead_start_slot)
      - [`compute_shuffling_dependent_slot`](#compute_shuffling_dependent_slot)
      - [`get_shuffling_dependent_root`](#get_shuffling_dependent_root)
      - [`update_proposer_boost_root`](#update_proposer_boost_root)
  - [Handlers](#handlers)
    - [`on_tick`](#on_tick)
    - [`on_block`](#on_block)
    - [`on_attestation`](#on_attestation)
    - [`on_attester_slashing`](#on_attester_slashing)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này là đặc tả fork choice (quy tắc chọn nhánh) của beacon chain, thuộc
Phase 0. Tài liệu giả định người đọc đã nắm
[đặc tả hàm state transition của beacon chain](./beacon-chain.md).

> 💡 Ghi chú: Fork choice là quy tắc mà mỗi node dùng để quyết định block nào là
> head (đỉnh) của chuỗi "chính tắc" khi có nhiều nhánh cạnh tranh. Phase 0 kết
> hợp LMD-GHOST (chọn nhánh theo trọng số vote mới nhất của validator) với Casper
> FFG (justification/finality theo checkpoint).

## Fork choice

Head block node gắn với một `store` được định nghĩa là `get_head(store)`. Tại
genesis, đặt `store = get_forkchoice_store(genesis_state, genesis_block)` rồi cập
nhật `store` bằng cách chạy:

- `on_tick(store, time_ms)` mỗi khi `time_ms > store.time_ms`, trong đó `time_ms`
  là thời gian Unix hiện tại tính bằng mili giây
- `on_block(store, block)` mỗi khi nhận được một block `block: SignedBeaconBlock`
- `on_attestation(store, attestation)` mỗi khi nhận được một attestation
  `attestation`
- `on_attester_slashing(store, attester_slashing)` mỗi khi nhận được một attester
  slashing `attester_slashing`

Bất kỳ lời gọi handler nào ở trên mà phát sinh exception không được xử lý (ví dụ
một `assert` thất bại hoặc truy cập list ngoài phạm vi) đều được coi là không hợp
lệ. Lời gọi handler không hợp lệ không được (must not) làm thay đổi `store`.

> 💡 Ghi chú: Nói cách khác, mỗi handler phải hoạt động như một giao dịch nguyên
> tử: hoặc chạy thành công hoàn toàn, hoặc `store` giữ nguyên như trước khi gọi.

*Ghi chú*:

1. **Leap seconds (giây nhuận)**: Quanh thời điểm có giây nhuận, slot sẽ kéo dài
   `SLOT_DURATION_MS + 1000` hoặc `SLOT_DURATION_MS - 1000` mili giây. Điều này
   được xử lý tự động bởi [UNIX time](https://en.wikipedia.org/wiki/Unix_time).
2. **Đồng hồ trung thực**: Giả định rằng đồng hồ của các node trung thực được
   đồng bộ với nhau, sai lệch không quá `SLOT_DURATION_MS` mili giây.
3. **Eth1 data**: Giá trị `ETH1_FOLLOW_DISTANCE` lớn được quy định trong
   [tài liệu honest validator](./validator.md) nhằm đảm bảo rằng
   `state.latest_eth1_data` của beacon chain chính tắc luôn nhất quán với chuỗi
   proof-of-work Ethereum chính tắc. Nếu không, sẽ cần can thiệp thủ công khẩn
   cấp.
4. **Fork thủ công**: Các fork thủ công có thể thay đổi tùy ý quy tắc fork
   choice, nhưng được kỳ vọng sẽ được áp dụng tại các thời điểm chuyển epoch, với
   thông tin chi tiết về fork được phản ánh trong `state.fork`.
5. **Triển khai**: Phần cài đặt trong đặc tả này được viết sao cho dễ hiểu, chứ
   không tối ưu về tính toán, bộ nhớ hay bất kỳ tài nguyên nào khác. Có thể tham
   khảo một số phương án tối ưu
   [tại đây](https://github.com/protolambda/lmd-ghost).

### Constants

| Name           | Value           |
| -------------- | --------------- |
| `BASIS_POINTS` | `Uint64(10000)` |

### Configs

| Name                                  | Value         |
| ------------------------------------- | ------------- |
| `PROPOSER_SCORE_BOOST`                | `Uint64(40)`  |
| `REORG_HEAD_WEIGHT_THRESHOLD`         | `Uint64(20)`  |
| `REORG_PARENT_WEIGHT_THRESHOLD`       | `Uint64(160)` |
| `REORG_MAX_EPOCHS_SINCE_FINALIZATION` | `Epoch(2)`    |

- Proposer score boost và các ngưỡng trọng số re-org là các giá trị phần trăm,
  được tính so với trọng số của một committee. Xem
  `calculate_committee_fraction`.

> 💡 Ghi chú: Ví dụ, `PROPOSER_SCORE_BOOST = 40` nghĩa là block được boost nhận
> thêm trọng số bằng 40% tổng effective balance của một committee (tức tổng
> balance của validator active, chưa bị slashed, chia cho `SLOTS_PER_EPOCH`).

#### Time parameters

| Name                        | Value          | Duration                         |
| --------------------------- | -------------- | -------------------------------- |
| `PROPOSER_REORG_CUTOFF_BPS` | `Uint64(1667)` | ~17% của `SLOT_DURATION_MS`      |

### Helpers

#### `ForkChoiceNode`

*Ghi chú*: Trong Phase0, `ForkChoiceNode` và `BeaconBlock` tương ứng một-một.
Lớp trừu tượng này được đưa vào để hỗ trợ khả năng nâng cấp (cho các fork sau).

```python
@dataclass(eq=True, frozen=True)
class ForkChoiceNode:
    root: Root
```

#### `LatestMessage`

*(Vote mới nhất của một validator: epoch của target và root của block được vote.)*

```python
@dataclass(eq=True, frozen=True)
class LatestMessage:
    epoch: Epoch
    root: Root
```

#### `Store`

`Store` chịu trách nhiệm lưu giữ các thông tin cần thiết cho thuật toán fork
choice. Các trường quan trọng được mô tả dưới đây:

- `justified_checkpoint`: justified checkpoint được dùng làm điểm xuất phát cho
  thuật toán fork choice LMD GHOST.
- `finalized_checkpoint`: finalized checkpoint cao nhất đã biết. Fork choice chỉ
  xét những block không xung đột với checkpoint này.
- `unrealized_justified_checkpoint` & `unrealized_finalized_checkpoint`: lần
  lượt theo dõi justified checkpoint và finalized checkpoint cao nhất, bất kể
  việc ***realization*** on-chain đã xảy ra hay chưa, tức là việc xử lý FFG cho
  các attestation mới bên trong hàm state transition. Đây là điểm khác biệt quan
  trọng so với `justified_checkpoint` & `finalized_checkpoint`, vì hai trường
  này chỉ theo dõi các checkpoint đã được realize on-chain. Lưu ý rằng việc xử lý
  thông tin FFG on-chain chỉ diễn ra tại ranh giới epoch.
- `unrealized_justifications`: lưu một map từ block root tới unrealized justified
  checkpoint quan sát được trong block đó.

> 💡 Ghi chú: "Unrealized" nghĩa là kết quả justification/finalization *sẽ* đạt
> được nếu ta chạy ngay quá trình xử lý FFG trên state hiện tại, thay vì phải chờ
> tới ranh giới epoch tiếp theo. Việc tính sớm này (gọi là "pull-up") giúp fork
> choice phản ứng nhanh hơn với các vote FFG mới.

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
    block_timeliness: dict[Root, bool]
    checkpoint_states: dict[Checkpoint, BeaconState]
    latest_messages: dict[ValidatorIndex, LatestMessage]
    unrealized_justifications: dict[Root, Checkpoint]
```

#### `get_forkchoice_store`

Anchor state được cung cấp sẽ được coi là state tin cậy, không bao giờ roll back
về trước nó. Với một full client, đây nên là genesis state.

*Ghi chú*: Xét về fork choice, block header có thể dùng thay thế cho block. Đặc
tả có thể sẽ chuyển sang dùng header để giảm chi phí trong test vector và đóng
gói tốt hơn. Các bản triển khai đầy đủ lưu block trong database của chúng và
thường dùng block đầy đủ khi chạy fork choice trong môi trường production.

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
        block_timeliness={},
        checkpoint_states={justified_checkpoint: anchor_state.copy()},
        latest_messages={},
        unrealized_justifications={anchor_root: justified_checkpoint},
    )
```

#### `get_time_into_slot_ms`

*(Số mili giây đã trôi qua kể từ đầu slot hiện tại.)*

```python
def get_time_into_slot_ms(store: Store) -> Uint64:
    return store.time_ms - compute_time_at_slot_ms(store.genesis_time_ms, get_current_slot(store))
```

#### `get_slots_since_genesis`

```python
def get_slots_since_genesis(store: Store) -> Slot:
    return compute_slot_at_time_ms(store.genesis_time_ms, store.time_ms)
```

#### `get_current_slot`

```python
def get_current_slot(store: Store) -> Slot:
    return get_slots_since_genesis(store)
```

#### `get_current_store_epoch`

```python
def get_current_store_epoch(store: Store) -> Epoch:
    return compute_epoch_at_slot(get_current_slot(store))
```

#### `compute_slots_since_epoch_start`

```python
def compute_slots_since_epoch_start(slot: Slot) -> Slot:
    return slot - compute_start_slot_at_epoch(compute_epoch_at_slot(slot))
```

#### `get_ancestor`

*(Trả về tổ tiên của `node` tại `slot` cho trước; nếu slot đó trống thì trả về
block gần nhất trước đó. Nếu block của `node` có slot ≤ `slot` thì trả về chính
`node`.)*

```python
def get_ancestor(store: Store, node: ForkChoiceNode, slot: Slot) -> ForkChoiceNode:
    block = store.blocks[node.root]
    if block.slot > slot:
        parent = ForkChoiceNode(root=block.parent_root)
        return get_ancestor(store, parent, slot)
    return node
```

#### `is_ancestor`

*(Kiểm tra `ancestor` có phải là tổ tiên của `node` hay không — một node cũng
được coi là tổ tiên của chính nó.)*

```python
def is_ancestor(store: Store, node: ForkChoiceNode, ancestor: ForkChoiceNode) -> bool:
    return get_ancestor(store, node, store.blocks[ancestor.root].slot) == ancestor
```

#### `calculate_committee_fraction`

*(Tính `committee_percent`% trọng số của một committee trung bình, dựa trên tổng
balance của các validator active và chưa bị slashed.)*

```python
def calculate_committee_fraction(state: BeaconState, committee_percent: Uint64) -> Gwei:
    unslashed_and_active_indices: set[ValidatorIndex] = set()
    for index in get_active_validator_indices(state, get_current_epoch(state)):
        if not state.validators[index].slashed:
            unslashed_and_active_indices.add(index)
    total_balance = get_total_balance(state, unslashed_and_active_indices)
    committee_weight = total_balance // Uint64(SLOTS_PER_EPOCH)
    return (committee_weight * committee_percent) // 100
```

#### `get_checkpoint_block`

```python
def get_checkpoint_block(store: Store, root: Root, epoch: Epoch) -> Root:
    """
    Compute the checkpoint block for epoch ``epoch`` in the chain of block ``root``
    """
    epoch_first_slot = compute_start_slot_at_epoch(epoch)
    node = ForkChoiceNode(root=root)
    return get_ancestor(store, node, epoch_first_slot).root
```

#### `get_supported_node`

```python
def get_supported_node(
    store: Store,  # noqa: ARG001
    message: LatestMessage,
) -> ForkChoiceNode:
    """
    Return a node supported by the ``message``.
    """
    return ForkChoiceNode(root=message.root)
```

#### `get_attestation_score`

*(Tổng effective balance của các validator active, chưa bị slashed, không
equivocate, có vote mới nhất ủng hộ `node` hoặc một hậu duệ của `node`.)*

```python
def get_attestation_score(store: Store, node: ForkChoiceNode, state: BeaconState) -> Gwei:
    unslashed_and_active_indices = [
        index
        for index in get_active_validator_indices(state, get_current_epoch(state))
        if not state.validators[index].slashed
    ]
    return Gwei(
        sum(
            state.validators[index].effective_balance
            for index in unslashed_and_active_indices
            if (
                index in store.latest_messages
                and index not in store.equivocating_indices
                and is_ancestor(
                    store, get_supported_node(store, store.latest_messages[index]), node
                )
            )
        )
    )
```

#### `compute_proposer_score`

```python
def compute_proposer_score(state: BeaconState) -> Gwei:
    return calculate_committee_fraction(state, PROPOSER_SCORE_BOOST)
```

#### `get_proposer_score`

```python
def get_proposer_score(store: Store) -> Gwei:
    justified_checkpoint_state = store.checkpoint_states[store.justified_checkpoint]
    return compute_proposer_score(justified_checkpoint_state)
```

#### `get_weight`

*(Trọng số của một node = attestation score + proposer boost, nếu node là tổ tiên
của block đang được boost.)*

```python
def get_weight(store: Store, node: ForkChoiceNode) -> Gwei:
    state = store.checkpoint_states[store.justified_checkpoint]
    attestation_score = get_attestation_score(store, node, state)
    if store.proposer_boost_root == Root():
        # Chỉ trả về attestation score nếu ``proposer_boost_root`` chưa được đặt
        return attestation_score

    # Tính proposer score nếu ``proposer_boost_root`` đã được đặt
    proposer_score = Gwei(0)
    proposer_boost_node = ForkChoiceNode(root=store.proposer_boost_root)
    # Boost được áp dụng nếu ``node`` là tổ tiên của ``proposer_boost_node``
    if is_ancestor(store, proposer_boost_node, node):
        proposer_score = get_proposer_score(store)

    return attestation_score + proposer_score
```

#### `get_voting_source`

```python
def get_voting_source(store: Store, block_root: Root) -> Checkpoint:
    """
    Compute the voting source checkpoint in event that block with root ``block_root`` is the head block
    """
    block = store.blocks[block_root]
    current_epoch = get_current_store_epoch(store)
    block_epoch = compute_epoch_at_slot(block.slot)
    if current_epoch > block_epoch:
        # Block thuộc một epoch trước, voting source sẽ được pull-up
        return store.unrealized_justifications[block_root]
    else:
        # Block không thuộc epoch trước, do đó voting source không được pull-up
        head_state = store.block_states[block_root]
        return head_state.current_justified_checkpoint
```

> 💡 Ghi chú: Voting source là checkpoint mà validator sẽ dùng làm `source` trong
> vote FFG nếu block này là head. Nếu block đến từ epoch trước, ranh giới epoch
> đã trôi qua nên ta dùng giá trị unrealized (đã pull-up) cho block đó.

#### `get_node_children`

```python
def get_node_children(store: Store, node: ForkChoiceNode) -> Sequence[ForkChoiceNode]:
    return [
        ForkChoiceNode(root=root)
        for root in store.blocks
        if store.blocks[root].parent_root == node.root
    ]
```

#### `filter_node_tree`

```python
def filter_node_tree(store: Store, node: ForkChoiceNode) -> Sequence[ForkChoiceNode]:
    children = get_node_children(store, node)

    # Nếu có nhánh con nào chứa finalized/justified checkpoint như kỳ vọng,
    # đưa node này và các hậu duệ đó vào cây node đã lọc.
    if any(children):
        viable_nodes: list[ForkChoiceNode] = []
        for child in children:
            viable_nodes.extend(filter_node_tree(store, child))
        if any(viable_nodes):
            return viable_nodes + [node]
        return []

    current_epoch = get_current_store_epoch(store)
    voting_source = get_voting_source(store, node.root)

    # Voting source phải ở cùng độ cao với justified checkpoint của store, hoặc
    # cách hiện tại không quá hai epoch
    correct_justified = (
        store.justified_checkpoint.epoch == GENESIS_EPOCH
        or voting_source.epoch == store.justified_checkpoint.epoch
        or voting_source.epoch + 2 >= current_epoch
    )

    finalized_checkpoint_block = get_checkpoint_block(
        store,
        node.root,
        store.finalized_checkpoint.epoch,
    )

    correct_finalized = (
        store.finalized_checkpoint.epoch == GENESIS_EPOCH
        or store.finalized_checkpoint.root == finalized_checkpoint_block
    )

    # Nếu đúng finalized/justified như kỳ vọng, thêm vào cây node khả thi và báo cho parent biết nhánh này khả thi.
    if correct_justified and correct_finalized:
        return [node]

    # Ngược lại, nhánh không khả thi
    return []
```

> 💡 Ghi chú: Hàm này duyệt đệ quy từ một node xuống các lá. Chỉ các **lá** được
> kiểm tra trực tiếp điều kiện justified/finalized; một node trong cây được giữ
> lại khi và chỉ khi có ít nhất một lá khả thi nằm dưới nó.

#### `get_filtered_node_tree`

```python
def get_filtered_node_tree(store: Store) -> Sequence[ForkChoiceNode]:
    """
    Retrieve a filtered node tree from ``store``, only returning branches
    whose leaf state's justified/finalized info agrees with that in ``store``.
    """
    base = ForkChoiceNode(root=store.justified_checkpoint.root)
    return filter_node_tree(store, base)
```

#### `get_head`

```python
def get_head(store: Store) -> ForkChoiceNode:
    # Lấy cây node đã lọc, chỉ gồm các nhánh khả thi
    nodes = get_filtered_node_tree(store)
    # Thực thi fork choice LMD-GHOST
    head = ForkChoiceNode(root=store.justified_checkpoint.root)
    while True:
        children = [child for child in get_node_children(store, head) if child in nodes]
        if len(children) == 0:
            return head
        # Sắp xếp theo latest attesting balance, hòa thì phân xử theo thứ tự từ điển
        # Khi hòa, ưu tiên block có root lớn hơn theo thứ tự từ điển
        head = max(children, key=lambda child: (get_weight(store, child), child.root))
```

> 💡 Ghi chú: Bắt đầu từ justified checkpoint root, ở mỗi bước ta đi xuống block
> con có trọng số lớn nhất (trong số các con nằm trong cây đã lọc), cho tới khi
> gặp một node không còn con nào. Node đó chính là head.

#### `update_checkpoints`

```python
def update_checkpoints(
    store: Store, justified_checkpoint: Checkpoint, finalized_checkpoint: Checkpoint
) -> None:
    """
    Update checkpoints in store if necessary
    """
    # Cập nhật justified checkpoint
    if justified_checkpoint.epoch > store.justified_checkpoint.epoch:
        store.justified_checkpoint = justified_checkpoint

    # Cập nhật finalized checkpoint
    if finalized_checkpoint.epoch > store.finalized_checkpoint.epoch:
        store.finalized_checkpoint = finalized_checkpoint
```

#### `update_unrealized_checkpoints`

```python
def update_unrealized_checkpoints(
    store: Store,
    unrealized_justified_checkpoint: Checkpoint,
    unrealized_finalized_checkpoint: Checkpoint,
) -> None:
    """
    Update unrealized checkpoints in store if necessary
    """
    # Cập nhật unrealized justified checkpoint
    if unrealized_justified_checkpoint.epoch > store.unrealized_justified_checkpoint.epoch:
        store.unrealized_justified_checkpoint = unrealized_justified_checkpoint

    # Cập nhật unrealized finalized checkpoint
    if unrealized_finalized_checkpoint.epoch > store.unrealized_finalized_checkpoint.epoch:
        store.unrealized_finalized_checkpoint = unrealized_finalized_checkpoint
```

#### `get_latest_message_epoch`

```python
def get_latest_message_epoch(latest_message: LatestMessage) -> Epoch:
    """
    Return epoch of the ``latest_message``.
    """
    return latest_message.epoch
```

#### `seconds_to_milliseconds`

```python
def seconds_to_milliseconds(seconds: Uint64) -> Uint64:
    """
    Convert seconds to milliseconds with overflow protection.
    Returns ``UINT64_MAX`` if the result would overflow.
    """
    if seconds > UINT64_MAX // 1000:
        return UINT64_MAX
    return seconds * 1000
```

#### `milliseconds_to_seconds`

```python
def milliseconds_to_seconds(milliseconds: Uint64) -> Uint64:
    """
    Convert milliseconds to seconds, discarding any remainder.
    """
    return milliseconds // 1000
```

#### `get_slot_component_duration_ms`

*(Đổi một giá trị basis points — phần vạn của slot — thành số mili giây.)*

```python
def get_slot_component_duration_ms(basis_points: Uint64) -> Uint64:
    """
    Calculate the duration of a slot component in milliseconds.
    """
    return basis_points * SLOT_DURATION_MS // BASIS_POINTS
```

#### `get_attestation_due_ms`

```python
def get_attestation_due_ms() -> Uint64:
    return get_slot_component_duration_ms(ATTESTATION_DUE_BPS)
```

#### `get_proposer_reorg_cutoff_ms`

```python
def get_proposer_reorg_cutoff_ms() -> Uint64:
    return get_slot_component_duration_ms(PROPOSER_REORG_CUTOFF_BPS)
```

#### `get_aggregate_due_ms`

```python
def get_aggregate_due_ms() -> Uint64:
    return get_slot_component_duration_ms(AGGREGATE_DUE_BPS)
```

#### Proposer head and reorg helpers

_Việc triển khai các helper này là tùy chọn_.

> 💡 Ghi chú: Nhóm helper này phục vụ cơ chế "proposer re-org": khi head block
> đến muộn và có ít vote, proposer của slot kế tiếp có thể chọn build trên
> parent của head (bỏ qua head block yếu đó) thay vì build trên head.

##### `is_head_late`

```python
def is_head_late(store: Store, head_root: Root) -> bool:
    return not store.block_timeliness[head_root]
```

##### `is_shuffling_stable`

```python
def is_shuffling_stable(slot: Slot) -> bool:
    return slot % SLOTS_PER_EPOCH != 0
```

##### `is_ffg_competitive`

```python
def is_ffg_competitive(store: Store, head_root: Root, parent_root: Root) -> bool:
    return (
        store.unrealized_justifications[head_root] == store.unrealized_justifications[parent_root]
    )
```

##### `is_finalization_ok`

```python
def is_finalization_ok(store: Store, slot: Slot) -> bool:
    epochs_since_finalization = compute_epoch_at_slot(slot) - store.finalized_checkpoint.epoch
    return epochs_since_finalization <= REORG_MAX_EPOCHS_SINCE_FINALIZATION
```

##### `is_proposing_on_time`

```python
def is_proposing_on_time(store: Store) -> bool:
    return get_time_into_slot_ms(store) <= get_proposer_reorg_cutoff_ms()
```

##### `is_head_weak`

*Ghi chú*: Hàm `is_head_weak` tính cả trọng số từ các validator equivocate
(vote mâu thuẫn) thuộc các committee của slot head. Điều này đảm bảo trọng số
được đếm và kết quả của `is_head_weak` là đơn điệu: thêm attestation chỉ có thể
làm tăng trọng số và đổi kết quả từ `True` sang `False`, chứ không bao giờ ngược
lại.

```python
def is_head_weak(store: Store, head_root: Root) -> bool:
    # Tính ngưỡng trọng số cho head yếu
    justified_state = store.checkpoint_states[store.justified_checkpoint]
    reorg_threshold = calculate_committee_fraction(justified_state, REORG_HEAD_WEIGHT_THRESHOLD)

    # Tính trọng số của head, bao gồm cả các equivocation
    head_state = store.block_states[head_root]
    head_block = store.blocks[head_root]
    epoch = compute_epoch_at_slot(head_block.slot)
    head_node = ForkChoiceNode(root=head_root)
    head_weight = get_attestation_score(store, head_node, justified_state)
    for index in range(get_committee_count_per_slot(head_state, epoch)):
        committee = get_beacon_committee(head_state, head_block.slot, CommitteeIndex(index))
        head_weight += Gwei(
            sum(
                justified_state.validators[index].effective_balance
                for index in committee
                if index in store.equivocating_indices
            )
        )

    return head_weight < reorg_threshold
```

##### `is_parent_strong`

```python
def is_parent_strong(store: Store, root: Root) -> bool:
    justified_state = store.checkpoint_states[store.justified_checkpoint]
    parent_threshold = calculate_committee_fraction(justified_state, REORG_PARENT_WEIGHT_THRESHOLD)
    parent_root = store.blocks[root].parent_root
    parent_node = ForkChoiceNode(root=parent_root)
    parent_weight = get_attestation_score(store, parent_node, justified_state)
    return parent_weight > parent_threshold
```

##### `is_proposer_equivocation`

```python
def is_proposer_equivocation(store: Store, root: Root) -> bool:
    block = store.blocks[root]
    proposer_index = block.proposer_index
    slot = block.slot
    # các root có cùng slot và cùng proposer
    matching_roots = [
        root
        for root, block in store.blocks.items()
        if (block.proposer_index == proposer_index and block.slot == slot)
    ]
    return len(matching_roots) > 1
```

##### `get_proposer_head`

```python
def get_proposer_head(store: Store, head_node: ForkChoiceNode, slot: Slot) -> ForkChoiceNode:
    head_block = store.blocks[head_node.root]
    parent_root = head_block.parent_root
    parent_block = store.blocks[parent_root]
    parent_node = ForkChoiceNode(root=parent_root)

    # Chỉ re-org head block nếu nó đến muộn hơn hạn chót attestation.
    head_late = is_head_late(store, head_node.root)

    # Không re-org tại ranh giới epoch, nơi proposer shuffling có thể thay đổi.
    shuffling_stable = is_shuffling_stable(slot)

    # Đảm bảo thông tin FFG của head mới sẽ cạnh tranh được với head hiện tại.
    ffg_competitive = is_ffg_competitive(store, head_node.root, parent_root)

    # Không re-org nếu chuỗi không được finalize với tần suất chấp nhận được.
    finalization_ok = is_finalization_ok(store, slot)

    # Chỉ re-org nếu chúng ta đang propose đúng giờ.
    proposing_on_time = is_proposing_on_time(store)

    # Chỉ re-org tối đa một slot.
    parent_slot_ok = parent_block.slot + 1 == head_block.slot
    current_time_ok = head_block.slot + 1 == slot
    single_slot_reorg = parent_slot_ok and current_time_ok

    # Kiểm tra head có đủ ít vote để bị proposer boost của chúng ta lấn át.
    assert store.proposer_boost_root != head_node.root  # đảm bảo boost đã hết hiệu lực
    head_weak = is_head_weak(store, head_node.root)

    # Kiểm tra các vote còn thiếu được dồn cho parent chứ không bị găm giữ.
    parent_strong = is_parent_strong(store, head_node.root)

    # Re-org mạnh tay hơn nếu có proposer equivocation ở slot trước.
    proposer_equivocation = is_proposer_equivocation(store, head_node.root)

    if all([
        head_late,
        shuffling_stable,
        ffg_competitive,
        finalization_ok,
        proposing_on_time,
        single_slot_reorg,
        head_weak,
        parent_strong,
    ]):
        # Có thể re-org head hiện tại bằng cách build trên parent node của nó.
        return parent_node
    elif all([head_weak, current_time_ok, proposer_equivocation]):
        return parent_node
    else:
        return head_node
```

*Ghi chú*: Thứ tự các điều kiện chỉ mang tính gợi ý. Các bản triển khai được tự
do tối ưu bằng cách sắp xếp lại các điều kiện từ rẻ nhất đến tốn kém nhất và trả
về sớm nếu bất kỳ điều kiện nào ở phía trước là `False`.

#### Pull-up tip helpers

##### `compute_pulled_up_tip`

```python
def compute_pulled_up_tip(store: Store, block_root: Root) -> None:
    state = store.block_states[block_root].copy()
    # Pull-up post-state của block tới ranh giới epoch kế tiếp
    process_justification_and_finalization(state)

    store.unrealized_justifications[block_root] = state.current_justified_checkpoint
    update_unrealized_checkpoints(
        store, state.current_justified_checkpoint, state.finalized_checkpoint
    )

    # Nếu block thuộc một epoch trước, áp dụng các giá trị như đã realized
    block_epoch = compute_epoch_at_slot(store.blocks[block_root].slot)
    current_epoch = get_current_store_epoch(store)
    if block_epoch < current_epoch:
        update_checkpoints(store, state.current_justified_checkpoint, state.finalized_checkpoint)
```

> 💡 Ghi chú: Hàm chạy `process_justification_and_finalization` trên một bản sao
> của post-state để biết trước kết quả FFG ("unrealized") mà không chờ tới ranh
> giới epoch. Nếu block thuộc epoch đã qua, ranh giới epoch thực ra đã trôi qua,
> nên các giá trị này được áp dụng luôn như checkpoint realized.

#### `on_tick` helpers

##### `on_tick_per_slot`

```python
def on_tick_per_slot(store: Store, time_ms: Uint64) -> None:
    previous_slot = get_current_slot(store)

    # Cập nhật thời gian của store
    store.time_ms = time_ms

    current_slot = get_current_slot(store)

    # Nếu đây là slot mới, reset store.proposer_boost_root
    if current_slot > previous_slot:
        store.proposer_boost_root = Root()

    # Nếu sang epoch mới, pull-up justification và finalization từ epoch trước
    if current_slot > previous_slot and compute_slots_since_epoch_start(current_slot) == 0:
        update_checkpoints(
            store, store.unrealized_justified_checkpoint, store.unrealized_finalized_checkpoint
        )
```

#### `on_attestation` helpers

##### `validate_target_epoch_against_current_time`

```python
def validate_target_epoch_against_current_time(store: Store, attestation: Attestation) -> None:
    target = attestation.data.target

    # Attestation phải thuộc epoch hiện tại hoặc epoch trước
    current_epoch = get_current_store_epoch(store)
    previous_epoch = saturating_sub(current_epoch, 1)
    # Nếu target của attestation thuộc epoch tương lai, hoãn xem xét cho tới khi epoch đó đến
    assert target.epoch in [current_epoch, previous_epoch]
```

##### `validate_on_attestation`

```python
def validate_on_attestation(store: Store, attestation: Attestation, is_from_block: bool) -> None:
    target = attestation.data.target

    # Nếu attestation không đến từ một beacon block message, ta phải kiểm tra phạm vi target epoch.
    if not is_from_block:
        validate_target_epoch_against_current_time(store, attestation)

    # Kiểm tra số epoch và số slot khớp nhau
    assert target.epoch == compute_epoch_at_slot(attestation.data.slot)

    # Target của attestation phải là một block đã biết. Nếu chưa biết target block, hoãn xem xét cho tới khi tìm thấy block
    assert target.root in store.blocks

    # Attestation phải trỏ tới một block đã biết. Nếu chưa biết block, hoãn xem xét cho tới khi tìm thấy block
    assert attestation.data.beacon_block_root in store.blocks
    # Attestation không được trỏ tới block ở tương lai. Nếu có, attestation không được xem xét
    assert store.blocks[attestation.data.beacon_block_root].slot <= attestation.data.slot

    # Vote LMD phải nhất quán với target của vote FFG
    assert target.root == get_checkpoint_block(
        store, attestation.data.beacon_block_root, target.epoch
    )

    # Attestation chỉ có thể ảnh hưởng tới fork choice của các slot sau đó.
    # Hoãn xem xét trong fork choice cho tới khi slot của chúng đã ở quá khứ.
    assert get_current_slot(store) >= attestation.data.slot + 1
```

##### `store_target_checkpoint_state`

```python
def store_target_checkpoint_state(store: Store, target: Checkpoint) -> None:
    # Lưu state của target checkpoint nếu chưa thấy trước đó
    if target not in store.checkpoint_states:
        base_state = store.block_states[target.root].copy()
        if base_state.slot < compute_start_slot_at_epoch(target.epoch):
            process_slots(base_state, compute_start_slot_at_epoch(target.epoch))
        store.checkpoint_states[target] = base_state
```

##### `update_latest_messages`

*(Cập nhật vote mới nhất cho mỗi validator không equivocate trong attestation,
chỉ khi target epoch mới hơn vote đang lưu.)*

```python
def update_latest_messages(
    store: Store, attesting_indices: Sequence[ValidatorIndex], attestation: Attestation
) -> None:
    target = attestation.data.target
    beacon_block_root = attestation.data.beacon_block_root
    non_equivocating_attesting_indices = [
        index for index in attesting_indices if index not in store.equivocating_indices
    ]
    for i in non_equivocating_attesting_indices:
        if i not in store.latest_messages or target.epoch > store.latest_messages[i].epoch:
            store.latest_messages[i] = LatestMessage(epoch=target.epoch, root=beacon_block_root)
```

#### `on_block` helpers

##### `record_block_timeliness`

*(Block được coi là "đúng giờ" (timely) nếu đến trong chính slot của nó và trước
hạn chót attestation.)*

```python
def record_block_timeliness(store: Store, root: Root) -> None:
    block = store.blocks[root]
    time_into_slot_ms = get_time_into_slot_ms(store)
    attestation_threshold_ms = get_attestation_due_ms()
    is_before_attesting_interval = time_into_slot_ms < attestation_threshold_ms
    is_timely = get_current_slot(store) == block.slot and is_before_attesting_interval
    store.block_timeliness[root] = is_timely
```

##### `compute_shuffling_lookahead_start_slot`

```python
def compute_shuffling_lookahead_start_slot(epoch: Epoch) -> Slot:
    lookahead_epoch = saturating_sub(epoch, MIN_SEED_LOOKAHEAD)
    return compute_start_slot_at_epoch(lookahead_epoch)
```

##### `compute_shuffling_dependent_slot`

```python
def compute_shuffling_dependent_slot(epoch: Epoch) -> Slot:
    lookahead_start_slot = compute_shuffling_lookahead_start_slot(epoch)
    return saturating_sub(lookahead_start_slot, 1)
```

##### `get_shuffling_dependent_root`

*(Root của block quyết định shuffling của `epoch` trên chuỗi chứa `root`. Hai
block có cùng dependent root thì có cùng shuffling cho epoch đó.)*

```python
def get_shuffling_dependent_root(store: Store, root: Root, epoch: Epoch) -> Root:
    node = ForkChoiceNode(root=root)
    dependent_slot = compute_shuffling_dependent_slot(epoch)
    return get_ancestor(store, node, dependent_slot).root
```

##### `update_proposer_boost_root`

```python
def update_proposer_boost_root(store: Store, head: Root, root: Root) -> None:
    is_first_block = store.proposer_boost_root == Root()
    is_timely = store.block_timeliness[root]
    epoch = get_current_store_epoch(store)
    head_dependent_root = get_shuffling_dependent_root(store, head, epoch)
    block_dependent_root = get_shuffling_dependent_root(store, root, epoch)
    is_same_dependent_root = head_dependent_root == block_dependent_root

    # Thêm proposer score boost nếu block đúng giờ, không xung đột với một block
    # đã có, và có cùng dependent root với head của chuỗi chính tắc.
    if is_timely and is_first_block and is_same_dependent_root:
        store.proposer_boost_root = root
```

### Handlers

#### `on_tick`

```python
def on_tick(store: Store, time_ms: Uint64) -> None:
    # Nếu ``store.time_ms`` bị tụt lại, vòng while sẽ đuổi kịp từng slot một
    # để đảm bảo mọi slot trước đó đều được xử lý bằng ``on_tick_per_slot``
    tick_slot = compute_slot_at_time_ms(store.genesis_time_ms, time_ms)
    while get_current_slot(store) < tick_slot:
        next_slot = get_current_slot(store) + 1
        next_slot_time_ms = compute_time_at_slot_ms(store.genesis_time_ms, next_slot)
        on_tick_per_slot(store, next_slot_time_ms)
    on_tick_per_slot(store, time_ms)
```

#### `on_block`

```python
def on_block(store: Store, signed_block: SignedBeaconBlock) -> None:
    """
    Run ``on_block`` upon receiving a new block.
    """
    block = signed_block.message
    block_root = hash_tree_root(block)

    # Trả về sớm nếu block đã được biết
    if block_root in store.blocks:
        return

    # Parent block phải đã được biết
    assert block.parent_root in store.block_states
    # Tạo bản sao của state để tránh vấn đề do tính khả biến (mutability)
    pre_state = store.block_states[block.parent_root].copy()
    # Block không được ở tương lai. Nếu có, phải hoãn xem xét cho tới khi chúng ở quá khứ.
    assert get_current_slot(store) >= block.slot

    # Kiểm tra block muộn hơn slot của finalized epoch (tối ưu để giảm số lần gọi get_ancestor)
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

    # Tính head trước khi áp dụng block
    head = get_head(store)
    # Thêm block mới vào store
    store.blocks[block_root] = block
    # Thêm state mới của block này vào store
    store.block_states[block_root] = state

    record_block_timeliness(store, block_root)
    update_proposer_boost_root(store, head.root, block_root)

    # Cập nhật checkpoint trong store nếu cần
    update_checkpoints(store, state.current_justified_checkpoint, state.finalized_checkpoint)

    # Tính sớm unrealized justification và finality
    compute_pulled_up_tip(store, block_root)
```

#### `on_attestation`

```python
def on_attestation(store: Store, attestation: Attestation, is_from_block: bool = False) -> None:
    """
    Run ``on_attestation`` upon receiving a new attestation from either within a block or directly on the wire.

    An ``attestation`` that is asserted as invalid may be valid at a later time,
    consider scheduling it for later processing in such case.
    """
    validate_on_attestation(store, attestation, is_from_block)

    store_target_checkpoint_state(store, attestation.data.target)

    # Lấy state tại `target` để xác thực đầy đủ attestation
    target_state = store.checkpoint_states[attestation.data.target]
    indexed_attestation = get_indexed_attestation(target_state, attestation)
    assert is_valid_indexed_attestation(target_state, indexed_attestation)

    # Cập nhật latest message cho các attesting index
    update_latest_messages(store, indexed_attestation.attesting_indices, attestation)
```

> 💡 Ghi chú: Một attestation bị `assert` từ chối (ví dụ vì block chưa đến hoặc
> slot chưa qua) có thể trở nên hợp lệ sau này, nên client có thể xếp lịch xử lý
> lại thay vì bỏ hẳn.

#### `on_attester_slashing`

*Ghi chú*: `on_attester_slashing` nên được gọi cả trong quá trình sync, và client
MUST duy trì tập equivocation từ các `AttesterSlashing` tính từ ít nhất finalized
checkpoint mới nhất.

> 💡 Ghi chú: Validator nằm trong cả hai attestation mâu thuẫn được đưa vào
> `store.equivocating_indices`; từ đó vote của họ không còn được tính vào trọng
> số fork choice (xem `get_attestation_score` và `update_latest_messages`).

```python
def on_attester_slashing(store: Store, attester_slashing: AttesterSlashing) -> None:
    """
    Run ``on_attester_slashing`` immediately upon receiving a new attester slashing
    from either within a block or directly on the wire.
    """
    attestation_1 = attester_slashing.attestation_1
    attestation_2 = attester_slashing.attestation_2
    assert is_slashable_attestation_data(attestation_1.data, attestation_2.data)
    state = store.block_states[store.justified_checkpoint.root]
    assert is_valid_indexed_attestation(state, attestation_1)
    assert is_valid_indexed_attestation(state, attestation_2)

    indices = set(attestation_1.attesting_indices).intersection(attestation_2.attesting_indices)
    for index in indices:
        store.equivocating_indices.add(index)
```
