"""Tiny writer for Magic .mag layout files. Coordinates in um, converted to Magic units (1 unit = 5 nm, header 'magscale 1 2').
A Cell has rectangles per layer, labels and instances of other cells (device cells from devices/*.mag or other generated cells)."""
import os, re

U = 200  # units per um


def u(v):
    return int(round(v * U))


class Dev:
    """A device cell file: bounding box and port label positions, in units."""
    def __init__(self, path):
        self.name = os.path.splitext(os.path.basename(path))[0]
        t = open(path).read()
        xs, ys = [], []
        cur = None
        for ln in t.splitlines():
            m = re.match(r"<< (\w+) >>", ln)
            if m:
                cur = m.group(1)
                continue
            m = re.match(r"rect (-?\d+) (-?\d+) (-?\d+) (-?\d+)", ln)
            if m and cur not in ("checkpaint", "labels", "properties"):
                a, b, c, d = map(int, m.groups())
                xs += [a, c]
                ys += [b, d]
        self.bbox = (min(xs), min(ys), max(xs), max(ys))
        self.ports = {}
        for m in re.finditer(r"rlabel (\w+) (-?\d+) (-?\d+) -?\d+ -?\d+ \d+ (\w+)", t):
            self.ports[m.group(4)] = (int(m.group(2)), int(m.group(3)))


class Cell:
    def __init__(self, name):
        self.name, self.rects, self.labels, self.uses, self.ports = name, [], [], [], []
        self.props = []      # (key, value) strings written to the properties section, e.g. FIXED_BBOX (the cell boundary in GDS/LEF)

    def rect(self, layer, x1, y1, x2, y2):
        self.rects.append((layer, u(min(x1, x2)), u(min(y1, y2)), u(max(x1, x2)), u(max(y1, y2))))

    def vline(self, layer, x, y1, y2, w):
        self.rect(layer, x - w / 2, y1, x + w / 2, y2)

    def hline(self, layer, y, x1, x2, w):
        self.rect(layer, x1, y - w / 2, x2, y + w / 2)

    def label(self, text, layer, x, y, port=True, size=0.1, attrs="", rect=None):
        """Label with a small rectangle at (x, y) um on `layer`; port=True also exports it as a pin.
        rect=(x0, y0, x1, y1) um makes the label as large as the pad: Magic writes a pin to the LEF with the label's rectangle, so
        a pin must be labelled over its whole rectangle (the Tiny Tapeout pin check compares the dimensions)."""
        if rect:
            self.labels.append((layer, u(rect[0]), u(rect[1]), u(rect[2]), u(rect[3]), text, (port, attrs)))
            return
        h = u(size) // 2
        self.labels.append((layer, u(x) - h, u(y) - h, u(x) + h, u(y) + h, text, (port, attrs)))

    def place(self, dev, inst, x, y, mirror_x=False):
        """Instance of a Dev with its origin at (x, y) um. mirror_x flips left-right (about the device origin)."""
        tx, ty = u(x), u(y)
        a = -1 if mirror_x else 1
        x1, y1, x2, y2 = dev.bbox
        xs = sorted([a * x1 + tx, a * x2 + tx])
        self.uses.append((dev.name, inst, a, tx, ty, (xs[0], y1 + ty, xs[1], y2 + ty)))
        return Placed(dev, a, tx, ty)

    def save(self, path):
        out = ["magic", "tech sky130A", "magscale 1 2", "timestamp 0"]
        layers = {}
        for l, a, b, c, d in self.rects:
            layers.setdefault(l, []).append((a, b, c, d))
        for l, rs in layers.items():
            out.append(f"<< {l} >>")
            out += [f"rect {a} {b} {c} {d}" for a, b, c, d in rs]
        for name, inst, a, tx, ty, bb in self.uses:
            out += [f"use {name}  {inst}", "timestamp 0", f"transform {a} 0 {tx} 0 1 {ty}", f"box {bb[0]} {bb[1]} {bb[2]} {bb[3]}"]
        if self.labels:
            out.append("<< labels >>")
            for i, (l, a, b, c, d, text, port) in enumerate(self.labels):
                out.append(f"rlabel {l} {a} {b} {c} {d} 0 {text}")
                if port[0]:
                    out.append(f"port {i + 1} nsew {port[1]}".rstrip())
        if self.props:
            out.append("<< properties >>")
            out += [f"string {k} {v}" for k, v in self.props]
        out.append("<< end >>")
        open(path, "w").write("\n".join(out) + "\n")


class Placed:
    def __init__(self, dev, a, tx, ty):
        self.dev, self.a, self.tx, self.ty = dev, a, tx, ty

    def port(self, name):
        """Port position in um (parent coordinates)."""
        px, py = self.dev.ports[name]
        return ((self.a * px + self.tx) / U, (py + self.ty) / U)


# ---- helpers shared by the generators -------------------------------------------------------------------------------
STACK = {  # contact between metal k and k+1: (contact layer, contact size um); pad sizes per metal layer (um), DRC-checked in Magic
    1: ("m2contact", 0.26), 2: ("m3contact", 0.34), 3: ("via3", 0.40)}   # via3 is the sky130A tech name of the metal3-metal4 contact; "m4contact" does not exist there and Magic ignores it silently (no connection, no DRC)
PAD = {"metal1": 0.38, "metal2": 0.50, "metal3": 0.50, "metal4": 0.50}


def stack(c, x, y, lo, hi):
    """Via stack at (x, y) from metal `lo` up to metal `hi` (1..4), with a pad on every metal layer it touches."""
    for k in range(lo, hi + 1):
        s = PAD[f"metal{k}"] / 2
        c.rect(f"metal{k}", x - s, y - s, x + s, y + s)
        if k < hi:
            name, size = STACK[k]
            c.rect(name, x - size / 2, y - size / 2, x + size / 2, y + size / 2)


def cell_bbox(cell, devs):
    """Bounding box (units) of a Cell: its rectangles and its instances (devs: dict name -> Dev or Cell-with-bbox)."""
    xs, ys = [], []
    for _, a, b, c2, d in cell.rects:
        xs += [a, c2]; ys += [b, d]
    for name, inst, a, tx, ty, bb in cell.uses:
        xs += [bb[0], bb[2]]; ys += [bb[1], bb[3]]
    return (min(xs), min(ys), max(xs), max(ys))
