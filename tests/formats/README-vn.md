# General test format

Tài liệu này định nghĩa định dạng YAML và cấu trúc được dùng cho việc kiểm thử
consensus spec.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [About](#about)
  - [Test-case formats](#test-case-formats)
- [Glossary](#glossary)
- [Test format philosophy](#test-format-philosophy)
  - [Config design](#config-design)
  - [Test completeness](#test-completeness)
- [Test structure](#test-structure)
  - [`<config name>/`](#config-name)
  - [`<fork or phase name>/`](#fork-or-phase-name)
  - [`<test runner name>/`](#test-runner-name)
  - [`<test handler name>/`](#test-handler-name)
  - [`<test suite name>/`](#test-suite-name)
  - [`<test case>/`](#test-case)
  - [`<output part>`](#output-part)
    - [Common output formats](#common-output-formats)
    - [Special output parts](#special-output-parts)
      - [`meta.yaml`](#metayaml)
      - [`manifest.yaml`](#manifestyaml)
      - [`config.yaml`](#configyaml)
- [Config sourcing](#config-sourcing)
- [Note for implementers](#note-for-implementers)

<!-- mdformat-toc end -->

## About

Consensus layer dùng YAML làm định dạng cho mọi bài test dùng chung giữa các
client (cross-client test). Tài liệu này mô tả ở mức tổng quan định dạng chung
mà mọi file test cần tuân theo.

### Test-case formats

Định dạng cụ thể của từng loại test (test suite) được định nghĩa trong các tài
liệu riêng.

Các test format:

- [`bls`](./bls/README.md)
- [`epoch_processing`](./epoch_processing/README.md)
- [`genesis`](./genesis/README.md)
- [`operations`](./operations/README.md)
- [`sanity`](./sanity/README.md)
- [`shuffling`](./shuffling/README.md)
- [`ssz_static`](./ssz_static/README.md)
- Còn nhiều format khác đang được lên kế hoạch, xem các tracking issue về
  CI/testing

## Glossary

*(Bảng thuật ngữ)*

- `generator`: một chương trình sinh ra một hoặc nhiều test case, mỗi test case
  được tổ chức theo phân cấp `config > runner > handler > suite`.
- `config`: các test được nhóm theo cấu hình (configuration) dùng cho spec
  preset. Ngoài các cấu hình chuẩn, có thể dùng `general` làm nhóm chung cho các
  test không bị giới hạn trong một cấu hình cụ thể (ví dụ: BLS).
- `type`: sự chuyên biệt hoá của một `generator` duy nhất. Ví dụ: epoch
  processing.
- `runner`: nếu generator là *"bên sản xuất" (producer)* thì runner là *"bên
  tiêu thụ" (consumer)*.
  - Một `runner` chỉ tập trung vào *duy nhất một* `type`, và mỗi type có *duy
    nhất một* `runner`.
- `handler`: đôi khi một `runner` là quá hạn chế, bạn có thể có một tập test
  với trọng tâm riêng cần một format khác. Để hỗ trợ việc này, bạn chỉ định một
  `handler`: runner có thể xử lý format đó bằng cách dùng handler được chỉ
  định.
- `suite`: một thư mục chứa các test case có liên quan chặt chẽ với nhau. Mọi
  `suite` dưới cùng một `handler` dùng chung một format. Đây là một tầng phân
  cấp mang tính tổ chức/hình thức.
- `case`: một test case, là một thư mục nằm trong `suite`. Về tổng quát, một
  case có thể là bất cứ thứ gì, nhưng format của nó cần được định nghĩa rõ ràng
  trong tài liệu tương ứng với `type` (và `handler`).
- `case part`: một test case gồm nhiều file khác nhau, có thể ở các format khác
  nhau, để phục vụ tốt hơn cho format cụ thể của test case. Tuỳ chọn, có thể kèm
  một file `meta.yaml` để khai báo meta-data cho test, ví dụ yêu cầu về BLS.

## Test format philosophy

*(Triết lý thiết kế test format)*

### Config design

Các loại hằng số cấu hình gồm:

- Không bao giờ thay đổi: dữ liệu genesis.
- Thay đổi, nhưng phụ thuộc vào giá trị cũ: ví dụ thời lượng một epoch có thể
  thay đổi, nhưng nếu muốn thực hiện phép chuyển đổi
  `(genesis data, timestamp) -> epoch number`, bạn sẽ cần cả hai hằng số.
- Thay đổi, nhưng vẫn được giữ lại trong giai đoạn chuyển fork: việc finalization
  có thể mất một khoảng thời gian, ví dụ một chương trình phải xử lý cả deposit
  mới và deposit cũ cùng lúc. Một ví dụ khác là các hằng số kinh tế.
- Bổ sung, tương thích ngược: các hằng số mới được thêm vào cho các phase sau.
- Thay đổi: có một khả năng rất nhỏ là một hằng số nào đó thực sự bị *thay thế*.
  Trong trường hợp hiếm này, tốt hơn là thêm nó như một biến bổ sung, và một số
  client có thể đơn giản là ngừng hỗ trợ biến cũ nếu họ không muốn sync từ
  genesis. Việc thay đổi chức năng sẽ trải qua một giai đoạn deprecate
  (ngừng khuyến khích dùng) hằng số cũ, và cuối cùng chỉ còn hằng số mới được
  giữ lại trong config (khi state cũ không còn được hỗ trợ nữa).

Dựa trên các loại thay đổi này, chúng ta mô hình hoá config thành một danh sách
các cặp key-value, chỉ tăng thêm qua mỗi fork (tuy nhiên chúng có thể thay đổi
trong các phiên bản đang phát triển của fork; việc này do git quản lý). Với cách
tiếp cận này, các cấu hình tương thích ngược (client cũ bỏ qua các biến mà nó
không biết) và dễ bảo trì.

### Test completeness

*(Tính đầy đủ, tự chứa của test)*

Test cần độc lập với mọi dữ liệu sync. Nếu muốn chạy một test, dữ liệu đầu vào
phải có sẵn từ YAML. Mục tiêu là cung cấp cho client một phạm vi công việc được
xác định rõ để chạy một tập test suite cụ thể.

- Các client đã hoàn chỉnh được kỳ vọng sẽ đóng góp vào việc kiểm thử, tìm kiếm
  nguồn lực tốt hơn để đạt được sự tuân thủ (conformance) với spec và với các
  client khác.
- Các client chưa hoàn chỉnh về chức năng có thể chọn bỏ qua các suite dùng một
  số test-runner nhất định, hoặc các handler cụ thể của các test-runner đó.
- Các client đang ở phiên bản cũ có thể kiểm thử dựa trên các bản release cũ
  hơn của bộ test được sinh ra, và bắt kịp các bản release mới hơn khi có thể.

## Test structure

```
File path structure:
tests/<config name>/<fork or phase name>/<test runner name>/<test handler name>/<test suite name>/<test case>/<output part>
```

### `<config name>/`

Config nằm ở tầng trên cùng. Một số client muốn chạy cấu hình minimal trước,
và điều này cũng hữu ích cho các bước kiểm tra sanity trong quá trình phát
triển. Vì là thư mục cấp cao nhất nên nó không bị lặp lại, và config được dùng
có thể được sao chép thẳng vào thư mục này để tham chiếu.

### `<fork or phase name>/`

Ví dụ: "phase0", "altair", v.v. Mỗi fork bổ sung các test mới, và sửa đổi các
test có thay đổi: một số test của các fork trước được lặp lại với dữ liệu state
đã cập nhật.

### `<test runner name>/`

Các runner quen thuộc như bls/shuffling/ssz_static/operations/epoch_processing/v.v.
Handler có thể thay đổi format, nhưng mỗi runner có một mục tiêu kiểm thử chung.

### `<test handler name>/`

Chuyên biệt hoá bên trong một nhóm (category). Mọi suite trong đây sẽ có cùng
format test case. Việc dùng `handler` trong `runner` là tuỳ chọn. Có thể dùng
handler `core` (hoặc một handler chung khác) nếu `runner` không có các format
khác nhau.

### `<test suite name>/`

Các suite được tách riêng. Kích thước suite (tức số lượng test) không làm thay
đổi yêu cầu bộ nhớ tối đa, vì các test case có thể được nạp lần lượt từng cái
một. Điều này cũng giúp việc nạp các tập test đã lọc trở nên nhanh và dễ dàng.

### `<test case>/`

Các case cũng được tách riêng. Điều này cho phép diff từng phần của test case,
theo dõi thay đổi theo từng phần, trong khi vẫn dùng LFS. Nó cũng cho phép dùng
format khác nhau cho một số phần.

### `<output part>`

Các file này cho phép dùng format tuỳ biến cho một số phần của test. Ví dụ: dữ
liệu được mã hoá SSZ. Hoặc để tránh file lớn, dữ liệu SSZ có thể được nén bằng
Snappy. Ví dụ: `pre.ssz_snappy`, `deposit.ssz_snappy`, `post.ssz_snappy`.

Việc diff `pre.ssz_snappy` và `post.ssz_snappy` cung cấp toàn bộ thông tin cần
cho việc kiểm thử, sau khi giải nén và giải mã. Sau đó, sự khác biệt giữa pre
và post có thể được đối chiếu với bất cứ thứ gì làm thay đổi pre state, ví dụ
`deposit.ssz_snappy`

Lưu ý rằng mặc định, dữ liệu SSZ ở phiên bản <fork or phase name> của test case
tương ứng, ví dụ nếu đó là test case `altair`, hãy dùng container
`altair.BeaconState` để giải tuần tự hoá (deserialize) state đã cho.

YAML thường được dùng cho metadata của test, và cho các test không dùng SSZ: ví
dụ test shuffling và BLS. Trong trường hợp này, không có lý do gì để thêm các
kiểu SSZ đặc biệt. Kích thước và hiệu năng của YAML là chấp nhận được.

#### Common output formats

Giữa tất cả các loại test, có một vài format dùng chung:

- **`.yaml`**: File YAML chứa dữ liệu có cấu trúc để mô tả thiết lập hoặc nội
  dung test.
- **`.ssz`**: File chứa dữ liệu thô được mã hoá SSZ. Trước đây được dùng rộng
  rãi trong test, nhưng đã được thay bằng biến thể nén.
- **`.ssz_snappy`**: Giống `.ssz`, nhưng được nén bằng Snappy block compression.
  Snappy block compression vốn đã được áp dụng cho SSZ trong gossip của
  consensus layer và có sẵn trong các client implementation, vì vậy được chọn
  làm phương thức nén.

#### Special output parts

##### `meta.yaml`

Nếu có (file này là tuỳ chọn), test được bổ sung thêm dữ liệu để mô tả cách sử
dụng. Dữ liệu chuyên biệt được mô tả trong tài liệu của từng test format cụ thể.

Dữ liệu chung được mô tả tại đây:

Một số test-case format có chung một số mẫu cặp key-value, và chúng được mô tả
tại đây:

```
bls_setting: int     -- optional, can have 3 different values:
                            0: (default, applies if key-value pair is absent). Free to choose either BLS ON or OFF.
                                 Tests are generated with valid BLS data in this case,
                                 but there is no change of outcome when running the test if BLS is ON or OFF.
                            1: known as "BLS required" - if the test validity is strictly dependent on BLS being ON
                            2: known as "BLS ignored"  - if the test validity is strictly dependent on BLS being OFF
```

> 💡 Ghi chú: `bls_setting` là tuỳ chọn, có 3 giá trị: `0` (mặc định, áp dụng
> khi không có key này) – client được tự do bật hoặc tắt BLS; test được sinh với
> dữ liệu BLS hợp lệ nên kết quả không đổi dù BLS bật hay tắt. `1` ("BLS
> required") – tính hợp lệ của test phụ thuộc chặt chẽ vào việc BLS được BẬT.
> `2` ("BLS ignored") – tính hợp lệ của test phụ thuộc chặt chẽ vào việc BLS
> bị TẮT.

##### `manifest.yaml`

Có trong mọi test case. Chứa metadata dùng để định danh test vector:

```yaml
preset: minimal      # Preset (mainnet, minimal, general)
fork: phase0         # Fork/phase name
runner: bls          # Test runner category
handler: eth_aggregate_pubkeys  # Specific handler
suite: bls           # Test suite name
case: eth_aggregate_pubkeys_valid_0  # Individual test case name
```

Metadata này trùng lặp với thông tin vốn đã được mã hoá trong đường dẫn thư
mục:

```
tests/<preset>/<fork>/<runner>/<handler>/<suite>/<case>/
```

Việc lưu nó trong một file giúp test vector có thể được di chuyển hoặc phân phối
mà không bị mất ngữ cảnh.

##### `config.yaml`

Các giá trị cấu hình lúc chạy (runtime-configurable) có thể khác nhau cho từng
test cụ thể. Khi có file này, nó thay thế runtime-config mặc định đi kèm với các
thiết lập preset vốn được cố định lúc biên dịch (compile-time).

Format giống với `mainnet_config.yaml` và `minimal_config.yaml`, xem tài liệu
[`/configs`](../../configs/README.md#format). Các giá trị config được giới
thiệu ở fork sau có thể bị lược bỏ khỏi test của các fork trước đó.

## Config sourcing

*(Nguồn của các config)*

Các cấu hình hằng số nằm tại:

```
<specs repo root>/configs/<config name>.yaml
```

Và được CI sao chép phục vụ mục đích kiểm thử tới:

```
<tests repo root>/tests/<config name>/<config name>.yaml
```

`<config name>` đầu tiên là một thư mục, chứa chính xác tất cả các test sử dụng
config đó.

## Note for implementers

*(Ghi chú cho người triển khai client)*

Mẫu cơ bản để nạp và chạy test suite là:

1. Với một config cụ thể, nạp nó trước (và chỉ cần làm một lần), sau đó tiếp tục
   với các test được định nghĩa trong thư mục config đó.
2. Chọn một fork. Lặp lại cho từng fork nếu chạy test cho nhiều fork.
3. Chọn nhóm (category) và chuyên biệt hoá cần quan tâm (ví dụ
   `operations > deposits`). Một lần nữa, lặp lại cho từng cái nếu chạy tất cả.
4. Chọn một test suite. Hoặc lặp lại cho từng suite.
5. Chọn một test case. Hoặc lặp lại cho từng case.
6. Nạp các phần của case. Gồm `manifest.yaml` và `meta.yaml` nếu có.
7. Chạy test, theo đúng định nghĩa của test format.

Bước 1 có thể là một bước chọn cấu hình lúc biên dịch (compile time), nếu muốn
tối ưu hoá. Yêu cầu cơ bản chỉ là dùng cùng một tập hằng số, độc lập với quá
trình nạp.
