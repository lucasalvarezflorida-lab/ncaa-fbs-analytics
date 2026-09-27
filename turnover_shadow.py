"""SHADOW: the on-air ridge re-solved on TURNOVER-ADJUSTED observations
(observation = margin - TO_PTS x turnover margin; item 1 of the 9/27 list,
measured in internal/TURNOVER_2026.md). Never the on-air number until Lucas
switches it.

    python turnover_shadow.py --week 5            -> internal/shadow_turnover_week5.json

Writes every team's rating under the on-air rule, the same rule on
de-lucked margins (cap 28 residual, as on air) and the no-cap variant, the
Top 25 differences, and each card game (card_data_weekN.json) as
"machine X, de-lucked Y".
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

TO_PTS = 3.0


def solve(ctx, cfg):
    """Ratings from every rated game played so far (week 99 = all)."""
    import backtest as bt
    mode = "residual" if 99 >= cfg["switch"] else "margin"
    return ctx.ridge(99, cfg["lam"], cfg["hfa"], cfg["cap"], mode, cfg.get("obs"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--to", type=float, default=TO_PTS)
    a = ap.parse_args()
    from refresh_all import load_env_key
    load_env_key()
    import backtest as bt
    ctx = bt.SeasonCtx(2026)
    cur = bt.MODELS["current"]
    variants = {
        "on_air": cur,
        "de_lucked": dict(cur, obs=dict(to=a.to)),
        "de_lucked_nocap": dict(cur, cap=None, obs=dict(to=a.to)),
    }
    R = {k: solve(ctx, cfg) for k, cfg in variants.items()}
    teams = ctx.teams
    rows = []
    for i, t in enumerate(teams):
        rows.append(dict(team=t, on_air=round(float(R["on_air"][i]), 2), de_lucked=round(float(R["de_lucked"][i]), 2),
                         de_lucked_nocap=round(float(R["de_lucked_nocap"][i]), 2)))
    for k in ("on_air", "de_lucked", "de_lucked_nocap"):
        order = sorted(rows, key=lambda r: -r[k])
        for n, r in enumerate(order, 1):
            r[f"rank_{k}"] = n
    rows.sort(key=lambda r: r["rank_on_air"])
    # card games
    card = []
    cp = HERE / f"card_data_week{a.week}.json"
    if cp.exists():
        c = json.loads(cp.read_text(encoding="utf-8"))
        idx = ctx.idx
        for g in c["games"]:
            h, aw = normalize_name(g["home"]), normalize_name(g["away"])
            if h not in idx or aw not in idx:
                continue
            hfa = 0.0 if g.get("neutral") else cur["hfa"]
            line = {k: round(float(R[k][idx[h]] - R[k][idx[aw]] + hfa), 1) for k in R}
            card.append(dict(game=f"{g['away']} at {g['home']}", machine=line["on_air"], de_lucked=line["de_lucked"],
                             de_lucked_nocap=line["de_lucked_nocap"], diff=round(line["de_lucked"] - line["on_air"], 1)))
    out = dict(week=a.week, generated=dt.datetime.now().isoformat(timespec="minutes"), to_pts=a.to,
               status="SHADOW - not on air until Lucas switches it (internal/TURNOVER_2026.md)",
               games_used=int(len(ctx.games)), teams=rows, card=card)
    (HERE / "internal").mkdir(exist_ok=True)
    p = HERE / "internal" / f"shadow_turnover_week{a.week}.json"
    p.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"wrote {p.relative_to(HERE)}  ({len(ctx.games)} rated games)")
    print("TOP 25 on air -> de-lucked (cap 28) -> de-lucked no cap")
    for r in rows[:25]:
        print(f"{r['rank_on_air']:3d} {r['team']:20s} {r['on_air']:6.1f} | {r['de_lucked']:6.1f} (#{r['rank_de_lucked']:2d}) | {r['de_lucked_nocap']:6.1f} (#{r['rank_de_lucked_nocap']:2d})")
    movers = sorted(rows, key=lambda r: -abs(r["de_lucked"] - r["on_air"]))[:10]
    print("biggest moves (de-lucked minus on air):", [(r["team"], round(r["de_lucked"] - r["on_air"], 1)) for r in movers])
    for g in card:
        print(f"  {g['game']:35s} machine {g['machine']:+6.1f}  de-lucked {g['de_lucked']:+6.1f}  no-cap {g['de_lucked_nocap']:+6.1f}")


if __name__ == "__main__":
    main()
