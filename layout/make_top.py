#!/usr/bin/env python3
"""Generates the top cell of the mixed-signal tile, tt_um_snn_mixed.mag (Magic), from
  - the template def (pin frame),
  - the hardened digital macro (digital/macro/: dig_top.mag + dig_top.lef),
  - the transmission-gate cell (analog/mux/tg_cell.mag).
Run from layout/:   python3 make_top.py [--pins]      (--pins only prints the bottom pin x positions the macro must have)
Geometry (um) is described in the README of layout/ and in docs/FLOORPLAN.md."""
import os, re, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "analog", "scripts"))
sys.path.insert(0, os.path.join(HERE, "..", "digital", "librelane"))
from mag import Cell, Dev, stack, u, U
import floorplan as fp

TOP = "tt_um_snn_mixed"
TILE_W, TILE_H, MACRO_H = fp.TILE_W, fp.TILE_H, fp.MACRO_H
MACRO_Y = TILE_H - MACRO_H                       # the macro's lower edge in the tile
LEF = os.path.join(HERE, "..", "digital", "macro", "dig_top.lef")

# --- mux geometry (from analog/mux/make_mux.py) ---
Y0 = 14.0                                        # y of the tg cell origins
DX, CELL_TOP, B_Y = 5.5, 8.0, -3.3               # nfet-pfet distance, top of the cell pins, y of the B wire (relative)
PITCH = 9.0
UA_X = {0: 152.26, 1: 132.94}                    # ua pad x (template def), y = 0.5
CLEAR = 1.3                                      # keep-out around a macro power stripe for the control pins (um)


def macro_stripes():
    t = open(LEF).read()
    out = {}
    for net in ("VPWR", "VGND"):
        m = re.search(rf"PIN {net}\b.*?END {net}", t, re.S)
        out[net] = [(float(a), float(b), float(c), float(d)) for a, b, c, d in re.findall(r"RECT ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+) ;", m.group(0))]
    return out


def cell_positions(stripes):
    """x of the 8 tg cells from digital/librelane/floorplan.py (the macro's bottom pins are placed above them). Checks that no
    control pin (SEL at x, SELB at x + DX) is closer than CLEAR to a macro power stripe."""
    keep = [(r[0] - CLEAR, r[2] + CLEAR) for net in stripes for r in stripes[net]]
    out = []
    for g in (1, 0):
        for k, x in enumerate(fp.MUX_CELLS[g]):
            for p in (x, x + DX):
                assert all(not (lo <= p <= hi) for lo, hi in keep), f"pin at x={p} is inside a stripe keep-out {keep}"
            out.append((g, k, x))
    return out


def pins_from_def():
    src = open(os.path.join(HERE, "tt_analog_1x2.def")).read()
    blocks = re.findall(r"    - (\S+) \+ NET \S+ \+ DIRECTION (\w+) \+ USE SIGNAL\n      \+ PORT\n        \+ LAYER (\w+) \( (-?\d+) (-?\d+) \) \( (-?\d+) (-?\d+) \)\n        \+ PLACED \( (\d+) (\d+) \) N ;", src)
    return [(n, l, int(x0) / 1000, int(y0) / 1000, int(x1) / 1000, int(y1) / 1000, int(px) / 1000, int(py) / 1000, d) for n, d, l, x0, y0, x1, y1, px, py in blocks]


def build():
    stripes = macro_stripes()
    cells = cell_positions(stripes)
    bottom = {}
    for g, k, x in cells:
        bottom[f"a_sel{g}[{k}]"] = round(x, 3)
        bottom[f"a_selb{g}[{k}]"] = round(x + DX, 3)
    if "--pins" in sys.argv:
        print(json.dumps(bottom, indent=1)); return None
    c = Cell(TOP)
    c.uses.append(("dig_top", "xdig", 1, 0, u(MACRO_Y), (0, u(MACRO_Y), u(TILE_W), u(TILE_H))))
    for g, k, x in cells:
        c.uses.append(("tg_cell", f"xtg{g}_{k}", 1, u(x), u(Y0), (u(x - 1.1), u(Y0 - 3.5), u(x + DX + 1.1), u(Y0 + CELL_TOP))))
    # ---- template pins (frame) --------------------------------------------------------------------------------
    attr = {"INPUT": "signal input", "OUTPUT": "signal output", "INOUT": "signal bidirectional"}      # as def read of the template gives them
    for n, l, x0, y0, x1, y1, px, py, d in pins_from_def():
        c.rect(l, px + x0, py + y0, px + x1, py + y1)
        c.label(n, l, px, py, attrs=attr[d], rect=(px + x0, py + y0, px + x1, py + y1))
    # ua pads of the template (def has them as inout met4 0.9 x 1.0)
    # ---- power stripes of the tile --------------------------------------------------------------------------------
    for net, x0, x1, use in (("VDPWR", 1.0, 3.0, "power"), ("VGND", 4.0, 6.0, "ground")):
        c.rect("metal4", x0, 5.0, x1, 220.76)
        c.label(net, "metal4", (x0 + x1) / 2, 10.0, attrs=use + " bidirectional", rect=(x0, 5.0, x1, 220.76))
    c.props.append(("FIXED_BBOX", f"0 0 {u(TILE_W)} {u(TILE_H)}"))      # tile boundary, becomes the prBoundary in the GDS and SIZE in the LEF
    # ---- mux wiring ---------------------------------------------------------------------------------------------
    ytop = Y0 + CELL_TOP
    first = min(x for _, _, x in cells)
    last = max(x for _, _, x in cells)
    for g, k, x in cells:
        # SEL, SELB: metal1 up to y = ytop - 1, stack to metal4, metal4 up to the macro pin
        for name, xx in ((f"a_sel{g}[{k}]", x), (f"a_selb{g}[{k}]", x + DX)):
            stack(c, xx, ytop - 1.0, 1, 4)
            c.vline("metal4", xx, ytop - 1.0, MACRO_Y + 0.9, 0.5)
            c.label(name, "metal4", xx, ytop + 5.0, port=False)
        # A: channel node, metal1 up to ytop - 0.5, stack to metal3, metal3 up to a label pad
        xa = x + DX / 2
        stack(c, xa, ytop - 0.5, 1, 3)
        c.vline("metal3", xa, ytop - 0.5, ytop + 8.0, 0.5)
        c.label(f"ch{g}_{k}", "metal3", xa, ytop + 7.5, port=False)      # inside the metal3 stub (a label must not stick out of the drawing)
        # power: VSS (x - 0.79) to rail y = ytop + 1.3 (metal2), VDD (x + 5.5 + 0.79) to rail y = ytop + 2.9
        yv, yd = ytop + 1.3, ytop + 2.9
        c.vline("metal1", x - 0.79, ytop, yv, 0.29)
        stack(c, x - 0.79, yv, 1, 2)
        c.vline("metal1", x + DX + 0.79, ytop, yd, 0.29)
        stack(c, x + DX + 0.79, yd, 1, 2)
    xr0 = first - 1.0
    c.hline("metal2", ytop + 1.3, 5.0, last + DX + 1.2, 0.5)        # VSS rail to the VGND stripe
    stack(c, 5.0, ytop + 1.3, 2, 4)
    c.hline("metal2", ytop + 2.9, 2.0, last + DX + 1.2, 0.5)        # VDD rail to the VDPWR stripe
    stack(c, 2.0, ytop + 2.9, 2, 4)
    # B buses: metal1 along the cells of a group, down to the ua pad
    yb = Y0 + B_Y
    for g in (0, 1):
        xs = [x for gg, _, x in cells if gg == g]
        x0, x1 = min(xs) - 0.335, max(xs) + DX + 0.335
        if g == 0:
            c.hline("metal1", yb, x0, UA_X[0] + 0.3, 0.23)
            c.vline("metal1", UA_X[0], 2.5, yb, 0.23)
            stack(c, UA_X[0], 2.5, 1, 4)
            c.vline("metal4", UA_X[0], 0.5, 2.5, 0.5)
        else:
            c.hline("metal1", yb, x0, x1 + 1.0, 0.23)
            stack(c, x1 + 1.0, yb, 1, 2)
            c.hline("metal2", yb, x1 + 1.0, UA_X[1], 0.5)
            c.vline("metal2", UA_X[1], 2.5, yb, 0.5)
            stack(c, UA_X[1], 2.5, 2, 4)
            c.vline("metal4", UA_X[1], 0.5, 2.5, 0.5)
    # ---- macro power: bars below the macro, stubs from the macro stripes ------------------------------------------
    yb_gnd, yb_vdd = MACRO_Y - 2.7, MACRO_Y - 1.5
    vp = [(r[0] + r[2]) / 2 for r in stripes["VPWR"]]
    vg = [(r[0] + r[2]) / 2 for r in stripes["VGND"]]
    for x in vp:
        c.vline("metal4", x, yb_vdd, MACRO_Y + 2.6, 1.6)
        stack(c, x, yb_vdd, 3, 4)
    for x in vg:
        c.vline("metal4", x, yb_gnd, MACRO_Y + 2.6, 1.6)
        stack(c, x, yb_gnd, 3, 4)
    tie_lo, tie_hi = bottom_x("osc_in"), bottom_x("por_n_in")
    c.hline("metal3", yb_vdd, 2.0, max(vp + [tie_hi]) + 1.0, 0.5)
    stack(c, 2.0, yb_vdd, 3, 4)
    c.hline("metal3", yb_gnd, 5.0, max(vg + [tie_lo]) + 1.0, 0.5)
    stack(c, 5.0, yb_gnd, 3, 4)
    # ties of the macro inputs that have no analog block yet: osc_in low, por_n_in high
    c.vline("metal4", tie_lo, yb_gnd, MACRO_Y + 0.5, 0.5); stack(c, tie_lo, yb_gnd, 3, 4)
    c.vline("metal4", tie_hi, yb_vdd, MACRO_Y + 0.5, 0.5); stack(c, tie_hi, yb_vdd, 3, 4)
    return c


def bottom_x(name):
    return fp.BOTTOM_PINS[name]


if __name__ == "__main__":
    cell = build()
    if cell:
        cell.save(os.path.join(HERE, TOP + ".mag"))
        print(TOP + ".mag written")
