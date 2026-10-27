# Altair -- BLS extensions

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Constants](#constants)
- [Extensions](#extensions)
  - [`eth_aggregate_pubkeys`](#eth_aggregate_pubkeys)
  - [`eth_fast_aggregate_verify`](#eth_fast_aggregate_verify)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này định nghĩa một số hàm mở rộng để xử lý BLS signature trong bản
nâng cấp Altair.

Tài liệu giả định người đọc đã nắm được
[phase 0 specification](../phase0/beacon-chain.md), bao gồm cả các định nghĩa
kiểu dữ liệu (type).

## Constants

| Name                   | Value                                  |
| ---------------------- | -------------------------------------- |
| `G2_POINT_AT_INFINITY` | `BLSSignature(b"\xc0" + b"\x00" * 95)` |

> 💡 Ghi chú: `G2_POINT_AT_INFINITY` là dạng nén (compressed) của điểm vô cực
> trên nhóm G2 — tức "chữ ký rỗng". Nó được dùng làm chữ ký hợp lệ khi không có
> public key nào tham gia (xem `eth_fast_aggregate_verify` bên dưới).

## Extensions

### `eth_aggregate_pubkeys`

Định nghĩa thêm hàm `AggregatePKs` để mở rộng đặc tả
[IETF BLS signature draft standard v4](https://tools.ietf.org/html/draft-irtf-cfrg-bls-signature-04)
đã được tham chiếu trong tài liệu phase 0. Hàm này gộp (aggregate) nhiều public
key thành một public key duy nhất bằng phép cộng điểm trên đường cong elliptic.

```python
def eth_aggregate_pubkeys(pubkeys: Sequence[BLSPubkey]) -> BLSPubkey:
    """
    Return the aggregate public key for the public keys in ``pubkeys``.

    Note: the ``+`` operation should be interpreted as elliptic curve point addition, which takes as input
    elliptic curve points that must be decoded from the input ``BLSPubkey``s.
    This implementation is for demonstrative purposes only and ignores encoding/decoding concerns.
    Refer to the BLS signature draft standard for more information.
    """
    assert len(pubkeys) > 0
    # Ensure that the given inputs are valid pubkeys
    assert all(bls.KeyValidate(pubkey) for pubkey in pubkeys)

    result = pubkeys[0].copy()
    for pubkey in pubkeys[1:]:
        result += pubkey
    return result
```

### `eth_fast_aggregate_verify`

Hàm bao (wrapper) quanh `bls.FastAggregateVerify`. Khác biệt duy nhất: nếu danh
sách `pubkeys` rỗng và chữ ký bằng `G2_POINT_AT_INFINITY` thì hàm trả về `True`
(trong khi `FastAggregateVerify` chuẩn sẽ từ chối trường hợp danh sách rỗng).
Điều này cần thiết cho sync committee: một block có thể không có thành viên sync
committee nào tham gia ký.

```python
def eth_fast_aggregate_verify(
    pubkeys: Sequence[BLSPubkey], message: Bytes32, signature: BLSSignature
) -> bool:
    """
    Wrapper to ``bls.FastAggregateVerify`` accepting the ``G2_POINT_AT_INFINITY`` signature when ``pubkeys`` is empty.
    """
    if len(pubkeys) == 0 and signature == G2_POINT_AT_INFINITY:
        return True
    return bls.FastAggregateVerify(pubkeys, message, signature)
```
