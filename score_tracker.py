"""Side tracker (INTERNAL): who was closer to EACH TEAM'S final score - the
machine's score call or the man's - game by game and on the season.

Ledger = score_tracker.json (append a week after grading):
  {"week": 3, "game": "Houston at Texas Tech", "away": "Houston", "home": "Texas Tech",
   "machine": [20, 33], "man": [24, 35], "final": [26, 28]}      # [away, home]
`final` can be null - it is filled from the CFBD games cache on the next run.
Man's calls come off Corey's score slides (each number under that team's logo).

  python score_tracker.py            -> prints the tracker, writes score_tracker.md"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER = os.path.join(HERE, "score_tracker.json")
CACHE = os.path.join(HERE, "fpi-decomposition", "data", "games_seasonType-regular_year-2026.json")


def load():
    rows = json.load(open(LEDGER, encoding="utf-8"))
    finals = {}
    if os.path.exists(CACHE):
        for g in json.load(open(CACHE, encoding="utf-8")):
            if g.get("homePoints") is not None and g.get("awayPoints") is not None:
                finals[(g["awayTeam"], g["homeTeam"])] = [g["awayPoints"], g["homePoints"]]
    changed = False
    for r in rows:
        if not r.get("final") and (r["away"], r["home"]) in finals:
            r["final"] = finals[(r["away"], r["home"])]; changed = True
    if changed:
        json.dump(rows, open(LEDGER, "w", encoding="utf-8"), indent=1)
    return rows


def grade(rows):
    out, tally = [], dict(machine=0, man=0, tie=0, m_pts=0, c_pts=0, games_m=0, games_c=0, games_t=0)
    for r in rows:
        if not r.get("final") or not r.get("man"):
            continue
        gm = gc = 0
        for i, team in enumerate((r["away"], r["home"])):
            em, ec = abs(r["machine"][i] - r["final"][i]), abs(r["man"][i] - r["final"][i])
            who = "machine" if em < ec else "man" if ec < em else "tie"
            tally[who] += 1; tally["m_pts"] += em; tally["c_pts"] += ec
            gm += em; gc += ec
            out.append(dict(week=r["week"], game=r["game"], team=team, final=r["final"][i],
                            machine=r["machine"][i], man=r["man"][i], m_off=em, c_off=ec, closer=who))
        tally["games_m" if gm < gc else "games_c" if gc < gm else "games_t"] += 1
    return out, tally


def render(rows):
    out, t = grade(rows)
    L = ["# Score tracker — who was closer to each team's final score (INTERNAL)", "",
         f"Season: **man closer on {t['man']} teams · machine on {t['machine']} · {t['tie']} tie** — "
         f"points off, all teams: man {t['c_pts']} · machine {t['m_pts']} — "
         f"games (both teams added up): man {t['games_c']} · machine {t['games_m']} · {t['games_t']} tie", "",
         "The machine has no totals model: its score is its margin laid over the market total, so its",
         "team-score misses are mostly the market's total miss. Corey's totals are his own.", "",
         "| Wk | Game | Team | Final | Machine | off | Man | off | Closer |", "|---|---|---|---|---|---|---|---|---|"]
    for o in out:
        L.append(f"| {o['week']} | {o['game']} | {o['team']} | {o['final']} | {o['machine']} | {o['m_off']} | {o['man']} | {o['c_off']} | {o['closer']} |")
    pend = [r for r in rows if not r.get("final") or not r.get("man")]
    if pend:
        L += ["", "Pending (no final yet, or no man call recorded): " + " · ".join(f"Wk {r['week']} {r['game']}" for r in pend)]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    md = render(load())
    open(os.path.join(HERE, "score_tracker.md"), "w", encoding="utf-8").write(md)
    print(md)
