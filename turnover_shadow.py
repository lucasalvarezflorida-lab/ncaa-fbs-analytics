"""Weekly comparison of the on-air rule and the rule it replaced.

From Sun 9/27 the on-air machine learns from de-lucked margins (margin - 3 x
turnover margin, lam 2, margin cap 42; internal/TURNOVER_2026.md). This
writes, for the record, what the 9/20 rule (lam 3, cap 28 residual, raw
margins) would say this week beside the on-air number, so the switch can
be graded over the season.

    python turnover_shadow.py --week 5   -> internal/shadow_turnover_week5.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    a = ap.parse_args()
    from refresh_all import load_env_key, load_fpi_2026
    load_env_key()
    import inseason_ratings as ir
    prior = load_fpi_2026()
    games = [g for g in ir.completed_games_2026(False) if g["home"] in prior and g["away"] in prior]
    variants = {"on_air": ir.RULE, "rule_920": ir.RULE_920, "delucked_nocap_lam3": dict(lam=3.0, cap=None, cap_mode="margin", to_pts=3.0)}
    R = {k: ir.solve_2026(prior, games, rule) for k, rule in variants.items()}
    teams = sorted(prior)
    rows = [dict(team=t, **{k: round(float(R[k][t]), 2) for k in R}) for t in teams]
    for k in R:
        for n, r in enumerate(sorted(rows, key=lambda r: -r[k]), 1):
            r[f"rank_{k}"] = n
    rows.sort(key=lambda r: r["rank_on_air"])
    card = []
    cp = HERE / f"card_data_week{a.week}.json"
    if cp.exists():
        c = json.loads(cp.read_text(encoding="utf-8"))
        for g in c["games"]:
            h, aw = normalize_name(g["home"]), normalize_name(g["away"])
            if h not in prior or aw not in prior:
                continue
            hfa = 0.0 if g.get("neutral") else ir.HFA
            line = {k: round(float(R[k][h] - R[k][aw] + hfa), 1) for k in R}
            card.append(dict(game=f"{g['away']} at {g['home']}", **line, diff=round(line["on_air"] - line["rule_920"], 1)))
    out = dict(week=a.week, generated=dt.datetime.now().isoformat(timespec="minutes"), on_air_rule=ir.RULE,
               games_used=len(games), teams=rows, card=card,
               note="on_air = the rule of the day; rule_920 = the rule replaced on 9/27, kept for grading the switch")
    p = HERE / "internal" / f"shadow_turnover_week{a.week}.json"
    p.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"wrote {p.relative_to(HERE)}  ({len(games)} rated games; on-air rule {ir.RULE})")
    print("TOP 25: on air | 9/20 rule | de-lucked no cap lam 3")
    for r in rows[:25]:
        print(f"{r['rank_on_air']:3d} {r['team']:20s} {r['on_air']:6.1f} | {r['rule_920']:6.1f} (#{r['rank_rule_920']:2d}) | {r['delucked_nocap_lam3']:6.1f} (#{r['rank_delucked_nocap_lam3']:2d})")
    for g in card:
        print(f"  {g['game']:35s} on air {g['on_air']:+6.1f}  9/20 rule {g['rule_920']:+6.1f}  diff {g['diff']:+5.1f}")


if __name__ == "__main__":
    main()
