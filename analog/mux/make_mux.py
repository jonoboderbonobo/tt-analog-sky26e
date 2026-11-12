#!/usr/bin/env python3
"""Generates the analog mux layout (Magic .mag): tg_cell.mag (one transmission gate) and tg_mux.mag (2 x 4 array).
Run from analog/mux:  python3 make_mux.py"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from mag import Cell, Dev

DEV = os.path.join(os.path.dirname(__file__), "..", "devices")
N3 = Dev(f"{DEV}/dev_nfet_w3p0_l0p15_t1b0.mag")
P5 = Dev(f"{DEV}/dev_pfet_w5p0_l0p15_t1b0.mag")

W = 0.23          # metal1 line width (the pad width of the device)
DX = 5.5          # distance between the nfet and pfet centres
TOP = 8.0         # y of the top edge of the cell pins


def tg_cell():
    c = Cell("tg_cell")
    n = c.place(N3, "xn", 0, 0)
    p = c.place(P5, "xp", DX, 0, mirror_x=True)       # mirrored: its source pad faces the nfet source pad
    # A: the two source pads joined at y = 0, stub up to the top
    c.hline("metal1", 0.0, 0.105, DX - 0.105, W)
    c.vline("metal1", DX / 2, 0.0, TOP, W)
    # B: the two drain pads continued downwards and joined below the devices
    yb = -3.3
    c.vline("metal1", -0.22, yb, -1.5, W)
    c.vline("metal1", DX + 0.22, yb, -1.5, W)
    c.hline("metal1", yb, -0.335, DX + 0.335, W)
    # gates: pad at (0, 1.62) and (DX, 2.64), line up to the top
    c.vline("metal1", 0.0, 1.55, TOP, 0.29)
    c.vline("metal1", DX, 2.55, TOP, 0.29)
    # bodies: contact on the outer guard ring strip, line up to the top
    for x, net in ((-0.79, "VSS"), (DX + 0.79, "VDD")):
        c.rect("viali", x - 0.085, -0.085, x + 0.085, 0.085)
        c.rect("metal1", x - 0.145, -0.145, x + 0.145, 0.145)
        c.vline("metal1", x, 0.0, TOP, 0.29)
    # pins (labels on the top edge, B on the bottom wire)
    c.label("VSS", "metal1", -0.79, TOP - 0.2)
    c.label("SEL", "metal1", 0.0, TOP - 0.2)
    c.label("A", "metal1", DX / 2, TOP - 0.2)
    c.label("SELB", "metal1", DX, TOP - 0.2)
    c.label("VDD", "metal1", DX + 0.79, TOP - 0.2)
    c.label("B", "metal1", DX / 2, yb)
    return c


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    tg_cell().save(os.path.join(here, "tg_cell.mag"))
    print("tg_cell.mag written")
