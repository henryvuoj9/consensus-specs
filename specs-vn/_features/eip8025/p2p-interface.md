# EIP-8025 -- Networking

Tài liệu này mô tả đặc tả networking (tầng mạng P2P) cho EIP-8025.

*Lưu ý*: Đặc tả này được xây dựng dựa trên [Gloas](../../gloas/p2p-interface.md)
và import các kiểu proof từ [beacon-chain.md](./beacon-chain.md).

Các proof của EIP-8025 chỉ được lan truyền qua gossip. Không có giao thức
Req/Resp nào dành riêng cho EIP-8025.

## Table of contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Table of contents](#table-of-contents)
- [Constants](#constants)
  - [Type-specific SSZ bounds](#type-specific-ssz-bounds)
- [Helpers](#helpers)
  - [Modified `Seen`](#modified-seen)
- [The gossip domain: gossipsub](#the-gossip-domain-gossipsub)
  - [Topics and messages](#topics-and-messages)
    - [Global topics](#global-topics)
      - [New `execution_proof`](#new-execution_proof)
- [The discovery domain: discv5](#the-discovery-domain-discv5)
  - [ENR structure](#enr-structure)
    - [Execution proof awareness](#execution-proof-awareness)

<!-- mdformat-toc end -->

## Constants

### Type-specific SSZ bounds

*(Giới hạn kích thước SSZ cho từng kiểu dữ liệu cụ thể)*

| Name                                       | Value             |
| ------------------------------------------ | ----------------- |
| `MAX_SIGNED_EXECUTION_PROOF_ENVELOPE_SIZE` | `Uint64(4194449)` |

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
    # [New in EIP8025]
    execution_proof_roots: dict[Root, set[Root]]
    # [New in EIP8025]
    execution_proof_provers: set[tuple[Root, ProofType, ValidatorIndex]]
```

> 💡 Ghi chú: `execution_proof_roots` lưu, theo từng beacon block root, tập các
> root của proof envelope đã xử lý (để loại bỏ trùng lặp). `execution_proof_provers`
> ghi nhận mỗi bộ (beacon block root, proof type, validator index) đã gửi proof,
> để mỗi prover chỉ được gửi một proof cho mỗi block và mỗi proof type.

## The gossip domain: gossipsub

### Topics and messages

#### Global topics

##### New `execution_proof`

Topic này được dùng để lan truyền các message `SignedExecutionProofEnvelope`.

```python
def validate_execution_proof_gossip(
    seen: Seen,
    store: Store,
    signed_proof_envelope: SignedExecutionProofEnvelope,
    proof_engine: ProofEngine,
) -> None:
    """
    Validate a SignedExecutionProofEnvelope for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    proof_envelope = signed_proof_envelope.message

    # [REJECT] Dữ liệu proof không được rỗng
    if len(proof_envelope.proof_data) == 0:
        raise GossipReject("execution proof is empty")

    # [REJECT] Proof type phải được hỗ trợ
    if proof_envelope.proof_type not in get_supported_proof_types():
        raise GossipReject("unexpected execution proof type")

    beacon_block_root = proof_envelope.beacon_block_root

    # [IGNORE] Beacon block tương ứng với proof đã được nhìn thấy
    if beacon_block_root not in store.blocks:
        raise GossipIgnore("execution proof's beacon block has not been seen")

    # [IGNORE] Chưa có proof hợp lệ nào được biết cho beacon block và proof type này
    if proof_envelope.proof_type in store.execution_proofs.get(beacon_block_root, {}):
        raise GossipIgnore("verified proof already known for this beacon block and proof type")

    proof_root = hash_tree_root(proof_envelope)

    # [IGNORE] Proof này chưa từng được xử lý trước đó
    if proof_root in seen.execution_proof_roots.get(beacon_block_root, set()):
        raise GossipIgnore("execution proof has already been processed")

    # [IGNORE] Đây là proof đầu tiên (dù hợp lệ hay không) của prover cho key này
    validator_index = signed_proof_envelope.validator_index
    prover_key = (beacon_block_root, proof_envelope.proof_type, validator_index)
    if prover_key in seen.execution_proof_provers:
        raise GossipIgnore(
            "proof already seen from this prover for this beacon block and proof type"
        )

    # [IGNORE] Execution payload tương ứng với proof đã có sẵn (available)
    if beacon_block_root not in store.payloads:
        raise GossipIgnore("execution proof's payload is unavailable")

    state = store.block_states[beacon_block_root]
    payload_envelope = store.payloads[beacon_block_root]

    # [REJECT] Execution proof envelope vượt qua bước kiểm tra hợp lệ
    try:
        verify_execution_proof_envelope(state, signed_proof_envelope)
    except AssertionError:
        raise GossipReject("execution proof envelope is invalid") from None

    proof = get_execution_proof(
        state,
        proof_envelope,
        payload_envelope,
    )

    # Đánh dấu proof đã được xác thực và lượt gửi của prover là đã thấy
    if beacon_block_root not in seen.execution_proof_roots:
        seen.execution_proof_roots[beacon_block_root] = set()
    seen.execution_proof_roots[beacon_block_root].add(proof_root)
    seen.execution_proof_provers.add(prover_key)

    # [REJECT] Execution proof phải hợp lệ
    if not proof_engine.verify_execution_proof(proof):
        raise GossipReject("execution proof is invalid")
```

> 💡 Ghi chú: Thứ tự kiểm tra được sắp xếp để các bước rẻ (kiểm tra rỗng, proof
> type, block/payload đã có hay chưa, trùng lặp) chạy trước, còn bước tốn kém
> nhất là xác minh proof qua `proof_engine` chạy cuối cùng. Proof và prover được
> đánh dấu "đã thấy" *trước* khi xác minh proof, nên một prover gửi proof không
> hợp lệ cũng sẽ không thể gửi lại proof khác cho cùng block và proof type.

## The discovery domain: discv5

### ENR structure

#### Execution proof awareness

Một field mới được thêm vào ENR với key `eproof` nhằm hỗ trợ việc discovery và
kết nối peer giữa các node tham gia gossip execution proof.

| Key      | Value                                    |
| -------- | ---------------------------------------- |
| `eproof` | Execution layer proof awareness, `Uint8` |

Một node được coi là execution proof-aware (nhận biết execution proof) nếu key
`eproof` có mặt và giá trị của nó khác `0`. Một node execution proof-aware sẽ
subscribe topic gossip `execution_proof` và thực thi các quy tắc kiểm tra hợp lệ
của topic đó. Client MAY (CÓ THỂ) ưu tiên các node execution proof-aware khi chọn
peer cho gossip execution proof.
