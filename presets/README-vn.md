# Presets

Preset có phạm vi rộng hơn so với config lúc chạy (runtime configuration), và
thường chỉ áp dụng tại thời điểm biên dịch (compile-time). Mỗi preset được định
nghĩa dưới dạng một thư mục, với một file YAML cho mỗi fork.

Config có thể mở rộng một preset bằng cách đặt biến `PRESET_BASE`. Một bản
implementation có thể chọn chỉ hỗ trợ 1 preset cho mỗi build-target và nên kiểm
tra rằng biến `PRESET_BASE` trong config khớp với bản build đang chạy.

Các preset tiêu chuẩn:

- [`mainnet/`](./mainnet): Dùng cho mainnet, các testnet giống mainnet (ví dụ
  Hoodi), và spec-testing
- [`minimal/`](./minimal): Dùng cho các testnet phát triển cục bộ với tài nguyên
  thấp, và spec-testing

Các nhà phát triển client có thể chọn hỗ trợ thêm các preset khác, ví dụ preset
cho beacon state cực lớn để benchmark. Xem [`/configs/`](../configs) để biết về
config lúc chạy, ví dụ để cấu hình một testnet mới.

## Forking

Tương tự như [config forking](../configs/README.md#forking), preset được mở rộng
theo mỗi fork thay vì ghi đè các giá trị trước đó. Một bản implementation có thể
bỏ qua toàn bộ các file preset của các fork tương lai, và nhờ đó có thể đưa ra
cảnh báo compile-time chặt chẽ hơn đối với các biến không nhận diện được hoặc bị
thiếu trong các fork hiện tại.

## Format

Định dạng preset giống với [định dạng config](../configs/README.md#format).
