# EIP-8025 -- The Beacon Chain

*Note*: Tài liệu này đang trong quá trình soạn thảo (work-in-progress), dành cho
các nhà nghiên cứu và người triển khai (implementer).

## Table of contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Table of contents](#table-of-contents)
- [Introduction](#introduction)
- [Types](#types)
  - [New `ProofData`](#new-proofdata)
  - [New `ProofType`](#new-prooftype)
- [Constants](#constants)
  - [Execution](#execution)
  - [Domains](#domains)
- [Containers](#containers)
  - [New `PublicInput`](#new-publicinput)
  - [New `ExecutionProof`](#new-executionproof)
  - [New `ExecutionProofEnvelope`](#new-executionproofenvelope)
  - [New `SignedExecutionProofEnvelope`](#new-signedexecutionproofenvelope)
- [Helpers](#helpers)
  - [New `get_supported_proof_types`](#new-get_supported_proof_types)
- [Execution proof verification](#execution-proof-verification)
  - [New `verify_execution_proof_envelope`](#new-verify_execution_proof_envelope)
  - [New `get_execution_proof`](#new-get_execution_proof)
  - [New `process_execution_proof`](#new-process_execution_proof)

<!-- mdformat-toc end -->

## Introduction

Đây là các spec beacon-chain đưa vào execution proof (bằng chứng thực thi), cho
phép xác thực execution payload theo kiểu stateless (không cần lưu execution
state) với thời gian hằng số.

> 💡 Ghi chú: Thay vì tự chạy lại toàn bộ các transaction trong execution
> payload, node chỉ cần kiểm tra một proof (ví dụ zk-proof) chứng minh rằng
> payload đó hợp lệ. Thời gian kiểm tra không phụ thuộc vào độ lớn của payload.

Execution proof là các artifact không thuộc consensus. Việc verify hay lưu trữ
một proof không làm thay đổi beacon-chain state, fork choice, hay trạng thái
payload của Gloas.

*Note*: Spec này được xây dựng dựa trên [Gloas](../../gloas/beacon-chain.md) và
sử dụng interface verify proof từ [proof-engine.md](./proof-engine.md).

## Types

### New `ProofData`

```python
class ProofData(ByteList):
    """
    The opaque proof bytes of an execution proof.
    """

    LIMIT = MAX_PROOF_SIZE
```

### New `ProofType`

```python
class ProofType(Uint8):
    """
    The identifier of the proof system, guest program, and version associated
    with an execution proof.
    """
```

## Constants

### Execution

*Note*: Các giá trị execution này chưa phải là bản cuối cùng.

| Name                        | Value                                  |
| --------------------------- | -------------------------------------- |
| `MAX_PROOF_SIZE`            | `Uint64(4194304)` (= 4,096 KiB, 4 MiB) |
| `STATELESS_INPUT_SCHEMA_ID` | `Uint16(0x1501)`                       |

`STATELESS_INPUT_SCHEMA_ID` mã hoá protocol fork Amsterdam (`0x15`) và phiên bản
schema (`0x01`).

### Domains

| Name                     | Value                      |
| ------------------------ | -------------------------- |
| `DOMAIN_EXECUTION_PROOF` | `DomainType("0x0F000000")` |

## Containers

### New `PublicInput`

```python
class PublicInput(ProgressiveContainer):
    ACTIVE_FIELDS = active_fields(width=4)

    new_payload_request_root: Root
    successful_validation: Boolean
    chain_id: Uint64
    schema_id: Uint16
```

### New `ExecutionProof`

```python
class ExecutionProof(Container):
    proof_data: ProofData
    proof_type: ProofType
    public_input: PublicInput
```

### New `ExecutionProofEnvelope`

```python
class ExecutionProofEnvelope(Container):
    proof_data: ProofData
    proof_type: ProofType
    beacon_block_root: Root
```

### New `SignedExecutionProofEnvelope`

```python
class SignedExecutionProofEnvelope(Container):
    message: ExecutionProofEnvelope
    validator_index: ValidatorIndex
    signature: BLSSignature
```

## Helpers

### New `get_supported_proof_types`

*Note*: Việc gán giá trị proof type ban đầu chỉ là tạm thời. Mỗi `ProofType`
định danh một tổ hợp bất biến gồm proof system, guest program và version. Các
giá trị đã gán MUST NOT được tái sử dụng (KHÔNG ĐƯỢC dùng lại cho tổ hợp khác).

```python
def get_supported_proof_types() -> set[ProofType]:
    """
    Return the supported execution proof types.
    """
    return {
        ProofType(1),
        ProofType(2),
        ProofType(3),
    }
```

## Execution proof verification

### New `verify_execution_proof_envelope`

```python
def verify_execution_proof_envelope(
    state: BeaconState,
    signed_proof_envelope: SignedExecutionProofEnvelope,
) -> None:
    """
    Verify an execution proof envelope against the beacon state.
    The execution proof itself is verified separately by the proof engine.
    """
    proof_envelope = signed_proof_envelope.message
    assert signed_proof_envelope.validator_index < len(state.validators)
    assert len(proof_envelope.proof_data) != 0
    assert proof_envelope.proof_type in get_supported_proof_types()

    # Kiểm tra prover là một validator đang active
    validator = state.validators[signed_proof_envelope.validator_index]
    assert is_active_validator(validator, get_current_epoch(state))

    # Kiểm tra chữ ký (signature) của prover
    domain = get_domain(state, DOMAIN_EXECUTION_PROOF, compute_epoch_at_slot(state.slot))
    signing_root = compute_signing_root(proof_envelope, domain)
    assert bls.Verify(validator.pubkey, signing_root, signed_proof_envelope.signature)
```

### New `get_execution_proof`

```python
def get_execution_proof(
    state: BeaconState,
    proof_envelope: ExecutionProofEnvelope,
    payload_envelope: ExecutionPayloadEnvelope,
) -> ExecutionProof:
    """
    Construct the ``ExecutionProof`` for submission to the proof engine.
    """
    # Xây dựng public input cho proof system từ execution payload đã được chấp nhận
    bid = state.latest_execution_payload_bid
    new_payload_request = NewPayloadRequest(
        execution_payload=payload_envelope.payload,
        versioned_hashes=VersionedHashes(
            data=[
                kzg_commitment_to_versioned_hash(commitment)
                for commitment in bid.blob_kzg_commitments
            ]
        ),
        parent_beacon_block_root=payload_envelope.parent_beacon_block_root,
        execution_requests=payload_envelope.execution_requests,
    )
    public_input = PublicInput(
        new_payload_request_root=hash_tree_root(new_payload_request),
        successful_validation=Boolean(True),
        chain_id=DEPOSIT_CHAIN_ID,
        schema_id=STATELESS_INPUT_SCHEMA_ID,
    )
    return ExecutionProof(
        proof_data=proof_envelope.proof_data,
        proof_type=proof_envelope.proof_type,
        public_input=public_input,
    )
```

### New `process_execution_proof`

```python
def process_execution_proof(
    state: BeaconState,
    signed_proof_envelope: SignedExecutionProofEnvelope,
    payload_envelope: ExecutionPayloadEnvelope,
    proof_engine: ProofEngine,
) -> None:
    """
    Authenticate and verify an execution proof envelope.
    """
    verify_execution_proof_envelope(
        state,
        signed_proof_envelope,
    )

    proof = get_execution_proof(
        state,
        signed_proof_envelope.message,
        payload_envelope,
    )
    assert proof_engine.verify_execution_proof(proof)
```
