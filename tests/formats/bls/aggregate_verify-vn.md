# Test format: BLS sign message

Verify signature với các pubkey và các message đã cho.

> 💡 Ghi chú: Tiêu đề gốc ghi "BLS sign message" nhưng thực chất đây là test cho
> `AggregateVerify`: mỗi pubkey ký một message riêng, và signature là bản
> aggregate của các chữ ký đó.

## Test case format

Dữ liệu test được khai báo trong file `data.yaml`:

```yaml
input:
  pubkeys: List[BLS Pubkey] -- the pubkeys
  messages: List[bytes32] -- the messages
  signature: BLS Signature -- the signature to verify against pubkeys and messages
output: bool  --  true (VALID) or false (INVALID)
```

- `BLS Pubkey` ở đây được mã hoá dưới dạng chuỗi: mã hoá hexa của 48 byte (96
  nibble), có tiền tố `0x`.
- `BLS Signature` ở đây được mã hoá dưới dạng chuỗi: mã hoá hexa của 96 byte
  (192 nibble), có tiền tố `0x`.

Mọi trường kiểu byte(s) đều được mã hoá thành chuỗi, dạng hexa, có tiền tố
`0x`.

## Condition

Handler `aggregate_verify` cần verify signature với các pubkey và message trong
`input`, và kết quả phải khớp với `output` mong đợi (`true` = VALID, `false` =
INVALID).
