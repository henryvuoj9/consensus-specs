# EIP-8198 -- Honest Validator

*Ghi chú*: Tài liệu này đang trong quá trình soạn thảo (work-in-progress), dành cho các nhà nghiên cứu và người triển khai client.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Beacon chain responsibilities](#beacon-chain-responsibilities)
  - [Block and sidecar proposal](#block-and-sidecar-proposal)
    - [Sidecar retention](#sidecar-retention)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này trình bày các thay đổi cần thực hiện trong code của một "honest
validator" (validator trung thực) để triển khai EIP-8198.

## Beacon chain responsibilities

Mọi trách nhiệm của validator giữ nguyên, ngoại trừ những điểm được nêu dưới đây.

*Ghi chú*: Validator MUST lập lịch các duty thông qua hàm
`get_slot_component_duration_ms` đã được cập nhật.

### Block and sidecar proposal

#### Sidecar retention

Khoảng thời gian lưu trữ data column sidecar được sửa thành
`MIN_BLOB_DATA_RETENTION_MS` mili giây.
