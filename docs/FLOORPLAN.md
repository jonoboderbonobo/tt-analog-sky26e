# Floorplan and area budget of the 1x2 analog tile (SKY26e, SkyWater 130 nm)

Numbers: cell areas from `sky130_fd_sc_hd.lef` of the PDK (read 2026-11-12), tile size from `tt_analog_1x2.def` of tt-support-tools,
synthesis areas from Yosys + `sky130_fd_sc_hd__tt_025C_1v80.lib` (`digital/area.sh`), placement from LibreLane 3.0.14.

## What fits
| | |
|---|---|
| 1x2 analog tile | 161.0 x 225.76 um = 36 347 um2 |
| NAND2 (sky130_fd_sc_hd__nand2_1) | 3.75 um2, so 9 683 NAND2 equivalents at 100 % fill |
| D flip-flop `dfxtp_1` / with enable `edfxtp_1` | 20.0 / 30.0 um2 |
| usable at 60 % cell area | 5 810 NAND2 equivalents, 1 089 plain flip-flops (flip-flops alone, nothing else) |

A weight bit in an enable flip-flop costs 30 um2 plus its share of the read multiplexer. So storage decides how many neurons fit.

## Spiking core: synthesised area (cells only, before placement)
| neurons / inputs / FIFO | flip-flops | area |
|---|---|---|
| 8 / 4 / 8 | 562 | 27 540 um2 |
| 6 / 2 / 6 | 329 | 16 881 um2 |
| 4 / 2 / 4 | 196 | 9 610 um2 |

The newest network of snn_gym (128 neurons, fan-in 8, `results/chemotaxis_n20/snn_delta1_s0`) needs 17.7 kbit of storage (its `design.md`): about 10 times the tile. Built here: 4 neurons.
The digital macro `dig_top` (core + configuration port + analog control + pin functions): 12 396 um2 synthesised, 266 flip-flops;
after placement and timing repair 17 000 um2 of cells in a 161 x 150 um macro (78 % utilisation). At 130 um height detailed placement failed (DPL-0036).

## Partition
| Region | y [um] | Content |
|---|---|---|
| digital macro | 75.76 .. 225.76 | `dig_top`, 161 x 150 um, pins on the top edge exactly where the template has them |
| mux | 10 .. 36 | 8 transmission gates, 2 groups of 4, B buses to `ua[0]`, `ua[1]` |
| free for analog blocks | x 8 .. 60, y 8 .. 72, about 52 x 64 um = 3 300 um2, plus the strip above the mux | clock, POR, ADC (not built yet); channel nodes `chG_K` are on metal3 at y = 30 |

The left 7.8 um of the macro are kept free (`LEFT_MARGIN_MULT` 17) so that the tile's power stripes (met4, x 1..3 `VDPWR`, 4..6 `VGND`, y 5..220.76)
run through as one rectangle each: the precheck requires every power-pin rectangle to start within 10 um of the bottom and reach within 10 um of the top (`tt/precheck/pin_check.py`).

## Macro power stripes
The macro's met4 stripes are at pitch 130 um, offset 12 um (`FP_PDN_VPITCH`, `FP_PDN_VOFFSET` in `digital/librelane/config.json`): VPWR x 19.0..20.6 and 149.0..150.6, VGND x 22.3..23.9 and 152.3..153.9 um.
The 16 control pins (x 62..132.5 um) are therefore free of stripes; `layout/make_top.py` asserts a 1.3 um clearance. With the default pitch (38.9 um) stripes ran through that span.
The metal3 bars under the macro (y 73..74.2 um) tie the macro's stripes to the tile's `VDPWR`/`VGND` stripes.

## Verification of the tile (2026-11-12, `layout/build_all.sh`)
| Check | Result | Tool / version |
|---|---|---|
| Digital: golden vectors of snn_gym through the pins | 4360 checks pass (RTL); hardened netlist equals RTL on all outputs on every clock edge outside reset | cocotb 2.1.0 + Icarus 12, `digital/test/Makefile.equiv` |
| Macro: LibreLane | 0 design violations, 0 route DRC, 0 antenna, Magic DRC 0, LVS 0, setup slack 27.5 ns, hold slack 0.026 ns | LibreLane 3.0.14 |
| Tile: DRC, flat | 0 | Magic 8.3.698, sky130A `drc(full)` |
| Tile: LVS against the golden netlist (`layout/make_golden.py`: macro netlist + 8 tg_cell instances + connections as designed) | circuits match uniquely, 73 nets, 9 devices (top level) | netgen 1.5.328 |
| Tile: Tiny Tapeout precheck (all 15 checks) | pass | `tt/precheck` of tt-support-tools, KLayout 0.30.8 |

Not verified: the analog switches were simulated as a single cell (Ron, leakage over corners), not inside the tile with parasitics; the extracted tile netlist was not simulated; the analog pin path to the board is not looked at yet.
The golden netlist is derived from the design description, not from a schematic drawn separately, so LVS checks the layout against the intended connections, not the intent itself.
Why the final GDS is composed with KLayout (`layout/compose_gds.py`): Magic regenerates implant and hvtp layers when it writes back the macro's GDS, which gave 378 FEOL violations in the precheck for cells that are clean in the macro.
