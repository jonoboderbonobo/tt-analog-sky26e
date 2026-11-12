import csv, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ron, leak, png = sys.argv[1:4]
rows = list(csv.DictReader(open(ron)))
fig, ax = plt.subplots(figsize=(7, 4.5))
for corner in ("tt", "ss", "ff", "sf", "fs"):
    for temp, ls in (("-40", ":"), ("27", "-"), ("100", "--")):
        pts = [(float(r["vin_V"]), float(r["ron_ohm"])) for r in rows if r["corner"] == corner and r["temp_C"] == temp]
        if pts:
            ax.plot(*zip(*pts), ls=ls, lw=1, label=f"{corner} {temp} C")
ax.set_xlabel("Vin at A [V]"); ax.set_ylabel("Ron [ohm]"); ax.set_yscale("log"); ax.grid(True, which="both", alpha=0.3)
ax.set_title("tg_cell on-resistance, 50 mV across the switch"); ax.legend(ncol=3, fontsize=6)
fig.tight_layout(); fig.savefig(png, dpi=130)
worst = max(rows, key=lambda r: float(r["ron_ohm"]))
print(f"worst Ron {float(worst['ron_ohm']):.0f} ohm at corner {worst['corner']}, {worst['temp_C']} C, Vin {worst['vin_V']} V")
for r in csv.DictReader(open(leak)):
    pass
lk = list(csv.DictReader(open(leak)))
w = max(lk, key=lambda r: abs(float(r["leak_A"])))
print(f"worst off-state leakage {abs(float(w['leak_A'])):.3e} A at corner {w['corner']}, {w['temp_C']} C")
