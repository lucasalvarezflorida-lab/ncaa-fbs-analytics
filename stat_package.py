"""Per-team stat package for the episode notes: every key needs its numbers.
From CFBD play-by-play (/plays per team per week) - explosives per dropback
(20+/30+), deep-throw rate, yards per attempt vs per completion, third-and-long
and third-and-short, stuffs, sacks, red zone - for the offense AND the defense,
plus results and the season stat leaders. RUSHING TOTALS (attempts / yards /
per carry) are the OFFICIAL BOX SCORE (NCAA convention: sacks and fumbled
snaps count as rushes) - Lucas 9/21; the play-by-play run count (sacks
excluded) is kept only for the stuff rate and the 10+ rate.

Run: python stat_package.py --week 4 --teams "Texas,Tennessee,..." [--refresh]
Writes stat_package_week{N}.json and prints a readable summary. Internal."""
import argparse, collections, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "fpi-decomposition"))
from refresh_all import load_env_key  # noqa: E402
import cfbd_client as cfbd  # noqa: E402

PASS = ("Pass", "Sack", "Interception")
SKIP = ("Kickoff", "Punt", "Field Goal", "Timeout", "End", "Penalty", "Extra Point", "Two Point")


def _is_drop(p):
    return any(t in p["playType"] for t in PASS)


def _is_rush(p):
    return "Rush" in p["playType"] or p["playType"] == "Fumble Recovery (Opponent)" and "rush" in (p.get("playText") or "").lower()


def side_stats(plays):
    """plays = one unit's scrimmage plays (as the offense)."""
    drop = [p for p in plays if _is_drop(p)]
    rush = [p for p in plays if _is_rush(p) and not _is_drop(p)]
    yd = lambda p: p.get("yardsGained") or 0
    sacks = [p for p in drop if "Sack" in p["playType"]]
    atts = [p for p in drop if "Sack" not in p["playType"]]
    comps = [p for p in atts if "Reception" in p["playType"] or "Passing Touchdown" in p["playType"]
             or ("complete" in (p.get("playText") or "").lower() and "incomplete" not in (p.get("playText") or "").lower())]
    deep = [p for p in atts if " deep " in (p.get("playText") or "").lower()]
    deep_c = [p for p in deep if p in comps]
    ints = [p for p in drop if "Interception" in p["playType"]]
    t3 = [p for p in plays if p.get("down") == 3 and (p in drop or p in rush)]
    conv = lambda ps: sum(1 for p in ps if yd(p) >= (p.get("distance") or 99) or "Touchdown" in p["playType"])
    t3l = [p for p in t3 if (p.get("distance") or 0) >= 6]
    t3s = [p for p in t3 if (p.get("distance") or 0) <= 2]
    rz_drives = {p["driveId"] for p in plays if (p.get("yardsToGoal") or 100) <= 20}
    rz_td = {p["driveId"] for p in plays if p["driveId"] in rz_drives and "Touchdown" in p["playType"]
             and "Return" not in p["playType"] and "Interception" not in p["playType"] and "Fumble" not in p["playType"]}
    n = lambda x: len(x)
    return dict(
        plays=n(drop) + n(rush), dropbacks=n(drop), sacks=n(sacks), att=n(atts), comp=n(comps),
        # passing yards = COMPLETIONS only: CFBD books an interception's return
        # yardage on the pass play, which inflated per-attempt (found 9/21)
        pass_yds=sum(yd(p) for p in comps), ypa=round(sum(yd(p) for p in comps) / max(n(atts), 1), 1),
        ypc=round(sum(yd(p) for p in comps) / max(n(comps), 1), 1),
        p20=sum(1 for p in drop if yd(p) >= 20), p30=sum(1 for p in drop if yd(p) >= 30),
        deep_att=n(deep), deep_comp=n(deep_c), ints=n(ints),
        rushes=n(rush), rush_yds=sum(yd(p) for p in rush), ypr=round(sum(yd(p) for p in rush) / max(n(rush), 1), 1),
        r10=sum(1 for p in rush if yd(p) >= 10), stuffs=sum(1 for p in rush if yd(p) <= 0),
        t3=f"{conv(t3)}/{n(t3)}", t3_long=f"{conv(t3l)}/{n(t3l)}", t3_short=f"{conv(t3s)}/{n(t3s)}",
        rz=f"{n(rz_td)}/{n(rz_drives)}",
        ppa=round(sum(p["ppa"] for p in plays if p.get("ppa") is not None and (p in drop or p in rush))
                  / max(sum(1 for p in plays if p.get("ppa") is not None and (p in drop or p in rush)), 1), 3))


def _sum(parts):
    out = collections.Counter()
    for s in parts:
        for k, v in s.items():
            if isinstance(v, (int, float)) and k not in ("ypa", "ypc", "ypr", "ppa"):
                out[k] += v
            elif isinstance(v, str) and "/" in v:
                a, b = v.split("/"); out[k + "_n"] += int(a); out[k + "_d"] += int(b)
            elif k == "box_rush" and v:
                out["box_att"] += v["att"]; out["box_yds"] += v["yds"]
    o = dict(out)
    o["box_ypc"] = round(o.get("box_yds", 0) / max(o.get("box_att", 0), 1), 1)
    o["ypa"] = round(o.get("pass_yds", 0) / max(o.get("att", 0), 1), 1)
    o["ypr"] = round(o.get("rush_yds", 0) / max(o.get("rushes", 0), 1), 1)
    o["sack_rate"] = round(100 * o.get("sacks", 0) / max(o.get("dropbacks", 0), 1), 1)
    o["p20_rate"] = round(100 * o.get("p20", 0) / max(o.get("dropbacks", 0), 1), 1)
    o["r10_rate"] = round(100 * o.get("r10", 0) / max(o.get("rushes", 0), 1), 1)
    o["stuff_rate"] = round(100 * o.get("stuffs", 0) / max(o.get("rushes", 0), 1), 1)
    o["deep_rate"] = round(100 * o.get("deep_att", 0) / max(o.get("att", 0), 1), 1)
    for k in ("t3", "t3_long", "t3_short", "rz"):
        o[k] = f"{o.pop(k + '_n', 0)}/{o.pop(k + '_d', 0)}"
    return o


def box_rushing(team, week, game_id, refresh):
    """Official box-score rushing (NCAA convention: sacks and fumbled snaps count
    as rushes) for the team and its opponent in game_id -> (own, opp), each
    dict(att, yds, ypc) or None. Matched by game id: a team can have two games
    in one CFBD 'week' (USC's Week 0 game is week 1)."""
    own = opp = None
    for g in cfbd.get("/games/teams", {"year": 2026, "week": week, "seasonType": "regular"}, refresh):
        if g.get("id") != game_id:
            continue
        for t in g["teams"]:
            st = {x["category"]: x["stat"] for x in t["stats"]}
            if st.get("rushingAttempts") is None:
                continue
            att, yds = int(st["rushingAttempts"]), int(st["rushingYards"])
            d = dict(att=att, yds=yds, ypc=round(yds / max(att, 1), 1))
            if t.get("team") == team:
                own = d
            else:
                opp = d
    return own, opp


def package(team, through_week, refresh):
    games = [g for g in cfbd.get("/games", {"year": 2026, "seasonType": "regular"}, False)
             if team in (g["homeTeam"], g["awayTeam"]) and g.get("completed") and g["week"] < through_week]
    out = dict(team=team, games=[], offense=None, defense=None)
    offs, defs = [], []
    for g in sorted(games, key=lambda g: g["startDate"]):
        home = g["homeTeam"] == team
        opp = g["awayTeam"] if home else g["homeTeam"]
        us, them = (g["homePoints"], g["awayPoints"]) if home else (g["awayPoints"], g["homePoints"])
        pl = cfbd.get("/plays", {"year": 2026, "week": g["week"], "seasonType": "regular", "team": team}, refresh)
        pl = [p for p in pl if p.get("gameId") == g["id"] and not any(s in p["playType"] for s in SKIP)]
        o = side_stats([p for p in pl if p["offense"] == team])
        d = side_stats([p for p in pl if p["defense"] == team])
        bo, bd = box_rushing(team, g["week"], g["id"], refresh)      # BOX-SCORE rushing = the headline numbers (Lucas 9/21)
        o["box_rush"], d["box_rush"] = bo, bd
        offs.append(o); defs.append(d)
        cls = g["awayClassification"] if home else g["homeClassification"]
        out["games"].append(dict(week=g["week"], opp=opp, site="vs" if home else "at", opp_class=cls,
                                 result=f"{'W' if us > them else 'L'} {us}-{them}", offense=o, defense=d))
    out["offense"], out["defense"] = _sum(offs), _sum(defs)
    fbs = [i for i, g in enumerate(out["games"]) if g["opp_class"] == "fbs"]
    out["offense_vs_fbs"], out["defense_vs_fbs"] = _sum([offs[i] for i in fbs]), _sum([defs[i] for i in fbs])
    lead = collections.defaultdict(dict)
    for cat in ("passing", "rushing", "receiving", "defensive"):
        for r in cfbd.get("/stats/player/season", {"year": 2026, "team": team, "category": cat}, refresh):
            lead[(cat, r["player"])][r["statType"]] = float(r["stat"])
    def top(cat, key, n=3):
        rows = [(nm, st) for (c, nm), st in lead.items() if c == cat and nm.strip() != "Team"]
        return [(nm, {k: v for k, v in st.items()}) for nm, st in sorted(rows, key=lambda kv: -kv[1].get(key, 0))[:n]]
    out["leaders"] = dict(passing=top("passing", "ATT", 2), rushing=top("rushing", "YDS"), receiving=top("receiving", "YDS"),
                          sacks=top("defensive", "SACKS"), tfl=top("defensive", "TFL"))
    return out


def show(pk):
    print(f"\n{'=' * 8} {pk['team']} {'=' * 8}")
    for g in pk["games"]:
        o, d = g["offense"], g["defense"]
        print(f"  wk{g['week']} {g['site']} {g['opp']} ({g['opp_class']}) {g['result']} | OFF ppa {o['ppa']:+.2f} pass {o['comp']}/{o['att']} {o['ypa']} ypa 20+ {o['p20']} sk {o['sacks']} rush(box) {(o.get('box_rush') or {}).get('att')}-{(o.get('box_rush') or {}).get('yds')} 3rd {o['t3']} (6+ {o['t3_long']}) rz {o['rz']} | DEF ppa {d['ppa']:+.2f} {d['ypa']} ypa 20+ {d['p20']} sk {d['sacks']} rush(box) {(d.get('box_rush') or {}).get('att')}-{(d.get('box_rush') or {}).get('yds')} stuffs {d['stuffs']} 3rd {d['t3']} (6+ {d['t3_long']}) rz {d['rz']}")
    for lab in ("offense", "defense", "offense_vs_fbs", "defense_vs_fbs"):
        s = pk[lab]
        print(f"  {lab.upper():15s} dropbacks {s.get('dropbacks', 0)} ypa {s['ypa']} ypc {round(s.get('pass_yds', 0) / max(s.get('comp', 0), 1), 1)} 20+ {s.get('p20', 0)} ({s['p20_rate']}%) 30+ {s.get('p30', 0)} deep {s.get('deep_comp', 0)}/{s.get('deep_att', 0)} ({s['deep_rate']}% of att) sacks {s.get('sacks', 0)} ({s['sack_rate']}%) INT {s.get('ints', 0)} | RUSH (box) {s.get('box_att', 0)}-{s.get('box_yds', 0)} ({s['box_ypc']}) | pbp runs {s.get('rushes', 0)}: 10+ {s.get('r10', 0)} ({s['r10_rate']}%) stuffs {s.get('stuffs', 0)} ({s['stuff_rate']}%) | 3rd {s['t3']} 3rd&6+ {s['t3_long']} 3rd&1-2 {s['t3_short']} | RZ TD {s['rz']}")
    L = pk["leaders"]
    for nm, st in L["passing"]:
        print(f"  QB {nm}: {st.get('COMPLETIONS', 0):.0f}/{st.get('ATT', 0):.0f} {st.get('YDS', 0):.0f} yds {st.get('TD', 0):.0f} TD {st.get('INT', 0):.0f} INT {st.get('YPA', 0)} ypa")
    print("  RUSH", [(nm, f"{st.get('CAR', 0):.0f}-{st.get('YDS', 0):.0f}, {st.get('TD', 0):.0f} TD") for nm, st in L["rushing"]])
    print("  REC ", [(nm, f"{st.get('REC', 0):.0f}-{st.get('YDS', 0):.0f}, {st.get('TD', 0):.0f} TD") for nm, st in L["receiving"]])
    print("  SACK", [(nm, st.get("SACKS", 0)) for nm, st in L["sacks"]], "TFL", [(nm, st.get("TFL", 0)) for nm, st in L["tfl"]])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True, help="the week being previewed (uses games before it)")
    ap.add_argument("--teams", required=True)
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    load_env_key()
    pks = [package(t.strip(), a.week, a.refresh) for t in a.teams.split(",")]
    json.dump(pks, open(f"stat_package_week{a.week}.json", "w", encoding="utf-8"), indent=1)
    for pk in pks:
        show(pk)
