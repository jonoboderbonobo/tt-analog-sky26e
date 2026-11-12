# Usage (from the folder with <cell>.mag):
#   cell=<name> magic -dnull -noconsole -rcfile $PDK_ROOT/sky130A/libs.tech/magic/sky130A.magicrc ../scripts/drc_extract.tcl < /dev/null
# Prints DRC of the flattened cell (a flat check is the one that counts: pads that are too small alone merge with the wires drawn on them),
# extracts, writes <name>.spice (LVS flavour, hierarchical) and <name>.gds
set cell $::env(cell)
load $cell
select top cell
# hierarchical extraction and netlist first
extract all
ext2spice lvs
ext2spice -o $cell.spice
gds write $cell.gds
# flat DRC
flatten ${cell}_flat
load ${cell}_flat
select top cell
drc euclidean on
drc style drc(full)
drc check
drc catchup
puts "DRC_COUNT_FLAT [drc listall count]"
foreach {why boxes} [drc listall why] { puts "DRC_WHY: $why ($boxes)" }
quit -noprompt
