# Gloas Light Client -- Full Node

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Helpers](#helpers)
  - [Modified `block_to_light_client_header`](#modified-block_to_light_client_header)

<!-- mdformat-toc end -->

## Introduction

Trong bản nâng cấp Gloas, thông tin execution payload trong light client header
được rút gọn chỉ còn block hash (kèm Merkle proof của nó).

## Helpers

### Modified `block_to_light_client_header`

*Ghi chú*: Một block trước Gloas được chuyển thành header bằng hàm của chính
fork tương ứng, rồi kết quả được nâng cấp lên bằng `upgrade_lc_header_to_gloas`.
Execution block hash và proof của nó được đọc từ payload bid, thứ mà chỉ block
Gloas mới có.

> 💡 Ghi chú: Hàm dưới đây lấy `parent_block_hash` từ
> `signed_execution_payload_bid`, tức block hash của execution payload mà block
> này xây dựng trên đó (payload của chính block này được công bố riêng trong
> envelope, không nằm trong beacon block).

```python
def block_to_light_client_header(block: SignedBeaconBlock) -> LightClientHeader:
    return LightClientHeader(
        beacon=BeaconBlockHeader(
            slot=block.message.slot,
            proposer_index=block.message.proposer_index,
            parent_root=block.message.parent_root,
            state_root=block.message.state_root,
            body_root=hash_tree_root(block.message.body),
        ),
        # [Modified in Gloas:EIP7732]
        execution_block_hash=(
            block.message.body.signed_execution_payload_bid.message.parent_block_hash
        ),
        # [Modified in Gloas:EIP7732]
        execution_branch=ExecutionBranch(
            data=compute_merkle_proof(block.message.body, EXECUTION_BLOCK_HASH_GINDEX_GLOAS)
        ),
    )
```
