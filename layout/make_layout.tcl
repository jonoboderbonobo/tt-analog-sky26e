# Draws tt_um_pipetest_analog in Magic and writes ../gds and ../lef.
# Run from this folder:
#   magic -dnull -noconsole -rcfile $PDK_ROOT/sky130A/libs.tech/magic/sky130A.magicrc make_layout.tcl
# Based on magic_init_project.tcl of TinyTapeout/tt-support-tools (Apache-2.0, Uri Shaked, Tiny Tapeout LTD).
# tt_analog_1x2.def is copied from the same repo, tech/sky130A/def/analog/.
set TOP_LEVEL_CELL     tt_um_pipetest_analog
set TEMPLATE_FILE      tt_analog_1x2.def
set POWER_STRIPE_WIDTH 2um

set POWER_STRIPES {
    VDPWR 1um
    VGND  4um
}

def read $TEMPLATE_FILE
cellname rename tt_um_template $TOP_LEVEL_CELL

proc draw_power_stripe {name x} {
    global POWER_STRIPE_WIDTH
    box $x 5um $x 220.76um
    box width $POWER_STRIPE_WIDTH
    paint met4
    label $name FreeSans 0.25u -met4
    port make
    port use [expr {$name eq "VGND" ? "ground" : "power"}]
    port class bidirectional
    port connections n s e w
}
foreach {name x} $POWER_STRIPES {
    puts "Drawing power stripe $name at $x"
    draw_power_stripe $name $x
}

# The test circuit: a met4 strap over the pads of ua[0] (x 152.26 um) and ua[1] (x 132.94 um), both 0.9 x 1.0 um at y 0..1 um.
box 132.49um 0um 152.71um 1um
paint met4

save ${TOP_LEVEL_CELL}.mag
file mkdir ../gds
gds write ../gds/${TOP_LEVEL_CELL}.gds
file mkdir ../lef
lef write ../lef/${TOP_LEVEL_CELL}.lef -hide -pinonly
quit -noprompt
