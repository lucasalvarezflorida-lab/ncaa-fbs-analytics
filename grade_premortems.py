"""Grade the pre-mortems after the games (Phase 3).

    python grade_premortems.py --week 4            # pull week-4 box scores + plays, grade, write notes/premortems.md
    python grade_premortems.py --week 4 --refresh  # force a fresh CFBD pull
    python grade_premortems.py --table             # just rebuild the season table from what is graded

For each pre-mortem in premortems.json the condition is evaluated on that
game's official box score (/games/teams, matched by game id) or play-by-play
(/plays, the same side_stats() the notes use, so "yards an attempt" is
completions-only and "sacks" are the play-by-play count). Records:
    fired      the condition happened
    pick_lost  the machine's pick lost straight up
    own_line   did the pick cover the MACHINE'S OWN number (no market here)
    verdict    named it     = fired and the pick lost
               survived it  = fired and the pick still won
               missed it    = did not fire and the pick lost (the machine
                              named the wrong reason)
               clean        = did not fire and the pick won
Season table -> notes/premortems.md (public; no market material)."""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "fpi-decomposition"))
from refresh_all import load_env_key  # noqa: E402
import cfbd_client as cfbd  # noqa: E402
from stat_package import SKIP, side_stats  # noqa: E402
from premortems import PM_FILE, load, save  # noqa: E402

OUT_MD = os.path.join(HERE, "notes", "premortems.md")


def box(team, week, game_id, refresh):
    """(own, opp) box rows for the team's game -> dict(category: stat)."""
    own = opp = None
    for g in cfbd.get("/games/teams", {"year": 2026, "week": week, "seasonType": "regular"}, refresh):
        if g.get("id") != game_id:
            continue
        for t in g["teams"]:
            st = {x["category"]: x["stat"] for x in t["stats"]}
            st["points"] = t.get("points")
            if t.get("team") == team:
                own = st
            else:
                opp = st
    return own, opp


def plays(team, week, game_id, refresh):
    pl = cfbd.get("/plays", {"year": 2026, "week": week, "seasonType": "regular", "team": team}, refresh)
    return [p for p in pl if p.get("gameId") == game_id and not any(s in p["playType"] for s in SKIP)]


def observe(cond, week, game_id, refresh):
    """The observed value of the condition's stat for cond['team'] in the game."""
    team, unit, stat = cond["team"], cond["unit"], cond["stat"]
    if cond["source"] == "box":
        own, opp = box(team, week, game_id, refresh)
        row = own if unit == "offense" else opp     # defense = what the opponent's offense did
        if row is None:
            return None
        if stat == "rush_ypc":
            return round(int(row["rushingYards"]) / max(int(row["rushingAttempts"]), 1), 2)
        if stat == "t3_pct":
            n, d = row["thirdDownEff"].split("-")
            return round(100 * int(n) / max(int(d), 1), 1)
        if stat == "ints_thrown":
            return int(row.get("interceptions") or 0)
        if stat == "sacks_taken":
            other = opp if unit == "offense" else own
            return int(float(other.get("sacks") or 0))
        if stat == "turnovers":
            return int(row.get("turnovers") or 0)
        raise ValueError(stat)
    pl = plays(team, week, game_id, refresh)
    s = side_stats([p for p in pl if p[("offense" if unit == "offense" else "defense")] == team])
    if stat == "pass_ypa":
        return s["ypa"]
    if stat == "p20":
        return s["p20"]
    if stat == "sacks_taken":
        return s["sacks"]
    if stat == "stuff_rate":
        return round(100 * s["stuffs"] / max(s["rushes"], 1), 1)
    if stat == "rush_ypc":
        return s["ypr"]
    raise ValueError(stat)


OPS = {">": lambda a, b: a > b, ">=": lambda a, b: a >= b, "<": lambda a, b: a < b, "<=": lambda a, b: a <= b}


def final(game_id):
    for g in cfbd.get("/games", {"year": 2026, "seasonType": "regular"}, False):
        if g["id"] == game_id and g.get("completed") and g.get("homePoints") is not None:
            return g["awayPoints"], g["homePoints"]
    return None


def grade_week(week, refresh):
    pms = load()
    wk = pms.get(str(week), {})
    if not wk:
        sys.exit(f"no week {week} pre-mortems in {os.path.basename(PM_FILE)}")
    load_env_key()
    if refresh:
        cfbd.get("/games", {"year": 2026, "seasonType": "regular"}, True)
    for game, p in wk.items():
        fin = final(p["game_id"])
        if not fin:
            print(f"{game}: no final yet"); continue
        ap_, hp_ = fin
        margin = hp_ - ap_
        pick_home = p["pick"] == p["home"]
        pick_margin = margin if pick_home else -margin
        obs = observe(p["condition"], week, p["game_id"], refresh)
        if obs is None:
            print(f"{game}: box score not available yet"); continue
        fired = bool(OPS[p["condition"]["op"]](obs, p["condition"]["value"]))
        lost = pick_margin < 0
        own = pick_margin - abs(p["machine_margin"])      # + = covered the machine's own number
        verdict = ("named it" if fired and lost else "survived it" if fired else "missed it" if lost else "clean")
        p["result"] = dict(final=[ap_, hp_], observed=obs, fired=fired, pick_lost=lost,
                           own_line=round(own, 1), verdict=verdict)
        print(f"{game:26s} final {ap_}-{hp_}  {p['text']}: observed {obs} -> fired={fired}  pick {'LOST' if lost else 'won'}  -> {verdict}")
    save(pms)
    return pms


def table(pms):
    rows, L = [], []
    for week, wk in sorted(pms.items(), key=lambda kv: int(kv[0])):
        for game, p in wk.items():
            r = p.get("result")
            rows.append((int(week), game, p["pick"], p["text"], r))
    graded = [r for r in rows if r[4]]
    n = len(graded)
    fired = sum(r[4]["fired"] for r in graded)
    lost = sum(r[4]["pick_lost"] for r in graded)
    named = sum(r[4]["verdict"] == "named it" for r in graded)
    survived = sum(r[4]["verdict"] == "survived it" for r in graded)
    summ = dict(written=len(rows), graded=n, fired=fired, lost=lost, named=named, survived=survived)
    L += ["# Pre-mortems — the machine names how each pick could be wrong, then grades itself", "",
          "One per card game, written before kickoff from the stat package: the matchup the two",
          "track records disagree on most, with the threshold at the midpoint. After the game the",
          "condition is checked from the box score or the play-by-play.", "",
          f"**Season: {n} graded · fired {fired} · picks lost {lost} · named the actual reason {named} of {lost}"
          f" · fired but the pick still won {survived}**" if n else "**Season: nothing graded yet**", "",
          "| Wk | Game | Pick | Wrong if | Observed | Fired | Pick | Verdict |", "|---|---|---|---|---|---|---|---|"]
    for w, game, pick, text, r in rows:
        if r:
            L.append(f"| {w} | {game} | {pick} | {text} | {r['observed']} | {'yes' if r['fired'] else 'no'} | "
                     f"{'lost' if r['pick_lost'] else 'won'} {r['final'][0]}–{r['final'][1]} | {r['verdict']} |")
        else:
            L.append(f"| {w} | {game} | {pick} | {text} | — | — | pending | — |")
    return "\n".join(L) + "\n", summ


def season_line(pms=None):
    """One line for the receipts slide / notes, '' until something is graded."""
    pms = pms or load()
    _, s = table(pms)
    if not s["graded"]:
        return ""
    return (f"Pre-mortems: {s['graded']} graded · {s['fired']} fired · {s['lost']} picks lost · "
            f"named the reason {s['named']} of {s['lost']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--table", action="store_true")
    a = ap.parse_args()
    pms = grade_week(a.week, a.refresh) if a.week else load()
    md, summ = table(pms)
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    open(OUT_MD, "w", encoding="utf-8").write(md)
    print("\n" + md)
    print("wrote", os.path.relpath(OUT_MD, HERE))
