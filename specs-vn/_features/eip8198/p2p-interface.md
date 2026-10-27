# EIP-8198 -- Networking

*Ghi chú*: Tài liệu này đang trong quá trình soạn thảo (work-in-progress), dành cho các nhà nghiên cứu và người triển khai client.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Configs](#configs)
- [Modifications in EIP-8198](#modifications-in-eip-8198)
  - [Helpers](#helpers)
    - [Modified `compute_fork_version`](#modified-compute_fork_version)
    - [New `compute_blob_data_retention_start_epoch`](#new-compute_blob_data_retention_start_epoch)
  - [The gossip domain: gossipsub](#the-gossip-domain-gossipsub)
  - [The Req/Resp domain](#the-reqresp-domain)
    - [Status v2](#status-v2)
    - [DataColumnSidecarsByRange v1](#datacolumnsidecarsbyrange-v1)
    - [DataColumnSidecarsByRoot v1](#datacolumnsidecarsbyroot-v1)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này chứa các đặc tả networking của consensus layer cho EIP-8198.

Đặc tả các thay đổi này tiếp nối cùng định dạng với đặc tả network của các lần
nâng cấp trước, và coi chúng là điều kiện tiên quyết (cần đọc trước).

*Ghi chú*: Đặc tả này được xây dựng dựa trên [Heze](../../heze/p2p-interface.md).

## Configs

| Name                         |                Value |
| ---------------------------- | -------------------: |
| `MIN_BLOB_DATA_RETENTION_MS` | `Uint64(1572864000)` |

*Ghi chú*: `MIN_BLOB_DATA_RETENTION_MS` thay thế cho
`MIN_EPOCHS_FOR_DATA_COLUMN_SIDECARS_REQUESTS` với cùng một khoảng thời gian,
nhưng được định nghĩa theo thời gian thực (wall-clock) thay vì theo số epoch.

> 💡 Ghi chú: `1572864000` ms = 4096 epoch × 32 slot × 12 giây, tức khoảng 18
> ngày — đúng bằng cửa sổ cũ với slot 12 giây. Định nghĩa theo mili giây giúp cửa
> sổ lưu trữ không bị co lại khi slot ngắn đi.

## Modifications in EIP-8198

### Helpers

#### Modified `compute_fork_version`

```python
def compute_fork_version(epoch: Epoch) -> Version:
    """
    Return the fork version at the given ``epoch``.
    """
    if epoch >= EIP8198_FORK_EPOCH:
        return EIP8198_FORK_VERSION
    if epoch >= HEZE_FORK_EPOCH:
        return HEZE_FORK_VERSION
    if epoch >= GLOAS_FORK_EPOCH:
        return GLOAS_FORK_VERSION
    if epoch >= FULU_FORK_EPOCH:
        return FULU_FORK_VERSION
    if epoch >= ELECTRA_FORK_EPOCH:
        return ELECTRA_FORK_VERSION
    if epoch >= DENEB_FORK_EPOCH:
        return DENEB_FORK_VERSION
    if epoch >= CAPELLA_FORK_EPOCH:
        return CAPELLA_FORK_VERSION
    if epoch >= BELLATRIX_FORK_EPOCH:
        return BELLATRIX_FORK_VERSION
    if epoch >= ALTAIR_FORK_EPOCH:
        return ALTAIR_FORK_VERSION
    return GENESIS_FORK_VERSION
```

#### New `compute_blob_data_retention_start_epoch`

```python
def compute_blob_data_retention_start_epoch(epoch: Epoch) -> Epoch:
    """
    Return the start epoch of the blob data retention window,
    preserving its wall-clock length across slot duration changes.
    """
    window_ms = MIN_BLOB_DATA_RETENTION_MS
    current_start_slot = compute_start_slot_at_epoch(epoch)
    current_start_ms = compute_time_at_slot_ms(Uint64(0), current_start_slot)
    if current_start_ms < window_ms:
        return GENESIS_EPOCH
    window_start_ms = Uint64(current_start_ms - window_ms)
    return compute_epoch_at_slot(compute_slot_at_time_ms(Uint64(0), window_start_ms))
```

### The gossip domain: gossipsub

Client SHOULD subscribe vào các topic theo fork digest mới trước
`EIP8198_FORK_EPOCH` và unsubscribe khỏi các topic cũ sau thời điểm đó.

Các khoảng thời gian được định nghĩa theo slot hoặc epoch MUST dùng dòng thời
gian từng đoạn (piecewise timeline — mỗi đoạn có độ dài slot riêng) thông qua
`compute_time_at_slot_ms` / `compute_slot_at_time_ms`. Ví dụ, `seen_ttl` của
gossipsub là hiệu giữa thời điểm bắt đầu của `current_slot + 2 * SLOTS_PER_EPOCH`
và của `current_slot`, được đổi sang giây bằng `milliseconds_to_seconds`. Bộ lập
lịch duty và `current_slot` theo đồng hồ cục bộ của light client cũng MUST dùng
dòng thời gian này. Các khoảng thời gian được cấu hình bằng mili giây, bao gồm
thời gian lưu trữ data column sidecar, vẫn cố định theo thời gian thực.

### The Req/Resp domain

#### Status v2

**Protocol ID:** `/eth2/beacon_chain/req/status/2/`

*[Modified in EIP8198]* Khoảng thời gian lưu trữ data column sidecar dùng để
xác định `earliest_available_slot` bắt đầu tại epoch
`max(compute_blob_data_retention_start_epoch(current_epoch), FULU_FORK_EPOCH)`.

#### DataColumnSidecarsByRange v1

**Protocol ID:** `/eth2/beacon_chain/req/data_column_sidecars_by_range/1/`

*[Modified in EIP8198]* `data_column_serve_range` được sửa thành
`[max(compute_blob_data_retention_start_epoch(current_epoch), FULU_FORK_EPOCH), current_epoch]`.

#### DataColumnSidecarsByRoot v1

**Protocol ID:** `/eth2/beacon_chain/req/data_column_sidecars_by_root/1/`

*[Modified in EIP8198]* `data_column_serve_range` được sửa thành
`[max(compute_blob_data_retention_start_epoch(current_epoch), FULU_FORK_EPOCH), current_epoch]`.
