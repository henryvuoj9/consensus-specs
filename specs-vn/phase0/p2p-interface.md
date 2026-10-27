# Phase 0 -- Networking

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Network fundamentals](#network-fundamentals)
  - [Transport](#transport)
  - [Encryption and identification](#encryption-and-identification)
  - [Protocol negotiation](#protocol-negotiation)
  - [Multiplexing](#multiplexing)
- [Consensus-layer network interaction domains](#consensus-layer-network-interaction-domains)
  - [Types](#types)
    - [`Attnets`](#attnets)
    - [`BeaconBlockRoots`](#beaconblockroots)
    - [`ErrorMessage`](#errormessage)
    - [`NodeID`](#nodeid)
    - [`SignedBeaconBlocks`](#signedbeaconblocks)
    - [`SubnetID`](#subnetid)
  - [Constants](#constants)
  - [Configs](#configs)
  - [Helpers](#helpers)
    - [`Seen`](#seen)
    - [`compute_fork_version`](#compute_fork_version)
    - [`compute_fork_digest`](#compute_fork_digest)
    - [`is_future_slot`](#is_future_slot)
    - [`is_future_epoch`](#is_future_epoch)
    - [`is_within_slot_range`](#is_within_slot_range)
    - [`compute_attestation_subnet_prefix_bits`](#compute_attestation_subnet_prefix_bits)
    - [`compute_min_epochs_for_block_requests`](#compute_min_epochs_for_block_requests)
    - [`is_non_strict_superset`](#is_non_strict_superset)
  - [MetaData](#metadata)
  - [Maximum message sizes](#maximum-message-sizes)
    - [`max_compressed_len`](#max_compressed_len)
    - [`max_message_size`](#max_message_size)
  - [The gossip domain: gossipsub](#the-gossip-domain-gossipsub)
    - [Topics and messages](#topics-and-messages)
      - [Global topics](#global-topics)
        - [`beacon_block`](#beacon_block)
        - [`beacon_aggregate_and_proof`](#beacon_aggregate_and_proof)
        - [`voluntary_exit`](#voluntary_exit)
        - [`proposer_slashing`](#proposer_slashing)
        - [`attester_slashing`](#attester_slashing)
      - [Attestation subnets](#attestation-subnets)
        - [`beacon_attestation_{subnet_id}`](#beacon_attestation_subnet_id)
      - [Attestations and Aggregation](#attestations-and-aggregation)
    - [Encodings](#encodings)
    - [Gossipsub size limits](#gossipsub-size-limits)
  - [The Req/Resp domain](#the-reqresp-domain)
    - [Protocol identification](#protocol-identification)
    - [Req/Resp interaction](#reqresp-interaction)
      - [Requesting side](#requesting-side)
      - [Responding side](#responding-side)
    - [Encoding strategies](#encoding-strategies)
      - [SSZ-snappy encoding strategy](#ssz-snappy-encoding-strategy)
    - [Messages](#messages)
      - [Status v1](#status-v1)
      - [Goodbye v1](#goodbye-v1)
      - [BeaconBlocksByRange v1](#beaconblocksbyrange-v1)
      - [BeaconBlocksByRoot v1](#beaconblocksbyroot-v1)
      - [Ping v1](#ping-v1)
      - [GetMetaData v1](#getmetadata-v1)
  - [The discovery domain: discv5](#the-discovery-domain-discv5)
    - [Integration into libp2p stacks](#integration-into-libp2p-stacks)
    - [ENR structure](#enr-structure)
      - [Attestation subnet bitfield](#attestation-subnet-bitfield)
      - [`eth2` field](#eth2-field)
  - [Attestation subnet subscription](#attestation-subnet-subscription)
- [Design decision rationale](#design-decision-rationale)
  - [Transport](#transport-1)
    - [Why are we defining specific transports?](#why-are-we-defining-specific-transports)
    - [Can clients support other transports/handshakes than the ones mandated by the specification?](#can-clients-support-other-transportshandshakes-than-the-ones-mandated-by-the-specification)
    - [What are the advantages of using TCP/QUIC/Websockets?](#what-are-the-advantages-of-using-tcpquicwebsockets)
    - [Why do we not just support a single transport?](#why-do-we-not-just-support-a-single-transport)
    - [Why is QUIC the primary transport?](#why-is-quic-the-primary-transport)
  - [Multiplexing](#multiplexing-1)
    - [Why are we using mplex/yamux?](#why-are-we-using-mplexyamux)
  - [Protocol negotiation](#protocol-negotiation-1)
    - [When is multiselect 2.0 due and why do we plan to migrate to it?](#when-is-multiselect-20-due-and-why-do-we-plan-to-migrate-to-it)
    - [What is the difference between connection-level and stream-level protocol negotiation?](#what-is-the-difference-between-connection-level-and-stream-level-protocol-negotiation)
  - [Encryption](#encryption)
    - [Why are we not supporting SecIO?](#why-are-we-not-supporting-secio)
    - [Why are we using Noise?](#why-are-we-using-noise)
    - [Why are we using encryption at all?](#why-are-we-using-encryption-at-all)
  - [Gossipsub](#gossipsub)
    - [Why are we using a pub/sub algorithm for block and attestation propagation?](#why-are-we-using-a-pubsub-algorithm-for-block-and-attestation-propagation)
    - [Why are we using topics to segregate encodings, yet only support one encoding?](#why-are-we-using-topics-to-segregate-encodings-yet-only-support-one-encoding)
    - [How do we upgrade gossip channels (e.g. changes in encoding, compression)?](#how-do-we-upgrade-gossip-channels-eg-changes-in-encoding-compression)
    - [Why must all clients use the same gossip topic instead of one negotiated between each peer pair?](#why-must-all-clients-use-the-same-gossip-topic-instead-of-one-negotiated-between-each-peer-pair)
    - [Why are the topics strings and not hashes?](#why-are-the-topics-strings-and-not-hashes)
    - [Why are we using the `StrictNoSign` signature policy?](#why-are-we-using-the-strictnosign-signature-policy)
    - [Why are we overriding the default libp2p pubsub `message-id`?](#why-are-we-overriding-the-default-libp2p-pubsub-message-id)
    - [Why are these specific gossip parameters chosen?](#why-are-these-specific-gossip-parameters-chosen)
    - [Why is there `MAXIMUM_GOSSIP_CLOCK_DISPARITY` when validating slot ranges of messages in gossip subnets?](#why-is-there-maximum_gossip_clock_disparity-when-validating-slot-ranges-of-messages-in-gossip-subnets)
    - [Why are there `ATTESTATION_SUBNET_COUNT` attestation subnets?](#why-are-there-attestation_subnet_count-attestation-subnets)
    - [Why are attestations limited to be broadcast on gossip channels within `SLOTS_PER_EPOCH` slots?](#why-are-attestations-limited-to-be-broadcast-on-gossip-channels-within-slots_per_epoch-slots)
    - [Why are aggregate attestations broadcast to the global topic as `AggregateAndProof`s rather than just as `Attestation`s?](#why-are-aggregate-attestations-broadcast-to-the-global-topic-as-aggregateandproofs-rather-than-just-as-attestations)
    - [Why are we sending entire objects in the pubsub and not just hashes?](#why-are-we-sending-entire-objects-in-the-pubsub-and-not-just-hashes)
    - [Should clients gossip blocks if they cannot validate the proposer signature due to not yet being synced, not knowing the head block, etc?](#should-clients-gossip-blocks-if-they-cannot-validate-the-proposer-signature-due-to-not-yet-being-synced-not-knowing-the-head-block-etc)
    - [How are we going to discover peers in a gossipsub topic?](#how-are-we-going-to-discover-peers-in-a-gossipsub-topic)
    - [How should fork version be used in practice?](#how-should-fork-version-be-used-in-practice)
  - [Req/Resp](#reqresp)
    - [Why segregate requests into dedicated protocol IDs?](#why-segregate-requests-into-dedicated-protocol-ids)
    - [Why are messages length-prefixed with a protobuf varint in the SSZ-encoding?](#why-are-messages-length-prefixed-with-a-protobuf-varint-in-the-ssz-encoding)
    - [Why do we version protocol strings with ordinals instead of semver?](#why-do-we-version-protocol-strings-with-ordinals-instead-of-semver)
    - [Why is it called Req/Resp and not RPC?](#why-is-it-called-reqresp-and-not-rpc)
    - [What is a typical rate limiting strategy?](#what-is-a-typical-rate-limiting-strategy)
    - [Why do we allow empty responses in block requests?](#why-do-we-allow-empty-responses-in-block-requests)
    - [Why does `BeaconBlocksByRange` let the server choose which branch to send blocks from?](#why-does-beaconblocksbyrange-let-the-server-choose-which-branch-to-send-blocks-from)
    - [Why are `BlocksByRange` requests only required to be served for the latest `compute_min_epochs_for_block_requests()` epochs?](#why-are-blocksbyrange-requests-only-required-to-be-served-for-the-latest-compute_min_epochs_for_block_requests-epochs)
    - [Why must the proposer signature be checked when backfilling blocks in the database?](#why-must-the-proposer-signature-be-checked-when-backfilling-blocks-in-the-database)
    - [What's the effect of empty slots on the sync algorithm?](#whats-the-effect-of-empty-slots-on-the-sync-algorithm)
  - [Discovery](#discovery)
    - [Why are we using discv5 and not libp2p Kademlia DHT?](#why-are-we-using-discv5-and-not-libp2p-kademlia-dht)
    - [What is the difference between an ENR and a multiaddr, and why are we using ENRs?](#what-is-the-difference-between-an-enr-and-a-multiaddr-and-why-are-we-using-enrs)
    - [Why do we not form ENRs and find peers until genesis block/state is known?](#why-do-we-not-form-enrs-and-find-peers-until-genesis-blockstate-is-known)
  - [Compression/Encoding](#compressionencoding)
    - [Why are we using SSZ for encoding?](#why-are-we-using-ssz-for-encoding)
    - [Why are we compressing, and at which layers?](#why-are-we-compressing-and-at-which-layers)
    - [Why are we using Snappy for compression?](#why-are-we-using-snappy-for-compression)
    - [Can I get access to unencrypted bytes on the wire for debugging purposes?](#can-i-get-access-to-unencrypted-bytes-on-the-wire-for-debugging-purposes)
    - [What are SSZ type size bounds?](#what-are-ssz-type-size-bounds)
    - [Why is the message size defined in terms of application payload?](#why-is-the-message-size-defined-in-terms-of-application-payload)
    - [Why is there a limit on message sizes at all?](#why-is-there-a-limit-on-message-sizes-at-all)
- [libp2p implementations matrix](#libp2p-implementations-matrix)

<!-- mdformat-toc end -->

## Introduction

*(Giới thiệu)*

Tài liệu này chứa đặc tả mạng (networking) cho Phase 0.

Tài liệu gồm bốn phần chính:

1. Đặc tả các thành phần nền tảng của mạng.
2. Đặc tả ba *domain* (miền tương tác mạng) của consensus layer proof-of-stake:
   (a) gossip domain, (b) discovery domain, và (c) Req/Resp domain.
3. Lý do (rationale) và giải thích thêm cho các lựa chọn thiết kế ở hai phần
   trên.
4. Phân tích mức độ hoàn thiện/trạng thái của các tính năng libp2p mà đặc tả này
   yêu cầu, trên các ngôn ngữ lập trình mà các client đang được phát triển.

## Network fundamentals

*(Nền tảng mạng)*

Phần này mô tả đặc tả cho network stack trong các client consensus layer của
Ethereum.

### Transport

Mặc dù libp2p là một stack đa transport (được thiết kế để có thể lắng nghe đồng
thời trên nhiều transport và endpoint một cách trong suốt), ở đây chúng ta định
nghĩa một profile tối thiểu để các client có thể tương tác được với nhau
(interoperability).

Mọi implementation MUST hỗ trợ transport QUIC (UDP) của libp2p và transport TCP
của libp2p. Mọi transport được hỗ trợ MUST được bật cho cả việc chủ động kết nối
(dialing) lẫn lắng nghe (listening), tức là cả kết nối đi (outbound) và kết nối
đến (inbound). Các transport QUIC (UDP) và TCP của libp2p hỗ trợ lắng nghe trên
địa chỉ IPv4 và IPv6 (và có thể trên nhiều địa chỉ cùng lúc).

QUIC là transport chính. Khi một peer có thể kết nối được qua cả TCP lẫn QUIC,
client SHOULD ưu tiên địa chỉ QUIC của peer đó.

Client phải hỗ trợ lắng nghe trên ít nhất một trong hai: IPv4 hoặc IPv6. Client
nào _không_ hỗ trợ lắng nghe trên IPv4 SHOULD ý thức được các bất lợi tiềm tàng
về khả năng định tuyến/hỗ trợ trên toàn Internet. Client MAY chọn chỉ lắng nghe
trên IPv6, nhưng MUST có khả năng dial tới cả địa chỉ IPv4 và IPv6.

Mọi endpoint lắng nghe phải có thể được dial tới công khai, và do đó không được
phụ thuộc vào các cơ chế circuit relay, AutoNAT hay AutoRelay của libp2p. (Việc
sử dụng circuit relay, AutoNAT hoặc AutoRelay sẽ sớm được xem xét lại cụ thể.)

Các node chạy phía sau NAT, hoặc mặc định không thể được dial tới (ví dụ: chạy
trong container runtime, sau firewall, v.v.), MUST cấu hình hạ tầng của mình để
cho phép lưu lượng inbound đi vào endpoint lắng nghe công khai đã được công bố.

### Encryption and identification

*(Mã hóa và định danh)*

Transport QUIC được bảo mật bằng TLS 1.3, cấu hình theo
[libp2p TLS specification](https://github.com/libp2p/specs/blob/master/tls/tls.md).

Với transport TCP (transport dự phòng), handshake kênh bảo mật
[Libp2p-noise](https://github.com/libp2p/specs/tree/master/noise) với định danh
`secp256k1` sẽ được dùng để mã hóa. Như đã quy định trong đặc tả libp2p, client
MUST hỗ trợ handshake pattern `XX`.

### Protocol negotiation

*(Thương lượng giao thức)*

Client MUST dùng so sánh bằng chính xác (exact equality) khi thương lượng phiên
bản giao thức sẽ dùng, và MAY dựa vào số phiên bản để ưu tiên các phiên bản cao
hơn.

Client MUST hỗ trợ
[multistream-select 1.0](https://github.com/multiformats/multistream-select/)
và MAY hỗ trợ [multiselect 2.0](https://github.com/libp2p/specs/pull/95) khi đặc
tả đó ổn định. Khi tất cả client đều đã implement multiselect 2.0, multistream-select
1.0 MAY được loại bỏ dần.

### Multiplexing

*(Ghép kênh)*

Trong quá trình khởi tạo kết nối, libp2p thương lượng động một phương thức
multiplexing mà cả hai bên cùng hỗ trợ để có thể thực hiện nhiều "cuộc hội
thoại" song song trên cùng một kết nối. Việc này áp dụng cho các transport vốn
không tự hỗ trợ multiplexing (ví dụ TCP, WebSockets, WebRTC), và được bỏ qua với
các transport đã tự hỗ trợ (ví dụ QUIC).

Có hai multiplexer phổ biến trong các implementation libp2p:
[mplex](https://github.com/libp2p/specs/tree/master/mplex) và
[yamux](https://github.com/libp2p/specs/blob/master/yamux/README.md). Protocol ID
của chúng lần lượt là: `/mplex/6.7.0` và `/yamux/1.0.0`.

Vì transport chính QUIC tự multiplex sẵn, stream multiplexer chỉ cần thiết cho
transport dự phòng TCP. Client hỗ trợ transport TCP MUST hỗ trợ
[mplex](https://github.com/libp2p/specs/tree/master/mplex) và MAY hỗ trợ
[yamux](https://github.com/libp2p/specs/blob/master/yamux/README.md). Nếu client
hỗ trợ cả hai, yamux MUST được ưu tiên trong quá trình thương lượng. Xem phần
[Rationale](#design-decision-rationale) bên dưới để biết các đánh đổi.

## Consensus-layer network interaction domains

*(Các domain tương tác mạng của consensus layer)*

### Types

Chúng ta định nghĩa các kiểu Python tùy biến sau để hỗ trợ type hinting và giúp
code dễ đọc hơn:

#### `Attnets`

```python
class Attnets(BitVector):
    """
    The attestation subnets a node is subscribed to, one bit per subnet.
    """

    LENGTH = ATTESTATION_SUBNET_COUNT
```

#### `BeaconBlockRoots`

```python
class BeaconBlockRoots(List[Root]):
    """
    Beacon block roots requested in a ``BeaconBlocksByRoot`` request.
    """

    LIMIT = MAX_REQUEST_BLOCKS
```

#### `ErrorMessage`

```python
class ErrorMessage(List[Byte]):
    """
    The error message of an unsuccessful response chunk.
    """

    LIMIT = 256
```

#### `NodeID`

```python
class NodeID(Uint256):
    """
    A node identifier on the discovery network.
    """
```

#### `SignedBeaconBlocks`

```python
class SignedBeaconBlocks(List[SignedBeaconBlock]):
    """
    Signed beacon blocks returned in a ``BeaconBlocksByRange`` or
    ``BeaconBlocksByRoot`` response.
    """

    LIMIT = MAX_REQUEST_BLOCKS
```

#### `SubnetID`

```python
class SubnetID(Uint64):
    """
    The identifier of a gossip subnet, like an attestation subnet.
    """
```

### Constants

| Name           | Value         |
| -------------- | ------------- |
| `NODE_ID_BITS` | `Uint64(256)` |

### Configs

Phần này liệt kê các cấu hình (config) được dùng trong đặc tả này.

| Name                                 | Value                                       | Description                                                                       |
| ------------------------------------ | ------------------------------------------- | --------------------------------------------------------------------------------- |
| `MAX_PAYLOAD_SIZE`                   | `Uint64(10 * 2**20)` (= 10,485,760, 10 MiB) | Kích thước tối đa cho phép của payload chưa nén trong gossipsub message và RPC chunk |
| `MAX_REQUEST_BLOCKS`                 | `Uint64(2**10)` (= 1,024)                   | Số block tối đa trong một request                                                 |
| `EPOCHS_PER_SUBNET_SUBSCRIPTION`     | `Epoch(2**8)` (= 256)                       | Số epoch của một lần subscribe vào subnet                                         |
| `ATTESTATION_PROPAGATION_SLOT_RANGE` | `Slot(32)`                                  | Số slot tối đa mà trong khoảng đó một attestation còn được phép lan truyền        |
| `MAXIMUM_GOSSIP_CLOCK_DISPARITY`     | `Uint64(500)`                               | Độ lệch đồng hồ tối đa (tính bằng **mili giây**) được giả định giữa các node trung thực |
| `MESSAGE_DOMAIN_INVALID_SNAPPY`      | `DomainType("0x00000000")`                  | Domain 4 byte dùng để tách biệt message-id của gossip message có snappy *không hợp lệ* |
| `MESSAGE_DOMAIN_VALID_SNAPPY`        | `DomainType("0x01000000")`                  | Domain 4 byte dùng để tách biệt message-id của gossip message có snappy *hợp lệ*  |
| `SUBNETS_PER_NODE`                   | `Uint64(2)`                                 | Số subnet dài hạn (long-lived) mà một beacon node nên subscribe                   |
| `ATTESTATION_SUBNET_COUNT`           | `Uint64(2**6)` (= 64)                       | Số attestation subnet dùng trong giao thức gossipsub                              |
| `ATTESTATION_SUBNET_EXTRA_BITS`      | `Uint64(0)`                                 | Số bit bổ sung của NodeId dùng khi ánh xạ sang subnet được subscribe              |
| `MAX_CONCURRENT_REQUESTS`            | `Uint64(2)`                                 | Số request đồng thời tối đa trên mỗi protocol ID mà một client được phép gửi      |

### Helpers

#### `Seen`

Class `Seen` theo dõi trạng thái chống trùng lặp (deduplication) ở tầng mạng
phục vụ cho việc validate gossip. Nó lưu các tập hợp message đã thấy trước đó để
tránh xử lý và lan truyền lặp lại.

```python
@dataclass
class Seen:
    proposer_slots: set[tuple[Slot, ValidatorIndex]]
    aggregator_epochs: set[tuple[Epoch, ValidatorIndex]]
    aggregate_data_roots: dict[Root, set[tuple[bool, ...]]]
    voluntary_exit_indices: set[ValidatorIndex]
    proposer_slashing_indices: set[ValidatorIndex]
    attester_slashing_indices: set[ValidatorIndex]
    attestation_validator_epochs: set[tuple[Epoch, ValidatorIndex]]
```

#### `compute_fork_version`

```python
def compute_fork_version(epoch: Epoch) -> Version:  # noqa: ARG001
    """
    Return the fork version at the given ``epoch``.
    """
    return GENESIS_FORK_VERSION
```

#### `compute_fork_digest`

```python
def compute_fork_digest(
    genesis_validators_root: Root,
    epoch: Epoch,
) -> ForkDigest:
    """
    Return the 4-byte fork digest for the ``genesis_validators_root`` at a given ``epoch``.

    This is a digest primarily used for domain separation on the p2p layer.
    4-bytes suffices for practical separation of forks/chains.
    """
    fork_version = compute_fork_version(epoch)
    base_digest = compute_fork_data_root(fork_version, genesis_validators_root)
    return ForkDigest(base_digest[:4])
```

#### `is_future_slot`

```python
def is_future_slot(
    store: Store,
    slot: Slot,
    current_time_ms: Uint64,
) -> bool:
    """
    Check if the given slot is in the future
    (with MAXIMUM_GOSSIP_CLOCK_DISPARITY allowance).
    """
    slot_time_ms = compute_time_at_slot_ms(store.genesis_time_ms, slot)
    return current_time_ms + MAXIMUM_GOSSIP_CLOCK_DISPARITY < slot_time_ms
```

#### `is_future_epoch`

```python
def is_future_epoch(
    store: Store,
    epoch: Epoch,
    current_time_ms: Uint64,
) -> bool:
    """
    Check if the given epoch is in the future
    (with MAXIMUM_GOSSIP_CLOCK_DISPARITY allowance).
    """
    current_time_with_disparity_ms = current_time_ms + MAXIMUM_GOSSIP_CLOCK_DISPARITY
    current_slot = compute_slot_at_time_ms(store.genesis_time_ms, current_time_with_disparity_ms)
    return compute_epoch_at_slot(current_slot) < epoch
```

#### `is_within_slot_range`

```python
def is_within_slot_range(
    store: Store,
    slot: Slot,
    slot_range: Uint64,
    current_time_ms: Uint64,
) -> bool:
    """
    Check if the current time is within the inclusive slot range ``[slot, slot + slot_range]``
    (with MAXIMUM_GOSSIP_CLOCK_DISPARITY allowance on both ends).
    """
    start_time_ms = compute_time_at_slot_ms(store.genesis_time_ms, slot)
    if current_time_ms + MAXIMUM_GOSSIP_CLOCK_DISPARITY < start_time_ms:
        return False
    end_time_ms = compute_time_at_slot_ms(store.genesis_time_ms, slot + slot_range + 1)
    if end_time_ms + MAXIMUM_GOSSIP_CLOCK_DISPARITY < current_time_ms:
        return False
    return True
```

#### `compute_attestation_subnet_prefix_bits`

```python
def compute_attestation_subnet_prefix_bits() -> Uint64:
    """
    Return the number of NodeId bits to use when mapping to a subscribed subnet.
    """
    return ceillog2(ATTESTATION_SUBNET_COUNT) + ATTESTATION_SUBNET_EXTRA_BITS
```

#### `compute_min_epochs_for_block_requests`

```python
def compute_min_epochs_for_block_requests() -> Epoch:
    """
    Return the minimum epoch range over which a node must serve blocks.
    """
    return MIN_VALIDATOR_WITHDRAWABILITY_DELAY + CHURN_LIMIT_QUOTIENT // 2
```

#### `is_non_strict_superset`

```python
def is_non_strict_superset(
    seen_bits_set: set[tuple[bool, ...]],
    new_bits: tuple[bool, ...],
) -> bool:
    """
    Return True if any prior bitset in ``seen_bits_set`` is a non-strict
    superset of ``new_bits`` (every bit set in new is also set in that prior).
    """
    for prior_bits in seen_bits_set:
        is_superset = True
        for prior_bit, new_bit in zip(prior_bits, new_bits, strict=True):
            if new_bit and not prior_bit:
                is_superset = False
                break
        if is_superset:
            return True
    return False
```

> 💡 Ghi chú: "non-strict superset" nghĩa là tập cha không chặt (có thể bằng
> nhau). Hàm trả về `True` nếu đã từng thấy một bitset mà mọi bit được bật trong
> `new_bits` cũng đã được bật trong bitset đó — tức aggregate mới không mang
> thêm thông tin gì so với một aggregate đã thấy.

### MetaData

Client MUST lưu cục bộ `MetaData` sau:

```
(
  seq_number: Uint64
  attnets: Attnets
)
```

Trong đó

- `seq_number` là một `Uint64` bắt đầu từ `0`, dùng để đánh phiên bản metadata
  của node. Nếu bất kỳ trường nào khác trong `MetaData` cục bộ thay đổi, node MUST
  tăng `seq_number` lên 1.
- `attnets` là một `BitVector` biểu diễn các attestation subnet mà node subscribe
  lâu dài (persistent).

*Lưu ý*: `MetaData.seq_number` được dùng để đánh phiên bản metadata của node, hoàn
toàn độc lập với sequence number của ENR, và trong hầu hết trường hợp sẽ không
đồng bộ (khác giá trị) với sequence number của ENR.

### Maximum message sizes

*(Kích thước message tối đa)*

Kích thước message tối đa được suy ra từ kích thước payload tối đa mà mạng có thể
truyền tải, theo các hàm sau:

#### `max_compressed_len`

```python
def max_compressed_len(n: Uint64) -> Uint64:
    # Độ dài sau nén trong trường hợp xấu nhất cho payload kích thước n khi dùng snappy:
    # https://github.com/google/snappy/blob/32ded457c0b1fe78ceb8397632c416568d6714a0/snappy.cc#L218C1-L218C47
    return 32 + n + n // 6
```

#### `max_message_size`

```python
def max_message_size() -> Uint64:
    # Dành 1024 byte cho overhead của framing và encoding, nhưng tối thiểu là 1MiB phòng khi MAX_PAYLOAD_SIZE nhỏ.
    return max(max_compressed_len(MAX_PAYLOAD_SIZE) + 1024, Uint64(1024 * 1024))
```

### The gossip domain: gossipsub

Client MUST hỗ trợ giao thức libp2p
[gossipsub v1](https://github.com/libp2p/specs/blob/master/pubsub/gossipsub/gossipsub-v1.0.md)
bao gồm cả phần mở rộng
[gossipsub v1.1](https://github.com/libp2p/specs/blob/master/pubsub/gossipsub/gossipsub-v1.1.md).

**Protocol ID:** `/meshsub/1.1.0`

**Gossipsub Parameters** *(Tham số gossipsub)*

Các
[tham số](https://github.com/libp2p/specs/blob/master/pubsub/gossipsub/gossipsub-v1.0.md#parameters)
gossipsub sau sẽ được sử dụng:

- `D` (số peer mục tiêu trong mesh ổn định của topic): 8
- `D_low` (ngưỡng dưới của mesh ổn định của topic): 6
- `D_high` (ngưỡng trên của mesh ổn định của topic): 12
- `D_lazy` (số peer mục tiêu để gossip): 6
- `heartbeat_interval` (chu kỳ heartbeat, tính bằng giây): 0.7
- `fanout_ttl` (ttl của fanout map cho các topic mà ta không subscribe nhưng đã
  publish vào, tính bằng giây): 60
- `mcache_len` (số window giữ message đầy đủ trong cache để phục vụ phản hồi
  `IWANT`): 6
- `mcache_gossip` (số window được đem ra gossip): 3
- `seen_ttl` (thời gian hết hạn của cache chứa các message id đã thấy, tính bằng
  giây): `milliseconds_to_seconds(SLOT_DURATION_MS * SLOTS_PER_EPOCH * 2)`

*Lưu ý*: Gossipsub v1.1 bổ sung một số
[tham số mới](https://github.com/libp2p/specs/blob/master/pubsub/gossipsub/gossipsub-v1.1.md#overview-of-new-parameters)
phục vụ chấm điểm peer (peer scoring) và các biện pháp giảm thiểu tấn công khác.
Các tham số này hiện vẫn đang được nghiên cứu và sẽ được đặc tả, đưa lên mainnet
khi sẵn sàng.

#### Topics and messages

*(Topic và message)*

Topic là các chuỗi UTF-8 thuần, được mã hóa khi truyền đi theo quy định của
protobuf (gossipsub message được bọc trong protobuf message). Chuỗi topic có dạng:
`/eth2/ForkDigestValue/Name/Encoding`. Chuỗi này xác định cả kiểu data được gửi
trên topic lẫn cách mã hóa trường data của message.

- `ForkDigestValue` - các byte của
  `compute_fork_digest(genesis_validators_root, epoch)` dưới dạng hex chữ thường
  (không có tiền tố "0x"), trong đó
  - `genesis_validators_root` là `Root` cố định lấy từ
    `state.genesis_validators_root`
  - `epoch` là epoch ngữ cảnh của message sẽ được gửi trên topic
- `Name` - xem bảng bên dưới
- `Encoding` - chiến lược encoding mô tả một cách biểu diễn cụ thể của các byte
  được truyền đi. Xem phần [Encodings](#encodings) để biết thêm chi tiết.

Client MUST từ chối các message có topic không xác định.

*Lưu ý*: `ForkDigestValue` được tạo từ các giá trị chỉ biết được khi đã có
genesis block/state. Vì vậy, client SHOULD NOT subscribe vào các topic gossipsub
cho đến khi biết các giá trị genesis này.

Các trường protobuf tùy chọn `from` (1), `seqno` (3), `signature` (5) và `key`
(6) được lược bỏ khỏi message, vì message được nhận diện theo nội dung, ẩn danh,
và (khi cần) được ký ở tầng ứng dụng. Từ Gossipsub v1.1 trở đi, client MUST bắt
buộc điều này bằng cách áp dụng
[signature policy](https://github.com/libp2p/specs/blob/master/pubsub/README.md#signature-policy-options)
`StrictNoSign`.

`message-id` của một gossipsub message MUST là giá trị 20 byte sau, được tính từ
data của message:

- Nếu `message.data` giải nén snappy thành công (hợp lệ), đặt `message-id` là 20
  byte đầu tiên của hash `SHA256` của chuỗi ghép `MESSAGE_DOMAIN_VALID_SNAPPY` với
  data đã giải nén snappy, tức là
  `SHA256(MESSAGE_DOMAIN_VALID_SNAPPY + snappy_decompress(message.data))[:20]`.
- Ngược lại, đặt `message-id` là 20 byte đầu tiên của hash `SHA256` của chuỗi
  ghép `MESSAGE_DOMAIN_INVALID_SNAPPY` với data thô của message, tức là
  `SHA256(MESSAGE_DOMAIN_INVALID_SNAPPY + message.data)[:20]`.

Ở những chỗ liên quan, client MUST từ chối các message có `message-id` với kích
thước khác 20 byte.

*Lưu ý*: Logic trên xử lý hai trường hợp ngoại lệ: (1) nhiều `data` snappy khác
nhau có thể giải nén ra cùng một giá trị, và (2) một số `data` của message có thể
hoàn toàn không giải nén snappy được.

> 💡 Ghi chú: Nhờ tính `message-id` trên data *đã giải nén*, hai message có
> cùng nội dung nhưng được nén khác nhau vẫn được coi là trùng lặp. Domain khác
> nhau cho trường hợp hợp lệ/không hợp lệ đảm bảo hai loại này không bao giờ
> va chạm `message-id` với nhau.

Payload được mang trong trường `data` của gossipsub message, và thay đổi tùy theo
topic:

| Name                             | Message Type              |
| -------------------------------- | ------------------------- |
| `beacon_block`                   | `SignedBeaconBlock`       |
| `beacon_aggregate_and_proof`     | `SignedAggregateAndProof` |
| `beacon_attestation_{subnet_id}` | `Attestation`             |
| `voluntary_exit`                 | `SignedVoluntaryExit`     |
| `proposer_slashing`              | `ProposerSlashing`        |
| `attester_slashing`              | `AttesterSlashing`        |

Client MUST từ chối (đánh trượt validation) các message chứa sai kiểu hoặc
payload không hợp lệ.

Khi xử lý gossip đến, client MAY trừ điểm (descore) hoặc ngắt kết nối với các
peer không tuân thủ các ràng buộc này.

Với mọi hàng đợi (queue) tùy chọn, client SHOULD giới hạn kích thước tối đa của
hàng đợi để tránh các hướng tấn công DoS.

Gossipsub v1.1 giới thiệu
[Extended Validators](https://github.com/libp2p/specs/blob/master/pubsub/gossipsub/gossipsub-v1.1.md#extended-validators)
cho phép tầng ứng dụng hỗ trợ cơ chế chấm điểm peer của gossipsub. Chúng ta sử
dụng `ACCEPT`, `REJECT` và `IGNORE`. Với mỗi topic gossipsub có các bước
validation riêng của ứng dụng. Nếu mọi bước validation đều qua, trả về `ACCEPT`.
Nếu một hoặc nhiều bước validation thất bại trong khi kiểm tra lần lượt theo thứ
tự, trả về `REJECT` hoặc `IGNORE` như được ghi ở tiền tố của điều kiện tương ứng.

> 💡 Ghi chú: `REJECT` nghĩa là message chắc chắn không hợp lệ — peer gửi nó sẽ
> bị trừ điểm và message không được lan truyền. `IGNORE` nghĩa là message không
> được lan truyền (ví dụ do trùng lặp, chưa đủ thông tin để kiểm tra, hoặc đến
> quá sớm/muộn) nhưng peer gửi *không* bị phạt, vì peer đó có thể vẫn trung thực.

##### Global topics

*(Các topic toàn cục)*

Có hai topic toàn cục chính dùng để lan truyền beacon block (`beacon_block`) và
aggregate attestation (`beacon_aggregate_and_proof`) tới mọi node trong mạng.

Có thêm ba topic toàn cục dùng để lan truyền các message liên quan đến validator
có tần suất thấp hơn (`voluntary_exit`, `proposer_slashing` và
`attester_slashing`).

###### `beacon_block`

Topic `beacon_block` chỉ được dùng để lan truyền các signed beacon block mới tới
mọi node trong mạng. Signed block được gửi nguyên vẹn (toàn bộ nội dung).

```python
def validate_beacon_block_gossip(
    seen: Seen,
    store: Store,
    signed_beacon_block: SignedBeaconBlock,
    current_time_ms: Uint64,
) -> None:
    """
    Validate a SignedBeaconBlock for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    block = signed_beacon_block.message

    # [IGNORE] Block là block đầu tiên có chữ ký hợp lệ nhận được cho cặp (slot, proposer) này
    proposer_slot_key = (block.slot, block.proposer_index)
    if proposer_slot_key in seen.proposer_slots:
        raise GossipIgnore("block is not the first valid block for this slot and proposer")

    # [IGNORE] Block không thuộc một slot trong tương lai
    # (MAY được đưa vào hàng đợi để xử lý khi tới slot thích hợp)
    if is_future_slot(store, block.slot, current_time_ms):
        raise GossipIgnore("block is from a future slot")

    # [IGNORE] Block thuộc slot lớn hơn slot finalized mới nhất
    # (MAY chọn validate và lưu các block như vậy cho mục đích khác
    # -- ví dụ phát hiện slashing, archive node, v.v.)
    finalized_slot = compute_start_slot_at_epoch(store.finalized_checkpoint.epoch)
    if block.slot <= finalized_slot:
        raise GossipIgnore("block is not from a slot greater than the latest finalized slot")

    # [IGNORE] Block cha đã được thấy (qua gossip hoặc nguồn khác ngoài gossip)
    # (MAY được đưa vào hàng đợi cho tới khi lấy được block cha)
    if block.parent_root not in store.blocks:
        raise GossipIgnore("block's parent has not been seen")

    # [REJECT] Block cha vượt qua validation
    if block.parent_root not in store.block_states:
        raise GossipReject("block's parent is invalid")

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

    # [REJECT] Block thuộc slot cao hơn slot của block cha
    if block.slot <= store.blocks[block.parent_root].slot:
        raise GossipReject("block is not from a higher slot than its parent")

    # [REJECT] Finalized checkpoint hiện tại là tổ tiên (ancestor) của block
    finalized_epoch = store.finalized_checkpoint.epoch
    finalized_checkpoint_block = get_checkpoint_block(store, block.parent_root, finalized_epoch)
    if finalized_checkpoint_block != store.finalized_checkpoint.root:
        raise GossipReject("finalized checkpoint is not an ancestor of block")

    # [REJECT] Block được đề xuất bởi đúng proposer dự kiến của slot
    # (nếu chưa có shuffling, thay vào đó IGNORE và MAY đưa vào hàng đợi để xử lý sau)
    parent_state = store.block_states[block.parent_root].copy()
    process_slots(parent_state, block.slot)
    expected_proposer = get_beacon_proposer_index(parent_state)
    if block.proposer_index != expected_proposer:
        raise GossipReject("block proposer_index does not match expected proposer")

    # Đánh dấu block này là đã thấy
    seen.proposer_slots.add(proposer_slot_key)
```

###### `beacon_aggregate_and_proof`

Topic `beacon_aggregate_and_proof` dùng để lan truyền các attestation đã được
aggregate (dưới dạng `SignedAggregateAndProof`) tới các node đã subscribe
(thường là các validator) để được đưa vào các block trong tương lai.

```python
def validate_beacon_aggregate_and_proof_gossip(
    seen: Seen,
    store: Store,
    signed_aggregate_and_proof: SignedAggregateAndProof,
    current_time_ms: Uint64,
) -> None:
    """
    Validate a SignedAggregateAndProof for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    aggregate_and_proof = signed_aggregate_and_proof.message
    aggregate = aggregate_and_proof.aggregate
    index = aggregate.data.index
    aggregation_bits = aggregate.aggregation_bits

    # [IGNORE] Chưa từng thấy một aggregate hợp lệ có tập aggregation bits là tập cha (superset) của aggregate này
    aggregate_data_root = hash_tree_root(aggregate.data)
    aggregate_bits = tuple(bool(bit) for bit in aggregation_bits)
    seen_bits = seen.aggregate_data_roots.get(aggregate_data_root, set())
    if is_non_strict_superset(seen_bits, aggregate_bits):
        raise GossipIgnore("already seen aggregate for this data")

    # [IGNORE] Đây là aggregate hợp lệ đầu tiên cho cặp (epoch, aggregator) này
    aggregator_index = aggregate_and_proof.aggregator_index
    target_epoch = aggregate.data.target.epoch
    aggregator_epoch_key = (target_epoch, aggregator_index)
    if aggregator_epoch_key in seen.aggregator_epochs:
        raise GossipIgnore("already seen aggregate for this epoch and aggregator")

    # [IGNORE] Block được vote đã được thấy (qua gossip hoặc nguồn khác ngoài gossip)
    # (MAY được đưa vào hàng đợi cho tới khi lấy được block)
    block_root = aggregate.data.beacon_block_root
    if block_root not in store.blocks:
        raise GossipIgnore("block being voted for has not been seen")

    # [REJECT] Block được vote vượt qua validation
    if block_root not in store.block_states:
        raise GossipReject("block being voted for failed validation")

    state = store.block_states[get_head(store).root]

    # [REJECT] Committee index nằm trong phạm vi dự kiến
    committee_count = get_committee_count_per_slot(state, aggregate.data.target.epoch)
    if index >= committee_count:
        raise GossipReject("committee index out of range")

    # [IGNORE] Slot của aggregate attestation nằm trong khoảng được phép lan truyền
    # (MAY được đưa vào hàng đợi để xử lý khi tới slot thích hợp)
    if not is_within_slot_range(
        store, aggregate.data.slot, ATTESTATION_PROPAGATION_SLOT_RANGE, current_time_ms
    ):
        raise GossipIgnore("attestation slot not within propagation range")

    # [REJECT] Epoch của aggregate attestation khớp với target của nó
    if aggregate.data.target.epoch != compute_epoch_at_slot(aggregate.data.slot):
        raise GossipReject("attestation epoch does not match target epoch")

    # [REJECT] Số aggregation bits khớp với kích thước committee
    committee = get_beacon_committee(state, aggregate.data.slot, index)
    if len(aggregation_bits) != len(committee):
        raise GossipReject("aggregation bits length does not match committee size")

    # [REJECT] Aggregate attestation có ít nhất một người tham gia
    attesting_indices = get_attesting_indices(state, aggregate)
    if len(attesting_indices) < 1:
        raise GossipReject("aggregate has no participants")

    # [REJECT] Selection proof chọn validator này làm aggregator
    if not is_aggregator(state, aggregate.data.slot, index, aggregate_and_proof.selection_proof):
        raise GossipReject("validator is not selected as aggregator")

    # [REJECT] Aggregator là thành viên của committee
    if aggregator_index not in committee:
        raise GossipReject("aggregator is not a member of the committee")

    # [REJECT] Chữ ký của selection proof hợp lệ
    aggregator = state.validators[aggregator_index]
    domain = get_domain(state, DOMAIN_SELECTION_PROOF, target_epoch)
    signing_root = compute_signing_root(aggregate.data.slot, domain)
    if not bls.Verify(aggregator.pubkey, signing_root, aggregate_and_proof.selection_proof):
        raise GossipReject("invalid selection proof signature")

    # [REJECT] Chữ ký của aggregator hợp lệ
    domain = get_domain(state, DOMAIN_AGGREGATE_AND_PROOF, target_epoch)
    signing_root = compute_signing_root(aggregate_and_proof, domain)
    if not bls.Verify(aggregator.pubkey, signing_root, signed_aggregate_and_proof.signature):
        raise GossipReject("invalid aggregator signature")

    # [REJECT] Chữ ký aggregate hợp lệ
    if not is_valid_indexed_attestation(state, get_indexed_attestation(state, aggregate)):
        raise GossipReject("invalid aggregate signature")

    # [REJECT] Target block là tổ tiên của block được LMD vote
    checkpoint_block = get_checkpoint_block(store, block_root, aggregate.data.target.epoch)
    if checkpoint_block != aggregate.data.target.root:
        raise GossipReject("target block is not an ancestor of LMD vote block")

    # [IGNORE] Finalized checkpoint là tổ tiên của block
    finalized_epoch = store.finalized_checkpoint.epoch
    finalized_checkpoint_block = get_checkpoint_block(store, block_root, finalized_epoch)
    if finalized_checkpoint_block != store.finalized_checkpoint.root:
        raise GossipIgnore("finalized checkpoint is not an ancestor of block")

    # Đánh dấu aggregate này là đã thấy
    seen.aggregator_epochs.add(aggregator_epoch_key)
    if aggregate_data_root not in seen.aggregate_data_roots:
        seen.aggregate_data_roots[aggregate_data_root] = set()
    seen.aggregate_data_roots[aggregate_data_root].add(aggregate_bits)
```

###### `voluntary_exit`

Topic `voluntary_exit` chỉ được dùng để lan truyền các yêu cầu exit tự nguyện
(voluntary exit) đã ký của validator tới các proposer trong mạng. Signed
voluntary exit được gửi nguyên vẹn.

```python
def validate_voluntary_exit_gossip(
    seen: Seen,
    store: Store,
    signed_voluntary_exit: SignedVoluntaryExit,
    current_time_ms: Uint64,
) -> None:
    """
    Validate a SignedVoluntaryExit for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    voluntary_exit = signed_voluntary_exit.message
    validator_index = voluntary_exit.validator_index

    # [IGNORE] Đây là voluntary exit hợp lệ đầu tiên nhận được cho validator này
    if validator_index in seen.voluntary_exit_indices:
        raise GossipIgnore("already seen voluntary exit for this validator")

    # [IGNORE] Epoch của voluntary exit không nằm trong tương lai
    if is_future_epoch(store, voluntary_exit.epoch, current_time_ms):
        raise GossipIgnore("voluntary exit epoch is in the future")

    state = store.block_states[get_head(store).root]

    # [REJECT] Validator index hợp lệ
    if validator_index >= len(state.validators):
        raise GossipReject("validator index out of range")

    validator = state.validators[validator_index]
    current_epoch = get_current_epoch(state)

    # [IGNORE] Validator chưa khởi tạo exit trước đó
    if validator.exit_epoch != FAR_FUTURE_EPOCH:
        raise GossipIgnore("validator has already initiated exit")

    # [REJECT] Validator đang active
    if not is_active_validator(validator, current_epoch):
        raise GossipReject("validator is not active")

    # [REJECT] Validator đã active đủ lâu
    if current_epoch < validator.activation_epoch + SHARD_COMMITTEE_PERIOD:
        raise GossipReject("validator has not been active long enough")

    # [REJECT] Chữ ký hợp lệ
    domain = get_domain(state, DOMAIN_VOLUNTARY_EXIT, voluntary_exit.epoch)
    signing_root = compute_signing_root(voluntary_exit, domain)
    if not bls.Verify(validator.pubkey, signing_root, signed_voluntary_exit.signature):
        raise GossipReject("invalid voluntary exit signature")

    # Đánh dấu voluntary exit này là đã thấy
    seen.voluntary_exit_indices.add(validator_index)
```

###### `proposer_slashing`

Topic `proposer_slashing` chỉ được dùng để lan truyền các proposer slashing (bằng
chứng proposer vi phạm, dùng để phạt cắt giảm stake) tới các proposer trong mạng.
Proposer slashing được gửi nguyên vẹn.

```python
def validate_proposer_slashing_gossip(
    seen: Seen,
    store: Store,
    proposer_slashing: ProposerSlashing,
) -> None:
    """
    Validate a ProposerSlashing for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    header_1 = proposer_slashing.signed_header_1.message
    header_2 = proposer_slashing.signed_header_2.message
    proposer_index = header_1.proposer_index

    # [IGNORE] Đây là proposer slashing hợp lệ đầu tiên nhận được cho proposer này
    if proposer_index in seen.proposer_slashing_indices:
        raise GossipIgnore("already seen proposer slashing for this proposer")

    # [REJECT] Slot của hai header trùng nhau
    if header_1.slot != header_2.slot:
        raise GossipReject("header slots do not match")

    # [REJECT] Proposer index của hai header trùng nhau
    if header_1.proposer_index != header_2.proposer_index:
        raise GossipReject("header proposer indices do not match")

    # [REJECT] Hai header khác nhau
    if header_1 == header_2:
        raise GossipReject("headers are not different")

    state = store.block_states[get_head(store).root]

    # [REJECT] Proposer index là một validator index hợp lệ
    if proposer_index >= len(state.validators):
        raise GossipReject("proposer index out of range")

    # [REJECT] Proposer có thể bị slash (slashable)
    proposer = state.validators[proposer_index]
    if not is_slashable_validator(proposer, get_current_epoch(state)):
        raise GossipReject("proposer is not slashable")

    # [REJECT] Các chữ ký hợp lệ
    for signed_header in (proposer_slashing.signed_header_1, proposer_slashing.signed_header_2):
        domain = get_domain(
            state, DOMAIN_BEACON_PROPOSER, compute_epoch_at_slot(signed_header.message.slot)
        )
        signing_root = compute_signing_root(signed_header.message, domain)
        if not bls.Verify(proposer.pubkey, signing_root, signed_header.signature):
            raise GossipReject("invalid proposer slashing signature")

    # Đánh dấu proposer slashing này là đã thấy
    seen.proposer_slashing_indices.add(proposer_index)
```

###### `attester_slashing`

Topic `attester_slashing` chỉ được dùng để lan truyền các attester slashing tới
các proposer trong mạng. Attester slashing được gửi nguyên vẹn.

```python
def validate_attester_slashing_gossip(
    seen: Seen,
    store: Store,
    attester_slashing: AttesterSlashing,
) -> None:
    """
    Validate an AttesterSlashing for gossip propagation.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    attestation_1 = attester_slashing.attestation_1
    attestation_2 = attester_slashing.attestation_2

    attesting_indices_1 = set(attestation_1.attesting_indices)
    attesting_indices_2 = set(attestation_2.attesting_indices)
    slashable_indices = attesting_indices_1.intersection(attesting_indices_2)

    # [IGNORE] Có ít nhất một index trong phần giao (intersection) chưa từng được thấy
    new_indices = slashable_indices.difference(seen.attester_slashing_indices)
    if len(new_indices) == 0:
        raise GossipIgnore("all attester slashing indices already seen")

    # [REJECT] Attestation data là slashable (double vote hoặc surround vote)
    if not is_slashable_attestation_data(attestation_1.data, attestation_2.data):
        raise GossipReject("attestation data is not slashable")

    state = store.block_states[get_head(store).root]

    # [REJECT] Mọi validator index trong indexed attestation thứ nhất đều hợp lệ
    if any(index >= len(state.validators) for index in attestation_1.attesting_indices):
        raise GossipReject("validator index out of range in indexed attestation 1")

    # [REJECT] Indexed attestation thứ nhất có các thuộc tính hợp lệ
    if not is_valid_indexed_attestation(state, attestation_1):
        raise GossipReject("invalid indexed attestation 1")

    # [REJECT] Mọi validator index trong indexed attestation thứ hai đều hợp lệ
    if any(index >= len(state.validators) for index in attestation_2.attesting_indices):
        raise GossipReject("validator index out of range in indexed attestation 2")

    # [REJECT] Indexed attestation thứ hai có các thuộc tính hợp lệ
    if not is_valid_indexed_attestation(state, attestation_2):
        raise GossipReject("invalid indexed attestation 2")

    # [REJECT] Có ít nhất một validator trong phần giao là slashable
    slashable_any = False
    current_epoch = get_current_epoch(state)
    for index in slashable_indices:
        if is_slashable_validator(state.validators[index], current_epoch):
            slashable_any = True
            break
    if not slashable_any:
        raise GossipReject("no slashable validators in intersection")

    # Đánh dấu các index này là đã thấy
    seen.attester_slashing_indices.update(slashable_indices)
```

##### Attestation subnets

Attestation subnet được dùng để lan truyền các attestation chưa aggregate
(unaggregated) tới từng phân vùng nhỏ của mạng.

###### `beacon_attestation_{subnet_id}`

Các topic `beacon_attestation_{subnet_id}` dùng để lan truyền các attestation
chưa aggregate tới subnet `subnet_id` (thường là các beacon committee và
persistent committee) để được aggregate trước khi được gossip lên topic
`beacon_aggregate_and_proof`.

```python
def validate_beacon_attestation_gossip(
    seen: Seen,
    store: Store,
    attestation: Attestation,
    current_time_ms: Uint64,
    subnet_id: SubnetID,
) -> None:
    """
    Validate an Attestation for gossip propagation on a subnet.
    Raises GossipIgnore or GossipReject on validation failure.
    """
    data = attestation.data
    committee_index = data.index
    target_epoch = data.target.epoch
    aggregation_bits = attestation.aggregation_bits

    # [IGNORE] Block được vote đã được thấy (qua gossip hoặc nguồn khác ngoài gossip)
    # (MAY được đưa vào hàng đợi cho tới khi lấy được block)
    block_root = data.beacon_block_root
    if block_root not in store.blocks:
        raise GossipIgnore("block being voted for has not been seen")

    # [REJECT] Block được vote vượt qua validation
    if block_root not in store.block_states:
        raise GossipReject("block being voted for failed validation")

    state = store.block_states[get_head(store).root]

    # [REJECT] Committee index nằm trong phạm vi dự kiến
    committees_per_slot = get_committee_count_per_slot(state, target_epoch)
    if committee_index >= committees_per_slot:
        raise GossipReject("committee index out of range")

    # [REJECT] Attestation được gửi đúng subnet
    expected_subnet = compute_subnet_for_attestation(
        committees_per_slot, data.slot, committee_index
    )
    if expected_subnet != subnet_id:
        raise GossipReject("attestation is for wrong subnet")

    # [IGNORE] Slot của attestation nằm trong khoảng được phép lan truyền
    # (MAY được đưa vào hàng đợi để xử lý khi tới slot thích hợp)
    if not is_within_slot_range(
        store, data.slot, ATTESTATION_PROPAGATION_SLOT_RANGE, current_time_ms
    ):
        raise GossipIgnore("attestation slot not within propagation range")

    # [REJECT] Epoch của attestation khớp với target của nó
    if target_epoch != compute_epoch_at_slot(data.slot):
        raise GossipReject("attestation epoch does not match target epoch")

    # [REJECT] Attestation chưa được aggregate (có đúng một bit được bật)
    num_bits_set = get_set_bit_count(aggregation_bits)
    if num_bits_set != 1:
        raise GossipReject("attestation is not unaggregated")

    # [REJECT] Số aggregation bits khớp với kích thước committee
    committee = get_beacon_committee(state, data.slot, committee_index)
    if len(aggregation_bits) != len(committee):
        raise GossipReject("aggregation bits length does not match committee size")

    # [IGNORE] Chưa thấy attestation hợp lệ nào khác cho cặp (target epoch, validator) này
    set_bit_indices = [index for index, bit in enumerate(aggregation_bits) if bit]
    participant_index = committee[set_bit_indices[0]]
    attestation_epoch_key = (target_epoch, participant_index)
    if attestation_epoch_key in seen.attestation_validator_epochs:
        raise GossipIgnore("already seen attestation for this epoch and validator")

    # [REJECT] Chữ ký của attestation hợp lệ
    indexed_attestation = get_indexed_attestation(state, attestation)
    if not is_valid_indexed_attestation(state, indexed_attestation):
        raise GossipReject("invalid attestation signature")

    # [REJECT] Target block của attestation là tổ tiên của block được LMD vote
    target_checkpoint_block = get_checkpoint_block(store, block_root, target_epoch)
    if target_checkpoint_block != data.target.root:
        raise GossipReject("target block is not an ancestor of LMD vote block")

    # [IGNORE] finalized_checkpoint hiện tại là tổ tiên của block
    finalized_epoch = store.finalized_checkpoint.epoch
    finalized_checkpoint_block = get_checkpoint_block(store, block_root, finalized_epoch)
    if finalized_checkpoint_block != store.finalized_checkpoint.root:
        raise GossipIgnore("finalized checkpoint is not an ancestor of block")

    # Đánh dấu attestation này là đã thấy
    seen.attestation_validator_epochs.add(attestation_epoch_key)
```

##### Attestations and Aggregation

*(Attestation và aggregation)*

Việc broadcast attestation được chia nhóm theo các subnet, mỗi subnet ứng với một
topic. Số lượng subnet được quy định bởi `ATTESTATION_SUBNET_COUNT`. Subnet đúng
cho một attestation có thể được tính bằng `compute_subnet_for_attestation`. Các
topic `beacon_attestation_{subnet_id}` được luân phiên (rotate) trong suốt epoch,
tương tự như cách luân phiên qua các shard trong committee (ở một bản nâng cấp
beacon chain trong tương lai). Các subnet được luân phiên với
`committees_per_slot = get_committee_count_per_slot(state, attestation.data.target.epoch)`
subnet cho mỗi slot.

Attestation chưa aggregate được gửi dưới dạng `Attestation` tới subnet topic
`beacon_attestation_{compute_subnet_for_attestation(committees_per_slot, attestation.data.slot, attestation.data.index)}`
dưới dạng `Attestation`.

Attestation đã aggregate được gửi tới topic `beacon_aggregate_and_proof` dưới
dạng `AggregateAndProof`.

#### Encodings

Topic có hậu tố là tên encoding. Encoding quy định cách payload của gossipsub
message được mã hóa.

- `ssz_snappy` - Mọi object được mã hóa SSZ rồi nén bằng block compression của
  [Snappy](https://github.com/google/snappy). Ví dụ: chuỗi topic của beacon
  aggregate attestation là `/eth2/446a7232/beacon_aggregate_and_proof/ssz_snappy`,
  fork digest là `446a7232` và trường data của gossipsub message là một
  `AggregateAndProof` đã được mã hóa SSZ rồi nén bằng Snappy.

Snappy có hai định dạng: "block" và "frames" (streaming). Gossip message tương
đối nhỏ (từ vài trăm byte đến vài trăm kilobyte) nên dùng
[basic snappy block compression](https://github.com/google/snappy/blob/master/format_description.txt)
để tránh overhead bổ sung đi kèm với snappy frames.

Các implementation MUST dùng một encoding duy nhất cho gossip. Việc thay đổi
encoding sẽ đòi hỏi sự phối hợp giữa các implementation tham gia mạng.

#### Gossipsub size limits

*(Giới hạn kích thước gossipsub)*

Giới hạn kích thước được áp dụng cho cả frame
[`RPCMsg`](https://github.com/libp2p/specs/blob/b5f7fce29b32d4c7d0efe37b019936a11e5db872/pubsub/README.md#the-rpc)
lẫn payload đã mã hóa trong mỗi
[`Message`](https://github.com/libp2p/specs/blob/b5f7fce29b32d4c7d0efe37b019936a11e5db872/pubsub/README.md#the-message).

Client MUST từ chối, và MUST NOT phát ra hay lan truyền, các message có kích thước
vượt quá các giới hạn sau:

- Kích thước của `RPCMsg` đã mã hóa (bao gồm control message, framing, topic,
  v.v.) không được vượt quá `max_message_size()`.
- Kích thước của payload đã nén trong trường `Message.data` không được vượt quá
  `max_compressed_len(MAX_PAYLOAD_SIZE)`.
- Kích thước của payload chưa nén không được vượt quá giá trị nhỏ hơn giữa
  `MAX_PAYLOAD_SIZE` và [giới hạn SSZ theo từng kiểu](#what-are-ssz-type-size-bounds).

### The Req/Resp domain

#### Protocol identification

Mỗi loại message được tách riêng thành một libp2p protocol ID của chính nó. Protocol ID là
một chuỗi UTF-8 phân biệt chữ hoa/chữ thường, có dạng:

```
/ProtocolPrefix/MessageName/SchemaVersion/Encoding
```

Trong đó:

- `ProtocolPrefix` - các message được gom thành từng nhóm, mỗi nhóm được nhận diện bằng
  một tiền tố tên protocol libp2p dùng chung. Ở đây ta dùng `/eth2/beacon_chain/req`.
- `MessageName` - mỗi request được nhận diện bằng một tên gồm các chữ cái tiếng Anh,
  chữ số và dấu gạch dưới (`_`).
- `SchemaVersion` - số phiên bản theo thứ tự (ví dụ 1, 2, 3…). Mỗi schema đều được
  đánh phiên bản để hỗ trợ tương thích ngược và tương thích về sau khi có thể.
- `Encoding` - trong khi schema định nghĩa các kiểu dữ liệu ở mức trừu tượng, thì
  chiến lược encoding mô tả cách biểu diễn cụ thể thành các byte sẽ được truyền đi
  trên đường truyền. Xem mục [Encodings](#encoding-strategies) để biết thêm chi tiết.

Việc tách protocol như vậy cho phép libp2p `multistream-select 1.0` /
`multiselect 2.0` xử lý việc thương lượng loại request, phiên bản và encoding
trước khi thiết lập các stream bên dưới.

#### Req/Resp interaction

Ta dùng MỘT stream cho MỖI lượt tương tác request/response. Stream được đóng lại khi
lượt tương tác kết thúc, dù thành công hay lỗi.

Các message request/response MUST tuân theo encoding được chỉ định trong tên protocol
và theo cấu trúc sau (ngữ pháp BNF dạng nới lỏng):

```
request   ::= <encoding-dependent-header> | <encoded-payload>
response  ::= <response_chunk>*
response_chunk  ::= <result> | <encoding-dependent-header> | <encoded-payload>
result    ::= “0” | “1” | “2” | "3" | [“128” ... ”255”]
```

Header phụ thuộc encoding (encoding-dependent header) có thể mang metadata hoặc các
khẳng định (assertion), chẳng hạn độ dài của payload đã encode, nhằm đảm bảo tính toàn
vẹn và chống tấn công. Vì các stream req/resp chỉ dùng một lần và việc đóng stream đã
ngầm đánh dấu ranh giới dữ liệu, nên về nguyên tắc không bắt buộc phải thêm tiền tố độ
dài cho payload; tuy nhiên, một số encoding như SSZ vẫn làm vậy để tăng tính an toàn.

Một `response` gồm không hoặc nhiều `response_chunk`. Các response chỉ gồm một
SSZ-list duy nhất (như `BlocksByRange` và `BlocksByRoot`) sẽ gửi mỗi phần tử của list
thành một `response_chunk` riêng. Mọi loại response khác (không phải List) gửi đúng một
`response_chunk`.

Với cả `request` lẫn `response`, `encoding-dependent-header` MUST hợp lệ, và
`encoded-payload` phải hợp lệ trong phạm vi ràng buộc của `encoding-dependent-header`.
Điều này bao gồm cả các giới hạn kích thước payload theo từng kiểu dữ liệu đối với một số
chiến lược encoding. Bất kể các giới hạn theo kiểu đó, một giới hạn toàn cục về kích thước
tối đa (tính theo byte chưa nén) là `MAX_PAYLOAD_SIZE` MUST được áp dụng cho mọi
response chunk của mọi method.

Client MUST đảm bảo các độ dài nằm trong những giới hạn này; nếu không, client SHOULD
reset stream ngay lập tức. Client có theo dõi uy tín (reputation) của peer MAY trừ điểm
của peer có hành vi sai trong trường hợp này.

##### Requesting side

Khi một stream mới với protocol ID tương ứng loại request đã được thương lượng xong,
toàn bộ message request SHOULD được gửi ngay lập tức. Request MUST được encode theo
chiến lược encoding.

Bên gửi request MUST đóng phía ghi (write side) của stream ngay khi ghi xong message
request. Lúc này stream ở trạng thái đóng một nửa (half-closed).

Bên gửi request MUST NOT gửi đồng thời nhiều hơn `MAX_CONCURRENT_REQUESTS` request
với cùng một protocol ID.

Nếu xảy ra timeout hoặc response không còn cần thiết nữa, bên gửi request SHOULD reset
stream.

Bên gửi request SHOULD đọc từ stream cho đến khi xảy ra một trong các trường hợp:

1. Nhận được kết quả lỗi trong một chunk nào đó (payload lỗi MAY được đọc trước khi
   dừng).
2. Bên phản hồi đóng stream.
3. Bất kỳ phần nào của `response_chunk` không vượt qua bước kiểm tra hợp lệ.
4. Đã đọc đủ số lượng chunk tối đa đã yêu cầu.

Với các request mà response chỉ gồm một `response_chunk` hợp lệ duy nhất, bên gửi
request SHOULD đọc trọn vẹn chunk đó (theo định nghĩa của `encoding-dependent-header`)
trước khi đóng stream.

##### Responding side

Khi một stream mới với protocol ID tương ứng loại request đã được thương lượng xong,
bên phản hồi SHOULD xử lý request đến và MUST kiểm tra tính hợp lệ của nó trước khi xử
lý. Việc xử lý và kiểm tra request MUST được thực hiện theo chiến lược encoding, cho
đến khi gặp EOF (biểu thị bên gửi request đã đóng một nửa stream).

Bên phản hồi MUST:

1. Dùng chiến lược encoding để đọc header (nếu có).
2. Nếu có khẳng định độ dài là `N`, nó nên đọc đúng `N` byte từ stream, và tại thời điểm
   đó phải gặp EOF (không còn byte nào nữa). Nếu không đúng như vậy, phải coi đó là lỗi.
3. Deserialize thành kiểu dữ liệu mong đợi và xử lý request.
4. Ghi response, có thể gồm không hoặc nhiều `response_chunk` (result, header tùy
   chọn, payload).
5. Đóng phía ghi của stream. Lúc này stream được đóng hoàn toàn.

Nếu bước (1), (2) hoặc (3) thất bại do dữ liệu không hợp lệ, sai định dạng hoặc không
nhất quán, bên phản hồi MUST trả về lỗi. Client có theo dõi uy tín của peer MAY ghi nhận
các lỗi như vậy, cũng như các sự kiện bất thường, ví dụ stream bị reset sớm.

Bên phản hồi MAY giới hạn tốc độ (rate-limit) các chunk bằng cách giữ lại từng chunk cho
đến khi có đủ năng lực xử lý. Bên phản hồi MUST NOT trả về lỗi hoặc đóng stream khi đang
rate limit.

Khi rate limit, bên phản hồi MUST gửi trọn vẹn mỗi `response_chunk` một cách nhanh chóng,
nhưng có thể chèn độ trễ giữa các chunk.

> 💡 Ghi chú: Nói cách khác, độ trễ chỉ được phép nằm *giữa* các chunk; một chunk khi đã
> bắt đầu gửi thì phải được gửi hết ngay, không được "nhỏ giọt" từng phần.

Mỗi chunk bắt đầu bằng một response code dài **một byte**, quyết định nội dung của
`response_chunk` (thành phần `result` trong ngữ pháp BNF ở trên). Khi có nhiều chunk, chỉ
chunk cuối cùng được phép có mã lỗi khác không (tức là chuỗi chunk sẽ kết thúc ngay khi
xảy ra lỗi).

Response code có thể nhận một trong các giá trị sau, được encode dưới dạng một byte
không dấu:

- 0: **Success** -- tiếp theo là một response bình thường, với nội dung khớp với schema
  message mong đợi và encoding đã chỉ định trong request.
- 1: **InvalidRequest** -- nội dung request không hợp lệ về mặt ngữ nghĩa, hoặc payload
  sai định dạng, hoặc không thể hiểu được. Payload của response tuân theo schema (mô tả
  bên dưới).
- 2: **ServerError** -- bên phản hồi gặp lỗi trong khi xử lý request. Payload của response
  tuân theo schema (mô tả bên dưới).
- 3: **ResourceUnavailable** -- bên phản hồi không có tài nguyên được yêu cầu. Payload của
  response tuân theo schema (mô tả bên dưới). *Lưu ý*: Response code này chỉ hợp lệ ở
  những nơi được chỉ định rõ.

Client MAY dùng các response code lớn hơn `128` để biểu thị các response lỗi khác, đặc
thù cho từng loại request.

Khoảng `[4, 127]` được DÀNH RIÊNG (RESERVED) cho mục đích sử dụng trong tương lai, và nên
được coi là lỗi nếu không được nhận diện một cách rõ ràng.

```
(
  error_message: ErrorMessage
)
```

*Lưu ý*: Theo quy ước, `error_message` là một chuỗi byte MAY được diễn giải như một chuỗi
UTF-8 (phục vụ mục đích debug). Client MUST coi mọi chuỗi byte là hợp lệ.

Bên phản hồi MAY phạt các peer mở đồng thời nhiều hơn `MAX_CONCURRENT_REQUESTS` stream
cho cùng một loại request, đối với các protocol ID được định nghĩa trong spec này.

#### Encoding strategies

Token (phần cuối) của protocol ID đã thương lượng chỉ định loại encoding được dùng cho
tương tác req/resp. Hiện tại chỉ có một giá trị khả dụng:

- `ssz_snappy`: Nội dung trước tiên được encode bằng SSZ, sau đó được nén theo định dạng
  frames của [Snappy](https://github.com/google/snappy). Với các đối tượng chỉ chứa một
  field, chỉ riêng field đó được SSZ-encode chứ không phải một container có một field. Ví
  dụ, request `BeaconBlocksByRoot` là một list các `Root` được SSZ-encode. Loại encoding
  này MUST được mọi client hỗ trợ.

##### SSZ-snappy encoding strategy

[SimpleSerialize (SSZ) specification](https://github.com/ethereum/ssz-specs) mô tả cách
các đối tượng được SSZ-encode.

Để có encoding snappy chồng lên SSZ, khi encode ta đưa dạng đã serialize của đối tượng
vào bộ nén Snappy. Khi decode thì làm ngược lại.

Snappy có hai định dạng: "block" và "frames" (streaming). Để hỗ trợ các request và
response chunk lớn, ta dùng snappy-framing.

Vì nội dung mỗi snappy frame
[có kích thước tối đa `65536` byte](https://github.com/google/snappy/blob/master/framing_format.txt#L104)
và header của frame chỉ gồm `identifier (1) + checksum (4)` byte, nên việc phải đệm
(buffer) một frame đơn lẻ là chấp nhận được.

**Encoding-dependent header:** Các protocol Req/Resp dùng chiến lược encoding
`ssz_snappy` MUST encode độ dài của dữ liệu SSZ thô (chưa nén) dưới dạng một
[protobuf varint](https://developers.google.com/protocol-buffers/docs/encoding#varints)
không dấu.

*Ghi (Writing)*: Bằng cách tính và ghi độ dài byte SSZ trước, SSZ encoder sau đó có thể
ghi trực tiếp nội dung chunk vào stream. Khi áp dụng Snappy, dữ liệu có thể được chuyển
qua một Snappy writer có buffer để nén từng frame một.

*Đọc (Reading)*: Sau khi đọc được độ dài byte SSZ mong đợi, SSZ decoder có thể đọc trực
tiếp nội dung từ stream. Khi áp dụng snappy, dữ liệu có thể được chuyển qua một Snappy
reader có buffer để giải nén từng frame một.

Trước khi đọc payload, header MUST được kiểm tra hợp lệ:

- Tiền tố độ dài (length-prefix) MUST được encode dưới dạng protobuf varint không dấu. Nó
  SHOULD được encode ở dạng tối thiểu (tức là không có byte thừa) và MUST not dài quá 10
  byte, đủ để biểu diễn bất kỳ giá trị `Uint64` nào. Length-prefix MUST được decode vào
  một kiểu dữ liệu hỗ trợ toàn bộ miền giá trị của `Uint64`.
- Length-prefix nằm trong
  [giới hạn kích thước suy ra từ kiểu SSZ của payload](#what-are-ssz-type-size-bounds)
  hoặc `MAX_PAYLOAD_SIZE`, lấy giá trị nhỏ hơn.

Sau khi đọc được một header hợp lệ, payload MAY được đọc, đồng thời vẫn phải tuân thủ các
ràng buộc kích thước từ header.

Bên đọc MUST NOT đọc nhiều hơn `max_compressed_len(n)` byte sau khi đã đọc length-prefix
SSZ `n` từ header.

> 💡 Ghi chú: `n` là độ dài dữ liệu *chưa nén*, còn `max_compressed_len(n)` là số byte tối
> đa mà dữ liệu dài `n` có thể chiếm sau khi nén bằng Snappy (trường hợp xấu nhất). Giới
> hạn này ngăn peer gửi luồng dữ liệu nén dài vô hạn.

Bên đọc MUST coi các trường hợp sau là input không hợp lệ:

- Còn byte thừa sau khi đã đọc đủ `n` byte SSZ. Phải gặp EOF nếu cố đọc thêm byte quá
  mức cần thiết.
- Gặp EOF sớm, trước khi đọc đủ số byte SSZ như length-prefix đã khai báo.

Trong trường hợp input không hợp lệ (header hoặc payload), bên đọc MUST:

- Nếu là request: gửi lại một message lỗi với response code `InvalidRequest`. Bản thân
  request đó bị bỏ qua.
- Nếu là response: bỏ qua response, và response đó MUST được coi là hành vi sai của
  server.

Mọi message chỉ chứa một field duy nhất MUST được encode trực tiếp theo kiểu của field đó
và MUST NOT được encode dưới dạng một SSZ container.

Các response là SSZ-list (ví dụ `SignedBeaconBlocks`) gửi từng phần tử của nó riêng lẻ
dưới dạng các `response_chunk`. Ví dụ, loại response `SignedBeaconBlocks` gửi không hoặc
nhiều `response_chunk`. Mỗi `response_chunk` _thành công_ chứa một payload
`SignedBeaconBlock` duy nhất.

#### Messages

##### Status v1

**Protocol ID:** `/eth2/beacon_chain/req/status/1/`

Nội dung Request, Response:

```
(
  fork_digest: ForkDigest
  finalized_root: Root
  finalized_epoch: Epoch
  head_root: Root
  head_slot: Slot
)
```

Theo góc nhìn của client tại thời điểm gửi message:

- `fork_digest`: `ForkDigest` của node
  (`compute_fork_digest(genesis_validators_root, epoch)`), trong đó
  - `genesis_validators_root` là `Root` cố định nằm trong
    `state.genesis_validators_root`
  - `epoch` là epoch hiện tại của node, xác định theo thời gian thực (wall-clock), không
    nhất thiết là epoch mà node đã sync tới.
- `finalized_root`: `store.finalized_checkpoint.root` theo
  [fork choice](./fork-choice.md). (Lưu ý giá trị này mặc định là `Root(b'\x00' * 32)`
  đối với finalized checkpoint tại genesis).
- `finalized_epoch`: `store.finalized_checkpoint.epoch` theo
  [fork choice](./fork-choice.md).
- `head_root`: root `hash_tree_root` của head block hiện tại (`BeaconBlock`).
- `head_slot`: slot của block tương ứng với `head_root`.

Client chủ động quay số kết nối (dialing client) MUST gửi request `Status` ngay khi kết
nối.

Request/response MUST được encode dưới dạng SSZ-container.

Response MUST gồm đúng một `response_chunk`.

Sau handshake ở trên, các client SHOULD ngắt kết nối với nhau ngay lập tức trong các
trường hợp sau:

1. Nếu `fork_digest` không khớp với `fork_digest` cục bộ của node, vì chain của client
   kia đang ở một fork khác.
2. Nếu cặp (`finalized_root`, `finalized_epoch`) mà peer chia sẻ không nằm trên chain của
   client tại epoch tương ứng. Ví dụ, nếu Peer 1 gửi (root, epoch) là (A, 5) và Peer 2
   gửi (B, 3), nhưng Peer 1 có root C tại epoch 3, thì Peer 1 sẽ ngắt kết nối vì biết
   rằng hai chain đã tách rời nhau và không thể hợp nhất lại.

Khi handshake hoàn tất, client có `finalized_epoch` thấp hơn, hoặc có `head_slot` thấp
hơn (nếu hai client có `finalized_epoch` bằng nhau), SHOULD yêu cầu các beacon block từ
phía bên kia thông qua request `BeaconBlocksByRange`.

*Lưu ý*: Trong điều kiện mạng bất thường hoặc sau vài lượt request
`BeaconBlocksByRange`, client có thể cần gửi lại request `Status` để biết peer có head
cao hơn hay không. Người triển khai được tự do hiện thực hành vi này theo cách riêng.

##### Goodbye v1

**Protocol ID:** `/eth2/beacon_chain/req/goodbye/1/`

Nội dung Request, Response:

```
(
  Uint64
)
```

Client MAY gửi message goodbye khi ngắt kết nối. Trường lý do (reason) MAY là một trong
các giá trị sau:

- 1: Client tắt (shut down).
- 2: Mạng không liên quan (irrelevant network, ví dụ khác chain/fork).
- 3: Lỗi (fault/error).

Client MAY dùng các reason code lớn hơn `128` để biểu thị các response lỗi khác, đặc thù
cho từng loại request.

Khoảng `[4, 127]` được DÀNH RIÊNG (RESERVED) cho mục đích sử dụng trong tương lai.

Request/response MUST được encode dưới dạng một SSZ-field đơn.

Response MUST gồm đúng một `response_chunk`.

##### BeaconBlocksByRange v1

**Protocol ID:** `/eth2/beacon_chain/req/beacon_blocks_by_range/1/`

Nội dung Request:

```
(
  start_slot: Slot
  count: Uint64
  step: Uint64 # Deprecated, must be set to 1
)
```

Nội dung Response:

```
(
  SignedBeaconBlocks
)
```

Yêu cầu các beacon block trong khoảng slot `[start_slot, start_slot + count)`, dẫn tới
head block hiện tại do fork choice chọn. Ví dụ, yêu cầu các block bắt đầu từ
`start_slot=2` với `count=4` sẽ trả về các block tại các slot `[2, 3, 4, 5]`. Nếu một slot
nào đó trống (không có block), sẽ không có block nào được trả về cho slot đó. Ví dụ, nếu
slot 4 trong ví dụ trước bị trống, mảng trả về sẽ chứa `[2, 3, 5]`.

`step` đã bị deprecated và phải được đặt bằng 1. Client có thể phản hồi bằng một block
duy nhất nếu nhận được step lớn hơn trong giai đoạn chuyển tiếp deprecation.

`/eth2/beacon_chain/req/beacon_blocks_by_range/1/` đã bị deprecated. Client MAY phản
hồi bằng một list rỗng trong giai đoạn chuyển tiếp deprecation.

`BeaconBlocksByRange` chủ yếu được dùng để sync các block lịch sử.

Request MUST được encode dưới dạng SSZ-container.

Response MUST gồm không hoặc nhiều `response_chunk`. Mỗi `response_chunk` _thành công_
MUST chứa một payload `SignedBeaconBlock` duy nhất.

Client MUST lưu giữ các signed block đã thấy trong khoảng epoch
`[max(GENESIS_EPOCH, current_epoch - compute_min_epochs_for_block_requests()), current_epoch]`
trong đó `current_epoch` được xác định theo thời gian thực hiện tại, và client MUST hỗ
trợ phục vụ các request block trong khoảng này.

*Lưu ý*: Khoảng epoch ở trên dựa trên thời gian thực hiện tại và không tính đến finality.
Client MUST đồng thời lưu giữ mọi block mới hơn finalized checkpoint gần nhất của mình và
MUST hỗ trợ phục vụ request cho các block này, kể cả khi chúng nằm ngoài khoảng trên, vì
các peer cần chúng để sync trong một giai đoạn dài không đạt finality.

Peer không thể trả lời các request block trong khoảng epoch
`compute_min_epochs_for_block_requests()` SHOULD phản hồi bằng mã lỗi
`3: ResourceUnavailable`. Những peer không thể trả lời thành công các request trong khoảng
này MAY bị trừ điểm (descore) hoặc bị ngắt kết nối bất kỳ lúc nào.

*Lưu ý*: Yêu cầu ở trên ngụ ý rằng các node khởi động từ một weak subjectivity checkpoint
gần đây MUST backfill (bổ sung ngược) cơ sở dữ liệu block cục bộ tối thiểu tới epoch
`current_epoch - compute_min_epochs_for_block_requests()` để tuân thủ đầy đủ các request
`BlocksByRange`. Để thực hiện backfill block về tới state gần đây một cách an toàn, node
MUST kiểm tra cả (1) chữ ký của proposer và (2) việc các block tạo thành một chain hợp lệ
cho tới block mới nhất được tham chiếu trong weak subjectivity state.

*Lưu ý*: Mặc dù client bootstrap từ một weak subjectivity checkpoint có thể tham gia mạng
ngay lập tức, các peer khác MAY ngắt kết nối và/hoặc tạm thời ban client chưa sync hoặc
mới sync một phần như vậy.

Client MUST phản hồi với ít nhất block đầu tiên tồn tại trong khoảng được yêu cầu, nếu
có, và không quá `MAX_REQUEST_BLOCKS` block.

Các block tiếp theo, nếu tồn tại, MUST được gửi theo thứ tự liên tiếp.

Client MAY giới hạn số block trong response.

Response MUST chứa không quá `count` block.

Client MUST phản hồi bằng các block theo góc nhìn fork choice hiện tại của mình -- tức là
các block thuộc chain duy nhất được xác định bởi head hiện tại. Đáng chú ý, các block ở
các slot trước thời điểm finalization MUST dẫn tới finalized block đã được báo cáo trong
handshake `Status`.

Client MUST phản hồi bằng các block nhất quán, thuộc cùng một chain trong phạm vi của
request. Điều này áp dụng cho mọi giá trị `step`. Cụ thể khi `step == 1`, mỗi
`parent_root` MUST khớp với `hash_tree_root` của block liền trước.

Sau block đầu tiên, client MAY dừng giữa chừng quá trình phản hồi nếu fork choice của nó
thay đổi góc nhìn về chain trong phạm vi của request.

##### BeaconBlocksByRoot v1

**Protocol ID:** `/eth2/beacon_chain/req/beacon_blocks_by_root/1/`

Nội dung Request:

```
(
  BeaconBlockRoots
)
```

Nội dung Response:

```
(
  SignedBeaconBlocks
)
```

Yêu cầu các block theo block root (= `hash_tree_root(SignedBeaconBlock.message)`).
Response là một list các `SignedBeaconBlock` có độ dài nhỏ hơn hoặc bằng số block được
yêu cầu. Nó có thể ít hơn trong trường hợp peer phản hồi không có một số block.

Không được yêu cầu quá `MAX_REQUEST_BLOCKS` block trong một lần.

`BeaconBlocksByRoot` chủ yếu được dùng để lấy lại các block gần đây (ví dụ khi nhận được
một block hoặc attestation mà block cha chưa được biết).

Request MUST được encode dưới dạng SSZ-field.

Response MUST gồm không hoặc nhiều `response_chunk`. Mỗi `response_chunk` _thành công_
MUST chứa một payload `SignedBeaconBlock` duy nhất.

Client MUST hỗ trợ yêu cầu block trong khoảng epoch
`[max(GENESIS_EPOCH, current_epoch - compute_min_epochs_for_block_requests()), current_epoch]`.
Nếu bất kỳ root nào trong nội dung request tham chiếu tới một block sớm hơn khoảng này,
peer MAY phản hồi bằng mã lỗi `3: ResourceUnavailable` hoặc không đưa block đó vào
response.

Client MUST phản hồi với ít nhất một block, nếu có. Client MAY giới hạn số block trong
response.

Client MAY đưa một block vào response ngay khi block đó vượt qua các quy tắc kiểm tra
gossip. Client SHOULD NOT phản hồi bằng các block không vượt qua được state transition
của beacon chain.

`/eth2/beacon_chain/req/beacon_blocks_by_root/1/` đã bị deprecated. Client MAY phản
hồi bằng một list rỗng trong giai đoạn chuyển tiếp deprecation.

##### Ping v1

**Protocol ID:** `/eth2/beacon_chain/req/ping/1/`

Nội dung Request:

```
(
  Uint64
)
```

Nội dung Response:

```
(
  Uint64
)
```

Được gửi định kỳ, protocol `Ping` kiểm tra xem các peer đang kết nối còn hoạt động hay
không. Các peer gửi request và phản hồi bằng số thứ tự metadata cục bộ của mình
(`MetaData.seq_number`).

Nếu peer không phản hồi request `Ping`, client MAY ngắt kết nối với peer đó.

Nhờ đó client có thể xác định bản ghi MetaData cục bộ về một peer còn cập nhật hay không,
và MAY yêu cầu phiên bản mới thông qua RPC method `MetaData` nếu đã cũ.

> 💡 Ghi chú: Nếu `seq_number` peer trả về lớn hơn giá trị client đang lưu, nghĩa là
> MetaData của peer đã thay đổi (ví dụ đổi các attestation subnet đang tham gia).

Request MUST được encode dưới dạng SSZ-field.

Response MUST gồm đúng một `response_chunk`.

##### GetMetaData v1

**Protocol ID:** `/eth2/beacon_chain/req/metadata/1/`

Không có nội dung Request.

Nội dung Response:

```
(
  MetaData
)
```

Yêu cầu MetaData của một peer. Request mở và thương lượng stream mà không gửi bất kỳ nội
dung request nào. Khi stream đã được thiết lập, peer nhận sẽ phản hồi bằng MetaData cục
bộ mới nhất của mình.

Response MUST được encode dưới dạng SSZ-container.

Response MUST gồm đúng một `response_chunk`.

### The discovery domain: discv5

Discovery Version 5
([discv5](https://github.com/ethereum/devp2p/blob/master/discv5/discv5.md))
(Protocol version v5.1) được dùng để khám phá peer (peer discovery).

`discv5` là một protocol độc lập, chạy trên UDP ở một port riêng, chỉ dành cho việc khám
phá peer. `discv5` hỗ trợ các bản ghi peer linh hoạt, tự chứng thực (ENR) và quảng bá theo
topic, cả hai đều là (hoặc sẽ là) yêu cầu trong bối cảnh này.

#### Integration into libp2p stacks

`discv5` SHOULD được tích hợp vào libp2p stack của client bằng cách hiện thực một adaptor
để nó tuân theo các abstraction và interface
[service discovery](https://github.com/libp2p/go-libp2p-core/blob/master/discovery/discovery.go)
và
[peer routing](https://github.com/libp2p/go-libp2p-core/blob/master/routing/routing.go#L36-L44)
(link dẫn tới go-libp2p).

Input của các thao tác gồm peer ID (khi tìm một peer cụ thể) hoặc capability (khi tìm các
peer có một khả năng cụ thể), và output là các multiaddr được chuyển đổi từ các bản ghi
ENR do backend discv5 trả về.

Việc tích hợp này cho phép libp2p stack sau đó thiết lập kết nối và stream với các peer
đã được khám phá.

#### ENR structure

Ethereum Node Record (ENR) của một Ethereum consensus client MUST chứa các mục sau (chưa
kể sequence number và signature, vốn MUST có mặt trong mọi ENR):

- Public key secp256k1 dạng nén, 33 byte (field `secp256k1`).

ENR MAY chứa các mục sau:

- Một địa chỉ IPv4 (field `ip`) và/hoặc địa chỉ IPv6 (field `ip6`).
- Một port QUIC IPv4 (field `quic`) biểu thị port lắng nghe QUIC (UDP) của libp2p cục bộ
  và/hoặc port IPv6 tương ứng (field `quic6`).
- Một port TCP IPv4 (field `tcp`) biểu thị port lắng nghe TCP của libp2p cục bộ và/hoặc
  port IPv6 tương ứng (field `tcp6`).
- Một port UDP IPv4 (field `udp`) biểu thị port lắng nghe discv5 cục bộ và/hoặc port IPv6
  tương ứng (field `udp6`).

Đặc tả của các tham số này có thể tìm thấy trong
[ENR Specification](http://eips.ethereum.org/EIPS/eip-778).

##### Attestation subnet bitfield

Mục ENR `attnets` biểu thị bitfield các attestation subnet với dạng sau, giúp dễ dàng
khám phá các peer đang tham gia những attestation gossip subnet cụ thể.

| Key       | Value     |
| --------- | --------- |
| `attnets` | `Attnets` |

Nếu `MetaData.attnets` của một node có bất kỳ bit nào khác không, ENR MUST chứa mục
`attnets` với giá trị giống hệt `MetaData.attnets`.

Nếu `MetaData.attnets` của một node toàn bit 0, ENR MAY tùy chọn chứa mục `attnets` hoặc
bỏ hẳn mục này.

##### `eth2` field

ENR MUST mang một key chung `eth2` với giá trị 16 byte gồm fork digest hiện tại, next fork
version và next fork epoch của node, nhằm đảm bảo kết nối được thiết lập với các peer
trên đúng mạng Ethereum mong muốn.

| Key    | Value       |
| ------ | ----------- |
| `eth2` | `ENRForkID` |

Cụ thể, giá trị của key `eth2` MUST là đối tượng được SSZ-encode sau (`ENRForkID`)

```
(
  fork_digest: ForkDigest
  next_fork_version: Version
  next_fork_epoch: Epoch
)
```

Các field của `ENRForkID` được định nghĩa như sau:

- `fork_digest` là
  `compute_fork_digest(genesis_validators_root, current_epoch)`.
- `next_fork_version` là fork version sẽ có hiệu lực tại `next_fork_epoch`:
  `compute_fork_version(current_epoch)` nếu `next_fork_epoch == FAR_FUTURE_EPOCH`, ngược
  lại là `compute_fork_version(next_fork_epoch)`.
- `next_fork_epoch` là epoch mà fork tiếp theo được lên kế hoạch. Nếu không có fork nào
  được lên kế hoạch trong tương lai, đặt `next_fork_epoch = FAR_FUTURE_EPOCH` để báo hiệu
  điều này.

*Lưu ý*: Trong các định nghĩa trên, `genesis_validators_root` là `Root` cố định nằm trong
`state.genesis_validators_root` và `current_epoch` là epoch hiện tại của node, xác định
theo thời gian thực (không nhất thiết là epoch mà node đã sync tới).

*Lưu ý*: `fork_digest` được tạo từ các giá trị chưa thể biết cho đến khi có genesis
block/state. Vì vậy, client SHOULD NOT tạo ENR và bắt đầu khám phá peer cho đến khi biết
các giá trị genesis. Một ngoại lệ đáng chú ý của quy tắc này là việc phân phối ENR của
bootnode trước genesis. Trong trường hợp này, ENR của bootnode SHOULD ban đầu được phân
phối với field `eth2` được đặt là
`ENRForkID(fork_digest=compute_fork_digest(b'\x00'*32, GENESIS_EPOCH), next_fork_version=GENESIS_FORK_VERSION, next_fork_epoch=FAR_FUTURE_EPOCH)`.
Sau khi biết các giá trị genesis, bootnode SHOULD cập nhật ENR để tham gia vào các hoạt
động khám phá bình thường.

Client SHOULD kết nối với các peer có `fork_digest`, `next_fork_version` và
`next_fork_epoch` khớp với giá trị cục bộ.

Client MAY kết nối với các peer có cùng `fork_digest` nhưng khác
`next_fork_version`/`next_fork_epoch`. Trừ khi `ENRForkID` được cập nhật thủ công cho
khớp nhau trước `next_fork_epoch` sớm hơn trong hai client, các client đang kết nối này sẽ
không thể tương tác thành công với nhau kể từ `next_fork_epoch` sớm hơn đó.

> 💡 Ghi chú: Nói cách khác, hai client cùng fork hiện tại nhưng dự kiến nâng cấp khác
> nhau sẽ "tách mạng" tại thời điểm fork sớm hơn, vì từ đó `fork_digest` của chúng không
> còn trùng nhau.

### Attestation subnet subscription

Vì Phase 0 không có shard và do đó không có Shard Committee, nên không có một "xương sống"
(backbone) ổn định cho các attestation subnet (`beacon_attestation_{subnet_id}`). Để tạo
sự ổn định này, mỗi beacon node nên:

- Duy trì subscribe vào `SUBNETS_PER_NODE` subnet trong `EPOCHS_PER_SUBNET_SUBSCRIPTION`
  epoch.
- Duy trì việc quảng bá các subnet đã chọn trong mục ENR `attnets` của node bằng cách đặt
  các bit `subnet_id` tương ứng thành `True` (ví dụ `ENR["attnets"][subnet_id] = True`)
  cho mọi attestation subnet cố định (persistent).
- Chọn các subnet này dựa trên node-id của mình, theo hàm
  `compute_subscribed_subnets(node_id, epoch)` dưới đây.

```python
def compute_subscribed_subnet(node_id: NodeID, epoch: Epoch, index: int) -> SubnetID:
    prefix_bits = int(compute_attestation_subnet_prefix_bits())
    node_id_prefix = node_id >> int(NODE_ID_BITS - prefix_bits)
    node_offset = Uint64(node_id % Uint256(EPOCHS_PER_SUBNET_SUBSCRIPTION))
    permutation_seed = sha256(
        uint_to_bytes(Uint64((epoch + node_offset) // EPOCHS_PER_SUBNET_SUBSCRIPTION))
    )
    permutated_prefix = compute_shuffled_index(
        Uint64(node_id_prefix),
        Uint64(1 << prefix_bits),
        permutation_seed,
    )
    return SubnetID((permutated_prefix + index) % ATTESTATION_SUBNET_COUNT)
```

```python
def compute_subscribed_subnets(node_id: NodeID, epoch: Epoch) -> Sequence[SubnetID]:
    return [compute_subscribed_subnet(node_id, epoch, index) for index in range(SUBNETS_PER_NODE)]
```

> 💡 Ghi chú: Các subnet được suy ra một cách tất định từ các bit đầu (prefix) của
> `node_id` và được hoán vị lại sau mỗi chu kỳ `EPOCHS_PER_SUBNET_SUBSCRIPTION` epoch.
> `node_offset` làm lệch thời điểm đổi subnet giữa các node, để không phải mọi node đều đổi
> subnet cùng một lúc. Nhờ tính tất định này, peer khác có thể kiểm chứng một node có thực
> sự subscribe đúng các subnet mà nó phải subscribe hay không.

*Lưu ý*: Khi chuẩn bị cho một đợt nâng cấp, node phải chọn và subscribe vào các subnet
thuộc phiên bản fork tương lai ít nhất `EPOCHS_PER_SUBNET_SUBSCRIPTION` epoch trước khi
nâng cấp diễn ra. Các subnet mới cho fork này được duy trì song song với các subnet của
fork hiện tại cho đến khi fork xảy ra. Sau khi fork xảy ra, để các subnet của fork trước
tự hết hạn mà không thay thế chúng.
## Design decision rationale

*(Lý do đằng sau các quyết định thiết kế — dạng hỏi đáp)*

### Transport

#### Why are we defining specific transports?

Các peer libp2p có thể lắng nghe đồng thời trên nhiều transport (giao thức vận
chuyển), và tập transport này có thể thay đổi theo thời gian. Multiaddr không
chỉ mã hóa địa chỉ mà còn mã hóa cả transport cần dùng để kết nối (dial) tới
địa chỉ đó.

Do tính chất động này, việc thống nhất "trên giấy" một transport cụ thể như TCP,
QUIC hay WebSockets trở nên không còn nhiều ý nghĩa.

Tuy vậy, vẫn hữu ích khi định nghĩa một mức tối thiểu (baseline) chung để đảm
bảo khả năng tương tác (interoperability) giữa các client.

#### Can clients support other transports/handshakes than the ones mandated by the specification?

Ngoài transport QUIC bắt buộc và TCP dùng làm phương án dự phòng (fallback),
client có thể hỗ trợ thêm các transport khác như WebSockets và WebRTC, nếu ngôn
ngữ lập trình được chọn có sẵn thư viện. Việc không hỗ trợ các transport này sẽ
không làm ảnh hưởng tới khả năng tương tác, nhưng hỗ trợ chúng mang lại lợi ích
đáng mong muốn:

- Mở đường cho việc giao tiếp với các light client trong tương lai (WebSockets,
  WebRTC).

Việc dùng thủ tục handshake này hay handshake khác phải trong suốt (transparent)
đối với tầng ứng dụng, một khi đối tượng Host/Node của libp2p đã được cấu hình
phù hợp. Nói cách khác, tầng ứng dụng không cần biết kết nối bên dưới đang dùng
transport/handshake nào.

#### What are the advantages of using TCP/QUIC/Websockets?

TCP là một giao thức mạng tin cậy, có thứ tự, song công toàn phần (full-duplex)
và có kiểm soát tắc nghẽn (congestion control); nó là nền tảng của phần lớn
Internet ngày nay. HTTP/1.1 và HTTP/2 đều chạy trên TCP.

QUIC là một transport dựa trên UDP, được IETF chuẩn hóa trong
[RFC 9000](https://www.rfc-editor.org/rfc/rfc9000). QUIC tin cậy, có thứ tự, hỗ
trợ multiplexing, bảo mật sẵn (TLS 1.3), giảm độ trễ thiết lập kết nối so với
TCP, có kiểm soát luồng ở mức stream (nhờ đó loại bỏ hiện tượng head-of-line
blocking — một gói bị mất làm nghẽn mọi stream phía sau), hỗ trợ thiết lập kết
nối 0-RTT và di chuyển endpoint (endpoint migration), cùng nhiều tính năng khác.
UDP cũng có khả năng vượt NAT (NAT traversal) tốt hơn TCP — điều mà chúng ta rất
cần trong mạng peer-to-peer. Chính những đặc điểm này là lý do QUIC được chọn làm
transport chính cho mạng của consensus layer.

QUIC cũng là giao thức nền của HTTP/3. Điều này có thể mang lại cho chúng ta khả
năng chống kiểm duyệt trước kỹ thuật kiểm tra gói tin sâu (deep packet
inspection) mà gần như không tốn thêm chi phí. Nếu chúng ta dùng cùng số port và
cơ chế mã hóa như HTTP/3, lưu lượng của chúng ta có thể không phân biệt được với
lưu lượng web thông thường, và khi đó chỉ còn bị ảnh hưởng bởi tường lửa lọc
theo IP thông thường — điều có thể đối phó bằng các cơ chế khác.

Transport WebSockets và/hoặc WebRTC là cần thiết để tương tác với trình duyệt, và
sẽ ngày càng quan trọng khi chúng ta đưa các light client chạy trên trình duyệt
vào mạng Ethereum.

#### Why do we not just support a single transport?

Mạng luôn tiến hóa. Việc "hardcode" các quyết định thiết kế dẫn tới sự xơ cứng
(ossification), ngăn mạng phát triển theo kịp công nghệ mới nhất. Đưa thay đổi
vào một giao thức đã xơ cứng là rất tốn kém, và đôi khi hoàn toàn không khả thi
nếu không muốn gây ra những đổ vỡ không mong muốn.

Thiết kế hướng tới khả năng nâng cấp và lựa chọn transport động ngay từ đầu sẽ
đặt nền móng cho một stack bền vững trước tương lai.

Client có thể áp dụng transport mới mà không phá vỡ transport cũ, và khả năng đa
transport cho phép các môi trường bị giới hạn hoặc chạy trong sandbox (ví dụ
trình duyệt, thiết bị nhúng) tham gia mạng như những thành viên bình đẳng thông
qua các transport phù hợp/có sẵn (ví dụ WSS), mà không cần proxy hay phải ủy
thác niềm tin cho server.

#### Why is QUIC the primary transport?

Khi đặc tả mạng này được viết lần đầu, chuẩn QUIC vẫn chưa hoàn thiện (lúc đó
mới ở bản working draft 22), và các runtime phổ biến chưa có hỗ trợ QUIC đủ
trưởng thành và tương thích lẫn nhau. Vì vậy TCP được quy định là transport cơ
bản bắt buộc, còn QUIC chỉ là một cải tiến tùy chọn.

Từ đó đến nay, QUIC đã được chuẩn hóa thành
[RFC 9000](https://www.rfc-editor.org/rfc/rfc9000) và được triển khai rộng rãi
trong hệ sinh thái libp2p. Khả năng multiplexing stream sẵn có, bảo mật TLS 1.3
tích hợp, độ trễ thiết lập kết nối thấp hơn (bao gồm 0-RTT) và khả năng vượt NAT
vượt trội khiến QUIC phù hợp với mạng p2p của consensus layer hơn TCP. Do đó QUIC
hiện là transport chính, còn TCP được giữ lại làm fallback cho các môi trường mà
QUIC hoặc UDP không khả dụng hoặc bị chặn.

### Multiplexing

#### Why are we using mplex/yamux?

[Yamux](https://github.com/hashicorp/yamux/blob/master/spec.md) là một bộ
multiplexer do Hashicorp phát triển, hỗ trợ kiểm soát tắc nghẽn ở mức stream. Nó
chỉ có implementation trong một số ít ngôn ngữ, và không phải là thành phần dễ
phát triển.

Nhận thức được điều đó, cộng đồng libp2p đã thiết kế
[mplex](https://github.com/libp2p/specs/blob/master/mplex/README.md) như một
multiplexer đơn giản, tối giản để dùng với libp2p. mplex không hỗ trợ kiểm soát
tắc nghẽn ở mức stream và bị ảnh hưởng bởi head-of-line blocking.

Với QUIC thì không cần multiplexer chồng lên (overlay multiplexer) vì bản thân
giao thức đã hỗ trợ multiplexing sẵn; nhưng các transport không có hỗ trợ này như
TCP, WebSockets, v.v. thì cần một multiplexer được đặt chồng lên trên.

### Protocol negotiation

#### When is multiselect 2.0 due and why do we plan to migrate to it?

multiselect 2.0 hiện vẫn đang trong giai đoạn hình thành ý tưởng. Cuộc thảo luận
bắt đầu [trong issue này](https://github.com/libp2p/specs/pull/95), nhưng đã trở
nên quá tải — như thường xảy ra với các thảo luận mã nguồn mở lớn mang tính khái
niệm, đụng chạm tới phần cốt lõi của hệ thống.

Vào một thời điểm nào đó trong năm 2020, chúng tôi kỳ vọng sẽ có một sáng kiến
mới nhằm trước hết xác định các yêu cầu, ràng buộc, giả định và tính năng, để
chốt được sự đồng thuận cơ bản từ đầu, rồi sau đó xây dựng tiếp trên sự đồng
thuận đó bằng cách đưa ra một đặc tả để triển khai.

Chúng tôi dự định cuối cùng sẽ chuyển sang multiselect 2.0 vì nó sẽ:

1. Giảm số lượt round trip khi khởi tạo kết nối và khi thương lượng giao thức
   cho stream.
2. Cho phép mô hình tương tác hiệu quả kiểu mỗi request một stream.
3. Tận dụng cơ chế *push data* (gửi dữ liệu sớm) của các giao thức bên dưới để
   đẩy nhanh quá trình thương lượng.
4. Cung cấp các khối xây dựng cho khả năng chống kiểm duyệt tốt hơn.

#### What is the difference between connection-level and stream-level protocol negotiation?

Mọi kết nối libp2p đều phải được xác thực, mã hóa và multiplex. Các kết nối dùng
transport không hỗ trợ sẵn xác thực/mã hóa và multiplexing (ví dụ TCP) cần trải
qua bước thương lượng giao thức để thống nhất một cơ chế mà cả hai bên cùng hỗ
trợ cho:

1. xác thực/mã hóa (như SecIO, TLS 1.3, Noise).
2. overlay multiplexer (như mplex, Yamux, spdystream).

Trong đặc tả này, chúng tôi gọi hai bước trên là *thương lượng mức kết nối
(connection-level negotiation)*. Các transport hỗ trợ sẵn các tính năng này (như
QUIC) sẽ bỏ qua các bước thương lượng đó.

Sau khi chọn được multiplexer, mọi I/O tiếp theo diễn ra trên các *stream*. Khi
mở stream, các peer gắn cố định một giao thức cho stream đó bằng cách thực hiện
*thương lượng giao thức mức stream (stream-level protocol negotiation)*.

Hiện tại, multistream-select 1.0 được dùng cho cả hai loại thương lượng, nhưng
multiselect 2.0 sẽ dùng các cơ chế riêng biệt cho quá trình khởi tạo kết nối và
cho việc thương lượng giao thức của stream.

### Encryption

#### Why are we not supporting SecIO?

SecIO đã là tầng mã hóa mặc định của libp2p trong nhiều năm. Nó được dùng trong
IPFS và Filecoin. Và dù sắp bị thay thế, nó đã được chứng minh là hoạt động tốt ở
quy mô lớn.

Mặc dù SecIO được hỗ trợ trong nhiều ngôn ngữ, chúng tôi sẽ không dùng nó cho
mainnet vì, cùng với các lý do khác, nó cần nhiều round trip để đảm bảo an toàn,
và không hỗ trợ early data (dữ liệu 0-RTT) — một cơ chế mà multiselect 2.0 sẽ
tận dụng để giảm round trip khi khởi tạo kết nối.

SecIO không được coi là an toàn cho các mục đích của đặc tả này.

#### Why are we using Noise?

Trích từ [website](http://www.noiseprotocol.org) của Noise Protocol Framework:

> Noise is a framework for building crypto protocols. Noise protocols support
> mutual and optional authentication, identity hiding, forward secrecy, zero
> round-trip encryption, and other advanced features.

*(Tạm dịch: Noise là một framework để xây dựng các giao thức mật mã. Các giao
thức Noise hỗ trợ xác thực hai chiều và xác thực tùy chọn, ẩn danh tính, forward
secrecy, mã hóa không cần round trip, và các tính năng nâng cao khác.)*

Bản thân Noise không quy định một thủ tục handshake duy nhất, mà cung cấp một
framework để xây dựng các handshake an toàn dựa trên trao đổi khóa
Diffie-Hellman, với nhiều lựa chọn đánh đổi và mức đảm bảo khác nhau.

Handshake Noise nhẹ, dễ hiểu, và được dùng trong các dự án lớn tập trung vào mật
mã như WireGuard, I2P và Lightning.
[Nhiều](https://www.wireguard.com/papers/kobeissi-bhargavan-noise-explorer-2018.pdf)
[nghiên cứu](https://eprint.iacr.org/2019/436.pdf) đã đánh giá các mục tiêu bảo
mật được tuyên bố của một số handshake Noise và cho kết quả tích cực.

#### Why are we using encryption at all?

Mã hóa ở tầng transport bảo vệ việc trao đổi thông điệp và mang lại các thuộc
tính hữu ích cho quyền riêng tư, an toàn và khả năng chống kiểm duyệt. Các thuộc
tính này đến từ những đảm bảo bảo mật sau, áp dụng cho toàn bộ quá trình giao
tiếp giữa hai peer:

- Xác thực peer (peer authentication): peer mà tôi đang nói chuyện thực sự là
  người họ tự nhận và là người tôi mong đợi.
- Tính bí mật (confidentiality): không bên quan sát nào có thể nghe lén nội dung
  thông điệp của chúng ta.
- Tính toàn vẹn (integrity): dữ liệu không bị bên thứ ba sửa đổi trong quá trình
  truyền.
- Chống chối bỏ (non-repudiation): peer gửi không thể phủ nhận rằng mình đã gửi
  thông điệp.
- Tùy theo thuật toán và cơ chế được chọn (ví dụ HMAC liên tục), chúng ta có thể
  có thêm các đảm bảo khác, như chống phát lại (non-replayability — byte này chỉ
  có thể được gửi *vào đúng lúc này*; ví dụ bằng cách dùng HMAC liên tục), hoặc
  perfect forward secrecy (nếu khóa của một peer bị lộ, nội dung các cuộc hội
  thoại trong quá khứ vẫn không bị lộ).

Lưu ý rằng mã hóa ở tầng transport không loại trừ việc mã hóa hay dùng mật mã ở
tầng ứng dụng. Mã hóa tầng transport bảo vệ bản thân kênh giao tiếp, còn mật mã ở
tầng ứng dụng là cần thiết cho các nhu cầu của ứng dụng (ví dụ signature, tính
ngẫu nhiên, v.v.).

### Gossipsub

#### Why are we using a pub/sub algorithm for block and attestation propagation?

Pubsub là một kỹ thuật để phát tán (broadcast/disseminate) data trên toàn mạng
một cách nhanh chóng. Data được đóng gói trong các thông điệp kiểu
"fire-and-forget" (gửi đi rồi thôi), không yêu cầu phản hồi từ từng bên nhận. Các
peer đăng ký (subscribe) một topic sẽ tham gia vào việc lan truyền các thông điệp
trong topic đó.

Phương án thay thế là duy trì một mạng lưới kết nối đầy đủ (mọi peer kết nối 1:1
với nhau), vốn mở rộng rất kém (O(n^2)).

#### Why are we using topics to segregate encodings, yet only support one encoding?

Để có thể mở rộng trong tương lai mà gần như không tốn chi phí ở hiện tại (ngoài
vài byte thêm vào tên topic).

#### How do we upgrade gossip channels (e.g. changes in encoding, compression)?

Thay đổi gossipsub/broadcast đòi hỏi một đợt nâng cấp có phối hợp, trong đó tất
cả client cùng bắt đầu publish lên topic mới tại thời điểm nâng cấp.

Khi một node đang chuẩn bị cho các nhiệm vụ sắp tới (ví dụ nhìn trước nhiệm vụ
của validator — validator duty lookahead) trên một topic gossipsub, node nên
tham gia topic của epoch tương lai mà nhiệm vụ sẽ diễn ra, bên cạnh việc vẫn
lắng nghe các topic của epoch hiện tại.

#### Why must all clients use the same gossip topic instead of one negotiated between each peer pair?

Việc hỗ trợ nhiều topic/encoding sẽ đòi hỏi phải có các relayer (bên chuyển
tiếp) để chuyển đổi giữa các encoding và topic, nhằm tránh phân mảnh mạng — tình
trạng các bên tham gia có góc nhìn khác nhau về state được gossip — khiến giao
thức phức tạp và dễ vỡ hơn.

Các giao thức gossip thường ghi nhớ những thông điệp đã thấy trong một khoảng
thời gian hữu hạn, dựa trên định danh của thông điệp — nếu bạn publish lại cùng
một thông điệp sau khi khoảng thời gian đó đã qua, nó sẽ bị broadcast lại; việc
thêm độ trễ do relay cũng làm tình huống này dễ xảy ra hơn.

Có thể hình dung trong một kịch bản nâng cấp phức tạp, ta có các peer publish
cùng một thông điệp trên hai topic/encoding, nhưng cái giá về overhead — cả tính
toán lẫn mạng — là khá cao, nên chúng tôi muốn tránh điều đó.

Client được phép publish data lên các topic thay thế, miễn là chúng cũng publish
lên topic bắt buộc chung của toàn mạng.

#### Why are the topics strings and not hashes?

Tên topic có cấu trúc phân cấp. Trong tương lai, gossipsub có thể hỗ trợ đăng ký
theo wildcard (ví dụ đăng ký tất cả các topic con dưới một tiền tố gốc) thông qua
so khớp tiền tố. Nếu bắt buộc dùng hash cho tên topic, chúng ta sẽ không thể tận
dụng những tính năng như vậy về sau.

Việc chọn tên topic dạng văn bản thô không làm mất đi đảm bảo nào về bảo mật hay
quyền riêng tư, vì miền giá trị vốn hữu hạn, nên việc tìm preimage của một digest
cũng sẽ rất dễ dàng.

Ngoài ra, tên topic còn ngắn hơn digest tương ứng (giả sử dùng hash SHA-256), nên
việc hash topic sẽ làm thông điệp phình to một cách không cần thiết.

#### Why are we using the `StrictNoSign` signature policy?

Policy này bỏ qua các trường `from` (1), `seqno` (3), `signature` (5) và `key`
(6). Nếu giữ lại, các trường này sẽ:

- Làm lộ nguồn gốc của người gửi (`from`), loại người gửi (dựa trên `seqno`).
- Thêm data thừa không dùng tới vào gossip, vì message ID được tính dựa trên
  `data`, không dựa trên `from` và `seqno`.
- Tạo ra nhiều bước kiểm tra thông điệp hơn mức cần thiết, ví dụ kiểm tra
  `signature`.

#### Why are we overriding the default libp2p pubsub `message-id`?

Với mục đích hiện tại, không cần định danh thông điệp dựa trên peer nguồn, hay
theo dõi `seqno` của thông điệp. Bằng cách ghi đè `message-id` mặc định để dùng
định danh theo nội dung (content-addressing), chúng ta có thể lọc bỏ các bản
trùng lặp không cần thiết trước khi chúng tới tầng ứng dụng.

Một số ví dụ về trường hợp thông điệp có thể bị trùng lặp:

- Một validator client kết nối tới nhiều beacon node và publish các gossip
  message trùng lặp.
- Các chiến lược aggregate attestation trong đó client aggregate một phần các
  attestation rồi lan truyền chúng. Các aggregate một phần có thể bị trùng lặp.
- Client publish lại các thông điệp đã thấy.

#### Why are these specific gossip parameters chosen?

- `D`, `D_low`, `D_high`, `D_lazy`: giá trị mặc định được khuyến nghị.
- `heartbeat_interval`: 0.7 giây, được khuyến nghị cho beacon chain trong
  [báo cáo đánh giá GossipSub của Protocol Labs](https://gateway.ipfs.io/ipfs/QmRAFP5DBnvNjdYSbWhEhVRJJDFCLpPyvew5GwCCB4VxM4).
- `fanout_ttl`: 60 giây, giá trị mặc định được khuyến nghị. Fanout chủ yếu được
  dùng bởi các committee khi publish attestation lên subnet. Việc này xảy ra một
  lần mỗi epoch cho mỗi validator, và subnet thay đổi mỗi epoch, nên tăng
  `fanout_ttl` so với mặc định cũng chẳng được lợi gì nhiều.
- `mcache_len`: 6, tăng thêm một để đảm bảo mcache tồn tại đủ lâu cho các
  `IWANT` phản hồi các `IHAVE`, trong bối cảnh `heartbeat_interval` ngắn hơn.
  Nếu tăng `mcache_gossip` thì tham số này nên được tăng sao cho lớn hơn
  `mcache_gossip` ít nhất `3` (~2 giây).
- `mcache_gossip`: 3, giá trị mặc định được khuyến nghị. Có thể tăng lên 5 hoặc 6
  (~4 giây) nếu thời gian gossip dài hơn dự kiến và cửa sổ hiện tại không đủ
  nhạy trong điều kiện bất lợi.
- `seen_ttl`: `SLOTS_PER_EPOCH * SLOT_DURATION_MS / 1000 / heartbeat_interval`.
  Tính hợp lệ của gossip attestation bị giới hạn trong một epoch, nên đây là cận
  trên an toàn.

> 💡 Ghi chú: `seen_ttl` được tính theo đơn vị số lần heartbeat; công thức trên
> tương ứng với độ dài một epoch (tính bằng giây) chia cho `heartbeat_interval`.

#### Why is there `MAXIMUM_GOSSIP_CLOCK_DISPARITY` when validating slot ranges of messages in gossip subnets?

Với một số gossip channel (ví dụ các channel cho Attestation và BeaconBlock), có
quy định các khoảng slot mà trong đó một thông điệp cụ thể được phép gửi, nhằm
chỉ gossip những thông điệp có thể được dùng một cách hợp lý trong đồng thuận tại
thời điểm/slot hiện tại. Mục đích là giảm bớt "không gian lựa chọn" cho các cuộc
tấn công DoS.

`MAXIMUM_GOSSIP_CLOCK_DISPARITY` cung cấp một khoảng dung sai khi kiểm tra khoảng
slot, để mạng gossip không trở nên quá mong manh trước sự lệch đồng hồ giữa các
node. Với thời điểm broadcast slot cho phép nhỏ nhất và lớn nhất,
`MAXIMUM_GOSSIP_CLOCK_DISPARITY` MUST lần lượt được trừ đi và cộng vào, qua đó mở
rộng nhẹ khoảng hợp lệ. Mặc dù đôi khi thông điệp có thể được gossip sớm lên
mạng, fork choice của node sẽ không đưa các thông điệp này vào đồng thuận thực sự
cho đến khi _slot đó thực sự bắt đầu theo đồng hồ local_.

#### Why are there `ATTESTATION_SUBNET_COUNT` attestation subnets?

Tùy theo số lượng validator, việc gom nhóm các shard subnet có thể hiệu quả hơn
và có thể giúp gossipsub channel ổn định hơn. Cách gom nhóm chính xác sẽ phụ
thuộc vào các thử nghiệm mạng chi tiết hơn. Hằng số này cho phép linh hoạt hơn
trong việc thiết lập topology mạng cho việc aggregate attestation (vì việc
aggregate cần diễn ra trên từng subnet). Giá trị hiện được đặt bằng
`MAX_COMMITTEES_PER_SLOT`, cho đến khi/trừ khi các thử nghiệm mạng chỉ ra điều
ngược lại.

#### Why are attestations limited to be broadcast on gossip channels within `SLOTS_PER_EPOCH` slots?

Attestation chỉ có thể được đưa vào chain trong khoảng thời gian tương đương một
epoch tính theo slot, nên đây là điểm cắt tự nhiên. Việc broadcast các
attestation cũ hơn một epoch không có ích gì cho chain; và vì mỗi validator có cơ
hội tạo attestation mới ở mỗi epoch, việc relay attestation cũ cũng gần như không
có ích cho fork choice, vì mỗi validator sẽ sớm tạo ra một "latest message" mới.

Ngoài ra, việc relay attestation đòi hỏi phải kiểm tra attestation đó trong bối
cảnh của `state` tại thời điểm nó được tạo. Do đó, việc kiểm tra các attestation
cũ tùy ý sẽ đặt thêm yêu cầu về việc node phải có sẵn những state nào. Điều này
dẫn tới gánh nặng tài nguyên lớn hơn và có thể trở thành một vector tấn công
DoS.

#### Why are aggregate attestations broadcast to the global topic as `AggregateAndProof`s rather than just as `Attestation`s?

Chiến lược trội (dominant strategy) đối với một validator riêng lẻ là luôn
broadcast một aggregate chứa attestation của chính mình lên channel toàn cục để
đảm bảo proposer nhìn thấy attestation đó và đưa vào block. Việc dùng một tiêu
chí lựa chọn riêng tư (private selection) và gửi kèm bằng chứng được chọn này
cùng với aggregate được gossip đảm bảo rằng chiến lược trội nói trên sẽ không làm
ngập channel toàn cục.

Hơn nữa, kẻ tấn công có thể tạo ra bao nhiêu aggregate trông có vẻ trung thực
tùy thích rồi broadcast chúng lên pubsub channel toàn cục. Vì vậy nếu không có
một dạng bằng chứng được chọn làm aggregator, channel toàn cục có thể bị spam một
cách dễ dàng.

#### Why are we sending entire objects in the pubsub and not just hashes?

Nên gửi toàn bộ object để đạt tốc độ lan truyền nhanh nhất. Nếu chỉ gửi hash, việc
lan truyền block và attestation sẽ phụ thuộc vào các request đệ quy từ từng peer.
Trong kịch bản chỉ gửi hash, peer có thể nhận được hash mà không biết phải tải
nội dung thực sự từ ai. Gửi toàn bộ object đảm bảo chúng được lan truyền ra toàn
mạng.

#### Should clients gossip blocks if they *cannot* validate the proposer signature due to not yet being synced, not knowing the head block, etc?

Không. Lệnh cấm gossip block chưa được xác minh cũng áp dụng cho các node không
thể xác minh signature do chưa sync xong, nhằm đảm bảo các cuộc tấn công DOS
(được khuếch đại) như vậy không thể xảy ra.

#### How are we going to discover peers in a gossipsub topic?

Trong Phase 0, peer cho các attestation subnet sẽ được tìm thông qua mục
`attnets` trong ENR.

Mặc dù phương pháp này đủ dùng cho giai đoạn đầu của beacon chain, về lâu dài
chúng tôi hướng tới việc dùng discv5 topic — phù hợp hơn — cho việc này và các
tác vụ tương tự. Cuối cùng thì ENR không nên được dùng cho mục đích này. ENR phù
hợp nhất để lưu thông tin về danh tính, vị trí và năng lực (capability) của node,
chứ không phải các thông tin quảng bá hay thay đổi.

#### How should fork version be used in practice?

Fork version được cập nhật thủ công (nhiều khả năng bằng cách tăng dần) ở mỗi đợt
nâng cấp. Mục đích là cung cấp sự phân tách domain sẵn có cho signature, đồng
thời giúp nhận diện peer (qua ENR) và đánh phiên bản cho các giao thức mạng (ví
dụ dùng fork version để tự nhiên đánh phiên bản cho các gossipsub topic).

`BeaconState.genesis_validators_root` được trộn vào domain của signature và của
fork trong ENR (`ForkDigest`) để dễ dàng phân tách domain giữa các chain khác
nhau. Điều này cho phép tái sử dụng fork version một cách an toàn giữa các chain,
trừ trường hợp fork gây tranh cãi (contentious fork) dùng chung genesis. Trong
những trường hợp đó, cần đặc biệt cẩn thận để tách biệt fork version (ví dụ lật
một bit bậc cao trong mọi version tương lai của một trong hai chain).

Mỗi node lưu local tất cả các fork version trước đây và các fork version dự kiến
trong tương lai, cùng với epoch của từng fork. Điều này cho phép xử lý sync và xử
lý thông điệp bắt đầu từ các fork/epoch trong quá khứ.

### Req/Resp

#### Why segregate requests into dedicated protocol IDs?

Các request được tách riêng theo protocol ID để:

1. Tận dụng cơ chế định tuyến giao thức của libp2p, sao cho stack libp2p sẽ định
   tuyến stream đến tới đúng handler. Điều này cho phép hàm handler của mỗi loại
   request được độc lập, khép kín. Để dễ hình dung, hãy nghĩ tới cách bạn gắn các
   HTTP handler vào một REST API server.
2. Đánh phiên bản request một cách độc lập. Với một giao thức "ô dù" gộp chung,
   chi tiết thô hơn, toàn bộ giao thức sẽ phải đổi phiên bản ngay cả khi chỉ một
   trường trong một thông điệp thay đổi.
3. Cho phép client chọn những request/phiên bản riêng lẻ mà chúng hỗ trợ. Sẽ
   không còn bắt buộc phải hỗ trợ tất cả request, và về nguyên tắc client có thể
   hỗ trợ một tập con các request và nhiều phiên bản khác nhau.
4. Mang lại sự linh hoạt và nhanh nhạy cho client khi áp dụng các thay đổi đặc
   tả có ảnh hưởng tới request, bằng cách báo cho peer biết chính xác tập con
   request mới/cũ nào mà chúng hỗ trợ.
5. Cho phép client chủ động chọn tương thích ngược ở mức từng request. Nếu
   không, client sẽ buộc phải hỗ trợ toàn bộ các phiên bản của giao thức request
   chi tiết thô.
6. Song song hóa các RFC (hoặc EIP). Bằng cách tách rời các request với nhau, mỗi
   RFC ảnh hưởng tới giao thức request có thể được triển khai/thử nghiệm/tranh
   luận độc lập mà không cần một điểm đồng bộ để đánh phiên bản giao thức tổng
   ở tầng trên cùng.
   1. Lợi ích là client có thể chủ động chọn triển khai RFC nào mà không phải chấp
      nhận tất cả các RFC khác có thể nằm trong phiên bản tổng đó.
   2. Để đạt được mức chi tiết này với một giao thức tầng trên cùng, ta sẽ phải
      tạo ra số biến thể (ví dụ /protocol/43-{a,b,c,d,...}) bằng tích Descartes
      của các RFC đang được xử lý, O(n^2).
7. Cho phép đơn giản hóa payload của request. Không cần gửi request-id và
   method-id nữa. Encoding/loại request và phiên bản đều có thể được framework xử
   lý.

**Lưu ý (Caveat)**: Thành phần thương lượng giao thức trong phiên bản libp2p hiện
tại được gọi là multistream-select 1.0. Nó khá đơn giản (ngây thơ) và gây thêm
overhead cho mỗi request khi thương lượng stream, dù có thể tối ưu theo từng
implementation để tiết kiệm chi phí này. Multiselect 2.0 cuối cùng sẽ loại bỏ
overhead này bằng cách ghi nhớ (memoize) các giao thức đã chọn trước đó và mô
hình hóa các bảng giao thức dùng chung. May mắn là giao thức req/resp này không
được dự kiến là nút thắt cổ chai về mạng trong toàn bộ giao thức, nên overhead
thêm vào không được kỳ vọng sẽ gây cản trở đáng kể.

#### Why are messages length-prefixed with a protobuf varint in the SSZ-encoding?

Chúng ta dùng các stream dùng một lần, trong đó mỗi stream được đóng lại khi kết
thúc thông điệp. Do đó, libp2p xử lý một cách trong suốt việc phân tách thông
điệp trong stream bên dưới. Stream của libp2p là full-duplex, và mỗi bên tự chịu
trách nhiệm đóng phía ghi của mình (giống TCP). Vì vậy ta có thể dùng việc đóng
stream để đánh dấu kết thúc của request và response một cách độc lập.

Dù vậy, trong trường hợp `ssz_snappy`, thông điệp vẫn được thêm tiền tố độ dài
(length-prefix) bằng độ dài của data bên dưới, vì:

- Một reader cơ bản có thể chuẩn bị buffer có kích thước chính xác trước khi đọc
  thông điệp.
- Một reader nâng cao hơn có thể giải mã SSZ theo kiểu streaming khi biết trước
  độ dài của data SSZ.
- Thống nhất với các giao thức như gRPC trên HTTP/2, vốn cũng thêm tiền tố độ
  dài.
- Cho phép kiểm tra hợp lý (sanity check) độ dài thông điệp, và áp đặt giới hạn
  độ dài chặt chẽ hơn nhiều dựa trên thông tin kiểu SSZ, nhằm chống DOS tốt hơn
  cả giới hạn độ dài thông điệp toàn cục. Ví dụ, một thông điệp `Status` nhỏ
  không thể nào cần tới `MAX_PAYLOAD_SIZE` byte.

[Protobuf varint](https://developers.google.com/protocol-buffers/docs/encoding#varints)
là một kỹ thuật hiệu quả để mã hóa số nguyên có độ dài thay đổi (ở đây là số
không dấu). Thay vì dành một trường có kích thước cố định với số byte đủ để biểu
diễn giá trị lớn nhất có thể, trường này co giãn được, đổi lại tốn 1 bit overhead
cho mỗi byte.

#### Why do we version protocol strings with ordinals instead of semver?

Dùng semver cho giao thức mạng dễ gây nhầm lẫn. Không bao giờ rõ ràng một thay
đổi ở một trường thực sự hàm ý điều gì, kể cả khi nó tương thích ngược về mặt
deserialize. Sự thống nhất về giao thức mạng nên được thể hiện tường minh. Hãy
hình dung hai peer:

- Peer A hỗ trợ v1.1.1 của giao thức X.
- Peer B hỗ trợ v1.1.2 của giao thức X.

Hai peer này không bao giờ nên giao tiếp với nhau vì kết quả có thể không lường
trước được. Đây là một ví dụ được đơn giản hóa quá mức: hãy hình dung vấn đề
tương tự với 10 phiên bản có thể có. Khi đó ta có 10^2 (100) kết quả khả dĩ mà
các peer cần mô hình hóa. Độ phức tạp sinh ra là không thể kiểm soát.

Vì lý do đó, chúng tôi dựa vào việc thương lượng các giao thức tường minh, khớp
chính xác từng ký tự. Trong ví dụ trên, peer B sẽ cung cấp tương thích ngược bằng
cách hỗ trợ và quảng bá cả v1.1.1 lẫn v1.1.2 của giao thức.

Do đó, semver chỉ còn được dùng để truyền đạt kỳ vọng ở mức con người, và ngay cả
ở đó nó cũng không làm tốt, vì không rõ "tương thích ngược" và "breaking change"
chỉ áp dụng ở mức schema dữ liệu truyền đi (wire schema), ở mức hành vi, hay ở
mức nào khác.

Vì vậy, chúng tôi loại bỏ semver và thay bằng số thứ tự (ordinal), vốn đòi hỏi
sự thống nhất tường minh và không áp đặt một chính sách cụ thể nào cho các thay
đổi.

#### Why is it called Req/Resp and not RPC?

Tên Req/Resp được dùng để tránh nhầm lẫn với JSON-RPC và các cơ chế tương tác
người dùng–client tương tự.

#### What is a typical rate limiting strategy?

Bên phản hồi (responder) thường muốn giới hạn tốc độ (rate limit) request để
chống spam và quản lý mức tiêu thụ tài nguyên, trong khi bên yêu cầu (requester)
muốn tối đa hóa hiệu năng dựa trên chiến lược phân bổ tài nguyên của chính mình.
Đối với mạng, việc sử dụng tài nguyên sẵn có một cách tối ưu là có lợi.

Nhìn chung, requester không biết năng lực/giới hạn của từng server, nhưng có thể
suy ra từ tốc độ phản hồi để chọn peer tiếp theo cho một request.

Vì server sẽ giữ response lại cho đến khi có đủ năng lực xử lý, client có thể lạc
quan gửi request mà không lo bị chấm điểm âm (negative scoring) hay phải thăm dò
tốc độ một cách kém tối ưu.

Một cách tiếp cận điển hình cho requester là đặt timeout cho request, tùy theo
bản chất của request và các tham số kết nối nói chung — ví dụ khi yêu cầu block,
một peer có thể chọn gửi request tới peer thứ hai nếu peer thứ nhất không phản
hồi trong một khoảng thời gian hợp lý, và hủy (reset) request tới peer thứ nhất
nếu peer thứ hai phản hồi nhanh hơn. Client có thể dùng hiệu năng phản hồi trong
quá khứ để thưởng cho các peer nhanh khi triển khai peer scoring.

Một cách tiếp cận điển hình cho responder là triển khai token bucket/leaky bucket
hai cấp, với một giới hạn theo từng peer và một giới hạn toàn cục. Mức chi tiết
của rate limiting có thể dựa trên toàn bộ request hoặc trên từng chunk, trong đó
cách thứ hai được ưu tiên hơn. Có thể gán một chi phí token cho bản thân request
và, riêng biệt, cho từng chunk trong response, để vừa được bảo vệ trước các
request lớn, vừa trước các request dồn dập.

Đối với requester, rate limiting không thể phân biệt được với các tình huống khác
gây phản hồi chậm (peer chậm, tắc nghẽn, v.v.), và vì các tình huống đó dù sao
cũng phải được xử lý, việc gộp rate limiting vào cùng chiến lược này giúp
implementation đơn giản.

#### Why do we allow empty responses in block requests?

Khi yêu cầu block theo khoảng (range) hoặc theo root, có thể xảy ra trường hợp
không có block nào trong khoảng được chọn, hoặc node phản hồi không có các block
được yêu cầu.

Do đó, có thể ta cần truyền một danh sách rỗng — có vài cách để mã hóa điều này:

0. Đóng stream mà không gửi data nào.
1. Thêm một lựa chọn `null` vào response `success`, ví dụ bằng cách thêm một byte
   bổ sung.
2. Phản hồi bằng một kết quả lỗi, dùng một mã lỗi riêng cho "Không có data".

Về mặt ngữ nghĩa, việc một slot không có block không phải là lỗi, nên phương án 2
không tự nhiên.

Phương án 1 cho phép responder báo hiệu "không có block", nhưng thông tin này có
thể sai — ví dụ trong trường hợp node độc hại.

Với phương án 0, client không có cách nào phân biệt một slot không có block với
một response bị thiếu, nhưng vì client vốn đã phải có logic xử lý sự không chắc
chắn trước peer độc hại, phương án 0 đã được chọn. Client nên đánh dấu mọi slot
thiếu block là chưa biết (unknown) cho đến khi có thể xác minh — nhờ các block kế
tiếp — rằng slot đó thực sự không chứa block.

Giả sử dùng phương án 0 không có mã hóa `null` đặc biệt, xét một request cho các
slot `2, 3, 4` — nếu không có block nào được tạo ở slot 4, response sẽ là
`2, 3, EOF`. Giờ xét cùng tình huống nhưng chỉ yêu cầu `4` — việc đóng stream chỉ
với `EOF` (không có `response_chunk` nào) là nhất quán.

Việc không cung cấp được những block mà node "lẽ ra" phải có là lý do để tin
tưởng một peer ít hơn — ví dụ, nếu một peer gossip một block thì nó phải có
block cha của block đó. Nếu request block cha thất bại, đó là dấu hiệu peer có
chất lượng kém, vì peer phải kiểm tra block trước khi gossip.

#### Why does `BeaconBlocksByRange` let the server choose which branch to send blocks from?

Khi kết nối, thông điệp `Status` cho biết phần nào về trạng thái sync của một
peer, nhưng trạng thái này thay đổi theo thời gian. Đến khi một request
`BeaconBlocksByRange` tiếp theo được xử lý, thông tin đó có thể đã cũ, và
responder có thể đã chuyển sang một điểm finalization mới và đã prune (cắt bỏ)
các block quanh head trước đó và các block đã finalized.

Để tránh race condition này, chúng tôi cho phép responder chọn branch để gửi cho
requester. Sau đó requester sẽ kiểm tra các block và đưa chúng vào database của
mình — vì cả hai bên tuân theo cùng một bộ quy tắc, tại thời điểm này họ phải đi
tới cùng một canonical chain.

#### Why are `BlocksByRange` requests only required to be served for the latest `compute_min_epochs_for_block_requests()` epochs?

Do tính finality kinh tế và các yêu cầu về weak subjectivity của một blockchain
proof-of-stake, để một node mới tham gia mạng một cách an toàn, node đó phải được
cung cấp một checkpoint gần đây lấy từ kênh ngoài (out-of-band). Checkpoint này
có thể ở dạng một cặp `root` & `epoch`, hoặc có thể là toàn bộ beacon state rồi
từ đó sync block đơn giản tới head. Chúng tôi kỳ vọng cách thứ hai sẽ là chiến
lược UX phổ biến.

Các checkpoint này, *trong trường hợp xấu nhất* (tức validator set rất lớn và mức
suy giảm an toàn tối đa cho phép), phải thuộc về
`compute_min_epochs_for_block_requests()` epoch gần nhất, và do đó người dùng
phải có thể sync block tới head từ điểm xuất phát này. Vì thế, giá trị này xác
định khoảng epoch mà bên ngoài nó node được phép prune các block đã finalized,
đồng thời là khoảng epoch mà một node mới sync từ checkpoint phải backfill (tải
bù về phía quá khứ).

`compute_min_epochs_for_block_requests()` được tính bằng phép toán của
`compute_weak_subjectivity_period` trong
[weak subjectivity guide](./weak-subjectivity.md). Cụ thể, để tìm khoảng epoch
tối đa này, chúng tôi dùng trường hợp xấu nhất là validator set rất lớn
(`>= MIN_PER_EPOCH_CHURN_LIMIT * CHURN_LIMIT_QUOTIENT`).

#### Why must the proposer signature be checked when backfilling blocks in the database?

Khi backfill block vào database từ một block/state đã biết là an toàn (ví dụ khi
khởi động từ một weak subjectivity state), node không chỉ phải đảm bảo các
`BeaconBlock` tạo thành một chain nối tới block an toàn đã biết, mà còn phải kiểm
tra rằng proposer signature trong wrapper `SignedBeaconBlock` là hợp lệ.

Lý do là signature không nằm trong chuỗi hash của `BeaconBlock`, nên có thể bị
một kẻ tấn công làm sai lệch bằng cách cung cấp các `BeaconBlock` hợp lệ nhưng
kèm signature không hợp lệ trong `SignedBeaconBlock`.

Mặc dù trong trường hợp sử dụng cụ thể này, điều đó không làm suy giảm an toàn
(do giả định đã bắt đầu từ một weak subjectivity checkpoint), nó vẫn tạo ra data
lịch sử không hợp lệ và có thể vô tình bị truyền tiếp tới các node khác.

#### What's the effect of empty slots on the sync algorithm?

Khi sync, ta chỉ có thể biết một slot đã bị bỏ qua (skipped) trên một branch cụ
thể bằng cách xem xét các block kế tiếp và phân tích đồ thị tạo bởi parent root.
Vì phía server có thể bỏ bớt block trong response vì bất kỳ lý do gì, client phải
kiểm tra đồ thị và sẵn sàng lấp các khoảng trống.

Ví dụ, nếu một peer trả về block [2, 3] khi được hỏi [2, 3, 4], client không được
giả định rằng block 4 không tồn tại — điều đó chỉ có nghĩa là peer phản hồi đã
không gửi nó (có thể họ chưa có, hoặc cố tình che giấu một cách độc hại), và cần
các block kế tiếp để xác định xem có tồn tại block ở slot 4 trên branch này hay
không.

### Discovery

#### Why are we using discv5 and not libp2p Kademlia DHT?

discv5 là một giao thức độc lập, chạy trên UDP ở một port riêng, chỉ dành cho
việc khám phá peer và dịch vụ. discv5 hỗ trợ các bản ghi peer tự chứng thực
(self-certified), linh hoạt (ENR) và quảng bá theo topic — cả hai đều là, hoặc sẽ
là, yêu cầu trong bối cảnh này.

Ngược lại, libp2p Kademlia DHT là một giao thức/implementation DHT đầy đủ với khả
năng định tuyến nội dung (content routing) và lưu trữ — cả hai đều không liên
quan trong bối cảnh này.

Các node execution-layer của Ethereum sẽ tiến tới hỗ trợ discv5. Bằng cách dùng
chung mạng discovery giữa client consensus-layer và execution-layer của Ethereum,
chúng ta hưởng lợi từ việc quy mô mạng được cộng dồn, giúp tăng khả năng chống
chịu và kháng một số loại tấn công mà các mạng nhỏ dễ bị tổn thương hơn. Điều này
cũng sẽ giúp light client của cả hai mạng tìm được các node có năng lực cụ thể.

discv5 đang trong quá trình được audit.

#### What is the difference between an ENR and a multiaddr, and why are we using ENRs?

Ethereum Node Record (ENR) là các bản ghi node tự chứng thực. Node tự tạo và phát
tán ENR của chính mình, chứng minh quyền tác giả bằng một signature mật mã. ENR
được đánh chỉ số tuần tự (sequence number), cho phép giải quyết xung đột (bản
mới hơn thắng).

ENR là các bản ghi key-value với key là chuỗi ASCII. Chúng có thể lưu thông tin
tùy ý, nhưng EIP-778 quy định một bộ từ điển định sẵn, bao gồm địa chỉ IPv4 và
IPv6, public key secp256k1, v.v.

So sánh ENR với multiaddr giống như so sánh táo với cam. ENR là các container tự
chứng thực chứa danh tính, địa chỉ và metadata về một node. Multiaddr là các
chuỗi địa chỉ với đặc điểm là tự mô tả, có thể ghép nối và bền vững trước tương
lai. Một ENR có thể chứa multiaddr, và multiaddr có thể được suy ra một cách an
toàn từ các trường của một ENR đã được xác thực.

discv5 dùng ENR và có lẽ chúng ta sẽ cần:

1. Thêm `multiaddr` vào từ điển, để node có thể quảng bá multiaddr của mình dưới
   một namespace dành riêng trong ENR. – và/hoặc –
2. Định nghĩa hàm chuyển đổi hai chiều giữa multiaddr và các trường tương ứng
   (dạng phân rã) trong ENR (ip, ip6, tcp, tcp6, v.v.), để tương thích với các
   node không hỗ trợ multiaddr sẵn (ví dụ node execution-layer của Ethereum).

#### Why do we not form ENRs and find peers until genesis block/state is known?

Mặc dù phần mềm client hoàn toàn có thể đã chạy local trước khi genesis state và
block của beacon chain được chốt, client không thể tạo ENR hợp lệ trước thời điểm
này. ENR chứa `fork_digest`, vốn sử dụng `genesis_validators_root` để phân tách
rõ ràng giữa các chain; do đó trước khi biết genesis, ta không thể dùng
`fork_digest` để tìm đúng peer trên chain mà ta muốn tham gia. Khi đã biết data
genesis, ta mới có thể tạo ENR và tìm peer một cách an toàn.

Khi dùng deposit contract trên proof-of-work cho các deposit, `fork_digest` sẽ
được biết trước `genesis_time` một khoảng `GENESIS_DELAY` (7 ngày theo cấu hình
mainnet), đủ thời gian để tìm peer, thiết lập các kết nối ban đầu và các gossip
subnet trước genesis.

### Compression/Encoding

#### Why are we using SSZ for encoding?

SSZ được dùng ở consensus layer, và mọi implementation đều phải hỗ trợ
encode/decode SSZ, nên không cần thêm dependency nào vào client. Đây là lựa chọn
tự nhiên để serialize các object gửi qua mạng. Data thực tế trong hầu hết các
giao thức sẽ còn được nén thêm để tăng hiệu quả.

SSZ có schema được định nghĩa rõ cho các object đồng thuận (thường được gửi qua
mạng), giúp giảm lượng thông tin về schema serialize cần gửi đi. SSZ cũng đã định
nghĩa mọi kiểu dữ liệu cần thiết cho đặc tả mạng này.

#### Why are we compressing, and at which layers?

Chúng ta nén dữ liệu khi truyền để có payload nhỏ hơn cho mỗi thông điệp; tổng
hợp lại, điều này giúp tăng hiệu quả, tận dụng băng thông tốt hơn và giảm overhead
lưu lượng trên toàn mạng.

Hiện tại, libp2p chưa có sẵn tính năng nén có thể thương lượng động và đặt chồng
lên kết nối và stream, nhưng tính năng này
[đang được xem xét](https://github.com/libp2p/libp2p/issues/81).

Đây không phải là một tính năng đơn giản, vì cần tính tới hành vi của vòng lặp
network IO, buffer của kernel, việc chia chunk, phân mảnh gói tin, cùng nhiều yếu
tố khác. Stream của libp2p là stream không giới hạn, trong khi các thuật toán nén
hoạt động tốt nhất trên các luồng byte có giới hạn mà ta có hiểu biết trước về
chúng.

Nén thường không phải là bài toán có một lời giải cho mọi trường hợp. Nhiều biến
số cần được đánh giá cẩn thận, và các cách tiếp cận/lựa chọn chung chung thường
chỉ giảm kích thước được rất ít, thậm chí còn phản tác dụng khi tính tới đánh đổi
về CPU và bộ nhớ.

Vì tất cả những lý do trên, việc thương lượng thuật toán nén một cách tổng quát
có thể được xem là một bài toán nghiên cứu trong cộng đồng libp2p, một bài toán
chúng tôi sẵn lòng giải quyết trong trung hạn.

Ở giai đoạn này, lựa chọn khôn ngoan nhất là coi libp2p như một "người đưa thư"
chuyển byte, và để tầng ứng dụng tham gia vào việc nén các byte đó. Cách làm khác
nhau tùy theo tầng tương tác:

- Miền gossip: vì gossipsub có giao thức đóng khung (framing) và cung cấp API,
  chúng ta nén payload (khi được chỉ định bởi token encoding trong tên topic)
  trước khi publish thông điệp qua API. Không cần thêm tiền tố độ dài vì protobuf
  đã lo việc giới hạn trường ở dạng serialize.
- Miền Req/Resp: vì chúng ta định nghĩa các giao thức riêng hoạt động trên luồng
  byte, implementer được khuyến khích đóng gói logic encoding và nén vào các
  thành phần/chiến lược MessageReader và MessageWriter, có thể đặt chồng lên trên
  luồng byte thô.

#### Why are we using Snappy for compression?

Snappy được dùng trong Ethereum 1.0. Nó được Google duy trì tốt, có kết quả
benchmark tốt, và có thể tính kích thước của object chưa nén mà không cần giải nén
nó ra bộ nhớ. Điều này ngăn chặn các vector DOS trong đó kẻ tấn công gửi data
chưa nén có kích thước rất lớn.

#### Can I get access to unencrypted bytes on the wire for debugging purposes?

Có, bạn có thể thêm logger vào các protocol handler libp2p của mình để ghi log
thông điệp đến và đi. Nên dùng các design pattern để đóng gói logic logging một
cách gọn gàng.

Nếu thư viện libp2p của bạn dựa trên framework/runtime như Netty (jvm) hoặc
Node.js (javascript), bạn có thể dùng các tiện ích logging của các
framework/runtime đó để bật tính năng trace thông điệp.

Với các kịch bản test ad-hoc cụ thể, bạn có thể dùng
[secure channel plaintext/2.0.0](https://github.com/libp2p/specs/blob/master/plaintext/README.md)
(về cơ bản là không mã hóa và không xác thực thông điệp), kết hợp với tcpdump
hoặc Wireshark để xem dữ liệu truyền trên mạng.

#### What are SSZ type size bounds?

Đầu ra encoding SSZ của mỗi kiểu đều có giới hạn kích thước: mỗi kiểu động, như
list, có một "limit" có thể dùng để tính kích thước đầu ra hợp lệ tối đa. Lưu ý
rằng với một số object có độ dài động phức tạp hơn, có thể cần tính thêm các
offset của phần tử (mỗi offset 4 byte). Các kiểu khác là kiểu tĩnh, có kích thước
cố định: không có nội dung độ dài động nào, và cận dưới và cận trên bằng nhau.

Để tham khảo, giới hạn kích thước của kiểu có thể được tính trước,
[như trong ví dụ này](https://gist.github.com/protolambda/db75c7faa1e94f2464787a480e5d613e).
Nên suy ra các độ dài này từ chính định nghĩa kiểu SSZ đang dùng, để đảm bảo việc
đổi phiên bản không khiến giới hạn kiểu bị lệch (không còn khớp).

#### Why is the message size defined in terms of application payload?

Khi truyền thông điệp qua gossipsub và/hoặc miền req/resp, chúng ta muốn đảm bảo
cùng một kích thước payload được hỗ trợ bất kể transport bên dưới là gì, tách
consensus layer khỏi overhead do libp2p gây ra và khỏi chiến lược truyền tải cụ
thể.

Để suy ra "giới hạn kích thước sau encoding" từ kích thước mong muốn ở tầng ứng
dụng, chúng tôi tính tới overhead của nén snappy và framing.

Với gossipsub, giao thức hỗ trợ gửi nhiều payload ứng dụng, cũng như trộn data
ứng dụng với các thông điệp điều khiển (control message) trong mỗi frame
gossipsub. Giới hạn được đặt sao cho cho phép ít nhất một thông điệp ứng dụng có
kích thước tối đa cùng với một lượng nhỏ (1 KiB) overhead của gossipsub.
Implementation được tự do gói nhiều thông điệp ứng dụng nhỏ hơn vào một frame
gossipsub, và/hoặc kết hợp với control message tùy ý.

Giới hạn được đặt trên kích thước payload chưa nén, đặc biệt để chống lại
"decompression bomb" (dữ liệu nén nhỏ nhưng giải nén ra cực lớn).

#### Why is there a limit on message sizes at all?

Giới hạn kích thước thông điệp giúp chống lại nhiều dạng tấn công DoS và tấn công
khuếch đại qua mạng, đồng thời đặt cận trên cho việc sử dụng tài nguyên (mạng, bộ
nhớ) trong client, dựa trên các yêu cầu của giao thức về decode, đệm (buffer),
cache, lưu trữ và truyền lại thông điệp. Những yêu cầu này lại chuyển thành các
đánh đổi giữa hiệu năng và mức bảo vệ, đảm bảo có đủ năng lực xử lý các trường
hợp xấu nhất trong quá trình phục hồi sau khi mạng mất ổn định.

Đặc biệt, block — hiện là loại thông điệp duy nhất không có cận trên kích thước
thực tế suy ra từ SSZ — không thể được xác minh đầy đủ một cách đồng bộ trong các
bước kiểm tra hợp lệ của gossipsub. Điều này có nghĩa là có những trường hợp
thông điệp không hợp lệ (nhưng có chữ ký của một validator) có thể bị mạng khuếch
đại.

## libp2p implementations matrix

Phần này sẽ sớm chứa một bảng (ma trận) thể hiện mức độ trưởng thành/trạng thái
của các tính năng libp2p mà đặc tả này yêu cầu, trên các ngôn ngữ mà các client
đang được phát triển.
