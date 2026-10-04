"""Does a replacement QB's recruiting rating (or the starter's quality) predict how much a team falls short
when its starting QB is absent?  INTERNAL study, Lucas 10/4/2026 ("do the backtest first").

EVENT  a team-game where the season's primary passer (>= 3 earlier games, >= 100 dropbacks) threw < 20% of
       the team's dropbacks.  That is the hindsight version of what a news entry "QB out" says, so it is the
       right sample for the on-air QB-out layer.  Split: FIRST absence (he played the previous game) vs
       CONTINUING (also absent the game before; the machine has absorbed one game of the backup).
OUTCOME shortfall = predicted margin - actual margin, from the team's side, vs the on-air machine's pre-game
       number (backtest "current" model); EXCESS = shortfall minus the mean shortfall of non-event team-sides
       in the same predicted-margin bucket (favorites run short anyway).
PREDICTORS  replacement's HS recruiting rating (CFBD /recruiting/players, classes 2016-2025, matched by team +
       initial.surname, else a unique national match = transfer), starter's PPA edge over the league.
FIT 2022-24, TEST 2025.   python qb_replacement_study.py
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
import backtest as bt  # noqa: E402
from availability import qb_table, passer_key, starter_status  # noqa: E402
from name_mapping import normalize_name  # noqa: E402

FIT, TEST = (2022, 2023, 2024), (2025,)
BUCKETS = [(-99, 0), (0, 7), (7, 14), (14, 99)]


def recruits():
    by_key = defaultdict(list)
    for y in range(2016, 2026):
        for r in cfbd.get("/recruiting/players", {"year": y, "position": "QB", "classification": "HighSchool"}, True):
            if r.get("rating") is None or not r.get("name"):
                continue
            by_key[passer_key(r["name"])].append((y, normalize_name(r.get("committedTo") or ""), float(r["rating"])))
    return by_key


def rating_for(by_key, key, team, season):
    c = [x for x in by_key.get(key, []) if x[0] <= season]
    if not c:
        return None, "none"
    same = [x for x in c if x[1] == team]
    if same:
        return max(x[2] for x in same), "team"
    if len(c) == 1:
        return c[0][2], "transfer"
    return None, "ambiguous"


def bucket(p):
    for lo, hi in BUCKETS:
        if lo <= p < hi:
            return (lo, hi)


def collect(by_key):
    rows = []
    for s in FIT + TEST:
        ctx = bt.SeasonCtx(s)
        qb = qb_table(s, ctx.games)
        league = [v for r in qb.values() for g in r for v in g["passers"].values()]
        lg_ppa = sum(v[1] for v in league) / max(sum(v[2] for v in league), 1)
        for w in range(2, 16):
            cur = bt.ridge_predict(ctx, w, bt.MODELS["current"])
            for g in ctx.games:
                if g["week"] != w or g["id"] not in cur:
                    continue
                for side, sign in ((g["home"], 1), (g["away"], -1)):
                    seq = qb.get(side, [])
                    this = next((r for r in seq if r["game_id"] == g["id"]), None)
                    prev = [r for r in seq if r["week"] < w]
                    if not this or len(prev) < 3:
                        continue
                    tot = defaultdict(lambda: [0, 0.0, 0])
                    for r in prev:
                        for n, v in r["passers"].items():
                            tot[n][0] += v[0]; tot[n][1] += v[1]; tot[n][2] += v[2]
                    star = max(tot, key=lambda n: tot[n][0])
                    pred = sign * cur[g["id"]][0]
                    short = pred - sign * g["margin"]
                    absent = this["passers"].get(star, [0])[0] / max(this["dropbacks"], 1) < 0.2
                    real = tot[star][0] >= 100
                    row = dict(season=s, week=w, team=side, pred=pred, short=short, event=bool(absent and real),
                               cont=False, rating=None, how="", edge=None)
                    if row["event"]:
                        last = prev[-1]
                        row["cont"] = last["passers"].get(star, [0])[0] / max(last["dropbacks"], 1) < 0.2
                        rep = this["primary"]
                        row["rating"], row["how"] = rating_for(by_key, rep, side, s)
                        if tot[star][2] >= 40:
                            row["edge"] = 100 * (tot[star][1] / tot[star][2] - lg_ppa)
                    rows.append(row)
    return rows


def ols(X, y):
    X = np.column_stack([np.ones(len(X)), X]); b, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ b; s2 = res @ res / max(len(y) - X.shape[1], 1)
    se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    return b, se


def main():
    by_key = recruits()
    rows = collect(by_key)
    base = defaultdict(list)
    for r in rows:
        if not r["event"]:
            base[bucket(r["pred"])].append(r["short"])
    bm = {k: float(np.mean(v)) for k, v in base.items()}
    for r in rows:
        r["excess"] = r["short"] - bm[bucket(r["pred"])]
    out = []
    P = out.append

    def stat(label, rs):
        if len(rs) < 3:
            return f"| {label} | {len(rs)} | - | - |"
        v = np.array([r["excess"] for r in rs]); return f"| {label} | {len(v)} | {v.mean():+.2f} | {v.std() / np.sqrt(len(v)):.2f} |"

    ev = [r for r in rows if r["event"]]
    P("# QB replacement study (INTERNAL, Sun Oct 4 2026)\n")
    P(f"Team-sides {len(rows)}, QB-absent events {len(ev)} (fit 2022-24: {sum(r['season'] in FIT for r in ev)}, test 2025: {sum(r['season'] in TEST for r in ev)}). "
      "Excess shortfall = points the team fell short of the on-air number beyond what non-event sides of the same predicted margin fall short (positive = hurt).\n")
    P("## All events\n\n| group | n | excess | se |\n|---|--:|--:|--:|")
    P(stat("all absent", ev)); P(stat("first game absent", [r for r in ev if not r["cont"]])); P(stat("continuing (machine absorbed 1)", [r for r in ev if r["cont"]]))
    for lo, hi in BUCKETS:
        P(stat(f"predicted margin {lo if lo > -99 else '<0'}..{hi if hi < 99 else '+'}", [r for r in ev if bucket(r["pred"]) == (lo, hi)]))
    P("\n## By replacement recruiting rating (HS composite)\n\n| replacement | n | excess | se |\n|---|--:|--:|--:|")
    rated = [r for r in ev if r["rating"] is not None]
    P(f"(rating found for {len(rated)} of {len(ev)}; matched by team {sum(r['how'] == 'team' for r in ev)}, as a transfer {sum(r['how'] == 'transfer' for r in ev)}, none {sum(r['how'] in ('none', 'ambiguous') for r in ev)})\n")
    cut = np.quantile([r["rating"] for r in rated], [1 / 3, 2 / 3]) if len(rated) >= 12 else (0.85, 0.9)
    P(stat(f"top third (>= {cut[1]:.3f})", [r for r in rated if r["rating"] >= cut[1]]))
    P(stat("middle third", [r for r in rated if cut[0] <= r["rating"] < cut[1]]))
    P(stat(f"bottom third (< {cut[0]:.3f})", [r for r in rated if r["rating"] < cut[0]]))
    P(stat("no HS rating found (walk-on / JUCO / unmatched)", [r for r in ev if r["rating"] is None]))
    P("\n## By starter quality (PPA edge over league, starter with >= 40 dropbacks)\n\n| starter | n | excess | se |\n|---|--:|--:|--:|")
    have = [r for r in ev if r["edge"] is not None]
    P(stat("above league", [r for r in have if r["edge"] >= 0])); P(stat("below league", [r for r in have if r["edge"] < 0]))
    P(stat("top quartile of starters", [r for r in have if r["edge"] >= np.quantile([x["edge"] for x in have], 0.75)]))

    # regression on favorites-aware features, fit vs test
    def feats(r):
        fav = max(r["pred"], 0.0)
        return [fav, (r["edge"] or 0.0), ((r["rating"] if r["rating"] is not None else 0.80) - 0.85) * 10]
    P("\n## Regression of excess on [favorite margin, starter PPA edge x100, replacement rating x10 vs .85]\n")
    tr = [r for r in ev if r["season"] in FIT]; te = [r for r in ev if r["season"] in TEST]
    b, se = ols(np.array([feats(r) for r in tr]), np.array([r["excess"] for r in tr]))
    names = ["const", "fav margin", "starter edge", "replacement rating"]
    P("| term | coef | se |\n|---|--:|--:|")
    for n_, c_, s_ in zip(names, b, se):
        P(f"| {n_} | {c_:+.3f} | {s_:.3f} |")
    # out-of-sample: MAE of (short - penalty) on test events, penalty = model vs 0 vs flat
    def pen(r, bb):
        return bb[0] + float(np.dot(bb[1:], feats(r)))
    y = np.array([r["excess"] for r in te])
    flat = float(np.mean([r["excess"] for r in tr]))
    P(f"\nTest 2025 ({len(te)} events), mean |excess left after the penalty| (lower = better; 0-penalty is today's machine before this layer):\n")
    P("| penalty rule | MAE on test events |\n|---|--:|")
    P(f"| none (machine as is) | {np.mean(np.abs(y)):.2f} |")
    P(f"| flat {flat:+.1f} for every absent QB | {np.mean(np.abs(y - flat)):.2f} |")
    P(f"| fitted (favorite margin + starter edge + replacement rating) | {np.mean(np.abs(y - np.array([pen(r, b) for r in te]))):.2f} |")
    b2, _ = ols(np.array([feats(r)[:1] for r in tr]), np.array([r["excess"] for r in tr]))
    P(f"| fitted, favorite margin only | {np.mean(np.abs(y - np.array([b2[0] + b2[1] * feats(r)[0] for r in te]))):.2f} |")
    P("\nCaveat: the event is defined with hindsight (the starter did not throw THIS game), which is exactly what a confirmed news entry says, "
      "so it is the right sample for the on-air layer, but it is not a deployable auto-rule.")
    text = "\n".join(out)
    (HERE / "internal" / "QB_REPLACEMENT_STUDY_2026.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
