# Operations tests

Các loại operation khác nhau (có thể hiểu là các "giao dịch" trong block) được
kiểm thử riêng lẻ, mỗi loại bằng một test handler.

## Test case format

### `meta.yaml`

```yaml
description: string    -- Optional description of test case, purely for debugging purposes.
                          Tests should use the directory name of the test case as identifier, not the description.
bls_setting: int       -- see general test-format spec.
parent_slot: int       -- Only for the `attestation` handler in Gloas and later.
                          The slot of the parent block, an extra input to `process_attestation`.
```

> 💡 Ghi chú: `description` là mô tả tùy chọn, chỉ phục vụ debug — test nên dùng
> tên thư mục của test case làm định danh, không dùng description. `bls_setting`
> xem trong spec test-format chung. `parent_slot` chỉ có ở handler `attestation`
> từ Gloas trở đi: đó là slot của block cha, một đầu vào bổ sung cho
> `process_attestation`.

### `pre.ssz_snappy`

Một `BeaconState` mã hóa SSZ-snappy: state trước khi áp dụng operation.

### `<input-name>.ssz_snappy`

Một đối tượng operation mã hóa SSZ-snappy, ví dụ `ProposerSlashing` hoặc
`Deposit`.

### `post.ssz_snappy`

Một `BeaconState` mã hóa SSZ-snappy: state sau khi áp dụng operation. File này
không có nếu việc xử lý operation bị hủy bỏ (abort).

## Condition

Một handler của test-runner `operations` cần xử lý các test case này bằng cách
gọi hàm xử lý (processing) tương ứng. Các phần khác của block-transition không
được thực hiện.

Danh sách operation:

| *`operation-name`*               | *`operation-object`*                 | *`input name`*                   | *`processing call`*                                                                               |
| -------------------------------- | ------------------------------------ | -------------------------------- | ------------------------------------------------------------------------------------------------- |
| `attestation`                    | `Attestation`                        | `attestation`                    | `process_attestation(state, attestation)` (`parent_slot` added in Gloas)                          |
| `attester_slashing`              | `AttesterSlashing`                   | `attester_slashing`              | `process_attester_slashing(state, attester_slashing)`                                             |
| `block_header`                   | `BeaconBlock`                        | **`block`**                      | `process_block_header(state, block)`                                                              |
| `deposit`                        | `Deposit`                            | `deposit`                        | `process_deposit(state, deposit)` (removed in Fulu)                                               |
| `proposer_slashing`              | `ProposerSlashing`                   | `proposer_slashing`              | `process_proposer_slashing(state, proposer_slashing)`                                             |
| `voluntary_exit`                 | `SignedVoluntaryExit`                | `voluntary_exit`                 | `process_voluntary_exit(state, voluntary_exit)`                                                   |
| `sync_aggregate`                 | `SyncAggregate`                      | `sync_aggregate`                 | `process_sync_aggregate(state, sync_aggregate)` (new in Altair)                                   |
| `execution_payload`              | `BeaconBlockBody`                    | **`body`**                       | `process_execution_payload(state, body)` (new in Bellatrix, removed in Gloas)                     |
| `withdrawals`                    | `ExecutionPayload`                   | `execution_payload`              | `process_withdrawals(state, execution_payload)` (new in Capella)                                  |
| `bls_to_execution_change`        | `SignedBLSToExecutionChange`         | `address_change`                 | `process_bls_to_execution_change(state, address_change)` (new in Capella)                         |
| `deposit_request`                | `DepositRequest`                     | `deposit_request`                | `process_deposit_request(state, deposit_request)` (new in Electra)                                |
| `withdrawal_request`             | `WithdrawalRequest`                  | `withdrawal_request`             | `process_withdrawal_request(state, withdrawal_request)` (new in Electra)                          |
| `consolidation_request`          | `ConsolidationRequest`               | `consolidation_request`          | `process_consolidation_request(state, consolidation_request)` (new in Electra)                    |
| `execution_payload_bid`          | `SignedExecutionPayloadBid`          | `execution_payload_bid`          | `process_execution_payload_bid(state, execution_payload_bid)` (new in Gloas)                      |
| `parent_execution_payload`       | `BeaconBlock`                        | **`block`**                      | `process_parent_execution_payload(state, block)` (new in Gloas)                                   |
| `payload_attestation`            | `PayloadAttestation`                 | `payload_attestation`            | `process_payload_attestation(state, payload_attestation)` (new in Gloas)                          |
| `builder_deposit_request`        | `BuilderDepositRequest`              | `builder_deposit_request`        | `process_builder_deposit_request(state, builder_deposit_request)` (new in Gloas)                  |
| `builder_exit_request`           | `BuilderExitRequest`                 | `builder_exit_request`           | `process_builder_exit_request(state, builder_exit_request)` (new in Gloas)                        |
| `randao_commitment_registration` | `SignedRandaoCommitmentRegistration` | `randao_commitment_registration` | `process_randao_commitment_registration(state, randao_commitment_registration)` (new in EIP-8321) |

> 💡 Ghi chú: Cột cuối cho biết hàm xử lý cần gọi; chú thích trong ngoặc cho biết
> fork mà operation được thêm vào ("new in ...") hoặc bị loại bỏ ("removed in
> ..."). Với `attestation`, từ Gloas có thêm tham số `parent_slot`.

Lưu ý rằng `block_header` không hẳn là một operation (và là một `Block` đầy đủ),
nhưng được xử lý theo cùng cách, nên cũng được đưa vào đây.

Việc xử lý `execution_payload` thông thường đòi hỏi gọi
`verify_execution_state_transition(execution_payload)`, vốn là trách nhiệm của
một execution engine (bên ngoài). Khi kiểm thử, phần thực thi này được giả lập
(mock): thay vào đó một file `execution.yml` được cung cấp — một dict chứa trường
boolean `execution_valid` là kết quả xác minh.

State thu được phải khớp với state `post` mong đợi; hoặc nếu state `post` bị để
trống, handler phải reject operation đầu vào vì không hợp lệ.
