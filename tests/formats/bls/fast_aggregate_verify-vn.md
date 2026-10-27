# Test format: BLS fast aggregate verify

Verify signature với các pubkey đã cho và một message duy nhất.

> 💡 Ghi chú: "Fast" aggregate verify áp dụng khi tất cả pubkey cùng ký trên
> cùng một message, nên có thể aggregate các pubkey trước rồi verify một lần.

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

Handler `fast_aggregate_verify` cần verify signature với các pubkey và message
trong `input`, và kết quả phải khớp với `output` mong đợi.
