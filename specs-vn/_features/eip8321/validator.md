# EIP-8321 -- Honest Validator

*Lưu ý*: Tài liệu này vẫn đang trong quá trình soạn thảo, dành cho các nhà nghiên cứu và người triển khai (implementer).

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Prerequisites](#prerequisites)
- [Registering a RANDAO commitment](#registering-a-randao-commitment)
  - [Generating the hash chain](#generating-the-hash-chain)
  - [Constructing and broadcasting the registration](#constructing-and-broadcasting-the-registration)
  - [Replacing a lost chain](#replacing-a-lost-chain)
- [Beacon chain responsibilities](#beacon-chain-responsibilities)
  - [Block and sidecar proposal](#block-and-sidecar-proposal)
    - [Constructing the `BeaconBlockBody`](#constructing-the-beaconblockbody)
      - [Randao reveal](#randao-reveal)
      - [Hash chain reveal](#hash-chain-reveal)
      - [RANDAO commitment registrations](#randao-commitment-registrations)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này trình bày những thay đổi cần thực hiện trong code của một "honest validator" (validator trung thực) để triển khai EIP-8321.

## Prerequisites

Tài liệu này là phần mở rộng của hướng dẫn [Heze -- Honest Validator](../../heze/validator.md). Mọi hành vi và định nghĩa trong tài liệu này, cũng như trong các tài liệu mà nó mở rộng, đều được giữ nguyên trừ khi được ghi chú hoặc ghi đè một cách tường minh.

Mọi thuật ngữ, hằng số, hàm và cơ chế giao thức được định nghĩa trong [đặc tả beacon-chain của EIP-8321](./beacon-chain.md) đã cập nhật là kiến thức bắt buộc cho tài liệu này và được dùng xuyên suốt. Vui lòng xem các đặc tả beacon-chain liên quan trước khi đọc tiếp và dùng chúng làm tài liệu tham chiếu trong suốt quá trình.

## Registering a RANDAO commitment

Một validator chỉ reveal từ hash chain sau khi đã đăng ký commitment. Trước đó, nó vẫn dùng con đường BLS reveal kiểu cũ (legacy), nên việc đăng ký là tùy chọn và có thể thực hiện bất cứ lúc nào sau fork EIP-8321.

*Cảnh báo*: Một commitment chỉ có thể được đăng ký một lần và không bao giờ có thể cập nhật tại chỗ. Một validator làm mất chain secret, dùng hết chain, hoặc đăng ký một commitment mà nó không nắm giữ chain tương ứng, sẽ không thể propose được nữa, và không có cách nào khôi phục cho validator index đó. Xem mục [Replacing a lost chain](#replacing-a-lost-chain) bên dưới.

Chain secret nên được bảo vệ theo cùng tiêu chuẩn lưu giữ (custody) như signing key, và không nên được dẫn xuất từ signing key: một hash chain cuối cùng sẽ để lộ seed của nó, trong khi signing key thì tuyệt đối không bao giờ được để lộ. Chain secret cũng nên được sao lưu độc lập với signing key, vì giờ đây hai thứ này có thể hỏng/mất một cách riêng rẽ.

### Generating the hash chain

Validator lấy ngẫu nhiên đều một chain secret dài 32 byte và sinh từ đó một chain gồm `length` mắt xích (link). Các reveal được dùng theo thứ tự ngược, mỗi block được propose dùng một reveal, nên chain phải đủ dài để dùng suốt vòng đời của validator; khuyến nghị `length` tối thiểu là `2**16`. Giao thức không bao giờ biết `length`, và việc sinh cũng như lưu trữ một chain rất rẻ, nên chọn một giá trị dư dả cũng không tốn kém gì.

```python
def compute_hash_chain(chain_secret: Bytes32, length: Uint64) -> Sequence[Bytes32]:
    """
    Return the hash chain ``[c_0, ..., c_length]`` generated from
    ``chain_secret``, where ``c_0`` is the secret itself.
    """
    chain = [chain_secret]
    for _ in range(length):
        chain.append(blake3(HASH_CHAIN_RANDAO_DST + chain[-1]))
    # A link equal to UNSET_RANDAO_COMMITMENT cannot be revealed, so the chain
    # must be regenerated from a fresh secret if one occurs
    assert all(value != UNSET_RANDAO_COMMITMENT for value in chain)
    return chain
```

Validator cam kết với đầu mút (tip) của chain, `chain[length]`, và lưu chain tại máy cục bộ (hoặc lưu chain secret cùng các checkpoint định kỳ, nếu chain lớn). Validator nên xác minh commitment bằng cách duyệt toàn bộ chain trước khi đăng ký.

### Constructing and broadcasting the registration

Validator tạo một `RandaoCommitmentRegistration` chứa `validator_index` của chính nó và tip của chain làm `commitment`, ký bằng **signing key** của nó, rồi broadcast `SignedRandaoCommitmentRegistration` thu được lên global topic `randao_commitment_registration`.

```python
def get_randao_commitment_registration_signature(
    state: BeaconState, registration: RandaoCommitmentRegistration, privkey: int
) -> BLSSignature:
    domain = compute_domain(
        DOMAIN_RANDAO_COMMITMENT_REGISTRATION,
        genesis_validators_root=state.genesis_validators_root,
    )
    signing_root = compute_signing_root(registration, domain)
    return bls.Sign(privkey, signing_root)
```

Registration được đưa vào hàng đợi khi nó được đưa vào một block, và có hiệu lực sau `COMMITMENT_REGISTRATION_DELAY` epoch. Việc kích hoạt là thuộc tính của canonical state, chứ không phụ thuộc vào lịch sử broadcast của validator: nếu block chứa nó bị orphan (bị bỏ khỏi chuỗi chính), phần tử pending sẽ không bao giờ vào hàng đợi canonical. Trong trường hợp đó message vẫn hợp lệ và vẫn có thể được đưa vào block khác, nên nó nên được giữ lại trong operation pool.

*Lưu ý*: Một validator **MUST** (PHẢI) tiếp tục tạo BLS reveal kiểu cũ cho đến khi `state.randao_commitments[validator_index]` khác 0 trong state mà nó dùng để propose, ngay cả khi nó đã thấy registration của mình được đưa vào một block nào đó.

### Replacing a lost chain

Một commitment đã đăng ký thuộc về validator index của nó vĩnh viễn: nó không bao giờ bị reset — không phải khi exit, không phải khi bị slash, và không phải khi balance về 0. Validator index cũng không bao giờ được thu hồi, và một deposit có public key đã có trong registry sẽ nạp thêm (top up) vào index hiện có thay vì tạo index mới. Do đó, một validator làm mất chain không thể khôi phục index đó bằng bất kỳ chuỗi operation nào của giao thức, và deposit lại với cùng public key sẽ chỉ quay về đúng commitment "chết" đó.

Cách khắc phục là onboard một **validator mới với public key mới**, cùng một chain mới được sinh, và cho validator cũ exit để thu hồi stake. Ràng buộc là: một chain ↔ một public key ↔ một validator index, trong suốt vòng đời của index đó.

Đây là chủ ý thiết kế cùng mô hình lỗi giống như khi mất signing key, nhằm tránh phải có một operation reset và bề mặt grinding mà nó sẽ mở ra: bất kỳ cơ chế nào cho phép validator thay commitment đang hoạt động đều sẽ phải phòng chống việc validator vứt bỏ một chain bất lợi theo ý muốn. Tiền không bao giờ gặp rủi ro, và hậu quả chỉ là bỏ lỡ các lượt propose chứ không phải bị slashing.

## Beacon chain responsibilities

Mọi trách nhiệm của validator vẫn giữ nguyên, ngoại trừ những điểm được nêu bên dưới.

### Block and sidecar proposal

#### Constructing the `BeaconBlockBody`

##### Randao reveal

*Lưu ý*: Hàm `get_epoch_signature` được sửa đổi để trả về điểm vô cực (point at infinity) khi proposer đã có commitment đang hoạt động, vì hash-chain reveal thay thế cho chữ ký.

```python
def get_epoch_signature(state: BeaconState, block: BeaconBlock, privkey: int) -> BLSSignature:
    # [New in EIP8321]
    if state.randao_commitments[block.proposer_index] != UNSET_RANDAO_COMMITMENT:
        return G2_POINT_AT_INFINITY
    domain = get_domain(state, DOMAIN_RANDAO, compute_epoch_at_slot(block.slot))
    signing_root = compute_signing_root(compute_epoch_at_slot(block.slot), domain)
    return bls.Sign(privkey, signing_root)
```

##### Hash chain reveal

Đặt `block.body.hash_chain_reveal = hash_chain_reveal`, trong đó `hash_chain_reveal` được lấy từ:

```python
def get_hash_chain_reveal(
    state: BeaconState, block: BeaconBlock, chain: Sequence[Bytes32]
) -> Bytes32:
    """
    Return the next hash-chain reveal for the proposer of ``block``, where
    ``chain`` is the proposer's locally stored hash chain.

    The reveal is the preimage of the commitment currently stored in the state,
    and is empty while the proposer has no commitment registered.
    """
    commitment = state.randao_commitments[block.proposer_index]
    if commitment == UNSET_RANDAO_COMMITMENT:
        return Bytes32()

    index = chain.index(commitment)
    # The chain is exhausted once its commitment reaches the chain secret, whose
    # preimage the validator does not hold
    assert index > 0
    return chain[index - 1]
```

> 💡 Ghi chú: Hàm tìm vị trí của commitment hiện tại trong chain cục bộ và trả về mắt xích liền trước nó (`chain[index - 1]`). Nếu commitment đã là `chain[0]` (chính chain secret) thì chain đã cạn và validator không thể reveal tiếp.

##### RANDAO commitment registrations

Có thể đưa tối đa `MAX_RANDAO_COMMITMENT_REGISTRATIONS` object [`SignedRandaoCommitmentRegistration`](./beacon-chain.md#signedrandaocommitmentregistration) vào `block`. Các registration phải thỏa mãn các điều kiện xác minh trong [RANDAO commitment registration processing](./beacon-chain.md#new-process_randao_commitment_registration).

*Lưu ý*: Một node *should* (NÊN) ưu tiên các operation `SignedRandaoCommitmentRegistration` nhận được cục bộ, để đảm bảo các registration này được đưa lên chain thông qua các block do chính node công bố, ngay cả khi phần còn lại của mạng kiểm duyệt (censor) chúng.
