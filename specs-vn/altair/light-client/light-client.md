# Altair Light Client -- Light Client

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Light client sync process](#light-client-sync-process)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này giải thích cách light client (client nhẹ) MAY (CÓ THỂ) lấy dữ liệu
light client để sync với mạng.

## Light client sync process

1. Light client MUST (PHẢI) được cấu hình từ bên ngoài (out-of-band, tức không
   qua mạng P2P) với một spec/preset (bao gồm lịch các fork), với
   `genesis_state` (bao gồm `genesis_time` và `genesis_validators_root`), và với
   một block root đáng tin cậy (trusted block root). Block đáng tin cậy này
   SHOULD (NÊN) nằm trong weak subjectivity period, và root của nó SHOULD lấy từ
   một `Checkpoint` đã finalized.
2. Đồng hồ cục bộ được khởi tạo dựa trên `genesis_time` đã cấu hình, và fork
   digest hiện tại được xác định để tìm kiếm và kết nối tới các nhà cung cấp dữ
   liệu light client phù hợp.
3. Light client tải về một đối tượng
   [`LightClientBootstrap`](./sync-protocol.md#lightclientbootstrap) cho trusted
   block root đã cấu hình. Đối tượng `bootstrap` được truyền vào
   [`initialize_light_client_store`](./sync-protocol.md#initialize_light_client_store)
   để tạo ra một [`LightClientStore`](./sync-protocol.md#lightclientstore) cục
   bộ.
4. Light client theo dõi các sync committee period: `finalized_period` tính từ
   `store.finalized_header.beacon.slot`, `optimistic_period` tính từ
   `store.optimistic_header.beacon.slot`, và `current_period` tính từ
   `current_slot` dựa trên đồng hồ cục bộ.
   1. Khi `finalized_period == optimistic_period` và
      [`is_next_sync_committee_known`](./sync-protocol.md#is_next_sync_committee_known)
      trả về `False`, light client tải một
      [`LightClientUpdate`](./sync-protocol.md#lightclientupdate) cho
      `finalized_period`. Nếu `finalized_period == current_period`, việc tải này
      SHOULD được lên lịch vào một thời điểm ngẫu nhiên trước khi
      `current_period` chuyển sang period tiếp theo.
   2. Khi `finalized_period + 1 < current_period`, light client tải một
      `LightClientUpdate` cho mỗi sync committee period trong khoảng
      `[finalized_period + 1, current_period)` (không bao gồm period hiện tại)
   3. Khi `finalized_period + 1 >= current_period`, light client tiếp tục theo
      dõi các
      [`LightClientFinalityUpdate`](./sync-protocol.md#lightclientfinalityupdate)
      và
      [`LightClientOptimisticUpdate`](./sync-protocol.md#lightclientoptimisticupdate).
      Các đối tượng nhận được sẽ được truyền vào
      [`process_light_client_finality_update`](./sync-protocol.md#process_light_client_finality_update)
      và
      [`process_light_client_optimistic_update`](./sync-protocol.md#process_light_client_optimistic_update).
      Điều này đảm bảo `finalized_header` và `optimistic_header` luôn phản ánh
      các block mới nhất.
5. [`process_light_client_store_force_update`](./sync-protocol.md#process_light_client_store_force_update)
   MAY được gọi dựa trên các heuristic tùy theo trường hợp sử dụng nếu quá trình
   sync của light client có vẻ bị kẹt. Nếu có thể, nên ưu tiên chuyển sang một
   cơ chế sync thay thế để bao phủ sync committee period bị ảnh hưởng.

> 💡 Ghi chú: Tóm lại, light client "nhảy" từng sync committee period một (mỗi
> period khoảng ~27 giờ): biết sync committee của period hiện tại thì có thể xác
> minh `LightClientUpdate` chứa `next_sync_committee`, từ đó tiến sang period kế
> tiếp. Khi đã bắt kịp period hiện tại, nó chỉ cần nghe finality update và
> optimistic update để cập nhật header mới nhất.
