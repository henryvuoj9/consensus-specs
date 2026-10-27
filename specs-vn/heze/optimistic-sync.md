# Heze -- Optimistic Sync

*Lưu ý*: Tài liệu này vẫn đang trong quá trình hoàn thiện, dành cho các nhà nghiên cứu và người triển khai client.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Mechanisms](#mechanisms)
  - [How to optimistically import blocks](#how-to-optimistically-import-blocks)
    - [New How to track inclusion list satisfaction](#new-how-to-track-inclusion-list-satisfaction)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này đặc tả các sửa đổi của Heze đối với optimistic sync liên quan đến
việc kiểm tra một block có thỏa mãn inclusion list hay không (inclusion list
satisfaction). Tài liệu này mở rộng
[Bellatrix optimistic sync specification](../bellatrix/optimistic-sync.md).

## Mechanisms

### How to optimistically import blocks

#### New How to track inclusion list satisfaction

Khi import một block theo kiểu optimistic:

- Hàm
  [`is_inclusion_list_satisfied`](./fork-choice.md#new-is_inclusion_list_satisfied)
  MUST trả về `True` nếu execution engine trả về `NOT_VALIDATED`. Một phản hồi
  `INVALIDATED` MUST dẫn đến kết quả `False`.

Khi một block chuyển trạng thái từ `NOT_VALIDATED` -> `VALID`, phản hồi từ
execution engine cũng cho biết execution payload của block đó có thỏa mãn các
ràng buộc của inclusion list hay không. Consensus engine MUST ghi lại kết quả
này cho block đó. Kết quả inclusion list satisfaction đã ghi nhận của các block
tổ tiên (ancestor) vẫn giữ nguyên, không thay đổi.

> 💡 Ghi chú: Nói cách khác, khi execution engine chưa xác thực được payload,
> consensus client tạm coi như inclusion list đã được thỏa mãn để không chặn
> fork choice; kết quả thật sẽ được cập nhật sau khi payload được xác thực.
