# Heze -- Inclusion List

*Lưu ý*: Tài liệu này vẫn đang trong quá trình hoàn thiện, dành cho các nhà nghiên cứu và người triển khai client.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Containers](#containers)
  - [New containers](#new-containers)
    - [`InclusionListEntry`](#inclusionlistentry)
    - [`InclusionListStore`](#inclusionliststore)
- [Helpers](#helpers)
  - [New `get_inclusion_list_store`](#new-get_inclusion_list_store)
  - [New `process_inclusion_list`](#new-process_inclusion_list)
  - [New `get_inclusion_list_transactions`](#new-get_inclusion_list_transactions)
  - [New `get_inclusion_list_bits`](#new-get_inclusion_list_bits)
  - [New `is_inclusion_list_bits_inclusive`](#new-is_inclusion_list_bits_inclusive)

<!-- mdformat-toc end -->

## Introduction

Đây là các đặc tả về inclusion list cần thiết để triển khai Heze.

> 💡 Ghi chú: Inclusion list store là một cấu trúc dữ liệu cục bộ (không nằm
> trong beacon state) mà mỗi node duy trì để lưu các inclusion list đã nhận qua
> mạng p2p, được nhóm theo cặp `(slot, dependent_root)`. Store này cũng ghi lại
> các validator đã equivocate (gửi hai inclusion list khác nhau cho cùng một
> khóa) để bỏ qua inclusion list của họ.

## Containers

### New containers

#### `InclusionListEntry`

```python
@dataclass(eq=True, frozen=True)
class InclusionListEntry:
    signed_inclusion_list: SignedInclusionList
    timely: bool
```

#### `InclusionListStore`

```python
@dataclass
class InclusionListStore:
    inclusion_lists: defaultdict[tuple[Slot, Root], dict[ValidatorIndex, InclusionListEntry]]
    equivocators: defaultdict[tuple[Slot, Root], set[ValidatorIndex]]
```

## Helpers

### New `get_inclusion_list_store`

```python
def get_inclusion_list_store() -> InclusionListStore:
    # `cached_or_new_inclusion_list_store` phụ thuộc vào cách triển khai và ngữ cảnh.
    # Hàm này trả về `InclusionListStore` đã được cache; nếu chưa có,
    # nó khởi tạo một instance mới, cache lại và trả về instance đó.
    inclusion_list_store = cached_or_new_inclusion_list_store()

    return inclusion_list_store
```

### New `process_inclusion_list`

```python
def process_inclusion_list(
    store: InclusionListStore, signed_inclusion_list: SignedInclusionList, timely: bool
) -> None:
    inclusion_list = signed_inclusion_list.message
    validator_index = inclusion_list.validator_index
    key = (inclusion_list.slot, inclusion_list.dependent_root)

    if validator_index in store.inclusion_lists[key]:
        # Đánh dấu validator là equivocator nếu nó đã công bố một inclusion list khác
        stored_entry = store.inclusion_lists[key][validator_index]
        stored_inclusion_list = stored_entry.signed_inclusion_list.message
        if stored_inclusion_list != inclusion_list:
            store.equivocators[key].add(validator_index)

        # Bỏ qua inclusion list đã được xử lý trước đó
        return

    # Lưu signed inclusion list cùng với trạng thái đúng hạn (timeliness) của nó
    store.inclusion_lists[key][validator_index] = InclusionListEntry(
        signed_inclusion_list=signed_inclusion_list,
        timely=timely,
    )
```

> 💡 Ghi chú: Chỉ inclusion list đầu tiên của mỗi validator (theo từng
> `(slot, dependent_root)`) được lưu lại. Nếu sau đó nhận được một inclusion list
> khác nội dung từ cùng validator, validator đó bị đánh dấu là equivocator và
> mọi inclusion list của nó cho khóa này sẽ bị bỏ qua ở các hàm bên dưới.

### New `get_inclusion_list_transactions`

*Lưu ý*: `get_inclusion_list_transactions` trả về danh sách các giao dịch không
trùng lặp, lấy từ tất cả các `InclusionList` hợp lệ và không bị equivocation ứng
với `slot` và `dependent_root` đã cho. Khi `only_timely` là `True`, chỉ những
`InclusionList` được nhận đúng hạn (timely) trên mạng p2p mới được xét; ngược
lại, tính đúng hạn không được xét đến.

*Lưu ý*: Các inclusion list MUST được lưu giữ ít nhất
`MIN_SLOTS_FOR_INCLUSION_LISTS_REQUESTS` slot sau slot của chúng; sau khoảng đó,
chúng MAY bị dọn bỏ (pruned).

```python
def get_inclusion_list_transactions(
    store: InclusionListStore, slot: Slot, dependent_root: Root, only_timely: bool = True
) -> Sequence[Transaction]:
    key = (slot, dependent_root)
    inclusion_lists = store.inclusion_lists[key]
    equivocators = store.equivocators[key]

    transactions: list[Transaction] = []
    for validator_index, inclusion_list in inclusion_lists.items():
        # Bỏ qua inclusion list từ các equivocator
        if validator_index in equivocators:
            continue

        # Bỏ qua inclusion list không đúng hạn nếu chỉ yêu cầu những cái đúng hạn
        if only_timely and not inclusion_list.timely:
            continue

        transactions.extend(inclusion_list.signed_inclusion_list.message.transactions)

    # Loại bỏ giao dịch trùng lặp. Không cần giữ nguyên thứ tự.
    return list(set(transactions))
```

### New `get_inclusion_list_bits`

```python
def get_inclusion_list_bits(
    store: InclusionListStore,
    committee: InclusionListCommittee,
    slot: Slot,
    dependent_root: Root,
    only_timely: bool = True,
) -> InclusionListBits:
    key = (slot, dependent_root)
    inclusion_lists = store.inclusion_lists[key]
    equivocators = store.equivocators[key]

    validator_indices = []
    for validator_index, inclusion_list in inclusion_lists.items():
        # Bỏ qua inclusion list từ các equivocator
        if validator_index in equivocators:
            continue

        # Bỏ qua inclusion list không đúng hạn nếu chỉ yêu cầu những cái đúng hạn
        if only_timely and not inclusion_list.timely:
            continue

        validator_indices.append(validator_index)

    return InclusionListBits(data=[index in validator_indices for index in committee])
```

Hàm trả về một `InclusionListBits`, trong đó bit thứ `i` được bật nếu thành viên
thứ `i` của committee có một inclusion list hợp lệ (không equivocation, và đúng
hạn nếu `only_timely` là `True`) trong store.

### New `is_inclusion_list_bits_inclusive`

```python
def is_inclusion_list_bits_inclusive(
    store: InclusionListStore,
    committee: InclusionListCommittee,
    slot: Slot,
    dependent_root: Root,
    inclusion_list_bits: InclusionListBits,
    only_timely: bool = True,
) -> bool:
    local_inclusion_list_bits = get_inclusion_list_bits(
        store, committee, slot, dependent_root, only_timely
    )

    for i in range(INCLUSION_LIST_COMMITTEE_SIZE):
        if local_inclusion_list_bits[i] and not inclusion_list_bits[i]:
            return False
    return True
```

> 💡 Ghi chú: Hàm kiểm tra `inclusion_list_bits` (ví dụ do builder khai báo
> trong bid) có "bao trùm" góc nhìn cục bộ của node hay không: mọi inclusion list
> mà node thấy (bit cục bộ = 1) cũng phải được bật trong `inclusion_list_bits`.
> Nếu node thấy một inclusion list mà bid không tính đến, hàm trả về `False`.
