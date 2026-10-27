# Sanity tests

Mục đích của các sanity test là đặt ra một mức cơ sở (base-line) về những gì
thực sự bắt buộc phải pass, tức là những phần thiết yếu nhất.

Có hai handler, mỗi handler được mô tả riêng:

- [`slots`](./slots.md): transition qua một hoặc nhiều slot (bao gồm cả các
  epoch transition nằm trong đó)
- [`blocks`](./blocks.md): transition được kích hoạt bởi một hoặc nhiều block
