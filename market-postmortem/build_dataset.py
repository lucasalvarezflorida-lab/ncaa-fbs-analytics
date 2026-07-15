"""Build the per-bet dataset for the market post-mortem (2021-2025).

One row per FBS-vs-FBS game with a closing line: closing/opening spread and
total, moneylines, final score, and every slice column the analysis needs
(power status, rankings, rest days, rivalry, line movement). Reads only from
the shared CFBD cache — run fetch_data.py first.

Output: market_bets_2021_2025.csv

Conventions (match backtest_upset_alert.py):
  spread is HOME-perspective (negative = home favored)
  home_cover_margin = margin + spread  (>0 home covered, 0 push)
"""

from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "fpi-decomposition"))

import cfbd_client as cfbd
from name_mapping import normalize_name as norm

SEASONS = [2021, 2022, 2023, 2024, 2025]
SEASON_TYPES = ["regular", "postseason"]

# Closing-line provider preference (prior art first, then best remaining
# coverage per the 2021-2025 survey). "Draft Kings" is a 2025 spelling glitch.
PROVIDER_RANK = ["DraftKings", "Bovada", "ESPN Bet", "William Hill (New Jersey)",
                 "consensus", "teamrankings", "numberfire"]

POWER_CONFS_PRE24 = {"SEC", "Big Ten", "Big 12", "ACC", "Pac-12"}
POWER_CONFS_24ON = {"SEC", "Big Ten", "Big 12", "ACC"}  # 2-team Pac-12 -> G5

# Curated annual rivalry pairs (normalized names). Not exhaustive — flagged as
# a curated list in the report.
RIVALRIES = {frozenset(map(norm, pair)) for pair in [
    ("Alabama", "Auburn"), ("Ohio State", "Michigan"), ("Army", "Navy"),
    ("Texas", "Oklahoma"), ("Georgia", "Florida"), ("USC", "UCLA"),
    ("USC", "Notre Dame"), ("Florida", "Florida State"),
    ("Miami", "Florida State"), ("Clemson", "South Carolina"),
    ("Oregon", "Oregon State"), ("Washington", "Washington State"),
    ("Alabama", "Tennessee"), ("Auburn", "Georgia"),
    ("Michigan", "Michigan State"), ("Ole Miss", "Mississippi State"),
    ("Oklahoma", "Oklahoma State"), ("Kansas", "Kansas State"),
    ("Iowa", "Iowa State"), ("BYU", "Utah"), ("Virginia", "Virginia Tech"),
    ("North Carolina", "NC State"), ("North Carolina", "Duke"),
    ("Pittsburgh", "West Virginia"), ("Indiana", "Purdue"),
    ("Illinois", "Northwestern"), ("Minnesota", "Wisconsin"),
    ("California", "Stanford"), ("Arizona", "Arizona State"),
    ("Colorado", "Colorado State"), ("Notre Dame", "Navy"),
    ("Georgia", "Georgia Tech"), ("Kentucky", "Louisville"),
    ("Air Force", "Army"), ("Air Force", "Navy"),
    ("Toledo", "Bowling Green"), ("Miami (OH)", "Ohio"),
    ("Utah", "Utah State"), ("Texas", "Texas A&M"),
]}


def pick(g: dict, *names):
    for n in names:
        if g.get(n) is not None:
            return g[n]
    return None


def provider_key(name: str) -> str:
    return "DraftKings" if name == "Draft Kings" else (name or "")


def rank_of(name: str) -> int:
    key = provider_key(name)
    return PROVIDER_RANK.index(key) if key in PROVIDER_RANK else 50


def best_line(lines: list, *fields) -> tuple:
    """First provider (by preference) whose line has ALL fields non-None.

    Returns (provider, line) or (None, None).
    """
    for ln in sorted(lines, key=lambda ln: rank_of(ln.get("provider"))):
        if all(ln.get(f) is not None for f in fields):
            return provider_key(ln.get("provider")), ln
    return None, None


def ap_rankings(year: int) -> dict:
    """(week -> {normalized team: rank}) from the AP Top 25 (fallback Coaches)."""
    weeks = {}
    for wk in cfbd.get("/rankings", {"year": year, "seasonType": "regular"}):
        polls = wk.get("polls") or []
        poll = next((p for p in polls if p.get("poll") == "AP Top 25"), None)
        if poll is None:
            poll = next((p for p in polls if p.get("poll") == "Coaches Poll"), None)
        if poll is None:
            continue
        weeks[wk.get("week")] = {
            norm(r.get("school")): r.get("rank")
            for r in poll.get("ranks") or [] if r.get("school")
        }
    return weeks


def power_status(conference: str, team: str, season: int) -> bool:
    confs = POWER_CONFS_PRE24 if season <= 2023 else POWER_CONFS_24ON
    if conference in confs:
        return True
    return norm(team or "") == norm("Notre Dame")  # power independent


def parse_date(s: str):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def build_season(year: int, out: list) -> dict:
    stats = dict(games=0, fbs=0, with_spread=0, with_total=0, with_ml=0,
                 with_open=0)

    games = []
    for stype in SEASON_TYPES:
        games += cfbd.get("/games", {"year": year, "seasonType": stype})

    lines_by_id = {}
    for stype in SEASON_TYPES:
        for rec in cfbd.get("/lines", {"year": year, "seasonType": stype}):
            if rec.get("lines"):
                lines_by_id[rec.get("id")] = rec["lines"]

    ranks = ap_rankings(year)
    max_poll_week = max(ranks) if ranks else 0

    # Rest days: last kickoff per team across the whole season.
    last_game: dict[str, datetime] = {}
    for g in sorted(games, key=lambda g: pick(g, "startDate") or ""):
        stats["games"] += 1

    for g in sorted(games, key=lambda g: pick(g, "startDate") or ""):
        home, away = pick(g, "homeTeam"), pick(g, "awayTeam")
        date = parse_date(pick(g, "startDate"))
        rest = {}
        for side, team in (("home", home), ("away", away)):
            key = norm(team) if team else None
            prev = last_game.get(key)
            rest[side] = (date - prev).days if (date and prev) else None
            if key and date:
                last_game[key] = date

        hp, ap_ = pick(g, "homePoints"), pick(g, "awayPoints")
        if (pick(g, "homeClassification") != "fbs"
                or pick(g, "awayClassification") != "fbs"):
            continue
        stats["fbs"] += 1
        if hp is None or ap_ is None or not pick(g, "completed"):
            continue

        game_lines = lines_by_id.get(pick(g, "id")) or []
        prov_spread, ln_spread = best_line(game_lines, "spread")
        if ln_spread is None:
            continue
        stats["with_spread"] += 1
        prov_total, ln_total = best_line(game_lines, "overUnder")
        prov_ml, ln_ml = best_line(game_lines, "homeMoneyline", "awayMoneyline")
        prov_move, ln_move = best_line(game_lines, "spread", "spreadOpen")
        prov_tmove, ln_tmove = best_line(game_lines, "overUnder", "overUnderOpen")

        week = pick(g, "week") or 0
        stype = pick(g, "seasonType")
        poll_week = min(week, max_poll_week) if week >= 1 else 1
        if stype == "postseason":
            poll_week = max_poll_week
        poll = ranks.get(poll_week, {})
        h_rank = poll.get(norm(home)) if home else None
        a_rank = poll.get(norm(away)) if away else None

        spread = float(ln_spread["spread"])
        margin = hp - ap_
        total_pts = hp + ap_
        total = float(ln_total["overUnder"]) if ln_total else None
        h_ml = ln_ml.get("homeMoneyline") if ln_ml else None
        a_ml = ln_ml.get("awayMoneyline") if ln_ml else None
        spread_open = float(ln_move["spreadOpen"]) if ln_move else None
        spread_close_mv = float(ln_move["spread"]) if ln_move else None
        total_open = float(ln_tmove["overUnderOpen"]) if ln_tmove else None
        total_close_mv = float(ln_tmove["overUnder"]) if ln_tmove else None

        if total is not None:
            stats["with_total"] += 1
        if h_ml is not None:
            stats["with_ml"] += 1
        if spread_open is not None:
            stats["with_open"] += 1

        neutral = bool(pick(g, "neutralSite"))
        h_power = power_status(pick(g, "homeConference"), home, year)
        a_power = power_status(pick(g, "awayConference"), away, year)
        matchup = {(True, True): "P4vP4", (False, False): "G5vG5"}.get(
            (h_power, a_power), "P4vG5")

        out.append(dict(
            game_id=pick(g, "id"), season=year, season_type=stype, week=week,
            date=date.date().isoformat() if date else "",
            home=home, away=away, neutral=int(neutral),
            conference_game=int(bool(pick(g, "conferenceGame"))),
            home_conference=pick(g, "homeConference"),
            away_conference=pick(g, "awayConference"),
            home_power=int(h_power), away_power=int(a_power),
            power_matchup=matchup,
            home_rank=h_rank or "", away_rank=a_rank or "",
            home_rest_days=rest["home"] if rest["home"] is not None else "",
            away_rest_days=rest["away"] if rest["away"] is not None else "",
            rivalry=int(frozenset((norm(home), norm(away))) in RIVALRIES),
            provider_spread=prov_spread, spread_close=spread,
            provider_move=prov_move or "",
            spread_open=spread_open if spread_open is not None else "",
            spread_move=(round(spread_close_mv - spread_open, 1)
                         if spread_open is not None else ""),
            provider_total=prov_total or "",
            total_close=total if total is not None else "",
            total_open=total_open if total_open is not None else "",
            total_move=(round(total_close_mv - total_open, 1)
                        if total_open is not None else ""),
            provider_ml=prov_ml or "",
            home_ml=h_ml if h_ml is not None else "",
            away_ml=a_ml if a_ml is not None else "",
            home_points=hp, away_points=ap_,
            margin=margin, total_points=total_pts,
            home_cover_margin=round(margin + spread, 1),
            home_covered=("P" if margin + spread == 0
                          else "W" if margin + spread > 0 else "L"),
            over_margin=(round(total_pts - total, 1) if total is not None else ""),
            over_result=("" if total is None else
                         "P" if total_pts == total else
                         "O" if total_pts > total else "U"),
            home_won=int(margin > 0),
        ))
    return stats


def main() -> None:
    rows: list[dict] = []
    for year in SEASONS:
        s = build_season(year, rows)
        print(f"{year}: fbs-vs-fbs completed w/ spread={s['with_spread']:>4} "
              f"(total={s['with_total']}, ml={s['with_ml']}, open={s['with_open']})")

    out_path = HERE / "market_bets_2021_2025.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    print(f"\nwrote {out_path.name}: {len(rows)} rows")


if __name__ == "__main__":
    main()
