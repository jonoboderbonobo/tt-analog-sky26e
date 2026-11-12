#!/usr/bin/env bash
# LVS of one analog cell: layout (Magic extraction, <cell>.spice from drc_extract.tcl) against the xschem schematic.
# Usage (after `source env-tt.sh sky`), from the cell's folder:   bash ../scripts/lvs_cell.sh tg_cell
set -euo pipefail
cell="$1"
export PATH="$HOME/tools/bin:$PATH"
out="lvs_run"; mkdir -p "$out"
xschem --no_x -n -q --rcfile "$PDK_ROOT/sky130A/libs.tech/xschem/xschemrc" --tcl "set top_subckt 1; set lvs_netlist 1" -o "$out" "$cell.sch" < /dev/null
netgen -batch lvs "$cell.spice $cell" "$out/$cell.spice $cell" "$PDK_ROOT/sky130A/libs.tech/netgen/sky130A_setup.tcl" "$out/lvs_$cell.out" | tee "$out/netgen.log" | tail -8
grep -q "Circuits match uniquely" "$out/netgen.log" && echo "LVS $cell: PASS" || { echo "LVS $cell: FAIL (see $out/lvs_$cell.out)"; exit 1; }
