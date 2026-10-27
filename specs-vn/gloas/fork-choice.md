# Gloas -- Fork Choice

*Ghi chú*: Tài liệu này đang trong quá trình soạn thảo (work-in-progress), dành cho các nhà nghiên cứu và đội ngũ phát triển client.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Types](#types)
  - [New `PayloadStatus`](#new-payloadstatus)
  - [New `CustodyColumnBits`](#new-custodycolumnbits)
- [Constants](#constants)
- [Protocols](#protocols)
  - [`ExecutionEngine`](#executionengine)
    - [Modified `notify_forkchoice_updated`](#modified-notify_forkchoice_updated)
- [Helpers](#helpers)
  - [Modified `ForkChoiceNode`](#modified-forkchoicenode)
  - [Modified `PayloadAttributes`](#modified-payloadattributes)
  - [Modified `LatestMessage`](#modified-latestmessage)
  - [Modified `Store`](#modified-store)
  - [Modified `get_forkchoice_store`](#modified-get_forkchoice_store)
  - [New `get_custody_column_bits`](#new-get_custody_column_bits)
  - [New `notify_ptc_messages`](#new-notify_ptc_messages)
  - [Modified `is_data_available`](#modified-is_data_available)
  - [New `is_payload_verified`](#new-is_payload_verified)
  - [New `payload_timeliness`](#new-payload_timeliness)
  - [New `payload_data_availability`](#new-payload_data_availability)
  - [New `get_parent_payload_status`](#new-get_parent_payload_status)
  - [New `is_parent_node_full`](#new-is_parent_node_full)
  - [Modified `get_ancestor`](#modified-get_ancestor)
  - [Modified `is_ancestor`](#modified-is_ancestor)
  - [Modified `get_checkpoint_block`](#modified-get_checkpoint_block)
  - [Modified `get_supported_node`](#modified-get_supported_node)
  - [New `is_previous_slot_payload_decision`](#new-is_previous_slot_payload_decision)
  - [New `should_build_on_full`](#new-should_build_on_full)
  - [New `should_extend_payload`](#new-should_extend_payload)
  - [New `get_payload_status_tiebreaker`](#new-get_payload_status_tiebreaker)
  - [New `should_apply_proposer_boost`](#new-should_apply_proposer_boost)
  - [Modified `get_weight`](#modified-get_weight)
  - [Modified `get_filtered_node_tree`](#modified-get_filtered_node_tree)
  - [Modified `get_node_children`](#modified-get_node_children)
  - [Modified `get_head`](#modified-get_head)
  - [Modified `get_latest_message_epoch`](#modified-get_latest_message_epoch)
  - [New `verify_execution_payload_envelope`](#new-verify_execution_payload_envelope)
  - [New `is_valid_dependent_root`](#new-is_valid_dependent_root)
  - [Modified `get_attestation_due_ms`](#modified-get_attestation_due_ms)
  - [Modified `get_aggregate_due_ms`](#modified-get_aggregate_due_ms)
  - [Modified `get_sync_message_due_ms`](#modified-get_sync_message_due_ms)
  - [Modified `get_contribution_due_ms`](#modified-get_contribution_due_ms)
  - [New `get_payload_due_ms`](#new-get_payload_due_ms)
  - [New `get_payload_attestation_due_ms`](#new-get_payload_attestation_due_ms)
  - [Proposer head and reorg helpers](#proposer-head-and-reorg-helpers)
    - [Modified `is_head_late`](#modified-is_head_late)
    - [Modified `is_head_weak`](#modified-is_head_weak)
    - [Modified `is_parent_strong`](#modified-is_parent_strong)
    - [Modified `get_proposer_head`](#modified-get_proposer_head)
  - [`on_attestation` helpers](#on_attestation-helpers)
    - [Modified `validate_on_attestation`](#modified-validate_on_attestation)
    - [Modified `update_latest_messages`](#modified-update_latest_messages)
  - [`on_block` helpers](#on_block-helpers)
    - [Modified `record_block_timeliness`](#modified-record_block_timeliness)
    - [Modified `get_shuffling_dependent_root`](#modified-get_shuffling_dependent_root)
    - [Modified `update_proposer_boost_root`](#modified-update_proposer_boost_root)
- [Handlers](#handlers)
  - [Modified `on_block`](#modified-on_block)
  - [New `on_execution_payload_envelope`](#new-on_execution_payload_envelope)
  - [New `on_payload_attestation_message`](#new-on_payload_attestation_message)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả các thay đổi đối với fork choice đi kèm bản nâng cấp Gloas.

> 💡 Ghi chú: Thay đổi cốt lõi đến từ EIP-7732 (ePBS - enshrined
> Proposer-Builder Separation). Beacon block giờ chỉ chứa *bid* của builder;
> execution payload được builder công bố riêng sau đó (trong một *envelope*), và
> PTC (payload timeliness committee) bỏ phiếu xem payload có đến đúng hạn và dữ
> liệu blob có sẵn hay không. Vì vậy, mỗi beacon block trong cây fork choice
> được tách thành nhiều node theo trạng thái payload: *pending* (chưa quyết
> định), *empty* (không có payload) và *full* (có payload).

## Types

### New `PayloadStatus`

Kiểu số biểu diễn trạng thái payload trong fork choice; nhận một trong các giá
trị `PAYLOAD_STATUS_*` (xem phần [Constants](#constants)).

```python
class PayloadStatus(Uint8):
    """
    The fork-choice status of an execution payload, one of the
    ``PAYLOAD_STATUS_*`` values.
    """
```

### New `CustodyColumnBits`

Bitvector đánh dấu các data column mà một node custody (lưu giữ), mỗi column
ứng với một bit.

```python
class CustodyColumnBits(BitVector):
    """
    Bits marking the data columns custodied by a node, one bit per column.
    """

    LENGTH = NUMBER_OF_COLUMNS
```

## Constants

| Name                                 | Value                           |
| ------------------------------------ | ------------------------------- |
| `PAYLOAD_TIMELY_THRESHOLD`           | `Uint64(PTC_SIZE // 2)` (= 256) |
| `DATA_AVAILABILITY_TIMELY_THRESHOLD` | `Uint64(PTC_SIZE // 2)` (= 256) |
| `PAYLOAD_STATUS_EMPTY`               | `PayloadStatus(0)`              |
| `PAYLOAD_STATUS_FULL`                | `PayloadStatus(1)`              |
| `PAYLOAD_STATUS_PENDING`             | `PayloadStatus(2)`              |
| `ATTESTATION_TIMELINESS_INDEX`       | `Uint64(0)`                     |
| `PTC_TIMELINESS_INDEX`               | `Uint64(1)`                     |
| `NUM_BLOCK_TIMELINESS_DEADLINES`     | `Uint64(2)`                     |

> 💡 Ghi chú: Hai ngưỡng `*_THRESHOLD` bằng một nửa kích thước PTC; một payload
> chỉ được coi là đúng hạn / có dữ liệu sẵn sàng khi số phiếu tương ứng *vượt
> quá* ngưỡng này (đa số tuyệt đối). `ATTESTATION_TIMELINESS_INDEX` và
> `PTC_TIMELINESS_INDEX` là chỉ số trong danh sách `store.block_timeliness[root]`,
> ứng với hai deadline: deadline của attestation và deadline của PTC.

## Protocols

### `ExecutionEngine`

#### Modified `notify_forkchoice_updated`

Trong Gloas, các giá trị `finalized_block_hash` và `safe_block_hash` **MUST**
được tính như dưới đây. Mọi ngữ nghĩa khác của `notify_forkchoice_updated` và
cách gọi hàm này được kế thừa từ các fork trước.

- `finalized_block_hash = finalized_block_bid.parent_block_hash`,
- `safe_block_hash = get_safe_execution_block_hash(fcr_store)`.

Trong đó:

- `finalized_block = store.blocks[store.finalized_checkpoint.root]`,
- `finalized_block_bid = finalized_block.body.signed_execution_payload_bid.message`.

> 💡 Ghi chú: Vì beacon block đã finalized chỉ cam kết tới payload *cha* (qua
> `parent_block_hash` trong bid), nên execution block được coi là finalized là
> block cha đó, chứ không phải payload của chính beacon block finalized.

*Ghi chú*: `get_safe_execution_block_hash` được sửa đổi trong Gloas, xem
[Fast Confirmation](./fast-confirmation.md#modified-get_safe_execution_block_hash).

*Ghi chú*: Execution engine dùng `custody_columns` làm tập sampling cho các blob
transaction trong transaction pool (mempool). Giá trị này SHOULD là
`get_custody_column_bits(node_id, custody_group_count)`, với custody group count
mà node đang quảng bá (advertise).

```python
def notify_forkchoice_updated(
    self: ExecutionEngine,
    head_block_hash: Hash32,
    safe_block_hash: Hash32,
    finalized_block_hash: Hash32,
    payload_attributes: PayloadAttributes | None,
    # [New in Gloas:EIP8070]
    custody_columns: CustodyColumnBits | None,
) -> PayloadId | None: ...
```

## Helpers

### Modified `ForkChoiceNode`

Mỗi node trong cây fork choice giờ gồm block root và `payload_status`. Cùng một
beacon block có thể xuất hiện dưới dạng ba node: *pending*, *empty* và *full*.

```python
@dataclass(eq=True, frozen=True)
class ForkChoiceNode:
    root: Root
    # [New in Gloas:EIP7732]
    payload_status: PayloadStatus  # Một trong các giá trị PAYLOAD_STATUS_*
```

### Modified `PayloadAttributes`

```python
@dataclass
class PayloadAttributes:
    timestamp: Uint64
    prev_randao: Bytes32
    suggested_fee_recipient: ExecutionAddress
    withdrawals: Sequence[Withdrawal]
    parent_beacon_block_root: Root
    # [New in Gloas:EIP7843]
    slot_number: Uint64
    # [New in Gloas]
    target_gas_limit: Uint64
```

### Modified `LatestMessage`

*Ghi chú*: Class này được sửa để lưu slot thay vì epoch.

> 💡 Ghi chú: Cần slot (thay vì epoch) để biết attestation được tạo ở slot sau
> block mà nó vote hay không; điều này quyết định vote ủng hộ node *pending* hay
> node *empty*/*full* (xem `get_supported_node`). Trường `payload_present` cho
> biết validator có thấy payload của block đó hay không.

```python
@dataclass(eq=True, frozen=True)
class LatestMessage:
    slot: Slot
    root: Root
    payload_present: bool
```

### Modified `Store`

> 💡 Ghi chú: Các trường mới: `payloads` lưu các execution payload envelope đã
> nhận và xác minh; `payload_timeliness_vote` và `payload_data_availability_vote`
> lưu phiếu của từng thành viên PTC (`None` nghĩa là chưa có phiếu).
> `block_timeliness` giờ là danh sách bool, mỗi phần tử ứng với một deadline.

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
    # [Modified in Gloas:EIP7732]
    block_timeliness: dict[Root, list[bool]]
    checkpoint_states: dict[Checkpoint, BeaconState]
    latest_messages: dict[ValidatorIndex, LatestMessage]
    unrealized_justifications: dict[Root, Checkpoint]
    # [New in Gloas:EIP7732]
    payloads: dict[Root, ExecutionPayloadEnvelope]
    # [New in Gloas:EIP7732]
    payload_timeliness_vote: dict[Root, list[Boolean | None]]
    # [New in Gloas:EIP7732]
    payload_data_availability_vote: dict[Root, list[Boolean | None]]
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
        # [New in Gloas:EIP7732]
        block_timeliness={anchor_root: [True, True]},
        checkpoint_states={justified_checkpoint: anchor_state.copy()},
        latest_messages={},
        unrealized_justifications={anchor_root: justified_checkpoint},
        # [New in Gloas:EIP7732]
        payloads={},
        # [New in Gloas:EIP7732]
        payload_timeliness_vote={anchor_root: [None] * PTC_SIZE},
        # [New in Gloas:EIP7732]
        payload_data_availability_vote={anchor_root: [None] * PTC_SIZE},
    )
```

### New `get_custody_column_bits`

Tính bitvector các column index mà `node_id` custody, dựa trên các custody group
của node.

```python
def get_custody_column_bits(node_id: NodeID, custody_group_count: Uint64) -> CustodyColumnBits:
    """
    Compute the bitvector of column indices custodied by ``node_id``.
    """
    bits = CustodyColumnBits()
    for custody_group in get_custody_groups(node_id, custody_group_count):
        for column in compute_columns_for_custody_group(custody_group):
            bits[column] = Boolean(True)
    return bits
```

### New `notify_ptc_messages`

Hàm tách các payload attestation được đóng gói trong beacon block thành từng
`PayloadAttestationMessage` riêng lẻ (mỗi validator tham gia một message) và đưa
chúng vào store qua `on_payload_attestation_message`. Vì các payload attestation
này nằm trong beacon block (đã được xác minh khi xử lý block), không cần kiểm tra
lại signature; message được tạo với signature rỗng và `is_from_block=True`.

```python
def notify_ptc_messages(
    store: Store, state: BeaconState, payload_attestations: Sequence[PayloadAttestation]
) -> None:
    """
    Extracts a list of ``PayloadAttestationMessage`` from ``payload_attestations`` and updates the store with them
    These Payload attestations are assumed to be in the beacon block hence signature verification is not needed
    """
    if state.slot == 0:
        return
    for payload_attestation in payload_attestations:
        indexed_payload_attestation = get_indexed_payload_attestation(state, payload_attestation)
        for idx in indexed_payload_attestation.attesting_indices:
            on_payload_attestation_message(
                store,
                PayloadAttestationMessage(
                    validator_index=idx,
                    data=payload_attestation.data,
                    signature=BLSSignature(),
                ),
                is_from_block=True,
            )
```

### Modified `is_data_available`

Trong Gloas, các KZG commitment không còn nằm trong data column sidecar mà nằm
trong execution payload bid của beacon block, nên hàm lấy cả column sidecar lẫn
KZG commitment tương ứng để xác minh.

```python
def is_data_available(beacon_block_root: Root) -> bool:
    # `retrieve_column_sidecars_and_kzg_commitments` phụ thuộc vào implementation
    # và ngữ cảnh, thay thế cho `retrieve_column_sidecars`. Với block root cho
    # trước, hàm trả về tất cả column sidecar cần sample, hoặc raise exception
    # nếu chúng không có sẵn; ngoài ra hàm còn trả về tất cả kzg commitment
    # tương ứng. Mạng p2p không đảm bảo lấy được sidecar nằm ngoài phạm vi
    # `MIN_EPOCHS_FOR_DATA_COLUMN_SIDECARS_REQUESTS` epoch.
    column_sidecars, kzg_commitments = retrieve_column_sidecars_and_kzg_commitments(
        beacon_block_root
    )
    return all(
        verify_data_column_sidecar(column_sidecar, kzg_commitments)
        and verify_data_column_sidecar_kzg_proofs(column_sidecar, kzg_commitments)
        for column_sidecar in column_sidecars
    )
```

### New `is_payload_verified`

Trả về `True` nếu execution payload envelope của beacon block có root `root` đã
được nhận cục bộ và xác minh thành công qua `on_execution_payload_envelope`.

```python
def is_payload_verified(store: Store, root: Root) -> bool:
    """
    Return whether the execution payload envelope for the beacon block with
    root ``root`` has been locally delivered and verified via
    ``on_execution_payload_envelope``.
    """
    return root in store.payloads
```

### New `payload_timeliness`

Trả về liệu execution payload của beacon block có root `root` có được coi là
đúng hạn (khi `timely=True`), hoặc là *không* đúng hạn (khi `timely=False`), có
xét cả việc payload có sẵn cục bộ hay không và phiếu của PTC.

> 💡 Ghi chú: Nếu node chưa có payload cục bộ, payload luôn bị coi là không đúng
> hạn, bất kể PTC bỏ phiếu thế nào. Ngược lại, hàm đếm số phiếu (bỏ qua phiếu
> `None`) có giá trị bằng `timely` và so với `PAYLOAD_TIMELY_THRESHOLD`. Lưu ý
> `payload_timeliness(..., timely=False)` không phải đơn giản là phủ định của
> `payload_timeliness(..., timely=True)`: có thể cả hai đều `False` nếu không bên
> nào đạt đa số.

```python
def payload_timeliness(store: Store, root: Root, timely: bool) -> bool:
    """
    Return whether the execution payload for the beacon block with root ``root``
    is considered ``timely`` (or not, when ``timely`` is ``False``), taking into
    consideration local availability and PTC votes.
    """
    # Beacon block root phải đã được biết
    assert root in store.payload_timeliness_vote

    # Nếu payload không có sẵn cục bộ, payload
    # không được coi là có sẵn bất kể phiếu PTC
    if not is_payload_verified(store, root):
        return not timely

    votes = [bool(vote) for vote in store.payload_timeliness_vote[root] if vote is not None]
    return sum(vote == timely for vote in votes) > PAYLOAD_TIMELY_THRESHOLD
```

### New `payload_data_availability`

Tương tự `payload_timeliness`, nhưng cho dữ liệu blob: trả về liệu blob data của
beacon block có root `root` có được coi là có sẵn (khi `available=True`), hoặc
*không* có sẵn (khi `available=False`), có xét việc payload có sẵn cục bộ và
phiếu của PTC.

```python
def payload_data_availability(store: Store, root: Root, available: bool) -> bool:
    """
    Return whether the blob data for the beacon block with root ``root`` is
    considered ``available`` (or not, when ``available`` is ``False``), taking into
    consideration local availability and PTC votes.
    """
    # Beacon block root phải đã được biết
    assert root in store.payload_data_availability_vote

    # Nếu payload không có sẵn cục bộ, blob data
    # không được coi là có sẵn bất kể phiếu PTC
    if not is_payload_verified(store, root):
        return not available

    votes = [bool(vote) for vote in store.payload_data_availability_vote[root] if vote is not None]
    return sum(vote == available for vote in votes) > DATA_AVAILABILITY_TIMELY_THRESHOLD
```

### New `get_parent_payload_status`

Xác định block được build trên node *full* hay *empty* của block cha: nếu
`parent_block_hash` trong bid của block trùng với `block_hash` trong bid của
block cha, nghĩa là block này build trên payload của block cha (*full*); ngược
lại là *empty*.

```python
def get_parent_payload_status(store: Store, block: BeaconBlock) -> PayloadStatus:
    parent = store.blocks[block.parent_root]
    parent_block_hash = block.body.signed_execution_payload_bid.message.parent_block_hash
    message_block_hash = parent.body.signed_execution_payload_bid.message.block_hash
    return PAYLOAD_STATUS_FULL if parent_block_hash == message_block_hash else PAYLOAD_STATUS_EMPTY
```

### New `is_parent_node_full`

```python
def is_parent_node_full(store: Store, block: BeaconBlock) -> bool:
    return get_parent_payload_status(store, block) == PAYLOAD_STATUS_FULL
```

### Modified `get_ancestor`

*Ghi chú*: `get_ancestor` được sửa để trả về cả thông tin chain dựa trên block
*empty* hay *full* (tức trả về `ForkChoiceNode` thay vì chỉ root).

```python
def get_ancestor(store: Store, node: ForkChoiceNode, slot: Slot) -> ForkChoiceNode:
    block = store.blocks[node.root]
    if block.slot > slot:
        # [Modified in Gloas:EIP7732]
        parent = ForkChoiceNode(
            root=block.parent_root,
            payload_status=get_parent_payload_status(store, block),
        )
        return get_ancestor(store, parent, slot)
    return node
```

### Modified `is_ancestor`

*Ghi chú*: Hàm này được sửa để xử lý quan hệ giữa các fork choice node *pending*,
*empty* và *full*.

> 💡 Ghi chú: Node `ancestor` là tổ tiên của `node` khi root trùng nhau và: hoặc
> `payload_status` cũng trùng, hoặc `ancestor` là node *pending* (node *pending*
> là tổ tiên chung của cả nhánh *empty* lẫn *full* của cùng block).

```python
def is_ancestor(store: Store, node: ForkChoiceNode, ancestor: ForkChoiceNode) -> bool:
    node_ancestor = get_ancestor(store, node, store.blocks[ancestor.root].slot)
    if node_ancestor.root != ancestor.root:
        return False

    # [New in Gloas:EIP7732]
    return (
        node_ancestor.payload_status == ancestor.payload_status
        or ancestor.payload_status == PAYLOAD_STATUS_PENDING
    )
```

### Modified `get_checkpoint_block`

```python
def get_checkpoint_block(store: Store, root: Root, epoch: Epoch) -> Root:
    """
    Compute the checkpoint block for epoch ``epoch`` in the chain of block ``root``
    """
    epoch_first_slot = compute_start_slot_at_epoch(epoch)
    # [Modified in Gloas:EIP7732]
    node = ForkChoiceNode(root=root, payload_status=PAYLOAD_STATUS_PENDING)
    return get_ancestor(store, node, epoch_first_slot).root
```

### Modified `get_supported_node`

*Ghi chú*: `get_supported_node` được sửa để gán `payload_status`.

> 💡 Ghi chú: Nếu attestation được tạo ở slot *sau* slot của block mà nó vote,
> vote đó ủng hộ node *full* hoặc *empty* tùy theo `payload_present`. Nếu
> attestation ở cùng slot với block (lúc đó payload chưa thể được công bố), vote
> chỉ ủng hộ node *pending*.

```python
def get_supported_node(store: Store, message: LatestMessage) -> ForkChoiceNode:
    """
    Return a node supported by the ``message``.
    """
    # [New in Gloas:EIP7732]
    block = store.blocks[message.root]
    if block.slot < message.slot:
        if message.payload_present:
            payload_status = PAYLOAD_STATUS_FULL
        else:
            payload_status = PAYLOAD_STATUS_EMPTY
    else:
        payload_status = PAYLOAD_STATUS_PENDING

    # [Modified in Gloas:EIP7732]
    return ForkChoiceNode(root=message.root, payload_status=payload_status)
```

### New `is_previous_slot_payload_decision`

*Ghi chú*: Predicate này nhận diện trường hợp một block từ slot trước chưa nhận
được các attestation để quyết định payload của nó là *empty* hay *full*, nên
không thể chọn dựa trên weight.

> 💡 Ghi chú: Attestation cho block ở slot `N` chỉ có thể biểu thị ý kiến về
> payload từ slot `N + 1` trở đi. Vì vậy khi đang ở slot `N + 1`, các node
> *empty*/*full* của block slot `N` chưa có weight có ý nghĩa, và lựa chọn giữa
> chúng được thực hiện bằng tiebreaker (xem `get_payload_status_tiebreaker`).

```python
def is_previous_slot_payload_decision(store: Store, node: ForkChoiceNode) -> bool:
    is_previous_slot = store.blocks[node.root].slot + 1 == get_current_slot(store)
    is_payload_decision = node.payload_status in [PAYLOAD_STATUS_EMPTY, PAYLOAD_STATUS_FULL]
    return is_previous_slot and is_payload_decision
```

### New `should_build_on_full`

*Ghi chú*: Hàm này được proposer gọi để quyết định build trên node cha *empty*
hay *full*. Với node từ slot sớm hơn, hàm tuân theo payload status của node. Với
node *full* từ slot ngay trước, hàm xét quan điểm của PTC về cả độ đúng hạn của
payload (payload timeliness) lẫn tính sẵn có của dữ liệu (data availability).

> 💡 Ghi chú: Cụ thể, với head *full* ở slot ngay trước, proposer build trên
> *full* trừ khi PTC có đa số cho rằng payload *không* đúng hạn, hoặc đa số cho
> rằng dữ liệu *không* có sẵn (hoặc node chưa có payload cục bộ).

```python
def should_build_on_full(store: Store, head: ForkChoiceNode, slot: Slot) -> bool:
    assert head.payload_status != PAYLOAD_STATUS_PENDING
    if store.blocks[head.root].slot + 1 != slot:
        return head.payload_status == PAYLOAD_STATUS_FULL
    if head.payload_status == PAYLOAD_STATUS_EMPTY:
        return False
    if payload_timeliness(store, head.root, timely=False):
        return False
    if payload_data_availability(store, head.root, available=False):
        return False
    return True
```

### New `should_extend_payload`

*Ghi chú*: Hàm này quyết định có extend (nối tiếp) payload đã có sẵn tương ứng
với beacon block `root` từ slot trước hay không. Payload được extend khi quan
điểm của PTC ủng hộ cả payload timeliness lẫn data availability. Nếu không, vẫn
extend, trừ khi block được proposer boost build trên beacon block `root` và chọn
*empty*.

> 💡 Ghi chú: Nếu payload chưa được xác minh cục bộ thì luôn trả về `False`.
> Ngoài ra hàm trả về `True` khi một trong các điều kiện sau đúng: PTC có đa số
> cho cả timeliness và data availability; chưa có proposer boost root; block
> được boost không phải là con của `root`; hoặc block được boost build trên node
> *full* của `root`.

```python
def should_extend_payload(store: Store, root: Root) -> bool:
    assert store.blocks[root].slot + 1 == get_current_slot(store)
    if not is_payload_verified(store, root):
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

### New `get_payload_status_tiebreaker`

Tiebreaker dùng khi các node có cùng weight. Với quyết định payload của block ở
slot trước, *empty* nhận giá trị 1; *full* nhận 2 nếu `should_extend_payload`
trả về `True` (thắng *empty*), ngược lại nhận 0 (thua *empty*). Các trường hợp
khác dùng chính giá trị `payload_status`.

```python
def get_payload_status_tiebreaker(store: Store, node: ForkChoiceNode) -> Uint8:
    if is_previous_slot_payload_decision(store, node):
        # Để quyết định payload từ slot trước, chọn
        # giữa FULL và EMPTY dựa trên `should_extend_payload`
        if node.payload_status == PAYLOAD_STATUS_EMPTY:
            return Uint8(1)
        if should_extend_payload(store, node.root):
            return Uint8(2)
        return Uint8(0)
    else:
        return node.payload_status
```

### New `should_apply_proposer_boost`

Quyết định có áp dụng proposer boost hay không. Mục đích là tránh việc proposer
boost giúp một block "đè" lên block cha yếu khi proposer của block cha đã
equivocate (tạo nhiều block cho cùng slot).

> 💡 Ghi chú: Proposer boost được áp dụng nếu: block cha không thuộc slot ngay
> trước; hoặc block cha không yếu (not weak); hoặc, khi block cha yếu và thuộc
> slot ngay trước, không tồn tại block nào khác của cùng proposer ở slot đó đến
> kịp deadline PTC (tức không có equivocation sớm).

```python
def should_apply_proposer_boost(store: Store) -> bool:
    if store.proposer_boost_root == Root():
        return False

    block = store.blocks[store.proposer_boost_root]
    parent_root = block.parent_root
    parent = store.blocks[parent_root]
    slot = block.slot

    # Áp dụng proposer boost nếu `parent` không thuộc slot ngay trước
    if parent.slot + 1 < slot:
        return True

    # Áp dụng proposer boost nếu `parent` không yếu
    if not is_head_weak(store, parent_root):
        return True

    # Nếu `parent` yếu và thuộc slot ngay trước, áp dụng
    # proposer boost nếu không có equivocation sớm nào
    equivocations = [
        root
        for root, block in store.blocks.items()
        if (
            store.block_timeliness[root][PTC_TIMELINESS_INDEX]
            and block.proposer_index == parent.proposer_index
            and block.slot + 1 == slot
            and root != parent_root
        )
    ]

    return len(equivocations) == 0
```

### Modified `get_weight`

> 💡 Ghi chú: Node *empty*/*full* của block ở slot ngay trước có weight bằng 0
> (lựa chọn giữa chúng do tiebreaker quyết định). Proposer score chỉ được cộng
> khi `should_apply_proposer_boost` trả về `True` và node là tổ tiên của node
> *pending* của block được boost.

```python
def get_weight(store: Store, node: ForkChoiceNode) -> Gwei:
    # [New in Gloas:EIP7732]
    if is_previous_slot_payload_decision(store, node):
        return Gwei(0)

    state = store.checkpoint_states[store.justified_checkpoint]
    attestation_score = get_attestation_score(store, node, state)
    # [Modified in Gloas:EIP7732]
    if not should_apply_proposer_boost(store):
        # Chỉ trả về attestation score nếu không áp dụng proposer boost
        return attestation_score

    # Tính proposer score nếu áp dụng proposer boost
    proposer_score = Gwei(0)
    # [Modified in Gloas:EIP7732]
    proposer_boost_node = ForkChoiceNode(
        root=store.proposer_boost_root, payload_status=PAYLOAD_STATUS_PENDING
    )
    # Boost được áp dụng nếu ``node`` là tổ tiên của ``proposer_boost_node``
    if is_ancestor(store, proposer_boost_node, node):
        proposer_score = get_proposer_score(store)

    return attestation_score + proposer_score
```

### Modified `get_filtered_node_tree`

```python
def get_filtered_node_tree(store: Store) -> Sequence[ForkChoiceNode]:
    """
    Retrieve a filtered node tree from ``store``, only returning branches
    whose leaf state's justified/finalized info agrees with that in ``store``.
    """
    # [Modified in Gloas:EIP7732]
    base = ForkChoiceNode(
        root=store.justified_checkpoint.root,
        payload_status=PAYLOAD_STATUS_PENDING,
    )
    return filter_node_tree(store, base)
```

### Modified `get_node_children`

*Ghi chú*: Hàm này được sửa đổi để đưa vào loại node con mới, đại diện cho các
block *full* (đã có execution payload) và *empty* (không có payload).

> 💡 Ghi chú: Trong Gloas, mỗi beacon block được biểu diễn trong cây fork choice
> bằng nhiều `ForkChoiceNode` cùng `root` nhưng khác `payload_status`. Một node
> *pending* có con là node *empty* (luôn có) và node *full* (chỉ khi payload của
> block đã được xác minh qua `is_payload_verified`). Ngược lại, con của một node
> *empty*/*full* là các node *pending* của những block con có `parent_root` trỏ
> tới block này và xây dựng trên đúng trạng thái payload đó của parent.

```python
def get_node_children(store: Store, node: ForkChoiceNode) -> Sequence[ForkChoiceNode]:
    if node.payload_status == PAYLOAD_STATUS_PENDING:
        children = [ForkChoiceNode(root=node.root, payload_status=PAYLOAD_STATUS_EMPTY)]
        if is_payload_verified(store, node.root):
            children.append(ForkChoiceNode(root=node.root, payload_status=PAYLOAD_STATUS_FULL))
        return children
    else:
        return [
            ForkChoiceNode(root=root, payload_status=PAYLOAD_STATUS_PENDING)
            for root in store.blocks
            if (
                store.blocks[root].parent_root == node.root
                and node.payload_status == get_parent_payload_status(store, store.blocks[root])
            )
        ]
```

### Modified `get_head`

*Ghi chú*: Được sửa đổi để dùng `get_payload_status_tiebreaker` nhằm phân xử
khi hai node *full* và *empty* hòa nhau (bằng weight và cùng root), đồng thời có
một cơ chế bảo vệ để đảm bảo không bao giờ trả về node *pending*.

```python
def get_head(store: Store) -> ForkChoiceNode:
    # Lấy cây node đã lọc, chỉ gồm các nhánh còn khả thi (viable)
    nodes = get_filtered_node_tree(store)

    # [New in Gloas:EIP7732]
    # Trả về node empty nếu không có node khả thi nào
    if not any(nodes):
        return ForkChoiceNode(
            root=store.justified_checkpoint.root,
            payload_status=PAYLOAD_STATUS_EMPTY,
        )

    # Execute the LMD-GHOST fork-choice
    head = ForkChoiceNode(
        root=store.justified_checkpoint.root,
        # [New in Gloas:EIP7732]
        payload_status=PAYLOAD_STATUS_PENDING,
    )

    while True:
        children = [child for child in get_node_children(store, head) if child in nodes]
        if len(children) == 0:
            return head
        # Chọn theo attesting balance mới nhất; hòa thì phân xử theo thứ tự từ điển
        head = max(
            children,
            key=lambda child: (
                get_weight(store, child),
                child.root,
                # [New in Gloas:EIP7732]
                get_payload_status_tiebreaker(store, child),
            ),
        )
```

### Modified `get_latest_message_epoch`

```python
def get_latest_message_epoch(latest_message: LatestMessage) -> Epoch:
    return compute_epoch_at_slot(latest_message.slot)
```

### New `verify_execution_payload_envelope`

```python
def verify_execution_payload_envelope(
    state: BeaconState,
    signed_envelope: SignedExecutionPayloadEnvelope,
    execution_engine: ExecutionEngine,
) -> None:
    envelope = signed_envelope.message
    payload = envelope.payload

    # Verify signature
    assert verify_execution_payload_envelope_signature(state, signed_envelope)

    # Kiểm tra tính nhất quán với beacon block
    header = state.latest_block_header.copy()
    header.state_root = hash_tree_root(state)
    assert envelope.beacon_block_root == hash_tree_root(header)
    assert envelope.parent_beacon_block_root == state.latest_block_header.parent_root

    # Kiểm tra tính nhất quán với bid đã được cam kết (committed bid)
    bid = state.latest_execution_payload_bid
    assert envelope.builder_index == bid.builder_index
    assert payload.prev_randao == bid.prev_randao
    assert payload.gas_limit == bid.gas_limit
    assert payload.block_hash == bid.block_hash
    assert hash_tree_root(envelope.execution_requests) == bid.execution_requests_root

    # Kiểm tra execution payload hợp lệ
    assert payload.slot_number == state.slot
    assert payload.parent_hash == state.latest_block_hash
    assert payload.timestamp == compute_time_at_slot(state.genesis_time, state.slot)
    assert hash_tree_root(payload.withdrawals) == hash_tree_root(state.payload_expected_withdrawals)

    # Tính các versioned hash
    versioned_hashes = VersionedHashes()
    for commitment in bid.blob_kzg_commitments:
        versioned_hashes.append(kzg_commitment_to_versioned_hash(commitment))

    assert execution_engine.verify_and_notify_new_payload(
        NewPayloadRequest(
            execution_payload=payload,
            versioned_hashes=versioned_hashes,
            parent_beacon_block_root=envelope.parent_beacon_block_root,
            execution_requests=envelope.execution_requests,
        )
    )
```

### New `is_valid_dependent_root`

> 💡 Ghi chú: Hàm này kiểm tra xem block có `root` cho trước có thể là "dependent
> block" (block quyết định, ví dụ, shuffling/proposer) cho `dependent_slot` hay
> không: hoặc nó chính là head hiện tại, hoặc nó đã có một block con nằm ở slot
> sau `dependent_slot` (nên trên nhánh đó, nó là block mới nhất tại hoặc trước
> `dependent_slot`).

```python
def is_valid_dependent_root(store: Store, root: Root, dependent_slot: Slot) -> bool:
    """
    Check if the block with the given ``root`` is a possible dependent block
    for the given ``dependent_slot``, meaning that on some branch it is, or
    could become, the latest block at or before ``dependent_slot``.
    """
    if root == get_head(store).root:
        return True
    for block in store.blocks.values():
        if block.parent_root == root:
            if block.slot > dependent_slot:
                return True
    return False
```

### Modified `get_attestation_due_ms`

```python
def get_attestation_due_ms() -> Uint64:
    # [Modified in Gloas]
    return get_slot_component_duration_ms(ATTESTATION_DUE_BPS_GLOAS)
```

### Modified `get_aggregate_due_ms`

```python
def get_aggregate_due_ms() -> Uint64:
    # [Modified in Gloas]
    return get_slot_component_duration_ms(AGGREGATE_DUE_BPS_GLOAS)
```

### Modified `get_sync_message_due_ms`

```python
def get_sync_message_due_ms() -> Uint64:
    # [Modified in Gloas]
    return get_slot_component_duration_ms(SYNC_MESSAGE_DUE_BPS_GLOAS)
```

### Modified `get_contribution_due_ms`

```python
def get_contribution_due_ms() -> Uint64:
    # [Modified in Gloas]
    return get_slot_component_duration_ms(CONTRIBUTION_DUE_BPS_GLOAS)
```

### New `get_payload_due_ms`

```python
def get_payload_due_ms() -> Uint64:
    return get_slot_component_duration_ms(PAYLOAD_DUE_BPS)
```

### New `get_payload_attestation_due_ms`

```python
def get_payload_attestation_due_ms() -> Uint64:
    return get_slot_component_duration_ms(PAYLOAD_ATTESTATION_DUE_BPS)
```

### Proposer head and reorg helpers

#### Modified `is_head_late`

*Ghi chú*: Thay đổi duy nhất là `store.block_timeliness[root]` giờ ghi nhận
tính đúng hạn (timeliness) theo hai deadline khác nhau (deadline attestation và
deadline của PTC). `is_head_late` chỉ xét timeliness theo deadline attestation,
giá trị này được lấy tại chỉ số `ATTESTATION_TIMELINESS_INDEX`.

```python
def is_head_late(store: Store, head_root: Root) -> bool:
    return not store.block_timeliness[head_root][ATTESTATION_TIMELINESS_INDEX]
```

#### Modified `is_head_weak`

```python
def is_head_weak(store: Store, head_root: Root) -> bool:
    # Tính ngưỡng weight để xác định head "yếu"
    justified_state = store.checkpoint_states[store.justified_checkpoint]
    reorg_threshold = calculate_committee_fraction(justified_state, REORG_HEAD_WEIGHT_THRESHOLD)

    # Tính weight của head, bao gồm cả các validator equivocate
    head_state = store.block_states[head_root]
    head_block = store.blocks[head_root]
    epoch = compute_epoch_at_slot(head_block.slot)
    # [Modified in Gloas:EIP7732]
    head_node = ForkChoiceNode(root=head_root, payload_status=PAYLOAD_STATUS_PENDING)
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

#### Modified `is_parent_strong`

*Ghi chú*: Hàm này được sửa đổi để đo mức ủng hộ dành cho root của parent beacon
block bất kể payload status của nó (dùng node *pending*, tức gộp cả nhánh full
và empty).

```python
def is_parent_strong(store: Store, root: Root) -> bool:
    justified_state = store.checkpoint_states[store.justified_checkpoint]
    parent_threshold = calculate_committee_fraction(justified_state, REORG_PARENT_WEIGHT_THRESHOLD)
    parent_root = store.blocks[root].parent_root
    # [Modified in Gloas:EIP7732]
    parent_node = ForkChoiceNode(root=parent_root, payload_status=PAYLOAD_STATUS_PENDING)
    parent_weight = get_attestation_score(store, parent_node, justified_state)
    return parent_weight > parent_threshold
```

#### Modified `get_proposer_head`

*Ghi chú*: Hàm này được sửa đổi để giữ nguyên payload status của node parent
khi proposer quyết định re-org (bỏ qua head hiện tại và xây block trên parent).

```python
def get_proposer_head(store: Store, head_node: ForkChoiceNode, slot: Slot) -> ForkChoiceNode:
    head_block = store.blocks[head_node.root]
    parent_root = head_block.parent_root
    parent_block = store.blocks[parent_root]
    # [Modified in Gloas:EIP7732]
    parent_payload_status = get_parent_payload_status(store, head_block)
    parent_node = ForkChoiceNode(root=parent_root, payload_status=parent_payload_status)

    # Chỉ re-org head block nếu nó đến muộn hơn deadline attestation.
    head_late = is_head_late(store, head_node.root)

    # Đảm bảo thông tin FFG của head mới vẫn cạnh tranh được với head hiện tại.
    ffg_competitive = is_ffg_competitive(store, head_node.root, parent_root)

    # Không re-org nếu chain không finalize với tần suất chấp nhận được.
    finalization_ok = is_finalization_ok(store, slot)

    # Chỉ re-org nếu chúng ta đang propose đúng thời điểm.
    proposing_on_time = is_proposing_on_time(store)

    # Chỉ re-org tối đa một slot.
    parent_slot_ok = parent_block.slot + 1 == head_block.slot
    current_time_ok = head_block.slot + 1 == slot
    single_slot_reorg = parent_slot_ok and current_time_ok

    # Kiểm tra head có đủ ít phiếu để proposer boost của ta có thể áp đảo.
    assert store.proposer_boost_root != head_node.root  # đảm bảo boost đã hết hiệu lực
    head_weak = is_head_weak(store, head_node.root)

    # Kiểm tra các phiếu còn thiếu được dồn cho parent chứ không bị giữ lại (hoarded).
    parent_strong = is_parent_strong(store, head_node.root)

    # Re-org mạnh tay hơn nếu có proposer equivocation ở slot trước.
    proposer_equivocation = is_proposer_equivocation(store, head_node.root)

    if all([
        head_late,
        ffg_competitive,
        finalization_ok,
        proposing_on_time,
        single_slot_reorg,
        head_weak,
        parent_strong,
    ]):
        # Có thể re-org head hiện tại bằng cách xây block trên node parent của nó.
        return parent_node
    elif all([head_weak, current_time_ok, proposer_equivocation]):
        return parent_node
    else:
        return head_node
```

### `on_attestation` helpers

#### Modified `validate_on_attestation`

```python
def validate_on_attestation(store: Store, attestation: Attestation, is_from_block: bool) -> None:
    target = attestation.data.target

    # Nếu attestation không đến từ một beacon block,
    # phải kiểm tra phạm vi target epoch.
    if not is_from_block:
        validate_target_epoch_against_current_time(store, attestation)

    # Kiểm tra epoch và slot khớp nhau.
    assert target.epoch == compute_epoch_at_slot(attestation.data.slot)

    # Target của attestation phải là block đã biết. Nếu chưa biết target block,
    # hoãn xử lý cho tới khi tìm thấy block.
    assert target.root in store.blocks

    # Attestation phải trỏ tới block đã biết. Nếu chưa biết block,
    # hoãn xử lý cho tới khi tìm thấy block.
    assert attestation.data.beacon_block_root in store.blocks
    # Attestation không được trỏ tới block ở tương lai.
    # Nếu vi phạm, attestation không được xét tới.
    block_slot = store.blocks[attestation.data.beacon_block_root].slot
    assert block_slot <= attestation.data.slot

    # [New in Gloas:EIP7732]
    assert attestation.data.index in [0, 1]
    if block_slot == attestation.data.slot:
        assert attestation.data.index == 0
    # [New in Gloas:EIP7732]
    # Nếu attest cho node full thì payload phải đã được biết (đã xác minh)
    if attestation.data.index == 1:
        assert is_payload_verified(store, attestation.data.beacon_block_root)

    # Phiếu LMD phải nhất quán với target của phiếu FFG
    assert target.root == get_checkpoint_block(
        store, attestation.data.beacon_block_root, target.epoch
    )

    # Attestation chỉ ảnh hưởng tới fork choice của các slot sau đó.
    # Hoãn xét trong fork choice cho tới khi slot của nó đã trôi qua.
    assert get_current_slot(store) >= attestation.data.slot + 1
```

#### Modified `update_latest_messages`

*Ghi chú*: Hàm `update_latest_messages` được cập nhật để dùng slot của
attestation thay vì target. Lưu ý rằng hàm này chỉ được gọi với các attestation
đã được kiểm tra hợp lệ, và validator không thể attest hai lần trong cùng một
epoch mà không bị coi là equivocate. Cũng lưu ý rằng target epoch và slot đã được
kiểm tra trong `validate_on_attestation`.

> 💡 Ghi chú: Ngoài ra, `LatestMessage` giờ lưu thêm `payload_present`, lấy từ
> `attestation.data.index` (`1` nghĩa là validator vote rằng payload có mặt, tức
> ủng hộ node full; `0` nghĩa là node empty hoặc vote cho block cùng slot).

```python
def update_latest_messages(
    store: Store, attesting_indices: Sequence[ValidatorIndex], attestation: Attestation
) -> None:
    slot = attestation.data.slot
    beacon_block_root = attestation.data.beacon_block_root
    payload_present = attestation.data.index == 1
    non_equivocating_attesting_indices = [
        index for index in attesting_indices if index not in store.equivocating_indices
    ]
    for i in non_equivocating_attesting_indices:
        if i not in store.latest_messages or slot > store.latest_messages[i].slot:
            # [Modified in Gloas:EIP7732]
            store.latest_messages[i] = LatestMessage(
                slot=slot,
                root=beacon_block_root,
                payload_present=payload_present,
            )
```

### `on_block` helpers

#### Modified `record_block_timeliness`

```python
def record_block_timeliness(store: Store, root: Root) -> None:
    block = store.blocks[root]
    time_into_slot_ms = get_time_into_slot_ms(store)
    attestation_threshold_ms = get_attestation_due_ms()
    # [New in Gloas:EIP7732]
    is_current_slot = get_current_slot(store) == block.slot
    ptc_threshold_ms = get_payload_attestation_due_ms()
    # [Modified in Gloas:EIP7732]
    store.block_timeliness[root] = [
        is_current_slot and time_into_slot_ms < threshold
        for threshold in [attestation_threshold_ms, ptc_threshold_ms]
    ]
```

#### Modified `get_shuffling_dependent_root`

```python
def get_shuffling_dependent_root(store: Store, root: Root, epoch: Epoch) -> Root:
    # [Modified in Gloas:EIP7732]
    node = ForkChoiceNode(
        root=root,
        payload_status=PAYLOAD_STATUS_PENDING,
    )
    dependent_slot = compute_shuffling_dependent_slot(epoch)
    return get_ancestor(store, node, dependent_slot).root
```

#### Modified `update_proposer_boost_root`

```python
def update_proposer_boost_root(store: Store, head: Root, root: Root) -> None:
    is_first_block = store.proposer_boost_root == Root()
    # [Modified in Gloas:EIP7732]
    is_timely = store.block_timeliness[root][ATTESTATION_TIMELINESS_INDEX]
    epoch = get_current_store_epoch(store)
    head_dependent_root = get_shuffling_dependent_root(store, head, epoch)
    block_dependent_root = get_shuffling_dependent_root(store, root, epoch)
    is_same_dependent_root = head_dependent_root == block_dependent_root

    # Thêm proposer score boost nếu block đến đúng hạn, không xung đột với block
    # đã có, và có cùng dependent root với head của canonical chain.
    if is_timely and is_first_block and is_same_dependent_root:
        store.proposer_boost_root = root
```

## Handlers

### Modified `on_block`

*Ghi chú*: Handler `on_block` được sửa đổi để assert rằng payload của parent đã
được xác minh (`is_payload_verified`) khi block xây dựng trên một parent full.
Ngoài ra, việc kiểm tra data availability của blob được hoãn lại tới lúc xử lý
execution payload (trong `on_execution_payload_envelope`), vì trong Gloas beacon
block không còn chứa payload.

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

    # Nếu block này xây trên payload full của parent, payload đó phải
    # đã được xác minh bởi on_execution_payload_envelope
    if is_parent_node_full(store, block):
        assert is_payload_verified(store, block.parent_root)

    # Block không được ở tương lai. Nếu có, phải hoãn xét cho tới khi nó thuộc về quá khứ.
    current_slot = get_current_slot(store)
    assert current_slot >= block.slot

    # Kiểm tra block ở sau slot của finalized epoch (tối ưu để giảm số lần gọi get_ancestor)
    finalized_slot = compute_start_slot_at_epoch(store.finalized_checkpoint.epoch)
    assert block.slot > finalized_slot
    # Kiểm tra block là hậu duệ của finalized block tại slot của finalized checkpoint
    finalized_checkpoint_block = get_checkpoint_block(
        store,
        block.parent_root,
        store.finalized_checkpoint.epoch,
    )
    assert store.finalized_checkpoint.root == finalized_checkpoint_block

    # Tạo bản sao state để tránh vấn đề thay đổi dữ liệu dùng chung
    state = store.block_states[block.parent_root].copy()

    # Kiểm tra block hợp lệ và tính post-state
    state_transition(state, signed_block, validate_result=True)

    # Tính head trước khi áp dụng block
    head = get_head(store)
    # Thêm block mới vào store
    store.blocks[block_root] = block
    # Thêm state mới của block này vào store
    store.block_states[block_root] = state
    # Thêm bảng phiếu PTC mới cho block này vào store
    store.payload_timeliness_vote[block_root] = [None] * PTC_SIZE
    store.payload_data_availability_vote[block_root] = [None] * PTC_SIZE

    # Thông báo cho store về các payload_attestations trong block
    notify_ptc_messages(store, state, block.body.payload_attestations)

    record_block_timeliness(store, block_root)
    update_proposer_boost_root(store, head.root, block_root)

    # Cập nhật checkpoint trong store nếu cần
    update_checkpoints(store, state.current_justified_checkpoint, state.finalized_checkpoint)

    # Tính trước (eager) unrealized justification và finality.
    compute_pulled_up_tip(store, block_root)
```

### New `on_execution_payload_envelope`

Handler `on_execution_payload_envelope` được gọi khi node nhận được một
`SignedExecutionPayloadEnvelope` để sync.

> 💡 Ghi chú: Trong Gloas, execution payload được builder công bố tách rời khỏi
> beacon block, trong một envelope riêng. Chỉ sau khi envelope được xác minh và
> lưu vào `store.payloads`, block tương ứng mới có thể có node *full* trong cây
> fork choice.

```python
def on_execution_payload_envelope(
    store: Store, signed_envelope: SignedExecutionPayloadEnvelope
) -> None:
    """
    Run ``on_execution_payload_envelope`` upon receiving a new execution payload envelope.
    """
    envelope = signed_envelope.message
    # Beacon block root tương ứng phải đã được biết
    assert envelope.beacon_block_root in store.block_states

    # Kiểm tra blob data đã sẵn có (available) chưa
    # Nếu chưa, payload này MAY được đưa vào hàng đợi và xét lại khi blob data sẵn có
    assert is_data_available(envelope.beacon_block_root)

    state = store.block_states[envelope.beacon_block_root]

    # Xác minh execution payload envelope
    verify_execution_payload_envelope(state, signed_envelope, EXECUTION_ENGINE)

    # Thêm execution payload envelope vào store
    store.payloads[envelope.beacon_block_root] = envelope
```

### New `on_payload_attestation_message`

```python
def on_payload_attestation_message(
    store: Store, ptc_message: PayloadAttestationMessage, is_from_block: bool = False
) -> None:
    """
    Run ``on_payload_attestation_message`` upon receiving a new payload attestation message
    from either within a block or directly on the wire.
    """
    data = ptc_message.data

    # PTC attestation phải trỏ tới block đã biết. Nếu chưa biết block, hoãn xét cho tới khi tìm thấy block
    assert data.beacon_block_root in store.block_states
    state = store.block_states[data.beacon_block_root]

    # Phiếu PTC chỉ thay đổi vote cho beacon block được giao cho nó; nếu không thì trả về sớm
    if data.slot != state.slot:
        return

    # Lấy mọi vị trí của attester trong PTC
    ptc_indices = []
    ptc = get_ptc(state, data.slot)
    for ptc_index, validator_index in enumerate(ptc):
        if validator_index == ptc_message.validator_index:
            ptc_indices.append(ptc_index)

    # Kiểm tra attester thuộc PTC
    assert len(ptc_indices) > 0

    # Nếu message đến trực tiếp từ mạng (wire): xác minh signature và kiểm tra nó thuộc slot hiện tại
    if not is_from_block:
        # Kiểm tra attestation thuộc slot hiện tại
        assert data.slot == get_current_slot(store)
        # Xác minh signature
        assert is_valid_indexed_payload_attestation(
            state,
            IndexedPayloadAttestation(
                attesting_indices=PayloadTimelinessCommitteeIndices(
                    data=[ptc_message.validator_index]
                ),
                data=data,
                signature=ptc_message.signature,
            ),
        )

    # Cập nhật các phiếu cho block
    payload_timeliness_vote = store.payload_timeliness_vote[data.beacon_block_root]
    payload_data_availability_vote = store.payload_data_availability_vote[data.beacon_block_root]
    for ptc_index in ptc_indices:
        payload_timeliness_vote[ptc_index] = data.payload_present
        payload_data_availability_vote[ptc_index] = data.blob_data_available
```
