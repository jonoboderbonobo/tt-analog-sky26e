v {xschem version=3.4.7 file_version=1.2
}
G {}
K {}
V {}
S {}
E {}
C {sky130_fd_pr/nfet_01v8.sym} 0 0 0 0 {name=Mn L=0.15 W=3 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=nfet_01v8 spiceprefix=X}
C {devices/lab_pin.sym} 20.0 -30.0 0 0 {name=l1 sig_type=std_logic lab=B}
C {devices/lab_pin.sym} -20.0 0.0 2 0 {name=l2 sig_type=std_logic lab=SEL}
C {devices/lab_pin.sym} 20.0 30.0 0 0 {name=l3 sig_type=std_logic lab=A}
C {devices/lab_pin.sym} 20.0 0.0 0 0 {name=l4 sig_type=std_logic lab=VSS}
C {sky130_fd_pr/pfet_01v8.sym} 200 0 0 0 {name=Mp L=0.15 W=5 nf=1 mult=1 ad="expr('int((@nf + 1)/2) * @W / @nf * 0.29')" pd="expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')" as="expr('int((@nf + 2)/2) * @W / @nf * 0.29')" ps="expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')" nrd="expr('0.29 / @W ')" nrs="expr('0.29 / @W ')" sa=0 sb=0 sd=0 model=pfet_01v8 spiceprefix=X}
C {devices/lab_pin.sym} 220.0 30.0 0 0 {name=l5 sig_type=std_logic lab=B}
C {devices/lab_pin.sym} 180.0 0.0 2 0 {name=l6 sig_type=std_logic lab=SELB}
C {devices/lab_pin.sym} 220.0 -30.0 0 0 {name=l7 sig_type=std_logic lab=A}
C {devices/lab_pin.sym} 220.0 0.0 0 0 {name=l8 sig_type=std_logic lab=VDD}
C {devices/ipin.sym} -150 -80 0 0 {name=p9 lab=SEL}
C {devices/ipin.sym} -150 -40 0 0 {name=p10 lab=SELB}
C {devices/iopin.sym} -150 0 0 0 {name=p11 lab=A}
C {devices/iopin.sym} -150 40 0 0 {name=p12 lab=B}
C {devices/iopin.sym} -150 80 0 0 {name=p13 lab=VSS}
C {devices/iopin.sym} -150 120 0 0 {name=p14 lab=VDD}
T {Transmission gate of the analog mux. SEL = 1, SELB = 0: A and B connected.} -150 -140 0 0 0.4 0.4 {}
