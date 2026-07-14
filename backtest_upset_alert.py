"""Backtest the Upset Board rules against 2023-2025.

For each season Y, the model prior is FINAL FPI FROM SEASON Y-1 — exactly the
information the live alert has in the preseason (it never peeks). Alert rules
are identical to build_conference_book.fetch_games:

  model margin (home persp.) = FPI[home] - FPI[away] + 2.5 HFA (0 neutral)
  edge = model margin + spread
  RED  = model picks the market underdog outright, |spread| >= 3
  YEL  = same side as market, |edge| >= 6

Grading: model side vs the recorded line; pushes excluded from win%.
Break-even at -110 juice is 52.38%.

Usage: python backtest_upset_alert.py [--refresh]
Writes per-alert detail to backtest_alerts.csv and a summary to
BACKTEST_RESULTS.md.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "fpi-decomposition"))

import cfbd_client as cfbd
from name_mapping import normalize_name as norm

HFA = 2.5
EDGE_YEL = 6.0
RED_MIN_SPREAD = 3.0
SEASONS = [2023, 2024, 2025]
PROVIDERS = ["DraftKings", "Bovada", "ESPN Bet"]


def fpi_map(year: int, refresh: bool) -> dict:
    rows = cfbd.get("/ratings/fpi", {"year": year}, refresh)
    out = {}
    for r in rows:
        team = r.get("team") or r.get("school")
        val = r.get("fpi") if r.get("fpi") is not None else r.get("rating")
        if team and val is not None:
            out[norm(team)] = float(val)
    return out


def lines_map(year: int, refresh: bool) -> dict:
    records = cfbd.get("/lines", {"year": year, "seasonType": "regular"}, refresh)
    out = {}
    for g in records:
        lines = g.get("lines") or []
        if not lines:
            continue
        ranked = sorted(lines, key=lambda ln: (
            PROVIDERS.index(ln.get("provider")) if ln.get("provider") in PROVIDERS else 99))
        spread = next((ln["spread"] for ln in ranked if ln.get("spread") is not None), None)
        if spread is not None:
            out[g.get("id")] = float(spread)
    return out


def run_season(year: int, refresh: bool) -> list[dict]:
    prior = fpi_map(year - 1, refresh)
    spreads = lines_map(year, refresh)
    games = cfbd.get("/games", {"year": year, "seasonType": "regular"}, refresh)

    def pick(g, *names):
        for n in names:
            if g.get(n) is not None:
                return g[n]
        return None

    alerts = []
    for g in games:
        home, away = pick(g, "homeTeam", "home_team"), pick(g, "awayTeam", "away_team")
        hp, ap = pick(g, "homePoints", "home_points"), pick(g, "awayPoints", "away_points")
        spread = spreads.get(pick(g, "id"))
        if not home or not away or spread is None or hp is None or ap is None:
            continue
        hf, af = prior.get(norm(home)), prior.get(norm(away))
        if hf is None or af is None:
            continue
        neutral = bool(pick(g, "neutralSite", "neutral_site"))
        model_margin = hf - af + (0 if neutral else HFA)
        edge = model_margin + spread  # spread is home-perspective
        model_side = home if edge > 0 else away
        model_fav = home if model_margin > 0 else away
        market_fav = home if spread < 0 else away
        if model_fav != market_fav and abs(spread) >= RED_MIN_SPREAD:
            tier = "RED"
        elif abs(edge) >= EDGE_YEL:
            tier = "YEL"
        else:
            continue

        margin = hp - ap
        covered = margin + spread  # >0 home covered
        side_is_home = model_side == home
        ats_val = covered if side_is_home else -covered
        ats = "P" if ats_val == 0 else ("W" if ats_val > 0 else "L")
        dog = away if market_fav == home else home
        dog_won = (margin < 0) if market_fav == home else (margin > 0)
        alerts.append(dict(season=year, week=pick(g, "week"), home=home, away=away,
                           spread=spread, model_margin=round(model_margin, 1),
                           edge=round(edge, 1), tier=tier, model_side=model_side,
                           final=f"{hp}-{ap}", ats=ats,
                           dog_won=(dog_won if tier == "RED" else "")))
    return alerts


def record(rows):
    w = sum(1 for r in rows if r["ats"] == "W")
    l = sum(1 for r in rows if r["ats"] == "L")
    p = sum(1 for r in rows if r["ats"] == "P")
    pct = 100 * w / (w + l) if w + l else 0
    return w, l, p, pct


def main():
    refresh = "--refresh" in sys.argv
    all_alerts = []
    for y in SEASONS:
        season = run_season(y, refresh)
        all_alerts += season
        print(f"{y}: {len(season)} alerts "
              f"({sum(1 for a in season if a['tier'] == 'RED')} red)")

    with open(HERE / "backtest_alerts.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(all_alerts[0].keys()))
        wr.writeheader()
        wr.writerows(all_alerts)

    lines = ["# Upset Alert Backtest — 2023-2025",
             "",
             "Prior = previous season's final FPI (exactly what the live alert knows in July).",
             "Model side graded ATS vs the recorded line. Break-even at -110: **52.38%**.",
             ""]
    lines.append("| slice | W-L-P | win% |")
    lines.append("|---|---|---|")

    def add(label, rows):
        w, l, p, pct = record(rows)
        lines.append(f"| {label} | {w}-{l}-{p} | {pct:.1f}% |")
        print(f"{label:<28} {w}-{l}-{p}  ({pct:.1f}%)")

    add("ALL alerts", all_alerts)
    for y in SEASONS:
        add(f"  {y}", [a for a in all_alerts if a["season"] == y])
    add("RED only", [a for a in all_alerts if a["tier"] == "RED"])
    add("YELLOW only", [a for a in all_alerts if a["tier"] == "YEL"])
    for lo, hi in ((6, 10), (10, 15), (15, 99)):
        add(f"edge {lo}-{hi if hi < 99 else '+'}",
            [a for a in all_alerts if lo <= abs(a["edge"]) < hi])
    add("early season (wks 1-4)", [a for a in all_alerts if (a["week"] or 0) <= 4])
    add("late season (wks 10+)", [a for a in all_alerts if (a["week"] or 0) >= 10])

    reds = [a for a in all_alerts if a["tier"] == "RED"]
    dog_w = sum(1 for a in reds if a["dog_won"] is True)
    lines += ["", f"**Red-alert dogs outright:** {dog_w}-{len(reds) - dog_w} "
              f"({100 * dog_w / len(reds):.1f}% — dogs at +3 or longer, so outright "
              "win% well below 50 can still be profitable at moneyline prices)."]
    print(f"\nRED dogs outright: {dog_w}-{len(reds) - dog_w}")

    lines += ["", "## Honest read", "",
              "The prior is *stale by construction* (last season's final FPI applied to a new",
              "roster year, all season long). If this shows edge, it's despite that handicap;",
              "in-season the live system upgrades to current-year FPI as CFBD mirrors it.",
              "Slippage, line-shopping, and closing-line movement are not modeled.",
              "", f"Per-alert detail: `backtest_alerts.csv` ({len(all_alerts)} alerts)."]
    (HERE / "BACKTEST_RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwrote BACKTEST_RESULTS.md + backtest_alerts.csv ({len(all_alerts)} alerts)")


if __name__ == "__main__":
    main()
