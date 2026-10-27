# Transition testing

Các transition test bao phủ việc xử lý chuỗi khi đi qua ranh giới của một fork
(fork boundary).

Mỗi test case có một khóa `post_fork` trong `meta.yaml`, cho biết fork đích; từ
đó cũng xác định luôn fork mà test bắt đầu.

Client nên giả định các fork diễn ra tuần tự theo thứ tự sau:

0. `phase0`
1. `altair`
2. `bellatrix`
3. `capella`
4. `deneb`

Ví dụ, nếu một test case có `post_fork` là `altair`, bên chạy test nên giả định
test bắt đầu ở `phase0` và dùng spec đó để xử lý state ban đầu cùng mọi block
cho đến fork epoch. Sau khi fork xảy ra, bên chạy test nên dùng spec của fork
`altair` để xử lý phần dữ liệu còn lại.

## Test case format

### `meta.yaml`

```yaml
post_fork: string              -- String name of the spec after the fork.
fork_epoch: int                -- The epoch at which the fork takes place.
fork_block: int                -- Optional. The `<index>` of the last block on the initial fork.
blocks_count: int              -- The number of blocks processed in this test.
```

> 💡 Ghi chú: `post_fork` là tên spec sau fork; `fork_epoch` là epoch mà fork
> diễn ra; `fork_block` (tùy chọn) là `<index>` của block cuối cùng thuộc fork
> ban đầu; `blocks_count` là số block được xử lý trong test này.

*Lưu ý*: Có thể có một hàm fork transition cần chạy tại `fork_epoch`. Tham khảo
spec của fork tương ứng để biết thêm chi tiết.

### `pre.ssz_snappy`

Một `BeaconState` mã hóa SSZ-snappy theo spec của fork ban đầu: state trước khi
chạy các block transition.

### `blocks_<index>.ssz_snappy`

Một chuỗi file, với `<index>` nằm trong khoảng `[0, blocks_count)`. Các block
phải được xử lý theo thứ tự, theo đúng hàm transition chính (tức là vẫn
xử lý slot transition và epoch transition giữa các block như bình thường).

Các block được mã hóa dưới dạng `SignedBeaconBlock` theo phiên bản spec tương
ứng, được xác định bởi dữ liệu `post_fork` và `fork_block` trong `meta.yaml`.

Vì các block trải dài qua ranh giới fork, `meta.yaml` cung cấp số `fork_block`
để giúp xác định block nào thuộc về fork nào.

`fork_block` là index (trong dữ liệu test) của block **cuối cùng** thuộc fork
**ban đầu**.

Để minh họa, sơ đồ sau biểu diễn các slot bằng `_` và các block trong các slot
đó bằng `x`. Fork diễn ra tại epoch được phân tách bởi dấu `|`.

```
x   x     x x
_ _ _ _ | _ _ _ _
```

Trong trường hợp này, giá trị `blocks_count` trong `meta.yaml` là `4`, còn giá
trị `fork_block` trong `meta.yaml` là `1`. Nếu ví dụ này kiểm thử fork từ Phase 0
sang Altair, các block có index `0, 1` là các `SignedBeaconBlock` được định
nghĩa trong spec Phase 0, còn các block có index `2, 3` là các
`SignedBeaconBlock` được định nghĩa trong spec Altair.

*Lưu ý*: Nếu thiếu `fork_block`, toàn bộ dữ liệu block cần được hiểu là thuộc
về fork sau (post fork).

### `post.ssz_snappy`

Một `BeaconState` mã hóa SSZ-snappy theo spec của fork sau: state sau khi chạy
các block transition.

Nếu block cuối cùng không hợp lệ, file này sẽ không có.

## Condition

State thu được phải khớp với state `post` mong đợi. Nếu không có `post`, việc
xử lý block cuối cùng phải thất bại ở bước validation.
