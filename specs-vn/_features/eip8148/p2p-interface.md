# EIP-8148 -- Networking

*Lưu ý*: Tài liệu này vẫn đang được soạn thảo, dành cho các nhà nghiên cứu và
người triển khai.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Helpers](#helpers)
  - [Modified `compute_fork_version`](#modified-compute_fork_version)
- [The gossip domain: gossipsub](#the-gossip-domain-gossipsub)
  - [Topics and messages](#topics-and-messages)
    - [Global topics](#global-topics)
      - [Modified `beacon_block`](#modified-beacon_block)
      - [Modified `execution_payload`](#modified-execution_payload)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này chứa đặc tả networking của consensus layer cho EIP-8148.

Đặc tả các thay đổi này tiếp nối theo cùng định dạng với đặc tả networking của
các bản nâng cấp trước, và coi các đặc tả đó là điều kiện tiên quyết (đã được
áp dụng).

## Helpers

### Modified `compute_fork_version`

```python
def compute_fork_version(epoch: Epoch) -> Version:
    """
    Return the fork version at the given ``epoch``.
    """
    if epoch >= EIP8148_FORK_EPOCH:
        return EIP8148_FORK_VERSION
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

## The gossip domain: gossipsub

### Topics and messages

#### Global topics

##### Modified `beacon_block`

*[Modified in EIP8148]*

**Added in EIP8148:**

- _[REJECT]_ Số lượng phần tử của
  `block.body.parent_execution_requests.sweep_thresholds` nằm trong giới hạn cho
  phép -- tức là kiểm tra rằng
  `len(block.body.parent_execution_requests.sweep_thresholds) <= MAX_SET_SWEEP_THRESHOLD_REQUESTS_PER_PAYLOAD`.

##### Modified `execution_payload`

*[Modified in EIP8148]*

**Added in EIP8148:**

- _[REJECT]_ Số lượng phần tử của `execution_requests.sweep_thresholds` nằm
  trong giới hạn cho phép -- tức là kiểm tra rằng
  `len(execution_requests.sweep_thresholds) <= MAX_SET_SWEEP_THRESHOLD_REQUESTS_PER_PAYLOAD`,
  với alias `execution_requests = envelope.execution_requests`.
