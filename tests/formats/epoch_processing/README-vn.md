# Epoch processing tests

Mỗi sub-transition (bước chuyển trạng thái con) của quá trình epoch processing
được kiểm thử riêng lẻ bằng các test handler. Format tương tự như các test
state-transition của block processing. Tuy nhiên ở đây không có yếu tố "thay đổi"
(change) nào cả: các transition là hàm thuần (pure function), chỉ nhận pre-state
làm đầu vào. Vì vậy, format này được dùng chung cho mọi test handler. (Xem tài
liệu về điều kiện kiểm thử để biết cách chạy test.)

## Test case format

### `meta.yaml`

```yaml
description: string    -- Optional description of test case, purely for debugging purposes.
                          Tests should use the directory name of the test case as identifier, not the description.
bls_setting: int       -- see general test-format spec.
```

### `pre.ssz_snappy`

Một `BeaconState` được mã hóa SSZ-snappy: state trước khi chạy sub-transition
của epoch.

### `post.ssz_snappy`

Một `BeaconState` được mã hóa SSZ-snappy: state sau khi áp dụng sub-transition
của epoch. Không có giá trị (file không tồn tại) nếu quá trình xử lý
sub-transition bị hủy bỏ (abort), tức là trường hợp không hợp lệ.

### `pre_epoch.ssz_snappy`

Tùy chọn (optional). Một `BeaconState` được mã hóa SSZ-snappy: state trước khi
chạy toàn bộ epoch transition.

Một số test case sửa đổi state giữa các sub-transition để kiểm tra riêng một
sub-transition cụ thể. Trong trường hợp đó, file này bị lược bỏ, vì
`process_epoch(pre_epoch)` sẽ không tái tạo được state đã bị sửa đổi.

### `post_epoch.ssz_snappy`

Tùy chọn (optional). Một `BeaconState` được mã hóa SSZ-snappy: state sau khi áp
dụng toàn bộ epoch transition. Không có giá trị nếu quá trình xử lý transition
bị hủy bỏ. File này bị lược bỏ trong cùng các trường hợp như
`pre_epoch.ssz_snappy`.

## Condition

Một handler của test runner `epoch_processing` cần xử lý các test case này bằng
cách gọi hàm xử lý tương ứng trong implementation (cùng tên, thêm tiền tố
`process_`). Việc này không bao gồm các phần khác của epoch transition. Pre-state
được cung cấp đã được chuyển tiếp đến ngay trước sub-transition cụ thể mà
handler đang tập trung kiểm thử.

> 💡 Ghi chú: Ví dụ, handler `registry_updates` sẽ gọi `process_registry_updates(state)`
> trên pre-state, và pre-state đó đã được chạy qua tất cả các sub-transition đứng
> trước `process_registry_updates` trong `process_epoch`.

Các sub-transition:

- `eth1_data_reset` (>=Phase0)
- `historical_roots_update` (>=Phase0,\<=Bellatrix)
- `justification_and_finalization` (>=Phase0)
- `participation_record_updates` (==Phase0)
- `randao_mixes_reset` (>=Phase0)
- `registry_updates` (>=Phase0)
- `rewards_and_penalties` (>=Phase0)
- `slashings_reset` (>=Phase0)
- `slashings` (>=Phase0)
- `inactivity_updates` (>=Altair)
- `participation_flag_updates` (>=Altair)
- `sync_committee_updates` (>=Altair)
- `historical_summaries_update` (>=Capella)
- `effective_balance_updates` (>=Electra)
- `pending_consolidations` (>=Electra)
- `pending_deposits` (>=Electra)
- `pending_randao_commitments` (>=EIP-8321)

State thu được phải khớp với `post` state mong đợi.

## Condition (alternative)

Thay vì dùng một handler riêng cho từng sub-transition, có thể dùng một handler
duy nhất cho mọi test case: load `pre_epoch` state, gọi `process_epoch`, rồi
assert rằng state thu được khớp với `post_epoch` state. Vì các file này là tùy
chọn, handler này phải bỏ qua (skip) những test case không cung cấp chúng.

Cách này có các ưu điểm:

- Ít code cần bảo trì hơn cho handler epoch processing.
- Hoạt động được với các implementation epoch processing kiểu single pass (xử lý
  tất cả trong một lượt duyệt).
- Có thể phát hiện các bug liên quan đến sự phụ thuộc dữ liệu giữa các
  sub-transition khác nhau.

Nhược điểm là điều kiện này tốn nhiều tài nguyên tính toán hơn, nhưng chỉ tăng
thêm một lượng không đổi cho mỗi test vector.
