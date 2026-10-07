"""Two machine-assisted boards for the podcast: the Hot Seat Top 10 and the
Heisman board ("our own favorite"). Writes boards_week{N}.json for
make_episode_deck.py; the notes (.md) carry the reasoning.

HOT SEAT — since 10/4/2026 (Lucas): seat score = 0.4 * (CBS rating / 5) + 0.6 * min(P(gone) / 0.5, 1)
  * P(gone) = hot_seat_study.p_gone_2026: logistic model of "not the coach next season" fit on 2014-25,
    from tenure, last season vs the program's ten-year bar, and this season's record and margin so far.
    Every FBS coach is scored; a coach CBS did not list in August carries CBS_DEFAULT (starred).
    internal/HOT_SEAT_STUDY_2026.md has the backtest. The old rule, kept for the record:
    0.6 * (CBS rating / 5) + 0.4 * (1 - P(hit the bar))
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


# What the SCHOOL owes if it fires him now (2026). Hand-maintained, dated; est=True = computed from reported terms or an
# outlet's estimate, not a reported figure. "—" = undisclosed. Researched Tue Oct 6 2026 (sources in
# internal/dossiers/Replacement_candidates_top3_seats_week6.md and the notes).
BUYOUT_DATE = "2026-10-06"
BUYOUT = {   # team: (slide text, est, note)
    "Clemson": ("$57M", False, "flat 2026 figure; full remaining salary through 2031 from 2027; no offset (CBS 9/20/25)"),
    "Colorado": ("~$25M", True, "75% of remaining salary -> ~$25.5M for 2026 per one outlet (10/5/26); the 75% term is from his 2022 deal, not confirmed in the 2025 extension"),
    "Boston College": ("$8–25M", True, "private school, undisclosed; estimates range $8–10M (EssentiallySports) to ~$25M (PFN, $5M x 5 yrs assumed)"),
    "South Carolina": ("~$21M", True, "65% of remaining (2020 terms) on the 2025 extension, $8.15M/yr through 2030; CBS: the extension raised it by nearly $20M"),
    "Rutgers": ("$18.5M", False, "76.85% of remaining salary through 2029 (ClutchPoints 9/4/26)"),
    "Maryland": ("$9.2M", False, "if fired in 2026, USA TODAY via Fox (9/26/26); $6.4M 2026 / $6.7M 2027 / $7M 2028"),
    "Wyoming": ("~$2M", True, "70–80% of remaining; $1.1M 2026 (less a $125K rev-share cut), $1.25M 2027–28 (FootballScoop)"),
    "Middle Tennessee": ("~$1M", True, "50% of remaining; $925K base through Dec 2028"),
    "UL Monroe": ("—", False, "undisclosed; base reported ~$725–750K, deal through 2029 (unverified)"),
    "UTEP": ("—", False, "undisclosed; 2025 salary $801K"),
    "Akron": ("—", False, "undisclosed; extended through 2027"),
    "Western Kentucky": ("—", False, "undisclosed; extended through 2028"),
    "Eastern Michigan": ("—", False, "undisclosed"),
}

# Heisman market (DraftKings via Covers, Sun Sep 13 2026) — refresh weekly
MARKET_DATE = "2026-10-04"
MARKET = {   # DraftKings via SI's Week 6 tracker, Sun 10/4 (post-Week 5); players not on that list carry no market number this week
    "Jeremiah Smith": 115, "Darian Mensah": 460, "Keelon Russell": 750, "C.J. Carr": 800,
    "Trinidad Chambliss": 1600, "Gunner Stockton": 2900, "Julian Sayin": 3100,
    "Arch Manning": 3200, "Kamario Taylor": 3200, "Malachi Toney": 3500,
}   # Bettors Insider had Smith +110 on 10/5 (+260 the week before) - the 10/4 table is used for one consistent snapshot
QB_POOL = ["Julian Sayin", "Darian Mensah", "C.J. Carr", "Josh Hoover",
           "Arch Manning", "Dante Moore", "Jayden Maiava", "Will Hammond",
           "Sam Leavitt", "Trinidad Chambliss", "Marcel Reed", "John Mateer",
           "Bear Bachmeier", "Devon Dampier", "Avery Johnson", "Keelon Russell",
           "Kevin Jennings", "Bryce Underwood", "Byrum Brown", "Kamario Taylor",
           "LaNorris Sellers", "Lanorris Sellers", "Lincoln Kienholz", "Gunner Stockton"]
NON_QB = ["Jeremiah Smith", "Malachi Toney", "Ryan Wingo", "Trent Mosley",
          "Jadan Baugh", "Koby Howard"]
K_PRIOR = 150.0
PRIOR_DEFAULT = 0.35
# ALL-POSITIONS board (Lucas 9/29: "who are our favorites regardless of position"):
# the common unit is POINTS ADDED PER GAME = shrunk per-play PPA x plays / games,
# times the same team factor. A receiver's per-touch PPA runs ~1.0 vs a passer's
# ~0.5, so per play is not comparable across positions; per game is what the
# voters see. Non-QB prior weight is smaller (a receiver sees ~12 plays a game).
K_PRIOR_NONQB = 40.0
PRIOR_DEFAULT_NONQB = 0.50
NONQB_AUTO = 12          # plus the top-N WR and RB by 2026 total PPA, so nobody is missed


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


CBS_W, P_FULL, CBS_DEFAULT = 0.4, 0.5, 1.5     # CBS weight; P(gone) that maxes the machine half; rating for a coach CBS did not list


def hot_seat(sim, ratings, results, week):
    from hot_seat_study import p_gone_2026
    model = p_gone_2026(week - 1)
    rows = []
    for team, m in model.items():
        s = sim.get(team)
        if not s:
            continue
        coach, cbs = CBS.get(team, (m["coach"], None))
        rating = cbs if cbs is not None else EST.get(team, CBS_DEFAULT)
        bar = BARS.get(team)
        p_bar = p_at_least(bar, s["proj"], s["p10"], s["p90"]) if bar else None
        score = CBS_W * rating / 5 + (1 - CBS_W) * min(m["p_gone"] / P_FULL, 1.0)
        r = ratings.get(normalize_name(team), {})
        rows.append(dict(team=team, coach=coach, cbs=rating, cbs_est=cbs is None,
                         tenure=TENURE.get(team, f"yr {m['tenure']}"), bar=bar, p_bar=round(p_bar, 3) if p_bar is not None else None,
                         p_gone=round(m["p_gone"], 3), record=m["rec"].replace("-", "–"),
                         buyout=BUYOUT.get(team, ("—", False, ""))[0], buyout_est=BUYOUT.get(team, ("—", False, ""))[1],
                         buyout_note=BUYOUT.get(team, ("—", False, ""))[2],
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


def heisman(sim, refresh, games=None):
    games = games or {}
    cur = {x["name"]: x for x in _ppa(2026, "QB", 15, refresh)}
    prior = {x["name"]: x for x in _ppa(2025, "QB", 100, False)}
    rows = []
    all_rows = []

    def _all_row(name, c, pos, avg25, k_prior, prior_default):
        avg26, tot26 = c["averagePPA"]["all"], c["totalPPA"]["all"]
        n26 = tot26 / avg26 if avg26 else 0
        blend = (n26 * avg26 + k_prior * (avg25 if avg25 is not None else prior_default)) / (n26 + k_prior)
        s = sim.get(c["team"], {})
        p10w = s.get("p10w", 0.0) or 0.0
        tf = 0.5 + 0.5 * p10w
        g = max(games.get(c["team"], 0), 1)
        ppg = blend * n26 / g
        ml = MARKET.get(name)
        return dict(name=name, team=c["team"], pos=pos, plays26=round(n26), games=g,
                    ppa26=round(avg26, 3), tot26=round(tot26, 1),
                    ppa25=round(avg25, 3) if avg25 is not None else None,
                    blend=round(blend, 3), ppg=round(ppg, 1), p10w=round(p10w, 2),
                    team_factor=round(tf, 3), index=round(tf * ppg, 1),
                    market=ml, market_p=round(100 / (100 + ml) * 100, 1) if ml else None)

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
        ar = _all_row(name, c, "QB", avg25, K_PRIOR, PRIOR_DEFAULT)
        ar["qb_index"] = rows[-1]["index"]
        all_rows.append(ar)
    rows.sort(key=lambda x: -x["index"])
    # non-QB watch (own scale): 2026 PPA per play + 2025 prior where it exists
    wr = {x["name"]: x for x in _ppa(2026, "WR", 5, refresh)}
    rb = {x["name"]: x for x in _ppa(2026, "RB", 5, refresh)}
    wr25 = {x["name"]: x for x in _ppa(2025, "WR", 40, False)}
    rb25 = {x["name"]: x for x in _ppa(2025, "RB", 40, False)}
    non = []
    for name in NON_QB:
        c = wr.get(name) or rb.get(name)
        if not c:
            continue
        p = wr25.get(name) or rb25.get(name)
        non.append(dict(name=name, team=c["team"], pos=c["position"],
                        ppa26=round(c["averagePPA"]["all"], 2),
                        tot26=round(c["totalPPA"]["all"], 1),
                        ppa25=round(p["averagePPA"]["all"], 2) if p else None,
                        p10w=round(sim.get(c["team"], {}).get("p10w", 0) or 0, 2),
                        market=MARKET.get(name)))
    # all-positions board: the hand list plus the top-N WR / RB by 2026 total PPA
    pool = list(NON_QB)
    for grp in (wr, rb):
        for x in sorted(grp.values(), key=lambda v: -(v["totalPPA"]["all"] or 0))[:NONQB_AUTO]:
            if x["name"] not in pool:
                pool.append(x["name"])
    for name in pool:
        c = wr.get(name) or rb.get(name)
        if not c or not c["team"]:
            continue
        p = wr25.get(name) or rb25.get(name)
        all_rows.append(_all_row(name, c, c["position"], p["averagePPA"]["all"] if p else None,
                                 K_PRIOR_NONQB, PRIOR_DEFAULT_NONQB))
    all_rows.sort(key=lambda x: -x["index"])
    return rows, non, all_rows


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
    hs = hot_seat(sim, ratings, results, a.week)
    games = {t: len(v) for t, v in results.items()}
    hb, non, hall = heisman(sim, a.refresh, games)
    ub = upset_board(a.week)
    out = dict(week=a.week, generated=dt.datetime.now().isoformat(timespec="seconds"),
               ratings_as_of=rt.get("as_of"), games_used=rt.get("games_used"),
               cbs_date=CBS_DATE, market_date=MARKET_DATE,
               hot_seat=hs, heisman=hb, heisman_non_qb=non, heisman_all=hall, upset_board=ub)
    path = HERE / f"boards_week{a.week}.json"
    json.dump(out, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    try:
        from refresh_all import wait_for_unlock
        wait_for_unlock(HERE / "NCAA_FBS_Teams.xlsm", timeout=60)
        write_hot_seat_sheet(HERE / "NCAA_FBS_Teams.xlsm", a.week, hs)
    except Exception as e:       # the workbook may be open in Excel; the board json is already written
        print("Hot Seat sheet not written:", e)
    print(f"HOT SEAT (40% CBS {CBS_DATE} + 60% P(gone) model, {len(hs)} coaches)")
    for i, r in enumerate(hs[:14], 1):
        est = "*" if r["cbs_est"] else ""
        print(f"{i:>2} {r['coach']:<18}{r['team']:<18} CBS {r['cbs']}{est}  {r['record']}  "
              f"P(gone) {r['p_gone']:.2f}  buyout {r['buyout']}{'*' if r['buyout_est'] else ''}  proj {r['proj']} ({r['p10']}-{r['p90']})  "
              f"rating {r['rating']} ({r['delta']:+})  score {r['score']}  | {'; '.join(r['results'])}")
    print(f"\nHEISMAN — ALL POSITIONS (points added per game x team factor; market DK {MARKET_DATE})")
    for i, r in enumerate(hall[:12], 1):
        print(f"{i:2d} {r['name']:<20} {r['pos']:<3}{r['team']:<18} {r['ppa26']:.3f} on {r['plays26']} plays in {r['games']} g"
              f"  blend {r['blend']:.3f}  pts/g {r['ppg']:5.1f}  tf {r['team_factor']:.2f}  index {r['index']:5.1f}"
              f"  market {('+' + str(r['market'])) if r['market'] else '—'}")
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


def write_hot_seat_sheet(book, week, rows=None):
    """'Hot Seat' sheet in the workbook: every FBS coach on the on-air rule (Lucas 10/6: the full report lives in Excel,
    not on a slide or in OneNote). Same columns as the board plus the buyout note and the season's results."""
    from pathlib import Path
    from openpyxl import load_workbook
    from openpyxl.styles import Font, PatternFill
    book = Path(book)
    if rows is None:
        rows = json.loads((HERE / f"boards_week{week}.json").read_text(encoding="utf-8"))["hot_seat"]
    wb = load_workbook(book, keep_vba=True)
    if "Hot Seat" in wb.sheetnames:
        del wb["Hot Seat"]
    ws = wb.create_sheet("Hot Seat")
    ws["A1"] = f"HOT SEAT - every FBS coach - before week {week} - score = {CBS_W:.0%} CBS ({CBS_DATE}) + {1 - CBS_W:.0%} P(gone) (full marks at {P_FULL:.0%})"
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"] = ("P(gone) = the model's odds he is not the school's coach next season (fired, retired or stepped down), fit on 2014-25: "
                "losses and scoring margin so far, tenure, last season vs the program's ten-year standard, preseason rank. CBS* = not on CBS's August list "
                f"(carries {CBS_DEFAULT}). Buyout = what the school owes to fire him now; * = estimated from reported terms, blank = undisclosed "
                f"(researched {BUYOUT_DATE}). Backtest: internal/HOT_SEAT_STUDY_2026.md.")
    hdr = ["Rank", "Coach", "School", "Tenure", "Record", "CBS", "CBS est.", "P(gone)", "Buyout", "Buyout est.", "Buyout note",
           "Machine rating", "Rating vs July", "Machine rank", "Proj. wins", "Proj. 10th-90th", "P(bowl)", "Score", "Last result", "Season results"]
    for j, h in enumerate(hdr, 1):
        c = ws.cell(row=4, column=j, value=h); c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F3864")
    for i, r in enumerate(rows, 5):
        vals = [i - 4, r["coach"], r["team"], r.get("tenure", ""), r.get("record", ""), r["cbs"], "*" if r.get("cbs_est") else "",
                r.get("p_gone"), (r.get("buyout") or "").replace("—", ""), "*" if r.get("buyout_est") else "", r.get("buyout_note", ""),
                r.get("rating"), r.get("delta"), r.get("machine_rank"), r.get("proj"), f"{r.get('p10')}-{r.get('p90')}", r.get("pbowl"),
                r["score"], (r.get("results") or [""])[-1], "; ".join(r.get("results") or [])]
        for j, v in enumerate(vals, 1):
            ws.cell(row=i, column=j, value=v)
        ws.cell(row=i, column=8).number_format = "0%"; ws.cell(row=i, column=17).number_format = "0%"
    ws.freeze_panes = "D5"
    ws.auto_filter.ref = f"A4:T{4 + len(rows)}"
    for col, w in zip("ABCDEFGHIJKLMNOPQRST", (6, 20, 20, 18, 8, 6, 7, 8, 10, 9, 60, 10, 10, 9, 9, 12, 8, 7, 30, 90)):
        ws.column_dimensions[col].width = w
    wb.save(book)
    print(f"Hot Seat sheet written: {len(rows)} coaches, before week {week}")


if __name__ == "__main__":
    main()
