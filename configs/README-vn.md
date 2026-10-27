# Configurations

Thư mục này chứa tập hợp các config (cấu hình) dùng cho việc test, các testnet
và mainnet. Một bản binary của client có thể được biên dịch cho một
`PRESET_BASE` cụ thể, sau đó nạp các config khác nhau dựa trên preset đó để tham
gia vào các mạng hoặc các bài test khác nhau.

Các config tiêu chuẩn:

- [`mainnet.yaml`](./mainnet.yaml): Config cho mainnet
- [`minimal.yaml`](./minimal.yaml): Config tối giản, dùng trong spec-testing
  cùng với preset [`minimal`](../presets/minimal).

Không phải mọi config mạng đều thuộc phạm vi của spec. Xem
[`github.com/eth-clients/eth2-networks`](https://github.com/eth-clients/eth2-networks)
để có config của các mạng phổ biến và các tài nguyên bổ sung cho testnet.

## Forking

Các biến không bị thay thế mà được mở rộng theo từng fork. Mục đích là để hỗ trợ
việc sync từ một state sang state khác vượt qua ranh giới fork, mà không cần
thay nóng (hot-swap) config. Thay vào đó, với những fork có thay đổi giá trị của
một biến, tên biến sẽ được thêm hậu tố là tên fork, ví dụ
`INACTIVITY_PENALTY_QUOTIENT_ALTAIR`.

Các biến của fork tương lai có thể được bỏ qua, ví dụ một client hiện chỉ hỗ trợ
Phase 0 có thể bỏ qua các biến của Sharding.

Theo thời gian, nhu cầu sync một state cũ có thể không còn nữa. Khi đó, hậu tố
của biến mới có thể được bỏ đi, và biến cũ sẽ mang một tên đặc biệt trước khi bị
xoá hoàn toàn.

Một cách làm forking trước đây từng sử dụng "timelines", nhưng cách này xung đột
với các định nghĩa dùng trong spec (các biến cho slot fork đặc biệt, v.v.), và
không được tích hợp đủ tốt vào bất kỳ công cụ spec hay bản implementation nào.
Thay vào đó, hiện nay bản thân config đóng vai trò luôn là định nghĩa fork, ví
dụ thay đổi giá trị của `ALTAIR_FORK_EPOCH` sẽ thay đổi thời điểm fork.

## Format

Mỗi preset và config là một ánh xạ key-value.

**Key**: một chuỗi định dạng `UPPER_SNAKE_CASE` (còn gọi là "macro case"), là
tên của biến.

**Value** có thể là:

- một số nguyên không dấu, tối đa 64 bit (bao gồm cả 64)
- một chuỗi hexa, có tiền tố `0x`

Định dạng này hoàn toàn tương thích với YAML. Các preset và config có thể chứa
comment để mô tả các giá trị.
