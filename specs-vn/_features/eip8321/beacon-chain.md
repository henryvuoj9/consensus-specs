# EIP-8321 -- The Beacon Chain

*Lưu ý*: Tài liệu này vẫn đang trong quá trình soạn thảo, dành cho các nhà nghiên cứu và người triển khai (implementer).

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Types](#types)
  - [New `PendingRandaoCommitments`](#new-pendingrandaocommitments)
  - [New `RandaoCommitmentRegistrations`](#new-randaocommitmentregistrations)
  - [New `RandaoCommitments`](#new-randaocommitments)
- [Constants](#constants)
  - [Domains](#domains)
  - [Hash chain](#hash-chain)
- [Presets](#presets)
  - [Hash-chain RANDAO](#hash-chain-randao)
- [Containers](#containers)
  - [New containers](#new-containers)
    - [`PendingRandaoCommitment`](#pendingrandaocommitment)
    - [`RandaoCommitmentRegistration`](#randaocommitmentregistration)
    - [`SignedRandaoCommitmentRegistration`](#signedrandaocommitmentregistration)
  - [Modified containers](#modified-containers)
    - [`BeaconBlockBody`](#beaconblockbody)
    - [`BeaconState`](#beaconstate)
- [Helpers](#helpers)
  - [Crypto](#crypto)
    - [New `blake3`](#new-blake3)
  - [Validator registry](#validator-registry)
    - [Modified `add_validator_to_registry`](#modified-add_validator_to_registry)
  - [RANDAO verifications](#randao-verifications)
    - [New `verify_hash_chain_reveal`](#new-verify_hash_chain_reveal)
    - [New `verify_bls_randao_reveal`](#new-verify_bls_randao_reveal)
- [Beacon chain state transition function](#beacon-chain-state-transition-function)
  - [Epoch processing](#epoch-processing)
    - [Modified `process_epoch`](#modified-process_epoch)
    - [New `process_pending_randao_commitments`](#new-process_pending_randao_commitments)
  - [Block processing](#block-processing)
    - [Modified `process_randao`](#modified-process_randao)
    - [Operations](#operations)
      - [Modified `process_operations`](#modified-process_operations)
      - [RANDAO commitment registrations](#randao-commitment-registrations)
        - [New `process_randao_commitment_registration`](#new-process_randao_commitment_registration)

<!-- mdformat-toc end -->

## Introduction

Bản nâng cấp này thay thế cơ chế RANDAO reveal dựa trên chữ ký BLS bằng một cơ chế commit-reveal dựa trên hash chain (chuỗi băm), như một phần của bản nâng cấp EIP-8321.

Hiện tại, khả năng chống grinding (thử đi thử lại nhiều giá trị để thao túng kết quả) của RANDAO dựa vào tính *duy nhất* của chữ ký BLS: với mỗi epoch, proposer chỉ có đúng một chữ ký hợp lệ, nên không thể làm lệch phần đóng góp của mình. Thay vào đó, hash chain chỉ dựa vào các tính chất an toàn tiêu chuẩn của hàm băm: tính kháng va chạm (collision resistance) đảm nhận vai trò của tính duy nhất trong BLS, còn tính kháng tìm tiền ảnh (preimage resistance) giữ cho mỗi reveal không thể đoán trước cho đến khi nó được công bố. Cả hai tính chất này được cho là vẫn đứng vững trước một đối thủ có máy tính lượng tử.

Mỗi validator tự sinh một hash chain off-chain và đăng ký phần tử đầu mút (tip) của chain đó làm commitment. Khi đề xuất block, validator reveal tiền ảnh (preimage) của commitment đang được lưu cho mình; state kiểm tra bước băm của chain, trộn (fold) preimage thô vào bộ tích lũy RANDAO, rồi lưu preimage đó làm commitment mới của validator. Do đó state chỉ cần giữ một word 32 byte cho mỗi validator, và mỗi lần đề xuất block thì lùi lại đúng một mắt xích (link) trên chain.

> 💡 Ghi chú: Nói cách khác, chain có dạng `c_0 -> c_1 = H(c_0) -> ... -> c_n = H(c_{n-1})`. Validator công bố `c_n` làm commitment, rồi lần lượt reveal `c_{n-1}`, `c_{n-2}`, ... Ai cũng kiểm tra được `H(reveal) == commitment`, nhưng không ai (kể cả máy tính lượng tử, theo giả định) tính ngược được reveal kế tiếp trước khi validator công bố nó.

Một commitment được đăng ký đúng một lần, thông qua một beacon operation mới có giới hạn số lượng trên mỗi block. Nó không thể được cập nhật tại chỗ, và một validator index giữ commitment của mình chừng nào index đó còn tồn tại; vì vậy ràng buộc là: một chain ↔ một public key ↔ một validator index. Một validator nếu cần một chain mới thì phải làm theo đúng cách nó khôi phục khi mất signing key: onboard một validator mới dưới một public key mới. Các validator chưa đăng ký commitment tiếp tục dùng BLS reveal kiểu cũ (legacy); đây là con đường chuyển tiếp, dự kiến sẽ bị loại bỏ trong một bản nâng cấp sau.

*Lưu ý*: Các trường của deposit contract là cố định và không có chỗ chứa commitment, nên một validator mới không thể đặt commitment ngay lúc deposit; nó phải đăng ký thông qua operation của bản nâng cấp này giống như mọi validator khác. Việc đặt commitment ngay tại thời điểm deposit được hoãn lại cho một fork vốn đã cần thay đổi luồng deposit, chẳng hạn fork loại bỏ con đường chữ ký BLS chuyển tiếp để chuyển sang một cơ chế post-quantum. Việc loại bỏ con đường đó cũng sẽ cần một cách để buộc các validator đã onboard nhưng chưa bao giờ đăng ký phải đăng ký, ví dụ bằng cách không chấp nhận block từ họ nữa; bản nâng cấp này không đặc tả cơ chế đó.

*Lưu ý*: Đặc tả này được xây dựng dựa trên [Heze](../../heze/beacon-chain.md).

## Types

### New `PendingRandaoCommitments`

```python
class PendingRandaoCommitments(ProgressiveList[PendingRandaoCommitment]):
    """
    The queue of hash-chain RANDAO commitments awaiting activation.
    """
```

### New `RandaoCommitmentRegistrations`

```python
class RandaoCommitmentRegistrations(ProgressiveList[SignedRandaoCommitmentRegistration]):
    """
    The signed hash-chain RANDAO commitment registrations included in a beacon
    block.
    """
```

### New `RandaoCommitments`

```python
class RandaoCommitments(ProgressiveList[Bytes32]):
    """
    The current hash-chain RANDAO commitment of every validator. A zero entry
    means that the validator has not registered a commitment and reveals with
    the legacy BLS signature instead.
    """
```

## Constants

### Domains

| Name                                    | Value                      |
| --------------------------------------- | -------------------------- |
| `DOMAIN_RANDAO_COMMITMENT_REGISTRATION` | `DomainType("0x11000000")` |

### Hash chain

| Name                      | Value                  |
| ------------------------- | ---------------------- |
| `HASH_CHAIN_RANDAO_DST`   | `b"HASH_CHAIN_RANDAO"` |
| `UNSET_RANDAO_COMMITMENT` | `Bytes32()`            |

> 💡 Ghi chú: `HASH_CHAIN_RANDAO_DST` là chuỗi phân tách miền (domain separation tag) được ghép vào trước dữ liệu khi băm mỗi mắt xích. `UNSET_RANDAO_COMMITMENT` (32 byte 0) là giá trị đánh dấu (sentinel) cho biết validator chưa đăng ký commitment.

## Presets

### Hash-chain RANDAO

| Name                                  | Value                  |
| ------------------------------------- | ---------------------- |
| `COMMITMENT_REGISTRATION_DELAY`       | `Epoch(3)` (= 3)       |
| `MAX_RANDAO_COMMITMENT_REGISTRATIONS` | `Uint64(2**7)` (= 128) |

*Lưu ý*: `COMMITMENT_REGISTRATION_DELAY` phải tối thiểu bằng `MIN_SEED_LOOKAHEAD + 2`, để tại thời điểm registration được đưa vào block, người đăng ký không thể biết liệu mình có được làm proposer trong epoch kích hoạt hay không.

## Containers

### New containers

#### `PendingRandaoCommitment`

```python
class PendingRandaoCommitment(Container):
    validator_index: ValidatorIndex
    commitment: Bytes32
    activation_epoch: Epoch
```

#### `RandaoCommitmentRegistration`

```python
class RandaoCommitmentRegistration(Container):
    validator_index: ValidatorIndex
    commitment: Bytes32
```

#### `SignedRandaoCommitmentRegistration`

```python
class SignedRandaoCommitmentRegistration(Container):
    message: RandaoCommitmentRegistration
    signature: BLSSignature
```

### Modified containers

#### `BeaconBlockBody`

*Lưu ý*: `randao_reveal` được giữ lại cho các validator chưa đăng ký commitment. Trong hai trường `randao_reveal` và `hash_chain_reveal`, đúng một trường được điền giá trị; trường còn lại để trống.

```python
class BeaconBlockBody(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=15, gaps=(1, 6))

    randao_reveal: BLSSignature
    graffiti: Bytes32
    proposer_slashings: ProposerSlashings
    attester_slashings: AttesterSlashings
    attestations: Attestations
    voluntary_exits: VoluntaryExits
    sync_aggregate: SyncAggregate
    bls_to_execution_changes: BLSToExecutionChanges
    signed_execution_payload_bid: SignedExecutionPayloadBid
    payload_attestations: PayloadAttestations
    parent_execution_requests: ExecutionRequests
    # [New in EIP8321]
    hash_chain_reveal: Bytes32
    # [New in EIP8321]
    randao_commitment_registrations: RandaoCommitmentRegistrations
```

#### `BeaconState`

```python
class BeaconState(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=48, gaps=(8, 9, 10, 28))

    genesis_time: Uint64
    genesis_validators_root: Root
    slot: Slot
    fork: Fork
    latest_block_header: BeaconBlockHeader
    block_roots: BlockRoots
    state_roots: StateRoots
    historical_roots: HistoricalRoots
    validators: Validators
    balances: Balances
    randao_mixes: RandaoMixes
    slashings: Slashings
    previous_epoch_participation: EpochParticipation
    current_epoch_participation: EpochParticipation
    justification_bits: JustificationBits
    previous_justified_checkpoint: Checkpoint
    current_justified_checkpoint: Checkpoint
    finalized_checkpoint: Checkpoint
    inactivity_scores: InactivityScores
    current_sync_committee: SyncCommittee
    next_sync_committee: SyncCommittee
    latest_block_hash: Hash32
    next_withdrawal_index: WithdrawalIndex
    next_withdrawal_validator_index: ValidatorIndex
    historical_summaries: HistoricalSummaries
    deposit_balance_to_consume: Gwei
    exit_balance_to_consume: Gwei
    earliest_exit_epoch: Epoch
    consolidation_balance_to_consume: Gwei
    earliest_consolidation_epoch: Epoch
    pending_deposits: PendingDeposits
    pending_partial_withdrawals: PendingPartialWithdrawals
    pending_consolidations: PendingConsolidations
    proposer_lookahead: ProposerLookahead
    builders: Builders
    next_withdrawal_builder_index: BuilderIndex
    execution_payload_availability: ExecutionPayloadAvailability
    builder_pending_payments: BuilderPendingPayments
    builder_pending_withdrawals: BuilderPendingWithdrawals
    latest_execution_payload_bid: ExecutionPayloadBid
    payload_expected_withdrawals: Withdrawals
    ptc_window: PayloadTimelinessCommitteeWindow
    # [New in EIP8321]
    randao_commitments: RandaoCommitments
    # [New in EIP8321]
    pending_randao_commitments: PendingRandaoCommitments
```

## Helpers

### Crypto

#### New `blake3`

```python
def blake3(data: bytes) -> Bytes32:
    """
    Return the BLAKE3 hash of ``data``.
    """
    return Bytes32(blake3_hash(data).digest())
```

### Validator registry

#### Modified `add_validator_to_registry`

*Lưu ý*: Hàm `add_validator_to_registry` được sửa đổi để khởi tạo phần tử tương ứng trong danh sách `randao_commitments`, nhằm duy trì bất biến (invariant) là danh sách này có đúng một phần tử cho mỗi validator.

```python
def add_validator_to_registry(
    state: BeaconState, pubkey: BLSPubkey, withdrawal_credentials: Bytes32, amount: Gwei
) -> None:
    index = get_index_for_new_validator(state)
    validator = get_validator_from_deposit(pubkey, withdrawal_credentials, amount)
    set_or_append_list(state.validators, index, validator)
    set_or_append_list(state.balances, index, amount)
    set_or_append_list(state.previous_epoch_participation, index, ParticipationFlags(0b0000_0000))
    set_or_append_list(state.current_epoch_participation, index, ParticipationFlags(0b0000_0000))
    set_or_append_list(state.inactivity_scores, index, Uint64(0))
    # [New in EIP8321]
    set_or_append_list(state.randao_commitments, index, UNSET_RANDAO_COMMITMENT)
```

### RANDAO verifications

#### New `verify_hash_chain_reveal`

```python
def verify_hash_chain_reveal(
    state: BeaconState, body: BeaconBlockBody, proposer_index: ValidatorIndex
) -> None:
    """
    Verify that ``body`` reveals the preimage of the proposer's stored commitment.
    """
    assert body.hash_chain_reveal != Bytes32()
    assert body.randao_reveal == G2_POINT_AT_INFINITY
    commitment = state.randao_commitments[proposer_index]
    assert blake3(HASH_CHAIN_RANDAO_DST + body.hash_chain_reveal) == commitment
```

> 💡 Ghi chú: Hàm kiểm tra rằng `hash_chain_reveal` khác 0, `randao_reveal` để trống (bằng điểm vô cực `G2_POINT_AT_INFINITY`), và `blake3(HASH_CHAIN_RANDAO_DST + hash_chain_reveal)` đúng bằng commitment đang lưu của proposer — tức reveal chính là mắt xích liền trước commitment trên hash chain.

#### New `verify_bls_randao_reveal`

```python
def verify_bls_randao_reveal(
    state: BeaconState, body: BeaconBlockBody, proposer_index: ValidatorIndex
) -> None:
    """
    Verify that ``body`` reveals the proposer's signature over the current epoch.
    """
    assert body.hash_chain_reveal == Bytes32()
    epoch = get_current_epoch(state)
    signing_root = compute_signing_root(epoch, get_domain(state, DOMAIN_RANDAO))
    pubkey = state.validators[proposer_index].pubkey
    assert bls.Verify(pubkey, signing_root, body.randao_reveal)
```

## Beacon chain state transition function

### Epoch processing

#### Modified `process_epoch`

*Lưu ý*: Hàm `process_epoch` được sửa đổi để gọi helper mới `process_pending_randao_commitments`.

```python
def process_epoch(state: BeaconState) -> None:
    process_justification_and_finalization(state)
    process_inactivity_updates(state)
    process_rewards_and_penalties(state)
    process_registry_updates(state)
    # [New in EIP8321]
    process_pending_randao_commitments(state)
    process_slashings(state)
    process_pending_deposits(state)
    process_pending_consolidations(state)
    process_builder_pending_payments(state)
    process_effective_balance_updates(state)
    process_slashings_reset(state)
    process_randao_mixes_reset(state)
    process_historical_summaries_update(state)
    process_participation_flag_updates(state)
    process_sync_committee_updates(state)
    process_proposer_lookahead(state)
    process_ptc_window(state)
```

#### New `process_pending_randao_commitments`

*Lưu ý*: Các commitment được đưa vào hàng đợi với activation epoch được tính từ epoch mà chúng được đưa vào block, nên hàng đợi luôn được sắp xếp theo activation epoch và có thể được xử lý (rút ra) dần từ đầu hàng đợi.

```python
def process_pending_randao_commitments(state: BeaconState) -> None:
    next_epoch = get_current_epoch(state) + 1
    next_pending_commitment = 0
    for pending_commitment in state.pending_randao_commitments:
        if pending_commitment.activation_epoch > next_epoch:
            break

        index = pending_commitment.validator_index
        state.randao_commitments[index] = pending_commitment.commitment
        next_pending_commitment += 1

    state.pending_randao_commitments = state.pending_randao_commitments[next_pending_commitment:]
```

> 💡 Ghi chú: Ở cuối mỗi epoch, mọi pending commitment có `activation_epoch <= next_epoch` được ghi vào `state.randao_commitments`, và bị xóa khỏi hàng đợi. Vòng lặp dừng ngay ở phần tử đầu tiên chưa đến hạn, vì các phần tử sau chắc chắn cũng chưa đến hạn.

### Block processing

#### Modified `process_randao`

*Lưu ý*: Một phần tử bằng 0 trong `randao_commitments` nghĩa là proposer chưa đăng ký hash chain, và BLS reveal kiểu cũ được áp dụng. Việc từ chối reveal bằng 0 giữ cho giá trị sentinel này có ý nghĩa: nếu không có kiểm tra đó, một validator reveal word 0 sẽ âm thầm lưu sentinel làm commitment và rơi trở lại nhánh legacy.

*Lưu ý*: Nhánh hash chain trộn reveal thô vào bằng một bộ tích lũy dạng băm thay vì `xor`. Commitment không gắn với danh tính nào và có thể sao chép được, nên một validator có thể đăng ký commitment của validator khác. Làm vậy là tự hại mình: kẻ sao chép không nắm preimage, nên không thể propose được gì cho đến khi nạn nhân reveal, và mất toàn bộ các slot được giao trong khoảng thời gian đó. Ngay cả khi nạn nhân đã reveal, bộ tích lũy không có hàm ngược tính được một cách hiệu quả, nên việc tiêm lại reveal đã sao chép chỉ sinh ra một mix không liên quan, chứ không triệt tiêu được phần đóng góp của nạn nhân — điều mà một bộ tích lũy `xor` lại cho phép.

> 💡 Ghi chú: Với `xor`, nếu cùng một giá trị được trộn vào hai lần thì nó tự triệt tiêu (`a ^ x ^ x = a`), nên kẻ sao chép có thể xóa đóng góp của nạn nhân. Với `blake3(mix + reveal)`, mỗi lần trộn đều cho ra một giá trị hoàn toàn mới, không thể "hoàn tác".

```python
def process_randao(state: BeaconState, body: BeaconBlockBody) -> None:
    epoch = get_current_epoch(state)
    proposer_index = get_beacon_proposer_index(state)

    # [New in EIP8321]
    if state.randao_commitments[proposer_index] != UNSET_RANDAO_COMMITMENT:
        verify_hash_chain_reveal(state, body, proposer_index)
        mix = blake3(get_randao_mix(state, epoch) + body.hash_chain_reveal)
        state.randao_mixes[epoch % EPOCHS_PER_HISTORICAL_VECTOR] = mix
        state.randao_commitments[proposer_index] = body.hash_chain_reveal
    else:
        verify_bls_randao_reveal(state, body, proposer_index)
        mix = xor(get_randao_mix(state, epoch), sha256(body.randao_reveal))
        state.randao_mixes[epoch % EPOCHS_PER_HISTORICAL_VECTOR] = mix
```

#### Operations

##### Modified `process_operations`

*Lưu ý*: Hàm `process_operations` được sửa đổi để xử lý các RANDAO commitment registration.

```python
def process_operations(
    state: BeaconState,
    body: BeaconBlockBody,
    parent_slot: Slot,
) -> None:
    def for_ops(operations: Sequence[Any], fn: Callable[..., None], *args: Any) -> None:
        for operation in operations:
            fn(state, operation, *args)

    assert len(body.proposer_slashings) <= MAX_PROPOSER_SLASHINGS
    assert len(body.attester_slashings) <= MAX_ATTESTER_SLASHINGS_ELECTRA
    assert len(body.attestations) <= MAX_ATTESTATIONS_ELECTRA
    assert len(body.voluntary_exits) <= MAX_VOLUNTARY_EXITS
    assert len(body.bls_to_execution_changes) <= MAX_BLS_TO_EXECUTION_CHANGES
    assert len(body.payload_attestations) <= MAX_PAYLOAD_ATTESTATIONS
    # [New in EIP8321]
    assert len(body.randao_commitment_registrations) <= MAX_RANDAO_COMMITMENT_REGISTRATIONS

    for_ops(body.proposer_slashings, process_proposer_slashing)
    for_ops(body.attester_slashings, process_attester_slashing)
    for_ops(body.attestations, process_attestation, parent_slot)
    for_ops(body.voluntary_exits, process_voluntary_exit)
    for_ops(body.bls_to_execution_changes, process_bls_to_execution_change)
    for_ops(body.payload_attestations, process_payload_attestation)
    # [New in EIP8321]
    for_ops(body.randao_commitment_registrations, process_randao_commitment_registration)
```

##### RANDAO commitment registrations

###### New `process_randao_commitment_registration`

Đây là con đường dùng một lần duy nhất để chuyển một validator từ BLS reveal kiểu cũ sang hash chain của nó. Operation này chỉ hợp lệ khi validator chưa đăng ký, và chỉ khi nó không có registration nào khác đang chờ xử lý. Không có gì xóa một phần tử của `randao_commitments`, nên một validator index đã đăng ký sẽ giữ chain của nó chừng nào index đó còn tồn tại; muốn thay một chain bị mất thì phải onboard một validator mới dưới một public key mới.

*Lưu ý*: Cả hai kiểm tra đều cần thiết để registration chỉ dùng được một lần. Khi một registration đã được kích hoạt, commitment đang lưu khác 0 và mọi lần replay đều thất bại ở kiểm tra thứ nhất. Khi nó vẫn đang chờ (pending), commitment đang lưu vẫn bằng 0, và kiểm tra thứ hai sẽ từ chối bản trùng lặp. Kiểm tra thứ hai cũng từ chối bản trùng lặp trong cùng một block, vì operation đầu tiên trong block đã thêm phần tử của nó vào hàng đợi.

*Lưu ý*: Độ trễ kích hoạt được tính từ epoch mà registration được đưa vào block, vì đó là sự kiện duy nhất state quan sát được. Ký một registration sớm hơn chỉ có nghĩa là cam kết với ít thông tin hơn.

```python
def process_randao_commitment_registration(
    state: BeaconState, signed_registration: SignedRandaoCommitmentRegistration
) -> None:
    registration = signed_registration.message
    index = registration.validator_index

    assert index < len(state.validators)
    assert registration.commitment != UNSET_RANDAO_COMMITMENT
    assert state.randao_commitments[index] == UNSET_RANDAO_COMMITMENT
    assert all(pending.validator_index != index for pending in state.pending_randao_commitments)

    # Fork-agnostic domain since registrations are valid across forks
    domain = compute_domain(
        DOMAIN_RANDAO_COMMITMENT_REGISTRATION,
        genesis_validators_root=state.genesis_validators_root,
    )
    signing_root = compute_signing_root(registration, domain)
    validator = state.validators[index]
    assert bls.Verify(validator.pubkey, signing_root, signed_registration.signature)

    state.pending_randao_commitments.append(
        PendingRandaoCommitment(
            validator_index=index,
            commitment=registration.commitment,
            activation_epoch=get_current_epoch(state) + COMMITMENT_REGISTRATION_DELAY,
        )
    )
```
