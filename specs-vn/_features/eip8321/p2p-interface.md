# EIP-8321 -- Networking

*Lưu ý*: Tài liệu này vẫn đang trong quá trình soạn thảo, dành cho các nhà nghiên cứu và người triển khai (implementer).

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Helpers](#helpers)
  - [Modified `Seen`](#modified-seen)
  - [Modified `compute_fork_version`](#modified-compute_fork_version)
- [The gossip domain: gossipsub](#the-gossip-domain-gossipsub)
  - [Topics and messages](#topics-and-messages)
    - [Global topics](#global-topics)
      - [Modified `beacon_block`](#modified-beacon_block)
      - [New `randao_commitment_registration`](#new-randao_commitment_registration)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này chứa các đặc tả networking của tầng đồng thuận (consensus layer) cho EIP-8321.

Đặc tả các thay đổi này tiếp tục theo cùng định dạng với các đặc tả mạng của những bản nâng cấp trước, và coi chúng là điều kiện tiên quyết.

## Helpers

### Modified `Seen`

```python
@dataclass
class Seen:
    proposer_slots: set[tuple[Slot, ValidatorIndex]]
    aggregator_epochs: set[tuple[Epoch, ValidatorIndex]]
    aggregate_data_roots: dict[tuple[Root, CommitteeIndex], set[tuple[bool, ...]]]
    voluntary_exit_indices: set[ValidatorIndex]
    proposer_slashing_indices: set[ValidatorIndex]
    attester_slashing_indices: set[ValidatorIndex]
    attestation_validator_epochs: set[tuple[Epoch, ValidatorIndex]]
    sync_contribution_aggregator_slots: set[tuple[Slot, ValidatorIndex, Uint64]]
    sync_contribution_data: dict[tuple[Slot, Root, Uint64], set[tuple[bool, ...]]]
    sync_message_validator_slots: set[tuple[Slot, ValidatorIndex, Uint64]]
    bls_to_execution_change_indices: set[ValidatorIndex]
    data_column_sidecar_tuples: set[tuple[Root, ColumnIndex]]
    execution_payloads: dict[Hash32, ExecutionPayload]
    execution_payload_envelopes: set[tuple[Root, BuilderIndex]]
    payload_attestation_validators: set[tuple[Slot, ValidatorIndex]]
    execution_payload_bids: set[tuple[Slot, Hash32, Root, BuilderIndex]]
    best_execution_payload_bid: dict[tuple[Slot, Hash32, Root], Gwei]
    proposer_preferences: dict[tuple[Slot, Root], ProposerPreferences]
    inclusion_list_counts: Counter[tuple[Slot, Root, ValidatorIndex]]
    # [New in EIP8321]
    randao_commitment_registration_indices: set[ValidatorIndex]
```

> 💡 Ghi chú: Trường mới `randao_commitment_registration_indices` ghi lại các validator index đã có registration được gossip hợp lệ, dùng để bỏ qua (IGNORE) các bản trùng lặp.

### Modified `compute_fork_version`

```python
def compute_fork_version(epoch: Epoch) -> Version:
    """
    Return the fork version at the given ``epoch``.
    """
    if epoch >= EIP8321_FORK_EPOCH:
        return EIP8321_FORK_VERSION
    if epoch >= HEZE_FORK_EPOCH:
        return HEZE_FORK_VERSION
    if epoch >= GLOAS_FORK_EPOCH:
        return GLOAS_FORK_VERSION
    if epoch >= FULU_FORK_EPOCH:
        return FULU_FORK_VERSION
    if epoch >= ELECTRA_FORK_EPOCH:
        return ELECTRA_FORK_VERSION
    if epoch >= DENEB_FORK_EPOCH:
        return DENEB_FORK_VERSION
    if epoch >= CAPELLA_FORK_EPOCH:
        return CAPELLA_FORK_VERSION
    if epoch >= BELLATRIX_FORK_EPOCH:
        return BELLATRIX_FORK_VERSION
    if epoch >= ALTAIR_FORK_EPOCH:
        return ALTAIR_FORK_VERSION
    return GENESIS_FORK_VERSION
```

## The gossip domain: gossipsub

### Topics and messages

Các topic tuân theo cùng đặc tả như các bản nâng cấp trước. Mọi topic hiện có giữ nguyên, ngoại trừ topic beacon block, được cập nhật theo kiểu dữ liệu đã sửa đổi.

Topic mới, cùng với kiểu của trường `data` trong một gossipsub message, được cho trong bảng sau:

| Name                             | Message Type                         |
| -------------------------------- | ------------------------------------ |
| `beacon_block`                   | `SignedBeaconBlock` (modified)       |
| `randao_commitment_registration` | `SignedRandaoCommitmentRegistration` |

#### Global topics

EIP-8321 thay đổi kiểu của global topic beacon block và thêm một global topic để lan truyền các RANDAO commitment registration tới tất cả các proposer tiềm năng của beacon block.

##### Modified `beacon_block`

*Kiểu* của payload trong topic này đổi thành `SignedBeaconBlock` (đã sửa đổi) trong EIP-8321. Cụ thể, kiểu này thay đổi do bổ sung `hash_chain_reveal` và `randao_commitment_registrations` vào `BeaconBlockBody` bên trong. Xem [tài liệu state transition](./beacon-chain.md#beaconblockbody) của EIP-8321 để biết thêm chi tiết.

##### New `randao_commitment_registration`

Topic `randao_commitment_registration` chỉ được dùng để lan truyền các RANDAO commitment registration đã ký trên mạng. Các message đã ký được gửi nguyên vẹn.

```python
def validate_randao_commitment_registration_gossip(
    seen: Seen,
    store: Store,
    signed_registration: SignedRandaoCommitmentRegistration,
) -> None:
    """
    Validate a SignedRandaoCommitmentRegistration for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    registration = signed_registration.message
    index = registration.validator_index

    # [IGNORE] Đây là registration hợp lệ đầu tiên nhận được cho validator này
    if index in seen.randao_commitment_registration_indices:
        raise GossipIgnore("already seen RANDAO commitment registration for this validator")

    state = store.block_states[get_head(store).root]

    # [IGNORE] Head state đã được nâng cấp lên EIP-8321
    if state.fork.current_version < EIP8321_FORK_VERSION:
        raise GossipIgnore("head state is pre-eip8321")

    # [REJECT] Validator index hợp lệ
    if index >= len(state.validators):
        raise GossipReject("validator index out of range")

    # [REJECT] Commitment khác 0
    if registration.commitment == UNSET_RANDAO_COMMITMENT:
        raise GossipReject("commitment is zero")

    # [IGNORE] Validator chưa được đăng ký
    if state.randao_commitments[index] != UNSET_RANDAO_COMMITMENT:
        raise GossipIgnore("validator is already registered")

    # [IGNORE] Theo góc nhìn của node, validator không có registration nào đang chờ xử lý
    if any(pending.validator_index == index for pending in state.pending_randao_commitments):
        raise GossipIgnore("RANDAO commitment registration is already pending for this validator")

    # [REJECT] Signature hợp lệ
    domain = compute_domain(
        DOMAIN_RANDAO_COMMITMENT_REGISTRATION,
        genesis_validators_root=state.genesis_validators_root,
    )
    signing_root = compute_signing_root(registration, domain)
    if not bls.Verify(state.validators[index].pubkey, signing_root, signed_registration.signature):
        raise GossipReject("invalid RANDAO commitment registration signature")

    # Đánh dấu registration này là đã thấy
    seen.randao_commitment_registration_indices.add(index)
```

> 💡 Ghi chú: Tóm tắt các điều kiện kiểm tra theo thứ tự trong hàm trên:
>
> - [IGNORE] Đây là registration hợp lệ đầu tiên nhận được cho validator này (chưa có trong `seen.randao_commitment_registration_indices`).
> - [IGNORE] Head state đã nâng cấp lên EIP-8321.
> - [REJECT] Validator index hợp lệ (nhỏ hơn số validator trong state).
> - [REJECT] Commitment khác 0 (khác `UNSET_RANDAO_COMMITMENT`).
> - [IGNORE] Validator chưa đăng ký commitment.
> - [IGNORE] Theo góc nhìn của node, validator không có registration nào đang chờ trong `pending_randao_commitments`.
> - [REJECT] Chữ ký hợp lệ (domain được tính bằng `compute_domain` chỉ với `genesis_validators_root`, nên không phụ thuộc fork).
>
> Nếu qua hết các kiểm tra, registration được đánh dấu là đã thấy.
