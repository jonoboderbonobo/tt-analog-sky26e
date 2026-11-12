"""Small writer for xschem .sch files with the SKY130 device symbols. Pin positions are read from the symbols,
every pin gets a lab_pin with the net name, so nets connect by name (no wires to draw)."""
import os, re

PDK_ROOT = os.environ["PDK_ROOT"]
SYMDIR = os.path.join(PDK_ROOT, "sky130A/libs.tech/xschem/sky130_fd_pr")


def sym_pins(path):
    pins = {}
    for m in re.finditer(r"^B 5 ([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+) \{name=(\w+)", open(path).read(), re.M):
        x1, y1, x2, y2 = map(float, m.groups()[:4])
        pins[m.group(5)] = ((x1 + x2) / 2, (y1 + y2) / 2)
    return pins


class Sch:
    def __init__(self):
        self.items = []
        self.n = 0

    def _id(self, p):
        self.n += 1
        return f"{p}{self.n}"

    def fet(self, kind, name, x, y, w, l, nets, nf=1):
        """kind 'nfet_01v8' or 'pfet_01v8'; nets: dict D,G,S,B -> net names."""
        pins = sym_pins(f"{SYMDIR}/{kind}.sym")
        self.items.append(f"C {{sky130_fd_pr/{kind}.sym}} {x} {y} 0 0 {{name={name} L={l} W={w} nf={nf} mult=1 ad=\"expr('int((@nf + 1)/2) * @W / @nf * 0.29')\" "
                          f"pd=\"expr('2*int((@nf + 1)/2) * (@W / @nf + 0.29)')\" as=\"expr('int((@nf + 2)/2) * @W / @nf * 0.29')\" ps=\"expr('2*int((@nf + 2)/2) * (@W / @nf + 0.29)')\" "
                          f"nrd=\"expr('0.29 / @W ')\" nrs=\"expr('0.29 / @W ')\" sa=0 sb=0 sd=0 model={kind} spiceprefix=X}}")
        for pin, net in nets.items():
            px, py = pins[pin]
            rot = 0 if px >= 0 else 2          # label points away from the device
            self.items.append(f"C {{devices/lab_pin.sym}} {x + px} {y + py} {rot} 0 {{name={self._id('l')} sig_type=std_logic lab={net}}}")

    def pin(self, kind, name, x, y, net):
        """kind ipin, opin or iopin."""
        self.items.append(f"C {{devices/{kind}.sym}} {x} {y} 0 0 {{name={self._id('p')} lab={net}}}")

    def text(self, s, x, y):
        self.items.append(f"T {{{s}}} {x} {y} 0 0 0.4 0.4 {{}}")

    def save(self, path):
        hdr = ["v {xschem version=3.4.7 file_version=1.2", "}", "G {}", "K {}", "V {}", "S {}", "E {}"]
        open(path, "w").write("\n".join(hdr + self.items) + "\n")
