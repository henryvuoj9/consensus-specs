# EIP-8025 -- Proof Engine

*Lưu ý*: Tài liệu này vẫn đang được soạn thảo, dành cho các nhà nghiên cứu và
người triển khai.

## Table of contents

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Table of contents](#table-of-contents)
- [Introduction](#introduction)
- [Proof engine](#proof-engine)
  - [New `verify_execution_proof`](#new-verify_execution_proof)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả đặc tả Proof Engine. Proof Engine cho phép kiểm tra hợp lệ
execution payload theo kiểu stateless (không cần lưu giữ execution state) thông
qua các execution proof.

> 💡 Ghi chú: Thay vì tự thực thi lại toàn bộ execution payload, node chỉ cần
> xác minh một proof chứng minh rằng payload đã được thực thi đúng.

## Proof engine

Protocol `ProofEngine` (phần cài đặt phụ thuộc vào từng client) đóng gói việc
xác minh proof thông qua `self.verify_execution_proof`.

### New `verify_execution_proof`

```python
def verify_execution_proof(
    self: ProofEngine,
    execution_proof: ExecutionProof,
) -> bool:
    """
    Verify an execution proof.

    Use ``hash_tree_root(execution_proof.public_input)`` as the proof-system
    public input.

    Return ``True`` if ``execution_proof`` is valid.
    """
```

> 💡 Ghi chú: Hàm này phải dùng `hash_tree_root(execution_proof.public_input)`
> làm public input cho hệ thống proof, và trả về `True` nếu `execution_proof`
> hợp lệ.
