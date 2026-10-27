"""
Lab thực hành phase0/beacon-chain.md — chạy:
    .venv/bin/python playground/phase0_lab.py

Mỗi bài = 1 section trong beacon-chain.md. Đọc section đó -> đoán output -> chạy -> so sánh.
Cột "TODO" là chỗ bạn tự sửa/thử.
"""
from eth_consensus_specs.phase0 import minimal as spec
from eth_consensus_specs.utils import bls
from eth_consensus_specs.test.helpers.genesis import create_genesis_state
from eth_consensus_specs.test.helpers.block import build_empty_block_for_next_slot
from eth_consensus_specs.test.helpers.state import state_transition_and_sign_block, next_epoch
from eth_consensus_specs.test.helpers.attestations import next_epoch_with_attestations

bls.bls_active = False  # tắt BLS cho nhanh (chữ ký không được verify)

def title(s): print(f"\n=== {s} ===")

# ---------------------------------------------------------------------------
title("Bài 1: Constants / Preset  (section: Constants, Preset, Configuration)")
# Preset 'minimal' khác 'mainnet' — đoán trước rồi chạy
print("SLOTS_PER_EPOCH        =", spec.SLOTS_PER_EPOCH)
print("MAX_EFFECTIVE_BALANCE  =", spec.MAX_EFFECTIVE_BALANCE, "Gwei")
print("SHUFFLE_ROUND_COUNT    =", spec.SHUFFLE_ROUND_COUNT)
# TODO: đổi import thành `mainnet` và so sánh

# ---------------------------------------------------------------------------
title("Bài 2: Genesis  (section: Genesis -> initialize_beacon_state_from_eth1)")
N = 64
state = create_genesis_state(spec, [spec.MAX_EFFECTIVE_BALANCE] * N, spec.MAX_EFFECTIVE_BALANCE)
print("slot =", state.slot, "| số validator =", len(state.validators))
v = state.validators[0]
print("validator[0]: activation_epoch =", v.activation_epoch, "exit_epoch =", v.exit_epoch)
print("is_valid_genesis_state? ->", spec.is_valid_genesis_state(state))
# TODO: vì sao False? Đọc is_valid_genesis_state (MIN_GENESIS_ACTIVE_VALIDATOR_COUNT, MIN_GENESIS_TIME)

# ---------------------------------------------------------------------------
title("Bài 3: Helper - slot/epoch  (section: Misc helpers)")
for s in [0, 7, 8, 17]:
    print(f"slot {s:>2} -> epoch {spec.compute_epoch_at_slot(s)}")
print("compute_activation_exit_epoch(0) =", spec.compute_activation_exit_epoch(0))
# TODO: giải thích vì sao = 1 + MAX_SEED_LOOKAHEAD

# ---------------------------------------------------------------------------
title("Bài 4: Shuffling & committee  (compute_shuffled_index, get_beacon_committee)")
seed = spec.get_seed(state, spec.Epoch(0), spec.DOMAIN_BEACON_ATTESTER)  # phải dùng kiểu SSZ, int thường sẽ lỗi
print("shuffle 10 index đầu:", [int(spec.compute_shuffled_index(spec.Uint64(i), spec.Uint64(N), seed)) for i in range(10)])
print("committees/slot =", spec.get_committee_count_per_slot(state, spec.Epoch(0)))
for slot in range(3):
    print(f"slot {slot} committee 0:", list(map(int, spec.get_beacon_committee(state, spec.Slot(slot), spec.CommitteeIndex(0)))))
print("proposer slot hiện tại:", spec.get_beacon_proposer_index(state))
# TODO: kiểm chứng: mỗi validator xuất hiện đúng 1 lần trong cả epoch (viết vòng lặp)

# ---------------------------------------------------------------------------
title("Bài 5: State transition với 1 block  (section: Beacon chain state transition function)")
block = build_empty_block_for_next_slot(spec, state)
print("block.slot =", block.slot, "proposer =", block.proposer_index)
state_transition_and_sign_block(spec, state, block)
print("sau block: state.slot =", state.slot,
      "| latest_block_header.slot =", state.latest_block_header.slot)
# TODO: sửa block.proposer_index = sai -> chạy lại -> assert nào trong process_block_header nổ?

# ---------------------------------------------------------------------------
title("Bài 6: Epoch processing không ai attest  (process_justification_and_finalization, rewards)")
state2 = create_genesis_state(spec, [spec.MAX_EFFECTIVE_BALANCE] * N, spec.MAX_EFFECTIVE_BALANCE)
b0 = int(state2.balances[0])
for _ in range(5):
    next_epoch(spec, state2)
print("epoch =", spec.get_current_epoch(state2),
      "| finalized =", state2.finalized_checkpoint.epoch,
      "| balance[0] thay đổi:", int(state2.balances[0]) - b0, "Gwei")
# TODO: vì sao balance giảm? (get_attestation_deltas, inactivity leak sau MIN_EPOCHS_TO_INACTIVITY_PENALTY)

# ---------------------------------------------------------------------------
title("Bài 7: Mọi người attest đầy đủ -> justify & finalize (Casper FFG)")
state3 = create_genesis_state(spec, [spec.MAX_EFFECTIVE_BALANCE] * N, spec.MAX_EFFECTIVE_BALANCE)
b0 = int(state3.balances[0])
next_epoch(spec, state3)
for _ in range(4):
    _, _, state3 = next_epoch_with_attestations(spec, state3, True, True)
    print(f"epoch {spec.get_current_epoch(state3)}: justified={state3.current_justified_checkpoint.epoch}"
          f" finalized={state3.finalized_checkpoint.epoch}"
          f" bits={[int(b) for b in state3.justification_bits]}")
print("balance[0] thay đổi:", int(state3.balances[0]) - b0, "Gwei")
# TODO: đổi fill_cur_epoch=False -> finality đi theo rule nào trong 4 rule (2nd/3rd/4th...)?
