# Capella -- Networking

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Helpers](#helpers)
  - [Modified `Seen`](#modified-seen)
  - [Modified `compute_fork_version`](#modified-compute_fork_version)
- [The gossip domain: gossipsub](#the-gossip-domain-gossipsub)
  - [Topics and messages](#topics-and-messages)
    - [Global topics](#global-topics)
      - [Modified `beacon_block`](#modified-beacon_block)
      - [New `bls_to_execution_change`](#new-bls_to_execution_change)
  - [Transitioning the gossip](#transitioning-the-gossip)
- [The Req/Resp domain](#the-reqresp-domain)
  - [Messages](#messages)
    - [BeaconBlocksByRange v2](#beaconblocksbyrange-v2)
    - [BeaconBlocksByRoot v2](#beaconblocksbyroot-v2)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này chứa đặc tả networking của consensus layer cho Capella.

Đặc tả các thay đổi này tiếp tục theo cùng định dạng với đặc tả networking của
các bản nâng cấp trước, và coi các đặc tả đó là điều kiện tiên quyết (tức là chỉ
mô tả những gì thay đổi; phần còn lại được kế thừa nguyên vẹn).

## Helpers

### Modified `Seen`

*(Bổ sung tập `bls_to_execution_change_indices` để ghi nhớ các validator đã có
message BLS-to-execution change được thấy trên gossip)*

```python
@dataclass
class Seen:
    proposer_slots: set[tuple[Slot, ValidatorIndex]]
    aggregator_epochs: set[tuple[Epoch, ValidatorIndex]]
    aggregate_data_roots: dict[Root, set[tuple[bool, ...]]]
    voluntary_exit_indices: set[ValidatorIndex]
    proposer_slashing_indices: set[ValidatorIndex]
    attester_slashing_indices: set[ValidatorIndex]
    attestation_validator_epochs: set[tuple[Epoch, ValidatorIndex]]
    sync_contribution_aggregator_slots: set[tuple[Slot, ValidatorIndex, Uint64]]
    sync_contribution_data: dict[tuple[Slot, Root, Uint64], set[tuple[bool, ...]]]
    sync_message_validator_slots: set[tuple[Slot, ValidatorIndex, Uint64]]
    # [New in Capella]
    bls_to_execution_change_indices: set[ValidatorIndex]
```

### Modified `compute_fork_version`

```python
def compute_fork_version(epoch: Epoch) -> Version:
    """
    Return the fork version at the given ``epoch``.
    """
    if epoch >= CAPELLA_FORK_EPOCH:
        return CAPELLA_FORK_VERSION
    if epoch >= BELLATRIX_FORK_EPOCH:
        return BELLATRIX_FORK_VERSION
    if epoch >= ALTAIR_FORK_EPOCH:
        return ALTAIR_FORK_VERSION
    return GENESIS_FORK_VERSION
```

## The gossip domain: gossipsub

Một topic mới được thêm vào để hỗ trợ gossip các message thay đổi withdrawal
credential (thông tin xác định địa chỉ nhận tiền rút). Đồng thời, một topic hiện
có được nâng cấp để dùng các kiểu dữ liệu đã cập nhật trong Capella.

### Topics and messages

Các topic tuân theo cùng đặc tả như ở các bản nâng cấp trước. Mọi topic hiện có
đều giữ nguyên, ngoại trừ topic beacon block được cập nhật với kiểu dữ liệu đã
sửa đổi.

Các topic mới cùng với kiểu của trường `data` trong message gossipsub được liệt
kê trong bảng sau:

| Name                      | Message Type                   |
| ------------------------- | ------------------------------ |
| `beacon_block`            | `SignedBeaconBlock` (modified) |
| `bls_to_execution_change` | `SignedBLSToExecutionChange`   |

Lưu ý rằng đoạn `ForkDigestValue` trong đường dẫn topic giúp phân tách topic
`beacon_block` cũ và mới (hai topic có fork digest khác nhau nên là hai topic
riêng biệt).

#### Global topics

Capella thay đổi kiểu dữ liệu của topic beacon block toàn cục và thêm một topic
toàn cục để lan truyền các message thay đổi withdrawal credential đến tất cả các
proposer tiềm năng của beacon block.

##### Modified `beacon_block`

*Kiểu* của payload trên topic này đổi thành `SignedBeaconBlock` (đã sửa đổi) của
Capella. Cụ thể, kiểu này thay đổi do có thêm trường `bls_to_execution_changes`
trong `BeaconBlockBody` bên trong. Xem
[tài liệu state transition](./beacon-chain.md#beaconblockbody) của Capella để
biết thêm chi tiết.

*Lưu ý*: `is_execution_enabled` bị loại bỏ trong Capella vì execution luôn được
bật vô điều kiện sau The Merge, mà The Merge xảy ra trước Capella.

```python
def validate_beacon_block_gossip(
    seen: Seen,
    store: Store,
    signed_beacon_block: SignedBeaconBlock,
    current_time_ms: Uint64,
    block_payload_statuses: dict[Root, PayloadValidationStatus],
) -> None:
    """
    Validate a SignedBeaconBlock for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    block = signed_beacon_block.message
    execution_payload = block.body.execution_payload

    # [IGNORE] Block là block đầu tiên có chữ ký hợp lệ nhận được cho cặp (slot, proposer) này
    proposer_slot_key = (block.slot, block.proposer_index)
    if proposer_slot_key in seen.proposer_slots:
        raise GossipIgnore("block is not the first valid block for this slot and proposer")

    # [IGNORE] Block không thuộc một slot trong tương lai
    # (MAY được đưa vào hàng đợi để xử lý khi đến slot phù hợp)
    if is_future_slot(store, block.slot, current_time_ms):
        raise GossipIgnore("block is from a future slot")

    # [IGNORE] Block thuộc slot lớn hơn slot finalized mới nhất
    # (MAY chọn validate và lưu trữ các block như vậy cho mục đích khác
    # -- ví dụ: phát hiện slashing, archive node, v.v.)
    finalized_slot = compute_start_slot_at_epoch(store.finalized_checkpoint.epoch)
    if block.slot <= finalized_slot:
        raise GossipIgnore("block is not from a slot greater than the latest finalized slot")

    # [IGNORE] Block cha đã được thấy (qua gossip hoặc nguồn khác ngoài gossip)
    # (MAY được đưa vào hàng đợi cho đến khi lấy được block cha)
    if block.parent_root not in store.blocks:
        raise GossipIgnore("block's parent has not been seen")

    parent_payload_status = PAYLOAD_STATUS_NOT_VALIDATED
    if block.parent_root in block_payload_statuses:
        parent_payload_status = block_payload_statuses[block.parent_root]

    if block.parent_root not in store.block_states:
        if parent_payload_status == PAYLOAD_STATUS_NOT_VALIDATED:
            # [REJECT] Block cha không qua được validation và execution payload của nó đang ở trạng thái optimistic
            raise GossipReject("block's parent is invalid and its payload is optimistic")

        # [IGNORE] Block cha không qua được validation và execution payload của nó đã được xử lý
        raise GossipIgnore("block's parent is invalid and its payload is processed")

    # [IGNORE] Block cha qua được validation nhưng execution payload của nó không hợp lệ
    if parent_payload_status == PAYLOAD_STATUS_INVALIDATED:
        raise GossipIgnore("block's parent is valid and its payload is invalid")

    state = store.block_states[get_head(store).root]

    # [REJECT] Proposer index là một validator index hợp lệ
    if block.proposer_index >= len(state.validators):
        raise GossipReject("proposer index out of range")

    # [REJECT] Chữ ký của proposer hợp lệ
    proposer = state.validators[block.proposer_index]
    domain = get_domain(state, DOMAIN_BEACON_PROPOSER, compute_epoch_at_slot(block.slot))
    signing_root = compute_signing_root(block, domain)
    if not bls.Verify(proposer.pubkey, signing_root, signed_beacon_block.signature):
        raise GossipReject("invalid proposer signature")

    # [REJECT] Timestamp của execution payload trong block khớp với thời điểm của slot
    if execution_payload.timestamp != compute_time_at_slot(state.genesis_time, block.slot):
        raise GossipReject("incorrect execution payload timestamp")

    # [REJECT] Block thuộc slot cao hơn slot của block cha
    if block.slot <= store.blocks[block.parent_root].slot:
        raise GossipReject("block is not from a higher slot than its parent")

    # [REJECT] Finalized checkpoint hiện tại là tổ tiên (ancestor) của block
    finalized_epoch = store.finalized_checkpoint.epoch
    finalized_checkpoint_block = get_checkpoint_block(store, block.parent_root, finalized_epoch)
    if finalized_checkpoint_block != store.finalized_checkpoint.root:
        raise GossipReject("finalized checkpoint is not an ancestor of block")

    # [REJECT] Block được đề xuất bởi đúng proposer dự kiến của slot
    # (nếu chưa có dữ liệu shuffling thì IGNORE thay vì REJECT, và MAY đưa vào hàng đợi để xử lý sau)
    parent_state = store.block_states[block.parent_root].copy()
    process_slots(parent_state, block.slot)
    expected_proposer = get_beacon_proposer_index(parent_state)
    if block.proposer_index != expected_proposer:
        raise GossipReject("block proposer_index does not match expected proposer")

    # Đánh dấu block này là đã thấy
    seen.proposer_slots.add(proposer_slot_key)
```

> 💡 Ghi chú: Điểm khác biệt chính so với Bellatrix là không còn kiểm tra
> `is_execution_enabled`: mọi block từ Capella trở đi đều có execution payload,
> nên điều kiện về timestamp của execution payload luôn được áp dụng. Quy ước
> chung: `[IGNORE]` nghĩa là bỏ qua message (không lan truyền, nhưng không phạt
> peer), còn `[REJECT]` nghĩa là message chắc chắn không hợp lệ (không lan truyền
> và có thể hạ điểm peer gửi).

##### New `bls_to_execution_change`

Topic `bls_to_execution_change` chỉ được dùng để lan truyền các message BLS to
execution change đã được ký trên mạng. Các message đã ký được gửi nguyên vẹn
(toàn bộ message cùng chữ ký).

```python
def validate_bls_to_execution_change_gossip(
    seen: Seen,
    store: Store,
    signed_bls_to_execution_change: SignedBLSToExecutionChange,
    current_time_ms: Uint64,
) -> None:
    """
    Validate a SignedBLSToExecutionChange for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    bls_to_execution_change = signed_bls_to_execution_change.message
    validator_index = bls_to_execution_change.validator_index

    # [IGNORE] Đây là bls_to_execution_change hợp lệ đầu tiên nhận được cho validator này
    if validator_index in seen.bls_to_execution_change_indices:
        raise GossipIgnore("already seen BLS to execution change for this validator")

    # [IGNORE] Epoch hiện tại bằng hoặc sau fork epoch của Capella
    if is_future_epoch(store, CAPELLA_FORK_EPOCH, current_time_ms):
        raise GossipIgnore("current epoch is pre-capella")

    state = store.block_states[get_head(store).root]

    # [REJECT] Validator index hợp lệ
    if validator_index >= len(state.validators):
        raise GossipReject("validator index out of range")

    validator = state.validators[validator_index]

    # [REJECT] Validator đang có withdrawal credentials kiểu BLS
    if validator.withdrawal_credentials[:1] != BLS_WITHDRAWAL_PREFIX:
        raise GossipReject("validator does not have BLS withdrawal credentials")

    # [REJECT] bls_to_execution_change dùng đúng withdrawal pubkey của validator
    pubkey = bls_to_execution_change.from_bls_pubkey
    if validator.withdrawal_credentials[1:] != sha256(pubkey)[1:]:
        raise GossipReject("pubkey does not match validator withdrawal credentials")

    # [REJECT] Chữ ký hợp lệ
    domain = compute_domain(
        DOMAIN_BLS_TO_EXECUTION_CHANGE, genesis_validators_root=state.genesis_validators_root
    )
    signing_root = compute_signing_root(bls_to_execution_change, domain)
    if not bls.Verify(pubkey, signing_root, signed_bls_to_execution_change.signature):
        raise GossipReject("invalid BLS to execution change signature")

    # Đánh dấu bls_to_execution_change này là đã thấy
    seen.bls_to_execution_change_indices.add(validator_index)
```

> 💡 Ghi chú: Withdrawal credentials kiểu BLS có dạng
> `BLS_WITHDRAWAL_PREFIX || sha256(pubkey)[1:]`, vì vậy việc so sánh
> `withdrawal_credentials[1:]` với `sha256(pubkey)[1:]` xác nhận rằng
> `from_bls_pubkey` chính là withdrawal public key đã cam kết lúc deposit. Lưu ý
> domain được tính bằng `compute_domain` với `genesis_validators_root` và không
> truyền fork version, nên chữ ký vẫn hợp lệ qua các fork sau này.

### Transitioning the gossip

Xem chi tiết về việc chuyển đổi gossip trong
[tài liệu Altair](../altair/p2p-interface.md#transitioning-the-gossip) để biết
cách xử lý việc chuyển đổi các gossip topic khi sang Capella.

## The Req/Resp domain

### Messages

#### BeaconBlocksByRange v2

**Protocol ID:** `/eth2/beacon_chain/req/beacon_blocks_by_range/2/`

Fork digest của Capella được bổ sung vào enum `context` để chỉ định kiểu block
của Capella.

<!-- eth_consensus_specs: skip -->

| `fork_version`           | Chunk SSZ type                |
| ------------------------ | ----------------------------- |
| `GENESIS_FORK_VERSION`   | `phase0.SignedBeaconBlock`    |
| `ALTAIR_FORK_VERSION`    | `altair.SignedBeaconBlock`    |
| `BELLATRIX_FORK_VERSION` | `bellatrix.SignedBeaconBlock` |
| `CAPELLA_FORK_VERSION`   | `capella.SignedBeaconBlock`   |

#### BeaconBlocksByRoot v2

**Protocol ID:** `/eth2/beacon_chain/req/beacon_blocks_by_root/2/`

Fork digest của Capella được bổ sung vào enum `context` để chỉ định kiểu block
của Capella.

<!-- eth_consensus_specs: skip -->

| `fork_version`           | Chunk SSZ type                |
| ------------------------ | ----------------------------- |
| `GENESIS_FORK_VERSION`   | `phase0.SignedBeaconBlock`    |
| `ALTAIR_FORK_VERSION`    | `altair.SignedBeaconBlock`    |
| `BELLATRIX_FORK_VERSION` | `bellatrix.SignedBeaconBlock` |
| `CAPELLA_FORK_VERSION`   | `capella.SignedBeaconBlock`   |
