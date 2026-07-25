"""Do PRESEASON rankings carry market-facing information? Three sources:

  AP_PRE   - preseason AP top 25 (CFBD rankings, first poll of each season),
             2021-25.
  FPI_PRE  - prior season's FINAL FPI top 30 as a preseason-FPI proxy
             (ESPN's actual preseason FPI isn't archived anywhere CFBD
             reaches; preseason FPI is mostly prior-driven, but this IS a
             proxy and is labeled as such), seasons 2021-25.
  MODEL    - the fpi-decomposition backtest's `predicted` rating, top 25
             (built from preseason-known inputs: prior SP+, returning PPA,
             talent, recruiting). 2025 ONLY - single season, exploratory,
             no persistence possible.

Slices are pre-specified below; the two MODEL-vs-AP disagreement slices are
the actual point (where would a proprietary ranking beat the market?).
Rules as always: bet the ranked team's side, both sides logged when both
qualify, pushes excluded, exact binomial vs 50%, BH q=0.10 across the whole
battery, persistence = direction agrees in >=4 of 5 seasons.
"""
import sys
from pathlib import Path

import pandas as pd
from scipy.stats import binomtest

HERE = Path(__file__).parent
FPI_DIR = HERE.parent / "fpi-decomposition"
sys.path.insert(0, str(FPI_DIR))
import cfbd_client as cfbd
from name_mapping import normalize_name as norm

SEASONS = range(2021, 2026)
df = pd.read_csv(HERE / "market_bets_2021_2025.csv")
df["home_n"], df["away_n"] = df.home.map(norm), df.away.map(norm)

# --- ranking sets per season ---
ap_pre, fpi_pre = {}, {}
for y in SEASONS:
    weeks = cfbd.get("/rankings", {"year": y, "seasonType": "regular"})
    first = min((w for w in weeks if any(p.get("poll") == "AP Top 25"
                                         for p in w.get("polls") or [])),
                key=lambda w: w.get("week", 99))
    poll = next(p for p in first["polls"] if p["poll"] == "AP Top 25")
    ap_pre[y] = {norm(r["school"]) for r in poll["ranks"]}

    prior = cfbd.get("/ratings/fpi", {"year": y - 1})
    rated = sorted((r for r in prior if r.get("fpi") is not None),
                   key=lambda r: -r["fpi"])
    fpi_pre[y] = {norm(r["team"]) for r in rated[:30]}

tbl = pd.read_csv(FPI_DIR / "output" / "team_table_2025.csv")
model25 = set(tbl.sort_values("predicted", ascending=False)
              .head(25).team.map(norm))
print(f"AP sets: {[len(ap_pre[y]) for y in SEASONS]}  "
      f"FPI-proxy sets: {[len(fpi_pre[y]) for y in SEASONS]}  "
      f"model top-25 (2025): {len(model25)}")
print(f"model/AP-2025 overlap: {len(model25 & ap_pre[2025])} teams; "
      f"model-only: {sorted(model25 - ap_pre[2025])}")

# --- slice machinery: one row per qualifying game-side ---
long = []
for side in ("home", "away"):
    part = df.copy()
    part["team_n"] = part[f"{side}_n"]
    part["is_home"] = side == "home"
    long.append(part)
g_all = pd.concat(long, ignore_index=True)
g_all["ats"] = ((g_all.is_home & (g_all.home_covered == "W"))
                | (~g_all.is_home & (g_all.home_covered == "L")))


def in_set(row, sets):
    s = sets.get(row.season) if isinstance(sets, dict) else sets
    return s is not None and row.team_n in s


def run(label, mask, metric):
    g = g_all[mask]
    if metric == "ats":
        sub = g[g.home_covered.isin(["W", "L"])]
        w, n = int(sub.ats.sum()), len(sub)
    else:  # over
        sub = g[g.over_result.isin(["O", "U"])]
        w, n = int((sub.over_result == "O").sum()), len(sub)
    pv = binomtest(w, n, 0.5).pvalue if n else 1.0
    pooled_dir = w / n > 0.5 if n else True
    agree = seasons = 0
    splits = []
    for s, gs in sub.groupby("season"):
        sw = int(gs.ats.sum()) if metric == "ats" \
            else int((gs.over_result == "O").sum())
        sn = len(gs)
        if sn >= 25:
            seasons += 1
            if (sw / sn > 0.5) == pooled_dir:
                agree += 1
        splits.append(f"{s}:{sw}/{sn}")
    return dict(slice=label, metric=metric, n=n, wins=w,
                pct=round(100 * w / n, 1) if n else None, p=pv,
                persist=f"{agree}/{seasons}", splits=" ".join(splits))


ap_m = g_all.apply(lambda r: in_set(r, ap_pre), axis=1)
fpi_m = g_all.apply(lambda r: in_set(r, fpi_pre), axis=1)
y25 = g_all.season == 2025
mod_m = y25 & g_all.team_n.isin(model25)
early = g_all.week <= 4

rows = [
    run("AP-pre-25 team", ap_m, "ats"),
    run("AP-pre-25 team", ap_m, "over"),
    run("AP-pre-25 team, wks 1-4", ap_m & early, "ats"),
    run("FPIproxy-pre-30 team", fpi_m, "ats"),
    run("FPIproxy-pre-30 team", fpi_m, "over"),
    run("FPIproxy-pre-30 team, wks 1-4", fpi_m & early, "ats"),
    run("MODEL-pre-25 team [2025 only]", mod_m, "ats"),
    run("MODEL-pre-25 team [2025 only]", mod_m, "over"),
    run("MODEL in, AP out [2025 only]",
        mod_m & ~g_all.team_n.isin(ap_pre[2025]), "ats"),
    run("AP in, MODEL out [2025 only]",
        y25 & g_all.team_n.isin(ap_pre[2025] - model25), "ats"),
]

res = pd.DataFrame(rows).sort_values("p").reset_index(drop=True)
passed = res.p <= 0.10 * (res.index + 1) / len(res)
res["bh_sig"] = False
if passed.any():
    res.loc[:passed[passed].index.max(), "bh_sig"] = True

print(f"\nbattery: {len(res)} tests, BH survivors: {res.bh_sig.sum()}")
print(res[["slice", "metric", "n", "wins", "pct", "p", "persist",
           "bh_sig"]].to_string(index=False))
print("\nseason splits:")
for _, r in res.iterrows():
    print(f"  {r['slice']} ({r.metric}): {r.splits}")
