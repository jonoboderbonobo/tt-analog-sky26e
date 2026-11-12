<!---
Datasheet source, built by the Tiny Tapeout docs action.
-->

## How it works

One tile of 1x2 on SKY26e (SkyWater 130 nm) with a digital core and an analog switch matrix. Pins, frame format and register map: `docs/PINS.md`; area and floorplan: `docs/FLOORPLAN.md`.

**Spiking core.** 4 leaky integrate-and-fire neurons, 2 input lines, 4-bit signed weights (6 x 4 matrix, rows 0..3 recurrent, 4..5 inputs), 12-bit signed state, shared threshold and leak. The arithmetic is bit-exact with the tinyODIN model of `snn_gym` (saturating add of the weight, spike at `state >= thr` with reset to 0, leak toward 0 on a time-reference event); the cocotb test replays a reference trace from that model through the pins. Weights, threshold, leak and the analog control register are written over a 24-bit serial port (`ui_in[0]` = cs, `ui_in[1]` = din, MSB first, one bit per clock).

**Analog switch matrix.** Eight transmission gates (2 groups of 4) connect `ua[0]` and `ua[1]` each to one of four channel nodes, selected in the control register; all gates are open after reset. The channel nodes are not connected to any circuit yet (oscillator and SAR ADC are planned, not built). `osc_en`, `adc_en` and the oscillator divider output exist in the register map; with no oscillator, `uo_out[5]` stays 0.

## How to test

1. Apply 1.8 V, clock (20 MHz at most) and release `rst_n`. Write all 24 weights first (they have no reset), then threshold and leak.
2. Send events (`ui_in[2]` rising edge, line number on `ui_in[3]`) one at a time, waiting for `uo_out[4]` (busy) = 0; read the spikes on `uo_out[3:0]`. Compare with the Python model.
3. Analog: write the control register (op 4) with a channel number for `ua[0]` / `ua[1]` and measure the on-resistance and the off leakage of the gates from outside with a source-measure unit on the analog pins; the channel nodes themselves are not on a pin, so only the path to the other side is observable. See the Tiny Tapeout analog specs page for how the analog pins reach the board.

## External hardware

Tiny Tapeout demo board (drives the digital pins), a source-measure unit or multimeter for the analog pins.
