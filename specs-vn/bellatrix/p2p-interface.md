# Bellatrix -- Networking

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Types](#types)
  - [New `PayloadValidationStatus`](#new-payloadvalidationstatus)
- [Constants](#constants)
- [Helpers](#helpers)
  - [Modified `compute_fork_version`](#modified-compute_fork_version)
- [The gossip domain: gossipsub](#the-gossip-domain-gossipsub)
  - [Topics and messages](#topics-and-messages)
    - [Global topics](#global-topics)
      - [Modified `beacon_block`](#modified-beacon_block)
  - [Transitioning the gossip](#transitioning-the-gossip)
- [The Req/Resp domain](#the-reqresp-domain)
  - [Messages](#messages)
    - [BeaconBlocksByRange v2](#beaconblocksbyrange-v2)
    - [BeaconBlocksByRoot v2](#beaconblocksbyroot-v2)
- [Gossipsub](#gossipsub)
  - [Why was the max gossip message size increased at Bellatrix?](#why-was-the-max-gossip-message-size-increased-at-bellatrix)
  - [Req/Resp](#reqresp)
    - [Why was the max chunk response size increased at Bellatrix?](#why-was-the-max-chunk-response-size-increased-at-bellatrix)
    - [Why allow invalid payloads on the P2P network?](#why-allow-invalid-payloads-on-the-p2p-network)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả đặc tả networking của consensus layer cho bản nâng cấp
Bellatrix.

Đặc tả các thay đổi ở đây tiếp tục dùng cùng định dạng với đặc tả network của
các bản nâng cấp trước, và coi các đặc tả đó là kiến thức tiên quyết. Tài liệu
này cần được hiểu là phần *bổ sung* cho các tài liệu của
[Phase 0](../phase0/p2p-interface.md) và
[Altair](../altair/p2p-interface.md); từ đây trở đi chúng lần lượt được gọi là
"tài liệu Phase 0" và "tài liệu Altair". Người đọc nên nắm vững tài liệu Phase 0
và Altair, rồi dùng chúng làm nền tảng để hiểu những thay đổi được nêu trong tài
liệu này.

## Types

### New `PayloadValidationStatus`

*(Trạng thái kiểm tra execution payload của một block, do execution engine trả về.)*

```python
class PayloadValidationStatus(Uint8):
    """
    The status of an execution payload's validation by the execution engine.
    """
```

## Constants

| Name                           | Value                        |
| ------------------------------ | ---------------------------- |
| `PAYLOAD_STATUS_VALID`         | `PayloadValidationStatus(0)` |
| `PAYLOAD_STATUS_INVALIDATED`   | `PayloadValidationStatus(1)` |
| `PAYLOAD_STATUS_NOT_VALIDATED` | `PayloadValidationStatus(2)` |

> 💡 Ghi chú: `PAYLOAD_STATUS_VALID` nghĩa là execution engine đã xác nhận
> payload hợp lệ; `PAYLOAD_STATUS_INVALIDATED` nghĩa là payload đã được kiểm tra
> và bị xác định là không hợp lệ; `PAYLOAD_STATUS_NOT_VALIDATED` nghĩa là payload
> chưa được execution engine kiểm tra (node đang ở chế độ optimistic đối với
> block đó).

## Helpers

### Modified `compute_fork_version`

```python
def compute_fork_version(epoch: Epoch) -> Version:
    """
    Return the fork version at the given ``epoch``.
    """
    if epoch >= BELLATRIX_FORK_EPOCH:
        return BELLATRIX_FORK_VERSION
    if epoch >= ALTAIR_FORK_EPOCH:
        return ALTAIR_FORK_VERSION
    return GENESIS_FORK_VERSION
```

## The gossip domain: gossipsub

Ở Bellatrix, một số gossip mesh được nâng cấp để hỗ trợ các kiểu dữ liệu đã được
thay đổi.

### Topics and messages

Các topic tuân theo cùng đặc tả như ở các bản nâng cấp trước. Mọi topic đều giữ
nguyên, ngoại trừ topic beacon block — topic này được cập nhật để dùng kiểu dữ
liệu đã sửa đổi.

Đặc tả về việc tạo, kiểm tra (validation) và phát tán message không thay đổi so
với tài liệu Altair, trừ khi được ghi chú rõ ở đây.

Cách tính `message-id` giữ nguyên.

Các topic mới cùng với kiểu của trường `data` trong gossipsub message được liệt
kê trong bảng sau:

| Name           | Message Type                   |
| -------------- | ------------------------------ |
| `beacon_block` | `SignedBeaconBlock` (modified) |

Lưu ý rằng phân đoạn `ForkDigestValue` trong đường dẫn topic giúp tách biệt topic
`beacon_block` cũ và mới (mỗi fork có fork digest khác nhau nên tên topic cũng
khác nhau).

#### Global topics

Bellatrix thay đổi kiểu dữ liệu của topic beacon block toàn cục.

##### Modified `beacon_block`

Topic `beacon_block` chỉ được dùng để lan truyền các beacon block mới đã được ký
tới tất cả các node trong mạng. Block đã ký được gửi nguyên vẹn (toàn bộ nội
dung).

*Lưu ý*: Các block đã bật execution sẽ được phép lan truyền bất kể execution
payload có hợp lệ hay không. Điều này ngăn việc mạng bị chia tách giữa các node
[optimistic](./optimistic-sync.md) và non-optimistic.

> 💡 Ghi chú: Node optimistic là node đã import block nhưng execution engine của
> nó chưa kiểm tra xong execution payload. Nếu gossip từ chối block chỉ vì
> payload chưa/không hợp lệ, các node optimistic và non-optimistic có thể có cái
> nhìn khác nhau về chain và bị phân mảnh. Vì vậy, quy tắc gossip bên dưới chủ
> yếu dựa trên các điều kiện của consensus layer.

```python
def validate_beacon_block_gossip(
    seen: Seen,
    store: Store,
    signed_beacon_block: SignedBeaconBlock,
    current_time_ms: Uint64,
    # [New in Bellatrix]
    block_payload_statuses: dict[Root, PayloadValidationStatus],
) -> None:
    """
    Validate a SignedBeaconBlock for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    block = signed_beacon_block.message
    execution_payload = block.body.execution_payload

    # [IGNORE] Block là block đầu tiên có chữ ký hợp lệ nhận được cho cặp (slot, proposer) này
    proposer_slot_key = (block.slot, block.proposer_index)
    if proposer_slot_key in seen.proposer_slots:
        raise GossipIgnore("block is not the first valid block for this slot and proposer")

    # [IGNORE] Block không thuộc một slot trong tương lai
    # (MAY đưa vào hàng đợi để xử lý khi tới slot thích hợp)
    if is_future_slot(store, block.slot, current_time_ms):
        raise GossipIgnore("block is from a future slot")

    # [IGNORE] Block thuộc slot lớn hơn slot finalized mới nhất
    # (MAY vẫn kiểm tra và lưu những block như vậy cho mục đích khác
    # -- ví dụ phát hiện slashing, archive node, v.v.)
    finalized_slot = compute_start_slot_at_epoch(store.finalized_checkpoint.epoch)
    if block.slot <= finalized_slot:
        raise GossipIgnore("block is not from a slot greater than the latest finalized slot")

    # [IGNORE] Block cha đã được thấy (qua gossip hoặc nguồn khác ngoài gossip)
    # (MAY đưa vào hàng đợi cho tới khi lấy được block cha)
    if block.parent_root not in store.blocks:
        raise GossipIgnore("block's parent has not been seen")

    # [New in Bellatrix]
    parent_payload_status = PAYLOAD_STATUS_NOT_VALIDATED
    if block.parent_root in block_payload_statuses:
        parent_payload_status = block_payload_statuses[block.parent_root]

    # [New in Bellatrix]
    if block.parent_root not in store.block_states:
        # Block cha không có post-state, nên `is_execution_enabled` dùng state của
        # justified checkpoint (luôn đã được import). Trạng thái merge-complete là đơn điệu (đã complete thì không quay lại).
        if is_execution_enabled(store.block_states[store.justified_checkpoint.root], block.body):
            if parent_payload_status == PAYLOAD_STATUS_NOT_VALIDATED:
                # [REJECT] Block cha không qua được kiểm tra và execution payload của nó đang ở trạng thái optimistic
                raise GossipReject("block's parent is invalid and its payload is optimistic")

            # [IGNORE] Block cha không qua được kiểm tra và execution payload của nó đã được xử lý
            raise GossipIgnore("block's parent is invalid and its payload is processed")

        # [Modified in Bellatrix]
        # [REJECT] Block cha phải qua được kiểm tra
        raise GossipReject("block's parent is invalid and execution is not enabled")

    state = store.block_states[get_head(store).root]

    # [REJECT] Proposer index là một validator index hợp lệ
    if block.proposer_index >= len(state.validators):
        raise GossipReject("proposer index out of range")

    # [REJECT] Chữ ký của proposer hợp lệ
    proposer = state.validators[block.proposer_index]
    domain = get_domain(state, DOMAIN_BEACON_PROPOSER, compute_epoch_at_slot(block.slot))
    signing_root = compute_signing_root(block, domain)
    if not bls.Verify(proposer.pubkey, signing_root, signed_beacon_block.signature):
        raise GossipReject("invalid proposer signature")

    # [New in Bellatrix]
    if is_execution_enabled(state, block.body):
        # [REJECT] Timestamp của execution payload trong block khớp với slot
        if execution_payload.timestamp != compute_time_at_slot(state.genesis_time, block.slot):
            raise GossipReject("incorrect execution payload timestamp")

        # [IGNORE] Block cha đã qua kiểm tra nhưng execution payload của nó không hợp lệ
        if parent_payload_status == PAYLOAD_STATUS_INVALIDATED:
            raise GossipIgnore("block's parent is valid and its payload is invalid")

    # [REJECT] Block thuộc slot cao hơn slot của block cha
    if block.slot <= store.blocks[block.parent_root].slot:
        raise GossipReject("block is not from a higher slot than its parent")

    # [REJECT] Finalized checkpoint hiện tại là tổ tiên (ancestor) của block
    finalized_epoch = store.finalized_checkpoint.epoch
    finalized_checkpoint_block = get_checkpoint_block(store, block.parent_root, finalized_epoch)
    if finalized_checkpoint_block != store.finalized_checkpoint.root:
        raise GossipReject("finalized checkpoint is not an ancestor of block")

    # [REJECT] Block được đề xuất bởi đúng proposer dự kiến cho slot đó
    # (nếu chưa có dữ liệu shuffling thì IGNORE thay vì REJECT, và MAY đưa vào hàng đợi để xử lý sau)
    parent_state = store.block_states[block.parent_root].copy()
    process_slots(parent_state, block.slot)
    expected_proposer = get_beacon_proposer_index(parent_state)
    if block.proposer_index != expected_proposer:
        raise GossipReject("block proposer_index does not match expected proposer")

    # Đánh dấu block này là đã thấy
    seen.proposer_slots.add(proposer_slot_key)
```

> 💡 Ghi chú: Tóm tắt các điểm mới ở Bellatrix trong quy tắc gossip trên:
>
> - Nếu block cha đã được thấy nhưng không có post-state (tức là block cha không
>   qua được state transition) và execution đã được bật: block bị REJECT nếu
>   payload của block cha còn chưa được kiểm tra (optimistic), hoặc bị IGNORE nếu
>   payload của block cha đã được xử lý. Nếu execution chưa bật, block bị REJECT
>   như trước đây.
> - Nếu execution đã bật cho block: `timestamp` của execution payload PHẢI khớp
>   chính xác với thời điểm bắt đầu của slot, nếu không block bị REJECT.
> - Nếu block cha hợp lệ ở consensus layer nhưng execution payload của nó đã bị
>   execution engine đánh dấu là không hợp lệ, block con bị IGNORE (không phạt
>   peer).

### Transitioning the gossip

Xem chi tiết về việc chuyển đổi gossip trong
[tài liệu Altair](../altair/p2p-interface.md#transitioning-the-gossip) để biết
cách xử lý việc chuyển đổi các gossip topic khi qua fork.

## The Req/Resp domain

Các node [optimistic](./optimistic-sync.md) hoạt động bình thường (không có lỗi)
vẫn có thể gửi những block mà execution engine sẽ trả về kết quả INVALID. Để
ngăn mạng bị chia tách giữa các node optimistic và non-optimistic, việc truyền
một execution payload INVALID qua Req/Resp domain SHOULD NOT khiến node gửi bị
hạ điểm (down-score) hoặc bị ngắt kết nối. Ngược lại, việc truyền một block không
hợp lệ do vi phạm bất kỳ quy tắc nào của consensus layer (tức là *không phải* quy
tắc của execution layer) MAY dẫn tới việc bị hạ điểm hoặc bị ngắt kết nối.

### Messages

#### BeaconBlocksByRange v2

**Protocol ID:** `/eth2/beacon_chain/req/beacon_blocks_by_range/2/`

Request và Response giữ nguyên. Fork digest của Bellatrix được bổ sung vào enum
`context` để chỉ định kiểu block của Bellatrix.

<!-- eth_consensus_specs: skip -->

| `fork_version`           | Chunk SSZ type                |
| ------------------------ | ----------------------------- |
| `GENESIS_FORK_VERSION`   | `phase0.SignedBeaconBlock`    |
| `ALTAIR_FORK_VERSION`    | `altair.SignedBeaconBlock`    |
| `BELLATRIX_FORK_VERSION` | `bellatrix.SignedBeaconBlock` |

#### BeaconBlocksByRoot v2

**Protocol ID:** `/eth2/beacon_chain/req/beacon_blocks_by_root/2/`

Request và Response giữ nguyên. Fork digest của Bellatrix được bổ sung vào enum
`context` để chỉ định kiểu block của Bellatrix.

<!-- eth_consensus_specs: skip -->

| `fork_version`           | Chunk SSZ type                |
| ------------------------ | ----------------------------- |
| `GENESIS_FORK_VERSION`   | `phase0.SignedBeaconBlock`    |
| `ALTAIR_FORK_VERSION`    | `altair.SignedBeaconBlock`    |
| `BELLATRIX_FORK_VERSION` | `bellatrix.SignedBeaconBlock` |

# Design decision rationale

*(Lý do của các quyết định thiết kế)*

## Gossipsub

### Why was the max gossip message size increased at Bellatrix?

Khi `ExecutionPayload` được thêm vào `BeaconBlock`, block có thêm một trường có
kích thước động -- `transactions` -- và trường này hoàn toàn có thể (một cách hợp
lệ) vượt quá giới hạn `MAX_PAYLOAD_SIZE` (1 MiB) được đặt ra từ Phase 0. Vì vậy
MAX_PAYLOAD_SIZE trên mạng được tăng lên 10 MiB. Với `GAS_LIMIT` (~30M) quan sát
được trên mainnet vào năm 2021, một transaction duy nhất chứa toàn dữ liệu với
chi phí 16 gas mỗi byte có thể tạo ra một `ExecutionPayload` hợp lệ có kích thước
~2 MiB. Do đó cần một giới hạn kích thước ít nhất phải đáp ứng được điều kiện
hiện tại của mainnet.

> 💡 Ghi chú: 30.000.000 gas / 16 gas mỗi byte ≈ 1.875.000 byte ≈ 1,8–2 MiB, vượt
> xa giới hạn 1 MiB cũ.

Lưu ý rằng do phần kích thước tăng thêm từ các nội dung khác của `BeaconBlock`
(ví dụ chữ ký của proposer, các danh sách operation, v.v.), kích thước tối đa
theo lý thuyết của một `ExecutionPayload` hợp lệ (và của danh sách
`transactions`) sẽ thấp hơn 10 MiB một chút. Xét rằng kích thước tối đa của
`BeaconBlock` (không tính payload) chỉ vào khoảng 128 KiB trong trường hợp xấu
nhất, và gas limit hiện tại (~30M) giới hạn kích thước block tối đa ở dưới 2 MiB,
khác biệt nhỏ này trong giới hạn lý thuyết sẽ không ảnh hưởng gì đến chức năng
và bảo mật của mạng.

### Req/Resp

#### Why was the max chunk response size increased at Bellatrix?

Tương tự như phần thảo luận về việc tăng kích thước gossip tối đa, kiểu
`ExecutionPayload` có thể khiến `BeaconBlock` vượt quá giới hạn 1 MiB được đặt
ra ở Phase 0.

Cũng như với giới hạn gossip, con số 10 MiB được chọn vì nó chắc chắn cao hơn
kích thước của mọi block hợp lệ trong phạm vi gas limit dự kiến trong trung hạn.

Đối với cả giá trị tối đa của gossip lẫn req/resp, các giới hạn riêng theo từng
kiểu dữ liệu (type-specific limits) luôn phải được tuân thủ đồng thời.

#### Why allow invalid payloads on the P2P network?

Đặc tả cho phép các block có execution payload không hợp lệ được lan truyền qua
gossip và qua các lời gọi RPC. Lý do như sau:

1. Các node optimistic phải lắng nghe gossip block để có được cái nhìn về head
   của chain.
2. Do đó, các node optimistic phải lan truyền gossip block. Nếu không, chúng sẽ
   trở thành đang kiểm duyệt (censor) block.
3. Nếu các node optimistic lan truyền block qua gossip, thì chúng cũng phải trả
   lời các request lấy block cha qua RPC.
4. Do đó, các node optimistic phải gửi các block optimistic (block có payload
   chưa được kiểm tra) qua RPC.

Vì vậy, để tránh mạng bị chia tách do các node optimistic vô tình gửi execution
payload không hợp lệ, các node không bao giờ nên hạ điểm/ngắt kết nối node khác
chỉ vì những payload không hợp lệ như vậy. Điều này có mở ra khả năng bị tấn
công DoS bằng execution payload không hợp lệ, nhưng phạm vi kẻ tấn công bị giới
hạn ở các validator — những người có thể đưa payload đó vào một beacon block hợp
lệ (và slashable). Vì thế, rủi ro DoS phát sinh được
cho là chấp nhận được.

Có thể thiết kế các cơ chế phức tạp hơn để chặn payload không hợp lệ khỏi RPC.
Tuy nhiên, chưa rõ liệu sự phức tạp đó có đáng hay không.
