# BLS tests

Một loại test dành cho BLS. Chủ yếu nhằm kiểm tra việc *tích hợp* (integration)
một thư viện BLS bất kỳ. Chúng tôi không khuyến khích tự viết thư viện mật mã
(rolling your own crypto) hoặc dùng một thư viện BLS chưa được kiểm thử.

BLS test suite runner có các handler sau:

- [`aggregate_verify`](./aggregate_verify.md)
- [`aggregate`](./aggregate.md)
- [`eth_aggregate_pubkeys`](./eth_aggregate_pubkeys.md)
- [`eth_fast_aggregate_verify`](./eth_fast_aggregate_verify.md)
- [`fast_aggregate_verify`](./fast_aggregate_verify.md)
- [`sign`](./sign.md)
- [`verify`](./verify.md)

*Lưu ý*: Các test case về signature-verification và aggregate-verify hiện chưa
được hỗ trợ.
