#!/usr/bin/env python3
"""Final GDS of the tile: the cells drawn in Magic (top, transmission gates) with the digital macro's own polygons.
Why: Magic reads a GDS into its own layer model and writes it back with regenerated implant/hvtp/npc layers; the Tiny Tapeout precheck
(KLayout sky130A_mr FEOL) then finds 378 violations in cells that are clean in the hardened macro. So the macro cells are taken from the
LibreLane GDS untouched: read the Magic GDS first, then the macro GDS with OverwriteCell, then drop every cell not below the top.
Usage: python3 compose_gds.py <magic_top.gds> <macro.gds> <out.gds> <top cell>"""
import sys
import klayout.db as pya

magic_gds, macro_gds, out_gds, top_name = sys.argv[1:5]
ly = pya.Layout()
ly.read(magic_gds)
n0 = ly.cells()
opt = pya.LoadLayoutOptions()
opt.cell_conflict_resolution = pya.LoadLayoutOptions.CellConflictResolution.OverwriteCell
macro = pya.Layout(); macro.read(macro_gds)
assert abs(macro.dbu - ly.dbu) < 1e-12, f"dbu differs: macro {macro.dbu}, magic {ly.dbu}"
ly.read(macro_gds, opt)
top = ly.cell(top_name)
used = {top.cell_index()} | set(top.called_cells())
for ci in [c.cell_index() for c in ly.each_cell() if c.cell_index() not in used]:
    ly.delete_cell(ci)
# every cell of the macro file must carry the macro's geometry: same number of shapes on every layer, same instances, same bbox
for a in macro.each_cell():
    b = ly.cell(a.name)
    assert b is not None, f"macro cell {a.name} missing in the result"
    assert a.bbox() == b.bbox(), f"bbox of {a.name} differs"
    assert a.child_instances() == b.child_instances(), f"instances of {a.name} differ"
    for li in macro.layer_infos():
        la, lb = macro.find_layer(li), ly.find_layer(li)
        na = a.shapes(la).size()
        nb = b.shapes(lb).size() if lb is not None else 0
        assert na == nb, f"{a.name} layer {li}: {na} shapes in the macro, {nb} in the result"
ly.write(out_gds)
print(f"{out_gds}: {ly.cells()} cells (Magic file had {n0}), top {top_name}, bbox {top.dbbox()}")
