# Heze -- Honest Builder

*Lưu ý*: Tài liệu này vẫn đang trong quá trình hoàn thiện, dành cho các nhà nghiên cứu và người triển khai client.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Builder activities](#builder-activities)
  - [Constructing the `SignedExecutionPayloadBid`](#constructing-the-signedexecutionpayloadbid)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả những thay đổi cần thực hiện trong code của một "honest
builder" (builder trung thực) để triển khai Heze.

## Builder activities

### Constructing the `SignedExecutionPayloadBid`

*Lưu ý*: Thay đổi duy nhất đối với `SignedExecutionPayloadBid` là đặt giá trị
`bid.inclusion_list_bits` dựa trên góc nhìn inclusion list của builder, tức là
tập hợp tất cả các inclusion list hợp lệ và không bị equivocation (không có hai
bản mâu thuẫn từ cùng một validator) mà builder đã quan sát được.

1. Đặt `bid.inclusion_list_bits` bằng
   `get_inclusion_list_bits(get_inclusion_list_store(), inclusion_list_committee, slot, dependent_root, only_timely=False)`,
   trong đó `inclusion_list_committee` là
   `get_inclusion_list_committee(state, slot)`, `dependent_root` là
   `get_shuffling_dependent_root(store, bid.parent_block_root, compute_epoch_at_slot(slot))`,
   `slot` là `bid.slot - 1`, và `store` là fork choice store.

> 💡 Ghi chú: Inclusion list được sinh ra ở slot ngay trước slot của bid (nên
> dùng `bid.slot - 1`). Builder dùng `only_timely=False` để tính cả những
> inclusion list đến muộn mà nó đã thấy, khác với các attester vốn chỉ xét
> inclusion list đến đúng hạn.
