# Phase 0 -- Deposit Contract

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Types](#types)
  - [`ExecutionAddress`](#executionaddress)
- [Constants](#constants)
- [Configs](#configs)
- [Staking deposit contract](#staking-deposit-contract)
  - [`deposit` function](#deposit-function)
    - [Deposit amount](#deposit-amount)
    - [Withdrawal credentials](#withdrawal-credentials)
    - [`DepositEvent` log](#depositevent-log)
- [Solidity code](#solidity-code)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này là đặc tả cho deposit contract (hợp đồng nạp tiền) của beacon
chain, thuộc Phase 0.

## Types

### `ExecutionAddress`

```python
class ExecutionAddress(Bytes20):
    """
    The address of an account on the execution layer.
    """
```

*(Địa chỉ của một tài khoản trên execution layer.)*

## Constants

Các giá trị sau là hằng số (không cấu hình được) được dùng xuyên suốt đặc tả.

| Name                          | Value                 |
| ----------------------------- | --------------------- |
| `DEPOSIT_CONTRACT_TREE_DEPTH` | `Uint64(2**5)` (= 32) |

## Configs

*Lưu ý*: Các giá trị cấu hình mặc định của mainnet được đưa vào đây phục vụ cho
mục đích thiết kế đặc tả.

| Name                       | Value                                                            |
| -------------------------- | ---------------------------------------------------------------- |
| `DEPOSIT_CHAIN_ID`         | `Uint64(1)`                                                      |
| `DEPOSIT_NETWORK_ID`       | `Uint64(1)`                                                      |
| `DEPOSIT_CONTRACT_ADDRESS` | `ExecutionAddress("0x00000000219ab540356cBB839Cbe05303d7705Fa")` |

## Staking deposit contract

Các giai đoạn triển khai ban đầu của Ethereum proof-of-stake được thực hiện mà
không cần thay đổi consensus của chain Ethereum proof-of-work hiện có. Một
deposit contract tại địa chỉ `DEPOSIT_CONTRACT_ADDRESS` được thêm vào chain
Ethereum proof-of-work, được xác định bởi
[chain-id](https://eips.ethereum.org/EIPS/eip-155) -- `DEPOSIT_CHAIN_ID` -- và
network-id -- `DEPOSIT_NETWORK_ID` -- để nạp ETH vào beacon chain. Balance của
validator sẽ có thể được rút (withdraw) về execution layer trong một bản nâng
cấp tiếp theo sau Bellatrix.

> 💡 Ghi chú: Nói cách khác, ở Phase 0 việc nạp stake diễn ra một chiều: người
> dùng gửi ETH vào contract trên chain proof-of-work, beacon chain đọc các
> deposit này để tạo/nạp thêm validator. Việc rút tiền về chỉ được bật ở các
> bản nâng cấp sau (thực tế là Capella).

*Lưu ý*: Xem [tại đây](https://chainid.network/) để có danh sách đầy đủ chain-id
và network-id của các chain Ethereum công khai.

### `deposit` function

Deposit contract có một hàm public `deposit` để thực hiện deposit. Hàm nhận các
tham số
`bytes calldata pubkey, bytes calldata withdrawal_credentials, bytes calldata signature, bytes32 deposit_data_root`.
Ba tham số đầu được dùng để điền vào một object
[`DepositData`](./beacon-chain.md#depositdata), còn `deposit_data_root` là root
mong đợi của `DepositData`, dùng để bảo vệ khỏi calldata bị sai định dạng.

> 💡 Ghi chú: Contract tự tính root của `DepositData` từ các tham số (kèm số
> tiền gửi) và so với `deposit_data_root` do người gọi cung cấp; nếu không khớp
> thì giao dịch bị revert, tránh việc mất ETH do dữ liệu bị encode sai.

#### Deposit amount

Lượng ETH gửi vào deposit contract (làm tròn xuống tới Gwei gần nhất) chính là
số tiền deposit, và PHẢI tối thiểu là `MIN_DEPOSIT_AMOUNT` Gwei. Lưu ý rằng ETH
đã bị deposit contract tiêu thụ sẽ không còn dùng được trên execution layer cho
đến một thời điểm nào đó sau bản nâng cấp Bellatrix.

#### Withdrawal credentials

Một trong các trường của `DepositData` là `withdrawal_credentials`, trường này
ràng buộc việc withdrawal của validator (ai/địa chỉ nào được nhận tiền rút).
Byte đầu tiên của trường 32 byte này là withdrawal prefix, quyết định ý nghĩa
của 31 byte còn lại. Các withdrawal prefix hiện được hỗ trợ là
`BLS_WITHDRAWAL_PREFIX` và `ETH1_ADDRESS_WITHDRAWAL_PREFIX`. Đọc thêm trong
[validator guide](./validator.md#withdrawal-credentials).

*Lưu ý*: Deposit contract không kiểm tra trường `withdrawal_credentials`. Nhờ
vậy, có thể bổ sung hỗ trợ cho các withdrawal prefix mới mà không cần sửa
deposit contract.

#### `DepositEvent` log

Mỗi deposit phát ra một log `DepositEvent` để beacon chain tiêu thụ. Deposit
contract chỉ kiểm tra rất ít, đẩy phần lớn logic tiếp nhận validator mới sang
beacon chain. Đặc biệt, proof of possession (bằng chứng sở hữu private key — một
signature BLS12-381) không được deposit contract xác minh.

> 💡 Ghi chú: Vì contract không kiểm tra signature, một deposit có signature sai
> vẫn được ghi nhận on-chain; beacon chain sẽ bỏ qua deposit đó khi xử lý (nếu
> là deposit đầu tiên tạo validator mới), và ETH đã gửi coi như bị mất.

## Solidity code

Mã nguồn deposit contract, viết bằng Solidity, có
[tại đây](https://github.com/ethereum/solidity-deposit-contract/blob/master/deposit_contract.sol).

*Lưu ý*: Để tiết kiệm gas, deposit contract dùng thuật toán tính Merkle root
tăng dần (progressive), chỉ cần O(log(n)) storage. Xem
[tại đây](https://github.com/ethereum/research/blob/master/beacon_chain_impl/progressive_merkle_tree.py)
để có bản hiện thực bằng Python, và
[tại đây](https://github.com/runtimeverification/verified-smart-contracts/blob/master/deposit/formal-incremental-merkle-tree-algorithm.pdf)
để có chứng minh hình thức về tính đúng đắn.
