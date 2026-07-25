"""Per-team CFB market trends 2021-25, same rules as the NFL run:
pushes excluded, exact binomial, BH FDR q=0.10 across the whole battery,
persistence = pooled direction repeats in >=80% of seasons played.
Teams need >=30 graded games (FBS-vs-FBS only, so newcomers drop out)."""
from pathlib import Path

import pandas as pd
from scipy.stats import binomtest

df = pd.read_csv(Path(__file__).parent / "market_bets_2021_2025.csv")

league_onescore = (df.margin.abs() <= 8).mean()
teams = sorted(set(df.home) | set(df.away))
rows = []

for t in teams:
    g = df[(df.home == t) | (df.away == t)].copy()
    if len(g) < 30:
        continue
    g["is_home"] = g.home == t

    ou = g[g.over_result.isin(["O", "U"])]
    over_w = (ou.over_result == "O").sum()

    ats = g[g.home_covered.isin(["W", "L"])]
    cov_w = ((ats.is_home & (ats.home_covered == "W"))
             | (~ats.is_home & (ats.home_covered == "L"))).sum()

    osc = (g.margin.abs() <= 8).sum()

    for metric, w, n, p0 in [("over", over_w, len(ou), 0.5),
                             ("ats_cover", cov_w, len(ats), 0.5),
                             ("one_score", osc, len(g), league_onescore)]:
        if n < 30:
            continue
        pv = binomtest(int(w), int(n), p0).pvalue
        agree = 0; seasons = 0; splits = []
        pooled_dir = (w / n) > p0
        for s, gs in g.groupby("season"):
            gs = gs.copy(); gs["is_home"] = gs.home == t
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
        rows.append(dict(team=t, metric=metric, n=int(n), wins=int(w),
                         pct=round(100 * w / n, 1), p=pv,
                         persist=f"{agree}/{seasons}",
                         persistent=seasons >= 4 and agree / seasons >= 0.8,
                         splits=" ".join(splits)))

res = pd.DataFrame(rows).sort_values("p").reset_index(drop=True)
m = len(res)
thresh = res.p <= 0.10 * (res.index + 1) / m
res["bh_sig"] = False
if thresh.any():
    res.loc[:thresh[thresh].index.max(), "bh_sig"] = True

print(f"Teams with 30+ graded games: {res.team.nunique()}  "
      f"tests: {m}  league one-score rate: {100*league_onescore:.1f}%")
print(f"Raw p<0.05: {(res.p<0.05).sum()} (~{m*0.05:.0f} expected by chance). "
      f"BH survivors: {res.bh_sig.sum()}")
print("\n=== Everything at raw p<0.05, plus BH/persistence flags ===")
sig = res[res.p < 0.05]
print(sig[["team", "metric", "n", "wins", "pct", "p", "persist",
           "persistent", "bh_sig"]].to_string(index=False))
print("\n=== Season splits for BH survivors and persistent raw hits ===")
show = res[(res.bh_sig) | ((res.p < 0.05) & res.persistent)]
for _, r in show.iterrows():
    print(f"{r.team} {r.metric}: {r.pct}% ({r.wins}/{r.n}) p={r.p:.4f} "
          f"BH={r.bh_sig}  {r.splits}")
