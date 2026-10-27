# Phase 0 -- Fast Confirmation

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Fast Confirmation Rule](#fast-confirmation-rule)
  - [Constants](#constants)
  - [Configs](#configs)
  - [Helpers](#helpers)
    - [`FastConfirmationStore`](#fastconfirmationstore)
    - [`get_fast_confirmation_store`](#get_fast_confirmation_store)
    - [Misc helper functions](#misc-helper-functions)
      - [`get_node_for_root`](#get_node_for_root)
      - [`get_block_slot`](#get_block_slot)
      - [`get_block_epoch`](#get_block_epoch)
      - [`get_checkpoint_for_block`](#get_checkpoint_for_block)
      - [`get_current_target`](#get_current_target)
      - [`is_start_slot_at_epoch`](#is_start_slot_at_epoch)
      - [`get_ancestor_roots`](#get_ancestor_roots)
    - [State helpers](#state-helpers)
      - [`get_slot_committee`](#get_slot_committee)
      - [`get_pulled_up_head_state`](#get_pulled_up_head_state)
      - [`get_previous_balance_source`](#get_previous_balance_source)
      - [`get_current_balance_source`](#get_current_balance_source)
    - [LMD-GHOST helpers](#lmd-ghost-helpers)
      - [`get_node_support_between_slots`](#get_node_support_between_slots)
      - [`is_full_validator_set_covered`](#is_full_validator_set_covered)
      - [`adjust_committee_weight_estimate_to_ensure_safety`](#adjust_committee_weight_estimate_to_ensure_safety)
      - [`estimate_committee_weight_between_slots`](#estimate_committee_weight_between_slots)
      - [`get_equivocation_score`](#get_equivocation_score)
      - [`compute_adversarial_weight`](#compute_adversarial_weight)
      - [`get_adversarial_weight`](#get_adversarial_weight)
      - [`compute_empty_slot_support_discount`](#compute_empty_slot_support_discount)
      - [`get_support_discount`](#get_support_discount)
      - [`compute_safety_threshold`](#compute_safety_threshold)
      - [`is_one_confirmed`](#is_one_confirmed)
      - [`is_confirmed_chain_safe`](#is_confirmed_chain_safe)
    - [FFG helpers](#ffg-helpers)
      - [`get_current_target_score`](#get_current_target_score)
      - [`compute_honest_ffg_support_for_current_target`](#compute_honest_ffg_support_for_current_target)
      - [`will_no_conflicting_checkpoint_be_justified`](#will_no_conflicting_checkpoint_be_justified)
      - [`will_current_target_be_justified`](#will_current_target_be_justified)
    - [`update_fast_confirmation_variables`](#update_fast_confirmation_variables)
    - [`find_latest_confirmed_descendant`](#find_latest_confirmed_descendant)
    - [`get_latest_confirmed`](#get_latest_confirmed)
    - [`get_restart_resilient_confirmed_root`](#get_restart_resilient_confirmed_root)
  - [Handlers](#handlers)
    - [`on_fast_confirmation`](#on_fast_confirmation)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này đặc tả một quy tắc xác nhận block nhanh (fast block confirmation
rule, còn gọi tắt là FCR) cho giao thức Ethereum.

Bài báo nghiên cứu về quy tắc này có thể xem
[tại đây](https://arxiv.org/abs/2405.00549).

Một bản giải thích ngắn gọn hơn có thể xem
[tại đây](https://www.overleaf.com/read/cvfzznvcwffh#057762).

Quy tắc này dựa trên giả định về tính đồng bộ (synchrony) của mạng như sau: kể từ
slot hiện tại trở đi, các attestation do validator trung thực tạo ra trong bất kỳ
slot nào đều được nhận trước khi slot đó kết thúc. Do đó, quy tắc này chỉ cung
cấp xác nhận có ý nghĩa cho những người dùng chấp nhận giả định trên. Nếu giả
định này bị vi phạm, các block đã được xác nhận vẫn có thể bị reorg (tổ chức lại
chuỗi) mà không cần bất kỳ hành vi tấn công nào và không có ai bị slashing.

> 💡 Ghi chú: Khác với finality của Casper FFG (thường mất khoảng 2 epoch), FCR
> cho phép một node kết luận sớm hơn nhiều — thường trong vòng một slot — rằng
> một block sẽ luôn nằm trên chuỗi canonical, với điều kiện mạng đồng bộ và tỷ lệ
> validator Byzantine không vượt quá `CONFIRMATION_BYZANTINE_THRESHOLD`. Đây là
> bảo đảm yếu hơn finality nhưng đến nhanh hơn.

## Fast Confirmation Rule

### Constants

| Name                                            | Value       | Description |
| ----------------------------------------------- | ----------- | ----------- |
| `COMMITTEE_WEIGHT_ESTIMATION_ADJUSTMENT_FACTOR` | `Uint64(5)` | Giá trị tính theo phần nghìn (per mille) được cộng thêm vào ước lượng trọng số committee trên một dải slot không bao trọn một epoch nào, nhằm bảo đảm tính an toàn của quy tắc xác nhận với xác suất cao. Xem [tại đây](https://gist.github.com/saltiniroberto/9ee53d29c33878d79417abb2b4468c20) để biết giải thích về giá trị được chọn. |

### Configs

| Name                               | Value        | Max. Value   | Description |
| ---------------------------------- | ------------ | ------------ | ----------- |
| `CONFIRMATION_BYZANTINE_THRESHOLD` | `Uint64(25)` | `Uint64(25)` | Tỷ lệ phần trăm tối đa (theo giả định) của validator Byzantine (có hành vi tùy ý/độc hại) trong tập validator |

### Helpers

#### `FastConfirmationStore`

`FastConfirmationStore` chịu trách nhiệm lưu giữ các thông tin cần thiết cho
quy tắc xác nhận nhanh. Các trường được theo dõi được mô tả dưới đây:

- `store`: instance chỉ-đọc của `Store` dùng cho fork choice, được thêm vào cho
  tiện truy cập.
- `confirmed_root`: root của block được xác nhận gần đây nhất.
- `previous_epoch_observed_justified_checkpoint`: một checkpoint justified mà tất
  cả các node trung thực đều đã quan sát thấy vào đầu epoch trước, với giả định
  mạng đồng bộ.
- `current_epoch_observed_justified_checkpoint`: một checkpoint justified mà tất
  cả các node trung thực đều đã quan sát thấy vào đầu epoch hiện tại, với giả
  định mạng đồng bộ.
- `previous_epoch_greatest_unrealized_checkpoint`: checkpoint justified chưa hiện
  thực hóa (unrealized justified) lớn nhất tại thời điểm bắt đầu slot cuối cùng
  của epoch trước, theo góc nhìn cục bộ của node.
- `previous_slot_head`: head tại thời điểm bắt đầu slot trước.
- `current_slot_head`: head tại thời điểm bắt đầu slot hiện tại.

> 💡 Ghi chú: "Unrealized justification" là justification sẽ đạt được nếu xử lý
> epoch (epoch processing) được chạy ngay bây giờ trên các attestation đã có
> trong block, thay vì phải đợi đến ranh giới epoch.

```python
@dataclass
class FastConfirmationStore:
    store: Store
    confirmed_root: Root
    previous_epoch_observed_justified_checkpoint: Checkpoint
    current_epoch_observed_justified_checkpoint: Checkpoint
    previous_epoch_greatest_unrealized_checkpoint: Checkpoint
    previous_slot_head: Root
    current_slot_head: Root
```

#### `get_fast_confirmation_store`

Việc khởi tạo fast confirmation store nên diễn ra cùng lúc với việc khởi tạo
fork choice store và sử dụng cùng một checkpoint tin cậy (trusted checkpoint).

*Note*: Hàm này dùng `store.finalized_checkpoint` một cách thận trọng cho tất cả
các biến của fast confirmation. Block được xác nhận sẽ được đẩy lên tại một ranh
giới epoch nào đó trong tương lai khi các điều kiện khởi đầu được thỏa mãn; trước
thời điểm đó, block finalized sẽ được trả về làm block được xác nhận.

```python
def get_fast_confirmation_store(store: Store) -> FastConfirmationStore:
    return FastConfirmationStore(
        store=store,
        confirmed_root=store.finalized_checkpoint.root,
        previous_epoch_observed_justified_checkpoint=store.finalized_checkpoint,
        current_epoch_observed_justified_checkpoint=store.finalized_checkpoint,
        previous_epoch_greatest_unrealized_checkpoint=store.finalized_checkpoint,
        previous_slot_head=store.finalized_checkpoint.root,
        current_slot_head=store.finalized_checkpoint.root,
    )
```

#### Misc helper functions

##### `get_node_for_root`

```python
def get_node_for_root(block_root: Root) -> ForkChoiceNode:
    return ForkChoiceNode(root=block_root)
```

##### `get_block_slot`

```python
def get_block_slot(store: Store, block_root: Root) -> Slot:
    """
    Return a slot of the block.
    """
    return store.blocks[block_root].slot
```

##### `get_block_epoch`

```python
def get_block_epoch(store: Store, block_root: Root) -> Epoch:
    """
    Return an epoch of the block.
    """
    return compute_epoch_at_slot(store.blocks[block_root].slot)
```

##### `get_checkpoint_for_block`

```python
def get_checkpoint_for_block(store: Store, block_root: Root, epoch: Epoch) -> Checkpoint:
    """
    Return a checkpoint in the chain of the block at the ``epoch``.
    """
    return Checkpoint(epoch=epoch, root=get_checkpoint_block(store, block_root, epoch))
```

##### `get_current_target`

```python
def get_current_target(store: Store) -> Checkpoint:
    """
    Return current epoch target.
    """
    head = get_head(store).root
    current_epoch = get_current_store_epoch(store)
    return get_checkpoint_for_block(store, head, current_epoch)
```

##### `is_start_slot_at_epoch`

```python
def is_start_slot_at_epoch(slot: Slot) -> bool:
    """
    Return ``True`` if ``slot`` is the start slot of an epoch.
    """
    return compute_slots_since_epoch_start(slot) == 0
```

##### `get_ancestor_roots`

```python
def get_ancestor_roots(store: Store, block_root: Root, terminal_root: Root) -> Sequence[Root]:
    """
    Return a list of ancestors of ``block_root`` inclusive until ``terminal_root`` exclusive.
    """
    root = block_root
    ancestor_roots: list[Root] = []
    while store.blocks[root].slot > store.blocks[terminal_root].slot:
        ancestor_roots.insert(0, root)
        root = store.blocks[root].parent_root

        # Return when terminal_root is reached
        if root == terminal_root:
            return ancestor_roots

    # Return empty list if terminal_root is not in the chain of block_root
    return []
```

#### State helpers

Phần này gom lại các thao tác đọc từ những beacon state khác nhau mà Fast
Confirmation Rule sử dụng.

Các implementation MAY ghi đè logic của từng hàm trong phần này, nhưng ngữ nghĩa
(semantics) MUST được giữ nguyên.

##### `get_slot_committee`

*Note*: Hàm này trả về committee của một slot cụ thể. Hàm MUST hỗ trợ các
committee của các epoch bắt đầu từ `current_epoch - 2` trở đi.

```python
def get_slot_committee(store: Store, slot: Slot) -> set[ValidatorIndex]:
    """
    Return participants of all committees in ``slot``.
    """
    head = get_head(store).root
    shuffling_source = store.block_states[head]
    committees_count = get_committee_count_per_slot(shuffling_source, compute_epoch_at_slot(slot))
    participants: set[ValidatorIndex] = set()
    for i in range(committees_count):
        participants.update(get_beacon_committee(shuffling_source, slot, CommitteeIndex(i)))
    return participants
```

##### `get_pulled_up_head_state`

```python
def get_pulled_up_head_state(store: Store) -> BeaconState:
    """
    Return the state of the head pulled up to the current epoch if needed.
    """
    head = get_head(store).root
    head_state = store.block_states[head]
    if get_current_epoch(head_state) < get_current_store_epoch(store):
        pulled_up_state = head_state.copy()
        process_slots(pulled_up_state, compute_start_slot_at_epoch(get_current_store_epoch(store)))
        return pulled_up_state
    else:
        return head_state
```

> 💡 Ghi chú: "Pulled up" nghĩa là state của head được xử lý tiếp (bằng
> `process_slots`) đến slot đầu tiên của epoch hiện tại nếu head nằm ở epoch cũ
> hơn, để các phép tính như tổng active balance phản ánh đúng epoch hiện tại.

##### `get_previous_balance_source`

*Note*: Tái xác nhận (reconfirmation) là nơi duy nhất sử dụng balance source của
epoch trước. Các implementation MAY chuyển sang balance source của epoch hiện tại
sau khi đã chạy reconfirmation và trước khi gọi đến logic xác nhận block mới.
Khi đó, implementation chỉ cần giữ lại một balance source duy nhất.

```python
def get_previous_balance_source(fcr_store: FastConfirmationStore) -> BeaconState:
    store = fcr_store.store
    return store.checkpoint_states[fcr_store.previous_epoch_observed_justified_checkpoint]
```

##### `get_current_balance_source`

```python
def get_current_balance_source(fcr_store: FastConfirmationStore) -> BeaconState:
    store = fcr_store.store
    return store.checkpoint_states[fcr_store.current_epoch_observed_justified_checkpoint]
```

#### LMD-GHOST helpers

##### `get_node_support_between_slots`

*Notes:*

Phiếu bầu của validator từ các slot trước `start_slot` và sau `end_slot` có thể
không phân biệt được với phiếu bầu mà chính validator đó gửi trong khoảng
`[start_slot, end_slot]`. Do việc shuffling committee gần ranh giới epoch, các
trường hợp sau có thể xảy ra:

1. Validator được phân công vào cả `start_slot - 1` và `end_slot` đã bỏ phiếu cho
   `node` ở `start_slot - 1` nhưng không bỏ phiếu ở `end_slot`.
2. Validator được phân công vào cả `start_slot` và `end_slot + 1` bỏ lỡ phiếu ở
   `start_slot`, nhưng bỏ phiếu cho `node` ở `end_slot + 1`.

Trong cả hai trường hợp, lượng support (ủng hộ) sẽ tính cả một phiếu nằm ngoài
khoảng `[start_slot, end_slot]`. Sự thiếu chính xác này chấp nhận được vì nó
không ảnh hưởng đến tính an toàn.

Do logic của thuật toán, khoảng cách tối đa giữa `balance_source` và
`start_slot` hoặc `end_slot` là hai epoch, nhỏ hơn `MAX_SEED_LOOKAHEAD`. Vì vậy,
thành viên các committee trong dải slot đó nhất quán với tập validator của
`balance_source`.

```python
def get_node_support_between_slots(
    store: Store,
    balance_source: BeaconState,
    node: ForkChoiceNode,
    start_slot: Slot,
    end_slot: Slot,
) -> Gwei:
    """
    Return support of the node by validators assigned to slots
    between ``start_slot`` and ``end_slot`` (inclusive of both).
    """
    participants: set[ValidatorIndex] = set()
    for slot in range(start_slot, end_slot + 1):
        participants.update(get_slot_committee(store, Slot(slot)))

    # Keep validators that were active at the balance_source epoch to be consistent
    # with get_total_active_balance() computation, also filter out slashed validators
    unslashed_and_active_indices = [
        index
        for index in participants
        if (
            not balance_source.validators[index].slashed
            and is_active_validator(
                balance_source.validators[index], get_current_epoch(balance_source)
            )
        )
    ]

    return Gwei(
        sum(
            balance_source.validators[index].effective_balance
            for index in unslashed_and_active_indices
            # Check that validator has voted in the support of the node
            # and has not been slashed
            if (
                index in store.latest_messages
                and get_supported_node(store, store.latest_messages[index]) == node
                and index not in store.equivocating_indices
            )
        )
    )
```

##### `is_full_validator_set_covered`

```python
def is_full_validator_set_covered(start_slot: Slot, end_slot: Slot) -> bool:
    """
    Return ``True`` if the range between ``start_slot`` and ``end_slot`` (inclusive of both) includes an entire epoch.
    """
    start_full_epoch = compute_epoch_at_slot(start_slot + SLOTS_PER_EPOCH - 1)
    end_full_epoch = compute_epoch_at_slot(end_slot + 1)
    return start_full_epoch < end_full_epoch
```

> 💡 Ghi chú: Nếu dải slot bao trọn ít nhất một epoch thì mọi validator active
> đều đã được phân công vào đúng một slot trong dải đó, nên tổng trọng số
> committee chính là toàn bộ active balance.

##### `adjust_committee_weight_estimate_to_ensure_safety`

*Note*: Hàm này điều chỉnh ước lượng trọng số committee cho một chuỗi slot vắt
qua ranh giới epoch nhưng không bao trọn epoch nào, nhằm bảo đảm tính an toàn
của FCR với xác suất cao. Chuỗi slot này có thể dài hơn SLOTS_PER_EPOCH. Xem
https://gist.github.com/saltiniroberto/9ee53d29c33878d79417abb2b4468c20 để biết
giải thích vì sao cần điều này.

```python
def adjust_committee_weight_estimate_to_ensure_safety(estimate: Gwei) -> Gwei:
    """
    Return adjusted ``estimate`` of the weight of a committee for a sequence of slots
    spanning an epoch boundary that does not cover any full epoch.
    """
    ceil = (estimate + 999) // 1000
    return ceil * (1000 + COMMITTEE_WEIGHT_ESTIMATION_ADJUSTMENT_FACTOR)
```

> 💡 Ghi chú: Nói cách khác, ước lượng được làm tròn lên theo đơn vị 1/1000 rồi
> nhân với `(1000 + COMMITTEE_WEIGHT_ESTIMATION_ADJUSTMENT_FACTOR)`, tức là tăng
> thêm khoảng 0,5% để bù cho sai số do việc phân bổ validator ngẫu nhiên giữa
> hai epoch.

##### `estimate_committee_weight_between_slots`

```python
def estimate_committee_weight_between_slots(
    total_active_balance: Gwei, start_slot: Slot, end_slot: Slot
) -> Gwei:
    """
    Return estimate of the total weight of committees
    between ``start_slot`` and ``end_slot`` (inclusive of both).
    """

    # Sanity check
    if start_slot > end_slot:
        return Gwei(0)

    # If an entire epoch is covered by the range, return the total active balance
    if is_full_validator_set_covered(start_slot, end_slot):
        return total_active_balance

    start_epoch = compute_epoch_at_slot(start_slot)
    end_epoch = compute_epoch_at_slot(end_slot)
    committee_weight = total_active_balance // Uint64(SLOTS_PER_EPOCH)
    if start_epoch == end_epoch:
        return committee_weight * Uint64(end_slot - start_slot + 1)
    else:
        # First, calculate the number of committees in the end epoch
        num_slots_in_end_epoch = Uint64(compute_slots_since_epoch_start(end_slot) + 1)
        # Next, calculate the number of slots remaining in the end epoch
        remaining_slots_in_end_epoch = Uint64(SLOTS_PER_EPOCH) - num_slots_in_end_epoch
        # Then, calculate the number of slots in the start epoch
        num_slots_in_start_epoch = Uint64(
            SLOTS_PER_EPOCH - compute_slots_since_epoch_start(start_slot)
        )

        start_epoch_weight = committee_weight * num_slots_in_start_epoch
        end_epoch_weight = committee_weight * num_slots_in_end_epoch

        # A range that spans an epoch boundary, but does not span any full epoch
        # needs pro-rata calculation, see https://gist.github.com/saltiniroberto/9ee53d29c33878d79417abb2b4468c20
        # start_epoch_weight_pro_rated = start_epoch_weight * (1 - num_slots_in_end_epoch / SLOTS_PER_EPOCH)
        start_epoch_weight_pro_rated = (
            start_epoch_weight // Uint64(SLOTS_PER_EPOCH) * remaining_slots_in_end_epoch
        )

        return adjust_committee_weight_estimate_to_ensure_safety(
            start_epoch_weight_pro_rated + end_epoch_weight
        )
```

> 💡 Ghi chú: Có ba trường hợp: (1) dải slot bao trọn một epoch → trả về toàn bộ
> active balance; (2) dải slot nằm trong cùng một epoch → mỗi slot đóng góp
> `total_active_balance / SLOTS_PER_EPOCH`; (3) dải slot vắt qua ranh giới epoch
> nhưng không bao trọn epoch nào → phần thuộc epoch đầu được tính theo tỷ lệ
> (pro-rata), vì một số validator của epoch đầu có thể cũng xuất hiện ở epoch
> sau, rồi kết quả được điều chỉnh tăng để bảo đảm an toàn.

##### `get_equivocation_score`

*Notes:*

Để đơn giản, hàm này không tìm trong `balance_source` các validator đã bị
slashing, vì nhiều khả năng các validator đó đã nằm sẵn trong
`store.equivocating_indices`.

Do logic của thuật toán, khoảng cách tối đa giữa `balance_source` và
`start_slot` hoặc `end_slot` là hai epoch, nhỏ hơn `MAX_SEED_LOOKAHEAD`. Vì vậy,
thành viên các committee trong dải slot đó nhất quán với tập validator của
`balance_source`.

```python
def get_equivocation_score(
    store: Store,
    balance_source: BeaconState,
    start_slot: Slot,
    end_slot: Slot,
) -> Gwei:
    """
    Return total weight of equivocating participants of all committees
    in the slots between ``start_slot`` and ``end_slot`` (inclusive of both).
    """
    committee_indices: set[ValidatorIndex] = set()
    for slot in range(start_slot, end_slot + 1):
        committee_indices.update(get_slot_committee(store, Slot(slot)))

    # Keep equivocating validators that were active at the balance_source epoch to be consistent
    # with get_total_active_balance() computation
    active_equivocating_indices = [
        index
        for index in committee_indices.intersection(store.equivocating_indices)
        if is_active_validator(balance_source.validators[index], get_current_epoch(balance_source))
    ]

    return Gwei(
        sum(
            balance_source.validators[index].effective_balance
            for index in active_equivocating_indices
        )
    )
```

##### `compute_adversarial_weight`

*Note*: Hàm này tính trọng số tối đa có thể thuộc về đối thủ (adversarial) trong
các committee của dải slot, với giả định ngưỡng `CONFIRMATION_BYZANTINE_THRESHOLD`
và trừ đi các validator đã equivocate (bỏ phiếu mâu thuẫn).

```python
def compute_adversarial_weight(
    store: Store,
    balance_source: BeaconState,
    start_slot: Slot,
    end_slot: Slot,
) -> Gwei:
    """
    Return maximum possible adversarial weight in the committees of the slots
    between ``start_slot`` and ``end_slot`` (inclusive of both).
    """
    total_active_balance = get_total_active_balance(balance_source)
    maximum_weight = estimate_committee_weight_between_slots(
        total_active_balance, start_slot, end_slot
    )
    max_adversarial_weight = maximum_weight // 100 * CONFIRMATION_BYZANTINE_THRESHOLD

    # Discount total weight of equivocating validators
    equivocation_score = get_equivocation_score(store, balance_source, start_slot, end_slot)
    if max_adversarial_weight > equivocation_score:
        return max_adversarial_weight - equivocation_score
    else:
        return Gwei(0)
```

> 💡 Ghi chú: Validator đã equivocate bị fork choice loại khỏi việc tính trọng
> số, nên đối thủ không thể dùng chúng thêm nữa; vì vậy phần trọng số này được
> trừ khỏi ngân sách tối đa của đối thủ.

##### `get_adversarial_weight`

```python
def get_adversarial_weight(store: Store, balance_source: BeaconState, block_root: Root) -> Gwei:
    """
    Return maximum adversarial weight that can support the block.
    """
    current_slot = get_current_slot(store)
    block = store.blocks[block_root]
    if get_block_epoch(store, block_root) > get_block_epoch(store, block.parent_root):
        # Use the first epoch slot as the start slot when crossing epoch boundary
        start_slot = compute_start_slot_at_epoch(get_block_epoch(store, block_root))
        return compute_adversarial_weight(store, balance_source, start_slot, current_slot - 1)
    else:
        return compute_adversarial_weight(store, balance_source, block.slot, current_slot - 1)
```

##### `compute_empty_slot_support_discount`

*Note*: Hàm này MAY tính support của block cha và trọng số adversarial cho các
slot trống (empty slot) thuộc `current_epoch - 2`. Điều này chỉ có thể xảy ra
trong quá trình reconfirmation; trong mọi trường hợp khác, epoch sớm nhất có thể
là `current_epoch - 1`.

```python
def compute_empty_slot_support_discount(
    store: Store, balance_source: BeaconState, block_root: Root
) -> Gwei:
    """
    Return weight that can be discounted during the safety threshold computation
    if there are empty slots preceding the block.
    """
    block = store.blocks[block_root]
    parent_block = store.blocks[block.parent_root]
    # No empty slot
    if parent_block.slot + 1 == block.slot:
        return Gwei(0)

    # Discount votes supporting the parent block if they are from the committees of empty slots
    parent_node = get_ancestor(store, get_node_for_root(block_root), parent_block.slot)
    parent_support_in_empty_slots = get_node_support_between_slots(
        store,
        balance_source,
        parent_node,
        parent_block.slot + 1,
        block.slot - 1,
    )
    # Adversarial weight is not discounted
    adversarial_weight = compute_adversarial_weight(
        store, balance_source, parent_block.slot + 1, block.slot - 1
    )
    if parent_support_in_empty_slots > adversarial_weight:
        return parent_support_in_empty_slots - adversarial_weight
    else:
        return Gwei(0)
```

> 💡 Ghi chú: Nếu giữa block cha và block đang xét có các slot trống, thì phiếu
> của committee trong các slot trống đó đã dồn cho block cha (chứ không cho một
> nhánh cạnh tranh nào). Phần phiếu này — sau khi trừ đi phần có thể thuộc về đối
> thủ — có thể được trừ khỏi ngưỡng an toàn, giúp block dễ được xác nhận hơn.

##### `get_support_discount`

```python
def get_support_discount(store: Store, balance_source: BeaconState, block_root: Root) -> Gwei:
    """
    Return weight that can be discounted during the safety threshold computation for the block.
    """
    return compute_empty_slot_support_discount(store, balance_source, block_root)
```

##### `compute_safety_threshold`

```python
def compute_safety_threshold(store: Store, block_root: Root, balance_source: BeaconState) -> Gwei:
    """
    Compute the LMD-GHOST safety threshold for ``block_root``.
    """
    current_slot = get_current_slot(store)
    block = store.blocks[block_root]
    parent_block = store.blocks[block.parent_root]

    total_active_balance = get_total_active_balance(balance_source)
    proposer_score = compute_proposer_score(balance_source)
    maximum_support = estimate_committee_weight_between_slots(
        total_active_balance, parent_block.slot + 1, current_slot - 1
    )
    support_discount = get_support_discount(store, balance_source, block_root)
    adversarial_weight = get_adversarial_weight(store, balance_source, block_root)

    # Return (maximum_support + proposer_score - support_discount) // 2 + adversarial_weight
    # with an underflow guard
    if support_discount < maximum_support + proposer_score + 2 * adversarial_weight:
        return (maximum_support + proposer_score + 2 * adversarial_weight - support_discount) // 2
    else:
        return Gwei(0)
```

> 💡 Ghi chú: Ý tưởng là block được coi là an toàn nếu support thực tế của nó
> vượt quá một nửa tổng trọng số có thể bỏ phiếu (kể cả proposer boost), cộng
> thêm phần trọng số mà đối thủ có thể "rút lại" hoặc dồn cho nhánh khác.

##### `is_one_confirmed`

*Notes:*

Hàm này kiểm tra xem một block đơn lẻ có LMD-GHOST safe (an toàn theo LMD-GHOST)
hay không, bằng cách tính chỉ số an toàn LMD-GHOST và so sánh với ngưỡng an toàn.

Ở mức tổng quát, phép tính kiểm tra xem score thực tế của block có vượt trội so
với score tiềm năng của bất kỳ block nào xung đột với nó hay không, có xét đến
tổng trọng số của các committee và trọng số adversarial tối đa.

Nếu phép kiểm tra này đạt, block được coi là LMD-GHOST safe, nhưng như vậy chưa
đủ để khẳng định block sẽ tiếp tục là canonical. Để bảo đảm điều đó, mỗi tổ tiên
(ancestor) của block cũng phải vượt qua phép kiểm tra này.

Chi tiết hơn về phép kiểm tra này có trong
[bài báo](https://arxiv.org/abs/2405.00549).

Hàm này **MUST** trả về `False` nếu trạng thái của `block_root` **không** phải
`VALID` theo đặc tả [Optimistic sync](../bellatrix/optimistic-sync.md).

```python
def is_one_confirmed(store: Store, balance_source: BeaconState, block_root: Root) -> bool:
    """
    Return ``True`` if and only if the block is LMD-GHOST safe.
    """
    support = get_attestation_score(store, get_node_for_root(block_root), balance_source)
    safety_threshold = compute_safety_threshold(store, block_root, balance_source)
    return support > safety_threshold
```

##### `is_confirmed_chain_safe`

*Notes*:

Hàm này nên được gọi vào đầu mỗi epoch để bảo đảm rằng chuỗi đã xác nhận, bắt
đầu từ `fcr_store.current_epoch_observed_justified_checkpoint.root`, vẫn còn
LMD-GHOST safe.

Phép kiểm tra này nới lỏng giả định đồng bộ bằng cách cho phép GST (Global
Stabilization Time — thời điểm từ đó mạng được coi là đồng bộ) bắt đầu từ đầu
slot trước. Nếu không chạy phép kiểm tra này, ta sẽ phải giả định GST bắt đầu từ
lần chạy đầu tiên của thuật toán, có thể là từ nhiều epoch trước.

```python
def is_confirmed_chain_safe(fcr_store: FastConfirmationStore, confirmed_root: Root) -> bool:
    """
    Return ``True`` if and only if all blocks of the confirmed chain
    starting from current_epoch_observed_justified_checkpoint are LMD-GHOST safe.
    """
    store = fcr_store.store
    # Check if the confirmed_root has current_epoch_observed_justified_checkpoint in its chain
    if fcr_store.current_epoch_observed_justified_checkpoint != get_checkpoint_for_block(
        store, confirmed_root, fcr_store.current_epoch_observed_justified_checkpoint.epoch
    ):
        return False

    current_epoch = get_current_store_epoch(store)
    if fcr_store.current_epoch_observed_justified_checkpoint.epoch + 1 >= current_epoch:
        # Exclude the justified checkpoint block if it is from the previous epoch
        # as then this block will always be canonical in this case.
        start_root_exclusive = fcr_store.current_epoch_observed_justified_checkpoint.root
    else:
        # Limit reconfirmation to the first block of the previous epoch
        # as if it is successful, reconfirmation of the ancestors is implied.
        ancestor_at_previous_epoch_start = get_ancestor(
            store,
            get_node_for_root(confirmed_root),
            compute_start_slot_at_epoch(current_epoch - 1),
        ).root
        if get_block_epoch(store, ancestor_at_previous_epoch_start) + 1 == current_epoch:
            # The parent of the first block of the previous epoch
            start_root_exclusive = store.blocks[ancestor_at_previous_epoch_start].parent_root
        else:
            # The last block of the epoch before the previous one
            start_root_exclusive = ancestor_at_previous_epoch_start

    # Run is_one_confirmed for each block in the confirmed chain with the previous epoch balance source
    chain_roots = get_ancestor_roots(store, confirmed_root, start_root_exclusive)
    return all(
        is_one_confirmed(store, get_previous_balance_source(fcr_store), root)
        for root in chain_roots
    )
```

#### FFG helpers

##### `get_current_target_score`

*Note*: Hàm này dùng các phiếu LMD-GHOST để ước lượng support FFG cho target
của epoch hiện tại. Do cách thức tính toán, hàm MUST được dùng không muộn hơn
thời điểm kết thúc epoch hiện tại.

```python
def get_current_target_score(store: Store) -> Gwei:
    """
    Return the estimate of FFG support of the current epoch target by using LMD-GHOST votes.
    """
    target = get_current_target(store)
    state = get_pulled_up_head_state(store)
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
                and target
                == get_checkpoint_for_block(
                    store,
                    store.latest_messages[index].root,
                    get_latest_message_epoch(store.latest_messages[index]),
                )
            )
        )
    )
```

> 💡 Ghi chú: Mỗi attestation chứa cả phiếu LMD-GHOST (head) lẫn phiếu FFG
> (target). Với validator trung thực, target chính là checkpoint trên chuỗi của
> head mà nó bỏ phiếu, nên có thể suy ra phiếu FFG từ `store.latest_messages`.

##### `compute_honest_ffg_support_for_current_target`

*Note*: Hàm này tính support FFG trung thực cho target của epoch hiện tại, với
giả định `CONFIRMATION_BYZANTINE_THRESHOLD` và mạng đồng bộ, có tính đến các
phiếu ủng hộ target đã nhận được cho đến thời điểm này.

```python
def compute_honest_ffg_support_for_current_target(store: Store) -> Gwei:
    """
    Compute honest FFG support of the current epoch target.
    """
    current_slot = get_current_slot(store)
    current_epoch = compute_epoch_at_slot(current_slot)
    balance_source = get_pulled_up_head_state(store)
    total_active_balance = get_total_active_balance(balance_source)

    # Compute FFG support for the target
    ffg_support_for_checkpoint = get_current_target_score(store)

    # Compute the total FFG weight up to, but excluding, the current slot
    ffg_weight_till_now = estimate_committee_weight_between_slots(
        total_active_balance, compute_start_slot_at_epoch(current_epoch), current_slot - 1
    )

    # Compute remaining honest FFG weight
    remaining_ffg_weight = total_active_balance - ffg_weight_till_now
    remaining_honest_ffg_weight = (
        remaining_ffg_weight // 100 * (100 - CONFIRMATION_BYZANTINE_THRESHOLD)
    )

    # Compute potential adversarial weight
    adversarial_weight = compute_adversarial_weight(
        store, balance_source, compute_start_slot_at_epoch(current_epoch), current_slot - 1
    )

    # Compute min honest FFG support
    min_honest_ffg_support = saturating_sub(ffg_support_for_checkpoint, adversarial_weight)

    return min_honest_ffg_support + remaining_honest_ffg_weight
```

> 💡 Ghi chú: Kết quả = (support đã quan sát được − phần có thể do đối thủ đóng
> góp) + (phần trọng số trung thực của các slot còn lại trong epoch, những slot
> này chắc chắn sẽ bỏ phiếu cho target theo giả định đồng bộ).

##### `will_no_conflicting_checkpoint_be_justified`

*Note*: Hàm này giả định rằng tất cả validator trung thực sẽ bỏ phiếu ủng hộ
target của epoch hiện tại kể từ thời điểm hiện tại trở đi.

```python
def will_no_conflicting_checkpoint_be_justified(store: Store) -> bool:
    """
    Return ``True`` if and only if no checkpoint conflicting with the current target can ever be justified.
    """

    # If the target is unrealized justified then no conflicting checkpoint can be justified
    if get_current_target(store) == store.unrealized_justified_checkpoint:
        return True

    state = get_pulled_up_head_state(store)
    total_active_balance = get_total_active_balance(state)
    honest_ffg_support = compute_honest_ffg_support_for_current_target(store)
    return 3 * honest_ffg_support > 1 * total_active_balance
```

> 💡 Ghi chú: Nếu support trung thực cho target hiện tại vượt quá 1/3 tổng
> active balance, thì không checkpoint xung đột nào có thể gom đủ 2/3 để được
> justified.

##### `will_current_target_be_justified`

*Note*: Hàm này giả định rằng tất cả validator trung thực sẽ bỏ phiếu ủng hộ
target của epoch hiện tại kể từ thời điểm hiện tại trở đi.

```python
def will_current_target_be_justified(store: Store) -> bool:
    """
    Return ``True`` if and only if the current target will eventually be justified.
    """
    state = get_pulled_up_head_state(store)
    total_active_balance = get_total_active_balance(state)
    honest_ffg_support = compute_honest_ffg_support_for_current_target(store)
    return 3 * honest_ffg_support >= 2 * total_active_balance
```

#### `update_fast_confirmation_variables`

*Note*: Hàm này cập nhật các biến được fast confirmation rule sử dụng.

```python
def update_fast_confirmation_variables(fcr_store: FastConfirmationStore) -> None:
    # Update prev and curr slot head
    store = fcr_store.store
    fcr_store.previous_slot_head = fcr_store.current_slot_head
    fcr_store.current_slot_head = get_head(store).root

    # Update greatest unrealized justified checkpoint at the last slot of an epoch
    if is_start_slot_at_epoch(get_current_slot(store) + 1):
        fcr_store.previous_epoch_greatest_unrealized_checkpoint = (
            store.unrealized_justified_checkpoint
        )

    # Update observed justified checkpoints at the start of an epoch
    if is_start_slot_at_epoch(get_current_slot(store)):
        fcr_store.previous_epoch_observed_justified_checkpoint = (
            fcr_store.current_epoch_observed_justified_checkpoint
        )
        fcr_store.current_epoch_observed_justified_checkpoint = (
            fcr_store.previous_epoch_greatest_unrealized_checkpoint
        )
```

#### `find_latest_confirmed_descendant`

*Notes*:

Hàm này duyệt các block của chuỗi canonical bắt đầu từ `latest_confirmed_root`
và trả về block mới nhất thỏa mãn các điều kiện của FCR:

1. Mọi block trong chuỗi của nó đều LMD-GHOST safe, tức là sẽ thắng theo quy tắc
   fork choice LMD-GHOST kể từ thời điểm hiện tại trở đi.
2. Block sẽ không bị lọc bỏ (filtered out) trong epoch hiện tại và epoch kế tiếp.

Với giả định đồng bộ và giá trị `CONFIRMATION_BYZANTINE_THRESHOLD`, các tiêu chí
trên bảo đảm rằng block do hàm này trả về sẽ tiếp tục là canonical trong góc nhìn
của mọi validator trung thực kể từ thời điểm hiện tại trở đi.

Hàm này chỉ hoạt động đúng nếu `latest_confirmed_root` thuộc chuỗi canonical và
nằm ở epoch trước hoặc epoch hiện tại.

> 💡 Ghi chú: Hàm gồm hai giai đoạn. Giai đoạn đầu cố gắng xác nhận thêm các
> block thuộc epoch trước (chỉ khi các điều kiện về voting source và
> justification cho phép). Giai đoạn sau tiếp tục tiến về phía head, kể cả các
> block của epoch hiện tại — nhưng để vượt sang epoch hiện tại thì target của
> epoch hiện tại phải chắc chắn sẽ được justified; và kết quả "tạm thời"
> (`tentative_confirmed_root`) chỉ được chấp nhận nếu block chắc chắn không bị
> loại khỏi chuỗi trong epoch hiện tại hoặc epoch kế tiếp. "Bị lọc bỏ" ở đây
> nói đến bước lọc các nhánh có voting source không phù hợp trong fork choice
> (`filter_block_tree`).

```python
def find_latest_confirmed_descendant(
    fcr_store: FastConfirmationStore, latest_confirmed_root: Root
) -> Root:
    """
    Return the most recent confirmed block in the suffix of the canonical chain
    starting from ``latest_confirmed_root``.
    """
    store = fcr_store.store
    head = get_head(store).root
    current_epoch = get_current_store_epoch(store)
    confirmed_root = latest_confirmed_root

    if (
        get_block_epoch(store, confirmed_root) + 1 == current_epoch
        and get_voting_source(store, fcr_store.previous_slot_head).epoch + 2 >= current_epoch
        and (
            is_start_slot_at_epoch(get_current_slot(store))
            or (
                will_no_conflicting_checkpoint_be_justified(store)
                and (
                    store.unrealized_justifications[fcr_store.previous_slot_head].epoch + 1
                    >= current_epoch
                    or store.unrealized_justifications[head].epoch + 1 >= current_epoch
                )
            )
        )
    ):
        # Get suffix of the canonical chain
        canonical_roots = get_ancestor_roots(store, head, confirmed_root)

        # Starting with the child of the latest_confirmed_root
        # move towards the head in attempt to advance the confirmed block
        # and stop when the first unconfirmed descendant is encountered
        for block_root in canonical_roots:
            block_epoch = get_block_epoch(store, block_root)

            # If the current epoch is reached, exit the loop
            # as this code is meant to confirm blocks from the previous epoch
            if block_epoch == current_epoch:
                break

            # The algorithm can only rely on the previous head
            # if it is a descendant of the block that is attempted to be confirmed
            if not is_ancestor(
                store,
                get_node_for_root(fcr_store.previous_slot_head),
                get_node_for_root(block_root),
            ):
                break

            if not is_one_confirmed(store, get_current_balance_source(fcr_store), block_root):
                break

            confirmed_root = block_root

    if (
        is_start_slot_at_epoch(get_current_slot(store))
        or store.unrealized_justifications[head].epoch + 1 >= current_epoch
    ):
        # Get suffix of the canonical chain
        canonical_roots = get_ancestor_roots(store, head, confirmed_root)

        tentative_confirmed_root = confirmed_root

        for block_root in canonical_roots:
            block_epoch = get_block_epoch(store, block_root)
            tentative_confirmed_epoch = get_block_epoch(store, tentative_confirmed_root)

            # The following condition can only be true the first time
            # the algorithm advances to a block from the current epoch
            if block_epoch > tentative_confirmed_epoch:
                # To confirm blocks from the current epoch ensure that
                # current epoch target will be justified
                if not will_current_target_be_justified(store):
                    break

            if not is_one_confirmed(store, get_current_balance_source(fcr_store), block_root):
                break

            tentative_confirmed_root = block_root

        # The tentative_confirmed_root can only be confirmed
        # if it is for sure not going to be reorged out in either the current or next epoch.
        if get_block_epoch(store, tentative_confirmed_root) == current_epoch or (
            get_voting_source(store, tentative_confirmed_root).epoch + 2 >= current_epoch
            and (
                is_start_slot_at_epoch(get_current_slot(store))
                or will_no_conflicting_checkpoint_be_justified(store)
            )
        ):
            confirmed_root = tentative_confirmed_root

    return confirmed_root
```

#### `get_latest_confirmed`

*Notes:*

Hàm này thực thi thuật toán FCR theo trình tự các bước sau:

1. Kiểm tra xem `fcr_store.confirmed_root` có thuộc chuỗi canonical và không cũ
   hơn epoch trước hay không.
2. Kiểm tra xem chuỗi đã xác nhận bắt đầu từ
   `fcr_store.current_epoch_observed_justified_checkpoint` có thể được xác nhận
   lại (re-confirm) vào đầu epoch hiện tại hay không; việc này đặt lại GST về
   thời điểm bắt đầu epoch hiện tại.
3. Nếu bất kỳ phép kiểm tra nào ở trên thất bại, đặt `fcr_store.confirmed_root`
   về `store.finalized_checkpoint.root`. Bất kỳ điều kiện nào ở trên không thỏa
   cũng cho thấy các giả định của FCR (ít nhất là giả định đồng bộ) đã bị phá vỡ
   và block đã xác nhận có thể không còn an toàn.
4. Khởi động lại chuỗi xác nhận bằng cách đặt `fcr_store.confirmed_root` thành
   `fcr_store.current_epoch_observed_justified_checkpoint.root` nếu các điều kiện
   khởi động lại được thỏa mãn. Dưới giả định đồng bộ, checkpoint này chắc chắn
   hiện là checkpoint justified lớn nhất trong góc nhìn của mọi validator trung
   thực, và do đó mọi validator trung thực sẽ tiếp tục bỏ phiếu cho nó trong
   suốt cả epoch.
5. Cố gắng đẩy `fcr_store.confirmed_root` tiến lên bằng cách gọi
   `find_latest_confirmed_descendant`.

```python
def get_latest_confirmed(fcr_store: FastConfirmationStore) -> Root:
    """
    Return the most recent confirmed block by executing the FCR algorithm.
    """
    store = fcr_store.store
    confirmed_root = fcr_store.confirmed_root
    current_epoch = get_current_store_epoch(store)

    # Revert to finalized block if either of the following is true:
    # 1) the latest confirmed block's epoch is older than the previous epoch,
    # 2) the latest confirmed block does not belong to the canonical chain,
    # 3) the confirmed chain starting from the current epoch observed justified checkpoint
    #    cannot be re-confirmed at the start of the current epoch.
    head = get_head(store).root
    if (
        get_block_epoch(store, confirmed_root) + 1 < current_epoch
        or not is_ancestor(store, get_node_for_root(head), get_node_for_root(confirmed_root))
        or (
            is_start_slot_at_epoch(get_current_slot(store))
            and not is_confirmed_chain_safe(fcr_store, confirmed_root)
        )
    ):
        confirmed_root = store.finalized_checkpoint.root

    # Restart the confirmation chain if each of the following conditions are true:
    # 1) it is the start of the current epoch,
    # 2) epoch of fcr_store.current_epoch_observed_justified_checkpoint.root equals to the previous epoch,
    # 3) fcr_store.current_epoch_observed_justified_checkpoint equals to unrealized justification of the head,
    # 4) confirmed block is older than the block of fcr_store.current_epoch_observed_justified_checkpoint.
    is_epoch_start = is_start_slot_at_epoch(get_current_slot(store))
    observed_justified_block_slot = get_block_slot(
        store, fcr_store.current_epoch_observed_justified_checkpoint.root
    )
    is_observed_justified_block_epoch_ok = (
        compute_epoch_at_slot(observed_justified_block_slot) + 1 == current_epoch
    )
    is_head_unrealized_justified_ok = (
        fcr_store.current_epoch_observed_justified_checkpoint
        == store.unrealized_justifications[head]
    )
    is_confirmed_block_stale = get_block_slot(store, confirmed_root) < observed_justified_block_slot
    if (
        is_epoch_start
        and is_observed_justified_block_epoch_ok
        and is_head_unrealized_justified_ok
        and is_confirmed_block_stale
    ):
        confirmed_root = fcr_store.current_epoch_observed_justified_checkpoint.root

    # Attempt to further advance the latest confirmed block
    if get_block_epoch(store, confirmed_root) + 1 >= current_epoch:
        return find_latest_confirmed_descendant(fcr_store, confirmed_root)
    else:
        return confirmed_root
```

#### `get_restart_resilient_confirmed_root`

*Note*: Các implementation MAY dùng cơ chế dưới đây để khôi phục confirmed root
sau khi node khởi động lại. Cơ chế này an toàn chừng nào tính đồng bộ được duy
trì trong ít nhất ba epoch kể từ khi node offline. Nếu được sử dụng,
`get_restart_resilient_confirmed_root` MUST được gọi khi node đã sync đầy đủ và
`on_fast_confirmation` đã được gọi. Phần thân của
`get_root_confirmed_before_restart` phụ thuộc vào implementation.

```python
def block_should_be_finalized(store: Store, block_root: Root) -> bool:
    block_slot = get_block_slot(store, block_root)
    next_checkpoint_epoch = compute_epoch_at_slot(block_slot + SLOTS_PER_EPOCH - 1)
    earliest_finality_slot = compute_start_slot_at_epoch(next_checkpoint_epoch + 2)
    return earliest_finality_slot <= get_current_slot(store)


def get_restart_resilient_confirmed_root(fcr_store: FastConfirmationStore) -> Root:
    store = fcr_store.store
    root_before_restart = get_root_confirmed_before_restart()
    root_before_restart_slot = get_block_slot(store, root_before_restart)

    # Recently confirmed block has advanced beyond the block that was confirmed
    # before the node restart
    if root_before_restart_slot <= get_block_slot(store, fcr_store.confirmed_root):
        return fcr_store.confirmed_root

    # If the block is old enough it either has been finalized already or
    # finality has been delayed which makes block confirmed before restart
    # unreliable
    if block_should_be_finalized(store, root_before_restart):
        return fcr_store.confirmed_root

    # If a block confirmed before the restart is not canonical,
    # return the recently confirmed block
    if not is_ancestor(store, get_head(store), get_node_for_root(root_before_restart)):
        return fcr_store.confirmed_root

    return root_before_restart
```

> 💡 Ghi chú: Block đã xác nhận trước khi restart chỉ được dùng lại nếu nó mới
> hơn block vừa được xác nhận sau restart, chưa "đủ cũ" để lẽ ra đã được
> finalized, và vẫn nằm trên chuỗi canonical hiện tại; nếu không, dùng
> `fcr_store.confirmed_root` hiện tại.

### Handlers

#### `on_fast_confirmation`

*Notes:*

Handler này gọi `update_fast_confirmation_variables`, sau đó gọi
`get_latest_confirmed` và cập nhật `fcr_store.confirmed_root` bằng kết quả trả
về của lời gọi đó.

Các implementation MUST tuân thủ nghiêm ngặt thứ tự gọi:

1. `update_fast_confirmation_variables`
2. `get_latest_confirmed`

Các implementation MUST gọi `update_fast_confirmation_variables` trong phần đầu
của slot, sau khi các attestation từ các slot trước đã được áp dụng và trước khi
`get_attestation_due_ms(epoch)` mili giây trôi qua kể từ đầu slot.

Các implementation MAY gọi `update_fast_confirmation_variables` sau khi đã nhận
và xử lý một block hợp lệ từ đúng block proposer được phân công cho `slot`, nếu
việc này diễn ra trước khi `get_attestation_due_ms(epoch)` mili giây trôi qua
kể từ đầu `slot`. Bất kể thời điểm gọi là khi nào,
`update_fast_confirmation_variables` MUST chỉ được gọi đúng một lần mỗi slot.

Các implementation MAY gọi `get_latest_confirmed` vào bất kỳ thời điểm nào trong
suốt slot.

```python
def on_fast_confirmation(fcr_store: FastConfirmationStore) -> None:
    update_fast_confirmation_variables(fcr_store)
    fcr_store.confirmed_root = get_latest_confirmed(fcr_store)
```
