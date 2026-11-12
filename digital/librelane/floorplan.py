"""Shared geometry of the mixed-signal tile (all in um). Used by make_def.py (macro pins) and by ../../layout/make_top.tcl via floorplan.tcl."""
TILE_W, TILE_H = 161.0, 225.76          # tt_analog_1x2
MACRO_H = 150.0                         # height of the digital macro; its top edge is the tile's top edge
# Interface pins on the bottom edge of the macro (x of the pin centre). They sit directly above the analog blocks that use them.
BOTTOM_PINS = {  # x of the pin centre; the mux cells of layout/make_top.py sit directly below the a_sel* / a_selb* pins
    "a_sel0[0]": 100.0,
    "a_selb0[0]": 105.5,
    "a_sel0[1]": 109.0,
    "a_selb0[1]": 114.5,
    "a_sel0[2]": 118.0,
    "a_selb0[2]": 123.5,
    "a_sel0[3]": 127.0,
    "a_selb0[3]": 132.5,
    "a_sel1[0]": 62.0,
    "a_selb1[0]": 67.5,
    "a_sel1[1]": 71.0,
    "a_selb1[1]": 76.5,
    "a_sel1[2]": 80.0,
    "a_selb1[2]": 85.5,
    "a_sel1[3]": 89.0,
    "a_selb1[3]": 94.5,
    "osc_en": 30.0,
    "osc_in": 38.0,
    "por_n_in": 46.0,
    "adc_en": 54.0
}
BOTTOM_DIR = {"osc_in": "INPUT", "por_n_in": "INPUT"}      # everything else is an output of the macro

# mux cell origins (x, um): group 1 drives ua[1], group 0 drives ua[0]; SEL at x, SELB at x + 5.5
MUX_CELLS = {1: [62.0, 71.0, 80.0, 89.0], 0: [100.0, 109.0, 118.0, 127.0]}
MUX_DX = 5.5
