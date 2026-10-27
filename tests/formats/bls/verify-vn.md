# Test format: BLS sign message

Verify signature với một pubkey và một message đã cho.

## Test case format

Dữ liệu test được khai báo trong file `data.yaml`:

```yaml
input:
  pubkey: bytes48 -- the pubkey
  message: bytes32 -- the message
  signature: bytes96 -- the signature to verify against pubkey and message
output: bool  -- VALID or INVALID
```

Mọi trường kiểu byte(s) đều được mã hoá thành chuỗi, dạng hexa, có tiền tố
`0x`.
