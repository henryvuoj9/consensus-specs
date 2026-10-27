# Altair Light Client -- Sync Protocol

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Types](#types)
  - [`CurrentSyncCommitteeBranch`](#currentsynccommitteebranch)
  - [`FinalityBranch`](#finalitybranch)
  - [`NextSyncCommitteeBranch`](#nextsynccommitteebranch)
- [Constants](#constants)
- [Presets](#presets)
  - [Misc](#misc)
- [Containers](#containers)
  - [`LightClientHeader`](#lightclientheader)
  - [`LightClientBootstrap`](#lightclientbootstrap)
  - [`LightClientUpdate`](#lightclientupdate)
  - [`LightClientFinalityUpdate`](#lightclientfinalityupdate)
  - [`LightClientOptimisticUpdate`](#lightclientoptimisticupdate)
  - [`LightClientStore`](#lightclientstore)
- [Helpers](#helpers)
  - [`finalized_root_gindex_at_slot`](#finalized_root_gindex_at_slot)
  - [`current_sync_committee_gindex_at_slot`](#current_sync_committee_gindex_at_slot)
  - [`next_sync_committee_gindex_at_slot`](#next_sync_committee_gindex_at_slot)
  - [`is_valid_light_client_header`](#is_valid_light_client_header)
  - [`is_sync_committee_update`](#is_sync_committee_update)
  - [`is_finality_update`](#is_finality_update)
  - [`is_better_update`](#is_better_update)
  - [`is_next_sync_committee_known`](#is_next_sync_committee_known)
  - [`get_safety_threshold`](#get_safety_threshold)
  - [`get_subtree_index`](#get_subtree_index)
  - [`is_valid_normalized_merkle_branch`](#is_valid_normalized_merkle_branch)
  - [`compute_sync_committee_period_at_slot`](#compute_sync_committee_period_at_slot)
- [Light client initialization](#light-client-initialization)
  - [`initialize_light_client_store`](#initialize_light_client_store)
- [Light client state updates](#light-client-state-updates)
  - [`validate_light_client_update`](#validate_light_client_update)
  - [`apply_light_client_update`](#apply_light_client_update)
  - [`process_light_client_store_force_update`](#process_light_client_store_force_update)
  - [`process_light_client_update`](#process_light_client_update)
  - [`process_light_client_finality_update`](#process_light_client_finality_update)
  - [`process_light_client_optimistic_update`](#process_light_client_optimistic_update)

<!-- mdformat-toc end -->

## Introduction

Beacon chain được thiết kế để thân thiện với light client (client "nhẹ"
chỉ tải và kiểm tra một phần nhỏ dữ liệu chain), giúp các môi trường bị giới hạn
tài nguyên có thể truy cập Ethereum với mức an toàn (safety) và tính sống
(liveness) hợp lý. Các môi trường này bao gồm thiết bị hạn chế tài nguyên (ví dụ:
điện thoại chạy ví theo hướng tối thiểu hoá sự tin cậy) và các VM tính phí theo
mức sử dụng (ví dụ: VM của blockchain khác dùng cho cross-chain bridge).

Tài liệu này đề xuất một thiết kế light client tối giản cho beacon chain, dựa
trên các sync committee được giới thiệu trong
[phần mở rộng beacon-chain này](../beacon-chain.md).

> 💡 Ghi chú: Ý tưởng cốt lõi là light client không cần theo dõi toàn bộ
> validator set. Nó chỉ cần biết sync committee hiện tại (512 validator, thay đổi
> mỗi sync committee period ~27 giờ) và kiểm tra chữ ký aggregate của committee
> này trên các block header. Mỗi update còn kèm Merkle proof cho sync committee kế
> tiếp, nên light client có thể "nối chuỗi" tin cậy từ period này sang period sau.

Các tài liệu bổ sung mô tả cách sử dụng light client sync protocol:

- [Full node](./full-node.md)
- [Light client](./light-client.md)
- [Networking](./p2p-interface.md)

## Types

### `CurrentSyncCommitteeBranch`

```python
class CurrentSyncCommitteeBranch(Vector[Bytes32]):
    """
    A Merkle branch proving ``current_sync_committee`` within ``BeaconState``.
    """

    LENGTH = floorlog2(CURRENT_SYNC_COMMITTEE_GINDEX)
```

### `FinalityBranch`

```python
class FinalityBranch(Vector[Bytes32]):
    """
    A Merkle branch proving ``finalized_checkpoint.root`` within
    ``BeaconState``.
    """

    LENGTH = floorlog2(FINALIZED_ROOT_GINDEX)
```

### `NextSyncCommitteeBranch`

```python
class NextSyncCommitteeBranch(Vector[Bytes32]):
    """
    A Merkle branch proving ``next_sync_committee`` within ``BeaconState``.
    """

    LENGTH = floorlog2(NEXT_SYNC_COMMITTEE_GINDEX)
```

## Constants

| Name                            | Value                                                                        |
| ------------------------------- | ---------------------------------------------------------------------------- |
| `FINALIZED_ROOT_GINDEX`         | `get_generalized_index(BeaconState, "finalized_checkpoint", "root")` (= 105) |
| `CURRENT_SYNC_COMMITTEE_GINDEX` | `get_generalized_index(BeaconState, "current_sync_committee")` (= 54)        |
| `NEXT_SYNC_COMMITTEE_GINDEX`    | `get_generalized_index(BeaconState, "next_sync_committee")` (= 55)           |

## Presets

### Misc

| Name                              | Value                                                      |
| --------------------------------- | ---------------------------------------------------------- |
| `MIN_SYNC_COMMITTEE_PARTICIPANTS` | `Uint64(1)`                                                |
| `UPDATE_TIMEOUT`                  | `Slot(SLOTS_PER_EPOCH * EPOCHS_PER_SYNC_COMMITTEE_PERIOD)` |

## Containers

### `LightClientHeader`

```python
class LightClientHeader(Container):
    beacon: BeaconBlockHeader
```

Các bản nâng cấp (fork) trong tương lai có thể bổ sung thêm field vào cấu trúc
này, và kiểm tra tính hợp lệ của chúng bằng cách mở rộng
[`is_valid_light_client_header`](#is_valid_light_client_header).

> 💡 Ghi chú: Ở Altair, header chỉ chứa `BeaconBlockHeader`. Từ Capella trở đi,
> header được mở rộng thêm thông tin execution payload header kèm Merkle proof.

### `LightClientBootstrap`

```python
class LightClientBootstrap(Container):
    # Header khớp với beacon block root được yêu cầu
    header: LightClientHeader
    # Sync committee hiện tại tương ứng với `header.beacon.state_root`
    current_sync_committee: SyncCommittee
    current_sync_committee_branch: CurrentSyncCommitteeBranch
```

### `LightClientUpdate`

```python
class LightClientUpdate(Container):
    # Header được sync committee attest (ký xác nhận)
    attested_header: LightClientHeader
    # Sync committee kế tiếp tương ứng với `attested_header.beacon.state_root`
    next_sync_committee: SyncCommittee
    next_sync_committee_branch: NextSyncCommitteeBranch
    # Finalized header tương ứng với `attested_header.beacon.state_root`
    finalized_header: LightClientHeader
    finality_branch: FinalityBranch
    # Chữ ký aggregate của sync committee
    sync_aggregate: SyncAggregate
    # Slot tại đó chữ ký aggregate được tạo (không đáng tin cậy, chưa được xác minh)
    signature_slot: Slot
```

### `LightClientFinalityUpdate`

```python
class LightClientFinalityUpdate(Container):
    # Header được sync committee attest (ký xác nhận)
    attested_header: LightClientHeader
    # Finalized header tương ứng với `attested_header.beacon.state_root`
    finalized_header: LightClientHeader
    finality_branch: FinalityBranch
    # Chữ ký aggregate của sync committee
    sync_aggregate: SyncAggregate
    # Slot tại đó chữ ký aggregate được tạo (không đáng tin cậy, chưa được xác minh)
    signature_slot: Slot
```

### `LightClientOptimisticUpdate`

```python
class LightClientOptimisticUpdate(Container):
    # Header được sync committee attest (ký xác nhận)
    attested_header: LightClientHeader
    # Chữ ký aggregate của sync committee
    sync_aggregate: SyncAggregate
    # Slot tại đó chữ ký aggregate được tạo (không đáng tin cậy, chưa được xác minh)
    signature_slot: Slot
```

### `LightClientStore`

```python
@dataclass
class LightClientStore:
    # Header đã được finalized
    finalized_header: LightClientHeader
    # Các sync committee tương ứng với finalized header
    current_sync_committee: SyncCommittee
    next_sync_committee: SyncCommittee
    # Update tốt nhất hiện có, dùng để chuyển finalized head sang nếu không nhận được gì tốt hơn
    best_valid_update: LightClientUpdate | None
    # Header mới nhất có mức an toàn chấp nhận được
    optimistic_header: LightClientHeader
    # Số participant hoạt động tối đa trong một sync committee (dùng để tính safety threshold)
    previous_max_active_participants: Uint64
    current_max_active_participants: Uint64
```

## Helpers

### `finalized_root_gindex_at_slot`

```python
def finalized_root_gindex_at_slot(_slot: Slot) -> GeneralizedIndex:
    return FINALIZED_ROOT_GINDEX
```

### `current_sync_committee_gindex_at_slot`

```python
def current_sync_committee_gindex_at_slot(_slot: Slot) -> GeneralizedIndex:
    return CURRENT_SYNC_COMMITTEE_GINDEX
```

### `next_sync_committee_gindex_at_slot`

```python
def next_sync_committee_gindex_at_slot(_slot: Slot) -> GeneralizedIndex:
    return NEXT_SYNC_COMMITTEE_GINDEX
```

### `is_valid_light_client_header`

```python
def is_valid_light_client_header(_header: LightClientHeader) -> bool:
    return True
```

### `is_sync_committee_update`

```python
def is_sync_committee_update(update: LightClientUpdate) -> bool:
    return update.next_sync_committee_branch != NextSyncCommitteeBranch()
```

### `is_finality_update`

```python
def is_finality_update(update: LightClientUpdate) -> bool:
    return update.finality_branch != FinalityBranch()
```

### `is_better_update`

```python
def is_better_update(new_update: LightClientUpdate, old_update: LightClientUpdate) -> bool:
    # So sánh xem mức tham gia sync committee có đạt supermajority (> 2/3) hay không
    max_active_participants = len(new_update.sync_aggregate.sync_committee_bits)
    new_num_active_participants = get_set_bit_count(new_update.sync_aggregate.sync_committee_bits)
    old_num_active_participants = get_set_bit_count(old_update.sync_aggregate.sync_committee_bits)
    new_has_supermajority = new_num_active_participants * 3 >= max_active_participants * 2
    old_has_supermajority = old_num_active_participants * 3 >= max_active_participants * 2
    if new_has_supermajority != old_has_supermajority:
        return new_has_supermajority
    if not new_has_supermajority and new_num_active_participants != old_num_active_participants:
        return new_num_active_participants > old_num_active_participants

    # So sánh sự có mặt của sync committee liên quan (next sync committee cùng period với signature slot)
    new_has_relevant_sync_committee = is_sync_committee_update(new_update) and (
        compute_sync_committee_period_at_slot(new_update.attested_header.beacon.slot)
        == compute_sync_committee_period_at_slot(new_update.signature_slot)
    )
    old_has_relevant_sync_committee = is_sync_committee_update(old_update) and (
        compute_sync_committee_period_at_slot(old_update.attested_header.beacon.slot)
        == compute_sync_committee_period_at_slot(old_update.signature_slot)
    )
    if new_has_relevant_sync_committee != old_has_relevant_sync_committee:
        return new_has_relevant_sync_committee

    # So sánh xem update có chứa thông tin finality hay không
    new_has_finality = is_finality_update(new_update)
    old_has_finality = is_finality_update(old_update)
    if new_has_finality != old_has_finality:
        return new_has_finality

    # So sánh sync committee finality (finalized header cùng period với attested header)
    if new_has_finality:
        new_has_sync_committee_finality = compute_sync_committee_period_at_slot(
            new_update.finalized_header.beacon.slot
        ) == compute_sync_committee_period_at_slot(new_update.attested_header.beacon.slot)
        old_has_sync_committee_finality = compute_sync_committee_period_at_slot(
            old_update.finalized_header.beacon.slot
        ) == compute_sync_committee_period_at_slot(old_update.attested_header.beacon.slot)
        if new_has_sync_committee_finality != old_has_sync_committee_finality:
            return new_has_sync_committee_finality

    # Tiebreaker 1: mức tham gia sync committee vượt trên supermajority
    if new_num_active_participants != old_num_active_participants:
        return new_num_active_participants > old_num_active_participants

    # Tiebreaker 2: ưu tiên dữ liệu cũ hơn (ít phải thay đổi best update hơn)
    if new_update.attested_header.beacon.slot != old_update.attested_header.beacon.slot:
        return new_update.attested_header.beacon.slot < old_update.attested_header.beacon.slot

    # Tiebreaker 3: ưu tiên update có signature slot sớm hơn
    return new_update.signature_slot < old_update.signature_slot
```

### `is_next_sync_committee_known`

```python
def is_next_sync_committee_known(store: LightClientStore) -> bool:
    return store.next_sync_committee != SyncCommittee.empty()
```

### `get_safety_threshold`

```python
def get_safety_threshold(store: LightClientStore) -> Uint64:
    return (
        max(
            store.previous_max_active_participants,
            store.current_max_active_participants,
        )
        // 2
    )
```

### `get_subtree_index`

```python
def get_subtree_index(generalized_index: GeneralizedIndex) -> Uint64:
    return Uint64(generalized_index % 2 ** (floorlog2(generalized_index)))
```

### `is_valid_normalized_merkle_branch`

```python
def is_valid_normalized_merkle_branch(
    leaf: Bytes32, branch: Sequence[Bytes32], gindex: GeneralizedIndex, root: Root
) -> bool:
    depth = floorlog2(gindex)
    index = get_subtree_index(gindex)
    num_extra = len(branch) - depth
    for i in range(num_extra):
        if branch[i] != Bytes32():
            return False
    return is_valid_merkle_branch(leaf, branch[num_extra:], depth, index, root)
```

### `compute_sync_committee_period_at_slot`

```python
def compute_sync_committee_period_at_slot(slot: Slot) -> Uint64:
    return compute_sync_committee_period(compute_epoch_at_slot(slot))
```

## Light client initialization

Light client lưu trạng thái của mình trong một object `store` có kiểu
`LightClientStore`. Hàm `initialize_light_client_store` khởi tạo một `store` mới
từ một `LightClientBootstrap` nhận được, tương ứng với một `trusted_block_root`
cho trước.

> 💡 Ghi chú: `trusted_block_root` là điểm neo tin cậy ban đầu (thường là root
> của một block finalized gần đây, lấy từ nguồn đáng tin cậy — khái niệm weak
> subjectivity checkpoint). Light client kiểm tra `bootstrap.header` khớp với root
> này, rồi dùng Merkle proof để xác minh `current_sync_committee` thuộc về state
> của header đó.

### `initialize_light_client_store`

```python
def initialize_light_client_store(
    trusted_block_root: Root, bootstrap: LightClientBootstrap
) -> LightClientStore:
    assert is_valid_light_client_header(bootstrap.header)
    assert hash_tree_root(bootstrap.header.beacon) == trusted_block_root

    assert is_valid_normalized_merkle_branch(
        leaf=hash_tree_root(bootstrap.current_sync_committee),
        branch=bootstrap.current_sync_committee_branch,
        gindex=current_sync_committee_gindex_at_slot(bootstrap.header.beacon.slot),
        root=bootstrap.header.beacon.state_root,
    )

    return LightClientStore(
        finalized_header=bootstrap.header,
        current_sync_committee=bootstrap.current_sync_committee,
        next_sync_committee=SyncCommittee.empty(),
        best_valid_update=None,
        optimistic_header=bootstrap.header,
        previous_max_active_participants=Uint64(0),
        current_max_active_participants=Uint64(0),
    )
```

## Light client state updates

- Light client nhận các object có kiểu `LightClientUpdate`,
  `LightClientFinalityUpdate` và `LightClientOptimisticUpdate`:
  - **`update: LightClientUpdate`**: Mỗi `update` kích hoạt lời gọi
    `process_light_client_update(store, update, current_slot, genesis_validators_root)`
    trong đó `current_slot` là slot hiện tại tính theo đồng hồ cục bộ.
  - **`finality_update: LightClientFinalityUpdate`**: Mỗi `finality_update`
    kích hoạt lời gọi
    `process_light_client_finality_update(store, finality_update, current_slot, genesis_validators_root)`.
  - **`optimistic_update: LightClientOptimisticUpdate`**: Mỗi
    `optimistic_update` kích hoạt lời gọi
    `process_light_client_optimistic_update(store, optimistic_update, current_slot, genesis_validators_root)`.
- `process_light_client_store_force_update` MAY (có thể) được gọi dựa trên các
  heuristic tuỳ theo use case, khi quá trình sync của light client có vẻ bị kẹt.

> 💡 Ghi chú: `finality_update` và `optimistic_update` thực chất là các phiên
> bản rút gọn của `LightClientUpdate` (không có `next_sync_committee`, và với
> optimistic update thì cũng không có finalized header). Chúng được chuyển thành
> `LightClientUpdate` với các field còn thiếu để trống rồi xử lý chung qua
> `process_light_client_update`. Force update là cơ chế dự phòng khi chain lâu
> không finalize, để light client vẫn có thể chuyển sang sync committee period
> tiếp theo.

### `validate_light_client_update`

```python
def validate_light_client_update(
    store: LightClientStore,
    update: LightClientUpdate,
    current_slot: Slot,
    genesis_validators_root: Root,
) -> None:
    # Kiểm tra sync committee có đủ số participant
    sync_aggregate = update.sync_aggregate
    assert get_set_bit_count(sync_aggregate.sync_committee_bits) >= MIN_SYNC_COMMITTEE_PARTICIPANTS

    # Kiểm tra update không nhảy cóc qua một sync committee period
    assert is_valid_light_client_header(update.attested_header)
    update_attested_slot = update.attested_header.beacon.slot
    update_finalized_slot = update.finalized_header.beacon.slot
    assert current_slot >= update.signature_slot > update_attested_slot >= update_finalized_slot
    store_period = compute_sync_committee_period_at_slot(store.finalized_header.beacon.slot)
    update_signature_period = compute_sync_committee_period_at_slot(update.signature_slot)
    if is_next_sync_committee_known(store):
        assert update_signature_period in (store_period, store_period + 1)
    else:
        assert update_signature_period == store_period

    # Kiểm tra update có liên quan (mang thông tin mới cho store)
    update_attested_period = compute_sync_committee_period_at_slot(update_attested_slot)
    update_has_next_sync_committee = not is_next_sync_committee_known(store) and (
        is_sync_committee_update(update) and update_attested_period == store_period
    )
    assert (
        update_attested_slot > store.finalized_header.beacon.slot or update_has_next_sync_committee
    )

    # Kiểm tra rằng `finality_branch`, nếu có, xác nhận `finalized_header`
    # khớp với finalized checkpoint root được lưu trong state của `attested_header`.
    # Lưu ý: finalized checkpoint root tại genesis được biểu diễn bằng hash toàn số 0.
    if not is_finality_update(update):
        assert update.finalized_header == LightClientHeader.empty()
    else:
        if update_finalized_slot == GENESIS_SLOT:
            assert update.finalized_header == LightClientHeader.empty()
            finalized_root = Bytes32()
        else:
            assert is_valid_light_client_header(update.finalized_header)
            finalized_root = hash_tree_root(update.finalized_header.beacon)
        assert is_valid_normalized_merkle_branch(
            leaf=finalized_root,
            branch=update.finality_branch,
            gindex=finalized_root_gindex_at_slot(update.attested_header.beacon.slot),
            root=update.attested_header.beacon.state_root,
        )

    # Kiểm tra rằng `next_sync_committee`, nếu có, đúng là next sync committee được lưu trong
    # state của `attested_header`
    if not is_sync_committee_update(update):
        assert update.next_sync_committee == SyncCommittee.empty()
    else:
        if update_attested_period == store_period and is_next_sync_committee_known(store):
            assert update.next_sync_committee == store.next_sync_committee
        assert is_valid_normalized_merkle_branch(
            leaf=hash_tree_root(update.next_sync_committee),
            branch=update.next_sync_committee_branch,
            gindex=next_sync_committee_gindex_at_slot(update.attested_header.beacon.slot),
            root=update.attested_header.beacon.state_root,
        )

    # Kiểm tra chữ ký aggregate của sync committee
    if update_signature_period == store_period:
        sync_committee = store.current_sync_committee
    else:
        sync_committee = store.next_sync_committee
    participant_pubkeys = [
        pubkey
        for (bit, pubkey) in zip(
            sync_aggregate.sync_committee_bits, sync_committee.pubkeys, strict=True
        )
        if bit
    ]
    fork_version_slot = saturating_sub(update.signature_slot, 1)
    fork_version = compute_fork_version(compute_epoch_at_slot(fork_version_slot))
    domain = compute_domain(DOMAIN_SYNC_COMMITTEE, fork_version, genesis_validators_root)
    signing_root = compute_signing_root(update.attested_header.beacon, domain)
    assert bls.FastAggregateVerify(
        participant_pubkeys, signing_root, sync_aggregate.sync_committee_signature
    )
```

### `apply_light_client_update`

```python
def apply_light_client_update(store: LightClientStore, update: LightClientUpdate) -> None:
    store_period = compute_sync_committee_period_at_slot(store.finalized_header.beacon.slot)
    update_finalized_period = compute_sync_committee_period_at_slot(
        update.finalized_header.beacon.slot
    )
    if not is_next_sync_committee_known(store):
        assert update_finalized_period == store_period
        store.next_sync_committee = update.next_sync_committee
    elif update_finalized_period == store_period + 1:
        store.current_sync_committee = store.next_sync_committee
        store.next_sync_committee = update.next_sync_committee
        store.previous_max_active_participants = store.current_max_active_participants
        store.current_max_active_participants = Uint64(0)
    if update.finalized_header.beacon.slot > store.finalized_header.beacon.slot:
        store.finalized_header = update.finalized_header
        if store.finalized_header.beacon.slot > store.optimistic_header.beacon.slot:
            store.optimistic_header = store.finalized_header
```

### `process_light_client_store_force_update`

```python
def process_light_client_store_force_update(store: LightClientStore, current_slot: Slot) -> None:
    if (
        current_slot > store.finalized_header.beacon.slot + UPDATE_TIMEOUT
        and store.best_valid_update is not None
    ):
        # Ép áp dụng best update khi đã hết update timeout.
        # Vì logic apply chờ `finalized_header.beacon.slot` thể hiện sync committee finality,
        # nên `attested_header` có thể được coi như `finalized_header` khi chain lâu không finalize
        # để đảm bảo vẫn tiến được sang các sync committee period sau, theo thứ tự của `is_better_update`.
        if (
            store.best_valid_update.finalized_header.beacon.slot
            <= store.finalized_header.beacon.slot
        ):
            store.best_valid_update.finalized_header = store.best_valid_update.attested_header
        apply_light_client_update(store, store.best_valid_update)
        store.best_valid_update = None
```

### `process_light_client_update`

```python
def process_light_client_update(
    store: LightClientStore,
    update: LightClientUpdate,
    current_slot: Slot,
    genesis_validators_root: Root,
) -> None:
    validate_light_client_update(store, update, current_slot, genesis_validators_root)

    sync_committee_bits = update.sync_aggregate.sync_committee_bits

    # Cập nhật best update, phòng khi phải force-update sang nó nếu hết timeout
    if store.best_valid_update is None or is_better_update(update, store.best_valid_update):
        store.best_valid_update = update

    # Theo dõi số participant hoạt động tối đa trong các chữ ký của committee
    store.current_max_active_participants = max(
        store.current_max_active_participants,
        get_set_bit_count(sync_committee_bits),
    )

    # Cập nhật optimistic header
    if (
        get_set_bit_count(sync_committee_bits) > get_safety_threshold(store)
        and update.attested_header.beacon.slot > store.optimistic_header.beacon.slot
    ):
        store.optimistic_header = update.attested_header

    # Cập nhật finalized header
    update_has_finalized_next_sync_committee = (
        not is_next_sync_committee_known(store)
        and is_sync_committee_update(update)
        and is_finality_update(update)
        and (
            compute_sync_committee_period_at_slot(update.finalized_header.beacon.slot)
            == compute_sync_committee_period_at_slot(update.attested_header.beacon.slot)
        )
    )
    if get_set_bit_count(sync_committee_bits) * 3 >= len(sync_committee_bits) * 2 and (
        update.finalized_header.beacon.slot > store.finalized_header.beacon.slot
        or update_has_finalized_next_sync_committee
    ):
        # Update bình thường khi đạt ngưỡng 2/3
        apply_light_client_update(store, update)
        store.best_valid_update = None
```

### `process_light_client_finality_update`

```python
def process_light_client_finality_update(
    store: LightClientStore,
    finality_update: LightClientFinalityUpdate,
    current_slot: Slot,
    genesis_validators_root: Root,
) -> None:
    update = LightClientUpdate(
        attested_header=finality_update.attested_header,
        next_sync_committee=SyncCommittee.empty(),
        next_sync_committee_branch=NextSyncCommitteeBranch(),
        finalized_header=finality_update.finalized_header,
        finality_branch=finality_update.finality_branch,
        sync_aggregate=finality_update.sync_aggregate,
        signature_slot=finality_update.signature_slot,
    )
    process_light_client_update(store, update, current_slot, genesis_validators_root)
```

### `process_light_client_optimistic_update`

```python
def process_light_client_optimistic_update(
    store: LightClientStore,
    optimistic_update: LightClientOptimisticUpdate,
    current_slot: Slot,
    genesis_validators_root: Root,
) -> None:
    update = LightClientUpdate(
        attested_header=optimistic_update.attested_header,
        next_sync_committee=SyncCommittee.empty(),
        next_sync_committee_branch=NextSyncCommitteeBranch(),
        finalized_header=LightClientHeader.empty(),
        finality_branch=FinalityBranch(),
        sync_aggregate=optimistic_update.sync_aggregate,
        signature_slot=optimistic_update.signature_slot,
    )
    process_light_client_update(store, update, current_slot, genesis_validators_root)
```
