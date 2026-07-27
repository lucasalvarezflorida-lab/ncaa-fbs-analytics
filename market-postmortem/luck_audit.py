"""Luck audit: which records were built on coin flips.

For every team, compare the prior season's actual wins to its
Pythagorean expectation (points-based) and its one-score record
(decided by <= 8). Big gaps = standings luck: one-score outcomes are
near-coin-flips and don't persist (see the identity batteries — the
one-possession "trends" were the biggest source of fake team angles).

  python luck_audit.py cfb [--year 2025]   # every team on Lucas's boards,
                                           # annotated with board rank/flag
  python luck_audit.py nfl [--year 2025]   # all 32, from the tracker's
                                           # nfl_games_live.csv

Regular season only (that's what standings and narratives are built on).
Forecasting context, NOT a betting rule: the NFL board priced 0/42
slices and win-total markets track Pythagorean already. luck > 0 means
the record flattered the team; luck < 0 means it undersold them.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent      # market-postmortem/
ROOT = HERE.parent

PYTH_EXP = {"cfb": 2.9, "nfl": 2.37}
ONE_SCORE = 8
SHOW_LUCK = 1.0     # |luck wins| to make the table
SHOW_OSNET = 3      # or |one-score net|


def tally(games):
    """games: iterable of (team, pts_for, pts_against). -> {team: stats}"""
    S = {}
    for team, pf, pa in games:
        s = S.setdefault(team, dict(w=0, l=0, t=0, pf=0, pa=0, osw=0, osl=0))
        s["pf"] += pf; s["pa"] += pa
        if pf == pa:
            s["t"] += 1
            continue
        won = pf > pa
        s["w"] += won; s["l"] += not won
        if abs(pf - pa) <= ONE_SCORE:
            s["osw"] += won; s["osl"] += not won
    return S


def rows_from(stats, exp, min_games, extra=lambda t: {}):
    out = []
    for t, s in stats.items():
        n = s["w"] + s["l"] + s["t"]
        if n < min_games:
            continue
        pyth = n * s["pf"] ** exp / (s["pf"] ** exp + s["pa"] ** exp)
        rec = f"{s['w']}-{s['l']}" + (f"-{s['t']}" if s["t"] else "")
        out.append(dict(
            team=t, rec=rec, diff=s["pf"] - s["pa"],
            onescore=f"{s['osw']}-{s['osl']}", osnet=s["osw"] - s["osl"],
            pyth=round(pyth, 1), luck=round(s["w"] + 0.5 * s["t"] - pyth, 1),
            **extra(t)))
    out.sort(key=lambda r: -r["luck"])
    return out


def cfb_rows(year):
    sys.path.insert(0, str(ROOT / "fpi-decomposition"))
    from name_mapping import normalize_name as norm
    games = json.load(open(
        ROOT / "fpi-decomposition" / "data" /
        f"games_seasonType-regular_year-{year}.json", encoding="utf-8"))
    board = json.load(open(ROOT / "lucas-board" / "lucas_board_2026.json",
                           encoding="utf-8"))["teams"]
    names = {norm(v["team"]): v["team"] for v in board.values()}

    def gp(g, *keys):
        for k in keys:
            if g.get(k) is not None:
                return g[k]

    flat = []
    for g in games:
        hp = gp(g, "homePoints", "home_points")
        if hp is None:
            continue
        ap = gp(g, "awayPoints", "away_points")
        for team, pf, pa in ((gp(g, "homeTeam", "home_team"), hp, ap),
                             (gp(g, "awayTeam", "away_team"), ap, hp)):
            t = names.get(norm(team or ""))
            if t:
                flat.append((t, pf, pa))

    info = {v["team"]: v for v in board.values()}

    def extra(t):
        v = info[t]
        return dict(board=v["group"],
                    lucas=v["lucas_rank"] if v["lucas_rank"] else "-",
                    flag=v["flag"] or "")
    return rows_from(tally(flat), PYTH_EXP["cfb"], min_games=8, extra=extra)


def nfl_rows(year):
    import pandas as pd
    csv = HERE / "nfl_games_live.csv"
    if not csv.exists():
        raise SystemExit("nfl_games_live.csv missing — run nfl_watchlist.py "
                         "once to download the nflverse feed")
    df = pd.read_csv(csv, low_memory=False)
    g = df[(df.season == year) & (df.game_type == "REG") & df.result.notna()]
    flat = []
    for _, r in g.iterrows():
        flat.append((r.home_team, r.home_score, r.away_score))
        flat.append((r.away_team, r.away_score, r.home_score))
    return rows_from(tally(flat), PYTH_EXP["nfl"], min_games=10)


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("sport", choices=("cfb", "nfl"))
    p.add_argument("--year", type=int, default=2025)
    p.add_argument("--all", action="store_true",
                   help="print every team, not just the notable ones")
    a = p.parse_args()

    rows = cfb_rows(a.year) if a.sport == "cfb" else nfl_rows(a.year)
    cols = [k for k in rows[0] if k != "osnet"]
    widths = {k: max(len(k), *(len(str(r[k])) for r in rows)) + 2
              for k in cols}
    print("".join(k.rjust(widths[k]) for k in cols))
    shown = 0
    for r in rows:
        if not a.all and abs(r["luck"]) < SHOW_LUCK and abs(r["osnet"]) < SHOW_OSNET:
            continue
        shown += 1
        print("".join(str(r[k]).rjust(widths[k]) for k in cols))
    print(f"\n{shown}/{len(rows)} teams shown "
          f"(|luck| >= {SHOW_LUCK} wins or |one-score net| >= {SHOW_OSNET}; "
          f"--all for everyone). luck > 0: record flattered them; "
          f"< 0: record undersold them.")


if __name__ == "__main__":
    main()
