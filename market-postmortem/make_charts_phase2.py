"""Phase-2 charts: NFL/NBA calibration + cross-sport comparisons.

Same palette/chrome as make_charts.py (dataviz reference palette, light).
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "charts"
OUT.mkdir(exist_ok=True)

SURFACE, INK, SECONDARY, MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"
BLUE, RED, AQUA = "#2a78d6", "#e34948", "#1baf7a"

plt.rcParams.update({
    "font.family": "Segoe UI", "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "text.color": INK, "axes.edgecolor": BASELINE,
    "axes.labelcolor": SECONDARY, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.spines.left": False, "font.size": 10,
})


def style_axis(ax):
    ax.grid(axis="y", alpha=0.9)
    ax.grid(axis="x", visible=False)
    ax.tick_params(length=0)


def calibration_figure(sport: str, res_file: str, out_name: str,
                       subtitle: str, spread_lim, total_lim):
    cal = json.load(open(HERE / res_file, encoding="utf-8"))["calibration"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    fig.subplots_adjust(top=0.80, bottom=0.14, wspace=0.25)

    for ax, key, color, lim, xlabel, ylabel in (
            (axes[0], "spread", BLUE, spread_lim,
             "Closing spread's predicted home margin (pts)",
             "Actual home margin (pts)"),
            (axes[1], "total", AQUA, total_lim,
             "Closing total (pts)", "Actual combined points")):
        c = cal[key]
        x = [r["mean_line"] for r in c["curve"]]
        y = [r["mean_actual"] for r in c["curve"]]
        ax.plot(lim, lim, ls="--", lw=1, color=BASELINE, zorder=1)
        ax.plot(x, y, "-o", color=color, lw=2, ms=5, zorder=3)
        ax.set_xlim(lim); ax.set_ylim(lim)
        ax.set_xlabel(xlabel); ax.set_ylabel(ylabel)
        ax.set_title(f"slope {c['slope']:.2f} (SE {c['slope_se']:.2f}), "
                     f"bias {c['bias_pts']:+.2f} pts, MAE {c['mae']}",
                     loc="left", fontsize=10, color=SECONDARY)
        style_axis(ax)

    fig.suptitle(f"{sport}: closing-line calibration — spreads (left) and "
                 "totals (right)", x=0.07, ha="left", fontsize=13,
                 fontweight="bold")
    fig.text(0.07, 0.885, subtitle, fontsize=9, color=MUTED)
    fig.savefig(OUT / out_name, dpi=200)
    plt.close(fig)


calibration_figure(
    "NFL 2021–2025", "nfl_results.json", "nfl_calibration_curves.png",
    "Bucket means, 1,424 games incl. playoffs, dashed = perfect calibration · "
    "nflverse closing lines", (-18, 18), (36, 56))
calibration_figure(
    "NBA 2011–2021", "nba_results.json", "nba_calibration_curves.png",
    "Bucket means, 13,893 games incl. playoffs, dashed = perfect calibration · "
    "closing lines from local odds archive (933 corrupted spreads excluded)",
    (-16, 16), (180, 235))

# ---------------------------------------------- favorite-longshot, 3 sports
SPORTS = [
    ("CFB 2021–25", "slice_results.csv",
     ["Favorites ML -401 and heavier", "Favorites ML -251 to -400",
      "Favorites ML -151 to -250", "Favorites ML -101 to -150",
      "Dogs ML +100 to +150", "Dogs ML +151 to +250",
      "Dogs ML +251 to +400", "Dogs ML +401 and up"],
     ["≤-401", "-251/\n-400", "-151/\n-250", "-101/\n-150",
      "+100/\n+150", "+151/\n+250", "+251/\n+400", "+401\nand up"]),
    ("NFL 2021–25", "nfl_slice_results.csv",
     ["Favorites ML -251 and heavier", "Favorites ML -151 to -250",
      "Favorites ML -101 to -150", "Dogs ML +100 to +150",
      "Dogs ML +151 to +250", "Dogs ML +251 and up"],
     ["≤-251", "-151/\n-250", "-101/\n-150", "+100/\n+150",
      "+151/\n+250", "+251\nand up"]),
    ("NBA 2011–21", "nba_slice_results.csv",
     ["Favorites ML -401 and heavier", "Favorites ML -251 to -400",
      "Favorites ML -151 to -250", "Favorites ML -101 to -150",
      "Dogs ML +100 to +150", "Dogs ML +151 to +250",
      "Dogs ML +251 to +400", "Dogs ML +401 and up"],
     ["≤-401", "-251/\n-400", "-151/\n-250", "-101/\n-150",
      "+100/\n+150", "+151/\n+250", "+251/\n+400", "+401\nand up"]),
]

fig, axes = plt.subplots(1, 3, figsize=(13, 4.8), sharey=True)
fig.subplots_adjust(top=0.78, bottom=0.20, wspace=0.08)
for ax, (label, csv, order, ticks) in zip(axes, SPORTS):
    df = pd.read_csv(HERE / csv)
    rows = [df[df.strategy == s].iloc[0] for s in order]
    for i, r in enumerate(rows):
        color = BLUE if r.roi_at_110 >= 0 else RED
        ax.plot([i, i], [r.ci_lo, r.ci_hi], color=color, lw=2, alpha=0.45,
                zorder=2)
        ax.plot(i, r.roi_at_110, "o", color=color, ms=7, zorder=3)
    ax.axhline(0, color=BASELINE, lw=1)
    ax.set_xticks(range(len(order)), ticks, fontsize=8)
    ax.set_title(label, loc="left", fontsize=11, color=SECONDARY)
    style_axis(ax)
axes[0].set_ylabel("Flat-bet ROI per $1 staked (%)")
axes[0].set_ylim(-45, 16)
fig.suptitle("Favorite–longshot bias is a college problem: ML ROI by closing "
             "price, three markets", x=0.05, ha="left", fontsize=13,
             fontweight="bold")
fig.text(0.05, 0.87, "Dot = mean ROI · whisker = bootstrap 95% CI. CFB "
         "longshots (+401+) bled −22.9%; the NFL and NBA price every band "
         "within a point or three of the vig.", fontsize=9, color=SECONDARY)
fig.text(0.5, 0.045, "Closing moneyline price (favorites → longshots)",
         ha="center", fontsize=10, color=SECONDARY)
fig.savefig(OUT / "phase2_favorite_longshot.png", dpi=200)
plt.close(fig)

# ---------------------------------------------- totals tail compression
def slope_ci(res_file, key):
    c = json.load(open(HERE / res_file, encoding="utf-8"))["calibration"][key]
    se = c.get("slope_se")
    if se is None:  # CFB run predates slope_se; recover from R², n
        se = c["slope"] * np.sqrt((1 / c["r2"] - 1) / (c["n"] - 2))
    return c["slope"], 1.96 * se


labels = ["CFB\n2021–25", "NFL\n2021–25", "NBA\n2011–21"]
slopes = [slope_ci("results.json", "total"),
          slope_ci("nfl_results.json", "total"),
          slope_ci("nba_results.json", "total")]
# over% in the lowest and highest total buckets per sport
tails = [(57.5, 41.5), (51.9, 45.1), (51.8, 48.4)]

fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
fig.subplots_adjust(top=0.78, bottom=0.16, wspace=0.28)

ax = axes[0]
for i, (s, half) in enumerate(slopes):
    color = RED if s + half < 1 else MUTED
    ax.plot([i, i], [s - half, s + half], color=color, lw=2, alpha=0.5)
    ax.plot(i, s, "o", color=color, ms=9, zorder=3)
    ax.text(i, s + half + 0.015, f"{s:.2f}", ha="center", fontsize=10,
            fontweight="bold", color=INK)
ax.axhline(1.0, color=BASELINE, lw=1.2, ls="--")
ax.text(0.5, 1.013, "fair = 1.00", fontsize=8, color=MUTED, ha="center")
ax.set_xticks(range(3), labels)
ax.set_ylim(0.75, 1.12)
ax.set_ylabel("Slope: actual points on closing total")
ax.set_title("Below 1.00 = lines more extreme than reality", loc="left",
             fontsize=10, color=SECONDARY)
style_axis(ax)

ax = axes[1]
x = np.arange(3)
w = 0.32
b1 = ax.bar(x - w / 2, [t[0] - 50 for t in tails], w, bottom=50, color=BLUE,
            zorder=3, label="lowest-total bucket")
b2 = ax.bar(x + w / 2, [t[1] - 50 for t in tails], w, bottom=50, color=RED,
            zorder=3, label="highest-total bucket")
for xi, (lo, hi) in enumerate(tails):
    ax.text(xi - w / 2, lo + (0.5 if lo >= 50 else -1.3), f"{lo:.1f}",
            ha="center", fontsize=9, color=INK)
    ax.text(xi + w / 2, hi + (0.5 if hi >= 50 else -1.3), f"{hi:.1f}",
            ha="center", fontsize=9, color=INK)
ax.axhline(50, color=BASELINE, lw=1)
ax.set_xticks(x, labels)
ax.set_ylim(38, 61)
ax.set_ylabel("Over win % (pushes excluded)")
ax.set_title("Overs cash on tiny totals, die on huge ones — mostly in CFB",
             loc="left", fontsize=10, color=SECONDARY)
ax.legend(loc="upper right", fontsize=8, frameon=False)
style_axis(ax)

fig.suptitle("The totals tail-compression bias, by sport: big in CFB, faint "
             "in the NFL, almost gone in the NBA", x=0.06, ha="left",
             fontsize=13, fontweight="bold")
fig.text(0.06, 0.875, "Left: regression slope of actual on line (95% CI). "
         "Right: over win% in each sport's lowest vs highest closing-total "
         "bucket (CFB ≤42/66+ · NFL ≤41/51+ · NBA within-season Q1/Q5).",
         fontsize=9, color=SECONDARY)
fig.savefig(OUT / "phase2_totals_tails.png", dpi=200)
plt.close(fig)

print("wrote 4 phase-2 charts to", OUT)
