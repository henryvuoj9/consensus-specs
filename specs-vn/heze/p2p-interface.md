# Heze -- Networking

*Lưu ý*: Tài liệu này vẫn đang trong quá trình soạn thảo, dành cho các nhà
nghiên cứu và đội ngũ phát triển client.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Presets](#presets)
  - [Type-specific SSZ bounds](#type-specific-ssz-bounds)
- [Configs](#configs)
- [Types](#types)
  - [New `SignedInclusionLists`](#new-signedinclusionlists)
- [Helpers](#helpers)
  - [Modified `Seen`](#modified-seen)
  - [Modified `compute_fork_version`](#modified-compute_fork_version)
  - [Modified `verify_block_body_operation_limits`](#modified-verify_block_body_operation_limits)
- [The gossip domain: gossipsub](#the-gossip-domain-gossipsub)
  - [Topics and messages](#topics-and-messages)
    - [Global topics](#global-topics)
      - [Modified `execution_payload_bid`](#modified-execution_payload_bid)
      - [New `inclusion_list`](#new-inclusion_list)
- [The Req/Resp domain](#the-reqresp-domain)
  - [Messages](#messages)
    - [BeaconBlocksByRange v2](#beaconblocksbyrange-v2)
    - [BeaconBlocksByRoot v2](#beaconblocksbyroot-v2)
    - [InclusionListsByIndices v1](#inclusionlistsbyindices-v1)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả đặc tả networking (mạng ngang hàng) của tầng đồng thuận
(consensus layer) cho bản nâng cấp Heze.

Đặc tả các thay đổi ở đây tiếp nối theo cùng định dạng với đặc tả networking của
các bản nâng cấp trước, và coi chúng là điều kiện tiên quyết. Nói cách khác, mọi
quy tắc của các fork trước vẫn giữ nguyên trừ khi được nêu rõ là thay đổi ở đây.

> 💡 Ghi chú: Heze bổ sung cơ chế inclusion list (EIP-7805, FOCIL — danh sách
> giao dịch mà một committee yêu cầu phải được đưa vào block) và loại bỏ cơ chế
> deposit/eth1 data cũ trong block (EIP-8015). Về mặt networking, điều này dẫn
> tới: một gossip topic mới `inclusion_list`, một giao thức req/resp mới
> `InclusionListsByIndices`, và quy tắc kiểm tra bổ sung cho
> `execution_payload_bid`.

## Presets

### Type-specific SSZ bounds

*(Giới hạn kích thước SSZ cho từng kiểu dữ liệu)*

| Name                                         | Value                         |
| -------------------------------------------- | ----------------------------- |
| `MAX_SIGNED_EXECUTION_PAYLOAD_BID_SIZE_HEZE` | `Uint64(196934)` (= ~192 KiB) |
| `MAX_SIGNED_INCLUSION_LIST_SIZE`             | `Uint64(41112)` (= ~40 KiB)   |

## Configs

| Name                                        | Value                     | Description                                                                 |
| ------------------------------------------- | ------------------------- | --------------------------------------------------------------------------- |
| `MAX_REQUEST_INCLUSION_LIST`                | `Uint64(2**4)` (= 16)     | Số lượng inclusion list tối đa trong một request                            |
| `MIN_SLOTS_FOR_INCLUSION_LISTS_REQUESTS`    | `Slot(1)`                 | Khoảng slot tối thiểu mà một node phải phục vụ được inclusion list          |
| `MAX_TRANSACTIONS_BYTES_PER_INCLUSION_LIST` | `Uint64(2**13)` (= 8,192) | Kích thước tối đa (tính bằng byte) của các giao dịch trong một inclusion list |

## Types

### New `SignedInclusionLists`

```python
class SignedInclusionLists(List[SignedInclusionList]):
    """
    Signed inclusion lists returned in an ``InclusionListsByIndices``
    response.
    """

    LIMIT = MAX_REQUEST_INCLUSION_LIST
```

## Helpers

### Modified `Seen`

*(Cấu trúc `Seen` lưu lại những gì node đã thấy qua gossip, dùng để loại bỏ
message trùng lặp. Heze bổ sung trường `inclusion_list_counts` để đếm số
inclusion list hợp lệ đã nhận từ mỗi validator cho mỗi cặp slot và
`dependent_root`.)*

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
    # [New in Heze:EIP7805]
    inclusion_list_counts: Counter[tuple[Slot, Root, ValidatorIndex]]
```

### Modified `compute_fork_version`

```python
def compute_fork_version(epoch: Epoch) -> Version:
    """
    Return the fork version at the given ``epoch``.
    """
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

### Modified `verify_block_body_operation_limits`

*Lưu ý*: `verify_block_body_operation_limits` bỏ đi bước kiểm tra rằng
`body.deposits` phải rỗng (vì từ Heze, trường `deposits` đã bị loại khỏi
`BeaconBlockBody`).

```python
def verify_block_body_operation_limits(body: BeaconBlockBody) -> None:
    """
    Verify that each block body operation count is within its limit.
    Raises GossipReject on validation failure.
    """
    # [REJECT] Số lượng proposer slashing nằm trong giới hạn
    if len(body.proposer_slashings) > MAX_PROPOSER_SLASHINGS:
        raise GossipReject("too many proposer slashings")

    # [REJECT] Số lượng attester slashing nằm trong giới hạn
    if len(body.attester_slashings) > MAX_ATTESTER_SLASHINGS_ELECTRA:
        raise GossipReject("too many attester slashings")

    # [REJECT] Số lượng attestation nằm trong giới hạn
    if len(body.attestations) > MAX_ATTESTATIONS_ELECTRA:
        raise GossipReject("too many attestations")

    # [REJECT] Số lượng voluntary exit nằm trong giới hạn
    if len(body.voluntary_exits) > MAX_VOLUNTARY_EXITS:
        raise GossipReject("too many voluntary exits")

    # [REJECT] Số lượng BLS to execution change nằm trong giới hạn
    if len(body.bls_to_execution_changes) > MAX_BLS_TO_EXECUTION_CHANGES:
        raise GossipReject("too many bls to execution changes")

    # [REJECT] Số lượng payload attestation nằm trong giới hạn
    if len(body.payload_attestations) > MAX_PAYLOAD_ATTESTATIONS:
        raise GossipReject("too many payload attestations")
```

## The gossip domain: gossipsub

### Topics and messages

Topic `execution_payload_bid` được sửa đổi để hỗ trợ các bid theo định dạng của
Heze.

Các topic mới cùng kiểu dữ liệu của trường `data` trong gossipsub message được
liệt kê trong bảng sau:

| Name             | Message Type          |
| ---------------- | --------------------- |
| `inclusion_list` | `SignedInclusionList` |

#### Global topics

##### Modified `execution_payload_bid`

```python
def validate_execution_payload_bid_gossip(
    seen: Seen,
    store: Store,
    signed_execution_payload_bid: SignedExecutionPayloadBid,
    current_time_ms: Uint64,
) -> None:
    """
    Validate a SignedExecutionPayloadBid for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    bid = signed_execution_payload_bid.message

    # [IGNORE] Đây là bid đầu tiên cho slot, parent và builder này
    bid_key = (bid.slot, bid.parent_block_hash, bid.parent_block_root, bid.builder_index)
    if bid_key in seen.execution_payload_bids:
        raise GossipIgnore("already seen valid bid for this slot, parent, and builder")

    # [IGNORE] Đây là bid có giá trị cao nhất được thấy cho slot và parent này
    best_bid_key = (bid.slot, bid.parent_block_hash, bid.parent_block_root)
    if best_bid_key in seen.best_execution_payload_bid:
        if bid.value <= seen.best_execution_payload_bid[best_bid_key]:
            raise GossipIgnore("bid is not the highest value bid seen for this slot and parent")

    # [IGNORE] Slot của bid là slot hiện tại hoặc slot kế tiếp
    if not is_current_or_next_slot(store, bid.slot, current_time_ms):
        raise GossipIgnore("bid's slot is not the current or next slot")

    # [REJECT] Execution payment của bid bằng 0
    if bid.execution_payment != 0:
        raise GossipReject("bid's execution payment must be zero")

    # [REJECT] Block hash của bid không bằng parent block hash của nó
    if bid.block_hash == bid.parent_block_hash:
        raise GossipReject("bid's block hash equals its parent block hash")

    # [REJECT] Số lượng blob KZG commitment của bid nằm trong giới hạn theo epoch
    proposal_epoch = compute_epoch_at_slot(bid.slot)
    max_blobs = get_blob_parameters(proposal_epoch).max_blobs_per_block
    if len(bid.blob_kzg_commitments) > max_blobs:
        raise GossipReject("too many blob kzg commitments")

    # [IGNORE] Parent block root của bid là một beacon block đã biết
    # (MAY đưa vào hàng đợi cho đến khi parent được truy xuất)
    if bid.parent_block_root not in store.blocks:
        raise GossipIgnore("bid's parent block root is not a known beacon block")

    # [REJECT] Bid thuộc slot cao hơn parent block của nó
    if bid.slot <= store.blocks[bid.parent_block_root].slot:
        raise GossipReject("bid's slot is not higher than its parent's slot")

    # [IGNORE] Parent block của bid đã được import
    # (MAY đưa vào hàng đợi cho đến khi parent được import)
    if bid.parent_block_root not in store.block_states:
        raise GossipIgnore("bid's parent block post-state is unavailable")

    state = store.block_states[bid.parent_block_root]

    # [IGNORE] Slot của bid nằm trong proposer lookahead của parent
    if proposal_epoch > get_current_epoch(state) + MIN_SEED_LOOKAHEAD:
        raise GossipIgnore("bid's slot is past the parent's proposer lookahead")

    # [IGNORE] Proposer preferences tương ứng đã được thấy
    dependent_root = get_shuffling_dependent_root(store, bid.parent_block_root, proposal_epoch)
    prefs_key = (bid.slot, dependent_root)
    if prefs_key not in seen.proposer_preferences:
        raise GossipIgnore("matching proposer preferences have not been seen")

    proposer_preferences = seen.proposer_preferences[prefs_key]

    # [IGNORE] Fee recipient của bid khớp với preference của proposer
    if bid.fee_recipient != proposer_preferences.fee_recipient:
        raise GossipIgnore("bid's fee recipient does not match the proposer's preference")

    # [IGNORE] Parent block hash của bid là hash của một execution payload đã biết
    if bid.parent_block_hash not in seen.execution_payloads:
        raise GossipIgnore("bid's parent block hash is not a known execution payload")

    # [IGNORE] Gas limit của bid tương thích với target gas limit của proposer
    parent_gas_limit = seen.execution_payloads[bid.parent_block_hash].gas_limit
    if not is_gas_limit_target_compatible(
        parent_gas_limit, bid.gas_limit, proposer_preferences.target_gas_limit
    ):
        raise GossipIgnore("bid's gas limit is not compatible with the proposer's target")

    # [IGNORE] Bid tương thích với nhánh head hiện tại
    if not is_bid_compatible_with_head(store, bid):
        raise GossipIgnore("bid is not compatible with the current head branch")

    # [REJECT] Previous randao của bid là đúng
    if bid.prev_randao != get_randao_mix(state, get_current_epoch(state)):
        raise GossipReject("bid's previous randao is incorrect")

    state = state.copy()
    process_slots(state, bid.slot)

    # [REJECT] Builder index hợp lệ
    if bid.builder_index >= len(state.builders):
        raise GossipReject("builder index out of range")

    builder = state.builders[bid.builder_index]

    # [REJECT] Builder là một payload builder
    if builder.version != PAYLOAD_BUILDER_VERSION:
        raise GossipReject("builder is not a payload builder")

    # [REJECT] Builder đang active
    if not is_active_builder(state, bid.builder_index):
        raise GossipReject("builder is not active")

    # [IGNORE] Builder đủ khả năng chi trả bid
    if not can_builder_cover_bid(state, bid.builder_index, bid.value):
        raise GossipIgnore("builder cannot cover bid value")

    # [IGNORE] Payload của parent không cố gắng exit builder này
    if bid.parent_block_hash == state.latest_execution_payload_bid.block_hash:
        envelope = store.payloads[bid.parent_block_root]
        for request in envelope.execution_requests.builder_exits:
            if request.pubkey == builder.pubkey:
                if request.source_address == builder.execution_address:
                    raise GossipIgnore("builder may exit")

    # [New in Heze:EIP7805]
    # [IGNORE] Inclusion list bits của bid có tính bao hàm (inclusive)
    inclusion_list_slot = bid.slot - 1
    inclusion_list_epoch = compute_epoch_at_slot(inclusion_list_slot)
    if not is_inclusion_list_bits_inclusive(
        get_inclusion_list_store(),
        get_inclusion_list_committee(state, inclusion_list_slot),
        inclusion_list_slot,
        get_shuffling_dependent_root(store, bid.parent_block_root, inclusion_list_epoch),
        bid.inclusion_list_bits,
        only_timely=True,
    ):
        raise GossipIgnore("bid's inclusion list bits is not inclusive")

    # [REJECT] Signature của bid hợp lệ
    if not verify_execution_payload_bid_signature(state, signed_execution_payload_bid):
        raise GossipReject("invalid bid signature")

    # Đánh dấu bid này là đã thấy và cập nhật bid có giá trị cao nhất cho slot/parent này
    seen.execution_payload_bids.add(bid_key)
    seen.best_execution_payload_bid[best_bid_key] = bid.value
```

> 💡 Ghi chú: Tóm tắt các điều kiện kiểm tra ở trên (theo đúng thứ tự trong
> code). `[IGNORE]` nghĩa là bỏ qua message, không lan truyền tiếp nhưng không
> phạt peer; `[REJECT]` nghĩa là message không hợp lệ, từ chối và có thể hạ điểm
> peer đã gửi.
>
> - [IGNORE] Đây là bid đầu tiên cho bộ (slot, parent, builder) này.
> - [IGNORE] Đây là bid có giá trị cao nhất đã thấy cho slot và parent này.
> - [IGNORE] Slot của bid là slot hiện tại hoặc slot kế tiếp.
> - [REJECT] `execution_payment` của bid phải bằng 0.
> - [REJECT] `block_hash` của bid không được trùng với `parent_block_hash`.
> - [REJECT] Số lượng blob KZG commitment của bid không vượt quá giới hạn của
>   epoch tương ứng.
> - [IGNORE] `parent_block_root` của bid là một beacon block đã biết (MAY xếp
>   hàng chờ cho tới khi lấy được parent).
> - [REJECT] Slot của bid phải lớn hơn slot của parent block.
> - [IGNORE] Parent block của bid đã được import (MAY xếp hàng chờ cho tới khi
>   parent được import).
> - [IGNORE] Slot của bid nằm trong phạm vi proposer lookahead của parent.
> - [IGNORE] Đã thấy proposer preferences tương ứng.
> - [IGNORE] Fee recipient của bid khớp với preference của proposer.
> - [IGNORE] `parent_block_hash` của bid là hash của một execution payload đã
>   biết.
> - [IGNORE] Gas limit của bid tương thích với target gas limit của proposer.
> - [IGNORE] Bid tương thích với nhánh head hiện tại.
> - [REJECT] `prev_randao` của bid đúng.
> - [REJECT] Builder index hợp lệ; builder là payload builder; builder đang
>   active.
> - [IGNORE] Builder đủ khả năng chi trả giá trị bid.
> - [IGNORE] Payload của parent không chứa yêu cầu exit chính builder này.
> - **[Mới trong Heze:EIP7805]** [IGNORE] `inclusion_list_bits` của bid phải
>   "inclusive" — tức là bid phải bao phủ (đánh dấu) tất cả các inclusion list
>   đến đúng hạn (timely) mà node này đã quan sát được cho slot trước đó
>   (`bid.slot - 1`). Nếu bid bỏ sót một inclusion list mà node đã thấy, bid bị
>   bỏ qua.
> - [REJECT] Chữ ký của bid hợp lệ.
>
> Cuối cùng, bid được đánh dấu là đã thấy và giá trị bid cao nhất cho
> slot/parent được cập nhật.

##### New `inclusion_list`

Topic này dùng để lan truyền các inclusion list đã được ký (`SignedInclusionList`).

```python
def validate_inclusion_list_gossip(
    seen: Seen,
    store: Store,
    signed_inclusion_list: SignedInclusionList,
    current_time_ms: Uint64,
) -> None:
    """
    Validate a SignedInclusionList for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    inclusion_list = signed_inclusion_list.message

    # [IGNORE] Đây là message hợp lệ thứ nhất hoặc thứ hai từ validator này
    includer_index = inclusion_list.validator_index
    inclusion_list_key = (inclusion_list.slot, inclusion_list.dependent_root, includer_index)
    if seen.inclusion_list_counts[inclusion_list_key] >= 2:
        raise GossipIgnore("already seen two valid inclusion lists from this validator")

    # [IGNORE] Slot của inclusion list là slot hiện tại
    if not is_current_slot(store, inclusion_list.slot, current_time_ms):
        raise GossipIgnore("inclusion list is not for the current slot")

    transactions_size = sum(len(transaction) for transaction in inclusion_list.transactions)

    # [IGNORE] Kích thước các transaction của inclusion list phải khác rỗng
    if transactions_size == 0:
        raise GossipIgnore("inclusion list contains no transactions")

    # [REJECT] Kích thước các transaction của inclusion list không được vượt quá kích thước tối đa
    if transactions_size > MAX_TRANSACTIONS_BYTES_PER_INCLUSION_LIST:
        raise GossipReject("inclusion list transactions exceed the maximum size")

    # [REJECT] Mọi transaction đều phải khác rỗng
    if any(len(transaction) == 0 for transaction in inclusion_list.transactions):
        raise GossipReject("inclusion list contains an empty transaction")

    # [IGNORE] Dependent block đã được thấy (qua gossip hoặc nguồn không phải gossip)
    # (MAY đưa vào hàng đợi cho đến khi block được truy xuất)
    if inclusion_list.dependent_root not in store.blocks:
        raise GossipIgnore("dependent block has not been seen")

    # [IGNORE] Dependent block qua được validation
    if inclusion_list.dependent_root not in store.block_states:
        raise GossipIgnore("dependent block failed validation")

    # [REJECT] Slot của dependent block không nằm sau shuffling dependent slot
    epoch = compute_epoch_at_slot(inclusion_list.slot)
    dependent_slot = compute_shuffling_dependent_slot(epoch)
    if store.blocks[inclusion_list.dependent_root].slot > dependent_slot:
        raise GossipReject("dependent block is after the shuffling dependent slot")

    # [IGNORE] Dependent block là một dependent block khả dĩ cho committee lookahead
    if not is_valid_dependent_root(store, inclusion_list.dependent_root, dependent_slot):
        raise GossipIgnore("dependent block is not a possible dependent block")

    state = store.block_states[inclusion_list.dependent_root].copy()
    lookahead_start_slot = compute_shuffling_lookahead_start_slot(epoch)
    if state.slot < lookahead_start_slot:
        process_slots(state, lookahead_start_slot)

    # [REJECT] Includer là thành viên của committee
    if includer_index not in get_inclusion_list_committee(state, inclusion_list.slot):
        raise GossipReject("includer is not a member of the committee")

    # [REJECT] Signature hợp lệ
    if not is_valid_inclusion_list_signature(state, signed_inclusion_list):
        raise GossipReject("invalid inclusion list signature")

    # Đánh dấu inclusion list này là đã thấy
    seen.inclusion_list_counts[inclusion_list_key] += 1
```

> 💡 Ghi chú: Tóm tắt các điều kiện kiểm tra ở trên:
>
> - [IGNORE] Đây là message hợp lệ thứ nhất hoặc thứ hai từ validator này (cho
>   cùng `slot` và `dependent_root`). Việc chấp nhận tối đa hai message cho phép
>   lan truyền bằng chứng equivocation (validator ký hai inclusion list khác
>   nhau), nhưng chặn spam từ message thứ ba trở đi.
> - [IGNORE] Slot của inclusion list là slot hiện tại.
> - [IGNORE] Tổng kích thước các giao dịch phải khác 0 (inclusion list không
>   rỗng).
> - [REJECT] Tổng kích thước các giao dịch không vượt quá
>   `MAX_TRANSACTIONS_BYTES_PER_INCLUSION_LIST`.
> - [REJECT] Không có giao dịch nào rỗng.
> - [IGNORE] Block ứng với `dependent_root` đã được thấy (qua gossip hoặc nguồn
>   khác; MAY xếp hàng chờ cho tới khi lấy được block).
> - [IGNORE] Block ứng với `dependent_root` đã vượt qua validation.
> - [REJECT] Slot của dependent block không được sau shuffling dependent slot.
> - [IGNORE] Dependent block là một dependent block khả dĩ cho committee
>   lookahead.
> - [REJECT] Validator gửi (includer) là thành viên của inclusion list
>   committee.
> - [REJECT] Chữ ký hợp lệ.
>
> Cuối cùng, bộ đếm `inclusion_list_counts` cho khóa tương ứng được tăng thêm 1.

## The Req/Resp domain

### Messages

#### BeaconBlocksByRange v2

**Protocol ID:** `/eth2/beacon_chain/req/beacon_blocks_by_range/2/`

Fork digest của Heze được bổ sung vào enum `context` để chỉ định kiểu beacon
block của Heze.

<!-- eth_consensus_specs: skip -->

| `fork_version`           | Chunk SSZ type                |
| ------------------------ | ----------------------------- |
| `GENESIS_FORK_VERSION`   | `phase0.SignedBeaconBlock`    |
| `ALTAIR_FORK_VERSION`    | `altair.SignedBeaconBlock`    |
| `BELLATRIX_FORK_VERSION` | `bellatrix.SignedBeaconBlock` |
| `CAPELLA_FORK_VERSION`   | `capella.SignedBeaconBlock`   |
| `DENEB_FORK_VERSION`     | `deneb.SignedBeaconBlock`     |
| `ELECTRA_FORK_VERSION`   | `electra.SignedBeaconBlock`   |
| `FULU_FORK_VERSION`      | `fulu.SignedBeaconBlock`      |
| `GLOAS_FORK_VERSION`     | `gloas.SignedBeaconBlock`     |
| `HEZE_FORK_VERSION`      | `heze.SignedBeaconBlock`      |

#### BeaconBlocksByRoot v2

**Protocol ID:** `/eth2/beacon_chain/req/beacon_blocks_by_root/2/`

Fork digest của Heze được bổ sung vào enum `context` để chỉ định kiểu beacon
block của Heze.

<!-- eth_consensus_specs: skip -->

| `fork_version`           | Chunk SSZ type                |
| ------------------------ | ----------------------------- |
| `GENESIS_FORK_VERSION`   | `phase0.SignedBeaconBlock`    |
| `ALTAIR_FORK_VERSION`    | `altair.SignedBeaconBlock`    |
| `BELLATRIX_FORK_VERSION` | `bellatrix.SignedBeaconBlock` |
| `CAPELLA_FORK_VERSION`   | `capella.SignedBeaconBlock`   |
| `DENEB_FORK_VERSION`     | `deneb.SignedBeaconBlock`     |
| `ELECTRA_FORK_VERSION`   | `electra.SignedBeaconBlock`   |
| `FULU_FORK_VERSION`      | `fulu.SignedBeaconBlock`      |
| `GLOAS_FORK_VERSION`     | `gloas.SignedBeaconBlock`     |
| `HEZE_FORK_VERSION`      | `heze.SignedBeaconBlock`      |

#### InclusionListsByIndices v1

**Protocol ID:** `/eth2/beacon_chain/req/inclusion_lists_by_indices/1/`

*[New in Heze:EIP7805]*

Nội dung request:

```
(
  slot: Slot
  dependent_root: Root
  indices: InclusionListBits
)
```

Nội dung response:

```
(
  SignedInclusionLists
)
```

Yêu cầu các inclusion list theo `slot`, `dependent_root` và các `indices` trong
inclusion list committee. Trường `indices` được hiểu tương ứng với
`get_inclusion_list_committee(state, slot)`, trong đó `state` là state thu được
khi xử lý block có root `dependent_root` cho tới slot `slot`. Response là một
danh sách `SignedInclusionList` có độ dài nhỏ hơn hoặc bằng số inclusion list
được yêu cầu. Độ dài có thể nhỏ hơn trong trường hợp peer phản hồi không có đủ
các inclusion list đó.

> 💡 Ghi chú: `indices` là một bitfield (`InclusionListBits`), mỗi bit ứng với
> một vị trí trong inclusion list committee của slot đó; bit bật nghĩa là muốn
> lấy inclusion list của thành viên ở vị trí tương ứng.

Không được yêu cầu quá `MAX_REQUEST_INCLUSION_LIST` inclusion list trong một
lần.

`InclusionListsByIndices` chủ yếu được dùng để lấy về các inclusion list có thể
đã bị bỏ lỡ trên gossip (ví dụ khi đang tạo execution payload cho một slot mà
còn thiếu một số inclusion list).

Request MUST được mã hóa dưới dạng một SSZ container.

Response MUST gồm không hoặc nhiều `response_chunk`. Mỗi `response_chunk` thành
công MUST chứa đúng một payload `SignedInclusionList`.

Client MUST hỗ trợ việc yêu cầu inclusion list kể từ `minimum_request_slot`,
trong đó
`minimum_request_slot = max(current_slot - MIN_SLOTS_FOR_INCLUSION_LISTS_REQUESTS, compute_start_slot_at_epoch(HEZE_FORK_EPOCH))`.
Nếu `slot` trong nội dung request trỏ tới một slot sớm hơn
`minimum_request_slot`, peer MAY phản hồi với mã lỗi `3: ResourceUnavailable`
hoặc không đưa các inclusion list đó vào response.

Client MUST phản hồi ít nhất một inclusion list nếu có. Client MAY giới hạn số
lượng inclusion list trong response.

Client SHOULD đưa một inclusion list vào response ngay khi nó vượt qua các quy
tắc gossip validation. Client SHOULD NOT phản hồi bằng các inclusion list không
vượt qua quy tắc gossip validation. Client SHOULD NOT phản hồi bằng các
inclusion list đến từ equivocator (validator đã ký hai inclusion list mâu thuẫn)
đối với `slot` và `dependent_root` được yêu cầu.

Với mỗi `response_chunk` thành công, epoch của context `ForkDigest` được xác
định bằng `compute_epoch_at_slot(signed_inclusion_list.message.slot)`.

Theo `fork_version = compute_fork_version(epoch)`:

<!-- eth_consensus_specs: skip -->

| `fork_version`      | Chunk SSZ type             |
| ------------------- | -------------------------- |
| `HEZE_FORK_VERSION` | `heze.SignedInclusionList` |
