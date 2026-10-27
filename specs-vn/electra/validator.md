# Electra -- Honest Validator

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Helpers](#helpers)
  - [Modified `GetPayloadResponse`](#modified-getpayloadresponse)
- [Containers](#containers)
  - [Modified containers](#modified-containers)
    - [`AggregateAndProof`](#aggregateandproof)
    - [`SignedAggregateAndProof`](#signedaggregateandproof)
- [Protocols](#protocols)
  - [`ExecutionEngine`](#executionengine)
    - [Modified `get_payload`](#modified-get_payload)
- [Block and sidecar proposal](#block-and-sidecar-proposal)
  - [Constructing the `BeaconBlockBody`](#constructing-the-beaconblockbody)
    - [Attester slashings](#attester-slashings)
    - [Attestations](#attestations)
    - [Deposits](#deposits)
    - [Execution requests](#execution-requests)
  - [Constructing the `BlobSidecar`s](#constructing-the-blobsidecars)
    - [Sidecar](#sidecar)
- [Attesting](#attesting)
  - [Construct attestation](#construct-attestation)
- [Attestation aggregation](#attestation-aggregation)
  - [Construct aggregate](#construct-aggregate)

<!-- mdformat-toc end -->

## Introduction

*(Giới thiệu)*

Tài liệu này mô tả những thay đổi cần thực hiện trong code của một "validator
trung thực" (honest validator) để triển khai Electra.

## Prerequisites

*(Điều kiện tiên quyết)*

Tài liệu này là phần mở rộng của hướng dẫn
[Deneb -- Honest Validator](../deneb/validator.md). Mọi hành vi và định nghĩa
trong tài liệu này, cũng như trong các tài liệu mà nó mở rộng, vẫn được giữ
nguyên trừ khi được ghi chú rõ ràng hoặc bị ghi đè.

Toàn bộ thuật ngữ, hằng số, hàm và cơ chế giao thức được định nghĩa trong đặc tả
beacon-chain đã cập nhật của [Electra](./beacon-chain.md) là kiến thức bắt buộc
cho tài liệu này và được sử dụng xuyên suốt. Vui lòng đọc các đặc tả beacon-chain
liên quan trước khi tiếp tục và dùng chúng làm tài liệu tham chiếu trong suốt quá
trình đọc.

## Helpers

### Modified `GetPayloadResponse`

```python
@dataclass
class GetPayloadResponse:
    execution_payload: ExecutionPayload
    block_value: Uint256
    blobs_bundle: BlobsBundle
    # [New in Electra]
    execution_requests: Sequence[bytes]
```

## Containers

### Modified containers

#### `AggregateAndProof`

```python
class AggregateAndProof(Container):
    aggregator_index: ValidatorIndex
    # [Modified in Electra:EIP7549]
    aggregate: Attestation
    selection_proof: BLSSignature
```

#### `SignedAggregateAndProof`

```python
class SignedAggregateAndProof(Container):
    # [Modified in Electra:EIP7549]
    message: AggregateAndProof
    signature: BLSSignature
```

## Protocols

### `ExecutionEngine`

#### Modified `get_payload`

*Ghi chú*: Hàm `get_payload` trả về đối tượng `GetPayloadResponse` đã được cập
nhật (có thêm trường `execution_requests`).

```python
def get_payload(self: ExecutionEngine, payload_id: PayloadId) -> GetPayloadResponse:
    """
    Return ExecutionPayload, Uint256, BlobsBundle, and execution requests (as Sequence[bytes]) objects.
    """
```

## Block and sidecar proposal

*(Đề xuất block và sidecar)*

### Constructing the `BeaconBlockBody`

#### Attester slashings

Số lượng attester slashing tối đa trong block được đổi thành
`MAX_ATTESTER_SLASHINGS_ELECTRA`.

#### Attestations

Số lượng attestation tối đa trong block được đổi thành `MAX_ATTESTATIONS_ELECTRA`.

Các aggregate attestation trên mạng (network aggregate) chỉ chứa attestation của
committee được phân công. Các aggregate attestation mà block proposer nhận được
từ các aggregator của từng committee, nếu có tập `committee_bits` rời nhau
(không giao nhau) và có cùng `AttestationData`, thì SHOULD được hợp nhất thành
một đối tượng `Attestation` duy nhất. Proposer nên chạy hàm sau để tạo ra
aggregate cuối cùng đưa lên chain (on-chain aggregate) từ danh sách các network
aggregate có cùng `AttestationData`:

```python
def compute_on_chain_aggregate(network_aggregates: Sequence[Attestation]) -> Attestation:
    aggregates = sorted(
        network_aggregates, key=lambda a: get_committee_indices(a.committee_bits)[0]
    )

    data = aggregates[0].data
    aggregation_bits = AggregationBits()
    for a in aggregates:
        for b in a.aggregation_bits:
            aggregation_bits.append(b)

    signature = bls.Aggregate([aggregate.signature for aggregate in aggregates])

    committee_indices = [
        get_committee_indices(aggregate.committee_bits)[0] for aggregate in aggregates
    ]
    committee_flags = [(index in committee_indices) for index in range(MAX_COMMITTEES_PER_SLOT)]
    committee_bits = CommitteeBits(data=committee_flags)

    return Attestation(
        aggregation_bits=AggregationBits(data=aggregation_bits),
        data=data,
        signature=signature,
        committee_bits=CommitteeBits(data=committee_bits),
    )
```

> 💡 Ghi chú: Hàm này sắp xếp các network aggregate theo committee index tăng dần,
> nối liên tiếp các `aggregation_bits` của chúng thành một bitfield duy nhất, gộp
> các chữ ký BLS bằng `bls.Aggregate`, và bật bit tương ứng với mỗi committee có
> mặt trong `committee_bits`. Nhờ vậy, một `Attestation` on-chain có thể đại diện
> cho nhiều committee trong cùng một slot (EIP-7549).

#### Deposits

*[New in Electra:EIP6110]* Số lượng deposit dự kiến (phải đưa vào block) MUST
được đổi từ
`min(MAX_DEPOSITS, eth1_data.deposit_count - state.eth1_deposit_index)` thành
kết quả của hàm sau:

```python
def get_eth1_pending_deposit_count(state: BeaconState) -> Uint64:
    eth1_deposit_index_limit = min(
        state.eth1_data.deposit_count, state.deposit_requests_start_index
    )
    if state.eth1_deposit_index < eth1_deposit_index_limit:
        return min(MAX_DEPOSITS, eth1_deposit_index_limit - state.eth1_deposit_index)
    else:
        return Uint64(0)
```

> 💡 Ghi chú: Từ EIP-6110, deposit được đưa vào chain trực tiếp qua execution
> request. Các deposit theo cơ chế `Eth1Data` cũ chỉ còn cần xử lý cho đến
> `state.deposit_requests_start_index`; sau ngưỡng đó, hàm trả về 0.

*Ghi chú*: Các client sẽ có thể loại bỏ cơ chế polling `Eth1Data` một cách không
cần phối hợp (mỗi client tự làm vào thời điểm của mình) khi giai đoạn chuyển
tiếp kết thúc. Giai đoạn chuyển tiếp được xem là kết thúc khi mạng đạt tới thời
điểm mà `state.eth1_deposit_index == state.deposit_requests_start_index`.

```python
def get_eth1_vote(state: BeaconState, eth1_chain: Sequence[Eth1Block]) -> Eth1Data:
    # [New in Electra:EIP6110]
    if state.eth1_deposit_index == state.deposit_requests_start_index:
        return state.eth1_data

    period_start = voting_period_start_time(state)
    # `eth1_chain` abstractly represents all blocks in the eth1 chain sorted by ascending block height
    votes_to_consider = [
        get_eth1_data(block)
        for block in eth1_chain
        if (
            is_candidate_block(block, period_start)
            # Ensure cannot move back to earlier deposit contract states
            and get_eth1_data(block).deposit_count >= state.eth1_data.deposit_count
        )
    ]

    # Valid votes already cast during this period
    valid_votes = [vote for vote in state.eth1_data_votes if vote in votes_to_consider]

    # Default vote on latest eth1 block data in the period range unless eth1 chain is not live
    # Non-substantive casting for linter
    state_eth1_data: Eth1Data = state.eth1_data
    default_vote = (
        votes_to_consider[len(votes_to_consider) - 1] if any(votes_to_consider) else state_eth1_data
    )

    return max(
        valid_votes,
        # Tiebreak by smallest distance
        key=lambda v: (
            valid_votes.count(v),
            -valid_votes.index(v),
        ),
        default=default_vote,
    )
```

#### Execution requests

*[New in Electra]*

1. Execution payload được lấy từ execution engine như đã định nghĩa ở trên, bằng
   `payload_id`. Response cũng chứa một mục `execution_requests` là một danh sách
   các chuỗi byte. Mỗi phần tử trong danh sách tương ứng với một SSZ list các
   request như định nghĩa trong
   [EIP-7685](https://eips.ethereum.org/EIPS/eip-7685). Byte đầu tiên của mỗi
   request được dùng để xác định loại request. Các request phải được sắp xếp
   theo loại request tăng dần. Do đó, mỗi loại request chỉ có thể xuất hiện tối
   đa một lần.
2. Gán
   `block.body.execution_requests = get_execution_requests(execution_requests)`,
   trong đó:

```python
def get_execution_requests(execution_requests_list: Sequence[bytes]) -> ExecutionRequests:
    deposits = DepositRequests()
    withdrawals = WithdrawalRequests()
    consolidations = ConsolidationRequests()

    request_types = [
        DEPOSIT_REQUEST_TYPE,
        WITHDRAWAL_REQUEST_TYPE,
        CONSOLIDATION_REQUEST_TYPE,
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

    return ExecutionRequests(
        deposits=deposits,
        withdrawals=withdrawals,
        consolidations=consolidations,
    )
```

### Constructing the `BlobSidecar`s

#### Sidecar

*[Modified in Electra:EIP7691]*

```python
def compute_subnet_for_blob_sidecar(blob_index: BlobIndex) -> SubnetID:
    return SubnetID(blob_index % BLOB_SIDECAR_SUBNET_COUNT_ELECTRA)
```

## Attesting

### Construct attestation

*(Tạo attestation)*

Validator tạo `attestation` dưới dạng một container `SingleAttestation` với các
trường được gán như sau:

- Gán `attestation_data.index = 0`.
- Gán `attestation.committee_index` bằng index của committee mà validator thuộc
  về.
- Gán `attestation.attester_index` bằng index của validator.

## Attestation aggregation

### Construct aggregate

*(Tạo aggregate)*

- Gán `attestation_data.index = 0`.
- Gán `aggregate_attestation.aggregation_bits` là một `AggregationBits` có độ dài
  `len(committee)`, trong đó các bit ứng với `attester_index` của từng
  `SingleAttestation` đầu vào được đặt thành `0b1`.
- Gán `aggregate_attestation.committee_bits` là một `CommitteeBits` trong đó chỉ
  duy nhất bit ứng với `committee_index` chung của tất cả các `SingleAttestation`
  đầu vào được đặt thành `0b1`.
