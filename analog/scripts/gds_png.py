#!/usr/bin/env python3
"""Renders a GDS (or a cell of it) to a PNG with the KLayout Python API.   python3 gds_png.py file.gds out.png [cell] [width_px]"""
import sys
import klayout.db as db
import klayout.lay as lay

gds, png = sys.argv[1], sys.argv[2]
cell = sys.argv[3] if len(sys.argv) > 3 else None
width = int(sys.argv[4]) if len(sys.argv) > 4 else 1600
v = lay.LayoutView()
v.load_layout(gds, True)
if cell:
    v.select_cell(v.active_cellview().layout().cell_by_name(cell), 0)
v.max_hier()
v.zoom_fit()
bb = v.box()
h = int(width * bb.height() / bb.width()) if bb.width() else width
v.save_image(png, width, h)
print("wrote", png, width, h)
