# Heze -- Honest Validator

*Lưu ý*: Tài liệu này vẫn đang trong quá trình soạn thảo, dành cho các nhà
nghiên cứu và đội ngũ phát triển client.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Configs](#configs)
- [Helpers](#helpers)
  - [New `GetInclusionListResponse`](#new-getinclusionlistresponse)
- [Protocols](#protocols)
  - [`ExecutionEngine`](#executionengine)
    - [New `get_inclusion_list`](#new-get_inclusion_list)
- [Validator assignments](#validator-assignments)
  - [Inclusion list committee](#inclusion-list-committee)
  - [Lookahead](#lookahead)
- [Beacon chain responsibilities](#beacon-chain-responsibilities)
  - [Block and sidecar proposal](#block-and-sidecar-proposal)
    - [Constructing the `BeaconBlockBody`](#constructing-the-beaconblockbody)
      - [Eth1 data](#eth1-data)
      - [Deposits](#deposits)
      - [Signed execution payload bid](#signed-execution-payload-bid)
      - [ExecutionPayload](#executionpayload)
  - [Inclusion list proposal](#inclusion-list-proposal)
    - [Constructing the `SignedInclusionList`](#constructing-the-signedinclusionlist)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả những thay đổi cần thực hiện trong code của một "honest
validator" (validator trung thực, tuân thủ đúng giao thức) để triển khai Heze.

> 💡 Ghi chú: Thay đổi chính ở phía validator trong Heze là nhiệm vụ mới: tham
> gia inclusion list committee (EIP-7805) — tạo, ký và phát tán inclusion list
> (danh sách giao dịch mà block kế tiếp phải tôn trọng). Ngoài ra, proposer phải
> chọn bid và xây execution payload tôn trọng các inclusion list mình đã quan
> sát, và các trường `eth1_data`/`deposits` bị loại khỏi block (EIP-8015).

## Configs

## Helpers

### New `GetInclusionListResponse`

```python
@dataclass
class GetInclusionListResponse:
    inclusion_list_transactions: Sequence[Transaction]
```

## Protocols

### `ExecutionEngine`

*Lưu ý*: Hàm `get_inclusion_list` được thêm vào protocol `ExecutionEngine` để
validator sử dụng khi là thành viên của inclusion list committee.

Phần thân của hàm này phụ thuộc vào cách triển khai. Có thể dùng Engine API để
hiện thực hàm này với một execution engine bên ngoài.

#### New `get_inclusion_list`

*Lưu ý*: `get_inclusion_list` trả về `GetInclusionListResponse` chứa các giao
dịch inclusion list mới nhất, được xây dựng dựa trên góc nhìn mới nhất của
execution engine về mempool công khai.

```python
def get_inclusion_list(self: ExecutionEngine) -> GetInclusionListResponse:
    """
    Return inclusion list transactions (as Sequence[Transaction]) object.
    """
```

## Validator assignments

### Inclusion list committee

Một validator có thể là thành viên của inclusion list committee mới tại một slot
nhất định. Để kiểm tra phân công vào inclusion list committee, dùng
`get_inclusion_list_committee_assignment(state, epoch, validator_index)` với
`epoch <= next_epoch`, vì việc chọn thành viên inclusion list committee chỉ ổn
định (không thay đổi) trong phạm vi epoch hiện tại và epoch kế tiếp.

```python
def get_inclusion_list_committee_assignment(
    state: BeaconState, epoch: Epoch, validator_index: ValidatorIndex
) -> Slot | None:
    """
    Returns the slot during the requested epoch in which the validator with
    index ``validator_index`` is a member of the inclusion list committee.
    Returns None if no assignment is found.
    """
    next_epoch = get_current_epoch(state) + 1
    assert epoch <= next_epoch

    start_slot = compute_start_slot_at_epoch(epoch)
    for slot in range(start_slot, start_slot + SLOTS_PER_EPOCH):
        if validator_index in get_inclusion_list_committee(state, Slot(slot)):
            return Slot(slot)
    return None
```

### Lookahead

`get_inclusion_list_committee_assignment` nên được gọi vào đầu mỗi epoch để lấy
phân công cho epoch kế tiếp (`current_epoch + 1`). Validator nên lên kế hoạch
cho các phân công sắp tới bằng cách ghi nhận slot mà mình được phân công vào
inclusion list committee.

## Beacon chain responsibilities

Mọi trách nhiệm của validator vẫn giữ nguyên, ngoại trừ những điểm được nêu dưới
đây.

### Block and sidecar proposal

#### Constructing the `BeaconBlockBody`

##### Eth1 data

*[Modified in Heze:EIP8015]*

*Lưu ý*: Trường `eth1_data` bị loại bỏ khỏi `BeaconBlockBody`.

##### Deposits

*[Modified in Heze:EIP8015]*

*Lưu ý*: Trường `deposits` bị loại bỏ khỏi `BeaconBlockBody`.

##### Signed execution payload bid

*Lưu ý*: Thay đổi duy nhất đối với `signed_execution_payload_bid` là yêu cầu
`bid.inclusion_list_bits` phải thỏa mãn `is_inclusion_list_bits_inclusive()`
xét theo góc nhìn inclusion list của proposer — tức là tập tất cả các inclusion
list hợp lệ và không equivocate (không bị ký hai phiên bản mâu thuẫn) mà
proposer đã quan sát được.

- `bid.inclusion_list_bits` phải thỏa mãn
  `is_inclusion_list_bits_inclusive(get_inclusion_list_store(), inclusion_list_committee, slot, dependent_root, bid.inclusion_list_bits, only_timely=False)`,
  trong đó `inclusion_list_committee` là
  `get_inclusion_list_committee(state, slot)`, `slot` là `bid.slot - 1`,
  `dependent_root` là
  `get_shuffling_dependent_root(store, bid.parent_block_root, compute_epoch_at_slot(slot))`,
  và `store` là fork choice store.

> 💡 Ghi chú: Nói cách khác, proposer chỉ nên chọn bid đã đánh dấu (cam kết tôn
> trọng) mọi inclusion list mà proposer biết cho slot ngay trước đó. Khác với
> quy tắc gossip (`only_timely=True`), ở đây dùng `only_timely=False`, nghĩa là
> xét cả các inclusion list đến muộn mà proposer đã nhận được.

##### ExecutionPayload

`prepare_execution_payload` được cập nhật so với đặc tả Gloas để cung cấp thêm
các giao dịch của inclusion list.

*Lưu ý*: Trong phần này, `state` là state tại slot đề xuất block, _chưa_ áp dụng
block đó. Tức là `state` là `previous_state` đã được xử lý qua các slot trống cho
tới slot được phân công bằng `process_slots(previous_state, slot)`.

*Lưu ý*: Proposer nên tạo một execution payload thỏa mãn các ràng buộc inclusion
list theo góc nhìn inclusion list của mình tại thời điểm xây payload — gồm tất
cả các inclusion list hợp lệ và không equivocate mà proposer đã quan sát được.

```python
def prepare_execution_payload(
    store: Store,
    head: ForkChoiceNode,
    state: BeaconState,
    safe_block_hash: Hash32,
    finalized_block_hash: Hash32,
    suggested_fee_recipient: ExecutionAddress,
    target_gas_limit: Uint64,
    execution_engine: ExecutionEngine,
) -> PayloadId | None:
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
        withdrawals=withdrawals,
        parent_beacon_block_root=hash_tree_root(state.latest_block_header),
        slot_number=state.slot,
        target_gas_limit=target_gas_limit,
        # [New in Heze:EIP7805]
        inclusion_list_transactions=get_inclusion_list_transactions(
            get_inclusion_list_store(),
            state.slot - 1,
            get_shuffling_dependent_root(store, head.root, compute_epoch_at_slot(state.slot - 1)),
            only_timely=False,
        ),
    )
    return execution_engine.notify_forkchoice_updated(
        head_block_hash=head_block_hash,
        safe_block_hash=safe_block_hash,
        finalized_block_hash=finalized_block_hash,
        payload_attributes=payload_attributes,
        custody_columns=None,
    )
```

### Inclusion list proposal

Một validator được kỳ vọng sẽ đề xuất một
[`SignedInclusionList`](./beacon-chain.md#signedinclusionlist) vào đầu mỗi
`slot` mà `get_inclusion_list_committee_assignment(state, epoch, validator_index)`
trả về.

Nếu validator thuộc inclusion list committee hiện tại, validator nên tạo và phát
tán `signed_inclusion_list` lên subnet toàn cục `inclusion_list` trước thời điểm
`get_inclusion_list_due_ms()` mili-giây tính từ đầu slot. Inclusion list được
xây dựa trên block của slot hiện tại nếu block đó đã được xử lý và xác nhận là
head; ngược lại thì dựa trên head cục bộ do `get_head()` trả về.

#### Constructing the `SignedInclusionList`

Validator tạo `signed_inclusion_list` bằng `get_signed_inclusion_list` cho
`slot` được phân công mà `get_inclusion_list_committee_assignment` trả về. Gọi
`head_root` là root của head hiện tại của validator và
`inclusion_list_transactions` là các giao dịch inclusion list lấy từ
`ExecutionEngine` thông qua `get_inclusion_list`.

```python
def get_inclusion_list_signature(
    state: BeaconState, inclusion_list: InclusionList, privkey: int
) -> BLSSignature:
    domain = compute_domain(
        DOMAIN_INCLUSION_LIST_COMMITTEE,
        compute_fork_version(compute_epoch_at_slot(inclusion_list.slot)),
        state.genesis_validators_root,
    )
    signing_root = compute_signing_root(inclusion_list, domain)
    return bls.Sign(privkey, signing_root)
```

```python
def get_signed_inclusion_list(
    store: Store,
    state: BeaconState,
    head_root: Root,
    slot: Slot,
    validator_index: ValidatorIndex,
    inclusion_list_transactions: Sequence[Transaction],
    privkey: int,
) -> SignedInclusionList:
    inclusion_list = InclusionList(
        slot=slot,
        validator_index=validator_index,
        dependent_root=get_shuffling_dependent_root(store, head_root, compute_epoch_at_slot(slot)),
        transactions=Transactions(data=inclusion_list_transactions),
    )
    signature = get_inclusion_list_signature(state, inclusion_list, privkey)
    return SignedInclusionList(message=inclusion_list, signature=signature)
```
