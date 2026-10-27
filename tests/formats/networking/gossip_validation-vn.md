# Gossip validation tests

Mục đích của các test kiểm tra hợp lệ gossip (gossip validation) là cung cấp độ
phủ kiểm thử cho các quy tắc kiểm tra hợp lệ (validation rules) áp dụng lên các
message nhận được qua các gossip topic.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Test case format](#test-case-format)
  - [`meta.yaml`](#metayaml)
  - [`state.ssz_snappy`](#statessz_snappy)
  - [Message files](#message-files)
- [Condition](#condition)
- [Expected results](#expected-results)

<!-- mdformat-toc end -->

## Test case format

### `meta.yaml`

```yaml
topic: string                -- The gossip topic name (e.g., "beacon_block", "blob_sidecar",
                             -- "data_column_sidecar", "partial_data_column_sidecar").
blocks: [{                   -- Optional. Blocks to import before validation (oldest to newest).
                             -- The first entry is the anchor block, consistent with
                             -- `state.ssz_snappy` (the anchor state); it initializes
                             -- the store and is not state-transitioned.
    block: string,           -- The block file (without extension).
    failed: bool,            -- Optional. If true, the block fails state transition.
                             -- Track it as seen but invalid, with no post-state
                             -- (for testing descendant rejection).
    pending: bool,           -- Optional. If true, the block has been seen but not
                             -- yet imported, e.g. it is queued for processing.
                             -- Track it as seen, with no post-state.
    payload_status: string,  -- Optional. Execution payload status for this block:
                             -- "VALID" | "INVALIDATED" | "NOT_VALIDATED".
                             -- Maps to the corresponding `PAYLOAD_STATUS_*` value
                             -- in the relevant specification.
    payload: string,         -- Optional. `SignedExecutionPayloadEnvelope` file for
                             -- this block. The envelope has been received and
                             -- verified, as recorded by `on_execution_payload_envelope`.
}]
finalized_checkpoint:        -- Optional. Custom finalized checkpoint. Use it wherever
                             -- validation consults finalization: the store's finalized
                             -- checkpoint and any state-based finalized checkpoint view
                             -- (e.g. builder activation).
  epoch: int                 -- The epoch of the finalized checkpoint.
  root: string               -- Hex-encoded root (use this OR block, not both).
  block: string              -- Block file whose root to use (use this OR root, not both).
seen_partial_data_column_headers: [{
                             -- Optional. Preload validated partial
                             -- data column headers into `seen`.
    block_root: string,      -- Hex-encoded partial message group root.
    header: string,          -- `PartialDataColumnHeader` file to cache.
}]
messages: [{                 -- List of messages to validate in sequence.
    current_time_ms: int,    -- Optional. The Unix time in milliseconds when the
                             -- message is received. Present if and only if the
                             -- validation function takes `current_time_ms`.
    subnet_id: int,          -- Optional. The subnet ID for subnet-scoped topics.
    column_index: int,       -- Optional. The column index for
                             -- `partial_data_column_sidecar` vectors.
    group_id: string,        -- Optional. The `PartialDataColumnGroupID` file
                             -- (without extension) for
                             -- `partial_data_column_sidecar` vectors.
    message: string,         -- The name of the message file (without extension).
    expected: string,        -- Expected result: "valid", "ignore", or "reject".
    reason: string,          -- Optional. The expected reason for ignore/reject.
}]
```

> 💡 Ghi chú: Tóm tắt các trường trong `meta.yaml` ở trên:
>
> - `topic`: tên gossip topic cần kiểm tra (ví dụ `"beacon_block"`,
>   `"blob_sidecar"`, `"data_column_sidecar"`, `"partial_data_column_sidecar"`).
> - `blocks` (tùy chọn): danh sách block cần import trước khi validation, theo
>   thứ tự từ cũ nhất đến mới nhất. Phần tử đầu tiên là anchor block, khớp với
>   `state.ssz_snappy` (anchor state); nó dùng để khởi tạo store và **không**
>   chạy state transition. Mỗi phần tử có:
>   - `block`: tên file block (không kèm phần mở rộng).
>   - `failed` (tùy chọn): nếu `true`, block này thất bại khi chạy state
>     transition — ghi nhận là đã thấy (seen) nhưng không hợp lệ, không có
>     post-state (dùng để test việc reject các block con cháu).
>   - `pending` (tùy chọn): nếu `true`, block đã được thấy nhưng chưa được
>     import (ví dụ đang nằm trong hàng đợi xử lý) — ghi nhận là seen, không có
>     post-state.
>   - `payload_status` (tùy chọn): trạng thái execution payload của block:
>     `"VALID"` | `"INVALIDATED"` | `"NOT_VALIDATED"`, tương ứng với giá trị
>     `PAYLOAD_STATUS_*` trong spec liên quan.
>   - `payload` (tùy chọn): file `SignedExecutionPayloadEnvelope` của block
>     này. Envelope đã được nhận và xác minh, đúng như
>     `on_execution_payload_envelope` sẽ ghi nhận.
> - `finalized_checkpoint` (tùy chọn): finalized checkpoint tùy chỉnh. Dùng nó ở
>   mọi chỗ mà validation tham chiếu đến finalization: cả finalized checkpoint
>   của store lẫn mọi góc nhìn finalized checkpoint dựa trên state (ví dụ
>   builder activation). Gồm `epoch`, và **một trong hai**: `root` (root mã hóa
>   hex) hoặc `block` (file block mà root của nó sẽ được dùng) — không dùng cả
>   hai.
> - `seen_partial_data_column_headers` (tùy chọn): nạp trước các partial data
>   column header đã được validate vào `seen`. Mỗi phần tử gồm `block_root`
>   (root của nhóm partial message, mã hóa hex) và `header` (file
>   `PartialDataColumnHeader` cần cache).
> - `messages`: danh sách message cần validate theo thứ tự. Mỗi phần tử gồm:
>   - `current_time_ms` (tùy chọn): thời điểm Unix (mili giây) nhận message.
>     Có mặt khi và chỉ khi hàm validation nhận tham số `current_time_ms`.
>   - `subnet_id` (tùy chọn): subnet ID cho các topic theo subnet.
>   - `column_index` (tùy chọn): chỉ số cột cho các vector
>     `partial_data_column_sidecar`.
>   - `group_id` (tùy chọn): file `PartialDataColumnGroupID` (không kèm phần mở
>     rộng) cho các vector `partial_data_column_sidecar`.
>   - `message`: tên file message (không kèm phần mở rộng).
>   - `expected`: kết quả mong đợi: `"valid"`, `"ignore"` hoặc `"reject"`.
>   - `reason` (tùy chọn): lý do mong đợi khi ignore/reject.

### `state.ssz_snappy`

Một `BeaconState` được mã hóa SSZ-snappy: đây là anchor state, trên đó các block
trong `blocks` (nếu có) được phát lại (replay). State này khớp với block đầu
tiên trong `blocks` (tức `state_root` của block đó chính là root của state này).
State này cung cấp:

- Điểm neo (anchor) cho fork choice store; từ đó post-state của từng block được
  suy ra bằng cách import lần lượt các block còn lại.
- `genesis_time`: dùng cho các phép tính thời gian.
- `finalized_checkpoint`: dùng cho các kiểm tra liên quan đến finalization (trừ
  khi bị ghi đè).
- Public key của các validator: dùng để xác minh signature.

### Message files

Các file message được đặt tên theo dạng: một tiền tố cho biết loại message, theo
sau là hash tree root 32 byte của nó:

| Topic                                   | File prefix                       | SSZ type                             |
| --------------------------------------- | --------------------------------- | ------------------------------------ |
| `beacon_block`                          | `block_`                          | `SignedBeaconBlock`                  |
| `beacon_attestation`                    | `attestation_`                    | `Attestation`                        |
| `beacon_aggregate_and_proof`            | `aggregate_`                      | `SignedAggregateAndProof`            |
| `proposer_slashing`                     | `proposer_slashing_`              | `ProposerSlashing`                   |
| `attester_slashing`                     | `attester_slashing_`              | `AttesterSlashing`                   |
| `voluntary_exit`                        | `voluntary_exit_`                 | `SignedVoluntaryExit`                |
| `sync_committee_contribution_and_proof` | `contribution_`                   | `SignedContributionAndProof`         |
| `sync_committee`                        | `sync_committee_message_`         | `SyncCommitteeMessage`               |
| `bls_to_execution_change`               | `bls_to_execution_change_`        | `SignedBLSToExecutionChange`         |
| `blob_sidecar`                          | `blob_sidecar_`                   | `BlobSidecar`                        |
| `data_column_sidecar`                   | `data_column_sidecar_`            | `DataColumnSidecar`                  |
| `partial_data_column_group_id`          | `partial_data_column_group_id_`   | `PartialDataColumnGroupID`           |
| `partial_data_column_header`            | `partial_data_column_header_`     | `PartialDataColumnHeader`            |
| `partial_data_column_sidecar`           | `partial_data_column_sidecar_`    | `PartialDataColumnSidecar`           |
| `randao_commitment_registration`        | `randao_commitment_registration_` | `SignedRandaoCommitmentRegistration` |

Các file block (`block_<root>.ssz_snappy`) được dùng cho nhiều mục đích:

1. **Block trong store**: được tham chiếu trong danh sách `blocks` của
   `meta.yaml`.
2. **Message**: được tham chiếu bởi trường `message` trong danh sách messages
   (đối với topic `beacon_block`).

## Condition

1. Giải mã (deserialize) `state.ssz_snappy` để lấy anchor state.
2. Khởi tạo store từ anchor state và block đầu tiên trong `blocks` (block có
   `state_root` khớp với anchor state), giống như cách `get_forkchoice_store`
   thực hiện. Không chạy state transition cho anchor block. Sau đó, với mỗi phần
   tử tiếp theo trong `blocks` (từ cũ nhất đến mới nhất):
   - Import block bằng cách áp dụng state transition lên post-state của block
     cha, từ đó suy ra post-state của block.
     - Nếu `failed: true`, block thất bại khi chạy state transition. Ghi nhận nó
       là đã thấy nhưng không hợp lệ: block được biết đến, nhưng không có
       post-state (dùng để test việc reject các block con cháu).
     - Nếu `pending: true`, không import block. Ghi nhận nó là đã thấy và không
       có post-state, như thể block đang nằm trong hàng đợi xử lý.
   - Nếu có `payload`, ghi nhận message của envelope được tham chiếu cho block
     đó, giống như `on_execution_payload_envelope` sẽ làm (ví dụ thêm vào
     `store.payloads`).
   - Nếu có `payload_status`, theo dõi trạng thái execution payload của block
     đó.
     - `VALID`: execution payload của block được biết là hợp lệ.
     - `INVALIDATED`: execution payload của block được biết là không hợp lệ.
     - `NOT_VALIDATED`: execution payload của block chưa được kiểm tra.
     - Với gossip validation của `beacon_block`, `NOT_VALIDATED` biểu diễn
       trường hợp optimistic, khi chưa có kết quả valid/invalid nào cho payload
       của block cha.
3. Nếu `meta.finalized_checkpoint` được chỉ định, dùng nó làm finalized
   checkpoint ở mọi chỗ validation tham chiếu đến finalization (thay thế cả
   finalized checkpoint của store lẫn mọi góc nhìn finalized checkpoint dựa trên
   state).
4. Nếu có `seen_partial_data_column_headers`, nạp trước từng
   `PartialDataColumnHeader` được tham chiếu vào
   `seen.partial_data_column_headers`, dùng `block_root` tương ứng làm khóa.
5. Duyệt tuần tự qua `messages`:
   - Giải mã file message dựa theo loại topic.
   - Gọi hàm validation phù hợp, sử dụng store đã xây dựng ở trên.
     - Nếu hàm validation nhận tham số `current_time_ms`, truyền vào
       `message.current_time_ms`. Các giá trị này không nhất thiết tăng dần.
     - Với các topic theo subnet như `beacon_attestation`, `blob_sidecar` và
       `data_column_sidecar`, truyền vào `message.subnet_id`.
     - Với `partial_data_column_sidecar`, truyền vào `PartialDataColumnGroupID`
       được tham chiếu bởi `message.group_id`, cùng với `message.column_index`.
   - Kiểm tra kết quả có khớp với `expected` hay không.
   - Nếu kết quả là `valid`, cập nhật store đúng như hàm validation sẽ làm (ví
     dụ thêm vào `seen_proposer_slots`, ghi nhận các attestation đã thấy).

## Expected results

| Result   | Mô tả                                                |
| -------- | ---------------------------------------------------- |
| `valid`  | Message vượt qua tất cả các kiểm tra hợp lệ.         |
| `ignore` | Message không thỏa mãn một điều kiện `[IGNORE]`.     |
| `reject` | Message không thỏa mãn một điều kiện `[REJECT]`.     |

Các test case được xây dựng sao cho mọi điều kiện validation bị vi phạm đều cho
ra cùng một kết quả mong đợi: client có thể đánh giá các điều kiện độc lập theo
bất kỳ thứ tự nào mà không làm thay đổi kết quả. Một số điều kiện chỉ có thể
được đánh giá sau khi một điều kiện khác đã thỏa mãn (ví dụ: một kiểm tra đọc bản
ghi builder đòi hỏi kiểm tra giới hạn builder index phải qua trước, và các kiểm
tra dùng state của block cha đòi hỏi block cha phải được biết đến) — các vector
luôn tôn trọng những phụ thuộc như vậy. Chuỗi `reason` phản ánh thứ tự kiểm tra
trong spec và chỉ mang tính tham khảo.
