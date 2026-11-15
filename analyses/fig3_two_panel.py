"""Figure 3: (A) isolated loop contributions to mean RI; (B) Monte Carlo attribution."""
import csv, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from metrics import HERE
R = os.path.join(HERE, "..", "results")
plt.rcParams.update({"font.family": "serif", "font.serif": ["DejaVu Serif"], "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 300})
loops = list(csv.DictReader(open(os.path.join(R, "loop_impact", "loop_impact.csv"))))
src = list(csv.DictReader(open(os.path.join(R, "section4", "src_attribution.csv"))))
order = ["R1", "R2", "B1", "B2", "B3", "B4"]
lab = {r["loop"]: r["label"] for r in loops}
fig, (a, b) = plt.subplots(1, 2, figsize=(7.4, 3.5), width_ratios=[1.05, 1])
y = np.arange(len(order))[::-1]
for k, (pol, col, off) in enumerate([("No-SC", "#b2182b", 0.18), ("Full-SC", "#1a7a4c", -0.18)]):
    v = [float(next(r for r in loops if r["loop"] == c and r["policy"] == pol)["contribution_mean_RI"]) for c in order]
    a.barh(y + off, v, height=0.34, color=col, label=pol)
a.axvline(0, color="black", lw=0.8)
a.set_yticks(y); a.set_yticklabels([lab[c] for c in order], fontsize=8)
a.set_xlabel("Contribution to mean RI\n(with loop minus loop cut)")
a.set_title("A. Isolated loop contributions", loc="left", fontsize=9, fontweight="bold")
a.legend(frameon=False, fontsize=7.5, loc="lower right")
names = [r["label"] for r in src][::-1]; vals = [float(r["src"]) for r in src][::-1]
cols = ["#b2182b" if "SC_" in n else "#2166ac" for n in names]
b.barh(names, vals, color=cols)
for i, v in enumerate(vals):
    b.text(v + (0.02 if v >= 0 else -0.02), i, ("0.00" if abs(v) < 0.005 else f"{v:+.2f}"), va="center", ha="left" if v >= 0 else "right", fontsize=7.5)
b.axvline(0, color="black", lw=0.8); b.set_xlim(min(vals) - 0.3, max(vals) + 0.3)
b.tick_params(axis="y", labelsize=8)
b.set_xlabel("Standardized regression coefficient on ΔRI\n(300 draws; R² = 0.996)")
b.set_title("B. Monte Carlo attribution", loc="left", fontsize=9, fontweight="bold")
fig.tight_layout(); fig.savefig(os.path.join(R, "section4", "fig3.png")); print("ok")
