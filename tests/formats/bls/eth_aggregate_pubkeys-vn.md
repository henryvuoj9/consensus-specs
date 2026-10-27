# Test format: Ethereum-customized BLS pubkey aggregation

Việc aggregate BLS pubkey kết hợp một chuỗi các pubkey thành một pubkey duy
nhất.

## Test case format

Dữ liệu test được khai báo trong file `data.yaml`:

```yaml
input: List[BLS Pubkey] -- list of input BLS pubkeys
output: BLSPubkey -- expected output, single BLS pubkeys or `null`.
```

- `BLS Pubkey` ở đây được mã hoá dưới dạng chuỗi: mã hoá hexa của 48 byte (96
  nibble), có tiền tố `0x`.
- Giá trị output là `null` nếu input không hợp lệ.

## Condition

Handler `eth_aggregate_pubkeys` cần aggregate các signature trong `input`, và
kết quả phải khớp với `output` mong đợi.

> 💡 Ghi chú: Câu gốc ghi "signatures", nhưng thực tế handler này aggregate các
> pubkey trong `input`.
