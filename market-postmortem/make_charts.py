"""Headline charts for the market post-mortem (static PNGs for the repo).

Reads results.json + slice_results.csv. Colors/chrome follow the dataviz
reference palette (light mode): diverging blue/red only where sign is the
story, recessive grid, thin marks, direct labels over legend clutter.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
OUT = HERE / "charts"
OUT.mkdir(exist_ok=True)

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
SECONDARY = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
BLUE = "#2a78d6"
RED = "#e34948"
AQUA = "#1baf7a"

plt.rcParams.update({
    "font.family": "Segoe UI",
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
    "text.color": INK,
    "axes.edgecolor": BASELINE,
    "axes.labelcolor": SECONDARY,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "font.size": 10,
})

res = json.load(open(HERE / "results.json", encoding="utf-8"))
cal = res["calibration"]
slices = pd.read_csv(HERE / "slice_results.csv")

BREAK_EVEN = 52.38


def style_axis(ax):
    ax.grid(axis="y", alpha=0.9)
    ax.grid(axis="x", visible=False)
    ax.tick_params(length=0)


# ------------------------------------------------- 1. calibration curves
fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
fig.subplots_adjust(top=0.80, bottom=0.14, wspace=0.25)

ax = axes[0]
curve = cal["spread_curve"]
x = [r["mean_pred"] for r in curve]
y = [r["mean_actual"] for r in curve]
lim = (-40, 45)
ax.plot(lim, lim, ls="--", lw=1, color=BASELINE, zorder=1)
ax.plot(x, y, "-o", color=BLUE, lw=2, ms=5, zorder=3)
ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel("Closing spread's predicted home margin (pts)")
ax.set_ylabel("Actual home margin (pts)")
s = cal["spread"]
ax.set_title(f"Spreads: nearly perfect\nslope {s['slope']:.2f}, bias "
             f"{s['bias_pts']:+.2f} pts, MAE {s['mae']}", loc="left",
             fontsize=10, color=SECONDARY)
style_axis(ax)

ax = axes[1]
curve = cal["total_curve"]
x = [r["mean_line"] for r in curve]
y = [r["mean_actual"] for r in curve]
lim = (36, 72)
ax.plot(lim, lim, ls="--", lw=1, color=BASELINE, zorder=1)
ax.plot(x, y, "-o", color=AQUA, lw=2, ms=5, zorder=3)
t = cal["total"]
xs = [36, 72]
ax.plot(xs, [t["intercept"] + t["slope"] * v for v in xs], lw=1.2,
        color=MUTED, zorder=2)
ax.annotate("lines too HIGH up here\n(unders cash)", xy=(69.4, 67.2),
            xytext=(56, 68.5), fontsize=9, color=SECONDARY,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.annotate("lines too LOW down here\n(overs cash)", xy=(39.2, 41.6),
            xytext=(41, 38.0), fontsize=9, color=SECONDARY,
            arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel("Closing total (pts)")
ax.set_ylabel("Actual combined points")
ax.set_title(f"Totals: too extreme at the tails\nslope {t['slope']:.2f} "
             f"(a fair market would be 1.00)", loc="left", fontsize=10,
             color=SECONDARY)
style_axis(ax)

fig.suptitle("CFB closing lines 2021–2025: the margin market is sharp, "
             "the totals market overshoots its tails",
             x=0.07, ha="left", fontsize=13, fontweight="bold")
fig.text(0.07, 0.885, "Bucket means, 3,944 FBS-vs-FBS games, dashed = perfect "
         "calibration · CFBD closing lines (DraftKings/Bovada/ESPN Bet)",
         fontsize=9, color=MUTED)
fig.savefig(OUT / "calibration_curves.png", dpi=200)
plt.close(fig)

# ------------------------------------------------- 2. totals tail bias
curve = cal["total_curve"]
labels = ["≤42", "42–46", "46–50", "50–54", "54–58",
          "58–62", "62–66", "66+"]
over = [r["over_pct"] for r in curve]
ns = [r["n"] for r in curve]
fig, ax = plt.subplots(figsize=(9, 4.8))
fig.subplots_adjust(top=0.78, bottom=0.16)
colors = [BLUE if v >= 50 else RED for v in over]
ticklabels = [f"{lbl}\nn={n}" for lbl, n in zip(labels, ns)]
bars = ax.bar(ticklabels, [v - 50 for v in over], bottom=50, width=0.55,
              color=colors, zorder=3)
for xi, v in enumerate(over):
    ax.text(xi, v + 0.5 if v >= 50 else v - 1.4, f"{v:.1f}%",
            ha="center", fontsize=9, color=INK, fontweight="bold")
ax.axhline(50, color=BASELINE, lw=1)
ax.axhline(BREAK_EVEN, color=MUTED, lw=1, ls="--")
ax.axhline(100 - BREAK_EVEN, color=MUTED, lw=1, ls="--")
ax.set_ylim(39.5, 59.5)
ax.set_ylabel("Over win % (pushes excluded)")
ax.set_xlabel("Closing total")
ax.set_title("Blue = overs covered · red = unders covered · dashed = "
             "break-even at -110 (52.4% over / 47.6% under) · 2021–2025",
             loc="left", fontsize=9, color=MUTED)
fig.suptitle("The one bias that survives correction: big totals were set too big",
             x=0.06, ha="left", fontsize=13, fontweight="bold")
fig.text(0.06, 0.885, "Under on totals of 60+ went 413–337–11 (55.1%), above "
         "50% all five seasons — the only spread/total slice to survive "
         "Benjamini–Hochberg FDR", fontsize=9, color=SECONDARY)
style_axis(ax)
fig.savefig(OUT / "totals_tail_bias.png", dpi=200)
plt.close(fig)

# ------------------------------------------------- 3. favorite-longshot (ML ROI)
order = ["Favorites ML -401 and heavier", "Favorites ML -251 to -400",
         "Favorites ML -151 to -250", "Favorites ML -101 to -150",
         "Dogs ML +100 to +150", "Dogs ML +151 to +250",
         "Dogs ML +251 to +400", "Dogs ML +401 and up"]
short = ["≤ -401", "-251/-400", "-151/-250", "-101/-150",
         "+100/+150", "+151/+250", "+251/+400", "+401 and up"]
rows = [slices[slices.strategy == s].iloc[0] for s in order]
roi = [r.roi_at_110 for r in rows]
lo = [r.ci_lo for r in rows]
hi = [r.ci_hi for r in rows]
n = [int(r.n) for r in rows]

fig, ax = plt.subplots(figsize=(9, 5))
fig.subplots_adjust(top=0.80, bottom=0.18)
xpos = range(len(order))
for i, (r, l, h) in enumerate(zip(roi, lo, hi)):
    color = BLUE if r >= 0 else RED
    ax.plot([i, i], [l, h], color=color, lw=2, alpha=0.45, zorder=2)
    ax.plot(i, r, "o", color=color, ms=9, zorder=3)
    ax.text(i, h + 1.2, f"{r:+.1f}%", ha="center", fontsize=9,
            fontweight="bold", color=INK)
    ax.text(i, -46, f"n={n[i]}", ha="center", fontsize=8, color=MUTED)
ax.axhline(0, color=BASELINE, lw=1)
ax.set_xticks(list(xpos), short)
ax.set_ylim(-48, 14)
ax.set_ylabel("ROI per $1 staked (%)")
ax.set_xlabel("Closing moneyline price (favorites → longshots)")
ax.set_title("Dot = mean ROI · whisker = bootstrap 95% CI · flat bet "
             "every game at the closing price, 2021–2025",
             loc="left", fontsize=9, color=MUTED)
fig.suptitle("Favorite–longshot bias: the longer the shot, the worse the price",
             x=0.06, ha="left", fontsize=13, fontweight="bold")
fig.text(0.06, 0.885, "Heavy favorites nearly beat the vig (−3%); +401-or-longer "
         "dogs torched −23% of every dollar — both persistent across seasons "
         "and BH-significant", fontsize=9, color=SECONDARY)
style_axis(ax)
fig.savefig(OUT / "favorite_longshot.png", dpi=200)
plt.close(fig)

# ------------------------------------------------- 4. persistence panel
def season_pcts(strategy: str, invert: bool = False) -> list[float]:
    row = slices[slices.strategy == strategy].iloc[0]
    out = []
    for yr in range(2021, 2026):
        w, l, p = (int(v) for v in re.findall(r"\d+", row[f"s{yr}"])[:3])
        if invert:
            w, l = l, w
        out.append(100 * w / (w + l))
    return out

seasons = list(range(2021, 2026))
panels = [
    ("Under, totals 60+", season_pcts("Under — total 60+"), AQUA),
    ("Favorites ATS, both AP-ranked", season_pcts("Dog ATS — both ranked",
                                                  invert=True), BLUE),
    ("Under, weeks 1–4", season_pcts("Under — weeks 1-4"), MUTED),
]
fig, axes = plt.subplots(1, 3, figsize=(11, 4.2), sharey=True)
fig.subplots_adjust(top=0.76, bottom=0.14, wspace=0.12)
for ax, (title, pcts, color) in zip(axes, panels):
    ax.bar([str(y) for y in seasons], [v - 50 for v in pcts], bottom=50,
           width=0.55, color=color, zorder=3)
    for xi, v in enumerate(pcts):
        ax.text(xi, v + 0.7, f"{v:.1f}", ha="center",
                fontsize=8.5, color=INK)
    ax.axhline(50, color=BASELINE, lw=1)
    ax.axhline(BREAK_EVEN, color=MUTED, lw=1, ls="--")
    ax.set_title(title, loc="left", fontsize=10, color=SECONDARY)
    ax.set_ylim(46, 68)
    style_axis(ax)
axes[0].set_ylabel("Win % vs closing line")
fig.suptitle("Persistence check: does the edge repeat every season?",
             x=0.06, ha="left", fontsize=13, fontweight="bold")
fig.text(0.06, 0.87, "Dashed = break-even at -110 (52.4%). Under 60+ cleared "
         "50% all five seasons (BH-significant). Ranked-matchup favorites "
         "repeated 5/5 but fail FDR correction; early-season unders hover at "
         "break-even — both are watch-list only.",
         fontsize=9, color=SECONDARY)
fig.savefig(OUT / "persistence_by_season.png", dpi=200)
plt.close(fig)

print("wrote 4 charts to", OUT)
