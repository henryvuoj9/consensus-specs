# Fulu -- The Beacon Chain

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Types](#types)
  - [New `ProposerIndices`](#new-proposerindices)
  - [New `ProposerLookahead`](#new-proposerlookahead)
- [Configs](#configs)
  - [Blob schedule](#blob-schedule)
- [Beacon chain state transition function](#beacon-chain-state-transition-function)
  - [Block processing](#block-processing)
    - [Execution payload](#execution-payload)
      - [Modified `process_execution_payload`](#modified-process_execution_payload)
    - [Operations](#operations)
      - [Modified `process_operations`](#modified-process_operations)
      - [Deposit requests](#deposit-requests)
        - [Modified `process_deposit_request`](#modified-process_deposit_request)
- [Containers](#containers)
  - [Modified containers](#modified-containers)
    - [`BeaconState`](#beaconstate)
- [Helpers](#helpers)
  - [Misc](#misc)
    - [New `BlobParameters`](#new-blobparameters)
    - [New `get_blob_parameters`](#new-get_blob_parameters)
    - [Modified `compute_fork_digest`](#modified-compute_fork_digest)
    - [New `compute_proposer_indices`](#new-compute_proposer_indices)
  - [Beacon state accessors](#beacon-state-accessors)
    - [Modified `get_beacon_proposer_index`](#modified-get_beacon_proposer_index)
    - [New `get_beacon_proposer_indices`](#new-get_beacon_proposer_indices)
  - [Epoch processing](#epoch-processing)
    - [Modified `process_epoch`](#modified-process_epoch)
    - [Modified `process_pending_deposits`](#modified-process_pending_deposits)
    - [New `process_proposer_lookahead`](#new-process_proposer_lookahead)

<!-- mdformat-toc end -->

## Introduction

Fulu là một bản nâng cấp của consensus layer (lớp đồng thuận) bao gồm nhiều tính
năng, trong đó có:

- [EIP-7594](https://eips.ethereum.org/EIPS/eip-7594): PeerDAS - Peer Data
  Availability Sampling (lấy mẫu tính sẵn có của dữ liệu giữa các peer)
- [EIP-7917](https://eips.ethereum.org/EIPS/eip-7917): Deterministic proposer
  lookahead (xác định trước, một cách tất định, danh sách proposer cho các epoch
  sắp tới)
- [EIP-7892](https://eips.ethereum.org/EIPS/eip-7892): Blob Parameter Only
  Hardforks (các hardfork chỉ thay đổi tham số blob)

## Types

### New `ProposerIndices`

```python
class ProposerIndices(Vector[ValidatorIndex]):
    """
    The proposer indices for every slot of a single epoch.
    """

    LENGTH = SLOTS_PER_EPOCH
```

### New `ProposerLookahead`

```python
class ProposerLookahead(Vector[ValidatorIndex]):
    """
    The precomputed proposer indices for the current and next
    ``MIN_SEED_LOOKAHEAD`` epochs.
    """

    LENGTH = Uint64(MIN_SEED_LOOKAHEAD + 1) * Uint64(SLOTS_PER_EPOCH)
```

## Configs

### Blob schedule

*[New in Fulu:EIP7892]* Lịch này (blob schedule) quy định giới hạn số blob tối đa
trong mỗi block áp dụng từ một epoch nhất định.

KHÔNG ĐƯỢC (MUST NOT) có nhiều entry trong blob schedule có cùng giá trị epoch.
Giá trị epoch trong mỗi entry PHẢI (MUST) lớn hơn hoặc bằng `FULU_FORK_EPOCH`.
Giới hạn số blob tối đa mỗi block trong mỗi entry PHẢI (MUST) nhỏ hơn hoặc bằng
`MAX_BLOB_COMMITMENTS_PER_BLOCK`. Các entry trong blob schedule NÊN (SHOULD)
được sắp xếp theo epoch tăng dần. Blob schedule CÓ THỂ (MAY) rỗng.

> 💡 Ghi chú: Mỗi dòng trong bảng dưới đây là một "BPO fork" (Blob Parameter
> Only): kể từ epoch đó trở đi, giới hạn số blob mỗi block được đổi sang giá trị
> mới mà không cần thay đổi logic nào khác của giao thức.

<!-- list-of-records:blob_schedule -->

|  Epoch | Max Blobs Per Block |                             Date |
| -----: | ------------------: | -------------------------------: |
| 412672 |                  15 | December 9, 2025, 02:21:11pm UTC |
| 419072 |                  21 |  January 7, 2026, 01:01:11am UTC |

## Beacon chain state transition function

### Block processing

```python
def process_block(state: BeaconState, block: BeaconBlock) -> None:
    process_block_header(state, block)
    process_withdrawals(state, block.body.execution_payload)
    process_execution_payload(state, block.body, EXECUTION_ENGINE)
    process_randao(state, block.body)
    process_eth1_data(state, block.body)
    # [Modified in Fulu]
    process_operations(state, block.body)
    process_sync_aggregate(state, block.body.sync_aggregate)
```

#### Execution payload

##### Modified `process_execution_payload`

> 💡 Ghi chú: Thay đổi duy nhất so với Electra là giới hạn số blob KZG
> commitment trong block giờ lấy từ `get_blob_parameters(...)` theo epoch hiện
> tại (tức là theo blob schedule), thay vì một hằng số cố định.

```python
def process_execution_payload(
    state: BeaconState, body: BeaconBlockBody, execution_engine: ExecutionEngine
) -> None:
    payload = body.execution_payload

    # Kiểm tra parent hash khớp với execution payload header trước đó
    assert payload.parent_hash == state.latest_execution_payload_header.block_hash
    # Kiểm tra prev_randao
    assert payload.prev_randao == get_randao_mix(state, get_current_epoch(state))
    # Kiểm tra timestamp
    assert payload.timestamp == compute_time_at_slot(state.genesis_time, state.slot)
    # [Modified in Fulu:EIP7892]
    # Kiểm tra số lượng commitment không vượt quá giới hạn
    assert (
        len(body.blob_kzg_commitments)
        <= get_blob_parameters(get_current_epoch(state)).max_blobs_per_block
    )

    # Tính các versioned hash
    versioned_hashes = VersionedHashes()
    for commitment in body.blob_kzg_commitments:
        versioned_hashes.append(kzg_commitment_to_versioned_hash(commitment))

    # Kiểm tra execution payload hợp lệ
    assert execution_engine.verify_and_notify_new_payload(
        NewPayloadRequest(
            execution_payload=payload,
            versioned_hashes=versioned_hashes,
            parent_beacon_block_root=state.latest_block_header.parent_root,
            execution_requests=body.execution_requests,
        )
    )

    # Lưu lại execution payload header
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
        blob_gas_used=payload.blob_gas_used,
        excess_blob_gas=payload.excess_blob_gas,
    )
```

#### Operations

##### Modified `process_operations`

*Ghi chú*: Hàm `process_operations` được sửa đổi để loại bỏ hỗ trợ cho cơ chế
deposit cũ (deposit qua deposit contract được xử lý bằng `process_deposit` với
Merkle proof).

> 💡 Ghi chú: Từ Fulu, mọi deposit mới chỉ đi vào qua `execution_requests.deposits`
> (cơ chế deposit request của EIP-6110, có từ Electra). Vì vậy `body.deposits`
> bắt buộc phải rỗng.

```python
def process_operations(state: BeaconState, body: BeaconBlockBody) -> None:
    # [Modified in Fulu]
    assert len(body.deposits) == 0

    def for_ops(operations: Sequence[Any], fn: Callable[[BeaconState, Any], None]) -> None:
        for operation in operations:
            fn(state, operation)

    for_ops(body.proposer_slashings, process_proposer_slashing)
    for_ops(body.attester_slashings, process_attester_slashing)
    for_ops(body.attestations, process_attestation)
    # [Modified in Fulu]
    # Đã loại bỏ `process_deposit`
    for_ops(body.voluntary_exits, process_voluntary_exit)
    for_ops(body.bls_to_execution_changes, process_bls_to_execution_change)
    for_ops(body.execution_requests.deposits, process_deposit_request)
    for_ops(body.execution_requests.withdrawals, process_withdrawal_request)
    for_ops(body.execution_requests.consolidations, process_consolidation_request)
```

##### Deposit requests

###### Modified `process_deposit_request`

*Ghi chú*: Hàm `process_deposit_request` được sửa đổi để loại bỏ hỗ trợ cho cơ
chế deposit cũ.

> 💡 Ghi chú: Ở Electra, hàm này còn phải thiết lập
> `deposit_requests_start_index` để đánh dấu điểm chuyển giao giữa cơ chế cũ và
> mới. Ở Fulu, việc chuyển giao đã hoàn tất nên hàm chỉ đơn giản thêm một
> `PendingDeposit` vào hàng đợi.

```python
def process_deposit_request(state: BeaconState, deposit_request: DepositRequest) -> None:
    state.pending_deposits.append(
        PendingDeposit(
            pubkey=deposit_request.pubkey,
            withdrawal_credentials=deposit_request.withdrawal_credentials,
            amount=deposit_request.amount,
            signature=deposit_request.signature,
            slot=state.slot,
        )
    )
```

## Containers

### Modified containers

#### `BeaconState`

*Ghi chú*: Container `BeaconState` được mở rộng thêm trường `proposer_lookahead`.
Đây là danh sách các validator index bao phủ toàn bộ khoảng lookahead (khoảng
thời gian nhìn trước), bắt đầu từ đầu epoch hiện tại. Ví dụ,
`proposer_lookahead[0]` là validator index của proposer đầu tiên trong epoch
hiện tại, `proposer_lookahead[1]` là validator index của proposer tiếp theo
trong epoch hiện tại, và cứ thế tiếp tục. Độ dài của danh sách
`proposer_lookahead` là `(MIN_SEED_LOOKAHEAD + 1) * SLOTS_PER_EPOCH`, phản ánh
việc proposer index được tính trước bao xa, dựa trên tham số
`MIN_SEED_LOOKAHEAD`.

> 💡 Ghi chú: Với `MIN_SEED_LOOKAHEAD = 1`, danh sách này chứa proposer của 2
> epoch: epoch hiện tại và epoch kế tiếp. Nhờ vậy ai cũng biết trước một cách
> tất định proposer của epoch kế tiếp, không bị thay đổi bởi các biến động
> effective balance xảy ra trong lúc chờ.

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
    latest_execution_payload_header: ExecutionPayloadHeader
    next_withdrawal_index: WithdrawalIndex
    next_withdrawal_validator_index: ValidatorIndex
    historical_summaries: HistoricalSummaries
    deposit_requests_start_index: Uint64
    deposit_balance_to_consume: Gwei
    exit_balance_to_consume: Gwei
    earliest_exit_epoch: Epoch
    consolidation_balance_to_consume: Gwei
    earliest_consolidation_epoch: Epoch
    pending_deposits: PendingDeposits
    pending_partial_withdrawals: PendingPartialWithdrawals
    pending_consolidations: PendingConsolidations
    # [New in Fulu:EIP7917]
    proposer_lookahead: ProposerLookahead
```

## Helpers

### Misc

#### New `BlobParameters`

```python
@dataclass
class BlobParameters:
    epoch: Epoch
    max_blobs_per_block: Uint64
```

#### New `get_blob_parameters`

> 💡 Ghi chú: Hàm duyệt `BLOB_SCHEDULE` theo epoch giảm dần và trả về entry gần
> nhất có epoch nhỏ hơn hoặc bằng `epoch` đầu vào. Nếu không có entry nào phù
> hợp (ví dụ schedule rỗng), dùng giá trị mặc định của Electra.

```python
def get_blob_parameters(epoch: Epoch) -> BlobParameters:
    """
    Return the blob parameters at a given epoch.
    """
    for entry in sorted(BLOB_SCHEDULE, key=lambda e: e["EPOCH"], reverse=True):
        if epoch >= entry["EPOCH"]:
            return BlobParameters(entry["EPOCH"], entry["MAX_BLOBS_PER_BLOCK"])
    return BlobParameters(ELECTRA_FORK_EPOCH, MAX_BLOBS_PER_BLOCK_ELECTRA)
```

#### Modified `compute_fork_digest`

*Ghi chú*: Helper `compute_fork_digest` được cập nhật để tính đến các fork chỉ
thay đổi tham số blob (Blob-Parameters-Only fork).

> 💡 Ghi chú: Một BPO fork không đổi fork version, nên nếu chỉ dùng fork version
> thì fork digest sẽ không đổi. Để các node có blob parameters khác nhau tách
> biệt được trên tầng p2p, từ Fulu fork digest được XOR thêm với hash của blob
> parameters đang có hiệu lực.

```python
def compute_fork_digest(
    genesis_validators_root: Root,
    epoch: Epoch,
) -> ForkDigest:
    """
    Return the 4-byte fork digest for the ``genesis_validators_root`` at a given ``epoch``.

    This is a digest primarily used for domain separation on the p2p layer.
    4-bytes suffices for practical separation of forks/chains.
    """
    fork_version = compute_fork_version(epoch)
    base_digest = compute_fork_data_root(fork_version, genesis_validators_root)

    # [New in Fulu:EIP7892]
    if epoch < FULU_FORK_EPOCH:
        return ForkDigest(base_digest[:4])

    # [Modified in Fulu:EIP7892]
    # XOR digest với hash của blob parameters
    blob_parameters = get_blob_parameters(epoch)
    return ForkDigest(
        xor(
            base_digest,
            sha256(
                uint_to_bytes(Uint64(blob_parameters.epoch))
                + uint_to_bytes(Uint64(blob_parameters.max_blobs_per_block))
            ),
        )[:4]
    )
```

#### New `compute_proposer_indices`

> 💡 Ghi chú: Hàm tính proposer index cho từng slot trong `epoch`. Seed riêng
> của mỗi slot được tạo bằng cách hash seed của epoch với số slot tương ứng.

```python
def compute_proposer_indices(
    state: BeaconState, epoch: Epoch, seed: Bytes32, indices: Sequence[ValidatorIndex]
) -> ProposerIndices:
    """
    Return the proposer indices for the given ``epoch``.
    """
    start_slot = compute_start_slot_at_epoch(epoch)
    seeds = [sha256(seed + uint_to_bytes(start_slot + index)) for index in range(SLOTS_PER_EPOCH)]
    return ProposerIndices(data=[compute_proposer_index(state, indices, seed) for seed in seeds])
```

### Beacon state accessors

#### Modified `get_beacon_proposer_index`

*Ghi chú*: Hàm `get_beacon_proposer_index` được sửa đổi để dùng giá trị
`proposer_lookahead` đã được tính sẵn, thay vì tính toán lại mỗi khi được gọi.

```python
def get_beacon_proposer_index(state: BeaconState) -> ValidatorIndex:
    """
    Return the beacon proposer index at the current slot.
    """
    return state.proposer_lookahead[state.slot % SLOTS_PER_EPOCH]
```

#### New `get_beacon_proposer_indices`

```python
def get_beacon_proposer_indices(state: BeaconState, epoch: Epoch) -> ProposerIndices:
    """
    Return the proposer indices for the given ``epoch``.
    """
    indices = get_active_validator_indices(state, epoch)
    seed = get_seed(state, epoch, DOMAIN_BEACON_PROPOSER)
    return compute_proposer_indices(state, epoch, seed, indices)
```

### Epoch processing

#### Modified `process_epoch`

*Ghi chú*: Ở Fulu, hàm `process_epoch` được sửa đổi để gọi thêm
`process_proposer_lookahead` nhằm cập nhật `proposer_lookahead` trong beacon
state.

```python
def process_epoch(state: BeaconState) -> None:
    process_justification_and_finalization(state)
    process_inactivity_updates(state)
    process_rewards_and_penalties(state)
    process_registry_updates(state)
    process_slashings(state)
    process_eth1_data_reset(state)
    process_pending_deposits(state)
    process_pending_consolidations(state)
    process_effective_balance_updates(state)
    process_slashings_reset(state)
    process_randao_mixes_reset(state)
    process_historical_summaries_update(state)
    process_participation_flag_updates(state)
    process_sync_committee_updates(state)
    # [New in Fulu:EIP7917]
    process_proposer_lookahead(state)
```

#### Modified `process_pending_deposits`

*Ghi chú*: Hàm `process_pending_deposits` được sửa đổi để loại bỏ hỗ trợ cho cơ
chế deposit cũ.

> 💡 Ghi chú: So với Electra, điều kiện dừng liên quan đến
> `deposit_requests_start_index` / `eth1_deposit_index` (dùng để chờ các deposit
> theo cơ chế cũ được xử lý xong) đã bị bỏ. Giờ một deposit chỉ cần đã được
> finalized, còn nằm trong giới hạn số lượng mỗi epoch và vừa với churn.

```python
def process_pending_deposits(state: BeaconState) -> None:
    next_epoch = get_current_epoch(state) + 1
    available_for_processing = state.deposit_balance_to_consume + get_activation_exit_churn_limit(
        state
    )
    processed_amount = 0
    next_deposit_index = 0
    deposits_to_postpone = []
    is_churn_limit_reached = False
    finalized_slot = compute_start_slot_at_epoch(state.finalized_checkpoint.epoch)

    for deposit in state.pending_deposits:
        # Kiểm tra deposit đã được finalized chưa; nếu chưa thì dừng xử lý.
        if deposit.slot > finalized_slot:
            break

        # Kiểm tra số deposit đã xử lý chưa chạm giới hạn; nếu đã chạm thì dừng xử lý.
        if next_deposit_index >= MAX_PENDING_DEPOSITS_PER_EPOCH:
            break

        # Đọc trạng thái của validator
        is_validator_exited = False
        is_validator_withdrawn = False
        validator_pubkeys = [validator.pubkey for validator in state.validators]
        if deposit.pubkey in validator_pubkeys:
            validator = state.validators[ValidatorIndex(validator_pubkeys.index(deposit.pubkey))]
            is_validator_exited = validator.exit_epoch < FAR_FUTURE_EPOCH
            is_validator_withdrawn = validator.withdrawable_epoch < next_epoch

        if is_validator_withdrawn:
            # Balance được deposit sẽ không bao giờ active. Tăng balance nhưng không tiêu thụ churn
            apply_pending_deposit(state, deposit)
        elif is_validator_exited:
            # Validator đang exit, hoãn deposit đến sau withdrawable epoch
            deposits_to_postpone.append(deposit)
        else:
            # Kiểm tra deposit có vừa churn không; nếu không thì ngừng xử lý deposit trong epoch này.
            is_churn_limit_reached = processed_amount + deposit.amount > available_for_processing
            if is_churn_limit_reached:
                break

            # Tiêu thụ churn và áp dụng deposit.
            processed_amount += deposit.amount
            apply_pending_deposit(state, deposit)

        # Dù deposit được xử lý theo cách nào, ta vẫn tiến tới phần tử tiếp theo trong hàng đợi.
        next_deposit_index += 1

    state.pending_deposits = state.pending_deposits[next_deposit_index:] + deposits_to_postpone

    # Chỉ tích lũy churn nếu đã chạm giới hạn churn.
    if is_churn_limit_reached:
        state.deposit_balance_to_consume = available_for_processing - processed_amount
    else:
        state.deposit_balance_to_consume = Gwei(0)
```

#### New `process_proposer_lookahead`

*Ghi chú*: Hàm này cập nhật trường `proposer_lookahead` trong beacon state bằng
cách đẩy bỏ (shift out) các proposer index của epoch sớm nhất và nối thêm các
proposer index mới cho epoch xa nhất. Với `MIN_SEED_LOOKAHEAD` bằng `1`, điều
này có nghĩa là tại đầu epoch `N`, proposer lookahead cho epoch `N+1` sẽ được
tính và đưa vào lookahead của beacon state.

```python
def process_proposer_lookahead(state: BeaconState) -> None:
    last_epoch_start = len(state.proposer_lookahead) - SLOTS_PER_EPOCH
    # Đẩy bỏ các proposer của epoch đầu tiên
    state.proposer_lookahead[:last_epoch_start] = state.proposer_lookahead[SLOTS_PER_EPOCH:]
    # Điền epoch cuối cùng bằng các proposer index mới
    last_epoch_proposers = get_beacon_proposer_indices(
        state, get_current_epoch(state) + MIN_SEED_LOOKAHEAD + 1
    )
    state.proposer_lookahead[last_epoch_start:] = last_epoch_proposers
```
