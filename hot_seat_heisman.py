"""Two machine-assisted boards for the podcast: the Hot Seat Top 10 and the
Heisman board ("our own favorite"). Writes boards_week{N}.json for
make_episode_deck.py; the notes (.md) carry the reasoning.

HOT SEAT — seat score = 0.6 * (CBS rating / 5) + 0.4 * (1 - P(hit the bar))
  * CBS rating  = the "man": CBS Sports' 2026 hot-seat rating (0-5, Aug 29).
  * P(hit bar)  = the machine: probability the team reaches the win total
    the coach needs, from the Season Sim's projected wins (our in-season
    rating, 10k Monte Carlo) with a normal spread fitted to the sim's
    10th/90th percentiles. The bar per coach is hand-set from the deep-dive
    "how he escapes" write-ups (see BARS) — that is a judgment call, say so.

HEISMAN — index = team factor * blended efficiency
  * team factor = 0.5 + 0.5 * P(10+ wins) from the Season Sim (winners come
    from 10-win teams; the floor keeps a great QB on a 9-win team alive).
  * blended efficiency = (n2026 * PPA2026 + K * PPA2025) / (n2026 + K), CFBD
    predicted points added per play, K = 150 plays of prior weight (about
    the machine's "prior is worth three games" idea at QB pace). New
    starters without a 2025 line get the FBS-average prior (0.35).
  * QBs only on the main board; non-QBs are listed separately because PPA
    per play is not comparable across positions.

Usage: python hot_seat_heisman.py [--week N] [--refresh]
"""

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "fpi-decomposition"))
import cfbd_client as cfbd  # noqa: E402
from name_mapping import normalize_name  # noqa: E402

WORKBOOK = HERE / "NCAA_FBS_Teams.xlsm"
RATINGS = HERE / "ratings_current_2026.json"

# ---- hand-maintained inputs (dated) -------------------------------------
CBS_DATE = "2026-08-29"
# CBS Sports 2026 hot-seat ratings (0-5). None = not in the published list;
# the prep boards' temperature is used instead (marked "est." on the slide).
CBS = {
    "Florida State": ("Mike Norvell", 5.0), "Wisconsin": ("Luke Fickell", 5.0),
    "Baylor": ("Dave Aranda", 5.0), "Maryland": ("Mike Locksley", 4.9),
    "South Carolina": ("Shane Beamer", 4.3), "North Carolina": ("Bill Belichick", 4.1),
    "Middle Tennessee": ("Derek Mason", 3.6), "Boston College": ("Bill O'Brien", 3.5),
    "Cincinnati": ("Scott Satterfield", 3.5), "Mississippi State": ("Jeff Lebby", 3.3),
    "Georgia State": ("Dell McGee", 3.3), "Louisiana Tech": ("Sonny Cumbie", 3.2),
    "Colorado": ("Deion Sanders", 3.1), "Georgia Southern": ("Clay Helton", 3.1),
    "Clemson": ("Dabo Swinney", 3.1), "Alabama": ("Kalen DeBoer", 3.0),
    "NC State": ("Dave Doeren", 3.0), "Nebraska": ("Matt Rhule", 3.0),
    "Eastern Michigan": ("Chris Creighton", 2.8), "Liberty": ("Jamey Chadwell", 2.7),
    "New Mexico State": ("Tony Sanchez", 2.7), "Arkansas State": ("Butch Jones", 2.4),
    "Kansas": ("Lance Leipold", 2.3), "Louisiana": ("Michael Desormeaux", 2.2),
    "Akron": ("Joe Moorhead", 2.2), "Nevada": ("Jeff Choate", 2.2),
    "Minnesota": ("P.J. Fleck", 2.1),
    # not in the fetched CBS list — estimated from the conference prep boards
    "Rutgers": ("Greg Schiano", None), "Oklahoma": ("Brent Venables", None),
    "USC": ("Lincoln Riley", None), "Wyoming": ("Jay Sawvel", None),
    "UL Monroe": ("Bryant Vincent", None),
}
EST = {"Rutgers": 3.0, "Oklahoma": 2.9, "USC": 2.9, "Wyoming": 3.0, "UL Monroe": 3.0}
# the win total that keeps the job (deep-dive "how he escapes"; judgment)
BARS = {
    "Florida State": 8, "Wisconsin": 6, "Baylor": 7, "Maryland": 6,
    "South Carolina": 7, "North Carolina": 6, "Middle Tennessee": 6,
    "Boston College": 5, "Cincinnati": 6, "Mississippi State": 5,
    "Georgia State": 5, "Louisiana Tech": 6, "Colorado": 6,
    "Georgia Southern": 6, "Clemson": 9, "Alabama": 10, "NC State": 7,
    "Nebraska": 8, "Eastern Michigan": 6, "Liberty": 7, "New Mexico State": 5,
    "Arkansas State": 7, "Kansas": 6, "Louisiana": 7, "Akron": 5, "Nevada": 5,
    "Minnesota": 7, "Rutgers": 6, "Oklahoma": 8, "USC": 9, "Wyoming": 5,
    "UL Monroe": 5,
}
# tenure record at the school entering 2026 (CFBD coach seasons 2021-25 +
# earlier years from the prep files where the tenure predates 2021)
TENURE = {
    "Florida State": "38-34, yr 7", "Wisconsin": "17-21, yr 4", "Baylor": "36-37, yr 7",
    "Maryland": "37-49, yr 8", "South Carolina": "33-30, yr 6", "North Carolina": "4-8, yr 2",
    "Middle Tennessee": "3-9 in 2024, yr 3", "Boston College": "9-16, yr 3", "Cincinnati": "15-22, yr 4",
    "Mississippi State": "7-18, yr 3", "Georgia State": "4-20, yr 3", "Louisiana Tech": "11-26 thru 2024, yr 5",
    "Colorado": "16-21, yr 4", "Georgia Southern": "20-19 thru 2024, yr 5", "Clemson": "186-53, yr 18",
    "Alabama": "20-8, yr 3", "NC State": "yr 14 - 6-7 and 6-6 the last two", "Nebraska": "19-19, yr 4",
    "Eastern Michigan": "27-24 thru 2024, yr 13", "Liberty": "21-5 thru 2024, yr 4", "New Mexico State": "3-9 in 2024, yr 3",
    "Arkansas State": "26-37, yr 6", "Kansas": "27-35, yr 6", "Louisiana": "29-25, yr 5",
    "Akron": "8-28 thru 2024, yr 5", "Nevada": "3-10 in 2024, yr 3", "Minnesota": "32-20 thru 2024, yr 10",
    "Rutgers": "31-41 2nd stint, yr 7", "Oklahoma": "32-20, yr 5", "USC": "35-18, yr 5",
    "Wyoming": "7-17, yr 3", "UL Monroe": "8-16, yr 3",
}

# Heisman market (DraftKings via NBC Sports, Sep 8 2026) — refresh weekly
MARKET_DATE = "2026-09-08"
MARKET = {
    "Darian Mensah": 600, "Arch Manning": 950, "Jeremiah Smith": 1000,
    "C.J. Carr": 1100, "Malachi Toney": 1250, "Dante Moore": 1300,
    "Trinidad Chambliss": 1300, "Julian Sayin": 1400, "Sam Leavitt": 1500,
    "Jayden Maiava": 1750, "Josh Hoover": 1900, "John Mateer": 2800,
}
QB_POOL = ["Julian Sayin", "Darian Mensah", "C.J. Carr", "Josh Hoover",
           "Arch Manning", "Dante Moore", "Jayden Maiava", "Will Hammond",
           "Sam Leavitt", "Trinidad Chambliss", "Marcel Reed", "John Mateer",
           "Bear Bachmeier", "Devon Dampier", "Avery Johnson", "Keelon Russell",
           "Kevin Jennings", "Bryce Underwood", "Byrum Brown"]
NON_QB = ["Jeremiah Smith", "Malachi Toney", "Ryan Wingo", "Trent Mosley",
          "Jadan Baugh", "Koby Howard"]
K_PRIOR = 150.0
PRIOR_DEFAULT = 0.35


def season_sim():
    """{team: dict(rank, fpi, proj, p10, p90, pbowl, p10w)} from the
    national block of the workbook's Season Sim sheet."""
    from openpyxl import load_workbook
    ws = load_workbook(WORKBOOK, read_only=True, data_only=True)["Season Sim"]
    out = {}
    for r in ws.iter_rows(min_row=5, values_only=True):
        if not r or not isinstance(r[0], (int, float)):
            break
        out[r[1]] = dict(rank=int(r[0]), fpi=r[3], games=r[4], proj=r[5],
                         p10=r[6], p90=r[7], pbowl=r[8], p10w=r[9])
    return out


def upset_board(week):
    """This week's Upset Board rows + the scorecard, straight from the
    workbook tab (built by build_conference_book from alerts_log.json)."""
    from openpyxl import load_workbook
    ws = load_workbook(WORKBOOK, read_only=True, data_only=True)["Upset Board"]
    rows, score, hdr = [], [], None
    for r in ws.iter_rows(min_row=1, values_only=True):
        if hdr is None:
            if r and r[0] == "Wk":
                hdr = r
            continue
        if r[0] is None and not (len(r) > 15 and r[15]):
            continue
        if isinstance(r[0], (int, float)) and int(r[0]) == week:
            rows.append(dict(wk=int(r[0]), date=r[1], matchup=r[2], alert_line=r[3],
                             now=r[4], clv=r[5], ou=str(r[6]) if r[6] is not None else "",
                             margin_home=r[7], edge=r[8], tier=r[9], dog_ml=r[10],
                             side=r[11], final=r[12], ats=r[13]))
        if len(r) > 16 and r[15] and r[15] != "Scorecard":
            score.append((str(r[15]), r[16] if r[16] is not None else (r[17] if len(r) > 17 else None)))
    order = {"🔴": 0, "🟡": 1}
    rows.sort(key=lambda x: (order.get(x["tier"], 2), -abs(x["edge"] or 0)))
    return dict(rows=rows, scorecard=score)


def p_at_least(bar, proj, p10, p90):
    """P(wins >= bar) with wins ~ Normal(proj, sd from the 10-90 spread)."""
    sd = max((p90 - p10) / 2.563, 0.9)
    z = (bar - 0.5 - proj) / sd
    return 0.5 * math.erfc(z / math.sqrt(2))


def hot_seat(sim, ratings, results):
    rows = []
    for team, (coach, cbs) in CBS.items():
        s = sim.get(team)
        if not s:
            continue
        rating = cbs if cbs is not None else EST[team]
        bar = BARS[team]
        p_bar = p_at_least(bar, s["proj"], s["p10"], s["p90"])
        score = 0.6 * rating / 5 + 0.4 * (1 - p_bar)
        r = ratings.get(normalize_name(team), {})
        rows.append(dict(team=team, coach=coach, cbs=rating, cbs_est=cbs is None,
                         tenure=TENURE.get(team, ""), bar=bar, p_bar=round(p_bar, 3),
                         proj=s["proj"], p10=s["p10"], p90=s["p90"],
                         pbowl=round(s["pbowl"], 3), machine_rank=s["rank"],
                         rating=r.get("cur"), delta=r.get("delta"), gp=r.get("gp"),
                         results=results.get(team, []), score=round(100 * score, 1)))
    rows.sort(key=lambda x: -x["score"])
    return rows


def _ppa(year, position, threshold, refresh):
    return cfbd.get("/ppa/players/season",
                    {"year": year, "position": position, "threshold": threshold},
                    refresh)


def heisman(sim, refresh):
    cur = {x["name"]: x for x in _ppa(2026, "QB", 15, refresh)}
    prior = {x["name"]: x for x in _ppa(2025, "QB", 100, False)}
    rows = []
    for name in QB_POOL:
        c = cur.get(name)
        if not c:
            continue
        avg26, tot26 = c["averagePPA"]["all"], c["totalPPA"]["all"]
        n26 = tot26 / avg26 if avg26 else 0
        p = prior.get(name)
        avg25 = p["averagePPA"]["all"] if p else None
        blend = (n26 * avg26 + K_PRIOR * (avg25 if avg25 is not None else PRIOR_DEFAULT)) / (n26 + K_PRIOR)
        s = sim.get(c["team"], {})
        p10w = s.get("p10w", 0.0) or 0.0
        tf = 0.5 + 0.5 * p10w
        ml = MARKET.get(name)
        rows.append(dict(name=name, team=c["team"], plays26=round(n26),
                         ppa26=round(avg26, 3), tot26=round(tot26, 1),
                         ppa25=round(avg25, 3) if avg25 is not None else None,
                         blend=round(blend, 3), p10w=round(p10w, 2),
                         team_factor=round(tf, 3), index=round(100 * tf * blend, 1),
                         market=ml, market_p=round(100 / (100 + ml) * 100, 1) if ml else None))
    rows.sort(key=lambda x: -x["index"])
    # non-QB watch (own scale): 2026 PPA per play + 2025 prior where it exists
    wr = {x["name"]: x for x in _ppa(2026, "WR", 5, refresh)}
    rb = {x["name"]: x for x in _ppa(2026, "RB", 5, refresh)}
    wr25 = {x["name"]: x for x in _ppa(2025, "WR", 40, False)}
    non = []
    for name in NON_QB:
        c = wr.get(name) or rb.get(name)
        if not c:
            continue
        p = wr25.get(name)
        non.append(dict(name=name, team=c["team"], pos=c["position"],
                        ppa26=round(c["averagePPA"]["all"], 2),
                        tot26=round(c["totalPPA"]["all"], 1),
                        ppa25=round(p["averagePPA"]["all"], 2) if p else None,
                        p10w=round(sim.get(c["team"], {}).get("p10w", 0) or 0, 2),
                        market=MARKET.get(name)))
    return rows, non


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, default=2)
    ap.add_argument("--refresh", action="store_true", help="re-pull 2026 PPA")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sim = season_sim()
    rt = json.load(open(RATINGS, encoding="utf-8"))
    ratings = {x["team"]: x for x in rt["teams"]}
    results = {}
    for g in cfbd.get("/games", {"year": 2026, "seasonType": "regular"}, False):
        if g.get("homePoints") is None:
            continue
        for me, opp, mp, op, ha in ((g["homeTeam"], g["awayTeam"], g["homePoints"], g["awayPoints"], "vs"),
                                    (g["awayTeam"], g["homeTeam"], g["awayPoints"], g["homePoints"], "at")):
            results.setdefault(me, []).append(f"{'W' if mp > op else 'L'} {mp}-{op} {ha} {opp}")
    hs = hot_seat(sim, ratings, results)
    hb, non = heisman(sim, a.refresh)
    ub = upset_board(a.week)
    out = dict(week=a.week, generated=dt.datetime.now().isoformat(timespec="seconds"),
               ratings_as_of=rt.get("as_of"), games_used=rt.get("games_used"),
               cbs_date=CBS_DATE, market_date=MARKET_DATE,
               hot_seat=hs, heisman=hb, heisman_non_qb=non, upset_board=ub)
    path = HERE / f"boards_week{a.week}.json"
    json.dump(out, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"HOT SEAT (CBS {CBS_DATE} x machine, {rt.get('games_used')} rated games)")
    for i, r in enumerate(hs[:14], 1):
        est = "*" if r["cbs_est"] else ""
        print(f"{i:>2} {r['coach']:<18}{r['team']:<18} CBS {r['cbs']}{est}  bar {r['bar']}  "
              f"P(bar) {r['p_bar']:.2f}  proj {r['proj']} ({r['p10']}-{r['p90']})  "
              f"rating {r['rating']} ({r['delta']:+})  score {r['score']}  | {'; '.join(r['results'])}")
    print(f"\nHEISMAN BOARD (market DK {MARKET_DATE})")
    for i, r in enumerate(hb[:12], 1):
        print(f"{i:>2} {r['name']:<20}{r['team']:<14} 2026 {r['ppa26']:.3f} on {r['plays26']} plays  "
              f"prior {r['ppa25']}  blend {r['blend']:.3f}  P(10+) {r['p10w']:.2f}  "
              f"index {r['index']}  market {('+' + str(r['market'])) if r['market'] else '—'}")
    print("non-QB:", [(x['name'], x['ppa26'], x['tot26'], x['ppa25'], x['market']) for x in non])
    print(f"\nUPSET BOARD week {a.week}: {len(ub['rows'])} alerts")
    for r in ub["rows"]:
        print(f"  {r['tier']} {r['matchup']:<42} alert {r['alert_line']:<26} now {r['now']:<24} "
              f"CLV {r['clv']}  edge {r['edge']}  side {r['side']}  ML {r['dog_ml']}  O/U {r['ou']}")
    print("  scorecard:", ub["scorecard"])
    print("wrote", path.name)


if __name__ == "__main__":
    main()
