# Gloas -- The Beacon Chain

*Lưu ý*: Tài liệu này vẫn đang trong quá trình hoàn thiện, dành cho các nhà nghiên cứu và đội ngũ triển khai client.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Types](#types)
  - [Modified `AggregationBits`](#modified-aggregationbits)
  - [Modified `Attestations`](#modified-attestations)
  - [Modified `AttesterSlashings`](#modified-attesterslashings)
  - [Modified `AttestingIndices`](#modified-attestingindices)
  - [Modified `Balances`](#modified-balances)
  - [Modified `BlobKZGCommitments`](#modified-blobkzgcommitments)
  - [Modified `BLSToExecutionChanges`](#modified-blstoexecutionchanges)
  - [Modified `ConsolidationRequests`](#modified-consolidationrequests)
  - [Modified `DepositRequests`](#modified-depositrequests)
  - [Modified `Deposits`](#modified-deposits)
  - [Modified `EpochParticipation`](#modified-epochparticipation)
  - [Modified `InactivityScores`](#modified-inactivityscores)
  - [Modified `PendingConsolidations`](#modified-pendingconsolidations)
  - [Modified `PendingDeposits`](#modified-pendingdeposits)
  - [Modified `PendingPartialWithdrawals`](#modified-pendingpartialwithdrawals)
  - [Modified `ProposerSlashings`](#modified-proposerslashings)
  - [Modified `Transaction`](#modified-transaction)
  - [Modified `Transactions`](#modified-transactions)
  - [Modified `Validators`](#modified-validators)
  - [Modified `VoluntaryExits`](#modified-voluntaryexits)
  - [Modified `WithdrawalRequests`](#modified-withdrawalrequests)
  - [Modified `Withdrawals`](#modified-withdrawals)
  - [New `BlockAccessList`](#new-blockaccesslist)
  - [New `BuilderDepositRequests`](#new-builderdepositrequests)
  - [New `BuilderExitRequests`](#new-builderexitrequests)
  - [New `BuilderIndex`](#new-builderindex)
  - [New `BuilderPendingPayments`](#new-builderpendingpayments)
  - [New `BuilderPendingWithdrawals`](#new-builderpendingwithdrawals)
  - [New `Builders`](#new-builders)
  - [New `ExecutionPayloadAvailability`](#new-executionpayloadavailability)
  - [New `PayloadAttestations`](#new-payloadattestations)
  - [New `PayloadTimelinessCommittee`](#new-payloadtimelinesscommittee)
  - [New `PayloadTimelinessCommitteeIndices`](#new-payloadtimelinesscommitteeindices)
  - [New `PayloadTimelinessCommitteeBits`](#new-payloadtimelinesscommitteebits)
  - [New `PayloadTimelinessCommitteeWindow`](#new-payloadtimelinesscommitteewindow)
- [Constants](#constants)
  - [Index flags](#index-flags)
  - [Domains](#domains)
  - [Misc](#misc)
  - [Withdrawal prefixes](#withdrawal-prefixes)
  - [Builder versions](#builder-versions)
  - [Execution-layer triggered requests](#execution-layer-triggered-requests)
- [Presets](#presets)
  - [Misc](#misc-1)
  - [Max operations per block](#max-operations-per-block)
  - [Execution](#execution)
  - [Withdrawals processing](#withdrawals-processing)
- [Configs](#configs)
  - [Validator cycle](#validator-cycle)
  - [Time parameters](#time-parameters)
  - [Gas limit schedule](#gas-limit-schedule)
- [Containers](#containers)
  - [New containers](#new-containers)
    - [`Builder`](#builder)
    - [`BuilderPendingPayment`](#builderpendingpayment)
    - [`BuilderPendingWithdrawal`](#builderpendingwithdrawal)
    - [`BuilderDepositRequest`](#builderdepositrequest)
    - [`BuilderExitRequest`](#builderexitrequest)
    - [`PayloadAttestationData`](#payloadattestationdata)
    - [`PayloadAttestation`](#payloadattestation)
    - [`PayloadAttestationMessage`](#payloadattestationmessage)
    - [`IndexedPayloadAttestation`](#indexedpayloadattestation)
    - [`ExecutionPayloadBid`](#executionpayloadbid)
    - [`SignedExecutionPayloadBid`](#signedexecutionpayloadbid)
    - [`ExecutionPayloadEnvelope`](#executionpayloadenvelope)
    - [`SignedExecutionPayloadEnvelope`](#signedexecutionpayloadenvelope)
  - [Modified containers](#modified-containers)
    - [`Attestation`](#attestation)
    - [`IndexedAttestation`](#indexedattestation)
    - [`BeaconBlockBody`](#beaconblockbody)
    - [`BeaconState`](#beaconstate)
    - [`ExecutionPayload`](#executionpayload)
    - [`ExecutionRequests`](#executionrequests)
    - [`NewPayloadRequest`](#newpayloadrequest)
- [Dataclasses](#dataclasses)
  - [Modified dataclasses](#modified-dataclasses)
    - [`ExpectedWithdrawals`](#expectedwithdrawals)
- [Helpers](#helpers)
  - [Predicates](#predicates)
    - [Modified `is_valid_indexed_attestation`](#modified-is_valid_indexed_attestation)
    - [New `is_builder_index`](#new-is_builder_index)
    - [New `is_active_builder`](#new-is_active_builder)
    - [New `is_builder_withdrawal_credential`](#new-is_builder_withdrawal_credential)
    - [New `is_attestation_same_slot`](#new-is_attestation_same_slot)
    - [New `is_valid_indexed_payload_attestation`](#new-is_valid_indexed_payload_attestation)
    - [New `is_pending_validator`](#new-is_pending_validator)
  - [Misc](#misc-2)
    - [New `convert_builder_index_to_validator_index`](#new-convert_builder_index_to_validator_index)
    - [New `convert_validator_index_to_builder_index`](#new-convert_validator_index_to_builder_index)
    - [New `get_scheduled_gas_limit`](#new-get_scheduled_gas_limit)
    - [New `get_pending_balance_to_withdraw_for_builder`](#new-get_pending_balance_to_withdraw_for_builder)
    - [New `can_builder_cover_bid`](#new-can_builder_cover_bid)
    - [New `compute_balance_weighted_selection`](#new-compute_balance_weighted_selection)
    - [Modified `compute_proposer_indices`](#modified-compute_proposer_indices)
    - [New `compute_ptc`](#new-compute_ptc)
  - [Beacon state accessors](#beacon-state-accessors)
    - [Modified `get_beacon_proposer_indices`](#modified-get_beacon_proposer_indices)
    - [Modified `get_next_sync_committee_indices`](#modified-get_next_sync_committee_indices)
    - [Modified `get_attestation_participation_flag_indices`](#modified-get_attestation_participation_flag_indices)
    - [New `get_ptc`](#new-get_ptc)
    - [New `get_indexed_payload_attestation`](#new-get_indexed_payload_attestation)
    - [New `get_builder_payment_quorum_threshold`](#new-get_builder_payment_quorum_threshold)
    - [New `get_activation_churn_limit`](#new-get_activation_churn_limit)
    - [New `get_exit_churn_limit`](#new-get_exit_churn_limit)
    - [Modified `get_consolidation_churn_limit`](#modified-get_consolidation_churn_limit)
    - [Modified `compute_exit_epoch_and_update_churn`](#modified-compute_exit_epoch_and_update_churn)
  - [Beacon state mutators](#beacon-state-mutators)
    - [New `initiate_builder_exit`](#new-initiate_builder_exit)
    - [New `settle_builder_payment`](#new-settle_builder_payment)
    - [Modified `slash_validator`](#modified-slash_validator)
- [Beacon chain state transition function](#beacon-chain-state-transition-function)
  - [Modified `process_slot`](#modified-process_slot)
  - [Epoch processing](#epoch-processing)
    - [Modified `process_epoch`](#modified-process_epoch)
    - [Modified `process_pending_deposits`](#modified-process_pending_deposits)
    - [New `process_builder_pending_payments`](#new-process_builder_pending_payments)
    - [New `process_ptc_window`](#new-process_ptc_window)
  - [Block processing](#block-processing)
    - [Parent execution payload](#parent-execution-payload)
      - [New `apply_parent_execution_payload`](#new-apply_parent_execution_payload)
      - [New `process_parent_execution_payload`](#new-process_parent_execution_payload)
    - [Withdrawals](#withdrawals)
      - [New `get_builder_withdrawals`](#new-get_builder_withdrawals)
      - [New `get_builder_balance_after_withdrawals`](#new-get_builder_balance_after_withdrawals)
      - [New `get_builders_sweep_withdrawals`](#new-get_builders_sweep_withdrawals)
      - [Modified `get_expected_withdrawals`](#modified-get_expected_withdrawals)
      - [Modified `apply_withdrawals`](#modified-apply_withdrawals)
      - [New `update_payload_expected_withdrawals`](#new-update_payload_expected_withdrawals)
      - [New `update_builder_pending_withdrawals`](#new-update_builder_pending_withdrawals)
      - [New `update_next_withdrawal_builder_index`](#new-update_next_withdrawal_builder_index)
      - [Modified `process_withdrawals`](#modified-process_withdrawals)
    - [Execution payload](#execution-payload)
      - [Removed `process_execution_payload`](#removed-process_execution_payload)
      - [New `verify_execution_payload_envelope_signature`](#new-verify_execution_payload_envelope_signature)
      - [Modified `get_execution_requests_list`](#modified-get_execution_requests_list)
    - [Execution payload bid](#execution-payload-bid)
      - [New `verify_execution_payload_bid_signature`](#new-verify_execution_payload_bid_signature)
      - [New `process_execution_payload_bid`](#new-process_execution_payload_bid)
    - [Operations](#operations)
      - [Modified `process_operations`](#modified-process_operations)
      - [Builder deposit requests](#builder-deposit-requests)
        - [New `is_valid_builder_deposit_signature`](#new-is_valid_builder_deposit_signature)
        - [New `get_index_for_new_builder`](#new-get_index_for_new_builder)
        - [New `add_builder_to_registry`](#new-add_builder_to_registry)
        - [New `process_builder_deposit_request`](#new-process_builder_deposit_request)
      - [Builder exit requests](#builder-exit-requests)
        - [New `process_builder_exit_request`](#new-process_builder_exit_request)
      - [Attestations](#attestations)
        - [Modified `process_attestation`](#modified-process_attestation)
      - [Payload attestations](#payload-attestations)
        - [New `process_payload_attestation`](#new-process_payload_attestation)

<!-- mdformat-toc end -->

## Introduction

Gloas là một bản nâng cấp tầng đồng thuận (consensus layer) gồm nhiều tính năng, cụ thể:

- [EIP-7688](https://github.com/ethereum/EIPs/blob/f2e6d7fb01194d590e16fcdcae8061d06cf1a7f1/EIPS/eip-7688.md):
  Các cấu trúc dữ liệu đồng thuận tương thích về sau (forward compatible) — dùng `ProgressiveList`/`ProgressiveContainer` để có thể thêm trường mà không làm đổi generalized index của các trường cũ
- [EIP-7732](https://github.com/ethereum/EIPs/blob/c36a2e58a4496ed21bef6b1c97505b03fd159f0a/EIPS/eip-7732.md):
  Tách vai trò proposer và builder ngay trong giao thức (Enshrined Proposer-Builder Separation, ePBS)
- [EIP-7843](https://github.com/ethereum/EIPs/blob/c3bfd4ba41cf0fcbfe8c404f33ba89f5174971e0/EIPS/eip-7843.md):
  Opcode SLOTNUM (trả về số slot hiện tại cho EVM)
- [EIP-8070](https://github.com/ethereum/EIPs/blob/f516cef8b482bf123d554ee12ff5b421f5578d38/EIPS/eip-8070.md):
  eth/72 - Sparse Blobpool (blobpool thưa)
- [EIP-8045](https://github.com/ethereum/EIPs/blob/414a8404198c5afaa3cfed10a385a9aae1dfaae3/EIPS/eip-8045.md):
  Loại các validator đã bị slashing (phạt cắt giảm stake) khỏi việc đề xuất block
- [EIP-8061](https://github.com/ethereum/EIPs/blob/01f15c37c64114c478cb1136e0a6966084e4db14/EIPS/eip-8061.md):
  Tăng churn (giới hạn lưu lượng) cho exit và consolidation
- [EIP-8261](https://github.com/ethereum/EIPs/blob/f6b4668ef37612feba85aef151303f4100b79360/EIPS/eip-8261.md):
  Lịch trình gas limit (Gas Limit Schedule)
- [EIP-8282](https://github.com/ethereum/EIPs/blob/de4c6f02c7bec4686762c55f8ab6abcf97a77d7d/EIPS/eip-8282.md):
  Các execution request dành cho builder (Builder Execution Requests)

*Lưu ý*: Các EIP này vẫn ở trạng thái bản nháp (draft) và có thể thay đổi hoặc bị
loại bỏ. Mỗi liên kết ở trên trỏ tới đúng phiên bản mà spec này nhắm tới, phiên bản
đó có thể khác với phiên bản EIP mới nhất đã được công bố.

## Types

*(Các kiểu dữ liệu SSZ. Phần lớn các list có giới hạn cố định trước đây được chuyển sang `ProgressiveList` theo EIP-7688.)*

### Modified `AggregationBits`

```python
# [Modified in Gloas:EIP7688]
class AggregationBits(ProgressiveBitList):
    """
    The participation bits of all committees participating in an attestation,
    concatenated in committee order.
    """
```

### Modified `Attestations`

```python
# [Modified in Gloas:EIP7688]
class Attestations(ProgressiveList[Attestation]):
    """
    The attestations included in a beacon block.
    """
```

### Modified `AttesterSlashings`

```python
# [Modified in Gloas:EIP7688]
class AttesterSlashings(ProgressiveList[AttesterSlashing]):
    """
    The attester slashings included in a beacon block.
    """
```

### Modified `AttestingIndices`

```python
# [Modified in Gloas:EIP7688]
class AttestingIndices(ProgressiveList[ValidatorIndex]):
    """
    The indices of the validators participating in an attestation.
    """
```

### Modified `Balances`

```python
# [Modified in Gloas:EIP7688]
class Balances(ProgressiveList[Gwei]):
    """
    The balances of all validators.
    """
```

### Modified `BlobKZGCommitments`

```python
# [Modified in Gloas:EIP7688]
class BlobKZGCommitments(ProgressiveList[KZGCommitment]):
    """
    The KZG commitments to the blobs of a beacon block.
    """
```

### Modified `BLSToExecutionChanges`

```python
# [Modified in Gloas:EIP7688]
class BLSToExecutionChanges(ProgressiveList[SignedBLSToExecutionChange]):
    """
    The signed BLS-to-execution credential changes included in a beacon
    block.
    """
```

### Modified `ConsolidationRequests`

```python
# [Modified in Gloas:EIP7688]
class ConsolidationRequests(ProgressiveList[ConsolidationRequest]):
    """
    The consolidation requests pertaining to a single execution payload.
    """
```

### Modified `DepositRequests`

```python
# [Modified in Gloas:EIP7688]
class DepositRequests(ProgressiveList[DepositRequest]):
    """
    The deposit requests pertaining to a single execution payload.
    """
```

### Modified `Deposits`

```python
# [Modified in Gloas:EIP7688]
class Deposits(ProgressiveList[Deposit]):
    """
    The deposits included in a beacon block.
    """
```

### Modified `EpochParticipation`

```python
# [Modified in Gloas:EIP7688]
class EpochParticipation(ProgressiveList[ParticipationFlags]):
    """
    The participation flags of each validator for an epoch.
    """
```

### Modified `InactivityScores`

```python
# [Modified in Gloas:EIP7688]
class InactivityScores(ProgressiveList[Uint64]):
    """
    Each validator's inactivity score, tracking missed timely target votes.
    """
```

### Modified `PendingConsolidations`

```python
# [Modified in Gloas:EIP7688]
class PendingConsolidations(ProgressiveList[PendingConsolidation]):
    """
    The queue of consolidations awaiting processing.
    """
```

### Modified `PendingDeposits`

```python
# [Modified in Gloas:EIP7688]
class PendingDeposits(ProgressiveList[PendingDeposit]):
    """
    The queue of deposits awaiting processing.
    """
```

### Modified `PendingPartialWithdrawals`

```python
# [Modified in Gloas:EIP7688]
class PendingPartialWithdrawals(ProgressiveList[PendingPartialWithdrawal]):
    """
    The queue of partial withdrawals awaiting processing.
    """
```

### Modified `ProposerSlashings`

```python
# [Modified in Gloas:EIP7688]
class ProposerSlashings(ProgressiveList[ProposerSlashing]):
    """
    The proposer slashings included in a beacon block.
    """
```

### Modified `Transaction`

```python
# [Modified in Gloas:EIP7688]
class Transaction(ProgressiveList[Byte]):
    """
    An opaque execution-layer transaction, either a typed transaction
    envelope or a legacy RLP-encoded transaction.
    """
```

### Modified `Transactions`

```python
# [Modified in Gloas:EIP7688]
class Transactions(ProgressiveList[Transaction]):
    """
    A list of execution-layer transactions.
    """
```

### Modified `Validators`

```python
# [Modified in Gloas:EIP7688]
class Validators(ProgressiveList[Validator]):
    """
    The validator registry.
    """
```

### Modified `VoluntaryExits`

```python
# [Modified in Gloas:EIP7688]
class VoluntaryExits(ProgressiveList[SignedVoluntaryExit]):
    """
    The signed voluntary exits included in a beacon block.
    """
```

### Modified `WithdrawalRequests`

```python
# [Modified in Gloas:EIP7688]
class WithdrawalRequests(ProgressiveList[WithdrawalRequest]):
    """
    The withdrawal requests pertaining to a single execution payload.
    """
```

### Modified `Withdrawals`

```python
# [Modified in Gloas:EIP7688]
class Withdrawals(ProgressiveList[Withdrawal]):
    """
    A list of withdrawals.
    """
```

### New `BlockAccessList`

```python
class BlockAccessList(ProgressiveList[Byte]):
    """
    The serialized block access list of an execution payload.
    """
```

### New `BuilderDepositRequests`

```python
class BuilderDepositRequests(ProgressiveList[BuilderDepositRequest]):
    """
    The builder deposit requests pertaining to a single execution payload.
    """
```

### New `BuilderExitRequests`

```python
class BuilderExitRequests(ProgressiveList[BuilderExitRequest]):
    """
    The builder exit requests pertaining to a single execution payload.
    """
```

### New `BuilderIndex`

```python
class BuilderIndex(Uint64):
    """
    The index of a builder in the builder registry.
    """
```

### New `BuilderPendingPayments`

```python
class BuilderPendingPayments(Vector[BuilderPendingPayment]):
    """
    The pending builder payments of the previous and current epoch.
    """

    LENGTH = 2 * SLOTS_PER_EPOCH
```

### New `BuilderPendingWithdrawals`

```python
class BuilderPendingWithdrawals(ProgressiveList[BuilderPendingWithdrawal]):
    """
    The queue of builder withdrawals awaiting processing.
    """
```

### New `Builders`

```python
class Builders(ProgressiveList[Builder]):
    """
    The builder registry.
    """
```

### New `ExecutionPayloadAvailability`

```python
class ExecutionPayloadAvailability(BitVector):
    """
    Bits tracking payload availability for recent slots, indexed by slot
    modulo ``SLOTS_PER_HISTORICAL_ROOT``.
    """

    LENGTH = SLOTS_PER_HISTORICAL_ROOT
```

### New `PayloadAttestations`

```python
class PayloadAttestations(ProgressiveList[PayloadAttestation]):
    """
    The payload attestations included in a beacon block.
    """
```

### New `PayloadTimelinessCommittee`

```python
class PayloadTimelinessCommittee(Vector[ValidatorIndex]):
    """
    The payload timeliness committee of a slot.
    """

    LENGTH = PTC_SIZE
```

### New `PayloadTimelinessCommitteeIndices`

```python
class PayloadTimelinessCommitteeIndices(List[ValidatorIndex]):
    """
    The indices of payload timeliness committee members, as a list limited
    by the size of the committee.
    """

    LIMIT = PTC_SIZE
```

### New `PayloadTimelinessCommitteeBits`

```python
class PayloadTimelinessCommitteeBits(BitVector):
    """
    The participation bits of the payload timeliness committee, one bit per
    member in committee order.
    """

    LENGTH = PTC_SIZE
```

### New `PayloadTimelinessCommitteeWindow`

```python
class PayloadTimelinessCommitteeWindow(Vector[PayloadTimelinessCommittee]):
    """
    A rolling window of payload timeliness committees for the previous,
    current, and lookahead epochs.
    """

    LENGTH = Uint64(MIN_SEED_LOOKAHEAD + 2) * Uint64(SLOTS_PER_EPOCH)
```

## Constants

### Index flags

*Lưu ý*: `BUILDER_INDEX_FLAG` là một cờ bit (bitwise flag) cho biết một
`ValidatorIndex` cần được hiểu là một `BuilderIndex`. Cờ này tồn tại để cùng một
container `Withdrawal` có thể dùng chung cho cả validator lẫn builder.

> 💡 Ghi chú: Nói cách khác, nếu bit thứ 40 của trường index trong `Withdrawal` được
> bật thì đó là withdrawal của builder (index thực = index sau khi bỏ cờ), ngược lại là
> withdrawal của validator thông thường.

| Name                 | Value           |
| -------------------- | --------------- |
| `BUILDER_INDEX_FLAG` | `Uint64(2**40)` |

### Domains

| Name                          | Value                      |
| ----------------------------- | -------------------------- |
| `DOMAIN_BEACON_BUILDER`       | `DomainType("0x0B000000")` |
| `DOMAIN_PTC_ATTESTER`         | `DomainType("0x0C000000")` |
| `DOMAIN_PROPOSER_PREFERENCES` | `DomainType("0x0D000000")` |
| `DOMAIN_BUILDER_DEPOSIT`      | `DomainType("0x0E000000")` |

### Misc

| Name                                    | Value                      |
| --------------------------------------- | -------------------------- |
| `BUILDER_INDEX_SELF_BUILD`              | `BuilderIndex(UINT64_MAX)` |
| `BUILDER_PAYMENT_THRESHOLD_NUMERATOR`   | `Uint64(6)`                |
| `BUILDER_PAYMENT_THRESHOLD_DENOMINATOR` | `Uint64(10)`               |

### Withdrawal prefixes

| Name                        | Value            |
| --------------------------- | ---------------- |
| `BUILDER_WITHDRAWAL_PREFIX` | `Bytes1("0xB0")` |

### Builder versions

| Name                      | Value      |
| ------------------------- | ---------- |
| `PAYLOAD_BUILDER_VERSION` | `Uint8(0)` |

### Execution-layer triggered requests

| Name                           | Value            |
| ------------------------------ | ---------------- |
| `BUILDER_DEPOSIT_REQUEST_TYPE` | `Bytes1("0x03")` |
| `BUILDER_EXIT_REQUEST_TYPE`    | `Bytes1("0x04")` |

## Presets

### Misc

| Name       | Value                  |
| ---------- | ---------------------- |
| `PTC_SIZE` | `Uint64(2**9)` (= 512) |

### Max operations per block

| Name                       | Value                |
| -------------------------- | -------------------- |
| `MAX_PAYLOAD_ATTESTATIONS` | `Uint64(2**2)` (= 4) |

### Execution

| Name                                       | Value                 |
| ------------------------------------------ | --------------------- |
| `MAX_BUILDER_DEPOSIT_REQUESTS_PER_PAYLOAD` | `Uint64(2**6)` (= 64) |
| `MAX_BUILDER_EXIT_REQUESTS_PER_PAYLOAD`    | `Uint64(2**4)` (= 16) |

### Withdrawals processing

| Name                                 | Value                      |
| ------------------------------------ | -------------------------- |
| `MAX_BUILDERS_PER_WITHDRAWALS_SWEEP` | `Uint64(2**14)` (= 16,384) |

## Configs

### Validator cycle

| Name                                         | Value                                    |
| -------------------------------------------- | ---------------------------------------- |
| `CHURN_LIMIT_QUOTIENT_GLOAS`                 | `Uint64(2**15)` (= 32,768)               |
| `CONSOLIDATION_CHURN_LIMIT_QUOTIENT`         | `Uint64(2**16)` (= 65,536)               |
| `MAX_PER_EPOCH_ACTIVATION_CHURN_LIMIT_GLOAS` | `Gwei(2**8 * 10**9)` (= 256,000,000,000) |

### Time parameters

| Name                                | Value                |
| ----------------------------------- | -------------------- |
| `MIN_BUILDER_WITHDRAWABILITY_DELAY` | `Epoch(2**6)` (= 64) |

### Gas limit schedule

*[New in Gloas:EIP8261]* Lịch trình này định nghĩa gas limit tối đa mặc định và
được khuyến nghị cho từng epoch. Trường này là tùy chọn: client nào không hỗ trợ thì
bỏ qua nó, và nó không đưa thêm bất kỳ quy tắc hợp lệ (validity rule) mới nào.

KHÔNG ĐƯỢC (MUST NOT) có nhiều mục trong gas limit schedule có cùng giá trị epoch.
Giá trị epoch của mỗi mục PHẢI (MUST) lớn hơn hoặc bằng `GLOAS_FORK_EPOCH`. Các mục
của gas limit schedule NÊN (SHOULD) được sắp xếp theo epoch tăng dần. Gas limit
schedule CÓ THỂ (MAY) rỗng.

<!-- list-of-records:gas_limit_schedule -->

| Epoch | Gas Limit | Date |
| ----: | --------: | ---: |

## Containers

### New containers

#### `Builder`

```python
class Builder(Container):
    pubkey: BLSPubkey
    version: Uint8
    execution_address: ExecutionAddress
    balance: Gwei
    deposit_epoch: Epoch
    withdrawable_epoch: Epoch
```

#### `BuilderPendingPayment`

```python
class BuilderPendingPayment(Container):
    weight: Gwei
    withdrawal: BuilderPendingWithdrawal
    proposer_index: ValidatorIndex
```

#### `BuilderPendingWithdrawal`

```python
class BuilderPendingWithdrawal(Container):
    fee_recipient: ExecutionAddress
    amount: Gwei
    builder_index: BuilderIndex
```

#### `BuilderDepositRequest`

```python
class BuilderDepositRequest(Container):
    pubkey: BLSPubkey
    withdrawal_credentials: Bytes32
    amount: Gwei
    signature: BLSSignature
```

#### `BuilderExitRequest`

```python
class BuilderExitRequest(Container):
    source_address: ExecutionAddress
    pubkey: BLSPubkey
```

#### `PayloadAttestationData`

```python
class PayloadAttestationData(Container):
    beacon_block_root: Root
    slot: Slot
    payload_present: Boolean
    blob_data_available: Boolean
```

#### `PayloadAttestation`

```python
class PayloadAttestation(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=3)

    aggregation_bits: PayloadTimelinessCommitteeBits
    data: PayloadAttestationData
    signature: BLSSignature
```

#### `PayloadAttestationMessage`

```python
class PayloadAttestationMessage(Container):
    validator_index: ValidatorIndex
    data: PayloadAttestationData
    signature: BLSSignature
```

#### `IndexedPayloadAttestation`

```python
class IndexedPayloadAttestation(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=3)

    attesting_indices: PayloadTimelinessCommitteeIndices
    data: PayloadAttestationData
    signature: BLSSignature
```

#### `ExecutionPayloadBid`

```python
class ExecutionPayloadBid(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=12)

    parent_block_hash: Hash32
    parent_block_root: Root
    block_hash: Hash32
    prev_randao: Bytes32
    fee_recipient: ExecutionAddress
    gas_limit: Uint64
    builder_index: BuilderIndex
    slot: Slot
    value: Gwei
    execution_payment: Gwei
    blob_kzg_commitments: BlobKZGCommitments
    execution_requests_root: Root
```

#### `SignedExecutionPayloadBid`

```python
class SignedExecutionPayloadBid(Container):
    message: ExecutionPayloadBid
    signature: BLSSignature
```

#### `ExecutionPayloadEnvelope`

```python
class ExecutionPayloadEnvelope(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=5)

    payload: ExecutionPayload
    execution_requests: ExecutionRequests
    builder_index: BuilderIndex
    beacon_block_root: Root
    parent_beacon_block_root: Root
```

#### `SignedExecutionPayloadEnvelope`

```python
class SignedExecutionPayloadEnvelope(Container):
    message: ExecutionPayloadEnvelope
    signature: BLSSignature
```

### Modified containers

#### `Attestation`

```python
# [Modified in Gloas:EIP7688]
class Attestation(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=4)

    aggregation_bits: AggregationBits
    data: AttestationData
    signature: BLSSignature
    committee_bits: CommitteeBits
```

#### `IndexedAttestation`

```python
# [Modified in Gloas:EIP7688]
class IndexedAttestation(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=3)

    attesting_indices: AttestingIndices
    data: AttestationData
    signature: BLSSignature
```

#### `BeaconBlockBody`

*Lưu ý*: Các trường đã bị loại bỏ (`execution_payload`, `blob_kzg_commitments` và
`execution_requests`) giờ nằm trong `ExecutionPayloadEnvelope`.

> 💡 Ghi chú: Với ePBS, beacon block chỉ chứa bid đã ký của builder
> (`signed_execution_payload_bid`); execution payload thực sự được builder công bố riêng
> sau đó trong một envelope (`SignedExecutionPayloadEnvelope`). Các execution request của
> payload ở slot cha được đưa vào block con qua trường `parent_execution_requests`.

```python
# [Modified in Gloas:EIP7688]
class BeaconBlockBody(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=13)

    randao_reveal: BLSSignature
    eth1_data: Eth1Data
    graffiti: Bytes32
    # [Modified in Gloas:EIP7688]
    proposer_slashings: ProposerSlashings
    # [Modified in Gloas:EIP7688]
    attester_slashings: AttesterSlashings
    # [Modified in Gloas:EIP7688]
    attestations: Attestations
    # [Modified in Gloas:EIP7688]
    deposits: Deposits
    # [Modified in Gloas:EIP7688]
    voluntary_exits: VoluntaryExits
    sync_aggregate: SyncAggregate
    # [Modified in Gloas:EIP7732]
    # Removed `execution_payload`
    # [Modified in Gloas:EIP7688]
    bls_to_execution_changes: BLSToExecutionChanges
    # [Modified in Gloas:EIP7732]
    # Removed `blob_kzg_commitments`
    # [Modified in Gloas:EIP7732]
    # Removed `execution_requests`
    # [New in Gloas:EIP7732]
    signed_execution_payload_bid: SignedExecutionPayloadBid
    # [New in Gloas:EIP7732]
    payload_attestations: PayloadAttestations
    # [New in Gloas:EIP7732]
    parent_execution_requests: ExecutionRequests
```

#### `BeaconState`

```python
# [Modified in Gloas:EIP7688]
class BeaconState(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=46)

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
    # [Modified in Gloas:EIP7688]
    validators: Validators
    # [Modified in Gloas:EIP7688]
    balances: Balances
    randao_mixes: RandaoMixes
    slashings: Slashings
    # [Modified in Gloas:EIP7688]
    previous_epoch_participation: EpochParticipation
    # [Modified in Gloas:EIP7688]
    current_epoch_participation: EpochParticipation
    justification_bits: JustificationBits
    previous_justified_checkpoint: Checkpoint
    current_justified_checkpoint: Checkpoint
    finalized_checkpoint: Checkpoint
    # [Modified in Gloas:EIP7688]
    inactivity_scores: InactivityScores
    current_sync_committee: SyncCommittee
    next_sync_committee: SyncCommittee
    # [Modified in Gloas:EIP7732]
    # Removed `latest_execution_payload_header`
    # [New in Gloas:EIP7732]
    latest_block_hash: Hash32
    next_withdrawal_index: WithdrawalIndex
    next_withdrawal_validator_index: ValidatorIndex
    historical_summaries: HistoricalSummaries
    deposit_requests_start_index: Uint64
    deposit_balance_to_consume: Gwei
    exit_balance_to_consume: Gwei
    earliest_exit_epoch: Epoch
    consolidation_balance_to_consume: Gwei
    earliest_consolidation_epoch: Epoch
    # [Modified in Gloas:EIP7688]
    pending_deposits: PendingDeposits
    # [Modified in Gloas:EIP7688]
    pending_partial_withdrawals: PendingPartialWithdrawals
    # [Modified in Gloas:EIP7688]
    pending_consolidations: PendingConsolidations
    proposer_lookahead: ProposerLookahead
    # [New in Gloas:EIP7732]
    builders: Builders
    # [New in Gloas:EIP7732]
    next_withdrawal_builder_index: BuilderIndex
    # [New in Gloas:EIP7732]
    execution_payload_availability: ExecutionPayloadAvailability
    # [New in Gloas:EIP7732]
    builder_pending_payments: BuilderPendingPayments
    # [New in Gloas:EIP7732]
    builder_pending_withdrawals: BuilderPendingWithdrawals
    # [New in Gloas:EIP7732]
    latest_execution_payload_bid: ExecutionPayloadBid
    # [New in Gloas:EIP7732]
    payload_expected_withdrawals: Withdrawals
    # [New in Gloas:EIP7732]
    ptc_window: PayloadTimelinessCommitteeWindow
```

#### `ExecutionPayload`

```python
# [Modified in Gloas:EIP7688]
class ExecutionPayload(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=19)

    parent_hash: Hash32
    fee_recipient: ExecutionAddress
    state_root: Bytes32
    receipts_root: Bytes32
    logs_bloom: LogsBloom
    prev_randao: Bytes32
    block_number: Uint64
    gas_limit: Uint64
    gas_used: Uint64
    timestamp: Uint64
    extra_data: ExtraData
    base_fee_per_gas: Uint256
    block_hash: Hash32
    # [Modified in Gloas:EIP7688]
    transactions: Transactions
    # [Modified in Gloas:EIP7688]
    withdrawals: Withdrawals
    blob_gas_used: Uint64
    excess_blob_gas: Uint64
    # [New in Gloas:EIP7928]
    block_access_list: BlockAccessList
    # [New in Gloas:EIP7843]
    slot_number: Uint64
```

#### `ExecutionRequests`

```python
# [Modified in Gloas:EIP7688]
class ExecutionRequests(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=5)

    deposits: DepositRequests
    withdrawals: WithdrawalRequests
    consolidations: ConsolidationRequests
    # [New in Gloas:EIP8282]
    builder_deposits: BuilderDepositRequests
    # [New in Gloas:EIP8282]
    builder_exits: BuilderExitRequests
```

#### `NewPayloadRequest`

```python
# [Modified in Gloas:EIP7688]
class NewPayloadRequest(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=4)

    execution_payload: ExecutionPayload
    versioned_hashes: VersionedHashes
    parent_beacon_block_root: Root
    execution_requests: ExecutionRequests
```

## Dataclasses

*(Các dataclass phụ trợ dùng trong spec — không phải SSZ container, không được serialize.)*

### Modified dataclasses

#### `ExpectedWithdrawals`

```python
@dataclass
class ExpectedWithdrawals:
    withdrawals: Sequence[Withdrawal]
    # [New in Gloas:EIP7732]
    processed_builder_withdrawals_count: Uint64
    processed_partial_withdrawals_count: Uint64
    # [New in Gloas:EIP7732]
    processed_builders_sweep_count: Uint64
    processed_sweep_withdrawals_count: Uint64
```

## Helpers

### Predicates

#### Modified `is_valid_indexed_attestation`

```python
def is_valid_indexed_attestation(
    state: BeaconState, indexed_attestation: IndexedAttestation
) -> bool:
    """
    Check if ``indexed_attestation`` is not empty, has sorted and unique indices and has a valid aggregate signature.
    """
    # Verify indices are sorted and unique
    indices = indexed_attestation.attesting_indices
    if (
        len(indices) == 0
        # [New in Gloas:EIP7688]
        or len(indices) > MAX_VALIDATORS_PER_COMMITTEE * MAX_COMMITTEES_PER_SLOT
        or list(indices) != sorted(set(indices))
    ):
        return False
    # Verify aggregate signature
    pubkeys = [state.validators[index].pubkey for index in indices]
    domain = get_domain(state, DOMAIN_BEACON_ATTESTER, indexed_attestation.data.target.epoch)
    signing_root = compute_signing_root(indexed_attestation.data, domain)
    return bls.FastAggregateVerify(pubkeys, signing_root, indexed_attestation.signature)
```

#### New `is_builder_index`

> 💡 Ghi chú: Builder index và validator index dùng chung không gian số
> `ValidatorIndex`; builder được đánh dấu bằng bit cờ `BUILDER_INDEX_FLAG`. Hàm này
> chỉ kiểm tra bit cờ đó có được bật hay không.

```python
def is_builder_index(validator_index: ValidatorIndex) -> bool:
    return (validator_index & BUILDER_INDEX_FLAG) != 0
```

#### New `is_active_builder`

```python
def is_active_builder(state: BeaconState, builder_index: BuilderIndex) -> bool:
    """
    Check if the builder at ``builder_index`` is active for the given ``state``.
    """
    builder = state.builders[builder_index]
    return (
        # Placement in builder list is finalized
        builder.deposit_epoch < state.finalized_checkpoint.epoch
        # Has not initiated exit
        and builder.withdrawable_epoch == FAR_FUTURE_EPOCH
    )
```

#### New `is_builder_withdrawal_credential`

```python
def is_builder_withdrawal_credential(withdrawal_credentials: Bytes32) -> bool:
    return withdrawal_credentials[:1] == BUILDER_WITHDRAWAL_PREFIX
```

#### New `is_attestation_same_slot`

> 💡 Ghi chú: Attestation được coi là "same slot" khi `beacon_block_root` của nó
> chính là block được đề xuất tại đúng `data.slot` (block root tại slot đó khác
> block root ở slot trước, tức slot không bị bỏ trống). Slot 0 luôn được coi là
> same slot.

```python
def is_attestation_same_slot(state: BeaconState, data: AttestationData) -> bool:
    """
    Check if the attestation is for the block proposed at the attestation slot.
    """
    if data.slot == 0:
        return True

    blockroot = data.beacon_block_root
    slot_blockroot = get_block_root_at_slot(state, data.slot)
    prev_blockroot = get_block_root_at_slot(state, data.slot - 1)

    return blockroot == slot_blockroot and blockroot != prev_blockroot
```

#### New `is_valid_indexed_payload_attestation`

```python
def is_valid_indexed_payload_attestation(
    state: BeaconState, attestation: IndexedPayloadAttestation
) -> bool:
    """
    Check if ``attestation`` is non-empty, has sorted indices, and has
    a valid aggregate signature.
    """
    # Verify indices are non-empty and sorted
    indices = attestation.attesting_indices
    if len(indices) == 0 or list(indices) != sorted(indices):
        return False

    # Verify aggregate signature
    pubkeys = [state.validators[index].pubkey for index in indices]
    domain = get_domain(state, DOMAIN_PTC_ATTESTER, compute_epoch_at_slot(attestation.data.slot))
    signing_root = compute_signing_root(attestation.data, domain)
    return bls.FastAggregateVerify(pubkeys, signing_root, attestation.signature)
```

#### New `is_pending_validator`

*Lưu ý*: Hàm này kiểm tra lại chữ ký (signature) của deposit một cách "ngây thơ"
ở mỗi lần gọi. Các implementation SHOULD cache kết quả xác minh để tránh lặp lại
công việc tốn kém này.

> 💡 Ghi chú: Hàm trả về `True` nếu trong hàng đợi `pending_deposits` có ít nhất
> một deposit cho `pubkey` này với chữ ký hợp lệ — tức là pubkey đó đang "chờ" trở
> thành validator. Deposit có chữ ký sai bị bỏ qua.

```python
def is_pending_validator(pending_deposits: Sequence[PendingDeposit], pubkey: BLSPubkey) -> bool:
    """
    Check if a pending deposit with a valid signature is in the queue for the given pubkey.
    """
    for pending_deposit in pending_deposits:
        if pending_deposit.pubkey != pubkey:
            continue
        if is_valid_deposit_signature(
            pending_deposit.pubkey,
            pending_deposit.withdrawal_credentials,
            pending_deposit.amount,
            pending_deposit.signature,
        ):
            return True
    return False
```

### Misc

#### New `convert_builder_index_to_validator_index`

```python
def convert_builder_index_to_validator_index(builder_index: BuilderIndex) -> ValidatorIndex:
    return ValidatorIndex(builder_index | BUILDER_INDEX_FLAG)
```

#### New `convert_validator_index_to_builder_index`

```python
def convert_validator_index_to_builder_index(validator_index: ValidatorIndex) -> BuilderIndex:
    return BuilderIndex(validator_index & ~BUILDER_INDEX_FLAG)
```

#### New `get_scheduled_gas_limit`

```python
def get_scheduled_gas_limit(epoch: Epoch) -> Uint64 | None:
    """
    Return the scheduled gas limit at a given epoch, if any.
    """
    for entry in sorted(GAS_LIMIT_SCHEDULE, key=lambda e: e["EPOCH"], reverse=True):
        if epoch >= entry["EPOCH"]:
            return entry["GAS_LIMIT"]
    return None
```

#### New `get_pending_balance_to_withdraw_for_builder`

```python
def get_pending_balance_to_withdraw_for_builder(
    state: BeaconState, builder_index: BuilderIndex
) -> Gwei:
    balance = Gwei(0)
    for withdrawal in state.builder_pending_withdrawals:
        if withdrawal.builder_index == builder_index:
            balance += withdrawal.amount
    for payment in state.builder_pending_payments:
        if payment.withdrawal.builder_index == builder_index:
            balance += payment.withdrawal.amount
    return balance
```

#### New `can_builder_cover_bid`

> 💡 Ghi chú: Builder chỉ có thể chi trả một bid nếu, sau khi trừ đi
> `MIN_DEPOSIT_AMOUNT` cùng tổng các khoản withdrawal/payment đang chờ của chính
> builder đó, phần balance còn lại vẫn ≥ `bid_amount`.

```python
def can_builder_cover_bid(
    state: BeaconState, builder_index: BuilderIndex, bid_amount: Gwei
) -> bool:
    builder_balance = state.builders[builder_index].balance
    pending_withdrawals_amount = get_pending_balance_to_withdraw_for_builder(state, builder_index)
    min_balance = MIN_DEPOSIT_AMOUNT + pending_withdrawals_amount
    if builder_balance < min_balance:
        return False
    return builder_balance - min_balance >= bid_amount
```

#### New `compute_balance_weighted_selection`

> 💡 Ghi chú: Đây là helper chung cho việc lấy mẫu theo trọng số effective balance
> (dùng cho proposer, sync committee và PTC). Mỗi ứng viên được chấp nhận với xác
> suất tỉ lệ với `effective_balance / MAX_EFFECTIVE_BALANCE_ELECTRA`, sử dụng 2 byte
> ngẫu nhiên (lấy từ `sha256(seed + i // 16)`) cho mỗi lần thử. Kết quả có thể chứa
> các index trùng lặp.

```python
def compute_balance_weighted_selection(
    state: BeaconState,
    indices: Sequence[ValidatorIndex],
    seed: Bytes32,
    size: Uint64,
    shuffle_indices: bool,
) -> Sequence[ValidatorIndex]:
    """
    Return ``size`` indices sampled by effective balance, using ``indices``
    as candidates. If ``shuffle_indices`` is ``True``, candidate indices
    are themselves sampled from ``indices`` by shuffling it, otherwise
    ``indices`` is traversed in order. The returned list can contain duplicates.
    """
    MAX_RANDOM_VALUE = 2**16 - 1
    total = Uint64(len(indices))
    assert total > 0
    effective_balances = [state.validators[index].effective_balance for index in indices]
    selected: list[ValidatorIndex] = []
    i = Uint64(0)
    while len(selected) < size:
        offset = i % 16 * 2
        if offset == 0:
            random_bytes = sha256(seed + uint_to_bytes(i // 16))
        next_index = i % total
        if shuffle_indices:
            next_index = compute_shuffled_index(next_index, total, seed)
        weight = effective_balances[next_index] * MAX_RANDOM_VALUE
        random_value = bytes_to_uint64(random_bytes[offset : offset + 2])
        threshold = MAX_EFFECTIVE_BALANCE_ELECTRA * random_value
        if weight >= threshold:
            selected.append(indices[next_index])
        i += 1
    return selected
```

#### Modified `compute_proposer_indices`

*Lưu ý*: `compute_proposer_indices` được sửa đổi để dùng
`compute_balance_weighted_selection` làm helper cho quá trình lấy mẫu có trọng số
theo balance.

```python
def compute_proposer_indices(
    state: BeaconState, epoch: Epoch, seed: Bytes32, indices: Sequence[ValidatorIndex]
) -> ProposerIndices:
    """
    Return the proposer indices for the given ``epoch``.
    """
    start_slot = compute_start_slot_at_epoch(epoch)
    seeds = [sha256(seed + uint_to_bytes(start_slot + index)) for index in range(SLOTS_PER_EPOCH)]
    # [Modified in Gloas:EIP7732]
    return ProposerIndices(
        data=[
            compute_balance_weighted_selection(
                state,
                indices,
                seed,
                size=Uint64(1),
                shuffle_indices=True,
            )[0]
            for seed in seeds
        ]
    )
```

#### New `compute_ptc`

> 💡 Ghi chú: PTC (payload timeliness committee — ủy ban xác nhận payload đến đúng
> hạn) của một slot được chọn từ tập hợp tất cả các beacon committee của slot đó
> (nối theo thứ tự), lấy mẫu theo effective balance mà không xáo trộn, với kích
> thước `PTC_SIZE`.

```python
def compute_ptc(state: BeaconState, slot: Slot) -> PayloadTimelinessCommittee:
    """
    Get the payload timeliness committee, with possible duplicates, for the given ``slot``.
    """
    epoch = compute_epoch_at_slot(slot)
    seed = sha256(get_seed(state, epoch, DOMAIN_PTC_ATTESTER) + uint_to_bytes(slot))
    indices: list[ValidatorIndex] = []
    # Concatenate all committees for this slot in order
    committees_per_slot = get_committee_count_per_slot(state, epoch)
    for i in range(committees_per_slot):
        committee = get_beacon_committee(state, slot, CommitteeIndex(i))
        indices.extend(committee)
    return PayloadTimelinessCommittee(
        data=compute_balance_weighted_selection(
            state, indices, seed, size=PTC_SIZE, shuffle_indices=False
        )
    )
```

### Beacon state accessors

#### Modified `get_beacon_proposer_indices`

*Lưu ý*: `get_beacon_proposer_indices` được sửa đổi để loại các validator đã bị
slash khỏi tập ứng viên trước khi gọi `compute_proposer_indices`, nhờ đó các
proposer index mới được tính chỉ gồm những validator đang active và chưa bị slash.

```python
def get_beacon_proposer_indices(state: BeaconState, epoch: Epoch) -> ProposerIndices:
    """
    Return the proposer indices for the given ``epoch``.
    """
    # [Modified in Gloas:EIP8045]
    indices = [
        index
        for index in get_active_validator_indices(state, epoch)
        if not state.validators[index].slashed
    ]
    seed = get_seed(state, epoch, DOMAIN_BEACON_PROPOSER)
    return compute_proposer_indices(state, epoch, seed, indices)
```

#### Modified `get_next_sync_committee_indices`

*Lưu ý*: `get_next_sync_committee_indices` được sửa đổi để dùng
`compute_balance_weighted_selection` làm helper cho quá trình lấy mẫu có trọng số
theo balance.

```python
def get_next_sync_committee_indices(state: BeaconState) -> Sequence[ValidatorIndex]:
    """
    Return the sync committee indices, with possible duplicates, for the next sync committee.
    """
    epoch = get_current_epoch(state) + 1
    seed = get_seed(state, epoch, DOMAIN_SYNC_COMMITTEE)
    indices = get_active_validator_indices(state, epoch)
    return compute_balance_weighted_selection(
        state, indices, seed, size=SYNC_COMMITTEE_SIZE, shuffle_indices=True
    )
```

#### Modified `get_attestation_participation_flag_indices`

*Lưu ý*: Hàm `get_attestation_participation_flag_indices` được sửa đổi để thêm
một ràng buộc mới về khớp payload vào điều kiện `is_matching_head`. Tham số mới
`parent_slot` là slot của block cha (parent block) của block đang được xử lý. Vì
cờ timely head đòi hỏi đồng thời inclusion delay tối thiểu và head root khớp với
block root tại slot của attestation, nên một attestation chỉ có thể nhận cờ này
nếu nó attest cho chính block cha. Do đó, trạng thái payload availability của
block được attest được tra cứu tại `parent_slot`, kể cả khi `data.slot` là một
slot bị bỏ trống (skipped slot).

> 💡 Ghi chú: Trong Gloas, `data.index` của attestation không còn là committee
> index mà được dùng để báo hiệu payload: với attestation same-slot thì
> `data.index` phải bằng 0; ngược lại, `data.index` phải khớp với bit
> `execution_payload_availability` (payload có/không có mặt) thì mới được coi là
> khớp head.

```python
def get_attestation_participation_flag_indices(
    state: BeaconState,
    data: AttestationData,
    inclusion_delay: Uint64,
    # [New in Gloas:EIP7732]
    parent_slot: Slot,
) -> Sequence[int]:
    """
    Return the flag indices that are satisfied by an attestation.
    """
    # Matching source
    if data.target.epoch == get_current_epoch(state):
        justified_checkpoint = state.current_justified_checkpoint
    else:
        justified_checkpoint = state.previous_justified_checkpoint
    is_matching_source = data.source == justified_checkpoint

    # Matching target
    target_root = get_block_root(state, data.target.epoch)
    target_root_matches = data.target.root == target_root
    is_matching_target = is_matching_source and target_root_matches

    # [New in Gloas:EIP7732]
    if is_attestation_same_slot(state, data):
        assert data.index == 0
        payload_matches = True
    else:
        slot_index = parent_slot % SLOTS_PER_HISTORICAL_ROOT
        payload_index = state.execution_payload_availability[slot_index]
        payload_matches = Uint64(data.index) == Uint64(payload_index)

    # Matching head
    head_root = get_block_root_at_slot(state, data.slot)
    head_root_matches = data.beacon_block_root == head_root
    # [Modified in Gloas:EIP7732]
    is_matching_head = is_matching_target and head_root_matches and payload_matches

    assert is_matching_source

    participation_flag_indices = []
    if is_matching_source and inclusion_delay <= integer_squareroot(SLOTS_PER_EPOCH):
        participation_flag_indices.append(TIMELY_SOURCE_FLAG_INDEX)
    if is_matching_target:
        participation_flag_indices.append(TIMELY_TARGET_FLAG_INDEX)
    if is_matching_head and inclusion_delay == MIN_ATTESTATION_INCLUSION_DELAY:
        participation_flag_indices.append(TIMELY_HEAD_FLAG_INDEX)

    return participation_flag_indices
```

#### New `get_ptc`

> 💡 Ghi chú: PTC được tính trước và cache trong `state.ptc_window`, gồm các slot
> của epoch trước, epoch hiện tại và tối đa `MIN_SEED_LOOKAHEAD` epoch tiếp theo.
> Hàm này chỉ tra cứu cửa sổ đó.

```python
def get_ptc(state: BeaconState, slot: Slot) -> PayloadTimelinessCommittee:
    """
    Get the payload timeliness committee for the given ``slot``.
    """
    epoch = compute_epoch_at_slot(slot)
    assert epoch >= GLOAS_FORK_EPOCH
    state_epoch = get_current_epoch(state)
    if epoch < state_epoch:
        assert epoch + 1 == state_epoch
        return state.ptc_window[slot % SLOTS_PER_EPOCH]
    assert epoch <= state_epoch + MIN_SEED_LOOKAHEAD
    offset = Uint64(epoch - state_epoch + 1) * SLOTS_PER_EPOCH
    return state.ptc_window[offset + slot % SLOTS_PER_EPOCH]
```

#### New `get_indexed_payload_attestation`

```python
def get_indexed_payload_attestation(
    state: BeaconState, payload_attestation: PayloadAttestation
) -> IndexedPayloadAttestation:
    """
    Return the indexed payload attestation corresponding to ``payload_attestation``.
    """
    slot = payload_attestation.data.slot
    ptc = get_ptc(state, slot)
    bits = payload_attestation.aggregation_bits
    attesting_indices = [
        validator_index for index, validator_index in enumerate(ptc) if bits[index]
    ]

    return IndexedPayloadAttestation(
        attesting_indices=PayloadTimelinessCommitteeIndices(data=sorted(attesting_indices)),
        data=payload_attestation.data,
        signature=payload_attestation.signature,
    )
```

#### New `get_builder_payment_quorum_threshold`

> 💡 Ghi chú: Ngưỡng quorum = (tổng active balance / `SLOTS_PER_EPOCH`) ×
> `BUILDER_PAYMENT_THRESHOLD_NUMERATOR` / `BUILDER_PAYMENT_THRESHOLD_DENOMINATOR`,
> tức một tỉ lệ của lượng stake trung bình attest trong một slot.

```python
def get_builder_payment_quorum_threshold(state: BeaconState) -> Gwei:
    """
    Calculate the quorum threshold for builder payments.
    """
    per_slot_balance = get_total_active_balance(state) // Uint64(SLOTS_PER_EPOCH)
    quorum = per_slot_balance * BUILDER_PAYMENT_THRESHOLD_NUMERATOR
    return quorum // BUILDER_PAYMENT_THRESHOLD_DENOMINATOR
```

#### New `get_activation_churn_limit`

```python
def get_activation_churn_limit(state: BeaconState) -> Gwei:
    """
    Per-epoch churn limit for activations, rounded to
    ``EFFECTIVE_BALANCE_INCREMENT``.
    """
    churn = max(
        MIN_PER_EPOCH_CHURN_LIMIT_ELECTRA,
        get_total_active_balance(state) // CHURN_LIMIT_QUOTIENT_GLOAS,
    )
    churn = churn - churn % EFFECTIVE_BALANCE_INCREMENT
    return min(MAX_PER_EPOCH_ACTIVATION_CHURN_LIMIT_GLOAS, churn)
```

#### New `get_exit_churn_limit`

```python
def get_exit_churn_limit(state: BeaconState) -> Gwei:
    """
    Per-epoch churn limit for exits, rounded to
    ``EFFECTIVE_BALANCE_INCREMENT``.
    """
    churn = max(
        MIN_PER_EPOCH_CHURN_LIMIT_ELECTRA,
        get_total_active_balance(state) // CHURN_LIMIT_QUOTIENT_GLOAS,
    )
    return churn - churn % EFFECTIVE_BALANCE_INCREMENT
```

#### Modified `get_consolidation_churn_limit`

*Lưu ý*: Consolidation churn giờ được tính độc lập từ tổng active balance thông
qua `CONSOLIDATION_CHURN_LIMIT_QUOTIENT` (không còn phụ thuộc vào churn của
activation/exit như trước).

```python
def get_consolidation_churn_limit(state: BeaconState) -> Gwei:
    """
    Per-epoch churn limit reserved for consolidations (EIP-7521).
    Derived from total active balance and rounded to
    ``EFFECTIVE_BALANCE_INCREMENT``.
    """
    churn = get_total_active_balance(state) // CONSOLIDATION_CHURN_LIMIT_QUOTIENT
    return churn - churn % EFFECTIVE_BALANCE_INCREMENT
```

#### Modified `compute_exit_epoch_and_update_churn`

*Lưu ý*: Việc xử lý exit giờ dùng exit churn không bị giới hạn trần (uncapped),
trong khi việc xử lý deposit vẫn bị giới hạn bởi `get_activation_churn_limit`.

```python
def compute_exit_epoch_and_update_churn(state: BeaconState, exit_balance: Gwei) -> Epoch:
    earliest_exit_epoch = max(
        state.earliest_exit_epoch, compute_activation_exit_epoch(get_current_epoch(state))
    )
    # [Modified in Gloas:EIP8061]
    per_epoch_churn = get_exit_churn_limit(state)
    # New epoch for exits.
    if state.earliest_exit_epoch < earliest_exit_epoch:
        exit_balance_to_consume = per_epoch_churn
    else:
        exit_balance_to_consume = state.exit_balance_to_consume

    # Exit doesn't fit in the current earliest epoch.
    if exit_balance > exit_balance_to_consume:
        balance_to_process = exit_balance - exit_balance_to_consume
        additional_epochs = (balance_to_process - 1) // per_epoch_churn + 1
        earliest_exit_epoch += Epoch(additional_epochs)
        exit_balance_to_consume += additional_epochs * per_epoch_churn

    # Consume the balance and update state variables.
    state.exit_balance_to_consume = exit_balance_to_consume - exit_balance
    state.earliest_exit_epoch = earliest_exit_epoch

    return state.earliest_exit_epoch
```

### Beacon state mutators

#### New `initiate_builder_exit`

```python
def initiate_builder_exit(state: BeaconState, builder_index: BuilderIndex) -> None:
    """
    Initiate the exit of the builder with index ``index``.
    """
    # Set builder exit epoch
    builder = state.builders[builder_index]
    builder.withdrawable_epoch = get_current_epoch(state) + MIN_BUILDER_WITHDRAWABILITY_DELAY
```

#### New `settle_builder_payment`

> 💡 Ghi chú: Chuyển khoản payment đang chờ tại `payment_index` sang hàng đợi
> `builder_pending_withdrawals` (nếu số tiền > 0), rồi xóa trống vị trí đó.

```python
def settle_builder_payment(state: BeaconState, payment_index: Uint64) -> None:
    assert payment_index < len(state.builder_pending_payments)
    payment = state.builder_pending_payments[payment_index]
    if payment.withdrawal.amount > 0:
        state.builder_pending_withdrawals.append(payment.withdrawal)
    state.builder_pending_payments[payment_index] = BuilderPendingPayment.empty()
```

#### Modified `slash_validator`

```python
def slash_validator(
    state: BeaconState,
    slashed_index: ValidatorIndex,
    whistleblower_index: ValidatorIndex | None = None,
) -> None:
    """
    Slash the validator with index ``slashed_index``.
    """
    epoch = get_current_epoch(state)
    initiate_validator_exit(state, slashed_index)
    validator = state.validators[slashed_index]
    validator.slashed = Boolean(True)
    validator.withdrawable_epoch = max(
        validator.withdrawable_epoch, epoch + EPOCHS_PER_SLASHINGS_VECTOR
    )
    state.slashings[epoch % EPOCHS_PER_SLASHINGS_VECTOR] += validator.effective_balance
    slashing_penalty = validator.effective_balance // MIN_SLASHING_PENALTY_QUOTIENT_ELECTRA
    decrease_balance(state, slashed_index, slashing_penalty)

    # Apply proposer and whistleblower rewards
    proposer_index = get_beacon_proposer_index(state)
    if whistleblower_index is None:
        whistleblower_index = proposer_index
    whistleblower_reward = validator.effective_balance // WHISTLEBLOWER_REWARD_QUOTIENT_ELECTRA
    proposer_reward = whistleblower_reward * PROPOSER_WEIGHT // WEIGHT_DENOMINATOR
    increase_balance(state, proposer_index, proposer_reward)
    increase_balance(state, whistleblower_index, whistleblower_reward - proposer_reward)

    # [New in Gloas:EIP7732]
    # Remove pending builder payments for blocks proposed by the slashed validator
    for payment_index, payment in enumerate(state.builder_pending_payments):
        if payment.proposer_index == slashed_index:
            state.builder_pending_payments[payment_index] = BuilderPendingPayment.empty()
```

## Beacon chain state transition function

State transition được thay đổi về căn bản trong Gloas. Toàn bộ state transition
được tách thành hai phần: trước tiên import một signed block, sau đó import một
execution payload.

Post-state tương ứng với pre-state `state` và signed beacon block `signed_block`
được định nghĩa là `state_transition(state, signed_block)`. Các state transition
gây ra exception không được xử lý (ví dụ `assert` thất bại hoặc truy cập list
ngoài phạm vi) được coi là không hợp lệ. Các state transition gây ra overflow hoặc
underflow `Uint64` cũng được coi là không hợp lệ.

Tính hợp lệ của một signed execution payload envelope `signed_envelope` đối với
pre-state `state` được kiểm tra bằng
`verify_execution_payload_envelope(state, signed_envelope, execution_engine)`.
Việc xử lý payload (áp dụng các thay đổi của payload vào state) được hoãn lại đến
beacon block kế tiếp thông qua `process_parent_execution_payload`. Các payload gây
ra exception không được xử lý (ví dụ `assert` thất bại hoặc truy cập list ngoài
phạm vi) được coi là không hợp lệ. Các payload gây ra overflow hoặc underflow
`Uint64` cũng được coi là không hợp lệ.

> 💡 Ghi chú: Nói cách khác, beacon block và execution payload giờ là hai đối
> tượng tách rời (ePBS — EIP-7732). Block được xử lý ngay qua `state_transition`;
> payload chỉ được xác minh khi nhận, còn tác động của nó lên beacon state được
> áp dụng khi xử lý block con tiếp theo.

### Modified `process_slot`

```python
def process_slot(state: BeaconState) -> None:
    slot_index = state.slot % SLOTS_PER_HISTORICAL_ROOT
    # Cache state root
    previous_state_root = hash_tree_root(state)
    state.state_roots[slot_index] = previous_state_root
    # Cache latest block header state root
    if state.latest_block_header.state_root == Bytes32():
        state.latest_block_header.state_root = previous_state_root
    # Cache block root
    previous_block_root = hash_tree_root(state.latest_block_header)
    state.block_roots[slot_index] = previous_block_root
    # [New in Gloas:EIP7732]
    # Unset the next payload availability
    next_slot_index = (state.slot + 1) % SLOTS_PER_HISTORICAL_ROOT
    state.execution_payload_availability[next_slot_index] = Boolean(False)
```

### Epoch processing

#### Modified `process_epoch`

*Lưu ý*: Hàm `process_epoch` được sửa đổi trong Gloas để gọi thêm các helper mới
`process_builder_pending_payments` và `process_ptc_window`.

```python
def process_epoch(state: BeaconState) -> None:
    process_justification_and_finalization(state)
    process_inactivity_updates(state)
    process_rewards_and_penalties(state)
    process_registry_updates(state)
    process_slashings(state)
    process_eth1_data_reset(state)
    # [Modified in Gloas:EIP8061]
    process_pending_deposits(state)
    process_pending_consolidations(state)
    # [New in Gloas:EIP7732]
    process_builder_pending_payments(state)
    process_effective_balance_updates(state)
    process_slashings_reset(state)
    process_randao_mixes_reset(state)
    process_historical_summaries_update(state)
    process_participation_flag_updates(state)
    process_sync_committee_updates(state)
    process_proposer_lookahead(state)
    # [New in Gloas:EIP7732]
    process_ptc_window(state)
```

#### Modified `process_pending_deposits`

```python
def process_pending_deposits(state: BeaconState) -> None:
    next_epoch = get_current_epoch(state) + 1
    # [Modified in Gloas:EIP8061]
    # Deposits still consume the activation-only churn budget in Gloas.
    available_for_processing = state.deposit_balance_to_consume + get_activation_churn_limit(state)
    processed_amount = 0
    next_deposit_index = 0
    deposits_to_postpone = []
    is_churn_limit_reached = False
    finalized_slot = compute_start_slot_at_epoch(state.finalized_checkpoint.epoch)

    for deposit in state.pending_deposits:
        # Check if deposit has been finalized, otherwise, stop processing.
        if deposit.slot > finalized_slot:
            break

        # Check if number of processed deposits has not reached the limit, otherwise, stop processing.
        if next_deposit_index >= MAX_PENDING_DEPOSITS_PER_EPOCH:
            break

        # Read validator state
        is_validator_exited = False
        is_validator_withdrawn = False
        validator_pubkeys = [validator.pubkey for validator in state.validators]
        if deposit.pubkey in validator_pubkeys:
            validator = state.validators[ValidatorIndex(validator_pubkeys.index(deposit.pubkey))]
            is_validator_exited = validator.exit_epoch < FAR_FUTURE_EPOCH
            is_validator_withdrawn = validator.withdrawable_epoch < next_epoch

        if is_validator_withdrawn:
            # Deposited balance will never become active. Increase balance but do not consume churn
            apply_pending_deposit(state, deposit)
        elif is_validator_exited:
            # Validator is exiting, postpone the deposit until after withdrawable epoch
            deposits_to_postpone.append(deposit)
        else:
            # Check if deposit fits in the churn, otherwise, do no more deposit processing in this epoch.
            is_churn_limit_reached = processed_amount + deposit.amount > available_for_processing
            if is_churn_limit_reached:
                break

            # Consume churn and apply deposit.
            processed_amount += deposit.amount
            apply_pending_deposit(state, deposit)

        # Regardless of how the deposit was handled, we move on in the queue.
        next_deposit_index += 1

    state.pending_deposits = state.pending_deposits[next_deposit_index:] + deposits_to_postpone

    # Accumulate churn only if the churn limit has been hit.
    if is_churn_limit_reached:
        state.deposit_balance_to_consume = available_for_processing - processed_amount
    else:
        state.deposit_balance_to_consume = Gwei(0)
```

#### New `process_builder_pending_payments`

> 💡 Ghi chú: `builder_pending_payments` chứa 2 epoch payment. Ở cuối mỗi epoch,
> các payment của epoch cũ hơn (nửa đầu) có `weight` đạt quorum sẽ được chuyển
> thành withdrawal cho builder; sau đó nửa sau dịch lên nửa đầu và nửa sau được
> làm trống.

```python
def process_builder_pending_payments(state: BeaconState) -> None:
    """
    Processes the builder pending payments from the previous epoch.
    """
    quorum = get_builder_payment_quorum_threshold(state)
    for payment in state.builder_pending_payments[:SLOTS_PER_EPOCH]:
        if payment.weight >= quorum:
            state.builder_pending_withdrawals.append(payment.withdrawal)

    old_payments = state.builder_pending_payments[SLOTS_PER_EPOCH:]
    state.builder_pending_payments[:SLOTS_PER_EPOCH] = old_payments
    new_payments = [BuilderPendingPayment.empty() for _ in range(SLOTS_PER_EPOCH)]
    state.builder_pending_payments[SLOTS_PER_EPOCH:] = new_payments
```

#### New `process_ptc_window`

> 💡 Ghi chú: Dịch cửa sổ `ptc_window` lên một epoch và tính PTC cho epoch mới
> nhất (`current_epoch + MIN_SEED_LOOKAHEAD + 1`).

```python
def process_ptc_window(state: BeaconState) -> None:
    """
    Update the cached PTC window.
    """
    # Shift all epochs forward by one
    state.ptc_window[: len(state.ptc_window) - SLOTS_PER_EPOCH] = state.ptc_window[SLOTS_PER_EPOCH:]
    # Fill in the last epoch
    next_epoch = get_current_epoch(state) + MIN_SEED_LOOKAHEAD + 1
    start_slot = compute_start_slot_at_epoch(next_epoch)
    state.ptc_window[len(state.ptc_window) - SLOTS_PER_EPOCH :] = [
        compute_ptc(state, Slot(slot)) for slot in range(start_slot, start_slot + SLOTS_PER_EPOCH)
    ]
```

### Block processing

```python
def process_block(state: BeaconState, block: BeaconBlock) -> None:
    # [New in Gloas:EIP7732]
    parent_slot = state.latest_block_header.slot

    # [New in Gloas:EIP7732]
    process_parent_execution_payload(state, block)
    process_block_header(state, block)
    # [Modified in Gloas:EIP7732]
    process_withdrawals(state)
    # [Modified in Gloas:EIP7732]
    # Removed `process_execution_payload`
    # [New in Gloas:EIP7732]
    process_execution_payload_bid(state, block.body.signed_execution_payload_bid)
    process_randao(state, block.body)
    process_eth1_data(state, block.body)
    # [Modified in Gloas:EIP7732]
    process_operations(state, block.body, parent_slot)
    process_sync_aggregate(state, block.body.sync_aggregate)
```

#### Parent execution payload

##### New `apply_parent_execution_payload`

*Ghi chú*: Hàm này đưa khoản thanh toán cho builder vào hàng đợi, xử lý các
execution request của parent (block cha), cập nhật trạng thái payload
availability (payload đã được công bố hay chưa) và cập nhật latest block hash.
Hàm được gọi bởi `process_parent_execution_payload` trong quá trình block
processing, và bởi validator trong quá trình tạo block (block production) trước
khi tính toán các withdrawal.

> 💡 Ghi chú: Trong Gloas (ePBS), execution payload của một block không được xử lý
> ngay trong chính block đó mà được "áp dụng trễ" khi block con (child) được xử lý.
> Vì vậy các execution request của parent được thực thi tại slot của block con.

```python
def apply_parent_execution_payload(
    state: BeaconState,
    requests: ExecutionRequests,
) -> None:
    parent_bid = state.latest_execution_payload_bid
    parent_slot = state.latest_block_header.slot
    parent_epoch = compute_epoch_at_slot(parent_slot)

    assert len(requests.withdrawals) <= MAX_WITHDRAWAL_REQUESTS_PER_PAYLOAD
    assert len(requests.consolidations) <= MAX_CONSOLIDATION_REQUESTS_PER_PAYLOAD
    assert len(requests.builder_deposits) <= MAX_BUILDER_DEPOSIT_REQUESTS_PER_PAYLOAD
    assert len(requests.builder_exits) <= MAX_BUILDER_EXIT_REQUESTS_PER_PAYLOAD

    # Tất toán khoản thanh toán cho builder trước khi xử lý các request, để một
    # builder exit request bị từ chối khi khoản thanh toán vẫn đang pending
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
    # request được xử lý tại state.slot (slot của block con), không phải slot của parent.
    def for_ops(operations: Sequence[Any], fn: Callable[[BeaconState, Any], None]) -> None:
        for operation in operations:
            fn(state, operation)

    for_ops(requests.deposits, process_deposit_request)
    for_ops(requests.withdrawals, process_withdrawal_request)
    for_ops(requests.consolidations, process_consolidation_request)
    for_ops(requests.builder_deposits, process_builder_deposit_request)
    for_ops(requests.builder_exits, process_builder_exit_request)

    # Cập nhật payload availability của parent và latest block hash
    state.execution_payload_availability[parent_slot % SLOTS_PER_HISTORICAL_ROOT] = Boolean(True)
    state.latest_block_hash = parent_bid.block_hash
```

##### New `process_parent_execution_payload`

*Ghi chú*: Hàm này kiểm tra hợp lệ và xử lý execution payload của parent.
`process_parent_execution_payload` phải được gọi trước
`process_execution_payload_bid` (vì hàm sau sẽ ghi đè
`state.latest_execution_payload_bid`).

> 💡 Ghi chú: Hàm phân biệt hai trường hợp dựa trên `bid.parent_block_hash`: nếu
> bid của block hiện tại không xây trên block hash của parent bid thì parent được
> coi là EMPTY (payload không được công bố), khi đó không được có execution request
> nào; ngược lại parent là FULL và các request phải khớp với
> `execution_requests_root` mà builder đã cam kết trong bid.

```python
def process_parent_execution_payload(state: BeaconState, block: BeaconBlock) -> None:
    bid = block.body.signed_execution_payload_bid.message
    parent_bid = state.latest_execution_payload_bid
    requests = block.body.parent_execution_requests

    if bid.parent_block_hash != parent_bid.block_hash:
        # Parent là EMPTY -- không được có execution request nào
        assert requests == ExecutionRequests.empty()
        return

    # Parent là FULL -- kiểm tra cam kết trong bid và áp dụng payload
    assert hash_tree_root(requests) == parent_bid.execution_requests_root
    apply_parent_execution_payload(state, requests)
```

#### Withdrawals

##### New `get_builder_withdrawals`

```python
def get_builder_withdrawals(
    state: BeaconState,
    withdrawal_index: WithdrawalIndex,
    prior_withdrawals: Sequence[Withdrawal],
) -> tuple[Sequence[Withdrawal], WithdrawalIndex, Uint64]:
    withdrawals_limit = MAX_WITHDRAWALS_PER_PAYLOAD - 1
    assert len(prior_withdrawals) <= withdrawals_limit

    processed_count = Uint64(0)
    withdrawals: list[Withdrawal] = []
    for withdrawal in state.builder_pending_withdrawals:
        all_withdrawals = list(prior_withdrawals) + withdrawals
        has_reached_limit = len(all_withdrawals) >= withdrawals_limit
        if has_reached_limit:
            break

        builder_index = withdrawal.builder_index
        withdrawals.append(
            Withdrawal(
                index=withdrawal_index,
                validator_index=convert_builder_index_to_validator_index(builder_index),
                address=withdrawal.fee_recipient,
                amount=withdrawal.amount,
            )
        )
        withdrawal_index += 1
        processed_count += 1

    return withdrawals, withdrawal_index, processed_count
```

##### New `get_builder_balance_after_withdrawals`

```python
def get_builder_balance_after_withdrawals(
    state: BeaconState, builder_index: BuilderIndex, withdrawals: Sequence[Withdrawal]
) -> Gwei:
    validator_index = convert_builder_index_to_validator_index(builder_index)
    withdrawn = Gwei(
        sum(
            withdrawal.amount
            for withdrawal in withdrawals
            if withdrawal.validator_index == validator_index
        )
    )
    return saturating_sub(state.builders[builder_index].balance, withdrawn)
```

##### New `get_builders_sweep_withdrawals`

```python
def get_builders_sweep_withdrawals(
    state: BeaconState,
    withdrawal_index: WithdrawalIndex,
    prior_withdrawals: Sequence[Withdrawal],
) -> tuple[Sequence[Withdrawal], WithdrawalIndex, Uint64]:
    epoch = get_current_epoch(state)
    builders_limit = min(len(state.builders), MAX_BUILDERS_PER_WITHDRAWALS_SWEEP)
    withdrawals_limit = MAX_WITHDRAWALS_PER_PAYLOAD - 1
    assert len(prior_withdrawals) <= withdrawals_limit

    processed_count = Uint64(0)
    withdrawals: list[Withdrawal] = []
    builder_index = state.next_withdrawal_builder_index
    for _ in range(builders_limit):
        all_withdrawals = list(prior_withdrawals) + withdrawals
        has_reached_limit = len(all_withdrawals) >= withdrawals_limit
        if has_reached_limit:
            break

        builder = state.builders[builder_index]
        balance = get_builder_balance_after_withdrawals(state, builder_index, all_withdrawals)
        if builder.withdrawable_epoch <= epoch and balance > 0:
            withdrawals.append(
                Withdrawal(
                    index=withdrawal_index,
                    validator_index=convert_builder_index_to_validator_index(builder_index),
                    address=builder.execution_address,
                    amount=balance,
                )
            )
            withdrawal_index += 1

        builder_index = (builder_index + 1) % len(state.builders)
        processed_count += 1

    return withdrawals, withdrawal_index, processed_count
```

##### Modified `get_expected_withdrawals`

```python
def get_expected_withdrawals(state: BeaconState) -> ExpectedWithdrawals:
    withdrawal_index = state.next_withdrawal_index
    withdrawals: list[Withdrawal] = []

    # [New in Gloas:EIP7732]
    # Lấy các builder withdrawal
    builder_withdrawals, withdrawal_index, processed_builder_withdrawals_count = (
        get_builder_withdrawals(state, withdrawal_index, withdrawals)
    )
    withdrawals.extend(builder_withdrawals)

    # Lấy các partial withdrawal
    partial_withdrawals, withdrawal_index, processed_partial_withdrawals_count = (
        get_pending_partial_withdrawals(state, withdrawal_index, withdrawals)
    )
    withdrawals.extend(partial_withdrawals)

    # [New in Gloas:EIP7732]
    # Lấy các withdrawal từ builders sweep
    builders_sweep_withdrawals, withdrawal_index, processed_builders_sweep_count = (
        get_builders_sweep_withdrawals(state, withdrawal_index, withdrawals)
    )
    withdrawals.extend(builders_sweep_withdrawals)

    # Lấy các withdrawal từ validators sweep
    validators_sweep_withdrawals, withdrawal_index, processed_validators_sweep_count = (
        get_validators_sweep_withdrawals(state, withdrawal_index, withdrawals)
    )
    withdrawals.extend(validators_sweep_withdrawals)

    return ExpectedWithdrawals(
        withdrawals,
        # [New in Gloas:EIP7732]
        processed_builder_withdrawals_count,
        processed_partial_withdrawals_count,
        # [New in Gloas:EIP7732]
        processed_builders_sweep_count,
        processed_validators_sweep_count,
    )
```

##### Modified `apply_withdrawals`

```python
def apply_withdrawals(state: BeaconState, withdrawals: Sequence[Withdrawal]) -> None:
    for withdrawal in withdrawals:
        # [Modified in Gloas:EIP7732]
        if is_builder_index(withdrawal.validator_index):
            builder_index = convert_validator_index_to_builder_index(withdrawal.validator_index)
            state.builders[builder_index].balance = saturating_sub(
                state.builders[builder_index].balance, withdrawal.amount
            )
        else:
            decrease_balance(state, withdrawal.validator_index, withdrawal.amount)
```

##### New `update_payload_expected_withdrawals`

```python
def update_payload_expected_withdrawals(
    state: BeaconState, withdrawals: Sequence[Withdrawal]
) -> None:
    state.payload_expected_withdrawals = Withdrawals(data=withdrawals)
```

##### New `update_builder_pending_withdrawals`

```python
def update_builder_pending_withdrawals(
    state: BeaconState, processed_builder_withdrawals_count: Uint64
) -> None:
    state.builder_pending_withdrawals = state.builder_pending_withdrawals[
        processed_builder_withdrawals_count:
    ]
```

##### New `update_next_withdrawal_builder_index`

```python
def update_next_withdrawal_builder_index(
    state: BeaconState, processed_builders_sweep_count: Uint64
) -> None:
    if len(state.builders) > 0:
        # Cập nhật builder index kế tiếp để bắt đầu lượt withdrawal sweep sau
        next_index = state.next_withdrawal_builder_index + processed_builders_sweep_count
        next_builder_index = next_index % len(state.builders)
        state.next_withdrawal_builder_index = next_builder_index
```

##### Modified `process_withdrawals`

*Ghi chú*: Hàm này được sửa để chỉ nhận tham số `state`. Các withdrawal được xác
định một cách tất định (deterministic) từ beacon state; bất kỳ execution payload
nào có block tương ứng làm parent beacon block đều bắt buộc phải thực hiện đúng
các withdrawal này ở execution layer. `process_withdrawals` phải được gọi sau
`process_parent_execution_payload` (hàm cập nhật `state.latest_block_hash`) và
trước `process_execution_payload_bid`, vì hàm sau có ảnh hưởng đến balance của
các validator.

*Ghi chú*: Khác với deposit (được áp dụng tại slot của block con thông qua
`apply_parent_execution_payload`), việc trừ balance cho withdrawal được áp dụng
ngay lập tức qua `apply_withdrawals`. Nếu hoãn việc trừ sang slot của block con
thì sẽ phá vỡ bất biến về tổng cung (total supply invariant): các state
transition xảy ra giữa slot cam kết (commitment slot) và slot trừ tiền (ví dụ
`process_pending_consolidations` tại ranh giới epoch) có thể làm balance của
validator giảm xuống dưới số tiền withdrawal đã cam kết, khiến
`decrease_balance` bị chặn dưới (saturate) ở 0. Vì execution layer vẫn luôn
mint (phát hành) đủ toàn bộ số tiền đã cam kết, bất kỳ sự saturate nào ở phía CL
đều tạo ra lạm phát ròng về nguồn cung. Hệ quả là `state.balances` đã phản ánh
khoản trừ withdrawal trước khi execution payload tương ứng được xác nhận, tạo ra
sự bất đối xứng tạm thời so với state của EL tại `state.latest_block_hash`. Các
bên sử dụng off-chain cần sự nhất quán balance giữa CL/EL có thể khôi phục lại
balance trước khi trừ bằng cách cộng ngược lại `state.payload_expected_withdrawals`.

```python
def process_withdrawals(
    state: BeaconState,
    # [Modified in Gloas:EIP7732]
    # Removed `payload`
) -> None:
    # [New in Gloas:EIP7732]
    # Trả về sớm nếu parent block là empty
    if state.latest_block_hash != state.latest_execution_payload_bid.block_hash:
        return

    # Lấy các expected withdrawal
    expected = get_expected_withdrawals(state)

    # Áp dụng các expected withdrawal
    apply_withdrawals(state, expected.withdrawals)

    # Cập nhật các trường liên quan đến withdrawal trong state
    update_next_withdrawal_index(state, expected.withdrawals)
    # [New in Gloas:EIP7732]
    update_payload_expected_withdrawals(state, expected.withdrawals)
    # [New in Gloas:EIP7732]
    update_builder_pending_withdrawals(state, expected.processed_builder_withdrawals_count)
    update_pending_partial_withdrawals(state, expected.processed_partial_withdrawals_count)
    # [New in Gloas:EIP7732]
    update_next_withdrawal_builder_index(state, expected.processed_builders_sweep_count)
    update_next_withdrawal_validator_index(state, expected.withdrawals)
```

#### Execution payload

##### Removed `process_execution_payload`

`process_execution_payload` đã được thay thế bởi
`verify_execution_payload_envelope`, một hàm helper chỉ làm nhiệm vụ kiểm tra
(không thay đổi state) và được gọi từ `on_execution_payload_envelope`. Việc xử
lý payload được hoãn sang beacon block kế tiếp thông qua
`process_parent_execution_payload`.

##### New `verify_execution_payload_envelope_signature`

```python
def verify_execution_payload_envelope_signature(
    state: BeaconState, signed_envelope: SignedExecutionPayloadEnvelope
) -> bool:
    builder_index = signed_envelope.message.builder_index
    if builder_index == BUILDER_INDEX_SELF_BUILD:
        validator_index = state.latest_block_header.proposer_index
        pubkey = state.validators[validator_index].pubkey
    else:
        pubkey = state.builders[builder_index].pubkey

    signing_root = compute_signing_root(
        signed_envelope.message, get_domain(state, DOMAIN_BEACON_BUILDER)
    )
    return bls.Verify(pubkey, signing_root, signed_envelope.signature)
```

##### Modified `get_execution_requests_list`

```python
def get_execution_requests_list(execution_requests: ExecutionRequests) -> Sequence[bytes]:
    requests: Sequence[tuple[Bytes1, ProgressiveList]] = [
        (DEPOSIT_REQUEST_TYPE, execution_requests.deposits),
        (WITHDRAWAL_REQUEST_TYPE, execution_requests.withdrawals),
        (CONSOLIDATION_REQUEST_TYPE, execution_requests.consolidations),
        # [New in Gloas:EIP8282]
        (BUILDER_DEPOSIT_REQUEST_TYPE, execution_requests.builder_deposits),
        # [New in Gloas:EIP8282]
        (BUILDER_EXIT_REQUEST_TYPE, execution_requests.builder_exits),
    ]

    return [
        request_type + ssz_serialize(request_data)
        for request_type, request_data in requests
        if len(request_data) != 0
    ]
```

#### Execution payload bid

##### New `verify_execution_payload_bid_signature`

```python
def verify_execution_payload_bid_signature(
    state: BeaconState, signed_bid: SignedExecutionPayloadBid
) -> bool:
    builder = state.builders[signed_bid.message.builder_index]
    signing_root = compute_signing_root(
        signed_bid.message, get_domain(state, DOMAIN_BEACON_BUILDER)
    )
    return bls.Verify(builder.pubkey, signing_root, signed_bid.signature)
```

##### New `process_execution_payload_bid`

```python
def process_execution_payload_bid(
    state: BeaconState, signed_bid: SignedExecutionPayloadBid
) -> None:
    bid = signed_bid.message
    builder_index = bid.builder_index
    amount = bid.value

    # Với self-build, amount phải bằng 0 bất kể prefix của withdrawal credential
    if builder_index == BUILDER_INDEX_SELF_BUILD:
        assert amount == 0
        assert signed_bid.signature == bls.G2_POINT_AT_INFINITY
    else:
        # Kiểm tra builder đang active
        assert is_active_builder(state, builder_index)
        # Kiểm tra builder là payload builder
        assert state.builders[builder_index].version == PAYLOAD_BUILDER_VERSION
        # Kiểm tra builder có đủ tiền để chi trả cho bid
        assert can_builder_cover_bid(state, builder_index, amount)
        # Kiểm tra signature của bid hợp lệ
        assert verify_execution_payload_bid_signature(state, signed_bid)

    # Kiểm tra số commitment không vượt giới hạn
    assert (
        len(bid.blob_kzg_commitments)
        <= get_blob_parameters(get_current_epoch(state)).max_blobs_per_block
    )

    # Kiểm tra bid dành cho slot hiện tại
    assert bid.slot == state.slot
    assert state.slot > GENESIS_SLOT
    # Kiểm tra bid dành cho đúng parent block
    assert bid.parent_block_hash == state.latest_block_hash
    # Kiểm tra block hash của bid khác với parent block hash của nó
    assert bid.block_hash != bid.parent_block_hash
    assert bid.parent_block_root == get_block_root_at_slot(state, state.slot - 1)
    assert bid.prev_randao == get_randao_mix(state, get_current_epoch(state))

    # Ghi nhận pending payment nếu có khoản thanh toán
    if amount > 0:
        pending_payment = BuilderPendingPayment(
            weight=Gwei(0),
            withdrawal=BuilderPendingWithdrawal(
                fee_recipient=bid.fee_recipient,
                amount=amount,
                builder_index=builder_index,
            ),
            proposer_index=get_beacon_proposer_index(state),
        )
        state.builder_pending_payments[SLOTS_PER_EPOCH + bid.slot % SLOTS_PER_EPOCH] = (
            pending_payment
        )

    # Lưu lại (cache) execution payload bid đã ký
    state.latest_execution_payload_bid = bid
```

#### Operations

##### Modified `process_operations`

*Ghi chú*: `process_operations` được sửa để xử lý các PTC attestation (payload
attestation), truyền slot của parent block vào `process_attestation`, và bỏ các
lời gọi tới `process_deposit_request`, `process_withdrawal_request` và
`process_consolidation_request` (các request này giờ được xử lý trong
`apply_parent_execution_payload`).

```python
def process_operations(
    state: BeaconState,
    body: BeaconBlockBody,
    # [New in Gloas:EIP7732]
    parent_slot: Slot,
) -> None:
    assert len(body.deposits) == 0

    # [Modified in Gloas:EIP7732]
    def for_ops(operations: Sequence[Any], fn: Callable[..., None], *args: Any) -> None:
        for operation in operations:
            fn(state, operation, *args)

    # [New in Gloas:EIP7688]
    assert len(body.proposer_slashings) <= MAX_PROPOSER_SLASHINGS
    assert len(body.attester_slashings) <= MAX_ATTESTER_SLASHINGS_ELECTRA
    assert len(body.attestations) <= MAX_ATTESTATIONS_ELECTRA
    assert len(body.voluntary_exits) <= MAX_VOLUNTARY_EXITS
    assert len(body.bls_to_execution_changes) <= MAX_BLS_TO_EXECUTION_CHANGES
    assert len(body.payload_attestations) <= MAX_PAYLOAD_ATTESTATIONS

    # [Modified in Gloas:EIP7732]
    for_ops(body.proposer_slashings, process_proposer_slashing)
    for_ops(body.attester_slashings, process_attester_slashing)
    # [Modified in Gloas:EIP7732]
    for_ops(body.attestations, process_attestation, parent_slot)
    for_ops(body.voluntary_exits, process_voluntary_exit)
    for_ops(body.bls_to_execution_changes, process_bls_to_execution_change)
    # [Modified in Gloas:EIP7732]
    # Removed `process_deposit_request`
    # [Modified in Gloas:EIP7732]
    # Removed `process_withdrawal_request`
    # [Modified in Gloas:EIP7732]
    # Removed `process_consolidation_request`
    # [New in Gloas:EIP7732]
    for_ops(body.payload_attestations, process_payload_attestation)
```

##### Builder deposit requests

###### New `is_valid_builder_deposit_signature`

*Ghi chú*: Builder deposit được ký trên `DepositMessage` với domain
`DOMAIN_BUILDER_DEPOSIT`. Việc dùng một domain riêng đảm bảo rằng signature của
validator deposit và signature của builder deposit không thể bị dùng lại
(replay) đối với deposit contract còn lại.

```python
def is_valid_builder_deposit_signature(request: BuilderDepositRequest) -> bool:
    deposit_message = DepositMessage(
        pubkey=request.pubkey,
        withdrawal_credentials=request.withdrawal_credentials,
        amount=request.amount,
    )
    domain = compute_domain(DOMAIN_BUILDER_DEPOSIT)
    signing_root = compute_signing_root(deposit_message, domain)
    return bls.Verify(request.pubkey, signing_root, request.signature)
```

###### New `get_index_for_new_builder`

```python
def get_index_for_new_builder(state: BeaconState) -> BuilderIndex:
    for index, builder in enumerate(state.builders):
        if builder.withdrawable_epoch <= get_current_epoch(state) and builder.balance == 0:
            return BuilderIndex(index)
    return BuilderIndex(len(state.builders))
```

###### New `add_builder_to_registry`

```python
def add_builder_to_registry(
    state: BeaconState,
    pubkey: BLSPubkey,
    version: Uint8,
    execution_address: ExecutionAddress,
    amount: Gwei,
    slot: Slot,
) -> None:
    set_or_append_list(
        state.builders,
        get_index_for_new_builder(state),
        Builder(
            pubkey=pubkey,
            version=version,
            execution_address=execution_address,
            balance=amount,
            deposit_epoch=compute_epoch_at_slot(slot),
            withdrawable_epoch=FAR_FUTURE_EPOCH,
        ),
    )
```

###### New `process_builder_deposit_request`

*Ghi chú*: Builder index có thể được tái sử dụng. Khi một builder exit, index của
nó sau này có thể được gán lại cho một builder khác với public key mới. Một
deposit cho builder đã exit nhưng vẫn còn trong registry sẽ được builders sweep
rút (withdraw) về execution address của builder đó. Nếu index của builder đã bị
gán lại, deposit sẽ được xử lý như một lần đăng ký builder mới, và khi đó cần
signature hợp lệ. Builder đã exit không thể được kích hoạt lại, tuy nhiên public
key của một builder mới đăng ký có thể đã từng xuất hiện trong tập builder
trước đó. Các implementation có dùng cache cần tính đến hành vi này.

```python
def process_builder_deposit_request(state: BeaconState, request: BuilderDepositRequest) -> None:
    # Bỏ qua các deposit có prefix withdrawal credential không đúng
    if not is_builder_withdrawal_credential(request.withdrawal_credentials):
        return

    builder_pubkeys = [builder.pubkey for builder in state.builders]
    if request.pubkey not in builder_pubkeys:
        if is_valid_builder_deposit_signature(request):
            add_builder_to_registry(
                state,
                request.pubkey,
                PAYLOAD_BUILDER_VERSION,
                ExecutionAddress(request.withdrawal_credentials[12:]),
                request.amount,
                state.slot,
            )
    else:
        builder_index = BuilderIndex(builder_pubkeys.index(request.pubkey))
        builder = state.builders[builder_index]

        # Nếu đã exit và đã được sweep, đặt lại withdrawable epoch
        if builder.withdrawable_epoch != FAR_FUTURE_EPOCH and builder.balance == 0:
            epoch = get_current_epoch(state)
            builder.withdrawable_epoch = epoch + MIN_BUILDER_WITHDRAWABILITY_DELAY

        # Tăng balance thêm đúng số tiền deposit
        builder.balance += request.amount
```

##### Builder exit requests

###### New `process_builder_exit_request`

```python
def process_builder_exit_request(state: BeaconState, request: BuilderExitRequest) -> None:
    builder_pubkeys = [builder.pubkey for builder in state.builders]
    if request.pubkey not in builder_pubkeys:
        return

    builder_index = BuilderIndex(builder_pubkeys.index(request.pubkey))
    builder = state.builders[builder_index]

    if not is_active_builder(state, builder_index):
        return
    if builder.execution_address != request.source_address:
        return
    if get_pending_balance_to_withdraw_for_builder(state, builder_index) != 0:
        return

    initiate_builder_exit(state, builder_index)
```

##### Attestations

###### Modified `process_attestation`

*Ghi chú*: Hàm được sửa để theo dõi weight (tổng effective balance ủng hộ) cho
các khoản thanh toán builder đang chờ (pending builder payment), và dùng trường
`index` trong `AttestationData` để báo hiệu payload availability. Tham số mới
`parent_slot` là slot của parent block, là nơi tra cứu payload availability của
block được attest.

> 💡 Ghi chú: Từ Gloas, `data.index` không còn là committee index (committee được
> xác định qua `committee_bits`), mà chỉ nhận giá trị 0 hoặc 1 để attester cho
> biết họ thấy payload của block là vắng mặt hay có mặt. Một khoản pending payment
> chỉ được cộng weight khi attester lần đầu tham gia trong epoch, attest cùng slot
> với block và khoản thanh toán lớn hơn 0.

```python
def process_attestation(
    state: BeaconState,
    attestation: Attestation,
    # [New in Gloas:EIP7732]
    parent_slot: Slot,
) -> None:
    data = attestation.data
    assert data.target.epoch in (get_previous_epoch(state), get_current_epoch(state))
    assert data.target.epoch == compute_epoch_at_slot(data.slot)
    assert data.slot + MIN_ATTESTATION_INCLUSION_DELAY <= state.slot

    # [Modified in Gloas:EIP7732]
    assert data.index < 2
    committee_indices = get_committee_indices(attestation.committee_bits)
    committee_offset = 0
    for committee_index in committee_indices:
        assert committee_index < get_committee_count_per_slot(state, data.target.epoch)
        committee = get_beacon_committee(state, data.slot, committee_index)
        committee_attesters = {
            attester_index
            for index, attester_index in enumerate(committee)
            if attestation.aggregation_bits[committee_offset + index]
        }
        assert len(committee_attesters) > 0
        committee_offset += len(committee)

    # Độ dài bitfield khớp với tổng số người tham gia
    assert len(attestation.aggregation_bits) == committee_offset

    # Các chỉ số participation flag
    # [Modified in Gloas:EIP7732]
    participation_flag_indices = get_attestation_participation_flag_indices(
        state, data, state.slot - data.slot, parent_slot
    )

    # Kiểm tra signature
    assert is_valid_indexed_attestation(state, get_indexed_attestation(state, attestation))

    # [Modified in Gloas:EIP7732]
    if data.target.epoch == get_current_epoch(state):
        current_epoch_target = True
        epoch_participation = state.current_epoch_participation
        payment = state.builder_pending_payments[SLOTS_PER_EPOCH + data.slot % SLOTS_PER_EPOCH]
    else:
        current_epoch_target = False
        epoch_participation = state.previous_epoch_participation
        payment = state.builder_pending_payments[data.slot % SLOTS_PER_EPOCH]

    proposer_reward_numerator = 0
    for index in get_attesting_indices(state, attestation):
        # [New in Gloas:EIP7732]
        had_no_participation = epoch_participation[index] == 0b0000_0000
        will_set_new_flag = False

        for flag_index, weight in enumerate(PARTICIPATION_FLAG_WEIGHTS):
            if flag_index in participation_flag_indices and not has_flag(
                epoch_participation[index], flag_index
            ):
                epoch_participation[index] = add_flag(epoch_participation[index], flag_index)
                proposer_reward_numerator += get_base_reward(state, index) * weight
                # [New in Gloas:EIP7732]
                will_set_new_flag = True

        # [New in Gloas:EIP7732]
        if (
            will_set_new_flag
            and had_no_participation
            and is_attestation_same_slot(state, data)
            and payment.withdrawal.amount > 0
        ):
            payment.weight += state.validators[index].effective_balance

    # Thưởng cho proposer
    proposer_reward_denominator = (
        (WEIGHT_DENOMINATOR - PROPOSER_WEIGHT) * WEIGHT_DENOMINATOR // PROPOSER_WEIGHT
    )
    proposer_reward = Gwei(proposer_reward_numerator // proposer_reward_denominator)
    increase_balance(state, get_beacon_proposer_index(state), proposer_reward)

    # [New in Gloas:EIP7732]
    # Cập nhật weight của khoản thanh toán cho builder
    if current_epoch_target:
        state.builder_pending_payments[SLOTS_PER_EPOCH + data.slot % SLOTS_PER_EPOCH] = payment
    else:
        state.builder_pending_payments[data.slot % SLOTS_PER_EPOCH] = payment
```

##### Payload attestations

###### New `process_payload_attestation`

```python
def process_payload_attestation(
    state: BeaconState, payload_attestation: PayloadAttestation
) -> None:
    data = payload_attestation.data

    # Kiểm tra attestation dành cho parent beacon block
    assert data.beacon_block_root == state.latest_block_header.parent_root
    # Kiểm tra attestation dành cho slot trước đó
    assert data.slot + 1 == state.slot
    # Kiểm tra signature
    indexed_payload_attestation = get_indexed_payload_attestation(state, payload_attestation)
    assert is_valid_indexed_payload_attestation(state, indexed_payload_attestation)
```
