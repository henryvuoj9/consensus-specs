# Ethereum Consensus Specifications

[![tests](https://github.com/ethereum/consensus-specs/actions/workflows/tests.yml/badge.svg?branch=master&event=schedule)](https://github.com/ethereum/consensus-specs/actions/workflows/tests.yml)
[![image](https://img.shields.io/pypi/v/eth-consensus-specs.svg)](https://pypi.python.org/pypi/eth-consensus-specs)
[![image](https://img.shields.io/pypi/l/eth-consensus-specs.svg)](https://pypi.python.org/pypi/eth-consensus-specs)
[![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?logo=discord&logoColor=white)](https://discord.gg/qGpsxSA)

Repository này chứa các spec (đặc tả) Ethereum
[proof-of-stake](https://ethereum.org/en/developers/docs/consensus-mechanisms/pos/)
dành cho các client ở tầng đồng thuận (consensus layer). Lý do thiết kế và các
thay đổi được đề xuất sẽ được thảo luận trong các issue. Những thay đổi đã được
thống nhất sẽ được đưa vào thông qua pull request. Các spec nằm trong thư mục
[specs](specs), được sắp xếp theo từng bản nâng cấp (upgrade). Mỗi upgrade được
xây dựng dựa trên upgrade trước đó và chỉ mô tả những gì nó thay đổi. Các
[feature](specs/_features) riêng lẻ được phát triển song song và sẽ được gộp vào
một upgrade khi đã sẵn sàng.

### Stable specifications

*(Các spec đã ổn định — đã được kích hoạt trên mainnet)*

| Seq. | Code Name     | Fork Epoch | Link                    |
| ---- | ------------- | ---------- | ----------------------- |
| 0    | **Phase0**    | `0`        | [Spec](specs/phase0)    |
| 1    | **Altair**    | `74240`    | [Spec](specs/altair)    |
| 2    | **Bellatrix** | `144896`   | [Spec](specs/bellatrix) |
| 3    | **Capella**   | `194048`   | [Spec](specs/capella)   |
| 4    | **Deneb**     | `269568`   | [Spec](specs/deneb)     |
| 5    | **Electra**   | `364032`   | [Spec](specs/electra)   |
| 6    | **Fulu**      | `411392`   | [Spec](specs/fulu)      |

### Unstable specifications

*(Các spec chưa ổn định — vẫn đang phát triển, chưa có fork epoch)*

| Seq. | Code Name | Fork Epoch | Link                |
| ---- | --------- | ---------- | ------------------- |
| 7    | **Gloas** | TBD        | [Spec](specs/gloas) |
| 8    | **Heze**  | TBD        | [Spec](specs/heze)  |

### Rendered viewers

*(Các trang hiển thị spec dưới dạng web)*

- https://ethereum.github.io/spec-viewer/
- https://ethereum.github.io/consensus-specs/

### Reference tests

- [Release assets](https://github.com/ethereum/consensus-specs/releases) (các
  tệp đính kèm theo từng bản release)
- [Nightly artifacts](https://github.com/ethereum/consensus-specs/actions/workflows/tests.yml)
  (các artifact được build hằng đêm)

### Design goals

- Giảm thiểu độ phức tạp, kể cả khi phải đánh đổi một phần hiệu năng.
- Mạng vẫn tiếp tục hoạt động (live) khi xảy ra phân mảnh mạng lớn (network
  partition) hoặc khi hàng loạt node ngừng hoạt động.
- Chọn các thành phần an toàn trước máy tính lượng tử (quantum-secure) hoặc dễ
  dàng thay thế.
- Sử dụng các kỹ thuật mật mã và thiết kế hỗ trợ được một tập validator rất lớn.
- Giảm thiểu yêu cầu phần cứng để một chiếc laptop phổ thông cũng có thể tham
  gia.

### External specifications

*(Các spec bên ngoài có liên quan)*

- [Beacon APIs](https://github.com/ethereum/beacon-apis)
- [Beacon Metrics](https://github.com/ethereum/beacon-metrics)
- [Builder Specs](https://github.com/ethereum/builder-specs)
- [Cryptography Specs](https://github.com/ethereum/cryptography-specs)
- [Deposit Contract](https://github.com/ethereum/solidity-deposit-contract)
- [Engine APIs](https://github.com/ethereum/execution-apis/tree/main/src/engine)
- [SimpleSerialize Specs](https://github.com/ethereum/ssz-specs)

### Useful resources

*(Tài liệu tham khảo hữu ích)*

- [Design Rationale](https://notes.ethereum.org/s/rkhCgQteN#) (lý do thiết kế)
- [Phase0 for Humans](https://notes.ethereum.org/s/Bkn3zpwxB) (giải thích Phase0
  dễ hiểu)
- [Combining GHOST and Casper](https://arxiv.org/abs/2003.03052) (bài báo kết
  hợp GHOST và Casper)
- [Vitalik's annotated spec](https://github.com/ethereum/annotated-spec) (spec
  có chú giải của Vitalik)
- [Upgrading Ethereum](https://eth2book.info)
