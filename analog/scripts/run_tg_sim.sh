#!/usr/bin/env bash
# Runs the transmission gate simulations over 5 corners x 3 temperatures and writes mux/results/tg_ron.csv, tg_leak.csv and tg_ron.png.
# Usage: source env-tt.sh sky first (PDK_ROOT, ngspice, xschem on the PATH); then   bash analog/scripts/run_tg_sim.sh
set -euo pipefail
cd "$(dirname "$0")/../mux"
mkdir -p results sim/run
export PATH="$HOME/tools/bin:$PATH"
xschem --no_x -n -q --rcfile "$PDK_ROOT/sky130A/libs.tech/xschem/xschemrc" --tcl "set top_subckt 1; set lvs_netlist 1" -o sim/run tg_cell.sch < /dev/null
SCH="$PWD/sim/run/tg_cell.spice"
echo "corner,temp_C,vin_V,ron_ohm" > results/tg_ron.csv
echo "corner,temp_C,leak_A" > results/tg_leak.csv
for corner in tt ss ff sf fs; do
  for temp in -40 27 100; do
    for kind in ron leak; do
      out="$PWD/sim/run/${kind}_${corner}_${temp}.dat"
      sed -e "s#@CORNER@#$corner#g; s#@TEMP@#$temp#g; s#@PDK_ROOT@#$PDK_ROOT#g; s#@SCH@#$SCH#g; s#@OUT@#$out#g" "sim/tg_$kind.spice.in" > "sim/run/tg_${kind}_${corner}_${temp}.spice"
      ngspice -b "sim/run/tg_${kind}_${corner}_${temp}.spice" > "sim/run/tg_${kind}_${corner}_${temp}.log" 2>&1
    done
    awk -v c=$corner -v t=$temp 'NF==2 {printf "%s,%s,%s,%s\n", c, t, $1, $2}' "sim/run/ron_${corner}_${temp}.dat" >> results/tg_ron.csv
    awk -v c=$corner -v t=$temp '/^LEAK/ {printf "%s,%s,%s\n", c, t, $4}' "sim/run/tg_leak_${corner}_${temp}.log" >> results/tg_leak.csv
  done
done
python3 -I "$PWD/../scripts/plot_tg.py" results/tg_ron.csv results/tg_leak.csv results/tg_ron.png
