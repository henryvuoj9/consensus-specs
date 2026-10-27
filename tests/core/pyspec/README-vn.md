# Executable Python Spec (PySpec)

Executable Python spec (spec Python có thể chạy được) được build từ các đặc tả
đồng thuận, bổ sung thêm các hàm helper cần thiết cho hashing, BLS, v.v.

Với executable spec này, các test generator có thể dễ dàng tạo test vector cho
các client implementation, đồng thời bản thân spec cũng có thể được kiểm chứng
là nhất quán và chặt chẽ thông qua các sanity test được viết bằng pytest.

## Py-tests

Các test này không dành cho client sử dụng. Chúng kiểm thử chính bản thân spec,
nhằm xác minh tính nhất quán và đưa ra phản hồi khi spec bị sửa đổi. Tuy nhiên,
phần lớn các test có thể chạy ở chế độ generator để xuất ra test vector cho
client sử dụng.

### How to run tests

Chạy toàn bộ test:

```shell
make test
```

Chạy toàn bộ test với preset minimal:

```shell
make test preset=minimal
```

Hoặc, để chạy một test function cụ thể, chỉ định `k=<test-name>`:

```shell
make test k=test_verify_kzg_proof
```

Hoặc, để chạy toàn bộ test của một fork, chỉ định `fork=<name>`:

```shell
make test fork=phase0
```

*Lưu ý*: các tùy chọn này có thể dùng kết hợp với nhau, ví dụ:

```shell
make test preset=minimal k=test_verify_kzg_proof fork=deneb
```

### How to generate coverage reports

Chạy `make test coverage=true` để bật theo dõi coverage (độ bao phủ code) và
tạo báo cáo.

Báo cáo được lưu tại:

- **Báo cáo HTML**: `tests/core/pyspec/.htmlcov/index.html`
- **Báo cáo JSON**: `tests/core/pyspec/.htmlcov/coverage.json`

Để mở báo cáo HTML trên trình duyệt:

```shell
xdg-open tests/core/pyspec/.htmlcov/index.html   # Linux
open tests/core/pyspec/.htmlcov/index.html       # macOS
```

## Contributing

Mọi đóng góp đều được hoan nghênh, nhưng hãy cân nhắc hiện thực ý tưởng của bạn
trong chính spec trước. Pyspec không phải là thứ thay thế cho spec.

## License

Giống như bản thân spec; xem file [LICENSE](../../../LICENSE) ở thư mục gốc của
repository specs.
