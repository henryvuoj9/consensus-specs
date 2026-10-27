# Test format: BLS sign message

Việc ký một message bằng BLS phải tạo ra một signature.

## Test case format

Dữ liệu test được khai báo trong file `data.yaml`:

```yaml
input:
  privkey: bytes32 -- the private key used for signing
  message: bytes32 -- input message to sign (a hash)
output: BLS Signature -- expected output, single BLS signature or `null`.
```

- Mọi trường kiểu byte(s) đều được mã hoá thành chuỗi, dạng hexa, có tiền tố
  `0x`.
- Giá trị output là `null` nếu input không hợp lệ.

## Condition

Handler `sign` cần ký `message` bằng `privkey` (private key), và signature thu
được phải khớp với `output` mong đợi.
