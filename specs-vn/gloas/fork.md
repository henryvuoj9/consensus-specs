# Gloas -- Fork Logic

*Ghi chú*: Tài liệu này đang trong quá trình soạn thảo, dành cho các nhà nghiên
cứu và đội ngũ triển khai client.

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Configs](#configs)
- [Helpers](#helpers)
  - [New `initialize_ptc_window`](#new-initialize_ptc_window)
  - [New `onboard_builders_from_pending_deposits`](#new-onboard_builders_from_pending_deposits)
- [Fork to Gloas](#fork-to-gloas)
  - [Fork trigger](#fork-trigger)
  - [Upgrading the state](#upgrading-the-state)
  - [Upgrading attestations and attester slashings](#upgrading-attestations-and-attester-slashings)

<!-- mdformat-toc end -->

## Introduction

Tài liệu này mô tả quy trình nâng cấp (upgrade) lên Gloas: các hằng số cấu hình
của fork, các hàm hỗ trợ, và cách chuyển đổi beacon state cũng như attestation
từ Fulu sang Gloas.

## Configs

Cảnh báo: cấu hình này chưa phải là bản chính thức cuối cùng.

| Name                 | Value                                 |
| -------------------- | ------------------------------------- |
| `GLOAS_FORK_VERSION` | `Version("0x07000000")`               |
| `GLOAS_FORK_EPOCH`   | `Epoch(18446744073709551615)` **TBD** |

## Helpers

### New `initialize_ptc_window`

> 💡 Ghi chú: Hàm này dựng sẵn cửa sổ cache các PTC (payload timeliness
> committee). Phần epoch trước được điền giá trị rỗng (toàn `ValidatorIndex(0)`),
> sau đó là PTC đã tính cho từng slot của epoch hiện tại và `MIN_SEED_LOOKAHEAD`
> epoch tiếp theo.

```python
def initialize_ptc_window(
    state: BeaconState,
) -> PayloadTimelinessCommitteeWindow:
    """
    Return the cached PTC window starting from the current epoch.
    Used to initialize the ``ptc_window`` field in the beacon state at genesis and after forks.
    """
    empty_previous_epoch = [
        PayloadTimelinessCommittee(data=[ValidatorIndex(0) for _ in range(PTC_SIZE)])
        for _ in range(SLOTS_PER_EPOCH)
    ]

    ptcs = []
    current_epoch = get_current_epoch(state)
    for e in range(1 + MIN_SEED_LOOKAHEAD):
        epoch = current_epoch + e
        start_slot = compute_start_slot_at_epoch(epoch)
        ptcs += [compute_ptc(state, start_slot + index) for index in range(SLOTS_PER_EPOCH)]

    return PayloadTimelinessCommitteeWindow(data=empty_previous_epoch + ptcs)
```

### New `onboard_builders_from_pending_deposits`

*Ghi chú*: Việc onboarding (đưa vào hệ thống) một lần duy nhất này là con đường
duy nhất qua deposit contract của validator để tạo ra builder. Kể từ fork trở đi,
builder chỉ được tạo và nạp thêm số dư thông qua `BuilderDepositRequest`.

*Ghi chú*: Trong các slot ngay trước fork, các implementation SHOULD kiểm tra
trước signature của các pending deposit và cache kết quả. Hàng đợi pending
deposit có thể rất lớn, và việc xác minh nhiều signature ngay tại thời điểm fork
có thể chậm.

> 💡 Ghi chú: Tóm tắt logic của hàm bên dưới, với mỗi pending deposit:
>
> - Nếu pubkey thuộc một validator đã có: giữ nguyên trong hàng đợi.
> - Nếu pubkey chưa phải builder: chỉ tạo builder mới khi withdrawal credential
>   là loại builder, không có pending deposit hợp lệ nào cho validator mới cùng
>   pubkey, và signature hợp lệ (signature sai thì deposit bị bỏ). Các trường hợp
>   còn lại giữ trong hàng đợi.
> - Nếu pubkey đã là builder: cộng `amount` vào balance của builder đó.

```python
def onboard_builders_from_pending_deposits(state: BeaconState) -> None:
    """
    Applies any pending deposit for builders, effectively
    onboarding builders at the fork.
    """
    validator_pubkeys = [validator.pubkey for validator in state.validators]

    pending_deposits = PendingDeposits()
    for deposit in state.pending_deposits:
        # Deposit cho validator đã tồn tại vẫn ở lại trong hàng đợi pending
        if deposit.pubkey in validator_pubkeys:
            pending_deposits.append(deposit)
            continue

        # Lưu ý việc áp dụng deposit bên dưới có thể thay đổi state và
        # có thể thêm builder vào registry. Vì vậy danh sách
        # pubkey của builder phải được tính lại ở mỗi vòng lặp.
        builder_pubkeys = [builder.pubkey for builder in state.builders]

        # Deposit không dành cho builder vẫn ở lại hàng đợi pending. Nếu đã có một
        # pending deposit hợp lệ cho validator mới với pubkey này, giữ deposit
        # này trong hàng đợi để sau này áp dụng cho validator đó.
        if deposit.pubkey not in builder_pubkeys:
            if not is_builder_withdrawal_credential(deposit.withdrawal_credentials):
                pending_deposits.append(deposit)
                continue
            if is_pending_validator(pending_deposits, deposit.pubkey):
                pending_deposits.append(deposit)
                continue
            if not is_valid_deposit_signature(
                deposit.pubkey,
                deposit.withdrawal_credentials,
                deposit.amount,
                deposit.signature,
            ):
                continue

            add_builder_to_registry(
                state,
                deposit.pubkey,
                PAYLOAD_BUILDER_VERSION,
                ExecutionAddress(deposit.withdrawal_credentials[12:]),
                deposit.amount,
                deposit.slot,
            )
        else:
            builder_index = BuilderIndex(builder_pubkeys.index(deposit.pubkey))
            state.builders[builder_index].balance += deposit.amount

    state.pending_deposits = pending_deposits
```

## Fork to Gloas

### Fork trigger

Fork được kích hoạt tại epoch `GLOAS_FORK_EPOCH`.

### Upgrading the state

Nếu `state.slot % SLOTS_PER_EPOCH == 0` và
`compute_epoch_at_slot(state.slot) == GLOAS_FORK_EPOCH`, một thay đổi state bất
thường (irregular state change, tức không đi qua state transition thông thường)
được thực hiện để nâng cấp lên Gloas.

> 💡 Ghi chú: Các điểm chính của `upgrade_to_gloas`: các list trong state được
> bọc lại bằng kiểu mới (EIP-7688); `latest_execution_payload_header` bị bỏ, thay
> bằng `latest_block_hash`; thêm các trường mới cho builder, PTC và execution
> payload bid (EIP-7732). `latest_execution_payload_bid` được khởi tạo từ header
> payload cuối cùng của Fulu, coi như một block tự build (`BUILDER_INDEX_SELF_BUILD`).
> Sau đó PTC window được khởi tạo và các builder được onboard từ pending deposit.

```python
def upgrade_to_gloas(pre: fulu.BeaconState) -> BeaconState:
    epoch = fulu.get_current_epoch(pre)

    post = BeaconState(
        genesis_time=pre.genesis_time,
        genesis_validators_root=pre.genesis_validators_root,
        slot=pre.slot,
        fork=Fork(
            previous_version=pre.fork.current_version,
            # [Modified in Gloas]
            current_version=GLOAS_FORK_VERSION,
            epoch=epoch,
        ),
        latest_block_header=pre.latest_block_header,
        block_roots=pre.block_roots,
        state_roots=pre.state_roots,
        historical_roots=pre.historical_roots,
        eth1_data=pre.eth1_data,
        eth1_data_votes=pre.eth1_data_votes,
        eth1_deposit_index=pre.eth1_deposit_index,
        # [Modified in Gloas:EIP7688]
        validators=Validators(data=pre.validators),
        # [Modified in Gloas:EIP7688]
        balances=Balances(data=pre.balances),
        randao_mixes=pre.randao_mixes,
        slashings=pre.slashings,
        # [Modified in Gloas:EIP7688]
        previous_epoch_participation=EpochParticipation(data=pre.previous_epoch_participation),
        # [Modified in Gloas:EIP7688]
        current_epoch_participation=EpochParticipation(data=pre.current_epoch_participation),
        justification_bits=pre.justification_bits,
        previous_justified_checkpoint=pre.previous_justified_checkpoint,
        current_justified_checkpoint=pre.current_justified_checkpoint,
        finalized_checkpoint=pre.finalized_checkpoint,
        # [Modified in Gloas:EIP7688]
        inactivity_scores=InactivityScores(data=pre.inactivity_scores),
        current_sync_committee=pre.current_sync_committee,
        next_sync_committee=pre.next_sync_committee,
        # [Modified in Gloas:EIP7732]
        # Removed `latest_execution_payload_header`
        # [New in Gloas:EIP7732]
        latest_block_hash=pre.latest_execution_payload_header.block_hash,
        next_withdrawal_index=pre.next_withdrawal_index,
        next_withdrawal_validator_index=pre.next_withdrawal_validator_index,
        historical_summaries=pre.historical_summaries,
        deposit_requests_start_index=pre.deposit_requests_start_index,
        deposit_balance_to_consume=pre.deposit_balance_to_consume,
        exit_balance_to_consume=pre.exit_balance_to_consume,
        earliest_exit_epoch=pre.earliest_exit_epoch,
        consolidation_balance_to_consume=pre.consolidation_balance_to_consume,
        earliest_consolidation_epoch=pre.earliest_consolidation_epoch,
        # [Modified in Gloas:EIP7688]
        pending_deposits=PendingDeposits(data=pre.pending_deposits),
        # [Modified in Gloas:EIP7688]
        pending_partial_withdrawals=PendingPartialWithdrawals(data=pre.pending_partial_withdrawals),
        # [Modified in Gloas:EIP7688]
        pending_consolidations=PendingConsolidations(data=pre.pending_consolidations),
        proposer_lookahead=pre.proposer_lookahead,
        # [New in Gloas:EIP7732]
        builders=Builders(),
        # [New in Gloas:EIP7732]
        next_withdrawal_builder_index=BuilderIndex(0),
        # [New in Gloas:EIP7732]
        execution_payload_availability=ExecutionPayloadAvailability(
            data=[0b1 for _ in range(SLOTS_PER_HISTORICAL_ROOT)]
        ),
        # [New in Gloas:EIP7732]
        builder_pending_payments=BuilderPendingPayments(),
        # [New in Gloas:EIP7732]
        builder_pending_withdrawals=BuilderPendingWithdrawals(),
        # [New in Gloas:EIP7732]
        latest_execution_payload_bid=ExecutionPayloadBid(
            parent_block_hash=pre.latest_execution_payload_header.parent_hash,
            parent_block_root=pre.latest_block_header.parent_root,
            block_hash=pre.latest_execution_payload_header.block_hash,
            prev_randao=pre.latest_execution_payload_header.prev_randao,
            fee_recipient=ExecutionAddress(),
            gas_limit=pre.latest_execution_payload_header.gas_limit,
            builder_index=BUILDER_INDEX_SELF_BUILD,
            slot=pre.latest_block_header.slot,
            value=Gwei(0),
            execution_payment=Gwei(0),
            blob_kzg_commitments=BlobKZGCommitments(),
            execution_requests_root=hash_tree_root(ExecutionRequests.empty()),
        ),
        # [New in Gloas:EIP7732]
        payload_expected_withdrawals=Withdrawals(),
        # [New in Gloas:EIP7732]
        ptc_window=PayloadTimelinessCommitteeWindow(),
    )

    # [New in Gloas:EIP7732]
    post.ptc_window = initialize_ptc_window(post)

    # [New in Gloas:EIP7732]
    onboard_builders_from_pending_deposits(post)

    return post
```

### Upgrading attestations and attester slashings

Một `BeaconBlockBody` của Gloas vẫn có thể chứa các attestation và attester
slashing từ trước fork. Để đóng gói chúng vào block, dữ liệu trước Gloas cần
được nâng cấp cục bộ (locally) sang định dạng Gloas trước khi tạo block.

```python
def upgrade_attestation_to_gloas(pre: fulu.Attestation) -> Attestation:
    return Attestation(
        aggregation_bits=AggregationBits(data=pre.aggregation_bits),
        data=pre.data,
        signature=pre.signature,
        committee_bits=pre.committee_bits,
    )
```

```python
def upgrade_indexed_attestation_to_gloas(pre: fulu.IndexedAttestation) -> IndexedAttestation:
    return IndexedAttestation(
        attesting_indices=AttestingIndices(data=pre.attesting_indices),
        data=pre.data,
        signature=pre.signature,
    )
```

```python
def upgrade_attester_slashing_to_gloas(pre: fulu.AttesterSlashing) -> AttesterSlashing:
    return AttesterSlashing(
        attestation_1=upgrade_indexed_attestation_to_gloas(pre.attestation_1),
        attestation_2=upgrade_indexed_attestation_to_gloas(pre.attestation_2),
    )
```
