"""Offensive and defensive stats for every FBS team (Lucas 9/23) -> the workbook.

From the cached CFBD box scores (/games/teams, per week) and full-week
play-by-play (/plays), season to date, every FBS team:

  offense   games, points/game, plays/game, yards/play, completions-attempts,
            passing yards, yards per attempt (completions only - the notes
            convention), yards per completion, pass TD-INT, explosive pass
            rate (20+ per dropback), sack rate allowed, rushing att-yds (box
            score: sacks count), yards per carry, 10+ run rate, stuff rate,
            third-down %, third-and-long %, red-zone TD %, turnovers
  defense   the same, allowed (sacks / stuffs / takeaways MADE)
plus a national rank (of 138) for each rate and a "vs FBS" copy of the key
rates (FCS games skew the averages).

    python team_stats.py                 # compute -> team_stats_2026.json, print a few teams
    python team_stats.py --sheet         # also write the 'Team Stats' sheet into the workbook
Sheet + conference-tab block are rebuilt by refresh_all every Tuesday."""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
import cfbd_client as cfbd  # noqa: E402
from stat_package import SKIP, side_stats  # noqa: E402

OUT_JSON = HERE / "team_stats_2026.json"
SHEET = "Team Stats"

# (key, label, source, higher_is_better_for_offense)  - defense rank flips where the stat is "allowed"
OFF_ROWS = [
    ("gp", "Games", None, None),
    ("ppg", "Points / game", "box", True),
    ("plays_pg", "Plays / game", "pbp", None),
    ("ypp", "Yards / play", "box", True),
    ("comp_att", "Completions - attempts", "pbp", None),
    ("pass_yds", "Passing yards", "pbp", True),
    ("ypa", "Yards / pass attempt", "pbp", True),
    ("ypc_pass", "Yards / completion", "pbp", True),
    ("td_int", "Pass TD - INT", "box", None),
    ("p20_rate", "Explosive pass rate (20+ / dropback)", "pbp", True),
    ("sack_rate", "Sack rate", "pbp", False),
    ("rush_att_yds", "Rushing att - yds (box score)", "box", None),
    ("rush_ypc", "Yards / carry (box score)", "box", True),
    ("r10_rate", "10+ run rate", "pbp", True),
    ("stuff_rate", "Stuff rate", "pbp", False),
    ("t3_pct", "Third down %", "box", True),
    ("t3_long_pct", "Third-and-long %", "pbp", True),
    ("rz_pct", "Red-zone TD %", "pbp", True),
    ("turnovers", "Turnovers", "box", False),
]


def _pct(frac):
    n, d = frac.split("/")
    return round(100 * int(n) / max(int(d), 1), 1)


def compute(season: int = 2026, refresh: bool = False) -> dict:
    games = cfbd.get("/games", {"year": season, "seasonType": "regular"}, refresh)
    fbs = sorted({g["homeTeam"] for g in games if g.get("homeClassification") == "fbs"}
                 | {g["awayTeam"] for g in games if g.get("awayClassification") == "fbs"})
    done = [g for g in games if g.get("completed") and g.get("homePoints") is not None
            and (g.get("homeClassification") == "fbs" or g.get("awayClassification") == "fbs")]
    weeks = sorted({g["week"] for g in done})
    by_id = {g["id"]: g for g in done}
    # box rows per (game, team)
    box = {}
    for w in weeks:
        for t in cfbd.get("/games/teams", {"year": season, "week": w, "seasonType": "regular"}, refresh):
            if t.get("id") in by_id:
                for side in t["teams"]:
                    st = {x["category"]: x["stat"] for x in side["stats"]}
                    st["points"] = side.get("points")
                    box[(t["id"], side["team"])] = st
    # plays per (game, offense team)
    plays = collections.defaultdict(list)
    for w in weeks:
        for p in cfbd.get("/plays", {"year": season, "week": w, "seasonType": "regular"}, refresh):
            if p.get("gameId") in by_id and not any(s in p["playType"] for s in SKIP):
                plays[(p["gameId"], p["offense"])].append(p)
    out = {}
    for team in fbs:
        rows = dict(off=[], def_=[], off_fbs=[], def_fbs=[])
        gp = 0
        for g in done:
            if team not in (g["homeTeam"], g["awayTeam"]):
                continue
            opp = g["awayTeam"] if g["homeTeam"] == team else g["homeTeam"]
            opp_fbs = (g["awayClassification"] if g["homeTeam"] == team else g["homeClassification"]) == "fbs"
            own_box, opp_box = box.get((g["id"], team)), box.get((g["id"], opp))
            own_pl, opp_pl = plays.get((g["id"], team), []), plays.get((g["id"], opp), [])
            if not own_box or not opp_box or len(own_pl) < 10:
                continue
            gp += 1
            o = dict(side_stats(own_pl), box=own_box, opp_box=opp_box)
            d = dict(side_stats(opp_pl), box=opp_box, opp_box=own_box)
            rows["off"].append(o); rows["def_"].append(d)
            if opp_fbs:
                rows["off_fbs"].append(o); rows["def_fbs"].append(d)

        def agg(parts):
            if not parts:
                return {}
            n = len(parts)
            S = lambda k: sum(p.get(k, 0) for p in parts)
            B = lambda k: sum(float(p["box"].get(k) or 0) for p in parts)
            ratt, ryds = B("rushingAttempts"), B("rushingYards")
            t3n = sum(int(p["box"]["thirdDownEff"].split("-")[0]) for p in parts if p["box"].get("thirdDownEff"))
            t3d = sum(int(p["box"]["thirdDownEff"].split("-")[1]) for p in parts if p["box"].get("thirdDownEff"))
            t3l = [p["t3_long"].split("/") for p in parts]; rz = [p["rz"].split("/") for p in parts]
            return dict(
                gp=n, ppg=round(B("points") / n, 1), plays_pg=round(S("plays") / n, 1),
                ypp=round(B("totalYards") / max(S("plays"), 1), 2),
                comp_att=f"{S('comp')}-{S('att')}", pass_yds=S("pass_yds"),
                ypa=round(S("pass_yds") / max(S("att"), 1), 1), ypc_pass=round(S("pass_yds") / max(S("comp"), 1), 1),
                td_int=f"{int(B('passingTDs'))}-{int(B('interceptions'))}",
                p20_rate=round(100 * S("p20") / max(S("dropbacks"), 1), 1), sack_rate=round(100 * S("sacks") / max(S("dropbacks"), 1), 1),
                rush_att_yds=f"{int(ratt)}-{int(ryds)}", rush_ypc=round(ryds / max(ratt, 1), 1),
                r10_rate=round(100 * S("r10") / max(S("rushes"), 1), 1), stuff_rate=round(100 * S("stuffs") / max(S("rushes"), 1), 1),
                t3_pct=round(100 * t3n / max(t3d, 1), 1),
                t3_long_pct=round(100 * sum(int(a) for a, b in t3l) / max(sum(int(b) for a, b in t3l), 1), 1),
                rz_pct=round(100 * sum(int(a) for a, b in rz) / max(sum(int(b) for a, b in rz), 1), 1),
                turnovers=int(B("turnovers")))
        out[team] = dict(gp=gp, off=agg(rows["off"]), def_=agg(rows["def_"]),
                         off_fbs=agg(rows["off_fbs"]), def_fbs=agg(rows["def_fbs"]))
    # national ranks (of the teams with games)
    for unit in ("off", "def_"):
        for key, _, _, better in OFF_ROWS:
            if better is None:
                continue
            hib = better if unit == "off" else (not better)          # defense: "allowed" flips; sacks/stuffs/turnovers made = good
            if unit == "def_" and key in ("sack_rate", "stuff_rate", "turnovers"):
                hib = True
            vals = [(t, v[unit][key]) for t, v in out.items() if v[unit]]
            vals.sort(key=lambda x: -x[1] if hib else x[1])
            for i, (t, _) in enumerate(vals, 1):
                out[t][unit][key + "_rk"] = i
    meta = dict(season=season, weeks=weeks, teams=len(out), as_of=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"))
    OUT_JSON.write_text(json.dumps(dict(meta=meta, teams=out), indent=1), encoding="utf-8")
    return out


def write_sheet(book: Path, data: dict | None = None) -> None:
    """'Team Stats' sheet: one row per team, offense then defense columns, ranks beside the rates.
    Column A = team (the conference tabs MATCH on it)."""
    from openpyxl import load_workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    if data is None:
        data = json.loads(OUT_JSON.read_text(encoding="utf-8"))["teams"]
    wb = load_workbook(book, keep_vba=True)
    if SHEET in wb.sheetnames:
        del wb[SHEET]
    ws = wb.create_sheet(SHEET)
    weeks = json.loads(OUT_JSON.read_text(encoding="utf-8"))["meta"]["weeks"]
    ws["A1"] = f"TEAM STATS 2026 - every FBS team, season to date (through week {max(weeks)})"
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"] = ("Offense then defense. Passing yards per attempt = completions only (the notes convention); rushing = official box "
                "score (sacks count); explosive / stuff / 10+ rates from play-by-play. Rank = of 138 (defense ranks are 'allowed', "
                "except sacks, stuffs and takeaways). 'vs FBS' columns leave out FCS games.")
    hdr = ["Team"]
    cols = []   # (unit, key, label)
    for unit, tag in (("off", "OFF"), ("def_", "DEF")):
        for key, label, _, better in OFF_ROWS:
            if unit == "def_" and key == "gp":
                continue
            lab = label if unit == "off" else def_label(key, label, better)
            hdr.append(f"{tag}: {lab}"); cols.append((unit, key))
            if better is not None:
                hdr.append("rk"); cols.append((unit, key + "_rk"))
    for unit, tag in (("off_fbs", "OFF vs FBS"), ("def_fbs", "DEF vs FBS")):
        for key in ("ppg", "ypp", "ypa", "rush_ypc", "p20_rate", "t3_pct"):
            hdr.append(f"{tag}: {dict((k, l) for k, l, _, _ in OFF_ROWS)[key]}"); cols.append((unit, key))
    for j, h in enumerate(hdr, 1):
        c = ws.cell(row=4, column=j, value=h)
        c.font = Font(bold=True, color="FFFFFF", size=9); c.fill = PatternFill("solid", fgColor="1F3864")
        c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[4].height = 54
    r = 5
    for team in sorted(data, key=lambda t: (-data[t]["gp"], t)):
        v = data[team]
        ws.cell(row=r, column=1, value=team).font = Font(bold=True)
        for j, (unit, key) in enumerate(cols, 2):
            ws.cell(row=r, column=j, value=(v.get(unit) or {}).get(key))
        r += 1
    ws.freeze_panes = "B5"
    ws.auto_filter.ref = f"A4:{ws.cell(row=4, column=len(hdr)).column_letter}{r - 1}"
    ws.column_dimensions["A"].width = 22
    for j in range(2, len(hdr) + 1):
        ws.column_dimensions[ws.cell(row=4, column=j).column_letter].width = 7 if hdr[j - 1] == "rk" else 11
    wb.save(book)
    print(f"{SHEET}: {r - 5} teams, {len(hdr)} columns")


def def_label(key, label, better):
    if key == "turnovers":
        return "Takeaways"
    if better is not None and key not in ("sack_rate", "stuff_rate"):
        return label + " allowed"
    return label


def block_spec():
    """Rows for the conference-tab block: (label, offense header, defense header or None, has_rank).
    The headers are the exact strings on the 'Team Stats' sheet, so the tab can MATCH on them."""
    out = []
    for key, label, _, better in OFF_ROWS:
        off_h = f"OFF: {label}"
        def_h = None if key == "gp" else f"DEF: {def_label(key, label, better)}"
        out.append((label, off_h, def_h, better is not None))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--sheet", action="store_true")
    a = ap.parse_args()
    from refresh_all import load_env_key
    load_env_key()
    d = compute(refresh=a.refresh)
    for t in ("Texas", "Georgia", "Miami"):
        o, de = d[t]["off"], d[t]["def_"]
        print(f"{t}: gp {d[t]['gp']} | OFF {o['ppg']} ppg (#{o['ppg_rk']}), {o['ypa']} ypa (#{o['ypa_rk']}), {o['rush_ypc']} ypc (#{o['rush_ypc_rk']}) "
              f"| DEF {de['ppg']} allowed (#{de['ppg_rk']}), {de['ypa']} ypa (#{de['ypa_rk']}), sack rate {de['sack_rate']} (#{de['sack_rate_rk']})")
    print("wrote", OUT_JSON.name)
    if a.sheet:
        write_sheet(HERE / "NCAA_FBS_Teams.xlsm", d)
