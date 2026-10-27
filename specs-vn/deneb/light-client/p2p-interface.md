# Deneb Light Client -- Networking

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Networking](#networking)
  - [The gossip domain: gossipsub](#the-gossip-domain-gossipsub)
    - [Topics and messages](#topics-and-messages)
      - [Global topics](#global-topics)
        - [Modified `light_client_finality_update`](#modified-light_client_finality_update)
        - [Modified `light_client_optimistic_update`](#modified-light_client_optimistic_update)
  - [The Req/Resp domain](#the-reqresp-domain)
    - [Messages](#messages)
      - [GetLightClientBootstrap](#getlightclientbootstrap)
      - [LightClientUpdatesByRange](#lightclientupdatesbyrange)
      - [GetLightClientFinalityUpdate](#getlightclientfinalityupdate)
      - [GetLightClientOptimisticUpdate](#getlightclientoptimisticupdate)

<!-- mdformat-toc end -->

## Networking

Đặc tả networking của light client trong
[Capella light client networking specification](../../capella/light-client/p2p-interface.md)
được mở rộng để trao đổi [dữ liệu light client của Deneb](./sync-protocol.md).

> 💡 Ghi chú: Về cơ chế (topic gossip, các message Req/Resp) không có gì mới so
> với Capella. Thay đổi duy nhất là kiểu SSZ của message/response phụ thuộc vào
> `fork_version` (được xác định qua fork digest của topic gossip, hoặc
> `context` bytes của response Req/Resp): từ `DENEB_FORK_VERSION` trở đi (cột
> "and later"), dùng các container `deneb.*`. Các bảng dưới đây
> liệt kê ánh xạ này cho từng topic và từng message.

### The gossip domain: gossipsub

#### Topics and messages

##### Global topics

###### Modified `light_client_finality_update`

*(Kiểu SSZ của message trên topic `light_client_finality_update`, theo `fork_version`)*

<!-- eth_consensus_specs: skip -->

| `fork_version`                                         | Message SSZ type                    |
| ------------------------------------------------------ | ----------------------------------- |
| `GENESIS_FORK_VERSION`                                 | n/a                                 |
| `ALTAIR_FORK_VERSION` through `BELLATRIX_FORK_VERSION` | `altair.LightClientFinalityUpdate`  |
| `CAPELLA_FORK_VERSION`                                 | `capella.LightClientFinalityUpdate` |
| `DENEB_FORK_VERSION` and later                         | `deneb.LightClientFinalityUpdate`   |

###### Modified `light_client_optimistic_update`

*(Kiểu SSZ của message trên topic `light_client_optimistic_update`, theo `fork_version`)*

<!-- eth_consensus_specs: skip -->

| `fork_version`                                         | Message SSZ type                      |
| ------------------------------------------------------ | ------------------------------------- |
| `GENESIS_FORK_VERSION`                                 | n/a                                   |
| `ALTAIR_FORK_VERSION` through `BELLATRIX_FORK_VERSION` | `altair.LightClientOptimisticUpdate`  |
| `CAPELLA_FORK_VERSION`                                 | `capella.LightClientOptimisticUpdate` |
| `DENEB_FORK_VERSION` and later                         | `deneb.LightClientOptimisticUpdate`   |

### The Req/Resp domain

#### Messages

##### GetLightClientBootstrap

*(Kiểu SSZ của response cho request bootstrap, theo `fork_version`)*

<!-- eth_consensus_specs: skip -->

| `fork_version`                                         | Response SSZ type              |
| ------------------------------------------------------ | ------------------------------ |
| `GENESIS_FORK_VERSION`                                 | n/a                            |
| `ALTAIR_FORK_VERSION` through `BELLATRIX_FORK_VERSION` | `altair.LightClientBootstrap`  |
| `CAPELLA_FORK_VERSION`                                 | `capella.LightClientBootstrap` |
| `DENEB_FORK_VERSION` and later                         | `deneb.LightClientBootstrap`   |

##### LightClientUpdatesByRange

*(Kiểu SSZ của mỗi response chunk, theo `fork_version` của chunk đó)*

<!-- eth_consensus_specs: skip -->

| `fork_version`                                         | Response chunk SSZ type     |
| ------------------------------------------------------ | --------------------------- |
| `GENESIS_FORK_VERSION`                                 | n/a                         |
| `ALTAIR_FORK_VERSION` through `BELLATRIX_FORK_VERSION` | `altair.LightClientUpdate`  |
| `CAPELLA_FORK_VERSION`                                 | `capella.LightClientUpdate` |
| `DENEB_FORK_VERSION` and later                         | `deneb.LightClientUpdate`   |

##### GetLightClientFinalityUpdate

*(Kiểu SSZ của response, theo `fork_version`)*

<!-- eth_consensus_specs: skip -->

| `fork_version`                                         | Response SSZ type                   |
| ------------------------------------------------------ | ----------------------------------- |
| `GENESIS_FORK_VERSION`                                 | n/a                                 |
| `ALTAIR_FORK_VERSION` through `BELLATRIX_FORK_VERSION` | `altair.LightClientFinalityUpdate`  |
| `CAPELLA_FORK_VERSION`                                 | `capella.LightClientFinalityUpdate` |
| `DENEB_FORK_VERSION` and later                         | `deneb.LightClientFinalityUpdate`   |

##### GetLightClientOptimisticUpdate

*(Kiểu SSZ của response, theo `fork_version`)*

<!-- eth_consensus_specs: skip -->

| `fork_version`                                         | Response SSZ type                     |
| ------------------------------------------------------ | ------------------------------------- |
| `GENESIS_FORK_VERSION`                                 | n/a                                   |
| `ALTAIR_FORK_VERSION` through `BELLATRIX_FORK_VERSION` | `altair.LightClientOptimisticUpdate`  |
| `CAPELLA_FORK_VERSION`                                 | `capella.LightClientOptimisticUpdate` |
| `DENEB_FORK_VERSION` and later                         | `deneb.LightClientOptimisticUpdate`   |
