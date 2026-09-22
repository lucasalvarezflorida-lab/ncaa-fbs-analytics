"""Play-level efficiency rating - SHADOW (Phase 1, built 2026-09-22).

Never on a slide, never the on-air number, until Lucas switches it. Graded
next to the on-air machine by backtest.py (model "efficiency").

THE IDEA
  Score margins carry turnover luck, garbage time and special-teams scores.
  Every team-game side is turned into the points its offense DESERVED from
  its non-garbage scrimmage plays, using the deserved-margin model already
  frozen in efficiency_model.json (fit 2021-24 on CFBD's advanced box scores):
      D = 0.887 * (league plays per game) * mean PPA per play + 20.78 * success rate
  so offense, defense and the rating all live in POINTS, the same scale as the
  on-air machine, and the preseason FPI can be the prior on each unit.

THE SOLVE (same ridge family as inseason_ratings)
      D_obs = mu + off_i - def_j + HFA * home_i + e          one row per team-game side
      minimize sum e^2 + lam * sum (off_i - FPI_i / 2)^2 + lam * sum (def_j - FPI_j / 2)^2
  off_i = points the offense produces above an average FBS offense, def_j =
  points the defense takes away below an average offense (higher = better for
  both). lam = games of evidence the prior is worth. Special teams is a
  separate small component: net PPA on kickoffs / punts / field goals per
  game, prior 0, shrunk hard (LAM_ST). Combined = off + def + st; predicted
  margin = (off_h - def_a) - (off_a - def_h) + (st_h - st_a) + HFA.

DATA  CFBD /plays per (year, week) - the whole week, all teams - cached in
  fpi-decomposition/data/plays_seasonType-regular_week-W_year-Y.json (about
  19,000 plays a week). Team-game observations are cached per season in
  fpi-decomposition/output/eff_obs_{season}.json (regenerate with --rebuild).
  Garbage time (Connelly): a play is skipped when the lead is more than 43 in
  the 1st quarter, 37 in the 2nd, 27 in the 3rd, 21 in the 4th. Success =
  50% of the distance on 1st down, 70% on 2nd, 100% on 3rd/4th; touchdowns
  succeed, turnovers fail.

    python efficiency_ratings.py --week 4               # 2026 shadow ratings before week 4 (weeks < 4)
    python efficiency_ratings.py --week 4 --refresh     # pull the missing 2026 play weeks first
    python efficiency_ratings.py --season 2025 --rebuild   # rebuild one season's observation cache
Writes internal/shadow_ratings_week{N}.json and prints the shadow top 25 next
to the on-air machine.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

OUT = HERE / "fpi-decomposition" / "output"
MODEL_JSON = HERE / "efficiency_model.json"
LAM = 3.0          # games of evidence the FPI prior is worth (per unit)
LAM_ST = 8.0       # special teams: shrunk hard toward 0
HFA = 2.5
PLAYS_PG = 68.0    # league-average scrimmage plays per team-game (points scale for mean PPA)
SCALE = 0.77       # deserved-points diff -> margin slope (2022: margin = 1.1 + 0.77 * D diff, r 0.90);
                   # without it a D residual counts as more than a point of evidence
GARBAGE = {1: 43, 2: 37, 3: 27, 4: 21}

SCRIMMAGE = {"Rush", "Pass Reception", "Pass Incompletion", "Sack", "Rushing Touchdown", "Passing Touchdown",
             "Interception", "Pass Interception Return", "Interception Return Touchdown", "Fumble Recovery (Own)",
             "Fumble Recovery (Opponent)", "Fumble Return Touchdown", "Safety", "Pass Completion", "Pass"}
TURNOVER = {"Interception", "Pass Interception Return", "Interception Return Touchdown", "Fumble Recovery (Opponent)",
            "Fumble Return Touchdown", "Safety"}
SPECIAL = {"Kickoff", "Kickoff Return (Offense)", "Kickoff Return Touchdown", "Punt", "Punt Return", "Punt Return Touchdown",
           "Blocked Punt", "Blocked Punt Touchdown", "Field Goal Good", "Field Goal Missed", "Blocked Field Goal",
           "Missed Field Goal Return", "Missed Field Goal Return Touchdown", "Blocked Field Goal Touchdown"}


def _model():
    m = json.loads(MODEL_JSON.read_text(encoding="utf-8"))
    return m["net_tppa"], m["net_sr"]


def _success(p):
    if "Touchdown" in p["playType"] and p["playType"] not in TURNOVER:
        return 1.0
    if p["playType"] in TURNOVER:
        return 0.0
    d, dist, yd = p.get("down"), p.get("distance"), p.get("yardsGained") or 0
    if not d or dist is None:
        return None
    need = {1: 0.5, 2: 0.7}.get(d, 1.0) * dist
    return 1.0 if yd >= need else 0.0


def _garbage(p):
    per = p.get("period") or 0
    lead = abs((p.get("offenseScore") or 0) - (p.get("defenseScore") or 0))
    return per in GARBAGE and lead > GARBAGE[per]


def build_obs(season: int, games: list[dict], refresh: bool = False) -> list[dict]:
    """One row per team-game SIDE for the rated games given (backtest.load_games
    rows: id, week, home, away, neutral, home_raw, away_raw)."""
    import cfbd_client as cfbd
    c_ppa, c_sr = _model()
    by_id = {g["id"]: g for g in games}
    weeks = sorted({g["week"] for g in games})
    rows = []
    for w in weeks:
        plays = cfbd.get("/plays", {"year": season, "week": w, "seasonType": "regular"}, refresh)
        per_game: dict[int, dict] = {}
        for p in plays:
            g = by_id.get(p.get("gameId"))
            if not g:
                continue
            slot = per_game.setdefault(g["id"], {g["home_raw"]: dict(ppa=[], sr=[], st=0.0), g["away_raw"]: dict(ppa=[], sr=[], st=0.0)})
            off, de = p.get("offense"), p.get("defense")
            if off not in slot or de not in slot:
                continue
            t = p["playType"]
            if t in SCRIMMAGE:
                if _garbage(p):
                    continue
                if p.get("ppa") is not None:
                    slot[off]["ppa"].append(float(p["ppa"]))
                s = _success(p)
                if s is not None:
                    slot[off]["sr"].append(s)
            elif t in SPECIAL and p.get("ppa") is not None:
                slot[off]["st"] += float(p["ppa"])
                slot[de]["st"] -= float(p["ppa"])
        for gid, sides in per_game.items():
            g = by_id[gid]
            for raw, s in sides.items():
                if len(s["ppa"]) < 20:
                    continue
                team = normalize_name(raw)
                opp = g["away"] if team == g["home"] else g["home"]
                mp, sr = float(np.mean(s["ppa"])), float(np.mean(s["sr"])) if s["sr"] else 0.4
                rows.append(dict(game_id=gid, week=g["week"], off=team, def_=opp,
                                 home=(0 if g["neutral"] else (1 if team == g["home"] else 0)),
                                 n=len(s["ppa"]), ppa=round(mp, 4), sr=round(sr, 4),
                                 D=round(c_ppa * PLAYS_PG * mp + c_sr * sr, 3), st=round(s["st"], 3)))
    return rows


def load_obs(season: int, games: list[dict] | None = None, rebuild: bool = False, refresh: bool = False) -> list[dict]:
    OUT.mkdir(exist_ok=True)
    path = OUT / f"eff_obs_{season}.json"
    if path.exists() and not rebuild and not refresh:
        return json.loads(path.read_text(encoding="utf-8"))
    if games is None:
        import backtest as bt
        games = bt.load_games(season, bt.load_prior(season))
    rows = build_obs(season, games, refresh)
    path.write_text(json.dumps(rows), encoding="utf-8")
    return rows


def solve(prior: dict[str, float], obs: list[dict], lam: float = LAM, lam_st: float = LAM_ST,
          hfa: float = HFA, cap: float | None = None, scale: float = SCALE) -> dict[str, dict]:
    """{team: {off, def, st, combined}} for every prior team from the
    observations given (the caller filters to weeks < w)."""
    teams = sorted(prior)
    idx = {t: i for i, t in enumerate(teams)}
    m = len(teams)
    p = np.array([prior[t] for t in teams])
    out_zero = {t: dict(off=round(prior[t] / 2, 2), def_=round(prior[t] / 2, 2), st=0.0, combined=round(prior[t], 2)) for t in teams}
    obs = [o for o in obs if o["off"] in idx and o["def_"] in idx]
    if not obs:
        return out_zero
    n = len(obs)
    X = np.zeros((n, 2 * m))
    oi = np.array([idx[o["off"]] for o in obs]); di = np.array([idx[o["def_"]] for o in obs])
    X[np.arange(n), oi] = 1.0
    X[np.arange(n), m + di] = -1.0
    h = np.array([o["home"] for o in obs], dtype=float) * hfa
    y = np.array([o["D"] for o in obs]) * scale
    p2 = np.concatenate([p / 2, p / 2])
    mu = float(np.mean(y - (X @ p2 + h)))      # league offense level not carried by the prior
    resid = y - (X @ p2 + h) - mu
    if cap is not None:
        resid = np.clip(resid, -cap, cap)
    d = np.linalg.solve(X.T @ X + lam * np.eye(2 * m), X.T @ resid)
    off, de = p / 2 + d[:m], p / 2 + d[m:]
    # special teams: net ST ppa margin per game, prior 0
    Xs = np.zeros((n, m)); ys = np.array([o["st"] for o in obs])
    Xs[np.arange(n), oi] = 1.0; Xs[np.arange(n), di] = -1.0
    st = np.linalg.solve(Xs.T @ Xs + lam_st * np.eye(m), Xs.T @ ys) / 2.0   # each game appears from both sides
    return {t: dict(off=round(float(off[i]), 2), def_=round(float(de[i]), 2), st=round(float(st[i]), 2),
                    combined=round(float(off[i] + de[i] + st[i]), 2)) for t, i in idx.items()}


def predict_margin(r: dict, home: str, away: str, neutral: bool, hfa: float = HFA) -> float:
    H, A = r[home], r[away]
    return (H["off"] - A["def_"]) - (A["off"] - H["def_"]) + (H["st"] - A["st"]) + (0.0 if neutral else hfa)


class EfficiencyModel:
    """backtest.py plug-in: callable(ctx, week) -> {game_id: (margin, p_home)}."""

    def __init__(self, lam=LAM, lam_st=LAM_ST, hfa=HFA, cap=None, blend=0.0, scale=SCALE, desc=""):
        self.lam, self.lam_st, self.hfa, self.cap, self.blend, self.scale = lam, lam_st, hfa, cap, blend, scale
        self.desc = desc or f"efficiency ridge lam {lam} st {lam_st} hfa {hfa}" + (f" blended {blend:g} with current" if blend else "")
        self._obs = {}

    def obs(self, season):
        if season not in self._obs:
            self._obs[season] = load_obs(season)
        return self._obs[season]

    def __call__(self, ctx, week):
        rows = np.flatnonzero(ctx.week == week)
        if not len(rows):
            return {}
        r = solve(ctx.prior, [o for o in self.obs(ctx.season) if o["week"] < week], self.lam, self.lam_st, self.hfa, self.cap, self.scale)
        m = np.array([predict_margin(r, ctx.games[i]["home"], ctx.games[i]["away"], ctx.games[i]["neutral"], self.hfa) for i in rows])
        if self.blend:
            import backtest as bt
            cur = bt.ridge_predict(ctx, week, bt.MODELS["current"])
            m = (1 - self.blend) * m + self.blend * np.array([cur[ctx.games[i]["id"]][0] for i in rows])
        p = ctx.curve(week).win_prob(m)
        return {ctx.games[i]["id"]: (float(mm), float(pp)) for i, mm, pp in zip(rows, m, p)}


# ---------------- 2026 weekly shadow ----------------

def shadow_week(week: int, refresh: bool = False, write: bool = True) -> dict:
    import backtest as bt
    from refresh_all import load_fpi_2026
    prior = load_fpi_2026()
    games = bt.load_games(2026, prior)
    obs = load_obs(2026, games, rebuild=True, refresh=refresh)
    before = [o for o in obs if o["week"] < week]
    r = solve(prior, before)
    cur = {row["team"]: row for row in json.loads((HERE / "ratings_current_2026.json").read_text(encoding="utf-8"))["teams"]}
    rank_s = {t: i + 1 for i, t in enumerate(sorted(r, key=lambda t: -r[t]["combined"]))}
    rank_c = {t: i + 1 for i, t in enumerate(sorted(cur, key=lambda t: -cur[t]["cur"]))}
    teams = [dict(team=t, shadow=r[t]["combined"], off=r[t]["off"], def_=r[t]["def_"], st=r[t]["st"], shadow_rank=rank_s[t],
                  machine=cur.get(t, {}).get("cur"), machine_rank=rank_c.get(t), pre=round(prior[t], 1),
                  gp=sum(1 for o in before if o["off"] == t)) for t in sorted(r, key=lambda t: rank_s[t])]
    out = dict(week=week, as_of=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), status="SHADOW - not on air",
               params=dict(lam=LAM, lam_st=LAM_ST, hfa=HFA, scale=SCALE, plays_pg=PLAYS_PG, garbage=GARBAGE), obs_used=len(before), teams=teams)
    if write:
        (HERE / "internal").mkdir(exist_ok=True)
        (HERE / "internal" / f"shadow_ratings_week{week}.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


def write_shadow_sheet(book: Path, week: int | None = None) -> None:
    """'Shadow Ratings' sheet in the workbook from the latest internal/shadow_ratings_week*.json.
    Never breaks a refresh: any failure is printed and swallowed by the caller."""
    from openpyxl import load_workbook
    from openpyxl.styles import Font, PatternFill
    files = sorted((HERE / "internal").glob("shadow_ratings_week*.json"), key=lambda p: int(p.stem.rsplit("week", 1)[1]))
    if week is not None:
        files = [f for f in files if f.stem.endswith(f"week{week}")]
    if not files:
        print("shadow sheet: no shadow_ratings_week*.json yet"); return
    d = json.loads(files[-1].read_text(encoding="utf-8"))
    wb = load_workbook(book, keep_vba=True)
    if "Shadow Ratings" in wb.sheetnames:
        del wb["Shadow Ratings"]
    ws = wb.create_sheet("Shadow Ratings")
    ws["A1"] = f"SHADOW RATINGS - play-level efficiency (Phase 1) - before week {d['week']} - NOT ON AIR"
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"] = ("Offense / defense / special teams in points above an average FBS team; prior = ESPN preseason FPI split "
                "evenly; garbage time filtered. Graded next to the on-air machine in internal/BACKTEST_2026.md.")
    hdr = ["Shadow rank", "Team", "Shadow rating", "Offense", "Defense", "Special teams", "Machine (on air)", "Machine rank",
           "Shadow - machine", "Preseason FPI", "Games"]
    for j, h in enumerate(hdr, 1):
        c = ws.cell(row=4, column=j, value=h); c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F3864")
    for i, t in enumerate(d["teams"], 5):
        vals = [t["shadow_rank"], t["team"], t["shadow"], t["off"], t["def_"], t["st"], t["machine"], t["machine_rank"],
                (round(t["shadow"] - t["machine"], 1) if t["machine"] is not None else None), t["pre"], t["gp"]]
        for j, v in enumerate(vals, 1):
            ws.cell(row=i, column=j, value=v)
    ws.freeze_panes = "C5"
    ws.auto_filter.ref = f"A4:K{4 + len(d['teams'])}"
    for col, w in zip("ABCDEFGHIJK", (11, 22, 13, 10, 10, 13, 16, 13, 16, 13, 8)):
        ws.column_dimensions[col].width = w
    wb.save(book)
    print(f"shadow sheet written: {len(d['teams'])} teams, before week {d['week']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, help="2026: shadow ratings BEFORE this week")
    ap.add_argument("--season", type=int, help="rebuild one season's observation cache")
    ap.add_argument("--rebuild", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--sheet", action="store_true", help="also write the Shadow Ratings sheet into the workbook")
    a = ap.parse_args()
    from refresh_all import load_env_key
    load_env_key()
    if a.season:
        rows = load_obs(a.season, rebuild=True, refresh=a.refresh)
        print(f"{a.season}: {len(rows)} team-game observations, mean D {np.mean([r['D'] for r in rows]):.2f}, "
              f"mean plays {np.mean([r['n'] for r in rows]):.1f}")
    if a.week:
        out = shadow_week(a.week, refresh=a.refresh)
        print(f"SHADOW ratings before week {a.week} ({out['obs_used']} team-game sides) - not on air")
        print(f"{'':4} {'team':22} {'shadow':>7} {'off':>6} {'def':>6} {'st':>5} | {'machine':>8} {'rk':>3}")
        for t in out["teams"][:25]:
            print(f"{t['shadow_rank']:3d}. {t['team']:22} {t['shadow']:7.1f} {t['off']:6.1f} {t['def_']:6.1f} {t['st']:5.1f} | "
                  f"{t['machine'] if t['machine'] is not None else float('nan'):8.1f} {t['machine_rank'] or 0:3d}")
        print(f"wrote internal/shadow_ratings_week{a.week}.json")
        if a.sheet:
            write_shadow_sheet(HERE / "NCAA_FBS_Teams.xlsm", a.week)
