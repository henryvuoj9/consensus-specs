# Altair Light Client -- Networking

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Networking](#networking)
  - [Types](#types)
    - [`LightClientUpdates`](#lightclientupdates)
  - [Configs](#configs)
  - [The gossip domain: gossipsub](#the-gossip-domain-gossipsub)
    - [Topics and messages](#topics-and-messages)
      - [Global topics](#global-topics)
        - [New `light_client_finality_update`](#new-light_client_finality_update)
        - [New `light_client_optimistic_update`](#new-light_client_optimistic_update)
  - [The Req/Resp domain](#the-reqresp-domain)
    - [Messages](#messages)
      - [GetLightClientBootstrap](#getlightclientbootstrap)
      - [LightClientUpdatesByRange](#lightclientupdatesbyrange)
      - [GetLightClientFinalityUpdate](#getlightclientfinalityupdate)
      - [GetLightClientOptimisticUpdate](#getlightclientoptimisticupdate)
- [Light clients](#light-clients)
- [Validator assignments](#validator-assignments)
  - [Beacon chain responsibilities](#beacon-chain-responsibilities)
  - [Sync committee](#sync-committee)

<!-- mdformat-toc end -->

## Networking

Phần này mở rộng
[đặc tả networking của Altair](../p2p-interface.md) bằng cách bổ sung thêm các
message, topic và dữ liệu vào domain Req-Resp và domain Gossip.

### Types

#### `LightClientUpdates`

```python
class LightClientUpdates(List[LightClientUpdate]):
    """
    Light client updates returned in a ``LightClientUpdatesByRange`` response.
    """

    LIMIT = MAX_REQUEST_LIGHT_CLIENT_UPDATES
```

### Configs

| Name                               | Value                  | Description                                                         |
| ---------------------------------- | ---------------------- | ------------------------------------------------------------------- |
| `MAX_REQUEST_LIGHT_CLIENT_UPDATES` | `Uint64(2**7)` (= 128) | Số lượng `LightClientUpdate` tối đa trong một request               |

### The gossip domain: gossipsub

Các gossip mesh mới được bổ sung để light client có thể luôn sync với mạng.

#### Topics and messages

Các global topic mới được thêm vào để cung cấp cho light client các update mới
nhất.

| name                             | Message Type                  |
| -------------------------------- | ----------------------------- |
| `light_client_finality_update`   | `LightClientFinalityUpdate`   |
| `light_client_optimistic_update` | `LightClientOptimisticUpdate` |

##### Global topics

###### New `light_client_finality_update`

Topic này dùng để lan truyền `LightClientFinalityUpdate` mới nhất tới các light
client, giúp chúng theo dõi được `finalized_header` mới nhất.

Các kiểm tra hợp lệ sau MUST (PHẢI) thỏa mãn trước khi chuyển tiếp (forward)
`finality_update` lên mạng.

- _[IGNORE]_ `finalized_header.beacon.slot` lớn hơn slot tương ứng của mọi
  `finality_update` đã được forward trước đó, hoặc bằng slot cao nhất đã forward
  trước đó nhưng có `sync_aggregate` cho thấy mức tham gia supermajority (> 2/3)
  của sync committee, trong khi `finality_update` đã forward trước đó cho slot
  này chưa đạt supermajority
- _[IGNORE]_ `finality_update` được nhận sau khi block tại `signature_slot` đã
  có đủ thời gian để lan truyền qua mạng -- tức là kiểm tra rằng đã trôi qua
  `get_sync_message_due_ms()` mili giây (có tính đến dung sai
  `MAXIMUM_GOSSIP_CLOCK_DISPARITY`) kể từ khi bắt đầu `signature_slot`.

Đối với full node, các kiểm tra sau MUST được thỏa mãn thêm trước khi forward
`finality_update` lên mạng.

- _[IGNORE]_ `finality_update` nhận được phải khớp hoàn toàn với bản do node tự
  tính cục bộ (theo định nghĩa trong
  [`create_light_client_finality_update`](./full-node.md#create_light_client_finality_update))

Đối với light client, các kiểm tra sau MUST được thỏa mãn thêm trước khi forward
`finality_update` lên mạng.

- _[REJECT]_ `finality_update` hợp lệ -- tức là kiểm tra rằng
  `process_light_client_finality_update` không báo lỗi
- _[IGNORE]_ `finality_update` làm tiến `finalized_header` của
  `LightClientStore` cục bộ -- tức là kiểm tra rằng việc xử lý `finality_update`
  làm tăng `store.finalized_header.beacon.slot`

Light client SHOULD (NÊN) gọi `process_light_client_finality_update` ngay cả khi
message bị ignore.

> 💡 Ghi chú: _[IGNORE]_ nghĩa là bỏ qua message (không forward) nhưng không
> phạt peer gửi; _[REJECT]_ nghĩa là message không hợp lệ và peer gửi có thể bị
> trừ điểm (peer scoring). Việc vẫn gọi hàm xử lý khi message bị ignore giúp
> light client không bỏ lỡ thông tin hữu ích (ví dụ cập nhật cho
> `best_valid_update`).

Epoch ngữ cảnh (context epoch) dùng cho `ForkDigest` được xác định bởi
`compute_epoch_at_slot(finality_update.attested_header.beacon.slot)`.

Theo `fork_version = compute_fork_version(epoch)`:

<!-- eth_consensus_specs: skip -->

| `fork_version`                  | Message SSZ type                   |
| ------------------------------- | ---------------------------------- |
| `GENESIS_FORK_VERSION`          | n/a                                |
| `ALTAIR_FORK_VERSION` and later | `altair.LightClientFinalityUpdate` |

###### New `light_client_optimistic_update`

Topic này dùng để lan truyền `LightClientOptimisticUpdate` mới nhất tới các
light client, giúp chúng theo dõi được `optimistic_header` mới nhất.

Các kiểm tra hợp lệ sau MUST thỏa mãn trước khi forward `optimistic_update` lên
mạng.

- _[IGNORE]_ `attested_header.beacon.slot` lớn hơn slot tương ứng của mọi
  `optimistic_update` đã được forward trước đó
- _[IGNORE]_ `optimistic_update` được nhận sau khi block tại `signature_slot` đã
  có đủ thời gian để lan truyền qua mạng -- tức là kiểm tra rằng đã trôi qua
  `get_sync_message_due_ms()` mili giây (có tính đến dung sai
  `MAXIMUM_GOSSIP_CLOCK_DISPARITY`) kể từ khi bắt đầu
  `optimistic_update.signature_slot`.

Đối với full node, các kiểm tra sau MUST được thỏa mãn thêm trước khi forward
`optimistic_update` lên mạng.

- _[IGNORE]_ `optimistic_update` nhận được phải khớp hoàn toàn với bản do node
  tự tính cục bộ (theo định nghĩa trong
  [`create_light_client_optimistic_update`](./full-node.md#create_light_client_optimistic_update))

Đối với light client, các kiểm tra sau MUST được thỏa mãn thêm trước khi forward
`optimistic_update` lên mạng.

- _[REJECT]_ `optimistic_update` hợp lệ -- tức là kiểm tra rằng
  `process_light_client_optimistic_update` không báo lỗi
- _[IGNORE]_ `optimistic_update` hoặc khớp với các trường tương ứng của
  `LightClientFinalityUpdate` được forward gần nhất (nếu có), hoặc làm tiến
  `optimistic_header` của `LightClientStore` cục bộ -- tức là kiểm tra rằng việc
  xử lý `optimistic_update` làm tăng `store.optimistic_header.beacon.slot`

Light client SHOULD gọi `process_light_client_optimistic_update` ngay cả khi
message bị ignore.

Epoch ngữ cảnh dùng cho `ForkDigest` được xác định bởi
`compute_epoch_at_slot(optimistic_update.attested_header.beacon.slot)`.

Theo `fork_version = compute_fork_version(epoch)`:

<!-- eth_consensus_specs: skip -->

| `fork_version`                  | Message SSZ type                     |
| ------------------------------- | ------------------------------------ |
| `GENESIS_FORK_VERSION`          | n/a                                  |
| `ALTAIR_FORK_VERSION` and later | `altair.LightClientOptimisticUpdate` |

### The Req/Resp domain

#### Messages

##### GetLightClientBootstrap

**Protocol ID:** `/eth2/beacon_chain/req/light_client_bootstrap/1/`

Nội dung request:

```
(
  Root
)
```

Nội dung response:

```
(
  LightClientBootstrap
)
```

Yêu cầu cấu trúc `LightClientBootstrap` tương ứng với một beacon block root
(thuộc giai đoạn sau Altair) cho trước.

Request MUST được mã hóa dưới dạng một SSZ-field.

Peer SHOULD trả về kết quả theo định nghĩa trong
[`create_light_client_bootstrap`](./full-node.md#create_light_client_bootstrap).
Để đáp ứng request, peer cần biết block được yêu cầu cùng post state của nó.

Khi không thể tạo được `LightClientBootstrap` cho block root được yêu cầu, peer
SHOULD phản hồi bằng mã lỗi `3: ResourceUnavailable`.

Với mỗi `response_chunk` thành công, epoch ngữ cảnh dùng cho `ForkDigest` được
xác định bởi `compute_epoch_at_slot(bootstrap.header.beacon.slot)`.

Theo `fork_version = compute_fork_version(epoch)`:

<!-- eth_consensus_specs: skip -->

| `fork_version`                  | Response SSZ type             |
| ------------------------------- | ----------------------------- |
| `GENESIS_FORK_VERSION`          | n/a                           |
| `ALTAIR_FORK_VERSION` and later | `altair.LightClientBootstrap` |

##### LightClientUpdatesByRange

**Protocol ID:** `/eth2/beacon_chain/req/light_client_updates_by_range/1/`

Nội dung request:

```
(
  start_period: Uint64
  count: Uint64
)
```

Nội dung response:

```
(
  LightClientUpdates
)
```

Yêu cầu các `LightClientUpdate` trong khoảng sync committee period
`[start_period, start_period + count)`, tính tới sync committee period của head
hiện tại do fork choice chọn.

Request MUST được mã hóa dưới dạng một SSZ-container.

Response MUST gồm không hoặc nhiều `response_chunk`. Mỗi `response_chunk`
_thành công_ MUST chứa đúng một payload `LightClientUpdate`.

Peer SHOULD trả về kết quả theo định nghĩa trong
[`create_light_client_update`](./full-node.md#create_light_client_update). Peer
MUST trả về ít nhất kết quả sớm nhất mà nó biết trong khoảng được yêu cầu, và
MUST gửi các kết quả theo thứ tự liên tiếp (theo period). Response MUST NOT
(KHÔNG ĐƯỢC) chứa nhiều hơn `min(MAX_REQUEST_LIGHT_CLIENT_UPDATES, count)` kết
quả.

Với mỗi `response_chunk` thành công, epoch ngữ cảnh dùng cho `ForkDigest` được
xác định bởi `compute_epoch_at_slot(update.attested_header.beacon.slot)`. Lưu ý
rằng epoch ngữ cảnh này có thể khác với epoch dùng để xác minh
`update.sync_aggregate`, vốn dựa trên `update.signature_slot`.

> 💡 Ghi chú: Điều này xảy ra ở ranh giới fork: `attested_header` có thể thuộc
> fork cũ trong khi block chứa chữ ký (tại `signature_slot`) đã thuộc fork mới.
> Khi xác minh chữ ký, phải dùng fork version tương ứng với `signature_slot`.

Theo `fork_version = compute_fork_version(epoch)`:

<!-- eth_consensus_specs: skip -->

| `fork_version`                  | Response chunk SSZ type    |
| ------------------------------- | -------------------------- |
| `GENESIS_FORK_VERSION`          | n/a                        |
| `ALTAIR_FORK_VERSION` and later | `altair.LightClientUpdate` |

##### GetLightClientFinalityUpdate

**Protocol ID:** `/eth2/beacon_chain/req/light_client_finality_update/1/`

Không có nội dung request.

Nội dung response:

```
(
  LightClientFinalityUpdate
)
```

Yêu cầu `LightClientFinalityUpdate` mới nhất mà peer biết.

Peer SHOULD trả về kết quả theo định nghĩa trong
[`create_light_client_finality_update`](./full-node.md#create_light_client_finality_update).

Khi không có `LightClientFinalityUpdate` nào, peer SHOULD phản hồi bằng mã lỗi
`3: ResourceUnavailable`.

Với mỗi `response_chunk` thành công, epoch ngữ cảnh dùng cho `ForkDigest` được
xác định bởi
`compute_epoch_at_slot(finality_update.attested_header.beacon.slot)`. Lưu ý rằng
epoch ngữ cảnh này có thể khác với epoch dùng để xác minh
`finality_update.sync_aggregate`, vốn dựa trên
`finality_update.signature_slot`.

Theo `fork_version = compute_fork_version(epoch)`:

<!-- eth_consensus_specs: skip -->

| `fork_version`                  | Response SSZ type                  |
| ------------------------------- | ---------------------------------- |
| `GENESIS_FORK_VERSION`          | n/a                                |
| `ALTAIR_FORK_VERSION` and later | `altair.LightClientFinalityUpdate` |

##### GetLightClientOptimisticUpdate

**Protocol ID:** `/eth2/beacon_chain/req/light_client_optimistic_update/1/`

Không có nội dung request.

Nội dung response:

```
(
  LightClientOptimisticUpdate
)
```

Yêu cầu `LightClientOptimisticUpdate` mới nhất mà peer biết.

Peer SHOULD trả về kết quả theo định nghĩa trong
[`create_light_client_optimistic_update`](./full-node.md#create_light_client_optimistic_update).

Khi không có `LightClientOptimisticUpdate` nào, peer SHOULD phản hồi bằng mã lỗi
`3: ResourceUnavailable`.

Với mỗi `response_chunk` thành công, epoch ngữ cảnh dùng cho `ForkDigest` được
xác định bởi
`compute_epoch_at_slot(optimistic_update.attested_header.beacon.slot)`. Lưu ý
rằng epoch ngữ cảnh này có thể khác với epoch dùng để xác minh
`optimistic_update.sync_aggregate`, vốn dựa trên
`optimistic_update.signature_slot`.

Theo `fork_version = compute_fork_version(epoch)`:

<!-- eth_consensus_specs: skip -->

| `fork_version`                  | Response SSZ type                    |
| ------------------------------- | ------------------------------------ |
| `GENESIS_FORK_VERSION`          | n/a                                  |
| `ALTAIR_FORK_VERSION` and later | `altair.LightClientOptimisticUpdate` |

## Light clients

Light client dùng libp2p để giữ sync với mạng SHOULD subscribe vào các pubsub
topic [`light_client_finality_update`](#new-light_client_finality_update) và
[`light_client_optimistic_update`](#new-light_client_optimistic_update), đồng
thời kiểm tra hợp lệ mọi message nhận được, trong khi
[quy trình sync của light client](./light-client.md#light-client-sync-process)
đang ở giai đoạn hỗ trợ xử lý các cấu trúc `LightClientFinalityUpdate` và
`LightClientOptimisticUpdate`.

Light client MAY (CÓ THỂ) thu thập thêm dữ liệu light client lịch sử và cung cấp
cho các peer khác. Nếu làm vậy, chúng SHOULD quảng bá (advertise) các endpoint
message được hỗ trợ trong [domain Req/Resp](#the-reqresp-domain), và MAY cập
nhật nội dung message [`Status`](../../phase0/p2p-interface.md#status-v1) của
mình để phản ánh dữ liệu light client đang có sẵn cục bộ.

Nếu chỉ có một phần hạn chế dữ liệu light client cục bộ, light client SHOULD
dùng dữ liệu dựa trên `genesis_block` và `GENESIS_SLOT` trong message `Status`
của mình. Các peer lai (hybrid) đồng thời triển khai chức năng full node MUST
chỉ đưa vào message `Status` dữ liệu dựa trên tiến độ sync của phần full node.

## Validator assignments

Phần này mở rộng [đặc tả honest validator](../validator.md) với các trách nhiệm
bổ sung để giúp light client có thể sync với mạng.

### Beacon chain responsibilities

Mọi full node SHOULD subscribe và góp phần duy trì sự ổn định của các pubsub
topic [`light_client_finality_update`](#new-light_client_finality_update) và
[`light_client_optimistic_update`](#new-light_client_optimistic_update) bằng
cách kiểm tra hợp lệ mọi message nhận được.

### Sync committee

Mỗi khi fork choice chọn một head block mới có mức tham gia sync aggregate
`>= MIN_SYNC_COMMITTEE_PARTICIPANTS` và có parent block thuộc giai đoạn sau
Altair, thì các full node có ít nhất một validator được phân công vào sync
committee hiện tại tại `slot` của block đó SHOULD broadcast dữ liệu light client
được tạo ra như sau:

- Nếu `finalized_header.beacon.slot` tăng lên, một `LightClientFinalityUpdate`
  SHOULD được broadcast lên pubsub topic `light_client_finality_update`, nếu
  chưa có message tương ứng nào được forward trong quá trình gossip validation.
- Nếu `attested_header.beacon.slot` tăng lên, một `LightClientOptimisticUpdate`
  SHOULD được broadcast lên pubsub topic `light_client_optimistic_update`, nếu
  chưa có message tương ứng nào được forward trong quá trình gossip validation.

Các message này SHOULD được broadcast sau `get_sync_message_due_ms()` mili giây
kể từ đầu slot. Để đảm bảo block tương ứng đã có đủ thời gian lan truyền qua
mạng, chúng SHOULD NOT (KHÔNG NÊN) được gửi sớm hơn. Lưu ý rằng điều này khác
với cách xử lý các message khác, ví dụ attestation, vốn có thể được gửi sớm.
