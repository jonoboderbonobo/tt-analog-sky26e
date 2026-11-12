#!/usr/bin/env python3
"""Writes dig_top.def: the digital pins of tt_analog_1x2.def moved to the top edge of a macro of height MACRO_H, plus the bottom pins.
Usage: python3 make_def.py ../../layout/tt_analog_1x2.def > dig_top.def"""
import re, sys
from floorplan import *

src = open(sys.argv[1]).read()
blocks = re.findall(r"    - (\S+) \+ NET \S+ \+ DIRECTION (\w+) \+ USE SIGNAL\n      \+ PORT\n        \+ LAYER (\w+) \( (-?\d+) (-?\d+) \) \( (-?\d+) (-?\d+) \)\n        \+ PLACED \( (\d+) (\d+) \) N ;", src)
dy = int(round((TILE_H - MACRO_H) * 1000))
pins = []
for name, d, layer, x0, y0, x1, y1, px, py in blocks:
    if name.startswith("ua["):
        continue
    pins.append((name, d, layer, (x0, y0, x1, y1), int(px), int(py) - dy))
for name, x in BOTTOM_PINS.items():
    pins.append((name, BOTTOM_DIR.get(name, "OUTPUT"), "met4", ("-150", "-500", "150", "500"), int(round(x * 1000)), 500))
out = ["VERSION 5.8 ;", 'DIVIDERCHAR "/" ;', 'BUSBITCHARS "[]" ;', "DESIGN dig_top ;", "UNITS DISTANCE MICRONS 1000 ;",
       f"DIEAREA ( 0 0 ) ( {int(TILE_W*1000)} {int(MACRO_H*1000)} ) ;", "COMPONENTS 0 ;", "END COMPONENTS", f"PINS {len(pins)} ;"]
for name, d, layer, (x0, y0, x1, y1), px, py in pins:
    out += [f"    - {name} + NET {name} + DIRECTION {d} + USE SIGNAL", "      + PORT", f"        + LAYER {layer} ( {x0} {y0} ) ( {x1} {y1} )", f"        + PLACED ( {px} {py} ) N ;"]
out += ["END PINS", f"NETS {len(pins)} ;"]
out += [f"    - {p[0]} ( PIN {p[0]} ) + USE SIGNAL ;" for p in pins]
out += ["END NETS", "END DESIGN"]
print("\n".join(out))
