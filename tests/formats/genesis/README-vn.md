# Genesis tests

Mục đích của các genesis test là cung cấp một mốc cơ sở (baseline) để kiểm thử
việc khởi tạo genesis state, và kiểm tra xem các điều kiện genesis-validity
(điều kiện để genesis hợp lệ) được đề xuất có hoạt động đúng hay không.

Có hai handler, được mô tả riêng biệt:

- [`validity`](./validity.md): Kiểm tra một genesis state có hợp lệ hay không,
  tức là nó có đủ điều kiện để kích hoạt khởi chạy chain hay không.
- [`initialization`](./initialization.md): Kiểm thử việc khởi tạo một genesis
  state dựa trên Eth1 data.
