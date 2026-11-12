# SPDX-License-Identifier: Apache-2.0
# dig_top through its pins: serial configuration, events, the snn_gym golden vectors, analog control lines, oscillator divider.
import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, Timer

GOLDEN = os.environ.get("GOLDEN", "golden_4x2.txt")
NN, NI = 4, 2
JW = 2


UI = [0]          # shadow of ui_in: a cocotb write is not visible to a read in the same time step


def setui(dut, v):
    UI[0] = v
    dut.ui_in.value = v


def to_signed(v, bits):
    return v - (1 << bits) if v >> (bits - 1) else v


async def tick(dut, n=1):
    await ClockCycles(dut.clk, n)
    await FallingEdge(dut.clk)


async def reset(dut):
    dut.rst_n.value = 0
    setui(dut, 0)
    await tick(dut, 4)
    dut.rst_n.value = 1
    await tick(dut, 4)


async def frame(dut, op, a, d, nbits=24):
    """Serial frame on ui_in[0] (cs) and ui_in[1] (din), one bit per clock, MSB first."""
    word = (op << 20) | (a << 12) | d
    base = UI[0] & ~0b11
    setui(dut, base | 1)
    for k in range(nbits - 1, -1, -1):
        setui(dut, base | 1 | (((word >> k) & 1) << 1))
        await tick(dut)
    setui(dut, base)
    await tick(dut, 6)


async def pulse(dut, bit, hold=4):
    v = UI[0]
    setui(dut, v | (1 << bit))
    await tick(dut, hold)
    setui(dut, v & ~(1 << bit))


async def wait_idle(dut, counts):
    for _ in range(20000):
        if dut.dut.core.spk_pulse.value == 1:
            counts[int(dut.dut.core.spk_idx.value)] += 1
        if dut.dut.core.busy.value == 0 and (int(dut.uo_out.value) >> 4) & 1 == 0:
            return
        await tick(dut)
    raise AssertionError("busy never went low")


@cocotb.test()
async def test_golden_through_pins(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.ena.value, dut.uio_in.value, dut.osc_in.value, dut.por_n_in.value = 1, 0, 0, 1
    checks, counts = 0, [0] * NN
    expect_w, cfg_checked = {}, True
    with open(os.path.join(os.path.dirname(__file__), GOLDEN)) as f:
        lines = [l.split() for l in f if l.strip() and not l.startswith("#")]
    for ln in lines:
        op = ln[0]
        if op in ("E", "R") and not cfg_checked:            # first event after a configuration: is the memory what was sent?
            wm = int(dut.dut.core.wmem.value)
            for (r, c), v in expect_w.items():
                got = to_signed((wm >> ((r * NN + c) * 4)) & 15, 4)
                assert got == v, f"weight[{r}][{c}] is {got}, sent {v}"
            assert int(dut.dut.core.thr.value) == expect_thr and int(dut.dut.core.leak.value) == expect_leak
            cfg_checked = True
        if op == "C":
            await reset(dut)
            expect_w, cfg_checked = {}, False
        elif op == "W":
            expect_w[(int(ln[1]), int(ln[2]))] = int(ln[3])
            await frame(dut, 1, (int(ln[1]) << JW) | int(ln[2]), int(ln[3]) & 15)
        elif op == "T":
            expect_thr, expect_leak = int(ln[1]), int(ln[2])
            await frame(dut, 2, 0, int(ln[1]))
            await frame(dut, 3, 0, int(ln[2]))
        elif op in ("E", "R"):
            counts = [0] * NN
            if op == "E":
                setui(dut, (UI[0] & ~0b1000) | (int(ln[1]) << 3))
                await pulse(dut, 2)
            else:
                await pulse(dut, 4)
            await wait_idle(dut, counts)
        elif op == "X":
            vals = [int(x) for x in ln[1:]]
            flat = int(dut.dut.core.state_flat.value)
            got = [to_signed((flat >> (12 * j)) & 0xFFF, 12) for j in range(NN)]
            assert got == vals[:NN], f"check {checks}: state {got} != model {vals[:NN]}"
            assert counts == vals[NN:], f"check {checks}: spikes {counts} != model {vals[NN:]}"
            checks += 1
    dut._log.info(f"{checks} checks through the pins equal the snn_gym model")


@cocotb.test()
async def test_analog_control(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.ena.value, dut.uio_in.value, dut.osc_in.value, dut.por_n_in.value = 1, 0, 0, 1
    await reset(dut)
    assert int(dut.a_sel0.value) == 0 and int(dut.a_sel1.value) == 0 and dut.osc_en.value == 0, "after reset: ua pins open, blocks off"
    assert int(dut.a_selb0.value) == 15 and int(dut.a_selb1.value) == 15, "after reset every switch is open: complements all 1"
    for ch in range(1, 5):                       # ua0 channel, ua1 another channel
        ch1 = 1 + (ch % 4)
        await frame(dut, 4, 0, ch | (ch1 << 3) | (1 << 6))
        assert int(dut.a_sel0.value) == 1 << (ch - 1), f"a_sel0 {int(dut.a_sel0.value):04b} for channel {ch}"
        assert int(dut.a_sel1.value) == 1 << (ch1 - 1)
        assert dut.osc_en.value == 1
        assert int(dut.a_selb0.value) == 15 ^ (1 << (ch - 1)) and int(dut.a_selb1.value) == 15 ^ (1 << (ch1 - 1)), "complement lines"
    await frame(dut, 4, 0, 5)                    # channel 5 does not exist: nothing selected
    assert int(dut.a_sel0.value) == 0
    await frame(dut, 4, 0, 0b100_001)            # ua0 channel 1 (ch0, one-hot 0001), ua1 channel 4 (ch3, one-hot 1000)
    assert int(dut.a_sel0.value) == 0b0001 and int(dut.a_sel1.value) == 0b1000
    await frame(dut, 4, 0, 0b1_011_010, nbits=23)  # wrong frame length: must be ignored, the register keeps its value
    assert int(dut.a_sel0.value) == 0b0001 and int(dut.a_sel1.value) == 0b1000, "a 23-bit frame must not execute"
    await frame(dut, 4, 0, 0)
    assert int(dut.a_sel0.value) == 0 and int(dut.a_sel1.value) == 0 and dut.adc_en.value == 0


@cocotb.test()
async def test_osc_divider_and_pins(dut):
    cocotb.start_soon(Clock(dut.clk, 10, unit="ns").start())
    dut.ena.value, dut.uio_in.value, dut.osc_in.value, dut.por_n_in.value = 1, 0, 0, 0
    await reset(dut)
    assert (int(dut.uo_out.value) >> 6) & 1 == 0, "uo[6] shows por_n of the analog side"
    dut.por_n_in.value = 1
    await tick(dut, 2)
    assert (int(dut.uo_out.value) >> 6) & 1 == 1
    assert int(dut.uio_oe.value) == 0 and int(dut.uio_out.value) == 0

    async def osc(n_edges, half_ns=50):
        for _ in range(n_edges):
            dut.osc_in.value = 1
            await Timer(half_ns, unit="ns")
            dut.osc_in.value = 0
            await Timer(half_ns, unit="ns")

    await frame(dut, 4, 0, (1 << 6) | (0 << 9))   # osc_en, divider tap 0: osc / 2
    seen = set()
    for _ in range(8):
        await osc(1)
        seen.add((int(dut.uo_out.value) >> 5) & 1)
    assert seen == {0, 1}, "uo[5] must toggle at osc/2"
    toggles = 0
    last = (int(dut.uo_out.value) >> 5) & 1
    await frame(dut, 4, 0, (1 << 6) | (1 << 9))   # tap 1 = counter bit 2: the pin toggles every 4 oscillator edges = 8 times in 32 periods
    for _ in range(32):
        await osc(1)
        v = (int(dut.uo_out.value) >> 5) & 1
        toggles += v != last
        last = v
    assert 7 <= toggles <= 9, f"tap 1 toggled {toggles} times in 32 oscillator periods (expected 8)"
    await frame(dut, 4, 0, 0)                     # osc_en low resets the divider
    assert (int(dut.uo_out.value) >> 5) & 1 == 0
