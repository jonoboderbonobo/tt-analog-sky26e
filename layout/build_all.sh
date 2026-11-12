#!/usr/bin/env bash
# Whole tile: top cell (make_top.py), Magic build + extraction, final GDS (compose_gds.py), flat Magic DRC, LVS against the golden netlist.
# Usage:  source ../../env-tt.sh sky ; bash build_all.sh      (from layout/)
set -euo pipefail
cd "$(dirname "$0")"
TOP=tt_um_snn_mixed
MAGIC="magic -dnull -noconsole -rcfile $PDK_ROOT/sky130A/libs.tech/magic/sky130A.magicrc"
python3 make_top.py
python3 make_golden.py
rm -rf build && mkdir build && cd build
$MAGIC ../build_top.tcl < /dev/null 2>&1 | grep -E 'TOP bbox|BUILD_DONE|rror' || true
mkdir -p ../../gds
python3 ../compose_gds.py $TOP.magic.gds ../../digital/macro/dig_top.gds ../../gds/$TOP.gds $TOP
$MAGIC ../drc_top.tcl < /dev/null 2>&1 | grep -E 'DRC_' | tee drc_top.log
netgen -batch lvs "$TOP.spice $TOP" "../${TOP}_golden.spice $TOP" "$PDK_ROOT/sky130A/libs.tech/netgen/sky130A_setup.tcl" lvs_top.out > lvs_top.log 2>&1
grep -q "Circuits match uniquely" lvs_top.log && echo "LVS $TOP: PASS" || { echo "LVS $TOP: FAIL (see layout/build/lvs_top.out)"; exit 1; }
