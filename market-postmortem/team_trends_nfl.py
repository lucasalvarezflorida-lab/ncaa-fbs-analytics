"""Per-team NFL market trends 2021-25: over rate, ATS cover rate,
one-possession rate. Same honesty rules as the post-mortem: pushes
excluded, exact binomial tests, BH FDR q=0.10 across the full 96-test
battery, persistence = direction agrees in >=4 of 5 seasons."""
from pathlib import Path

import pandas as pd
from scipy.stats import binomtest

df = pd.read_csv(Path(__file__).parent / "nfl_bets_2021_2025.csv")

rows = []
teams = sorted(set(df.home) | set(df.away))
league_onescore = (df.margin.abs() <= 8).mean()

for t in teams:
    m_home, m_away = df.home == t, df.away == t
    g = df[m_home | m_away].copy()
    g["is_home"] = g.home == t

    # over result (team-agnostic): over_res W = game went over
    ou = g[g.over_res.isin(["W", "L"])]
    over_w = (ou.over_res == "W").sum()

    # ATS from the team's perspective
    ats = g[g.home_covered.isin(["W", "L"])]
    cov_w = ((ats.is_home & (ats.home_covered == "W"))
             | (~ats.is_home & (ats.home_covered == "L"))).sum()

    # one-possession games
    osc = (g.margin.abs() <= 8).sum()

    for metric, w, n, p0 in [("over", over_w, len(ou), 0.5),
                             ("ats_cover", cov_w, len(ats), 0.5),
                             ("one_score", osc, len(g), league_onescore)]:
        pv = binomtest(int(w), int(n), p0).pvalue if n else 1.0
        # per-season direction for persistence
        agree = 0; seasons = 0; splits = []
        for s, gs in g.groupby("season"):
            gs = gs.copy(); gs["is_home"] = gs.home == t
            if metric == "over":
                sub = gs[gs.over_res.isin(["W", "L"])]
                sw, sn = (sub.over_res == "W").sum(), len(sub)
            elif metric == "ats_cover":
                sub = gs[gs.home_covered.isin(["W", "L"])]
                sw = ((sub.is_home & (sub.home_covered == "W"))
                      | (~sub.is_home & (sub.home_covered == "L"))).sum()
                sn = len(sub)
            else:
                sw, sn = (gs.margin.abs() <= 8).sum(), len(gs)
            if sn:
                seasons += 1
                pooled_dir = (w / n) > p0
                if ((sw / sn) > p0) == pooled_dir:
                    agree += 1
                splits.append(f"{s}:{sw}/{sn}")
        rows.append(dict(team=t, metric=metric, n=int(n), wins=int(w),
                         pct=round(100 * w / n, 1), p=pv,
                         persist=f"{agree}/{seasons}",
                         persistent=agree >= 4, splits=" ".join(splits)))

res = pd.DataFrame(rows)
# BH FDR q=0.10 over all 96 tests
res = res.sort_values("p").reset_index(drop=True)
k = res.index + 1
res["bh_sig"] = res.p <= 0.10 * k / len(res)
# BH: largest k where p <= q*k/m, all ranks below pass
if res.bh_sig.any():
    cutoff = res[res.bh_sig].index.max()
    res.loc[:cutoff, "bh_sig"] = True

print(f"League one-possession rate: {100*league_onescore:.1f}%")
print(f"\nBattery: {len(res)} tests. Raw p<0.05: {(res.p<0.05).sum()} "
      f"(~{len(res)*0.05:.0f} expected by chance). BH survivors: {res.bh_sig.sum()}")
print("\n=== Top 15 by p-value ===")
print(res.head(15)[["team", "metric", "n", "wins", "pct", "p",
                    "persist", "bh_sig"]].to_string(index=False))
print("\n=== Miami rows ===")
mia = res[res.team == "MIA"]
print(mia[["metric", "n", "wins", "pct", "p", "persist", "splits"]]
      .to_string(index=False))
