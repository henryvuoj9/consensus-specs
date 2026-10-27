# Fork choice tests

Mục đích của các fork choice test là cung cấp độ bao phủ kiểm thử cho các thành
phần khác nhau của fork choice.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Test case format](#test-case-format)
  - [`meta.yaml`](#metayaml)
  - [`anchor_state.ssz_snappy`](#anchor_statessz_snappy)
  - [`anchor_block.ssz_snappy`](#anchor_blockssz_snappy)
  - [`steps.yaml`](#stepsyaml)
    - [`on_tick` execution step](#on_tick-execution-step)
    - [`on_attestation` execution step](#on_attestation-execution-step)
    - [`on_block` execution step](#on_block-execution-step)
    - [`on_merge_block` execution step](#on_merge_block-execution-step)
    - [`on_attester_slashing` execution step](#on_attester_slashing-execution-step)
    - [`on_payload_info` execution step](#on_payload_info-execution-step)
    - [`on_execution_payload_envelope` execution step](#on_execution_payload_envelope-execution-step)
    - [`on_payload_attestation_message` execution step](#on_payload_attestation_message-execution-step)
    - [Checks step](#checks-step)
  - [`attestation_<32-byte-root>.ssz_snappy`](#attestation_32-byte-rootssz_snappy)
  - [`block_<32-byte-root>.ssz_snappy`](#block_32-byte-rootssz_snappy)
  - [`execution_payload_envelope_<32-byte-root>.ssz_snappy`](#execution_payload_envelope_32-byte-rootssz_snappy)
  - [`payload_attestation_message_<32-byte-root>.ssz_snappy`](#payload_attestation_message_32-byte-rootssz_snappy)
- [Condition](#condition)

<!-- mdformat-toc end -->

## Test case format

### `meta.yaml`

```yaml
description: string    -- Optional. Description of test case, purely for debugging purposes.
bls_setting: int       -- see general test-format spec.
```

### `anchor_state.ssz_snappy`

Một `BeaconState` được mã hóa SSZ-snappy: state dùng để khởi tạo store thông qua
helper
`get_forkchoice_store(anchor_state: BeaconState, anchor_block: BeaconBlock)`.

### `anchor_block.ssz_snappy`

Một `BeaconBlock` được mã hóa SSZ-snappy: block dùng để khởi tạo store thông qua
helper
`get_forkchoice_store(anchor_state: BeaconState, anchor_block: BeaconBlock)`.

> 💡 Ghi chú: anchor state và anchor block là điểm "neo" mà từ đó fork choice
> store bắt đầu (thường là genesis, hoặc một checkpoint tin cậy).

### `steps.yaml`

Các bước cần thực thi theo thứ tự. Có thể có nhiều mục thuộc các loại sau:

#### `on_tick` execution step

Tham số cần thiết để thực thi `on_tick(store, time_ms)`. Lưu ý rằng `tick` tính
bằng giây, trong khi `on_tick` nhận đơn vị mili giây.

```yaml
{
    tick: int       -- to execute `on_tick(store, seconds_to_milliseconds(tick))`.
    valid: bool     -- optional, default to `true`.
                       If it's `false`, this execution step is expected to be invalid.
}
```

Sau bước này, object `store` có thể đã được cập nhật.

#### `on_attestation` execution step

Tham số cần thiết để thực thi `on_attestation(store, attestation)`.

```yaml
{
    attestation: string  -- the name of the `attestation_<32-byte-root>.ssz_snappy` file.
                            To execute `on_attestation(store, attestation)` with the given attestation.
    valid: bool          -- optional, default to `true`.
                            If it's `false`, this execution step is expected to be invalid.
}
```

File này nằm trong cùng thư mục (xem bên dưới).

Sau bước này, object `store` có thể đã được cập nhật.

#### `on_block` execution step

Tham số cần thiết để thực thi `on_block(store, block)`.

```yaml
{
    block: string           -- the name of the `block_<32-byte-root>.ssz_snappy` file.
                              To execute `on_block(store, block)` with the given attestation.
    blobs: string           -- optional, the name of the `blobs_<32-byte-root>.ssz_snappy` file.
                               The blobs file content is a `List[Blob, MAX_BLOB_COMMITMENTS_PER_BLOCK]` SSZ object.
    proofs: array of byte48 hex string -- optional, the proofs of blob commitments.
    columns: string        -- optional, array of the names of the `column_<32-byte-root>.ssz_snappy` files.
    valid: bool             -- optional, default to `true`.
                               If it's `false`, this execution step is expected to be invalid.
}
```

File này nằm trong cùng thư mục (xem bên dưới).

`blobs` và `proofs` là các field mới từ Deneb EIP-4844. Các field này cho biết
giá trị mong đợi được trả về từ helper `retrieve_blobs_and_proofs()` bên trong
helper `is_data_available()`. Nếu hai field này không được cung cấp,
`retrieve_blobs_and_proofs()` trả về các list rỗng.

`columns` là field mới trong Fulu EIP-7594. Field này cho biết giá trị mong đợi
được trả về từ helper `retrieve_column_sidecars` bên trong helper
`is_data_available()`. Nếu field này là một mảng rỗng, `retrieve_column_sidecars`
cần ném ra một exception (do chưa sampling đủ dữ liệu). Nếu field này không được
cung cấp, `retrieve_column_sidecars` trả về một list rỗng.

> 💡 Ghi chú: Hãy phân biệt hai trường hợp: `columns: []` (mảng rỗng) nghĩa là
> data không available → exception; còn không có field `columns` nghĩa là trả về
> list rỗng (ví dụ block không có blob nào).

Sau Deneb và trước Fulu, `columns` không nên xuất hiện. Sau Fulu, `blobs` và
`proofs` không nên xuất hiện.

Sau bước này, object `store` có thể đã được cập nhật.

#### `on_merge_block` execution step

Bổ sung dữ liệu `PowBlock` cần thiết để thực thi `on_block(store, block)`.

```yaml
{
    pow_block: string  -- the name of the `pow_block_<32-byte-root>.ssz_snappy` file.
                          To be used in `get_pow_block` lookup
}
```

File này nằm trong cùng thư mục (xem bên dưới). Các PowBlock cần được dùng làm
giá trị trả về cho hàm `get_pow_block(hash: Hash32) -> PowBlock` nếu hash khớp.

#### `on_attester_slashing` execution step

Tham số cần thiết để thực thi `on_attester_slashing(store, attester_slashing)`.

```yaml
{
    attester_slashing: string  -- the name of the `attester_slashing_<32-byte-root>.ssz_snappy` file.
                            To execute `on_attester_slashing(store, attester_slashing)` with the given attester slashing.
    valid: bool          -- optional, default to `true`.
                            If it's `false`, this execution step is expected to be invalid.
}
```

File này nằm trong cùng thư mục (xem bên dưới).

Sau bước này, object `store` có thể đã được cập nhật.

#### `on_payload_info` execution step

Bước tùy chọn dành cho các test optimistic sync.

```yaml
{
    block_hash: string,             -- Encoded 32-byte value of payload's block hash.
    payload_status: {
        status: string,             -- Enum, "VALID" | "INVALID" | "SYNCING" | "ACCEPTED" | "INVALID_BLOCK_HASH".
        latest_valid_hash: string,    -- Encoded 32-byte value of the latest valid block hash, may be `null`.
        validation_error: string,    -- Message providing additional details on the validation error, may be `null`.
    }
}
```

Bước này thiết lập giá trị
[`payloadStatus`](https://github.com/ethereum/execution-apis/blob/main/src/engine/paris.md#payloadstatusv1)
mà execution-layer client giả lập (mock) trả về trong phản hồi cho các lời gọi
Engine API sau:

- [`engine_newPayloadV1(payload)`](https://github.com/ethereum/execution-apis/blob/main/src/engine/paris.md#engine_newpayloadv1)
  nếu `payload.blockHash == payload_info.block_hash`
- [`engine_forkchoiceUpdatedV1(forkchoiceState, ...)`](https://github.com/ethereum/execution-apis/blob/main/src/engine/paris.md#engine_forkchoiceupdatedv1)
  nếu `forkchoiceState.headBlockHash == payload_info.block_hash`

*Lưu ý*: Status của một payload phải được *khởi tạo* thông qua `on_payload_info`
trước bước thực thi `on_block` tương ứng.

*Lưu ý*: Status của cùng một payload có thể được cập nhật nhiều lần trong suốt
quá trình test.

#### `on_execution_payload_envelope` execution step

Tham số cần thiết để thực thi
`on_execution_payload_envelope(store, signed_execution_payload_envelope)`.

```yaml
{
    execution_payload: string  -- the name of the `execution_payload_envelope_<32-byte-root>.ssz_snappy` file.
                                  To execute `on_execution_payload_envelope(store, signed_envelope)` with the given envelope.
    valid: bool                -- optional, default to `true`.
                                  If it's `false`, this execution step is expected to be invalid.
}
```

File này nằm trong cùng thư mục (xem bên dưới).

Sau bước này, object `store` có thể đã được cập nhật.

#### `on_payload_attestation_message` execution step

Tham số cần thiết để thực thi
`on_payload_attestation_message(store, ptc_message)`.

```yaml
{
    payload_attestation_message: string  -- the name of the `payload_attestation_message_<32-byte-root>.ssz_snappy` file.
                                            To execute `on_payload_attestation_message(store, ptc_message)` with the given message.
    valid: bool                          -- optional, default to `true`.
                                            If it's `false`, this execution step is expected to be invalid.
}
```

File này nằm trong cùng thư mục (xem bên dưới).

Bước thực thi này có từ Gloas và các fork sau đó.

Sau bước này, object `store` có thể đã được cập nhật.

#### Checks step

Các check để xác minh trạng thái hiện tại của `store`.

```yaml
checks: {<store_attribute>: value}  -- the assertions.
```

`<store_attribute>` là field thành viên hoặc thuộc tính của object
[`Store`](../../../specs/phase0/fork-choice.md#store) được duy trì bởi
implementation của client. Các field bao gồm:

```yaml
head: {
    slot: int,
    root: string,             -- Encoded 32-byte value from get_head(store).root
    payload_status: int,      -- Gloas and later, the head's payload_status
}
time: int                     -- milliseconds_to_seconds(store.time_ms)
genesis_time: int             -- milliseconds_to_seconds(store.genesis_time_ms)
justified_checkpoint: {
    epoch: int,               -- Integer value from store.justified_checkpoint.epoch
    root: string,             -- Encoded 32-byte value from store.justified_checkpoint.root
}
finalized_checkpoint: {
    epoch: int,               -- Integer value from store.finalized_checkpoint.epoch
    root: string,             -- Encoded 32-byte value from store.finalized_checkpoint.root
}
proposer_boost_root: string   -- Encoded 32-byte value from store.proposer_boost_root
viable_for_head_roots_and_weights: [{
    root: string,             -- Encoded 32-byte value of filtered_node_tree leaf blocks/nodes
    weight: int,              -- Integer value of the weight of the block/node
    payload_status: int,      -- Gloas and later, the payload_status of the node
}]
```

Ngoài ra, có thêm các field sau nếu `get_proposer_head` được triển khai:

```yaml
get_proposer_head: string             -- Encoded 32-byte value from get_proposer_head(store)
payload_timeliness_vote: {            -- [New in Gloas]
    block_root: string,               -- Encoded 32-byte beacon block root
    votes: [bool | null, ...]         -- Votes ordered by PTC positions. Length is `PTC_SIZE`.
}
payload_data_availability_vote: {     -- [New in Gloas]
    block_root: string,               -- Encoded 32-byte beacon block root
    votes: [bool | null, ...]         -- Votes ordered by PTC positions. Length is `PTC_SIZE`.
}
```

Ví dụ:

```yaml
- checks:
    time: 192
    head: {slot: 32, root: '0xdaa1d49d57594ced0c35688a6da133abb086d191a2ebdfd736fad95299325aeb'}
    justified_checkpoint: {epoch: 3, root: '0xc25faab4acab38d3560864ca01e4d5cc4dc2cd473da053fbc03c2669143a2de4'}
    finalized_checkpoint: {epoch: 2, root: '0x40d32d6283ec11c53317a46808bc88f55657d93b95a1af920403187accf48f4f'}
    proposer_boost_root: '0xdaa1d49d57594ced0c35688a6da133abb086d191a2ebdfd736fad95299325aeb'
    get_proposer_head: '0xdaa1d49d57594ced0c35688a6da133abb086d191a2ebdfd736fad95299325aeb'
    viable_for_head_roots_and_weights: [
      {root: '0x533290b6f44d31c925acd08dfc8448624979d48c40b877d4e6714648866c9ddb', weight: 192000000000},
      {root: '0x5cfb9d9099cdf1d8ab68ce96cdae9f0fa6eef16914a01070580dfdc1d2d59ec3', weight: 544000000000}
    ]
```

*Lưu ý*: Mỗi bước `checks` có thể bao gồm một hoặc nhiều mục. Mỗi mục phải được
kiểm tra đối chiếu với store hiện tại.

### `attestation_<32-byte-root>.ssz_snappy`

`<32-byte-root>` là hash tree root của attestation tương ứng.

Mỗi file là một `Attestation` được mã hóa SSZ-snappy.

### `block_<32-byte-root>.ssz_snappy`

`<32-byte-root>` là hash tree root của `BeaconBlock` (tức field `message` của
`SignedBeaconBlock`).

Mỗi file là một `SignedBeaconBlock` được mã hóa SSZ-snappy.

### `execution_payload_envelope_<32-byte-root>.ssz_snappy`

`<32-byte-root>` là hash tree root của signed envelope tương ứng.

Mỗi file là một `SignedExecutionPayloadEnvelope` được mã hóa SSZ-snappy.

### `payload_attestation_message_<32-byte-root>.ssz_snappy`

`<32-byte-root>` là hash tree root của payload attestation message tương ứng.

Mỗi file là một `PayloadAttestationMessage` được mã hóa SSZ-snappy.

## Condition

1. Deserialize `anchor_state.ssz_snappy` và `anchor_block.ssz_snappy` để khởi
   tạo object store cục bộ bằng helper
   `get_forkchoice_store(anchor_state, anchor_block)`.
2. Duyệt tuần tự qua `steps.yaml`
   - Với mỗi bước thực thi, tìm file ssz_snappy tương ứng. Thực thi hàm helper
     tương ứng trên store hiện tại.
     - Với bước thực thi `on_block`: nếu
       `len(block.message.body.attestations) > 0`, thực thi từng attestation
       bằng `on_attestation(store, attestation)` sau khi đã thực thi
       `on_block(store, block)`. Với Gloas và các fork sau đó, nếu
       `len(block.message.body.payload_attestations) > 0`, hãy tách mỗi
       `PayloadAttestation` thành các giá trị `PayloadAttestationMessage` thành
       phần của nó và thực thi từng cái bằng
       `on_payload_attestation_message(store, ptc_message, is_from_block=True)`
       sau khi đã thực thi `on_block(store, block)`.
     - Với bước thực thi `on_execution_payload_envelope`: tìm file
       `execution_payload_envelope_<root>.ssz_snappy` tương ứng và thực thi
       `on_execution_payload_envelope(store, signed_envelope)`.
     - Với bước thực thi `on_payload_attestation_message`: tìm file
       `payload_attestation_message_<root>.ssz_snappy` tương ứng và thực thi
       `on_payload_attestation_message(store, ptc_message)`.
   - Với mỗi bước `checks`, các assertion trên store hiện tại phải được thỏa
     mãn.
