# SPDX-License-Identifier: Apache-2.0
# Runs after test_dig in the co-simulation (Makefile.equiv): the netlist must have agreed with the RTL on every output at every clock edge.
import cocotb


@cocotb.test()
async def test_netlist_equals_rtl(dut):
    assert int(dut.mism.value) == 0, f"{int(dut.mism.value)} clock edges where the netlist outputs differ from the RTL"
    dut._log.info("netlist == RTL on all outputs at every falling clock edge of the golden run")
