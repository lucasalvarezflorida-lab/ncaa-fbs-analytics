"""Availability layer - SHADOW (Phase 4, built 2026-09-22).

The rating knows nothing about who is missing. This adds a per-team points
adjustment on top of it, shown separately ("machine 7.5, with availability
5.5") and never on a slide until Lucas switches it.

AUTOMATIC PART (play-by-play): who threw each team's passes in each game
(the passer token in playText: "Bryce Young pass ..." / "#10 M.Reed pass
..."; sacks count). The season-to-date PRIMARY passer is the one with the
most dropbacks in the team's earlier games. Before week w the starter is
flagged OUT when the primary did not throw (or threw under SHARE_LT of the
dropbacks) in the team's most recent game - the only thing knowable before
kickoff without news. Cached per season in
fpi-decomposition/output/qb_starts_{season}.json.

HOW MUCH THE STARTER CARRIES (fit 2022-24, internal/AVAILABILITY_2026.md):
on average a flagged team does NOT fall short of the machine's number (+0.6,
se 0.7) - most flags are benchings, and the number already holds one game
of the backup. The shortfall lives in FAVORITES: flagged 7-14 point
favorites fall 3.1 short of the baseline, 14+ favorites 5.0. So the auto
rule is penalty = RULE["k"] x the team's predicted margin, favorites of
RULE["min_fav"] or more only, capped at RULE["cap"]; nothing for underdogs.
Tested on 2025 through backtest.py (model "availability"): a wash.

MANUAL PART: internal/availability.json, maintained by Lucas from the news.
    python availability.py add "Texas" "Arch Manning" QB out --return 6 --note "ankle, Sept 22"
    python availability.py add "LSU" "Whit Weeks" LB questionable
    python availability.py add "Miami" "CharMar Brown" RB out --points 1.0     # explicit points override
    python availability.py clear "Texas" "Arch Manning"
    python availability.py list
Status out = full weight, questionable = half. QB out = QB_PEN (or the
quality-scaled number when the starter's PPA edge is known); any other
position OTHER_PEN a head, capped at OTHER_CAP per team; --points overrides.
Entries expire on their --return week.

WEEKLY SHADOW:  python availability.py --week 4  ->  internal/availability_week4.json
(every team's adjustment, auto + manual, and each card game as
"machine X, with availability Y"). Internal only."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

OUT = HERE / "fpi-decomposition" / "output"
MANUAL = HERE / "internal" / "availability.json"
PASS_TYPES = {"Pass Reception", "Pass Incompletion", "Passing Touchdown", "Sack", "Pass Interception Return",
              "Interception", "Interception Return Touchdown", "Pass Completion", "Pass"}
PASSER = re.compile(r"(?:#\d+\s+)?([A-Z][\w'.-]*\.?\s?[A-Z][\w'-]+(?:\s(?:Jr|Sr|II|III|IV)\.?)?)\s+(?:pass|sacked)", re.I)
SHARE_LT = 0.2      # primary threw under this share of the last game's dropbacks -> flagged out
MIN_DB = 40         # dropbacks before a starter's PPA edge is trusted
QB_PEN = 3.0        # manual QB-out entry with no --points (news says the starter is out)
# AUTO flag rule (fit 2022-24, internal/AVAILABILITY_2026.md): a team flagged out
# underperforms the machine's number ONLY when it is favored - the better the
# team, the more of its number the starter carries. penalty = k * predicted
# margin, from min_fav up, capped; nothing for underdogs.
RULE = dict(k=0.3, min_fav=7.0, cap=6.0)
OTHER_PEN, OTHER_CAP = 0.5, 2.0


# ---------------- who threw the passes ----------------

def passer_key(name: str) -> str:
    """'Arch Manning' / '#16 A.Manning' / 'A. Manning' -> 'A.Manning'. CFBD's play
    text switched from full names to initial-dot-surname mid-2025, so passers
    are keyed by first initial + surname (suffixes dropped)."""
    name = re.sub(r"^#\d+\s+", "", name.strip())
    name = re.sub(r"\s+(Jr|Sr|II|III|IV)\.?$", "", name, flags=re.I)
    parts = name.replace(". ", ".").split()
    if len(parts) == 1:
        return parts[0]
    first, last = parts[0], parts[-1]
    if "." in first and len(first) <= 3:
        return f"{first[0]}.{last}"
    return f"{first[0]}.{last}"


def passer_of(p) -> str | None:
    m = PASSER.search(p.get("playText") or "")
    if not m:
        return None
    name = m.group(1).strip()
    return None if name.lower().startswith(("team", "no huddle", "shotgun")) else passer_key(name)


def qb_table(season: int, games: list[dict], rebuild: bool = False) -> dict:
    """{team: [ {week, game_id, opp, primary, share, dropbacks, passers: {name: [db, ppa_sum, ppa_n]}} ... ]}
    in game order, from the cached full-week play files."""
    OUT.mkdir(exist_ok=True)
    path = OUT / f"qb_starts_{season}.json"
    if path.exists() and not rebuild:
        return json.loads(path.read_text(encoding="utf-8"))
    import cfbd_client as cfbd
    by_id = {g["id"]: g for g in games}
    per: dict[tuple, dict] = {}
    for w in sorted({g["week"] for g in games}):
        for p in cfbd.get("/plays", {"year": season, "week": w, "seasonType": "regular"}, False):
            g = by_id.get(p.get("gameId"))
            if not g or p["playType"] not in PASS_TYPES:
                continue
            team = normalize_name(p.get("offense") or "")
            if team not in (g["home"], g["away"]):
                continue
            name = passer_of(p)
            if not name:
                continue
            slot = per.setdefault((team, g["id"]), dict(week=g["week"], game_id=g["id"],
                                                        opp=(g["away"] if team == g["home"] else g["home"]), passers={}))
            q = slot["passers"].setdefault(name, [0, 0.0, 0])
            q[0] += 1
            if p.get("ppa") is not None:
                q[1] += float(p["ppa"]); q[2] += 1
    out = defaultdict(list)
    for (team, gid), s in per.items():
        db = sum(v[0] for v in s["passers"].values())
        prim = max(s["passers"], key=lambda k: s["passers"][k][0])
        s.update(primary=prim, dropbacks=db, share=round(s["passers"][prim][0] / max(db, 1), 3))
        out[team].append(s)
    for t in out:
        out[t].sort(key=lambda s: (s["week"], s["game_id"]))
    path.write_text(json.dumps(out), encoding="utf-8")
    return out


def starter_status(rows: list[dict], week: int) -> dict | None:
    """Before `week`, from the team's earlier games: the season primary, whether
    he is flagged OUT (absent / under SHARE_LT in the last game), his PPA per
    dropback edge over the league (None until MIN_DB), and who started last."""
    prev = [r for r in rows if r["week"] < week]
    if len(prev) < 2:
        return None
    tot = defaultdict(lambda: [0, 0.0, 0])
    for r in prev:
        for n, v in r["passers"].items():
            tot[n][0] += v[0]; tot[n][1] += v[1]; tot[n][2] += v[2]
    primary = max(tot, key=lambda n: tot[n][0])
    last = prev[-1]
    share_last = last["passers"].get(primary, [0])[0] / max(last["dropbacks"], 1)
    out = share_last < SHARE_LT
    ppa = tot[primary][1] / tot[primary][2] if tot[primary][2] >= MIN_DB else None
    return dict(primary=primary, out=out, share_last=round(share_last, 3), last_primary=last["primary"],
                ppa=ppa, dropbacks=tot[primary][0], games=len(prev))


LEAGUE_PPA = 0.12   # league mean PPA per dropback, refit in fit_penalty


def qb_adjust(status: dict | None, pred: float, rule: dict | None = None) -> float:
    """Points taken OFF the team's margin when its starter is flagged out.
    pred = the team's predicted margin from the on-air machine (its side).
    rule: k / min_fav / cap (scaled by the number, favorites only); a rule with
    'flat' pays that many points to every flagged side at or above min_fav."""
    if not status or not status["out"]:
        return 0.0
    r = rule or RULE
    if "flat" in r:
        return r["flat"] if pred >= r.get("min_fav", -99) else 0.0
    if pred < r["min_fav"]:
        return 0.0
    return min(r["k"] * pred, r["cap"])


# ---------------- backtest / fit ----------------

class AvailabilityModel:
    """backtest.py plug-in: the on-air machine minus the QB-out penalty on the flagged side."""

    def __init__(self, rule=None, desc=""):
        self.rule = rule or RULE
        self.desc = desc or f"SHADOW availability: current minus QB-out penalty {self.rule}"
        self._qb = {}

    def qb(self, ctx):
        if ctx.season not in self._qb:
            self._qb[ctx.season] = qb_table(ctx.season, ctx.games)
        return self._qb[ctx.season]

    def __call__(self, ctx, week):
        import backtest as bt
        cur = bt.ridge_predict(ctx, week, bt.MODELS["current"])
        if not cur:
            return {}
        qb = self.qb(ctx)
        rows = np.flatnonzero(ctx.week == week)
        m = []
        for i in rows:
            g = ctx.games[i]
            base = cur[g["id"]][0]
            adj = (qb_adjust(starter_status(qb.get(g["home"], []), week), base, self.rule)
                   - qb_adjust(starter_status(qb.get(g["away"], []), week), -base, self.rule))
            m.append(base - adj)
        m = np.array(m)
        p = ctx.curve(week).win_prob(m)
        return {ctx.games[i]["id"]: (float(mm), float(pp)) for i, mm, pp in zip(rows, m, p)}


def fit_penalty(seasons=(2022, 2023, 2024)) -> dict:
    """Residual of the on-air machine (actual - predicted, from the flagged
    team's side) in games where a starter is flagged out. Returns the flat
    penalty, the quality-scaled fit and the league PPA baseline."""
    global LEAGUE_PPA
    import backtest as bt
    flagged, edges, ppas = [], [], []
    n_games = n_flag = 0
    for s in seasons:
        ctx = bt.SeasonCtx(s)
        qb = qb_table(s, ctx.games)
        # league PPA per dropback across all passers
        tot_ppa = sum(v[1] for rows in qb.values() for r in rows for v in r["passers"].values())
        tot_n = sum(v[2] for rows in qb.values() for r in rows for v in r["passers"].values())
        ppas.append(tot_ppa / max(tot_n, 1))
        for w in range(2, 16):
            cur = bt.ridge_predict(ctx, w, bt.MODELS["current"])
            for g in ctx.games:
                if g["week"] != w:
                    continue
                n_games += 1
                for side, sign in ((g["home"], 1), (g["away"], -1)):
                    st = starter_status(qb.get(side, []), w)
                    if st and st["out"]:
                        n_flag += 1
                        resid = sign * (g["margin"] - cur[g["id"]][0])      # + = flagged team beat the number
                        flagged.append(resid)
                        edges.append(st["ppa"])
    LEAGUE_PPA = float(np.mean(ppas))
    flagged = np.array(flagged)
    flat = -float(flagged.mean())
    se = float(flagged.std() / np.sqrt(len(flagged)))
    have = [(e, r) for e, r in zip(edges, flagged) if e is not None]
    if len(have) > 30:
        x = np.array([100 * (e - LEAGUE_PPA) for e, _ in have]); y = np.array([-r for _, r in have])
        b, a = np.polyfit(x, y, 1)
    else:
        a, b = flat, 0.0
    return dict(seasons=list(seasons), games=n_games, flagged_sides=int(len(flagged)), flat_penalty=round(flat, 2),
                se=round(se, 2), league_ppa=round(LEAGUE_PPA, 4), scaled=(round(float(a), 2), round(float(b), 3)),
                n_with_edge=len(have),
                by_edge=[dict(bucket=lab, n=int(len(v)), shortfall=round(-float(np.mean(v)), 2)) for lab, v in (
                    ("starter below league", [r for e, r in have if e < LEAGUE_PPA]),
                    ("starter above league", [r for e, r in have if e >= LEAGUE_PPA]),
                    ("edge unknown (<40 db)", [r for e, r in zip(edges, flagged) if e is None]))])


# ---------------- manual file ----------------

def load_manual() -> list[dict]:
    return json.loads(MANUAL.read_text(encoding="utf-8")) if MANUAL.exists() else []


def save_manual(rows):
    MANUAL.parent.mkdir(exist_ok=True)
    MANUAL.write_text(json.dumps(rows, indent=1), encoding="utf-8")


def manual_adjust(team: str, week: int, entries: list[dict]) -> tuple[float, list[str]]:
    """Points off the team's margin from the manual file for `week`, with the reasons."""
    pen, other, why = 0.0, 0.0, []
    for e in entries:
        if normalize_name(e["team"]) != team:
            continue
        if e.get("return") is not None and week >= int(e["return"]):
            continue
        w = 1.0 if e["status"] == "out" else 0.5 if e["status"] == "questionable" else 0.0
        if not w:
            continue
        if e.get("points") is not None:
            pts = float(e["points"]) * w
            pen += pts
        elif e["pos"].upper() == "QB":
            pts = QB_PEN * w
            pen += pts
        else:
            pts = OTHER_PEN * w
            other += pts
        why.append(f"{e['player']} ({e['pos']}, {e['status']}) -{pts:g}")
    return pen + min(other, OTHER_CAP), why


# ---------------- weekly shadow ----------------

def shadow_week(week: int, write: bool = True) -> dict:
    import backtest as bt
    ctx = bt.SeasonCtx(2026)
    qb = qb_table(2026, ctx.games, rebuild=True)
    manual = load_manual()
    # each team's predicted margin in its week-N game (its side) from the on-air machine
    pred_side = {}
    for gid, (mm, _) in bt.ridge_predict(ctx, week, bt.MODELS["current"]).items():
        g = next(x for x in ctx.games if x["id"] == gid)
        pred_side[g["home"]], pred_side[g["away"]] = mm, -mm
    src0 = HERE / f"card_data_week{week}_frozen.json"
    if not src0.exists():
        src0 = HERE / f"card_data_week{week}.json"
    if src0.exists():   # upcoming games are not in ctx.games (not completed) - take the card's numbers
        for g in json.loads(src0.read_text(encoding="utf-8"))["games"]:
            pred_side[normalize_name(g["home"])], pred_side[normalize_name(g["away"])] = g["model_margin"], -g["model_margin"]
    teams = {}
    for t in ctx.teams:
        st = starter_status(qb.get(t, []), week)
        auto = qb_adjust(st, pred_side.get(t, 0.0))
        man, why = manual_adjust(t, week, manual)
        # a manual QB entry for the same starter should not double count the auto flag
        if auto and any("QB" in w for w in why):
            auto = 0.0
        total = auto + man
        if total or (st and st["out"]):
            teams[t] = dict(adjustment=-round(total, 1), auto_qb=-round(auto, 1), manual=-round(man, 1),
                            primary=st["primary"] if st else None, starter_out=bool(st and st["out"]),
                            last_primary=st["last_primary"] if st else None, reasons=why)
    src = HERE / f"card_data_week{week}_frozen.json"
    if not src.exists():
        src = HERE / f"card_data_week{week}.json"
    card = json.loads(src.read_text(encoding="utf-8"))["games"] if src.exists() else []
    games = []
    for g in card:
        h, a = normalize_name(g["home"]), normalize_name(g["away"])
        adj = teams.get(h, {}).get("adjustment", 0.0) - teams.get(a, {}).get("adjustment", 0.0)
        games.append(dict(away=g["away"], home=g["home"], machine=g["model_margin"], with_availability=round(g["model_margin"] + adj, 1),
                          adj_home=teams.get(h, {}).get("adjustment", 0.0), adj_away=teams.get(a, {}).get("adjustment", 0.0)))
    out = dict(week=week, as_of=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), status="SHADOW - not on air",
               params=dict(rule=RULE, qb_pen_manual=QB_PEN, share_lt=SHARE_LT, other_pen=OTHER_PEN, other_cap=OTHER_CAP),
               manual_entries=len(manual), teams=teams, games=games)
    if write:
        (HERE / "internal").mkdir(exist_ok=True)
        (HERE / "internal" / f"availability_week{week}.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    a_add = sub.add_parser("add"); a_add.add_argument("team"); a_add.add_argument("player"); a_add.add_argument("pos")
    a_add.add_argument("status", choices=["out", "questionable", "back"]); a_add.add_argument("--return", dest="ret", type=int)
    a_add.add_argument("--points", type=float); a_add.add_argument("--note", default="")
    a_clr = sub.add_parser("clear"); a_clr.add_argument("team"); a_clr.add_argument("player")
    sub.add_parser("list")
    ap.add_argument("--week", type=int); ap.add_argument("--fit", action="store_true"); ap.add_argument("--season", type=int)
    a = ap.parse_args()
    if a.cmd == "add":
        rows = [r for r in load_manual() if not (r["team"] == a.team and r["player"] == a.player)]
        rows.append(dict(team=a.team, player=a.player, pos=a.pos, status=a.status, **{"return": a.ret}, points=a.points,
                         note=a.note, added=dt.date.today().isoformat()))
        save_manual(rows); print(f"added: {a.team} {a.player} {a.pos} {a.status}" + (f" back week {a.ret}" if a.ret else ""))
    elif a.cmd == "clear":
        rows = load_manual(); n = len(rows)
        rows = [r for r in rows if not (r["team"] == a.team and r["player"] == a.player)]
        save_manual(rows); print(f"cleared {n - len(rows)} entry")
    elif a.cmd == "list":
        for r in load_manual():
            print(f"  {r['team']:18s} {r['player']:22s} {r['pos']:3s} {r['status']:12s} return {r.get('return')}  pts {r.get('points')}  {r.get('note', '')}")
        print(f"({len(load_manual())} entries in {MANUAL.relative_to(HERE)})")
    if a.season:
        import backtest as bt
        ctx = bt.SeasonCtx(a.season)
        qb = qb_table(a.season, ctx.games, rebuild=True)
        flags = sum(1 for t, rows in qb.items() for w in range(2, 16) if (starter_status(rows, w) or {}).get("out"))
        print(f"{a.season}: {sum(len(v) for v in qb.values())} team-games, {flags} team-weeks with the starter flagged out")
    if a.fit:
        f = fit_penalty()
        print(json.dumps(f, indent=1))
    if a.week:
        out = shadow_week(a.week)
        print(f"SHADOW availability before week {a.week}: {len(out['teams'])} teams adjusted, {out['manual_entries']} manual entries - not on air")
        for t, v in sorted(out["teams"].items(), key=lambda kv: kv[1]["adjustment"]):
            print(f"  {t:22s} {v['adjustment']:+5.1f}  auto QB {v['auto_qb']:+4.1f} (primary {v['primary']} -> last {v['last_primary']})  manual {v['manual']:+4.1f} {v['reasons']}")
        for g in out["games"]:
            if g["adj_home"] or g["adj_away"]:
                print(f"  {g['away']} at {g['home']}: machine {g['machine']:+.1f}, with availability {g['with_availability']:+.1f}")
        print(f"wrote internal/availability_week{a.week}.json")
