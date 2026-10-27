# Gloas -- Honest Validator

*Lưu ý*: Tài liệu này vẫn đang trong quá trình hoàn thiện, dành cho các nhà
nghiên cứu và đội ngũ triển khai client.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Configs](#configs)
  - [Time parameters](#time-parameters)
- [Validator assignment](#validator-assignment)
  - [Payload timeliness committee](#payload-timeliness-committee)
  - [Lookahead](#lookahead)
- [Beacon chain responsibilities](#beacon-chain-responsibilities)
  - [Attestation](#attestation)
  - [Sync Committee participations](#sync-committee-participations)
  - [Block and sidecar proposal](#block-and-sidecar-proposal)
    - [Broadcasting `SignedProposerPreferences`](#broadcasting-signedproposerpreferences)
    - [Constructing the `BeaconBlockBody`](#constructing-the-beaconblockbody)
      - [Signed execution payload bid](#signed-execution-payload-bid)
      - [Payload attestations](#payload-attestations)
      - [Parent execution requests](#parent-execution-requests)
      - [Execution requests](#execution-requests)
      - [ExecutionPayload](#executionpayload)
      - [Voluntary exits](#voluntary-exits)
  - [Payload timeliness attestation](#payload-timeliness-attestation)
    - [Constructing the `PayloadAttestationMessage`](#constructing-the-payloadattestationmessage)
- [Modified functions](#modified-functions)
  - [Modified `get_data_column_sidecars_from_column_sidecar`](#modified-get_data_column_sidecars_from_column_sidecar)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả những thay đổi cần thực hiện trong code của một "honest
validator" (validator trung thực, tuân thủ đúng giao thức) để triển khai Gloas.

> 💡 Ghi chú: Thay đổi trọng tâm của Gloas là EIP-7732 (ePBS – enshrined
> proposer-builder separation). Proposer không còn tự đưa execution payload vào
> block mà chọn một bid đã ký từ builder; builder sau đó công bố payload trong một
> envelope riêng, và một committee mới là PTC sẽ attest xem payload có được công
> bố đúng hạn hay không.

## Configs

### Time parameters

| Name                          | Value          | Duration                    |
| ----------------------------- | -------------- | --------------------------- |
| `ATTESTATION_DUE_BPS_GLOAS`   | `Uint64(2500)` | 25% của `SLOT_DURATION_MS` |
| `AGGREGATE_DUE_BPS_GLOAS`     | `Uint64(5000)` | 50% của `SLOT_DURATION_MS` |
| `SYNC_MESSAGE_DUE_BPS_GLOAS`  | `Uint64(2500)` | 25% của `SLOT_DURATION_MS` |
| `CONTRIBUTION_DUE_BPS_GLOAS`  | `Uint64(5000)` | 50% của `SLOT_DURATION_MS` |
| `PAYLOAD_DUE_BPS`             | `Uint64(5000)` | 50% của `SLOT_DURATION_MS` |
| `PAYLOAD_ATTESTATION_DUE_BPS` | `Uint64(7500)` | 75% của `SLOT_DURATION_MS` |

> 💡 Ghi chú: "BPS" là basis points (1 bps = 0,01%), nên `2500` bps nghĩa là
> 25% thời lượng slot. Các mốc này tính từ đầu slot.

## Validator assignment

### Payload timeliness committee

Một validator có thể là thành viên của Payload Timeliness Committee (PTC –
committee xác nhận payload được công bố đúng hạn) mới cho một slot nhất định. Để
kiểm tra nhiệm vụ PTC, dùng `get_ptc_assignment(state, epoch, validator_index)`
với điều kiện `epoch <= get_current_epoch(state) + MIN_SEED_LOOKAHEAD`, vì việc
chọn thành viên PTC chỉ ổn định trong phạm vi epoch hiện tại và epoch kế tiếp
trong lookahead.

```python
def get_ptc_assignment(
    state: BeaconState, epoch: Epoch, validator_index: ValidatorIndex
) -> Slot | None:
    """
    Returns the slot during the requested epoch in which the validator with
    index ``validator_index`` is a member of the PTC. Returns None if no
    assignment is found.
    """
    max_epoch = get_current_epoch(state) + MIN_SEED_LOOKAHEAD
    assert epoch <= max_epoch

    start_slot = compute_start_slot_at_epoch(epoch)
    for slot in range(start_slot, start_slot + SLOTS_PER_EPOCH):
        if validator_index in get_ptc(state, Slot(slot)):
            return Slot(slot)
    return None
```

### Lookahead

`get_ptc_assignment` nên được gọi vào đầu mỗi epoch để lấy nhiệm vụ cho epoch kế
tiếp (`current_epoch + 1`). Validator nên lên kế hoạch cho các nhiệm vụ tương lai
bằng cách ghi nhớ slot PTC mà mình được phân công.

## Beacon chain responsibilities

Mọi trách nhiệm của validator đều giữ nguyên, ngoại trừ các điểm sau:

- Proposer không còn phải broadcast các đối tượng `DataColumnSidecar` nữa, vì
  việc này trở thành nhiệm vụ của builder.
- Mỗi slot, một số attester được chọn làm thành viên PTC; các validator này phải
  broadcast các đối tượng `PayloadAttestationMessage` trong slot được phân công,
  trước hạn chót `get_payload_attestation_due_ms()` mili giây tính từ đầu slot.

### Attestation

Hạn chót attestation được thay đổi theo `ATTESTATION_DUE_BPS_GLOAS`. Ngoài ra,
trường `attestation.data.index` giờ đây được dùng để báo hiệu trạng thái payload
của block đang được attest (`attestation.data.beacon_block_root`). Đặt alias
`data = attestation.data`, validator nên đặt giá trị trường này như sau:

- Nếu `block.slot == current_slot` (tức là `data.slot`), thì luôn đặt
  `data.index = 0`.
- Ngược lại, đặt `data.index` dựa trên trạng thái payload trong fork-choice của
  validator:
  - Đặt `data.index = 0` để báo hiệu payload không có mặt trong canonical chain
    (trạng thái payload là `EMPTY` trong fork-choice).
  - Đặt `data.index = 1` để báo hiệu payload có mặt trong canonical chain (trạng
    thái payload là `FULL` trong fork-choice).

> 💡 Ghi chú: Khi block thuộc chính slot hiện tại, payload của nó chưa được công
> bố tại thời điểm attest (payload đến muộn hơn, khoảng giữa slot), nên attester
> không thể nói gì về payload và luôn đặt `0`. Trạng thái payload của block hiện
> tại sẽ do PTC xác nhận.

### Sync Committee participations

Nhiệm vụ sync committee của validator không thay đổi, tuy nhiên hạn chót gửi được
thay đổi theo `SYNC_MESSAGE_DUE_BPS_GLOAS`.

### Block and sidecar proposal

Validator vẫn được kỳ vọng propose `SignedBeaconBlock` vào đầu bất kỳ slot nào mà
`is_proposer(state, validator_index)` trả về `True`. Cơ chế chuẩn bị beacon block
này và các sidecar liên quan khác với các fork trước như sau

#### Broadcasting `SignedProposerPreferences`

Validator MAY broadcast các message `SignedProposerPreferences` lên gossip topic
`proposer_preferences` cho mỗi slot được trả về bởi
`get_upcoming_proposal_slots(state, validator_index)`. Các slot này bao gồm mọi
slot propose trong tương lai nằm trong proposer lookahead, tức là từ epoch hiện
tại cho tới `MIN_SEED_LOOKAHEAD` epoch phía trước. Điều này cho phép builder xây
dựng execution payload với `fee_recipient` và `target_gas_limit` mà validator
mong muốn. Nếu validator không broadcast message `SignedProposerPreferences`,
điều đó ngụ ý rằng validator sẽ không chấp nhận bất kỳ bid trustless nào (bid từ
builder bên ngoài, được giao thức đảm bảo thanh toán) cho slot đó.

```python
def get_upcoming_proposal_slots(
    state: BeaconState, validator_index: ValidatorIndex
) -> Sequence[Slot]:
    """
    Get the future slots within the proposer lookahead for which
    ``validator_index`` is proposing.
    """
    current_epoch_start_slot = compute_start_slot_at_epoch(get_current_epoch(state))
    upcoming_proposal_slots = []
    for offset, proposer_index in enumerate(state.proposer_lookahead):
        slot = current_epoch_start_slot + offset
        if slot <= state.slot:
            continue
        if validator_index == proposer_index:
            upcoming_proposal_slots.append(slot)
    return upcoming_proposal_slots
```

Validator tạo mỗi `SignedProposerPreferences` bằng
`get_signed_proposer_preferences` cho mỗi `proposal_slot` trong
`get_upcoming_proposal_slots(state, validator_index)`. Gọi `head_root` là head
root hiện tại của validator, `fee_recipient` là địa chỉ execution nơi validator
muốn nhận khoản thanh toán từ builder, và `target_gas_limit` là gas limit mà
validator mong muốn cho execution payload.

```python
def get_signed_proposer_preferences(
    store: Store,
    state: BeaconState,
    head_root: Root,
    proposal_slot: Slot,
    validator_index: ValidatorIndex,
    fee_recipient: ExecutionAddress,
    target_gas_limit: Uint64,
    privkey: int,
) -> SignedProposerPreferences:
    proposal_epoch = compute_epoch_at_slot(proposal_slot)
    dependent_root = get_shuffling_dependent_root(store, head_root, proposal_epoch)
    preferences = ProposerPreferences(
        dependent_root=dependent_root,
        proposal_slot=proposal_slot,
        validator_index=validator_index,
        fee_recipient=fee_recipient,
        target_gas_limit=target_gas_limit,
    )
    domain = compute_domain(
        DOMAIN_PROPOSER_PREFERENCES,
        compute_fork_version(proposal_epoch),
        state.genesis_validators_root,
    )
    signing_root = compute_signing_root(preferences, domain)
    signature = bls.Sign(privkey, signing_root)
    return SignedProposerPreferences(message=preferences, signature=signature)
```

#### Constructing the `BeaconBlockBody`

Gọi `head = get_head(store)`. Proposer có thể đặt
`head = get_proposer_head(store, head, slot)` nếu cơ chế proposer re-org được
triển khai và bật. Gọi `head` là node cha mà proposer xây dựng block lên trên, và
`state` được suy ra từ node đó.

##### Signed execution payload bid

Để có `signed_execution_payload_bid`, proposer khi xây dựng block trên một
`state` MUST thực hiện các bước sau để tạo trường `signed_execution_payload_bid`
trong `BeaconBlockBody`:

- Lắng nghe gossip topic toàn cục `execution_payload_bid` và lưu lại một
  `signed_execution_payload_bid` đã được chấp nhận từ một builder. Proposer MAY
  lấy các message đã ký này bằng các phương thức khác nằm ngoài giao thức.
- `signed_execution_payload_bid` MUST thỏa mãn các điều kiện xác minh trong
  `process_execution_payload_bid` với alias
  `bid = signed_execution_payload_bid.message`, cụ thể là:
  - Với builder bên ngoài, signature MUST hợp lệ.
  - Với self-build (proposer tự xây payload), đặt `bid.builder_index` thành
    `BUILDER_INDEX_SELF_BUILD`.
  - Với self-build, signature MUST là `bls.G2_POINT_AT_INFINITY` và `bid.value`
    MUST bằng 0.
  - Balance của builder đủ để chi trả `bid.value`.
  - `bid.slot` là slot của block được propose.
  - `bid.parent_block_hash` bằng
    `state.latest_execution_payload_bid.block_hash` nếu
    `should_build_on_full(store, head, get_current_slot(store))` là true, ngược
    lại bằng `state.latest_execution_payload_bid.parent_block_hash`.
  - `bid.parent_block_root` bằng `parent_root` của block hiện tại.
  - `bid.prev_randao` bằng `get_randao_mix(state, get_current_epoch(state))`.
- Chọn một bid và đặt
  `block.body.signed_execution_payload_bid = signed_execution_payload_bid`.

*Lưu ý*: Địa chỉ execution được mã hóa trong trường `fee_recipient` của
`signed_execution_payload_bid.message` sẽ nhận khoản thanh toán từ builder.

##### Payload attestations

Tối đa `MAX_PAYLOAD_ATTESTATIONS` payload attestation dạng aggregate có thể được
đưa vào block. Proposer MUST thực hiện các bước sau để tạo trường
`payload_attestations` trong `BeaconBlockBody`:

- Lắng nghe gossip topic toàn cục `payload_attestation_message`.
- Các payload attestation được thêm vào MUST thỏa mãn các điều kiện xác minh
  trong gossip validation của payload attestation và trong quá trình xử lý
  payload attestation.
  - `data.beacon_block_root` tương ứng với `block.parent_root`.
  - Slot của block cha đứng ngay trước slot đang propose đúng một slot.
  - Signature của message dữ liệu payload attestation được xác minh đúng.
- Proposer MUST aggregate tất cả payload attestation có cùng data vào một đối
  tượng `PayloadAttestation`. Để làm vậy, proposer cần điền trường
  `aggregation_bits` dựa trên vị trí tương đối của validator index trong PTC thu
  được từ `get_ptc(state, Slot(block_slot - 1))`.

> 💡 Ghi chú: Payload attestation trong block N là các phiếu của PTC slot N-1 về
> payload của block cha, vì vậy PTC được lấy theo `block_slot - 1`.

##### Parent execution requests

Trường `parent_execution_requests` chứa các execution request lấy từ execution
payload của block cha. Proposer tạo trường này như sau:

- Nếu block cha thuộc giai đoạn trước Gloas (đây là block Gloas đầu tiên), đặt
  `parent_execution_requests` thành `ExecutionRequests.empty()`.
- Nếu `should_build_on_full(store, head, get_current_slot(store))` trả về `True`
  (proposer đang xây trên phiên bản "full" của block cha, tức có payload), đặt
  `parent_execution_requests` thành
  `store.payloads[head.root].execution_requests`.
- Ngược lại (proposer đang xây trên phiên bản "empty" của block cha, tức không có
  payload), đặt `parent_execution_requests` thành `ExecutionRequests.empty()`.

##### Execution requests

*Lưu ý*: Hàm `get_execution_requests` được sửa đổi để parse thêm các builder
deposit request và builder exit request.

```python
def get_execution_requests(execution_requests_list: Sequence[bytes]) -> ExecutionRequests:
    deposits = DepositRequests()
    withdrawals = WithdrawalRequests()
    consolidations = ConsolidationRequests()
    # [New in Gloas:EIP8282]
    builder_deposits = BuilderDepositRequests()
    # [New in Gloas:EIP8282]
    builder_exits = BuilderExitRequests()

    request_types = [
        DEPOSIT_REQUEST_TYPE,
        WITHDRAWAL_REQUEST_TYPE,
        CONSOLIDATION_REQUEST_TYPE,
        # [New in Gloas:EIP8282]
        BUILDER_DEPOSIT_REQUEST_TYPE,
        # [New in Gloas:EIP8282]
        BUILDER_EXIT_REQUEST_TYPE,
    ]

    prev_request_type = None
    for request in execution_requests_list:
        request_type, request_data = request[0:1], request[1:]

        # Check that the request type is valid
        assert request_type in request_types
        # Check that the request data is not empty
        assert len(request_data) != 0
        # Check that requests are in strictly ascending order
        # Each successive type must be greater than the last with no duplicates
        assert prev_request_type is None or prev_request_type < request_type
        prev_request_type = request_type

        if request_type == DEPOSIT_REQUEST_TYPE:
            deposits = ssz_deserialize(DepositRequests, request_data)
        elif request_type == WITHDRAWAL_REQUEST_TYPE:
            withdrawals = ssz_deserialize(WithdrawalRequests, request_data)
        elif request_type == CONSOLIDATION_REQUEST_TYPE:
            consolidations = ssz_deserialize(ConsolidationRequests, request_data)
        # [New in Gloas:EIP8282]
        elif request_type == BUILDER_DEPOSIT_REQUEST_TYPE:
            builder_deposits = ssz_deserialize(BuilderDepositRequests, request_data)
        # [New in Gloas:EIP8282]
        elif request_type == BUILDER_EXIT_REQUEST_TYPE:
            builder_exits = ssz_deserialize(BuilderExitRequests, request_data)

    return ExecutionRequests(
        deposits=deposits,
        withdrawals=withdrawals,
        consolidations=consolidations,
        # [New in Gloas:EIP8282]
        builder_deposits=builder_deposits,
        # [New in Gloas:EIP8282]
        builder_exits=builder_exits,
    )
```

##### ExecutionPayload

*Lưu ý*: `prepare_execution_payload` được sửa đổi để xây trên payload "full" của
block cha hoặc phiên bản "empty" của nó, tùy theo quyết định của
`should_build_on_full(store, head, get_current_slot(store))`; lựa chọn này xác
định nguồn withdrawal và execution head cho payload mới. Khi xây trên block cha
"full", `apply_parent_execution_payload` được gọi để withdrawal được tính toán
dựa trên state sau khi đã xử lý payload cha.

```python
def prepare_execution_payload(
    # [New in Gloas:EIP7732]
    store: Store,
    # [New in Gloas:EIP7732]
    head: ForkChoiceNode,
    state: BeaconState,
    safe_block_hash: Hash32,
    finalized_block_hash: Hash32,
    suggested_fee_recipient: ExecutionAddress,
    # [New in Gloas]
    target_gas_limit: Uint64,
    execution_engine: ExecutionEngine,
) -> PayloadId | None:
    # [New in Gloas:EIP7732]
    parent_bid = state.latest_execution_payload_bid
    if should_build_on_full(store, head, get_current_slot(store)):
        envelope = store.payloads[head.root]
        # Make a copy of the state to avoid mutability issues
        state = state.copy()
        # Apply parent payload before computing withdrawals
        apply_parent_execution_payload(state, envelope.execution_requests)
        withdrawals = get_expected_withdrawals(state).withdrawals
        head_block_hash = parent_bid.block_hash
    else:
        withdrawals = state.payload_expected_withdrawals
        head_block_hash = parent_bid.parent_block_hash

    # Set the forkchoice head and initiate the payload build process
    payload_attributes = PayloadAttributes(
        timestamp=compute_time_at_slot(state.genesis_time, state.slot),
        prev_randao=get_randao_mix(state, get_current_epoch(state)),
        suggested_fee_recipient=suggested_fee_recipient,
        # [Modified in Gloas:EIP7732]
        withdrawals=withdrawals,
        parent_beacon_block_root=hash_tree_root(state.latest_block_header),
        # [New in Gloas:EIP7843]
        slot_number=state.slot,
        # [New in Gloas]
        target_gas_limit=target_gas_limit,
    )
    return execution_engine.notify_forkchoice_updated(
        # [Modified in Gloas:EIP7732]
        head_block_hash=head_block_hash,
        safe_block_hash=safe_block_hash,
        finalized_block_hash=finalized_block_hash,
        payload_attributes=payload_attributes,
        # [New in Gloas:EIP8070]
        custody_columns=None,
    )
```

##### Voluntary exits

*Lưu ý*: Vì việc xử lý execution request bị trì hoãn (được xử lý trong block con
thông qua `parent_execution_requests`), một request trong
`parent_execution_requests` có thể làm một voluntary exit trong cùng block trở nên
không hợp lệ. Ví dụ, một withdrawal request cho một validator sẽ khiến voluntary
exit của chính validator đó thất bại, làm toàn bộ block không hợp lệ. Khi chọn
các voluntary exit để đưa vào block, proposer phải lưu ý tương tác này.

### Payload timeliness attestation

Một số validator được chọn để gửi payload timeliness attestation. Validator nên
gọi `get_ptc_assignment` vào đầu một epoch để chuẩn bị gửi PTC attestation của
mình trong epoch kế tiếp.

Validator nên tạo và broadcast `payload_attestation_message` ngay khi đã thấy
execution payload envelope và dữ liệu blob của block, và không muộn hơn
`get_payload_attestation_due_ms()` mili giây tính từ đầu slot.

#### Constructing the `PayloadAttestationMessage`

Nếu validator nằm trong payload attestation committee của slot hiện tại (theo kết
quả từ `get_ptc_assignment` ở trên) thì validator nên chuẩn bị một
`PayloadAttestationMessage` cho slot hiện tại và broadcast nó lên pubsub topic
toàn cục `payload_attestation_message`.

Validator tạo `payload_attestation_message` như sau:

- Nếu validator chưa thấy bất kỳ beacon block nào cho slot được phân công, không
  gửi payload attestation; dù sao nó cũng sẽ bị bỏ qua.
- Đặt `data.beacon_block_root` là hash tree root của beacon block đã thấy cho
  slot được phân công.
- Đặt `data.slot` là slot được phân công.
- Nếu một `SignedExecutionPayloadEnvelope` đã thấy trước đó tham chiếu tới block
  có root `data.beacon_block_root`, và nó được thấy trước mốc
  `get_payload_due_ms()` mili giây tính từ đầu slot, đặt `data.payload_present`
  thành `True`; ngược lại, đặt `data.payload_present` thành `False`.
- Đặt `data.blob_data_available` thành `is_data_available(data.beacon_block_root)`.
  Chỉ đặt nó thành `False` khi đã qua `get_payload_attestation_due_ms()` mili
  giây, vì dữ liệu blob vẫn có thể đến trước thời điểm đó.
- Đặt `payload_attestation_message.validator_index = validator_index`, trong đó
  `validator_index` là validator được chọn để gửi. Private key tương ứng với
  `state.validators[validator_index].pubkey` được dùng để ký payload timeliness
  attestation.
- Ký `payload_attestation_message.data` bằng hàm hỗ trợ
  `get_payload_attestation_message_signature`.

Lưu ý rằng attester chỉ ký `PayloadAttestationData` chứ không ký trường
`validator_index` trong message. Proposer cần aggregate các attestation này như
đã mô tả ở trên.

```python
def get_payload_attestation_message_signature(
    state: BeaconState, attestation: PayloadAttestationMessage, privkey: int
) -> BLSSignature:
    domain = get_domain(state, DOMAIN_PTC_ATTESTER, compute_epoch_at_slot(attestation.data.slot))
    signing_root = compute_signing_root(attestation.data, domain)
    return bls.Sign(privkey, signing_root)
```

*Lưu ý*: Validator không cần kiểm tra đầy đủ tính hợp lệ của `ExecutionPayload`
nằm trong envelope, nhưng các bước kiểm tra trong đặc tả
[Networking](./p2p-interface.md) phải được thỏa mãn đối với
`SignedExecutionPayloadEnvelope`.

## Modified functions

### Modified `get_data_column_sidecars_from_column_sidecar`

```python
def get_data_column_sidecars_from_column_sidecar(
    sidecar: DataColumnSidecar,
    cells_and_kzg_proofs: Sequence[tuple[Cells, Proofs]],
) -> Sequence[DataColumnSidecar]:
    """
    Given a data column sidecar and the cells/proofs associated with each blob
    in the corresponding payload, assemble the sidecars which can be
    distributed to peers.
    """
    # [Modified in Gloas:EIP7732]
    return get_data_column_sidecars(
        sidecar.beacon_block_root,
        sidecar.slot,
        cells_and_kzg_proofs,
    )
```
