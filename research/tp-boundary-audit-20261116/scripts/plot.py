import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

csv_path = Path(sys.argv[1])
out_prefix = Path(sys.argv[2])
png_path = out_prefix.with_suffix(".png")
pdf_path = out_prefix.with_suffix(".pdf")
if png_path.exists() or pdf_path.exists():
    raise SystemExit("output exists")

rows = []
with csv_path.open(newline="") as f:
    for r in csv.DictReader(f):
        rows.append(r)

def fnum(s):
    if s is None or s.strip() == "":
        return None
    return float(s)

u = [fnum(r["u"]) for r in rows]
gf = [fnum(r["gas_fraction"]) for r in rows]
old_r = [fnum(r["old_radius"]) for r in rows]
new_r = [fnum(r["new_radius"]) for r in rows]
status = [r["new_status"] for r in rows]

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle("TEST: fixed 8.04 M_E, demonstration TP, legacy water EOS; not a posterior")

# Panel 1
ax = axes[0]
for i in range(len(rows)):
    if u[i] is None or gf[i] is None:
        continue
    if old_r[i] is None:
        ax.scatter(u[i], gf[i], marker="x", color="red", s=40, label="original failure" if i == 0 else "")
    else:
        ax.scatter(u[i], gf[i], facecolors="none", edgecolors="gray", s=40, label="original model" if i == 0 else "")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("u = Fe/(Fe+water)")
ax.set_ylabel("gas mass fraction")
ax.legend(loc="best", fontsize=8)

# Panel 2
ax = axes[1]
for i in range(len(rows)):
    if u[i] is None or gf[i] is None:
        continue
    st = status[i]
    if st == "PASS_CONDITIONAL_NUMERICAL":
        ax.scatter(u[i], gf[i], color="blue", s=40, label="verified new" if i == 0 else "")
    elif st == "FAILED":
        ax.scatter(u[i], gf[i], marker="^", color="purple", s=40, label="still failed" if i == 0 else "")
    elif st == "HISTORICAL_ONLY":
        ax.scatter(u[i], gf[i], facecolors="none", edgecolors="gray", s=40, label="historical-only" if i == 0 else "")
    elif st == "UNRESOLVED_BRACKET":
        ax.scatter(u[i], gf[i], marker="x", color="red", s=40, label="still failed" if i == 0 else "")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_xlabel("u = Fe/(Fe+water)")
ax.set_ylabel("gas mass fraction")
ax.legend(loc="best", fontsize=8)

# Panel 3
ax = axes[2]
for i in range(len(rows)):
    if u[i] is None:
        continue
    if old_r[i] is not None:
        ax.scatter(u[i], old_r[i], facecolors="none", edgecolors="gray", s=40, label="original radius" if i == 0 else "")
    if new_r[i] is not None and status[i] == "PASS_CONDITIONAL_NUMERICAL":
        c = gf[i] if gf[i] is not None else 0
        ax.scatter(u[i], new_r[i], color="blue", s=40, label="new verified radius" if i == 0 else "")
ax.axhspan(2.28, 2.49, color="green", alpha=0.2, label="observed radius")
ax.set_xlabel("u = Fe/(Fe+water)")
ax.set_ylabel("R/R_E")
ax.legend(loc="best", fontsize=8)

from matplotlib.lines import Line2D

# Legend for axes[0]
handles0 = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='none', markeredgecolor='gray', markersize=8, label='original model'),
    Line2D([0], [0], marker='x', color='red', markersize=8, label='original failure')
]
axes[0].legend(handles=handles0, loc='best', fontsize=8)

# Legend for axes[1]
handles1 = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='none', markeredgecolor='gray', markersize=8, label='historical only'),
    Line2D([0], [0], marker='o', color='blue', markersize=8, label='verified rerun'),
    Line2D([0], [0], marker='x', color='red', markersize=8, label='no valid bracket'),
    Line2D([0], [0], marker='^', color='purple', markersize=8, label='later fitting failure')
]
axes[1].legend(handles=handles1, loc='upper left', bbox_to_anchor=(0.01,0.72), fontsize=8)

# Legend for axes[2]
handles2 = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='none', markeredgecolor='gray', markersize=8, label='original radius'),
    Line2D([0], [0], marker='o', color='blue', markersize=8, label='new verified radius'),
    Line2D([0], [0], marker='s', color='green', alpha=0.3, markersize=10, label='observed range')
]
axes[2].legend(handles=handles2, loc='best', fontsize=8)

# Set scales and titles
axes[0].set_xscale('linear')
axes[1].set_xscale('linear')
# yscale log is already set, but ensure it remains
axes[0].set_yscale('log')
axes[1].set_yscale('log')
axes[2].set_yscale('linear')
axes[0].set_title('Before repair')
axes[1].set_title('After initializer repair')
axes[2].set_title('Radius check')
fig.tight_layout()
fig.savefig(png_path, dpi=180)
fig.savefig(pdf_path)
print(png_path)
print(pdf_path)