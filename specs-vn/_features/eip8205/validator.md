# EIP-8205 -- Honest Validator

*Lưu ý*: Tài liệu này đang trong quá trình soạn thảo, dành cho các nhà nghiên cứu
và những người triển khai (implementer).

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Beacon chain responsibilities](#beacon-chain-responsibilities)
  - [Block and sidecar proposal](#block-and-sidecar-proposal)
    - [Constructing the `BeaconBlockBody`](#constructing-the-beaconblockbody)
      - [Execution requests](#execution-requests)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả những thay đổi cần thực hiện trong code của một "honest
validator" (validator trung thực) để triển khai EIP-8205.

## Beacon chain responsibilities

Mọi trách nhiệm của validator giữ nguyên, ngoại trừ những điểm được nêu dưới đây.

### Block and sidecar proposal

#### Constructing the `BeaconBlockBody`

##### Execution requests

*Lưu ý*: Hàm `get_execution_requests` được sửa đổi để parse thêm các validator
preregistration request.

```python
def get_execution_requests(execution_requests_list: Sequence[bytes]) -> ExecutionRequests:
    deposits = DepositRequests()
    withdrawals = WithdrawalRequests()
    consolidations = ConsolidationRequests()
    builder_deposits = BuilderDepositRequests()
    builder_exits = BuilderExitRequests()
    # [New in EIP8205]
    preregistrations = PreregistrationRequests()

    request_types = [
        DEPOSIT_REQUEST_TYPE,
        WITHDRAWAL_REQUEST_TYPE,
        CONSOLIDATION_REQUEST_TYPE,
        BUILDER_DEPOSIT_REQUEST_TYPE,
        BUILDER_EXIT_REQUEST_TYPE,
        # [New in EIP8205]
        PREREGISTRATION_REQUEST_TYPE,
    ]

    prev_request_type = None
    for request in execution_requests_list:
        request_type, request_data = request[0:1], request[1:]

        # Kiểm tra request type hợp lệ
        assert request_type in request_types
        # Kiểm tra request data không rỗng
        assert len(request_data) != 0
        # Kiểm tra các request được sắp theo thứ tự tăng ngặt
        # Mỗi type sau phải lớn hơn type trước, không được trùng lặp
        assert prev_request_type is None or prev_request_type < request_type
        prev_request_type = request_type

        if request_type == DEPOSIT_REQUEST_TYPE:
            deposits = ssz_deserialize(DepositRequests, request_data)
        elif request_type == WITHDRAWAL_REQUEST_TYPE:
            withdrawals = ssz_deserialize(WithdrawalRequests, request_data)
        elif request_type == CONSOLIDATION_REQUEST_TYPE:
            consolidations = ssz_deserialize(ConsolidationRequests, request_data)
        elif request_type == BUILDER_DEPOSIT_REQUEST_TYPE:
            builder_deposits = ssz_deserialize(BuilderDepositRequests, request_data)
        elif request_type == BUILDER_EXIT_REQUEST_TYPE:
            builder_exits = ssz_deserialize(BuilderExitRequests, request_data)
        # [New in EIP8205]
        elif request_type == PREREGISTRATION_REQUEST_TYPE:
            preregistrations = ssz_deserialize(PreregistrationRequests, request_data)

    return ExecutionRequests(
        deposits=deposits,
        withdrawals=withdrawals,
        consolidations=consolidations,
        builder_deposits=builder_deposits,
        builder_exits=builder_exits,
        # [New in EIP8205]
        preregistrations=preregistrations,
    )
```
