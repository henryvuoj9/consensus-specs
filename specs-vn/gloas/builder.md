# Gloas -- Honest Builder

*Ghi chú*: Tài liệu này đang trong quá trình hoàn thiện, dành cho các nhà nghiên
cứu và người triển khai (implementer).

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Becoming a builder](#becoming-a-builder)
  - [Submit deposit](#submit-deposit)
  - [Process deposit](#process-deposit)
  - [Builder index](#builder-index)
  - [Activation](#activation)
  - [Exiting](#exiting)
- [Builder activities](#builder-activities)
  - [Constructing the `SignedExecutionPayloadBid`](#constructing-the-signedexecutionpayloadbid)
  - [Constructing the `DataColumnSidecar`s](#constructing-the-datacolumnsidecars)
    - [Modified `get_data_column_sidecars`](#modified-get_data_column_sidecars)
    - [Modified `get_data_column_sidecars_from_block`](#modified-get_data_column_sidecars_from_block)
  - [Constructing the `SignedExecutionPayloadEnvelope`](#constructing-the-signedexecutionpayloadenvelope)
  - [Honest payload withheld messages](#honest-payload-withheld-messages)

<!-- mdformat-toc end -->

## Introduction

Đây là tài liệu đi kèm, mô tả các hành động được kỳ vọng của một "builder" khi
tham gia vào giao thức proof-of-stake của Ethereum.

Với bản nâng cấp Gloas, giao thức giới thiệu một loại tác nhân có stake mới
(không phải validator) gọi là *builder*. Vì builder không phải là validator, họ
không thực hiện các nhiệm vụ của validator (ví dụ attest và propose) và do đó
không nhận lợi suất (yield) trên số tiền stake của mình. Builder có thể (tùy chọn)
tạo ra execution payload bằng cách gửi các bid (giá thầu). Tài liệu này là tập
hợp các hướng dẫn dành cho builder.

> 💡 Ghi chú: Đây là một phần của ePBS (enshrined Proposer-Builder Separation,
> EIP-7732): proposer chọn bid của một builder và đưa bid đó vào beacon block;
> builder sau đó công bố execution payload tương ứng.

## Becoming a builder

### Submit deposit

Builder được tạo ra bằng cách gửi một builder deposit request tới builder deposit
contract trên execution layer, như được định nghĩa trong EIP-8282. Request phải
bao gồm:

- `pubkey`: BLS public key của builder.
- `withdrawal_credentials`: withdrawal credential, trong đó byte đầu tiên là
  `BUILDER_WITHDRAWAL_PREFIX` và 20 byte cuối là địa chỉ trên execution layer sẽ
  nhận các withdrawal.
- `amount`: tối thiểu `MIN_DEPOSIT_AMOUNT` gwei.
- `signature`: BLS proof of possession (bằng chứng sở hữu private key) trên
  `DepositMessage` tương ứng, với domain `DOMAIN_BUILDER_DEPOSIT`.

*Ghi chú*: Một builder deposit request có withdrawal credential không bắt đầu
bằng `BUILDER_WITHDRAWAL_PREFIX` sẽ bị bỏ qua và số tiền sẽ bị mất.

*Ghi chú*: Builder có thể được đưa vào hệ thống ngay tại thời điểm fork bằng cách
gửi deposit tới validator deposit contract với withdrawal credential có prefix
`BUILDER_WITHDRAWAL_PREFIX`. Việc này phải được thực hiện đủ muộn để deposit vẫn
còn ở trạng thái pending tại thời điểm fork, nhưng cũng đủ sớm để slot mà deposit
được thêm vào hàng đợi pending deposit đã được finalized, nhờ đó builder được coi
là active. Một deposit như vậy ký trên `DepositMessage` với domain
`DOMAIN_DEPOSIT`, với withdrawal credential có dạng
`BUILDER_WITHDRAWAL_PREFIX + b"\x00" * 11 + execution_address`.

### Process deposit

Một builder deposit request cho một pubkey mới sẽ đăng ký một builder. Một
request cho pubkey của builder đã tồn tại sẽ nạp thêm (top up) vào balance của
builder đó.

### Builder index

Khi deposit được xử lý trên beacon chain, builder được gán một `builder_index`
duy nhất trong builder registry. Index này được dùng để xác định builder trong
các execution payload bid và envelope.

### Activation

Builder trở thành active khi epoch mà nó được đăng ký (được gán index) đã được
finalized. Vì việc đăng ký diễn ra ngay khi deposit đến được beacon chain, builder
thường trở thành active khoảng hai epoch sau khi gửi deposit.

*Ghi chú*: Tại thời điểm fork, các pending deposit có `BUILDER_WITHDRAWAL_PREFIX`
được áp dụng vào builder registry. `deposit_epoch` của builder được đặt bằng
epoch của pending deposit, không phải epoch của fork. Do đó, nếu epoch đó đã được
finalized tại thời điểm fork, builder sẽ active ngay lập tức. Xem
`onboard_builders_from_pending_deposits` để biết chi tiết.

### Exiting

Builder exit bằng cách gửi một builder exit request tới builder exit contract
trên execution layer, như được định nghĩa trong EIP-8282. Request chứa `pubkey`
của builder và được ủy quyền bởi `execution_address` của builder (người gửi giao
dịch), chứ không phải bởi BLS key.

Consensus layer chỉ khởi tạo exit nếu builder đang active, `source_address` của
request khớp với `execution_address` của builder, và builder không còn balance
nào đang chờ rút (pending balance to withdraw). Nếu không, request sẽ bị tiêu thụ
mà không có tác dụng gì và phải được gửi lại khi các điều kiện trên được thỏa
mãn.

## Builder activities

Builder có hai hoạt động tùy chọn: gửi bid và gửi payload. Builder có thể gửi bid
để giành quyền tạo execution payload. Họ có thể broadcast các bid này dưới dạng
các object `SignedExecutionPayloadBid`. Các object này mã hóa một cam kết sẽ công
bố một execution payload để đổi lấy một khoản thanh toán. Khi bid của họ được
proposer tương ứng chọn, builder được kỳ vọng sẽ broadcast một object
`SignedExecutionPayloadEnvelope` đi kèm để thực hiện cam kết. Nếu proposer chấp
nhận bid của một builder, builder sẽ trả cho proposer số tiền đã hứa bất kể
builder có gửi payload hay không.

### Constructing the `SignedExecutionPayloadBid`

Builder có thể broadcast một payload bid để proposer của slot hiện tại hoặc slot
kế tiếp đưa vào block. Builder tạo `SignedExecutionPayloadBid` như sau.

01. Đặt `bid.parent_block_hash` là parent hash của payload được xây dựng, tức là
    `payload.parent_hash`.
02. Đặt `bid.parent_block_root` là head của chuỗi consensus. Giá trị này có thể
    lấy từ beacon state dưới dạng `hash_tree_root(state.latest_block_header)`.
    `parent_block_root` và `parent_block_hash` phải tương thích với nhau, theo
    nghĩa là cả hai nên được lấy từ cùng một `state` và `store` bằng phương pháp
    mô tả ở bước này và bước trước.
03. Xây dựng một execution payload. Việc này có thể được thực hiện với một
    execution engine bên ngoài thông qua lời gọi `engine_getPayloadV6`.
04. Đặt `bid.block_hash` là block hash của payload được xây dựng, tức là
    `payload.block_hash`.
05. Đặt `bid.prev_randao` là giá trị previous RANDAO của payload được xây dựng,
    tức là `payload.prev_randao`. Giá trị này **MUST** bằng
    `get_randao_mix(parent_state, get_current_epoch(parent_state))`, trong đó
    `parent_state` là post-state của `bid.parent_block_root`.
06. Đặt `bid.slot` là slot mà bid này nhắm tới. Slot này **MUST** là slot hiện
    tại hoặc slot kế tiếp.
07. Đặt `bid.fee_recipient` là một execution address để nhận khoản thanh toán.
    Fee recipient mà proposer mong muốn được lấy từ `SignedProposerPreferences`
    có `message.proposal_slot` khớp với `bid.slot` và có `message.dependent_root`
    khớp với
    `get_shuffling_dependent_root(store, bid.parent_block_root, compute_epoch_at_slot(bid.slot))`,
    trong đó `store` là fork choice store.
08. Đặt `bid.gas_limit` là gas limit của payload được xây dựng, giá trị này
    **MUST** thỏa mãn
    `is_gas_limit_target_compatible(parent_gas_limit, bid.gas_limit, target_gas_limit)`,
    trong đó `parent_gas_limit` là `gas_limit` của parent execution payload và
    `target_gas_limit` là `target_gas_limit` trong `SignedProposerPreferences`
    được nhắc đến ở bước 7.
09. Đặt `bid.builder_index` là index của builder đang thực hiện các bước này.
10. Đặt `bid.value` là giá trị (tính bằng gwei) mà builder sẽ trả cho proposer
    nếu bid được chấp nhận. Builder **MUST** có đủ balance dư để đáp ứng bid này
    cùng với tất cả các khoản thanh toán đang pending.
11. Đặt `bid.execution_payment` bằng 0. Giá trị khác 0 biểu thị một khoản thanh
    toán tin cậy (trusted) trên execution layer. Các bid có `execution_payment`
    khác 0 **MUST NOT** được broadcast lên gossip topic `execution_payload_bid`.
12. Đặt `bid.blob_kzg_commitments` là trường `blobsbundle.commitments` được trả
    về bởi `engine_getPayloadV6`.
13. Đặt `bid.execution_requests_root` bằng `hash_tree_root(execution_requests)`,
    trong đó `execution_requests` là trường `ExecutionRequests` được trả về bởi
    `engine_getPayloadV6`.

Sau khi xây dựng `bid`, builder lấy `signature` của bid bằng cách dùng:

```python
def get_execution_payload_bid_signature(
    state: BeaconState, bid: ExecutionPayloadBid, privkey: int
) -> BLSSignature:
    domain = get_domain(state, DOMAIN_BEACON_BUILDER, compute_epoch_at_slot(bid.slot))
    signing_root = compute_signing_root(bid, domain)
    return bls.Sign(privkey, signing_root)
```

Sau đó builder tạo
`signed_execution_payload_bid = SignedExecutionPayloadBid(message=bid, signature=signature)`
và broadcast nó lên global gossip topic `execution_payload_bid`.

### Constructing the `DataColumnSidecar`s

#### Modified `get_data_column_sidecars`

```python
def get_data_column_sidecars(
    # [Modified in Gloas:EIP7732]
    # Removed `signed_block_header`
    # [New in Gloas:EIP7732]
    beacon_block_root: Root,
    # [New in Gloas:EIP7732]
    slot: Slot,
    # [Modified in Gloas:EIP7732]
    # Removed `kzg_commitments`
    # [Modified in Gloas:EIP7732]
    # Removed `kzg_commitments_inclusion_proof`
    cells_and_kzg_proofs: Sequence[tuple[Cells, Proofs]],
) -> Sequence[DataColumnSidecar]:
    """
    Given a beacon block root and the cells/proofs associated with each blob
    in the corresponding payload, assemble the sidecars which can be
    distributed to peers.
    """
    sidecars = []
    for column_index in range(NUMBER_OF_COLUMNS):
        column_cells = DataColumn()
        column_proofs = KZGProofs()
        for cells, proofs in cells_and_kzg_proofs:
            column_cells.append(cells[column_index])
            column_proofs.append(proofs[column_index])
        sidecars.append(
            # [Modified in Gloas:EIP7732]
            DataColumnSidecar(
                index=ColumnIndex(column_index),
                column=column_cells,
                kzg_proofs=column_proofs,
                slot=slot,
                beacon_block_root=beacon_block_root,
            )
        )
    return sidecars
```

> 💡 Ghi chú: Trong Gloas, `DataColumnSidecar` không còn chứa signed block header,
> danh sách KZG commitment hay inclusion proof; thay vào đó nó chỉ tham chiếu
> `beacon_block_root` và `slot`. Các KZG commitment nằm trong bid đã được đưa vào
> beacon block.

#### Modified `get_data_column_sidecars_from_block`

*Ghi chú*: Hàm `get_data_column_sidecars_from_block` được sửa để dùng
`beacon_block_root` thay vì tính toán header và inclusion proof.

```python
def get_data_column_sidecars_from_block(
    signed_block: SignedBeaconBlock,
    cells_and_kzg_proofs: Sequence[tuple[Cells, Proofs]],
) -> Sequence[DataColumnSidecar]:
    """
    Given a signed block and the cells/proofs associated with each blob in the
    block, assemble the sidecars which can be distributed to peers.
    """
    beacon_block_root = hash_tree_root(signed_block.message)
    return get_data_column_sidecars(
        beacon_block_root,
        signed_block.message.slot,
        cells_and_kzg_proofs,
    )
```

### Constructing the `SignedExecutionPayloadEnvelope`

Khi proposer công bố một `SignedBeaconBlock` hợp lệ có chứa cam kết đã ký của
builder, builder sau đó được kỳ vọng sẽ broadcast `SignedExecutionPayloadEnvelope`
tương ứng để thực hiện cam kết này. Xem bên dưới về một trường hợp đặc biệt:
*payload được giữ lại một cách trung thực* (honestly withheld payload).

Để xây dựng `ExecutionPayloadEnvelope`, builder phải thực hiện các bước sau. Ta
gọi tắt `block` là `BeaconBlock` tương ứng và `bid` là `ExecutionPayloadBid` đã
được cam kết trong `block.body.signed_execution_payload_bid.message`.

1. Đặt `envelope.payload` là `ExecutionPayload` đã được xây dựng khi tạo bid
   tương ứng. Payload này **MUST** có cùng block hash với `bid.block_hash`.
2. Đặt `envelope.execution_requests` là `ExecutionRequests` gắn với `payload`.
3. Đặt `envelope.builder_index` là index của builder đang thực hiện các bước
   này. Trường này **MUST** bằng `bid.builder_index`.
4. Đặt `envelope.beacon_block_root` bằng `hash_tree_root(block)`.
5. Đặt `envelope.parent_beacon_block_root` bằng `block.parent_root`.

Sau khi chuẩn bị `envelope`, builder ký nó bằng cách dùng:

```python
def get_execution_payload_envelope_signature(
    state: BeaconState, envelope: ExecutionPayloadEnvelope, privkey: int
) -> BLSSignature:
    domain = get_domain(state, DOMAIN_BEACON_BUILDER, compute_epoch_at_slot(state.slot))
    signing_root = compute_signing_root(envelope, domain)
    return bls.Sign(privkey, signing_root)
```

Sau đó builder tạo
`signed_execution_payload_envelope = SignedExecutionPayloadEnvelope(message=envelope, signature=signature)`
và broadcast nó lên global gossip topic `execution_payload`.

### Honest payload withheld messages

Một builder trung thực đã thấy một `SignedBeaconBlock` tham chiếu tới bid đã ký
của mình, nhưng block đó không đến kịp thời (not timely) và do đó không phải là
head trong chuỗi của builder, có thể chọn giữ lại (withhold) execution payload
của mình. Khi đó, builder nên hành động như thể không có block nào được tạo ra và
không broadcast payload.
