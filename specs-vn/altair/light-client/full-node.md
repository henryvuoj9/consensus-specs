# Altair Light Client -- Full Node

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Helpers](#helpers)
  - [`compute_merkle_proof`](#compute_merkle_proof)
  - [`block_to_light_client_header`](#block_to_light_client_header)
- [Deriving light client data](#deriving-light-client-data)
  - [`create_light_client_bootstrap`](#create_light_client_bootstrap)
  - [`create_light_client_update`](#create_light_client_update)
  - [`create_light_client_finality_update`](#create_light_client_finality_update)
  - [`create_light_client_optimistic_update`](#create_light_client_optimistic_update)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này cung cấp các hàm hỗ trợ (helper function) giúp full node có thể
phục vụ dữ liệu cho light client (client nhẹ). Full node SHOULD (NÊN) triển khai
các chức năng được mô tả ở đây để light client có thể sync với mạng.

> 💡 Ghi chú: Light client không lưu toàn bộ beacon state mà chỉ theo dõi các
> block header và sync committee. Vì vậy chúng phụ thuộc vào full node để nhận
> các đối tượng dữ liệu đã được tính sẵn kèm Merkle proof.

## Helpers

### `compute_merkle_proof`

Hàm này trả về Merkle proof của đối tượng SSZ `object` tại generalized index
(chỉ số tổng quát trong cây Merkle) `index`.

```python
def compute_merkle_proof(object: SSZObject, index: GeneralizedIndex) -> Sequence[Bytes32]: ...
```

### `block_to_light_client_header`

```python
def block_to_light_client_header(block: SignedBeaconBlock) -> LightClientHeader:
    return LightClientHeader(
        beacon=BeaconBlockHeader(
            slot=block.message.slot,
            proposer_index=block.message.proposer_index,
            parent_root=block.message.parent_root,
            state_root=block.message.state_root,
            body_root=hash_tree_root(block.message.body),
        ),
    )
```

## Deriving light client data

Full node được kỳ vọng sẽ tạo ra (derive) dữ liệu light client từ các block và
state trong lịch sử, rồi cung cấp dữ liệu đó cho các client khác.

### `create_light_client_bootstrap`

Để tạo một `LightClientBootstrap`, cần có các đối tượng sau:

- `state`: post state (state sau khi xử lý) của bất kỳ block nào sau Altair
- `block`: block tương ứng với state đó

```python
def create_light_client_bootstrap(
    state: BeaconState, block: SignedBeaconBlock
) -> LightClientBootstrap:
    assert compute_epoch_at_slot(state.slot) >= ALTAIR_FORK_EPOCH

    assert state.slot == state.latest_block_header.slot
    header = state.latest_block_header.copy()
    header.state_root = hash_tree_root(state)
    assert hash_tree_root(header) == hash_tree_root(block.message)

    return LightClientBootstrap(
        header=block_to_light_client_header(block),
        current_sync_committee=state.current_sync_committee,
        current_sync_committee_branch=CurrentSyncCommitteeBranch(
            data=compute_merkle_proof(state, current_sync_committee_gindex_at_slot(state.slot))
        ),
    )
```

Full node SHOULD cung cấp `LightClientBootstrap` cho tất cả các epoch boundary
block (block ranh giới epoch) đã finalized trong khoảng epoch
`[max(ALTAIR_FORK_EPOCH, current_epoch - compute_min_epochs_for_block_requests()), current_epoch]`,
trong đó `current_epoch` được xác định theo thời gian thực (wall-clock) hiện tại.
Full node MAY (CÓ THỂ) cung cấp thêm `LightClientBootstrap` cho các block khác.

Một block được coi là epoch boundary block nếu block root của nó có thể xuất
hiện trong một `Checkpoint` hợp lệ, tức là: slot của block là slot đầu tiên của
một epoch, hoặc mọi slot tiếp theo cho tới slot đầu tiên của epoch kế tiếp đều
trống (không có block nào được đề xuất / block bị orphaned).

`LightClientBootstrap` được tính từ post state ngay sau block đó (không áp dụng
thêm các slot trống).

### `create_light_client_update`

Để tạo một `LightClientUpdate`, cần các state và block lịch sử sau:

- `state`: post state của bất kỳ block nào có parent block thuộc giai đoạn sau
  Altair
- `block`: block tương ứng
- `attested_state`: post state của `attested_block`
- `attested_block`: block được tham chiếu bởi `block.parent_root`
- `finalized_block`: block được tham chiếu bởi
  `attested_state.finalized_checkpoint.root`, nếu có sẵn cục bộ (có thể không
  có, ví dụ khi dùng checkpoint sync, hoặc khi block đó đã bị prune (xóa bớt)
  cục bộ)

> 💡 Ghi chú: `block` chứa `sync_aggregate` — chữ ký của sync committee ký lên
> block cha (`attested_block`). Vì vậy header được "chứng thực" (attested) là
> header của block cha, còn `signature_slot` là slot của `block`.

```python
def create_light_client_update(
    state: BeaconState,
    block: SignedBeaconBlock,
    attested_state: BeaconState,
    attested_block: SignedBeaconBlock,
    finalized_block: SignedBeaconBlock | None,
) -> LightClientUpdate:
    assert compute_epoch_at_slot(attested_state.slot) >= ALTAIR_FORK_EPOCH
    assert (
        get_set_bit_count(block.message.body.sync_aggregate.sync_committee_bits)
        >= MIN_SYNC_COMMITTEE_PARTICIPANTS
    )

    assert state.slot == state.latest_block_header.slot
    header = state.latest_block_header.copy()
    header.state_root = hash_tree_root(state)
    assert hash_tree_root(header) == hash_tree_root(block.message)
    update_signature_period = compute_sync_committee_period_at_slot(block.message.slot)

    assert attested_state.slot == attested_state.latest_block_header.slot
    attested_header = attested_state.latest_block_header.copy()
    attested_header.state_root = hash_tree_root(attested_state)
    assert (
        hash_tree_root(attested_header)
        == hash_tree_root(attested_block.message)
        == block.message.parent_root
    )
    update_attested_period = compute_sync_committee_period_at_slot(attested_block.message.slot)

    update = LightClientUpdate.empty()

    update.attested_header = block_to_light_client_header(attested_block)

    # `next_sync_committee` chỉ hữu ích nếu message được ký bởi sync committee hiện tại
    if update_attested_period == update_signature_period:
        update.next_sync_committee = attested_state.next_sync_committee
        update.next_sync_committee_branch = NextSyncCommitteeBranch(
            data=compute_merkle_proof(
                attested_state,
                next_sync_committee_gindex_at_slot(attested_state.slot),
            )
        )

    # Thể hiện finality bất cứ khi nào có thể
    if finalized_block is not None:
        if finalized_block.message.slot != GENESIS_SLOT:
            update.finalized_header = block_to_light_client_header(finalized_block)
            assert (
                hash_tree_root(update.finalized_header.beacon)
                == attested_state.finalized_checkpoint.root
            )
        else:
            assert attested_state.finalized_checkpoint.root == Bytes32()
        update.finality_branch = FinalityBranch(
            data=compute_merkle_proof(
                attested_state,
                finalized_root_gindex_at_slot(attested_state.slot),
            )
        )

    update.sync_aggregate = block.message.body.sync_aggregate
    update.signature_slot = block.message.slot

    return update
```

Full node SHOULD cung cấp `LightClientUpdate` tốt nhất có thể tạo ra được (theo
tiêu chí của `is_better_update`) cho mỗi sync committee period bao phủ bất kỳ
epoch nào trong khoảng
`[max(ALTAIR_FORK_EPOCH, current_epoch - compute_min_epochs_for_block_requests()), current_epoch]`,
trong đó `current_epoch` được xác định theo thời gian thực hiện tại. Full node
MAY cung cấp thêm `LightClientUpdate` cho các sync committee period khác.

- Các `LightClientUpdate` được gán vào sync committee period dựa trên
  `attested_header.beacon.slot` của chúng
- Chỉ xét các `LightClientUpdate` thỏa mãn
  `compute_sync_committee_period_at_slot(update.attested_header.beacon.slot) == compute_sync_committee_period_at_slot(update.signature_slot)`
- Chỉ xét các `LightClientUpdate` có `sync_aggregate` lấy từ các block nằm trên
  canonical chain (chuỗi chính tắc) do fork choice chọn, bất kể thứ hạng theo
  `is_better_update` ra sao. Các `LightClientUpdate` tham chiếu tới block bị
  orphaned SHOULD NOT (KHÔNG NÊN) được cung cấp.

### `create_light_client_finality_update`

```python
def create_light_client_finality_update(update: LightClientUpdate) -> LightClientFinalityUpdate:
    return LightClientFinalityUpdate(
        attested_header=update.attested_header,
        finalized_header=update.finalized_header,
        finality_branch=update.finality_branch,
        sync_aggregate=update.sync_aggregate,
        signature_slot=update.signature_slot,
    )
```

Full node SHOULD cung cấp `LightClientFinalityUpdate` có
`attested_header.beacon.slot` cao nhất (nếu có nhiều cái bằng nhau thì chọn cái
có `signature_slot` cao nhất) theo lựa chọn của fork choice, và SHOULD hỗ trợ cơ
chế push (đẩy chủ động) để gửi `LightClientFinalityUpdate` mới mỗi khi
`finalized_header` thay đổi. Nếu `LightClientFinalityUpdate` đó chưa đạt mức
tham gia supermajority (> 2/3) của sync committee, thì một
`LightClientFinalityUpdate` thứ hai SHOULD được gửi cho cùng `finalized_header`
đó ngay khi đạt được mức tham gia supermajority.

### `create_light_client_optimistic_update`

```python
def create_light_client_optimistic_update(update: LightClientUpdate) -> LightClientOptimisticUpdate:
    return LightClientOptimisticUpdate(
        attested_header=update.attested_header,
        sync_aggregate=update.sync_aggregate,
        signature_slot=update.signature_slot,
    )
```

Full node SHOULD cung cấp `LightClientOptimisticUpdate` có
`attested_header.beacon.slot` cao nhất (nếu có nhiều cái bằng nhau thì chọn cái
có `signature_slot` cao nhất) theo lựa chọn của fork choice, và SHOULD hỗ trợ cơ
chế push để gửi `LightClientOptimisticUpdate` mới mỗi khi `attested_header` thay
đổi.
