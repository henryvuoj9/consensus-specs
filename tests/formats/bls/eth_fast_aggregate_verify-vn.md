# Test format: Ethereum-customized BLS fast aggregate verify

Verify signature với các pubkey đã cho và một message duy nhất.

> 💡 Ghi chú: Đây là phiên bản tuỳ biến cho Ethereum của `FastAggregateVerify`
> (tất cả pubkey cùng ký một message). Điểm khác biệt chính: với danh sách
> pubkey rỗng và signature là điểm vô cực (G2 point at infinity), kết quả là
> `true` thay vì `false`.

## Test case format

Dữ liệu test được khai báo trong file `data.yaml`:

```yaml
input:
  pubkeys: List[BLS Pubkey] -- list of input BLS pubkeys
  message: bytes32 -- the message
  signature: BLS Signature -- the signature to verify against pubkeys and message
output: bool  --  true (VALID) or false (INVALID)
```

- `BLS Pubkey` ở đây được mã hoá dưới dạng chuỗi: mã hoá hexa của 48 byte (96
  nibble), có tiền tố `0x`.
- `BLS Signature` ở đây được mã hoá dưới dạng chuỗi: mã hoá hexa của 96 byte
  (192 nibble), có tiền tố `0x`.

Mọi trường kiểu byte(s) đều được mã hoá thành chuỗi, dạng hexa, có tiền tố
`0x`.

## Condition

Handler `eth_fast_aggregate_verify` cần verify signature với các pubkey và
message trong `input`, và kết quả phải khớp với `output` mong đợi.
