#!/usr/bin/env python3
"""Writes tg_cell.sch: the transmission gate of the analog mux (the layout in tg_cell.mag must equal it: LVS)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from xsch import Sch

s = Sch()
s.fet("nfet_01v8", "Mn", 0, 0, 3, 0.15, {"D": "B", "G": "SEL", "S": "A", "B": "VSS"})
s.fet("pfet_01v8", "Mp", 200, 0, 5, 0.15, {"D": "B", "G": "SELB", "S": "A", "B": "VDD"})
for k, (kind, net, x, y) in enumerate([("ipin", "SEL", -150, -80), ("ipin", "SELB", -150, -40), ("iopin", "A", -150, 0),
                                       ("iopin", "B", -150, 40), ("iopin", "VSS", -150, 80), ("iopin", "VDD", -150, 120)]):
    s.pin(kind, f"p{k}", x, y, net)
s.text("Transmission gate of the analog mux. SEL = 1, SELB = 0: A and B connected.", -150, -140)
s.save(os.path.join(os.path.dirname(__file__), "tg_cell.sch"))
print("tg_cell.sch written")
