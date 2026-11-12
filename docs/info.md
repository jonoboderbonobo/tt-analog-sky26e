<!---
Datasheet source, built by the Tiny Tapeout docs action.
-->

## How it works

Pipeline test for SKY26e (SkyWater 130 nm, analog template, 1x2 tiles). `ua[0]` and `ua[1]` are joined by a short met4 strap.
There is no active circuit. The 1.8 V supply (`VDPWR`) and ground (`VGND`) run as met4 stripes, as the template requires.

## How to test

Measure the resistance between `ua[0]` and `ua[1]` with a multimeter or source-measure unit: it should read a few ohms (the strap
plus two pad paths), not open. With the digital pins unused, nothing else is needed.

## External hardware

Multimeter or source-measure unit.
