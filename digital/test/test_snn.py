# SPDX-License-Identifier: Apache-2.0
# snn_tiny against the bit-exact tinyODIN model of snn_gym: states and spikes per neuron after every event.
import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge

GOLDEN = os.environ.get("GOLDEN", "golden_8x4.txt")


def to_signed(v, bits):
    return v - (1 << bits) if v >> (bits - 1) else v


async def tick(dut, n=1):
    await ClockCycles(dut.clk, n)
    await FallingEdge(dut.clk)


async def reset(dut):
    dut.rst_n.value = 0
    await tick(dut, 3)
    dut.rst_n.value = 1
    await tick(dut, 2)


async def write_weight(dut, r, c, v):
    dut.w_row.value, dut.w_col.value, dut.w_data.value, dut.w_we.value = r, c, v & 15, 1
    await tick(dut)
    dut.w_we.value = 0


async def run_event(dut, kind, line, NN, counts):
    """One event, then wait for idle; spikes per neuron are counted from spk_pulse."""
    if kind == "E":
        dut.in_line.value, dut.in_valid.value = line, 1
    else:
        dut.tref.value = 1
    await tick(dut)
    dut.in_valid.value = 0
    dut.tref.value = 0
    for _ in range(20000):
        if dut.spk_pulse.value == 1:
            counts[int(dut.spk_idx.value)] += 1
        if dut.busy.value == 0:
            return
        await tick(dut)
    raise AssertionError("busy never went low")


@cocotb.test()
async def test_against_model(dut):
    NN = int(dut.dut.NN.value) if hasattr(dut, "dut") else 8
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.w_we.value = dut.thr_we.value = dut.leak_we.value = dut.in_valid.value = dut.tref.value = 0
    checks = 0
    counts = [0] * NN
    expected_since_event = None
    with open(os.path.join(os.path.dirname(__file__), GOLDEN)) as f:
        lines = [l.split() for l in f if l.strip() and not l.startswith("#")]
    pending = None
    for ln in lines:
        op = ln[0]
        if op == "C":
            await reset(dut)
        elif op == "W":
            await write_weight(dut, int(ln[1]), int(ln[2]), int(ln[3]))
        elif op == "T":
            dut.thr_data.value, dut.thr_we.value = int(ln[1]), 1
            dut.leak_data.value, dut.leak_we.value = int(ln[2]), 1
            await tick(dut)
            dut.thr_we.value = dut.leak_we.value = 0
        elif op in ("E", "R"):
            counts = [0] * NN
            await run_event(dut, op, int(ln[1]) if op == "E" else 0, NN, counts)
        elif op == "X":
            vals = [int(x) for x in ln[1:]]
            exp_state, exp_counts = vals[:NN], vals[NN:]
            flat = int(dut.state_flat.value)
            got_state = [to_signed((flat >> (12 * j)) & 0xFFF, 12) for j in range(NN)]
            assert got_state == exp_state, f"check {checks}: state {got_state} != model {exp_state}"
            assert counts == exp_counts, f"check {checks}: spikes {counts} != model {exp_counts}"
            checks += 1
    dut._log.info(f"{checks} checks of states and spike counts equal the snn_gym model")
