# Generates the device cells used by the analog layouts (Magic gencell of the PDK) and saves them as devices/*.mag.
# Run:  cd analog/devices && magic -dnull -noconsole -rcfile $PDK_ROOT/sky130A/libs.tech/magic/sky130A.magicrc ../scripts/make_devices.tcl < /dev/null
# name  type  w  l  topc  botc
set devs {
  dev_n3  nfet 3.0 0.15 1 0
  dev_p5  pfet 5.0 0.15 1 0
}
cellname create devlib
load devlib
foreach {name type w l topc botc} $devs {
    box 0 0 0 0
    set tmp ${name}_tmp
    magic::gencell sky130::sky130_fd_pr__${type}_01v8 $tmp w $w l $l nf 1 diffcov 100 polycov 100 guard 1 compatible 1 topc $topc botc $botc
    select cell $tmp
    set def [cellname list instances $tmp]
    puts "$name -> instance of [instance list]"
}
writeall force
quit -noprompt
