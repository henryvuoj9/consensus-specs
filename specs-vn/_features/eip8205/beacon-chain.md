# EIP-8205 -- The Beacon Chain

*Lưu ý*: Tài liệu này đang trong quá trình soạn thảo, dành cho các nhà nghiên cứu
và những người triển khai (implementer).

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Types](#types)
  - [New `PreregistrationRequests`](#new-preregistrationrequests)
  - [New `ValidatorPreregistrations`](#new-validatorpreregistrations)
- [Constants](#constants)
  - [Domains](#domains)
  - [Execution-layer triggered requests](#execution-layer-triggered-requests)
- [Presets](#presets)
  - [Execution](#execution)
- [Containers](#containers)
  - [Modified containers](#modified-containers)
    - [`BeaconState`](#beaconstate)
    - [`ExecutionRequests`](#executionrequests)
  - [New containers](#new-containers)
    - [`ValidatorPreregistration`](#validatorpreregistration)
    - [`PreregistrationRequest`](#preregistrationrequest)
    - [`StoredPreregistration`](#storedpreregistration)
- [Helper functions](#helper-functions)
  - [Predicates](#predicates)
    - [New `is_valid_preregistration_signature`](#new-is_valid_preregistration_signature)
    - [New `is_active_preregistration`](#new-is_active_preregistration)
  - [Misc](#misc)
    - [New `get_stored_preregistration_index`](#new-get_stored_preregistration_index)
    - [New `get_active_preregistration`](#new-get_active_preregistration)
    - [New `remove_stored_preregistration`](#new-remove_stored_preregistration)
- [Beacon chain state transition function](#beacon-chain-state-transition-function)
  - [Epoch processing](#epoch-processing)
    - [Modified `process_epoch`](#modified-process_epoch)
    - [New `process_preregistration_expiry`](#new-process_preregistration_expiry)
  - [Block processing](#block-processing)
    - [Execution payload](#execution-payload)
      - [Modified `get_execution_requests_list`](#modified-get_execution_requests_list)
    - [Operations](#operations)
      - [New `process_preregistration_request`](#new-process_preregistration_request)
      - [Modified `process_deposit_request`](#modified-process_deposit_request)
    - [Parent execution payload](#parent-execution-payload)
      - [Modified `apply_parent_execution_payload`](#modified-apply_parent_execution_payload)

<!-- mdformat-toc end -->

## Introduction

Bản nâng cấp này bổ sung cơ chế *đăng ký trước withdrawal credentials*
(preregistration) vào beacon chain, như một phần của EIP-8205. Một
preregistration gắn (bind) một validator pubkey với một bộ withdrawal credentials
*trước khi* deposit đầu tiên của validator đó được xử lý. Nhờ vậy, các hệ thống
delegated staking (staking ủy thác) được bảo vệ trước tấn công deposit
front-running.

> 💡 Ghi chú: Trong tấn công deposit front-running, một bên (ví dụ node operator)
> nắm private key của validator có thể gửi trước một deposit cho cùng pubkey nhưng
> với withdrawal credentials do chính họ kiểm soát. Vì withdrawal credentials của
> validator được xác định bởi deposit *đầu tiên* được xử lý, deposit sau của người
> ủy thác sẽ chảy vào validator có withdrawal credentials sai. Preregistration
> khóa trước withdrawal credentials đúng để chặn kịch bản này.

Tài liệu này đặc tả các thay đổi trên beacon chain cần thiết để hỗ trợ các
preregistration. Bản nâng cấp giới thiệu một loại request mới nằm trong execution
payload, được kích hoạt bởi các giao dịch ở execution layer. Request này lưu một
liên kết pubkey → withdrawal credentials vào beacon state. Trong khi liên kết còn
hiệu lực (active), mọi deposit request cho pubkey đã được bind sẽ bị loại bỏ, trừ
khi withdrawal credentials của nó khớp với liên kết **và** signature của nó hợp
lệ.

*Lưu ý*: Đặc tả này được xây dựng dựa trên [Heze](../../heze/beacon-chain.md).

## Types

### New `PreregistrationRequests`

```python
class PreregistrationRequests(ProgressiveList[PreregistrationRequest]):
    """
    The preregistration requests pertaining to a single execution payload.
    """
```

### New `ValidatorPreregistrations`

```python
class ValidatorPreregistrations(ProgressiveList[StoredPreregistration]):
    """
    The preregistrations stored in the beacon state, including expired
    records not yet garbage-collected.
    """
```

## Constants

### Domains

*Lưu ý*: Signature của preregistration dùng một domain không phụ thuộc fork
(fork-agnostic), được tính bằng `compute_domain`. Do đó, một preregistration chỉ
cần ký một lần là vẫn hợp lệ qua các ranh giới fork, giống như deposit signature.
Khác với deposit signature, domain này được gắn với một chain cụ thể thông qua
`genesis_validators_root`, nhờ đó ngăn chặn việc phát lại (replay) chữ ký sang
mạng khác.

| Name                     | Value                      |
| ------------------------ | -------------------------- |
| `DOMAIN_PREREGISTRATION` | `DomainType("0x11000000")` |

### Execution-layer triggered requests

| Name                           | Value            |
| ------------------------------ | ---------------- |
| `PREREGISTRATION_REQUEST_TYPE` | `Bytes1("0x05")` |

## Presets

### Execution

| Name                                       | Value                       |
| ------------------------------------------ | --------------------------- |
| `MAX_PREREGISTRATION_REQUESTS_PER_PAYLOAD` | `Uint64(2**2)` (= 4)        |
| `PREREGISTRATIONS_LIMIT`                   | `Uint64(2**19)` (= 524,288) |
| `PREREGISTRATION_EXPIRY_SLOTS`             | `Slot(2**18)` (= 262,144)   |

> 💡 Ghi chú: `PREREGISTRATION_EXPIRY_SLOTS` = 262,144 slot, tương đương khoảng
> 36 ngày với slot 12 giây. `PREREGISTRATIONS_LIMIT` là số preregistration *đang
> active* tối đa được lưu trong state.

## Containers

### Modified containers

#### `BeaconState`

```python
class BeaconState(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=47, gaps=(8, 9, 10, 28))

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
    # [New in EIP8205]
    validator_preregistrations: ValidatorPreregistrations
```

#### `ExecutionRequests`

```python
class ExecutionRequests(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=6)

    deposits: DepositRequests
    withdrawals: WithdrawalRequests
    consolidations: ConsolidationRequests
    builder_deposits: BuilderDepositRequests
    builder_exits: BuilderExitRequests
    # [New in EIP8205]
    preregistrations: PreregistrationRequests
```

### New containers

#### `ValidatorPreregistration`

*Lưu ý*: Đây là container dùng để ký (signing container) cho signature của
preregistration — tức là đối tượng mà signing root được tính trên đó.

```python
class ValidatorPreregistration(Container):
    pubkey: BLSPubkey
    withdrawal_credentials: Bytes32
```

#### `PreregistrationRequest`

```python
class PreregistrationRequest(Container):
    pubkey: BLSPubkey
    withdrawal_credentials: Bytes32
    signature: BLSSignature
```

#### `StoredPreregistration`

*Lưu ý*: `expiry_slot` là hạn chót tuyệt đối (một slot cụ thể), được tính tại thời
điểm preregistration được lưu vào state. Vì vậy, nếu sau này giá trị
`PREREGISTRATION_EXPIRY_SLOTS` thay đổi, điều đó chỉ ảnh hưởng tới các bản ghi
được lưu mới, không ảnh hưởng tới các bản ghi đã có.

```python
class StoredPreregistration(Container):
    pubkey: BLSPubkey
    withdrawal_credentials: Bytes32
    expiry_slot: Slot
```

## Helper functions

### Predicates

#### New `is_valid_preregistration_signature`

```python
def is_valid_preregistration_signature(state: BeaconState, request: PreregistrationRequest) -> bool:
    preregistration = ValidatorPreregistration(
        pubkey=request.pubkey,
        withdrawal_credentials=request.withdrawal_credentials,
    )
    domain = compute_domain(
        DOMAIN_PREREGISTRATION,
        genesis_validators_root=state.genesis_validators_root,
    )
    signing_root = compute_signing_root(preregistration, domain)
    return bls.Verify(request.pubkey, signing_root, request.signature)
```

> 💡 Ghi chú: Signature phải được tạo bằng private key tương ứng với chính
> `pubkey` được đăng ký, nghĩa là chỉ người nắm giữ key của validator mới có thể
> tạo preregistration cho pubkey đó.

#### New `is_active_preregistration`

*Lưu ý*: Tính "active" được đánh giá dựa trên slot của parent payload đang chờ xử
lý (outstanding parent payload) — chính là payload có các execution request đang
được áp dụng trong quá trình block processing. Do đó, một khi đã được lưu, liên
kết vẫn active đối với các payload được xử lý sau đó có slot nhỏ hơn `expiry_slot`
đã lưu, bất kể bản ghi hết hạn được dọn khỏi state (sweep) vào lúc nào.

```python
def is_active_preregistration(state: BeaconState, preregistration: StoredPreregistration) -> bool:
    parent_slot = state.latest_execution_payload_bid.slot
    return parent_slot < preregistration.expiry_slot
```

### Misc

*Lưu ý*: Các implementation nên duy trì chỉ mục phụ (secondary index) theo pubkey
cho `validator_preregistrations` và `pending_deposits`, thay vì quét tuyến tính
như được minh họa ở đây. Khi xóa phần tử, phải giữ nguyên thứ tự của các phần tử
còn lại, vì thứ tự này ảnh hưởng tới consensus thông qua state root. Do state root
chỉ được tính sau khi block processing hoàn tất, các implementation SHOULD NOT
dựng lại toàn bộ list mỗi lần xóa một bản ghi: có thể đánh dấu (tombstone) các bản
ghi đã dùng trong lúc xử lý request, rồi nén (compact) list một lần duy nhất cho
mỗi block — cách này cho ra post-state giống hệt.

#### New `get_stored_preregistration_index`

```python
def get_stored_preregistration_index(state: BeaconState, pubkey: BLSPubkey) -> Uint64 | None:
    for index, preregistration in enumerate(state.validator_preregistrations):
        if preregistration.pubkey == pubkey:
            return Uint64(index)
    return None
```

#### New `get_active_preregistration`

```python
def get_active_preregistration(
    state: BeaconState, pubkey: BLSPubkey
) -> StoredPreregistration | None:
    index = get_stored_preregistration_index(state, pubkey)
    if index is None:
        return None
    preregistration = state.validator_preregistrations[index]
    if not is_active_preregistration(state, preregistration):
        return None
    return preregistration
```

#### New `remove_stored_preregistration`

```python
def remove_stored_preregistration(state: BeaconState, pubkey: BLSPubkey) -> None:
    state.validator_preregistrations = ValidatorPreregistrations(
        data=[
            preregistration
            for preregistration in state.validator_preregistrations
            if preregistration.pubkey != pubkey
        ]
    )
```

## Beacon chain state transition function

### Epoch processing

#### Modified `process_epoch`

```python
def process_epoch(state: BeaconState) -> None:
    process_justification_and_finalization(state)
    process_inactivity_updates(state)
    process_rewards_and_penalties(state)
    process_registry_updates(state)
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
    # [New in EIP8205]
    process_preregistration_expiry(state)
```

#### New `process_preregistration_expiry`

*Lưu ý*: Bước sweep này chỉ đơn thuần là dọn rác (garbage collection): việc thực
thi liên kết được quyết định bởi `is_active_preregistration`, nên thời điểm sweep
không ảnh hưởng tới việc một liên kết có được thực thi hay một request có được
chấp nhận hay không; và việc hết hạn cũng độc lập với finality. Vì thế, một bản ghi
đã hết hạn có thể vẫn nằm trong state cho tới lần sweep kế tiếp. Việc tái sử dụng
cùng một predicate (vốn dựa trên parent bid đang chờ xử lý) đảm bảo rằng một bản
ghi không bao giờ bị xóa khi một payload mà nó vẫn còn bao phủ vẫn đang chờ xử lý.

```python
def process_preregistration_expiry(state: BeaconState) -> None:
    state.validator_preregistrations = ValidatorPreregistrations(
        data=[
            preregistration
            for preregistration in state.validator_preregistrations
            if is_active_preregistration(state, preregistration)
        ]
    )
```

### Block processing

#### Execution payload

##### Modified `get_execution_requests_list`

```python
def get_execution_requests_list(execution_requests: ExecutionRequests) -> Sequence[bytes]:
    requests: Sequence[tuple[Bytes1, ProgressiveList]] = [
        (DEPOSIT_REQUEST_TYPE, execution_requests.deposits),
        (WITHDRAWAL_REQUEST_TYPE, execution_requests.withdrawals),
        (CONSOLIDATION_REQUEST_TYPE, execution_requests.consolidations),
        (BUILDER_DEPOSIT_REQUEST_TYPE, execution_requests.builder_deposits),
        (BUILDER_EXIT_REQUEST_TYPE, execution_requests.builder_exits),
        # [New in EIP8205]
        (PREREGISTRATION_REQUEST_TYPE, execution_requests.preregistrations),
    ]

    return [
        request_type + ssz_serialize(request_data)
        for request_type, request_data in requests
        if len(request_data) != 0
    ]
```

#### Operations

##### New `process_preregistration_request`

```python
def process_preregistration_request(state: BeaconState, request: PreregistrationRequest) -> None:
    pubkey = request.pubkey

    # Nếu pubkey này đã có một liên kết đang active thì request mới không có tác dụng,
    # dù nó trùng khớp hoàn toàn hay mâu thuẫn với liên kết hiện có
    if get_active_preregistration(state, pubkey) is not None:
        return

    # Không thể preregister một pubkey đã thuộc về một validator hiện có
    if pubkey in [validator.pubkey for validator in state.validators]:
        return

    # Không thể preregister một pubkey đang có pending deposit hợp lệ
    if is_pending_validator(state.pending_deposits, pubkey):
        return

    # Kiểm tra sức chứa chỉ đếm các bản ghi active, nên thời điểm của bước
    # sweep dọn rác không ảnh hưởng tới việc chấp nhận. Kiểm tra này áp dụng cho cả
    # việc thêm mới lẫn thay thế, vì cả hai đều tạo ra một liên kết active
    active_preregistrations = [
        preregistration
        for preregistration in state.validator_preregistrations
        if is_active_preregistration(state, preregistration)
    ]
    if len(active_preregistrations) >= PREREGISTRATIONS_LIMIT:
        return

    if not is_valid_preregistration_signature(state, request):
        return

    preregistration = StoredPreregistration(
        pubkey=pubkey,
        withdrawal_credentials=request.withdrawal_credentials,
        expiry_slot=state.slot + PREREGISTRATION_EXPIRY_SLOTS,
    )
    index = get_stored_preregistration_index(state, pubkey)
    if index is not None:
        # Thay thế tại chỗ bản ghi đã hết hạn
        state.validator_preregistrations[index] = preregistration
    else:
        state.validator_preregistrations.append(preregistration)
```

> 💡 Ghi chú: Tóm lại, một preregistration request chỉ được lưu khi: (1) pubkey
> chưa có liên kết active, (2) pubkey chưa là validator, (3) pubkey chưa có pending
> deposit hợp lệ, (4) số preregistration active chưa đạt `PREREGISTRATIONS_LIMIT`,
> và (5) signature hợp lệ. Mọi request không thỏa mãn đều bị bỏ qua lặng lẽ (no-op),
> không làm block bị coi là không hợp lệ.

##### Modified `process_deposit_request`

*Lưu ý*: Hàm `process_deposit_request` được sửa đổi để thực thi liên kết
preregistration đang active.

```python
def process_deposit_request(state: BeaconState, deposit_request: DepositRequest) -> None:
    # [New in EIP8205]
    preregistration = get_active_preregistration(state, deposit_request.pubkey)
    if preregistration is not None:
        if deposit_request.withdrawal_credentials != preregistration.withdrawal_credentials:
            return

        if not is_valid_deposit_signature(
            deposit_request.pubkey,
            deposit_request.withdrawal_credentials,
            deposit_request.amount,
            deposit_request.signature,
        ):
            return

        remove_stored_preregistration(state, deposit_request.pubkey)

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

> 💡 Ghi chú: Khi có liên kết active, deposit có withdrawal credentials sai hoặc
> signature không hợp lệ sẽ bị loại bỏ (không được thêm vào `pending_deposits`).
> Deposit hợp lệ đầu tiên khớp với liên kết sẽ "tiêu thụ" preregistration (xóa bản
> ghi khỏi state); sau đó pubkey này trở thành pending validator nên các deposit
> tiếp theo được xử lý như bình thường.

#### Parent execution payload

##### Modified `apply_parent_execution_payload`

*Lưu ý*: Các preregistration được xử lý sau cùng, để khi một execution payload chứa
cả một deposit và một preregistration cho cùng một pubkey thì vẫn giữ hành vi
"deposit trước" như EIP-8205 đã quy định.

> 💡 Ghi chú: Nghĩa là deposit được xử lý trước (khi chưa có liên kết nào), pubkey
> trở thành pending validator, và preregistration xử lý sau đó sẽ bị bỏ qua vì
> pubkey đã có pending deposit hợp lệ.

```python
def apply_parent_execution_payload(
    state: BeaconState,
    requests: ExecutionRequests,
) -> None:
    parent_bid = state.latest_execution_payload_bid
    parent_slot = parent_bid.slot
    parent_epoch = compute_epoch_at_slot(parent_slot)

    assert len(requests.withdrawals) <= MAX_WITHDRAWAL_REQUESTS_PER_PAYLOAD
    assert len(requests.consolidations) <= MAX_CONSOLIDATION_REQUESTS_PER_PAYLOAD
    assert len(requests.builder_deposits) <= MAX_BUILDER_DEPOSIT_REQUESTS_PER_PAYLOAD
    assert len(requests.builder_exits) <= MAX_BUILDER_EXIT_REQUESTS_PER_PAYLOAD
    # [New in EIP8205]
    assert len(requests.preregistrations) <= MAX_PREREGISTRATION_REQUESTS_PER_PAYLOAD

    # Thanh toán cho builder trước khi xử lý các request, để một builder exit
    # request sẽ bị từ chối khi khoản thanh toán vẫn đang chờ
    if parent_epoch == get_current_epoch(state):
        payment_index = SLOTS_PER_EPOCH + parent_slot % SLOTS_PER_EPOCH
        settle_builder_payment(state, payment_index)
    elif parent_epoch == get_previous_epoch(state):
        payment_index = parent_slot % SLOTS_PER_EPOCH
        settle_builder_payment(state, payment_index)
    elif parent_bid.value > 0:
        # Parent cũ hơn epoch trước, mục thanh toán của nó đã bị loại khỏi
        # builder_pending_payments. Thêm trực tiếp withdrawal vào hàng đợi.
        state.builder_pending_withdrawals.append(
            BuilderPendingWithdrawal(
                fee_recipient=parent_bid.fee_recipient,
                amount=parent_bid.value,
                builder_index=parent_bid.builder_index,
            )
        )

    # Xử lý các execution request từ payload của parent. Các execution
    # request được xử lý tại state.slot (slot của child), không phải slot của parent.
    def for_ops(operations: Sequence[Any], fn: Callable[[BeaconState, Any], None]) -> None:
        for operation in operations:
            fn(state, operation)

    for_ops(requests.deposits, process_deposit_request)
    for_ops(requests.withdrawals, process_withdrawal_request)
    for_ops(requests.consolidations, process_consolidation_request)
    for_ops(requests.builder_deposits, process_builder_deposit_request)
    for_ops(requests.builder_exits, process_builder_exit_request)
    # [New in EIP8205]
    for_ops(requests.preregistrations, process_preregistration_request)

    # Cập nhật trạng thái availability của parent payload và latest block hash
    state.execution_payload_availability[parent_slot % SLOTS_PER_HISTORICAL_ROOT] = Boolean(True)
    state.latest_block_hash = parent_bid.block_hash
```
