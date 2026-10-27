# Deneb -- The Beacon Chain

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Types](#types)
  - [New `Blob`](#new-blob)
  - [New `BlobIndex`](#new-blobindex)
  - [New `BlobKZGCommitments`](#new-blobkzgcommitments)
  - [New `KZGCommitment`](#new-kzgcommitment)
  - [New `KZGProof`](#new-kzgproof)
  - [New `VersionedHash`](#new-versionedhash)
  - [New `VersionedHashes`](#new-versionedhashes)
- [Constants](#constants)
  - [Blob](#blob)
- [Presets](#presets)
  - [Blob](#blob-1)
  - [Execution](#execution)
- [Configs](#configs)
  - [Execution](#execution-1)
  - [Validator cycle](#validator-cycle)
- [Containers](#containers)
  - [Modified containers](#modified-containers)
    - [`BeaconBlockBody`](#beaconblockbody)
    - [`ExecutionPayload`](#executionpayload)
    - [`ExecutionPayloadHeader`](#executionpayloadheader)
    - [`BeaconState`](#beaconstate)
    - [`NewPayloadRequest`](#newpayloadrequest)
- [Helpers](#helpers)
  - [Misc](#misc)
    - [`kzg_commitment_to_versioned_hash`](#kzg_commitment_to_versioned_hash)
  - [Beacon state accessors](#beacon-state-accessors)
    - [Modified `get_attestation_participation_flag_indices`](#modified-get_attestation_participation_flag_indices)
    - [New `get_validator_activation_churn_limit`](#new-get_validator_activation_churn_limit)
- [Beacon chain state transition function](#beacon-chain-state-transition-function)
  - [Execution engine](#execution-engine)
    - [Engine APIs](#engine-apis)
      - [`is_valid_block_hash`](#is_valid_block_hash)
      - [`is_valid_versioned_hashes`](#is_valid_versioned_hashes)
      - [Modified `notify_new_payload`](#modified-notify_new_payload)
      - [Modified `verify_and_notify_new_payload`](#modified-verify_and_notify_new_payload)
  - [Block processing](#block-processing)
    - [Modified `process_attestation`](#modified-process_attestation)
    - [Execution payload](#execution-payload)
      - [Modified `process_execution_payload`](#modified-process_execution_payload)
    - [Modified `process_voluntary_exit`](#modified-process_voluntary_exit)
  - [Epoch processing](#epoch-processing)
    - [Registry updates](#registry-updates)

<!-- mdformat-toc end -->

## Introduction

Deneb là một bản nâng cấp tầng đồng thuận (consensus layer) gồm nhiều tính năng,
trong đó có:

- [EIP-4788](https://eips.ethereum.org/EIPS/eip-4788): Đưa beacon block root vào
  EVM (để smart contract có thể truy cập root của beacon block cha).
- [EIP-4844](https://eips.ethereum.org/EIPS/eip-4844): Shard Blob Transactions —
  mở rộng khả năng cung cấp data (data availability) của Ethereum theo cách đơn
  giản và tương thích với các nâng cấp về sau.
- [EIP-7044](https://eips.ethereum.org/EIPS/eip-7044): Voluntary exit đã ký có
  hiệu lực vĩnh viễn (không bị vô hiệu khi qua các fork sau).
- [EIP-7045](https://eips.ethereum.org/EIPS/eip-7045): Tăng slot tối đa để đưa
  attestation vào block.
- [EIP-7514](https://eips.ethereum.org/EIPS/eip-7514): Thêm giới hạn churn tối
  đa mỗi epoch (giới hạn số validator được kích hoạt trong một epoch).

## Types

### New `Blob`

```python
class Blob(ByteVector):
    """
    A blob of data, encoded as a sequence of BLS scalar field elements.
    """

    LENGTH = BYTES_PER_FIELD_ELEMENT * FIELD_ELEMENTS_PER_BLOB
```

### New `BlobIndex`

```python
class BlobIndex(Uint64):
    """
    The index of a blob within a block.
    """
```

### New `BlobKZGCommitments`

```python
class BlobKZGCommitments(List[KZGCommitment]):
    """
    The KZG commitments to the blobs of a beacon block.
    """

    LIMIT = MAX_BLOB_COMMITMENTS_PER_BLOCK
```

### New `KZGCommitment`

```python
class KZGCommitment(Bytes48):
    """
    A commitment to the polynomial defined by the field elements of a blob.
    """
```

### New `KZGProof`

```python
class KZGProof(Bytes48):
    """
    A proof that the polynomial committed to by a ``KZGCommitment`` evaluates
    to expected values at one or more points.
    """
```

### New `VersionedHash`

```python
class VersionedHash(Bytes32):
    """
    A versioned hash of a blob's KZG commitment.
    """
```

### New `VersionedHashes`

```python
class VersionedHashes(List[VersionedHash]):
    """
    The versioned hashes for blobs associated with an execution payload.
    """

    LIMIT = MAX_BLOB_COMMITMENTS_PER_BLOCK
```

## Constants

### Blob

| Name                         | Value            | Description                                     |
| ---------------------------- | ---------------- | ----------------------------------------------- |
| `VERSIONED_HASH_VERSION_KZG` | `Bytes1("0x01")` | Byte phiên bản của versioned hash của một blob  |
| `BYTES_PER_FIELD_ELEMENT`    | `Uint64(32)`     | Số byte dùng để mã hóa một phần tử trường vô hướng (scalar field element) BLS |

## Presets

### Blob

| Name                      | Value          | Description                        |
| ------------------------- | -------------- | ---------------------------------- |
| `FIELD_ELEMENTS_PER_BLOB` | `Uint64(4096)` | Số field element trong một blob    |

### Execution

| Name                             | Value                     | Description                                                                     |
| -------------------------------- | ------------------------- | ------------------------------------------------------------------------------- |
| `MAX_BLOB_COMMITMENTS_PER_BLOCK` | `Uint64(2**12)` (= 4,096) | Giới hạn lý thuyết cố định, không phụ thuộc vào các bản nâng cấp, giống với `TARGET_BLOB_GAS_PER_BLOCK` |

## Configs

### Execution

| Name                  | Value       | Description                                                                           |
| --------------------- | ----------- | ------------------------------------------------------------------------------------- |
| `MAX_BLOBS_PER_BLOCK` | `Uint64(6)` | Số blob tối đa trong một block, bị chặn trên bởi `MAX_BLOB_COMMITMENTS_PER_BLOCK` |

*Ghi chú*: Các blob transaction được EL/builder đóng gói vào execution payload,
còn các blob tương ứng của chúng được truyền đi một cách độc lập; số lượng bị
giới hạn bởi `MAX_BLOB_GAS_PER_BLOCK // GAS_PER_BLOB` (phía EL). Tuy nhiên, giới
hạn phía CL được định nghĩa độc lập bằng `MAX_BLOBS_PER_BLOCK`.

### Validator cycle

| Name                                   | Value                |
| -------------------------------------- | -------------------- |
| `MAX_PER_EPOCH_ACTIVATION_CHURN_LIMIT` | `Uint64(2**3)` (= 8) |

## Containers

### Modified containers

#### `BeaconBlockBody`

*Ghi chú*: Các kiểu `BeaconBlock` và `SignedBeaconBlock` cũng được cập nhật
gián tiếp (vì chúng chứa `BeaconBlockBody`).

```python
class BeaconBlockBody(Container):
    randao_reveal: BLSSignature
    eth1_data: Eth1Data
    graffiti: Bytes32
    proposer_slashings: ProposerSlashings
    attester_slashings: AttesterSlashings
    attestations: Attestations
    deposits: Deposits
    voluntary_exits: VoluntaryExits
    sync_aggregate: SyncAggregate
    # [Modified in Deneb:EIP4844]
    execution_payload: ExecutionPayload
    bls_to_execution_changes: BLSToExecutionChanges
    # [New in Deneb:EIP4844]
    blob_kzg_commitments: BlobKZGCommitments
```

#### `ExecutionPayload`

```python
class ExecutionPayload(Container):
    parent_hash: Hash32
    fee_recipient: ExecutionAddress
    state_root: Bytes32
    receipts_root: Bytes32
    logs_bloom: LogsBloom
    prev_randao: Bytes32
    block_number: Uint64
    gas_limit: Uint64
    gas_used: Uint64
    timestamp: Uint64
    extra_data: ExtraData
    base_fee_per_gas: Uint256
    block_hash: Hash32
    transactions: Transactions
    withdrawals: Withdrawals
    # [New in Deneb:EIP4844]
    blob_gas_used: Uint64
    # [New in Deneb:EIP4844]
    excess_blob_gas: Uint64
```

#### `ExecutionPayloadHeader`

```python
class ExecutionPayloadHeader(Container):
    parent_hash: Hash32
    fee_recipient: ExecutionAddress
    state_root: Bytes32
    receipts_root: Bytes32
    logs_bloom: LogsBloom
    prev_randao: Bytes32
    block_number: Uint64
    gas_limit: Uint64
    gas_used: Uint64
    timestamp: Uint64
    extra_data: ExtraData
    base_fee_per_gas: Uint256
    block_hash: Hash32
    transactions_root: Root
    withdrawals_root: Root
    # [New in Deneb:EIP4844]
    blob_gas_used: Uint64
    # [New in Deneb:EIP4844]
    excess_blob_gas: Uint64
```

#### `BeaconState`

```python
class BeaconState(Container):
    genesis_time: Uint64
    genesis_validators_root: Root
    slot: Slot
    fork: Fork
    latest_block_header: BeaconBlockHeader
    block_roots: BlockRoots
    state_roots: StateRoots
    historical_roots: HistoricalRoots
    eth1_data: Eth1Data
    eth1_data_votes: Eth1DataVotes
    eth1_deposit_index: Uint64
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
    # [Modified in Deneb:EIP4844]
    latest_execution_payload_header: ExecutionPayloadHeader
    next_withdrawal_index: WithdrawalIndex
    next_withdrawal_validator_index: ValidatorIndex
    historical_summaries: HistoricalSummaries
```

#### `NewPayloadRequest`

```python
class NewPayloadRequest(Container):
    execution_payload: ExecutionPayload
    # [New in Deneb:EIP4844]
    versioned_hashes: VersionedHashes
    # [New in Deneb:EIP4788]
    parent_beacon_block_root: Root
```

## Helpers

### Misc

#### `kzg_commitment_to_versioned_hash`

```python
def kzg_commitment_to_versioned_hash(kzg_commitment: KZGCommitment) -> VersionedHash:
    return VersionedHash(VERSIONED_HASH_VERSION_KZG + sha256(kzg_commitment)[1:])
```

### Beacon state accessors

#### Modified `get_attestation_participation_flag_indices`

*Ghi chú*: Hàm `get_attestation_participation_flag_indices` được sửa đổi để
bật `TIMELY_TARGET_FLAG` cho mọi attestation có target đúng, bất kể giá trị
`inclusion_delay` là bao nhiêu. Đây là reward cơ bản cho việc đưa vào block (với
bất kỳ tốc độ nào) một attestation có đóng góp vào justification của chain chứa
nó, theo EIP-7045.

> 💡 Ghi chú: Trước Deneb, cờ target chỉ được bật nếu attestation được đưa vào
> trong vòng `SLOTS_PER_EPOCH` slot. Từ Deneb, chỉ cần target đúng là đủ.

```python
def get_attestation_participation_flag_indices(
    state: BeaconState, data: AttestationData, inclusion_delay: Uint64
) -> Sequence[int]:
    """
    Return the flag indices that are satisfied by an attestation.
    """
    # Matching source
    if data.target.epoch == get_current_epoch(state):
        justified_checkpoint = state.current_justified_checkpoint
    else:
        justified_checkpoint = state.previous_justified_checkpoint
    is_matching_source = data.source == justified_checkpoint

    # Matching target
    target_root = get_block_root(state, data.target.epoch)
    target_root_matches = data.target.root == target_root
    is_matching_target = is_matching_source and target_root_matches

    # Matching head
    head_root = get_block_root_at_slot(state, data.slot)
    head_root_matches = data.beacon_block_root == head_root
    is_matching_head = is_matching_target and head_root_matches

    assert is_matching_source

    participation_flag_indices = []
    if is_matching_source and inclusion_delay <= integer_squareroot(SLOTS_PER_EPOCH):
        participation_flag_indices.append(TIMELY_SOURCE_FLAG_INDEX)
    # [Modified in Deneb:EIP7045]
    if is_matching_target:
        participation_flag_indices.append(TIMELY_TARGET_FLAG_INDEX)
    if is_matching_head and inclusion_delay == MIN_ATTESTATION_INCLUSION_DELAY:
        participation_flag_indices.append(TIMELY_HEAD_FLAG_INDEX)

    return participation_flag_indices
```

#### New `get_validator_activation_churn_limit`

```python
def get_validator_activation_churn_limit(state: BeaconState) -> Uint64:
    """
    Return the validator activation churn limit for the current epoch.
    """
    return min(MAX_PER_EPOCH_ACTIVATION_CHURN_LIMIT, get_validator_churn_limit(state))
```

## Beacon chain state transition function

### Execution engine

#### Engine APIs

##### `is_valid_block_hash`

*Ghi chú*: Hàm `is_valid_block_hash` được sửa đổi để nhận thêm tham số
`parent_beacon_block_root`, phục vụ EIP-4788.

```python
def is_valid_block_hash(
    self: ExecutionEngine, execution_payload: ExecutionPayload, parent_beacon_block_root: Root
) -> bool:
    """
    Return ``True`` if and only if ``execution_payload.block_hash`` is computed correctly.
    """
```

##### `is_valid_versioned_hashes`

```python
def is_valid_versioned_hashes(
    self: ExecutionEngine, new_payload_request: NewPayloadRequest
) -> bool:
    """
    Return ``True`` if and only if the version hashes computed by the blob transactions of
    ``new_payload_request.execution_payload`` matches ``new_payload_request.versioned_hashes``.
    """
```

##### Modified `notify_new_payload`

*Ghi chú*: Hàm `notify_new_payload` được sửa đổi để nhận thêm tham số
`parent_beacon_block_root`, phục vụ EIP-4788.

```python
def notify_new_payload(
    self: ExecutionEngine, execution_payload: ExecutionPayload, parent_beacon_block_root: Root
) -> bool:
    """
    Return ``True`` if and only if ``execution_payload`` is valid with respect to ``self.execution_state``.
    """
```

##### Modified `verify_and_notify_new_payload`

```python
def verify_and_notify_new_payload(
    self: ExecutionEngine, new_payload_request: NewPayloadRequest
) -> bool:
    """
    Return ``True`` if and only if ``new_payload_request`` is valid with respect to ``self.execution_state``.
    """
    execution_payload = new_payload_request.execution_payload
    # [New in Deneb:EIP4788]
    parent_beacon_block_root = new_payload_request.parent_beacon_block_root

    if b"" in execution_payload.transactions:
        return False

    # [Modified in Deneb:EIP4788]
    if not self.is_valid_block_hash(execution_payload, parent_beacon_block_root):
        return False

    # [New in Deneb:EIP4844]
    if not self.is_valid_versioned_hashes(new_payload_request):
        return False

    # [Modified in Deneb:EIP4788]
    if not self.notify_new_payload(execution_payload, parent_beacon_block_root):
        return False

    return True
```

### Block processing

#### Modified `process_attestation`

*Ghi chú*: Hàm `process_attestation` được sửa đổi để mở rộng khoảng slot hợp lệ
cho việc đưa attestation vào block: chấp nhận các slot thuộc cả epoch
`target.epoch` lẫn epoch `target.epoch + 1` (EIP-7045). Ngoài ra, hàm dùng phiên
bản cập nhật của `get_attestation_participation_flag_indices` để đảm bảo vẫn có
reward cho attestation trong khoảng inclusion được mở rộng này (EIP-7045).

```python
def process_attestation(state: BeaconState, attestation: Attestation) -> None:
    data = attestation.data
    assert data.target.epoch in (get_previous_epoch(state), get_current_epoch(state))
    assert data.target.epoch == compute_epoch_at_slot(data.slot)
    # [Modified in Deneb:EIP7045]
    assert data.slot + MIN_ATTESTATION_INCLUSION_DELAY <= state.slot
    assert data.index < get_committee_count_per_slot(state, data.target.epoch)

    committee = get_beacon_committee(state, data.slot, data.index)
    assert len(attestation.aggregation_bits) == len(committee)

    # Participation flag indices
    participation_flag_indices = get_attestation_participation_flag_indices(
        state, data, state.slot - data.slot
    )

    # Verify signature
    assert is_valid_indexed_attestation(state, get_indexed_attestation(state, attestation))

    # Update epoch participation flags
    if data.target.epoch == get_current_epoch(state):
        epoch_participation = state.current_epoch_participation
    else:
        epoch_participation = state.previous_epoch_participation

    proposer_reward_numerator = 0
    for index in get_attesting_indices(state, attestation):
        for flag_index, weight in enumerate(PARTICIPATION_FLAG_WEIGHTS):
            if flag_index in participation_flag_indices and not has_flag(
                epoch_participation[index], flag_index
            ):
                epoch_participation[index] = add_flag(epoch_participation[index], flag_index)
                proposer_reward_numerator += get_base_reward(state, index) * weight

    # Reward proposer
    proposer_reward_denominator = (
        (WEIGHT_DENOMINATOR - PROPOSER_WEIGHT) * WEIGHT_DENOMINATOR // PROPOSER_WEIGHT
    )
    proposer_reward = Gwei(proposer_reward_numerator // proposer_reward_denominator)
    increase_balance(state, get_beacon_proposer_index(state), proposer_reward)
```

#### Execution payload

##### Modified `process_execution_payload`

*Ghi chú*: Hàm `process_execution_payload` được sửa đổi để truyền
`versioned_hashes` vào `execution_engine.verify_and_notify_new_payload` và gán
các trường mới trong `ExecutionPayloadHeader` cho EIP-4844. Hàm cũng được sửa để
truyền vào root của beacon block cha nhằm hỗ trợ EIP-4788.

```python
def process_execution_payload(
    state: BeaconState, body: BeaconBlockBody, execution_engine: ExecutionEngine
) -> None:
    payload = body.execution_payload

    # Verify consistency of the parent hash with respect to the previous execution payload header
    assert payload.parent_hash == state.latest_execution_payload_header.block_hash
    # Verify prev_randao
    assert payload.prev_randao == get_randao_mix(state, get_current_epoch(state))
    # Verify timestamp
    assert payload.timestamp == compute_time_at_slot(state.genesis_time, state.slot)
    # [New in Deneb:EIP4844]
    # Verify commitments are under limit
    assert len(body.blob_kzg_commitments) <= MAX_BLOBS_PER_BLOCK

    # [New in Deneb:EIP4844]
    # Compute versioned hashes
    versioned_hashes = VersionedHashes()
    for commitment in body.blob_kzg_commitments:
        versioned_hashes.append(kzg_commitment_to_versioned_hash(commitment))

    # Verify the execution payload is valid
    assert execution_engine.verify_and_notify_new_payload(
        NewPayloadRequest(
            execution_payload=payload,
            # [New in Deneb:EIP4844]
            versioned_hashes=versioned_hashes,
            # [New in Deneb:EIP4788]
            parent_beacon_block_root=state.latest_block_header.parent_root,
        )
    )

    # Cache execution payload header
    state.latest_execution_payload_header = ExecutionPayloadHeader(
        parent_hash=payload.parent_hash,
        fee_recipient=payload.fee_recipient,
        state_root=payload.state_root,
        receipts_root=payload.receipts_root,
        logs_bloom=payload.logs_bloom,
        prev_randao=payload.prev_randao,
        block_number=payload.block_number,
        gas_limit=payload.gas_limit,
        gas_used=payload.gas_used,
        timestamp=payload.timestamp,
        extra_data=payload.extra_data,
        base_fee_per_gas=payload.base_fee_per_gas,
        block_hash=payload.block_hash,
        transactions_root=hash_tree_root(payload.transactions),
        withdrawals_root=hash_tree_root(payload.withdrawals),
        # [New in Deneb:EIP4844]
        blob_gas_used=payload.blob_gas_used,
        # [New in Deneb:EIP4844]
        excess_blob_gas=payload.excess_blob_gas,
    )
```

#### Modified `process_voluntary_exit`

*Ghi chú*: Hàm `process_voluntary_exit` được sửa đổi để dùng fork version cố
định -- `CAPELLA_FORK_VERSION` -- theo EIP-7044.

> 💡 Ghi chú: Nhờ vậy, một voluntary exit đã ký từ Capella trở đi vẫn hợp lệ ở mọi
> fork sau, không cần ký lại.

```python
def process_voluntary_exit(state: BeaconState, signed_voluntary_exit: SignedVoluntaryExit) -> None:
    voluntary_exit = signed_voluntary_exit.message
    validator = state.validators[voluntary_exit.validator_index]
    # Verify the validator is active
    assert is_active_validator(validator, get_current_epoch(state))
    # Verify exit has not been initiated
    assert validator.exit_epoch == FAR_FUTURE_EPOCH
    # Exits must specify an epoch when they become valid; they are not valid before then
    assert get_current_epoch(state) >= voluntary_exit.epoch
    # Verify the validator has been active long enough
    assert get_current_epoch(state) >= validator.activation_epoch + SHARD_COMMITTEE_PERIOD
    # Verify signature
    # [Modified in Deneb:EIP7044]
    domain = compute_domain(
        DOMAIN_VOLUNTARY_EXIT, CAPELLA_FORK_VERSION, state.genesis_validators_root
    )
    signing_root = compute_signing_root(voluntary_exit, domain)
    assert bls.Verify(validator.pubkey, signing_root, signed_voluntary_exit.signature)
    # Initiate exit
    initiate_validator_exit(state, voluntary_exit.validator_index)
```

### Epoch processing

#### Registry updates

*Ghi chú*: Hàm `process_registry_updates` được sửa đổi để dùng
`get_validator_activation_churn_limit()` nhằm giới hạn tốc độ của hàng đợi kích
hoạt (activation queue) theo EIP-7514.

```python
def process_registry_updates(state: BeaconState) -> None:
    # Process activation eligibility and ejections
    for index, validator in enumerate(state.validators):
        if is_eligible_for_activation_queue(validator):
            validator.activation_eligibility_epoch = get_current_epoch(state) + 1

        if (
            is_active_validator(validator, get_current_epoch(state))
            and validator.effective_balance <= EJECTION_BALANCE
        ):
            initiate_validator_exit(state, ValidatorIndex(index))

    # Queue validators eligible for activation and not yet dequeued for activation
    activation_queue = sorted(
        [
            index
            for index, validator in enumerate(state.validators)
            if is_eligible_for_activation(state, validator)
        ],
        # Order by the sequence of activation_eligibility_epoch setting and then index
        key=lambda index: (state.validators[index].activation_eligibility_epoch, index),
    )
    # Dequeued validators for activation up to activation churn limit
    # [Modified in Deneb:EIP7514]
    for index in activation_queue[: get_validator_activation_churn_limit(state)]:
        validator = state.validators[index]
        validator.activation_epoch = compute_activation_exit_epoch(get_current_epoch(state))
```
