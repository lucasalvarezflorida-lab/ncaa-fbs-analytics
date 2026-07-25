"""Per-COACH CFB market trends 2021-25. Coach pools games across schools
(Riley = OU 2021 + USC 2022-25). Team-seasons with multiple head coaches
(mid-season changes) are excluded entirely - no interim-game contamination.
Same honesty rules: pushes excluded, exact binomial, BH q=0.10 across the
battery, persistence = pooled direction in >=80% of coach-seasons (>=5 gms).
"""
import sys
from pathlib import Path

import pandas as pd
from scipy.stats import binomtest

FPI = Path(__file__).resolve().parent.parent / "fpi-decomposition"
sys.path.insert(0, str(FPI))
import cfbd_client as cfbd
from name_mapping import normalize_name as norm

df = pd.read_csv(Path(__file__).parent / "market_bets_2021_2025.csv")

# --- build (season, school) -> head coach, excluding split seasons ---
coach_map, split = {}, []
for year in range(2021, 2026):
    per_team = {}
    for c in cfbd.get("/coaches", {"year": year}):
        first = c.get("firstName") or c.get("first_name") or ""
        last = c.get("lastName") or c.get("last_name") or ""
        name = f"{first} {last}".strip()
        for s in c.get("seasons") or []:
            if (s.get("year") == year and (s.get("games") or 0) > 0):
                per_team.setdefault(norm(s.get("school") or ""), []).append(name)
    for school, names in per_team.items():
        if len(set(names)) == 1:
            coach_map[(year, school)] = names[0]
        else:
            split.append((year, school, names))

print(f"coach map: {len(coach_map)} clean team-seasons, "
      f"{len(split)} split team-seasons excluded")

# --- attach a coach to each game side, run the battery ---
df["home_n"], df["away_n"] = df.home.map(norm), df.away.map(norm)
long = []
for side in ("home", "away"):
    part = df.copy()
    part["team_n"] = part[f"{side}_n"]
    part["is_home"] = side == "home"
    part["coach"] = [coach_map.get((y, t))
                     for y, t in zip(part.season, part.team_n)]
    long.append(part)
g_all = pd.concat(long, ignore_index=True).dropna(subset=["coach"])
print(f"game-sides with a clean coach: {len(g_all)} of {2*len(df)}")

league_onescore = (df.margin.abs() <= 8).mean()
rows = []
for coach, g in g_all.groupby("coach"):
    if len(g) < 30:
        continue
    ou = g[g.over_result.isin(["O", "U"])]
    over_w = (ou.over_result == "O").sum()
    ats = g[g.home_covered.isin(["W", "L"])]
    cov_w = ((ats.is_home & (ats.home_covered == "W"))
             | (~ats.is_home & (ats.home_covered == "L"))).sum()
    osc = (g.margin.abs() <= 8).sum()
    schools = ",".join(sorted(g.team_n.unique()))
    for metric, w, n, p0 in [("over", over_w, len(ou), 0.5),
                             ("ats_cover", cov_w, len(ats), 0.5),
                             ("one_score", osc, len(g), league_onescore)]:
        if n < 30:
            continue
        pv = binomtest(int(w), int(n), p0).pvalue
        pooled_dir = (w / n) > p0
        agree = seasons = 0
        splits = []
        for s, gs in g.groupby("season"):
            if metric == "over":
                sub = gs[gs.over_result.isin(["O", "U"])]
                sw, sn = (sub.over_result == "O").sum(), len(sub)
            elif metric == "ats_cover":
                sub = gs[gs.home_covered.isin(["W", "L"])]
                sw = ((sub.is_home & (sub.home_covered == "W"))
                      | (~sub.is_home & (sub.home_covered == "L"))).sum()
                sn = len(sub)
            else:
                sw, sn = (gs.margin.abs() <= 8).sum(), len(gs)
            if sn >= 5:
                seasons += 1
                if ((sw / sn) > p0) == pooled_dir:
                    agree += 1
                splits.append(f"{s}:{sw}/{sn}")
        rows.append(dict(coach=coach, metric=metric, n=int(n), wins=int(w),
                         pct=round(100 * w / n, 1), p=pv,
                         persist=f"{agree}/{seasons}",
                         persistent=seasons >= 4 and agree / seasons >= 0.8,
                         schools=schools, splits=" ".join(splits)))

res = pd.DataFrame(rows).sort_values("p").reset_index(drop=True)
m = len(res)
passed = res.p <= 0.10 * (res.index + 1) / m
res["bh_sig"] = False
if passed.any():
    res.loc[:passed[passed].index.max(), "bh_sig"] = True

print(f"\ncoaches with 30+ graded games: {res.coach.nunique()}  tests: {m}")
print(f"raw p<0.05: {(res.p<0.05).sum()} (~{m*0.05:.0f} expected). "
      f"BH survivors: {res.bh_sig.sum()}")
print("\n=== all raw p<0.05 ===")
print(res[res.p < 0.05][["coach", "metric", "n", "wins", "pct", "p",
                         "persist", "persistent", "bh_sig", "schools"]]
      .to_string(index=False))
print("\n=== named coaches, all metrics ===")
for who in ["Kiffin", "Riley"]:
    sub = res[res.coach.str.contains(who)]
    print(sub[["coach", "metric", "n", "wins", "pct", "p", "persist",
               "schools", "splits"]].to_string(index=False))
