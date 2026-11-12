# Flat Magic DRC of the tile top. Run from layout/build/ after build_top.tcl:
#   magic -dnull -noconsole -rcfile $PDK_ROOT/sky130A/libs.tech/magic/sky130A.magicrc ../drc_top.tcl < /dev/null
addpath ..
addpath ../../analog/mux
gds read ../../digital/macro/dig_top.gds
load tt_um_snn_mixed
select top cell
flatten tt_um_snn_mixed_flat
load tt_um_snn_mixed_flat
select top cell
drc euclidean on
drc style drc(full)
drc check
drc catchup
puts "DRC_COUNT_FLAT [drc listall count]"
foreach {why boxes} [drc listall why] { puts "DRC_WHY: $why ($boxes)" }
quit -noprompt
