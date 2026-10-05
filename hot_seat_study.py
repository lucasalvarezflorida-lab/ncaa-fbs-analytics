"""Hot-seat study (INTERNAL, Lucas 10/4/2026): who is gone by next season, from what is known after Week 5?

OUTCOME  the coach of record in season Y is not the head coach of that school in Y+1 AND is not an FBS head coach
         anywhere else in Y+1 (fired / forced out / retired / stepped down; a coach who left for another job is
         dropped from the sample, not counted either way).
FEATURES (all known after Week 5 of season Y; CFBD /coaches + /games)
  preseason view : tenure year, last season's win pct and its change from the year before, the program's win pct
                   over the ten years before (the "bar"), last season minus that bar, AP preseason ranked or not
  in-season view : win pct and average margin through Week 5, win pct minus last season's, losses so far,
                   whether the team was ranked in the preseason and already has 2+ losses
MODELS   logistic regression, standardized, L2; fit 2014-2021, test 2022-2025 (walk-forward by season block).
         pre = preseason features only, now = in-season only, both = all. Scored by AUC, log loss and how many of
         the test seasons' departures sit in each season's top 10 / top 15.
Then the fitted "both" model scores every 2026 coach -> internal/hot_seat_shadow_week6.json (SHADOW, not on air).

    python hot_seat_study.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / "fpi-decomposition"))
from refresh_all import load_env_key  # noqa: E402
load_env_key()
import cfbd_client as cfbd  # noqa: E402

THROUGH = 5                      # weeks of the season known (we are after Week 5)
FIT, TEST, NOW = range(2014, 2022), range(2022, 2026), 2026
PRE = ["tenure_log", "first_two", "last_wp", "last_delta", "bar", "last_vs_bar", "pre_ranked"]
INS = ["wp_now", "margin_now", "wp_vs_last", "losses_now", "ranked_2loss"]


def coach_table():
    """{(school, year): dict(coach, wins, losses, pre_rank)} - the coach with the most games that season
    (ties and 0-game current seasons: the last one listed)."""
    out, by = {}, defaultdict(list)
    for c in cfbd.get("/coaches", {"minYear": 2000, "maxYear": NOW}, True):
        name = f"{c['firstName']} {c['lastName']}"
        for s in c["seasons"]:
            by[(s["school"], s["year"])].append((s.get("games") or 0, name, s))
    for k, v in by.items():
        g, name, s = max(v, key=lambda x: x[0])
        out[k] = dict(coach=name, wins=s.get("wins") or 0, losses=s.get("losses") or 0, pre_rank=s.get("preseasonRank"),
                      n_coaches=len(v))
    return out


def early_records(year, through=THROUGH):
    """{school: (wins, losses, avg margin)} through week `through`, FBS teams."""
    rec = defaultdict(lambda: [0, 0, 0.0])
    for g in cfbd.get("/games", {"year": year, "seasonType": "regular"}, year == NOW):
        if (g.get("week") or 99) > through or g.get("homePoints") is None or g.get("awayPoints") is None:
            continue
        m = g["homePoints"] - g["awayPoints"]
        for t, mm in ((g["homeTeam"], m), (g["awayTeam"], -m)):
            r = rec[t]; r[0] += mm > 0; r[1] += mm < 0; r[2] += max(min(mm, 35), -35)
    return {t: (w, l, s / max(w + l, 1)) for t, (w, l, s) in rec.items()}


def build(through=THROUGH):
    T = coach_table()
    rows = []
    for year in list(FIT) + list(TEST) + [NOW]:
        early = early_records(year, through)
        hc_next = {v["coach"] for (s, y), v in T.items() if y == year + 1}
        for (school, y), v in T.items():
            if y != year or school not in early:
                continue
            prev = [T.get((school, year - k)) for k in range(1, 11)]
            if not prev[0] or sum(p is not None for p in prev) < 5:
                continue                                    # new to FBS
            tenure = 1
            while T.get((school, year - tenure), {}).get("coach") == v["coach"]:
                tenure += 1
            wp = lambda p: p["wins"] / max(p["wins"] + p["losses"], 1)
            last = wp(prev[0]); last2 = wp(prev[1]) if prev[1] else last
            bar = float(np.mean([wp(p) for p in prev if p]))
            w, l, mar = early[school]
            pr = v["pre_rank"] is not None
            f = dict(tenure_log=np.log(tenure), first_two=float(tenure <= 2), last_wp=last, last_delta=last - last2, bar=bar,
                     last_vs_bar=last - bar, pre_ranked=float(pr),
                     wp_now=w / max(w + l, 1), margin_now=mar, wp_vs_last=w / max(w + l, 1) - last, losses_now=float(l),
                     ranked_2loss=float(pr and l >= 2))
            row = dict(year=year, school=school, coach=v["coach"], tenure=tenure, rec=f"{w}-{l}", **f)
            if year < NOW:
                nxt = T.get((school, year + 1))
                if not nxt:
                    continue
                gone = nxt["coach"] != v["coach"]
                if gone and v["coach"] in hc_next:
                    continue                                # took another FBS head job - not a hot-seat outcome
                row["gone"] = int(gone)
            rows.append(row)
    return rows


def fit_logit(X, y, l2=1.0, iters=400):
    Xb = np.column_stack([np.ones(len(X)), X]); w = np.zeros(Xb.shape[1])
    for _ in range(iters):                                 # Newton
        p = 1 / (1 + np.exp(-Xb @ w)); W = p * (1 - p)
        R = np.eye(len(w)) * l2; R[0, 0] = 0
        H = Xb.T @ (Xb * W[:, None]) + R
        w -= np.linalg.solve(H, Xb.T @ (p - y) + R @ w)
    return w


def auc(p, y):
    order = np.argsort(p); r = np.empty(len(p)); r[order] = np.arange(1, len(p) + 1)
    n1 = y.sum(); n0 = len(y) - n1
    return float((r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def p_gone_2026(through):
    """ON AIR (Lucas 10/4/2026): {school: dict(coach, tenure, rec, p_gone)} for every 2026 coach, from the 'both' model
    refit on every completed season (2014-2025) with the same number of weeks known."""
    rows = build(through)
    tr = [r for r in rows if r["year"] < NOW]; now = [r for r in rows if r["year"] == NOW]
    cols = PRE + INS
    X = np.array([[r[c] for c in cols] for r in tr]); mu, sd = X.mean(0), X.std(0) + 1e-9
    w = fit_logit((X - mu) / sd, np.array([r["gone"] for r in tr], float))
    Xn = (np.array([[r[c] for c in cols] for r in now]) - mu) / sd
    p = 1 / (1 + np.exp(-(np.column_stack([np.ones(len(now)), Xn]) @ w)))
    return {r["school"]: dict(coach=r["coach"], tenure=r["tenure"], rec=r["rec"], p_gone=float(pp)) for r, pp in zip(now, p)}


def main():
    rows = build()
    tr = [r for r in rows if r["year"] in FIT]; te = [r for r in rows if r["year"] in TEST]; now = [r for r in rows if r["year"] == NOW]
    out = []; P = out.append
    P("# Hot-seat study (INTERNAL, Sun Oct 4 2026)\n")
    P(f"Coach-seasons: fit 2014-21 {len(tr)} ({sum(r['gone'] for r in tr)} gone, {100 * np.mean([r['gone'] for r in tr]):.1f}%), "
      f"test 2022-25 {len(te)} ({sum(r['gone'] for r in te)} gone). Outcome = not the school's coach next season and not an FBS head coach elsewhere. "
      f"Everything is measured after Week {THROUGH}.\n")
    models = {}
    P("| model | test AUC | test log loss | departures in the season's top 10 | in the top 15 |\n|---|--:|--:|--:|--:|")
    base = np.mean([r["gone"] for r in tr])
    yte = np.array([r["gone"] for r in te], float)
    P(f"| base rate only | 0.500 | {-np.mean(yte * np.log(base) + (1 - yte) * np.log(1 - base)):.4f} | - | - |")
    for name, cols in (("preseason view", PRE), ("in-season view (5 weeks)", INS), ("both", PRE + INS)):
        Xtr = np.array([[r[c] for c in cols] for r in tr]); mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
        w = fit_logit((Xtr - mu) / sd, np.array([r["gone"] for r in tr], float))
        score = lambda rs: 1 / (1 + np.exp(-(np.column_stack([np.ones(len(rs)), (np.array([[r[c] for c in cols] for r in rs]) - mu) / sd]) @ w)))
        p = score(te)
        hit10 = hit15 = tot = 0
        for yr in TEST:
            idx = [i for i, r in enumerate(te) if r["year"] == yr]
            order = sorted(idx, key=lambda i: -p[i])
            tot += int(yte[idx].sum()); hit10 += int(yte[order[:10]].sum()); hit15 += int(yte[order[:15]].sum())
        ll = -np.mean(yte * np.log(p) + (1 - yte) * np.log(1 - p))
        P(f"| {name} | {auc(p, yte):.3f} | {ll:.4f} | {hit10} of {tot} | {hit15} of {tot} |")
        models[name] = (cols, mu, sd, w, score)
    cols, mu, sd, w, score = models["both"]
    P("\n## What carries the 'both' model (standardized coefficients; + = more likely gone)\n\n| feature | coef |\n|---|--:|")
    for c, b in sorted(zip(cols, w[1:]), key=lambda x: -abs(x[1])):
        P(f"| {c} | {b:+.2f} |")
    # weight question: how much of the spread in the combined score comes from each view
    Xte = (np.array([[r[c] for c in cols] for r in te]) - mu) / sd
    zp = Xte[:, :len(PRE)] @ w[1:1 + len(PRE)]; zi = Xte[:, len(PRE):] @ w[1 + len(PRE):]
    P(f"\nShare of the score's spread after Week {THROUGH}: preseason view {100 * zp.var() / (zp.var() + zi.var()):.0f}%, in-season view {100 * zi.var() / (zp.var() + zi.var()):.0f}% "
      "(variance of each block's contribution on the test seasons).")
    pn = score(now)
    board = sorted(zip(pn, now), key=lambda x: -x[0])
    P(f"\n## 2026 shadow board after Week {THROUGH} (all {len(now)} FBS coaches, P(gone by 2027))\n\n| # | coach | school | yr | record | last yr win% | P(gone) |\n|--:|---|---|--:|---|--:|--:|")
    for k, (p, r) in enumerate(board[:25], 1):
        P(f"| {k} | {r['coach']} | {r['school']} | {r['tenure']} | {r['rec']} | {100 * r['last_wp']:.0f} | {100 * p:.0f}% |")
    rank = {r["school"]: (k, p) for k, (p, r) in enumerate(board, 1)}
    P("\nNamed checks: " + " · ".join(f"{s} #{rank[s][0]} ({100 * rank[s][1]:.0f}%)" for s in ("Clemson", "Florida State", "Maryland", "Baylor", "Wisconsin", "South Carolina", "USC", "Florida", "Penn State") if s in rank))
    P("\nLimits: no buyout, contract, AD or booster data, and no quotes; 'gone' mixes firings with retirements; a first-year coach is scored on the previous coach's record. "
      "The CBS rating cannot be backtested (no archive), so this measures the machine half only.")
    text = "\n".join(out)
    (HERE / "internal" / "HOT_SEAT_STUDY_2026.md").write_text(text, encoding="utf-8")
    (HERE / "internal" / f"hot_seat_shadow_week{THROUGH + 1}.json").write_text(json.dumps(
        [dict(rank=k, coach=r["coach"], school=r["school"], tenure=r["tenure"], record=r["rec"], p_gone=round(float(p), 3)) for k, (p, r) in enumerate(board, 1)], indent=1), encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
