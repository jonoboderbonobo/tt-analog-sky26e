# Pins, serial configuration port and register map

Source of truth: `digital/src/dig_top.v`. The test `digital/test/test_dig.py` checks every statement here.

## Pins
| Pin | Direction | Function |
|---|---|---|
| `clk` | in | clock of the digital part, 20 MHz at most (hardened with a 50 ns period, slack 27 ns on the slowest corner) |
| `rst_n` | in | reset, low = reset. Clears the control register (all analog switches open, blocks off), the neuron states, thr and leak. The weights have no reset: write all of them after power-up |
| `ui_in[0]` | in | `cs` of the configuration port (1 = shifting) |
| `ui_in[1]` | in | `din` of the configuration port, MSB first, one bit per `clk` |
| `ui_in[2]` | in | input event: a rising edge sends one event on input line `ui_in[3]` |
| `ui_in[3]` | in | input line number (0 or 1), row `NN + line` of the weight matrix |
| `ui_in[4]` | in | time-reference event: a rising edge leaks all neurons (as `aer_tref_all` in snn_gym) |
| `ui_in[7:5]` | in | unused |
| `uo_out[3:0]` | out | neurons that spiked at the last event (sticky until the next event) |
| `uo_out[4]` | out | `busy`: events pending or being processed. Send the next event only when 0 |
| `uo_out[5]` | out | oscillator divided by 2^(2k+1), k = `ctl[11:9]` (0 while the oscillator block is off) |
| `uo_out[6]` | out | `por_n` of the analog side (observed only, does not reset anything) |
| `uo_out[7]` | out | `clk / 128`, heartbeat |
| `uio[7:0]` | - | unused, all inputs (`uio_oe` = 0) |
| `ua[0]`, `ua[1]` | analog | the two analog pins. Each is connected through transmission gates to one of four channel nodes, selected in the control register; all open after reset |

## Frame of the configuration port
24 bits, MSB first: `op[3:0]  a[7:0]  d[11:0]`. Raise `cs`, put one bit on `din` per `clk`, lower `cs`. The frame executes in the clock after `cs` fell,
and only if exactly 24 bits were shifted (anything else is ignored).

| op | name | `a` | `d` |
|---|---|---|---|
| 1 | weight write | `{row[4:2], col[1:0]}`: row 0..5 (rows 0..3 recurrent, 4..5 input lines 0..1), column 0..3 | `d[3:0]` signed weight -8..7 |
| 2 | threshold | - | `d[11:0]`, 0..4095, shared by all neurons |
| 3 | leak | - | `d[6:0]`, 0..127, shared |
| 4 | analog control | - | see below |

Control register (op 4), reset value 0:
| bits | function |
|---|---|
| `d[2:0]` | channel on `ua[0]`: 0 = open, 1..4 = channel 0..3 of group 0 |
| `d[5:3]` | channel on `ua[1]`: 0 = open, 1..4 = channel 0..3 of group 1 |
| `d[6]` | `osc_en`, enables the oscillator block (no oscillator is built yet, the line is brought to the macro edge) |
| `d[7]` | `adc_en`, reserved for the ADC |
| `d[11:9]` | divider tap for `uo_out[5]` |

Values 5..7 in `d[2:0]` or `d[5:3]` select nothing (open).

## Spiking core
4 neurons, 2 input lines, FIFO of 4 entries, 4-bit signed weights, 12-bit signed state; arithmetic bit-exact with the tinyODIN model of `snn_gym`
(`snn/tinyodin.py`, commit 02757e1): saturating add of the weight, spike at `state >= thr` (reset to 0), leak toward 0 on a time-reference event.
Differences from the model: `thr` and `leak` shared by all neurons, no neuron-disable bit, no AER, no learning; events must be sent one at a time
(wait for `busy` = 0), as the model's "quiet" host does.
