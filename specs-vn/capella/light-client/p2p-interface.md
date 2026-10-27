# Capella Light Client -- Networking

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

[Altair light client networking specification](../../altair/light-client/p2p-interface.md)
được mở rộng để trao đổi [Capella light client data](./sync-protocol.md).

> 💡 Ghi chú: Các bảng dưới đây cho biết kiểu SSZ của message/response tương ứng
> với từng `fork_version` (xác định qua fork digest / context). Từ
> `CAPELLA_FORK_VERSION` trở đi, các đối tượng light client dùng phiên bản Capella
> (có thêm thông tin execution); các fork từ Altair đến Bellatrix vẫn dùng phiên
> bản Altair; trước Altair (`GENESIS_FORK_VERSION`) thì không áp dụng (n/a).

### The gossip domain: gossipsub

#### Topics and messages

##### Global topics

###### Modified `light_client_finality_update`

<!-- eth_consensus_specs: skip -->

| `fork_version`                                         | Message SSZ type                    |
| ------------------------------------------------------ | ----------------------------------- |
| `GENESIS_FORK_VERSION`                                 | n/a                                 |
| `ALTAIR_FORK_VERSION` through `BELLATRIX_FORK_VERSION` | `altair.LightClientFinalityUpdate`  |
| `CAPELLA_FORK_VERSION` and later                       | `capella.LightClientFinalityUpdate` |

###### Modified `light_client_optimistic_update`

<!-- eth_consensus_specs: skip -->

| `fork_version`                                         | Message SSZ type                      |
| ------------------------------------------------------ | ------------------------------------- |
| `GENESIS_FORK_VERSION`                                 | n/a                                   |
| `ALTAIR_FORK_VERSION` through `BELLATRIX_FORK_VERSION` | `altair.LightClientOptimisticUpdate`  |
| `CAPELLA_FORK_VERSION` and later                       | `capella.LightClientOptimisticUpdate` |

### The Req/Resp domain

#### Messages

##### GetLightClientBootstrap

<!-- eth_consensus_specs: skip -->

| `fork_version`                                         | Response SSZ type              |
| ------------------------------------------------------ | ------------------------------ |
| `GENESIS_FORK_VERSION`                                 | n/a                            |
| `ALTAIR_FORK_VERSION` through `BELLATRIX_FORK_VERSION` | `altair.LightClientBootstrap`  |
| `CAPELLA_FORK_VERSION` and later                       | `capella.LightClientBootstrap` |

##### LightClientUpdatesByRange

<!-- eth_consensus_specs: skip -->

| `fork_version`                                         | Response chunk SSZ type     |
| ------------------------------------------------------ | --------------------------- |
| `GENESIS_FORK_VERSION`                                 | n/a                         |
| `ALTAIR_FORK_VERSION` through `BELLATRIX_FORK_VERSION` | `altair.LightClientUpdate`  |
| `CAPELLA_FORK_VERSION` and later                       | `capella.LightClientUpdate` |

##### GetLightClientFinalityUpdate

<!-- eth_consensus_specs: skip -->

| `fork_version`                                         | Response SSZ type                   |
| ------------------------------------------------------ | ----------------------------------- |
| `GENESIS_FORK_VERSION`                                 | n/a                                 |
| `ALTAIR_FORK_VERSION` through `BELLATRIX_FORK_VERSION` | `altair.LightClientFinalityUpdate`  |
| `CAPELLA_FORK_VERSION` and later                       | `capella.LightClientFinalityUpdate` |

##### GetLightClientOptimisticUpdate

<!-- eth_consensus_specs: skip -->

| `fork_version`                                         | Response SSZ type                     |
| ------------------------------------------------------ | ------------------------------------- |
| `GENESIS_FORK_VERSION`                                 | n/a                                   |
| `ALTAIR_FORK_VERSION` through `BELLATRIX_FORK_VERSION` | `altair.LightClientOptimisticUpdate`  |
| `CAPELLA_FORK_VERSION` and later                       | `capella.LightClientOptimisticUpdate` |
