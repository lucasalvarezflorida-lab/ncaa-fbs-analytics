"""tape_data.py - the data file behind "Tale of the Tape" (tape/index.html), Lucas's
pick-two-teams matchup page (10/9: "FSU vs Miami at home, who would win and why?").

One JSON for every rated FBS team, built from what the machine already knows:
  * the on-air rating (ratings_current_2026.json: July prior, current, delta, rank, QB-out)
  * the efficiency shadow's offense / defense / special-teams split (internal/shadow_ratings_weekN.json,
    latest file) - the "plays" view, SHADOW, labelled as such on the page
  * team_stats_2026.json (the workbook's Team Stats: per-game offense / defense with FBS ranks)
  * the 2026 game log with each result graded against the CURRENT ratings (expected vs de-lucked
    margin, turnover margin from obs_features) - the resume
  * the production margin curve as a lookup table (margin -> home win probability) at the on-air sd
  * school colours and a small embedded logo (decks/logos cache, ESPN CDN on first use)

NO MARKET NUMBERS - the page is a presentable thing. Nothing here changes the on-air number.

    python tape_data.py            # -> tape_data_2026.json
    python tape.py                 # -> tape/index.html (template + data)
"""
from __future__ import annotations

import base64
import datetime as dt
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402
import inseason_ratings as ir  # noqa: E402
from margin_prob import load_curve  # noqa: E402

OUT = HERE / "tape_data_2026.json"
LOGO_DIR = HERE / "decks" / "logos"
LOGO_PX = 72

STAT_KEYS = [  # (key, label, higher-is-better-for-the-offense)
    ("ppg", "Points a game", True), ("ypp", "Yards a play", True), ("ypa", "Yards an attempt", True),
    ("rush_ypc", "Yards a carry", True), ("p20_rate", "20+ yd pass rate", True), ("r10_rate", "10+ yd run rate", True),
    ("stuff_rate", "Stuff rate", False), ("sack_rate", "Sack rate", False), ("t3_pct", "3rd down %", True),
    ("rz_pct", "Red zone TD %", True), ("turnovers", "Turnovers", False),
]


def slug(norm: str) -> str:
    return re.sub(r"[^a-z0-9]", "", norm)


def logo_data_uri(norm: str, url: str | None) -> str | None:
    """Small PNG as a data URI (the artifact CSP blocks every external image)."""
    p = LOGO_DIR / (slug(norm) + ".png")
    if not p.exists() and url:
        try:
            LOGO_DIR.mkdir(parents=True, exist_ok=True)
            req = urllib.request.Request(url.replace("http://", "https://"), headers={"User-Agent": "Mozilla/5.0"})
            p.write_bytes(urllib.request.urlopen(req, timeout=20).read())
        except Exception as e:  # noqa: BLE001
            print("logo fetch failed:", norm, e)
            return None
    if not p.exists():
        return None
    try:
        from PIL import Image
        im = Image.open(p).convert("RGBA")
        im.thumbnail((LOGO_PX, LOGO_PX))
        buf = io.BytesIO(); im.save(buf, "PNG", optimize=True)
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception as e:  # noqa: BLE001
        print("logo encode failed:", norm, e)
        return None


def latest_shadow() -> dict:
    files = sorted((HERE / "internal").glob("shadow_ratings_week*.json"), key=lambda p: int(p.stem.rsplit("week", 1)[1]))
    if not files:
        return {}
    d = json.loads(files[-1].read_text(encoding="utf-8"))
    return dict(week=d["week"], teams={t["team"]: t for t in d["teams"]})


def build() -> dict:
    cur = json.loads((HERE / "ratings_current_2026.json").read_text(encoding="utf-8"))
    rating = {t["team"]: t for t in cur["teams"]}
    rank = {t["team"]: i + 1 for i, t in enumerate(cur["teams"])}
    r_now = {t: v["cur"] for t, v in rating.items()}
    shadow = latest_shadow()
    stats = json.loads((HERE / "team_stats_2026.json").read_text(encoding="utf-8"))
    stats_by = {normalize_name(k): v for k, v in stats["teams"].items()}
    teams_meta = {normalize_name(t["school"]): t for t in json.loads((HERE / "rosters" / "data" / "teams_fbs_2026.json").read_text(encoding="utf-8"))}
    display = {normalize_name(t["school"]): t["school"] for t in teams_meta.values()}

    # game log, graded against the current ratings (same arithmetic as prior_weight.team_card)
    games = ir.completed_games_2026()
    week = ir.latest_full_week(games)
    to = ir.turnover_margins([g for g in games if g["home"] in rating and g["away"] in rating])
    hfa, to_pts, cap = ir.HFA, ir.RULE.get("to_pts", 0.0), ir.RULE.get("cap")
    log: dict[str, list] = {t: [] for t in rating}
    for g in sorted(games, key=lambda g: (g["week"] or 0)):
        for team, opp, home in ((g["home"], g["away"], True), (g["away"], g["home"], False)):
            if team not in rating:
                continue
            act = g["margin"] if home else -g["margin"]
            site = "neutral" if g["neutral"] else ("home" if home else "away")
            row = dict(wk=g["week"], opp=display.get(opp, opp.title()), opp_key=opp, site=site,
                       result=("W" if act > 0 else ("L" if act < 0 else "T")) + f" {int(abs(act))}", margin=act, rated=opp in rating)
            if opp in rating:
                h = 0.0 if g["neutral"] else (hfa if home else -hfa)
                exp = r_now[team] - r_now[opp] + h
                tom = to.get(g["id"], 0.0) * (1 if home else -1)
                dl = act - to_pts * tom
                resid = dl - exp
                row.update(opp_rank=rank[opp], opp_rating=round(r_now[opp], 1), expected=round(exp, 1), to=int(tom),
                           delucked=round(dl, 1), resid=round(max(-cap, min(cap, resid)) if cap else resid, 1))
            else:
                row.update(note="FCS - not rated, does not enter the machine")
            log[team].append(row)

    teams = {}
    for t, v in rating.items():
        meta = teams_meta.get(t, {})
        sh = shadow.get("teams", {}).get(t, {})
        st = stats_by.get(t, {})
        wins = sum(1 for r in log[t] if r["margin"] > 0); losses = sum(1 for r in log[t] if r["margin"] < 0)
        teams[t] = dict(
            key=t, name=display.get(t, t.title()), abbr=meta.get("abbreviation"), conf=meta.get("conference"),
            color=meta.get("color") or "#444444", alt=meta.get("alternateColor") or "#dddddd",
            logo=logo_data_uri(t, (meta.get("logos") or [None])[0]),
            record=f"{wins}-{losses}", rated_gp=v["gp"],
            july=v["pre"], now=v["cur"], delta=v["delta"], rank=rank[t], qb_out=v.get("qb_out", 0.0),
            eff=(dict(off=sh["off"], def_=sh["def_"], st=sh["st"], total=sh["shadow"], rank=sh["shadow_rank"]) if sh else None),
            stats=(dict(off={k: st["off"].get(k) for k, _, _ in STAT_KEYS} | {k + "_rk": st["off"].get(k + "_rk") for k, _, _ in STAT_KEYS},
                        def_={k: st["def_"].get(k) for k, _, _ in STAT_KEYS} | {k + "_rk": st["def_"].get(k + "_rk") for k, _, _ in STAT_KEYS},
                        gp=st.get("gp")) if st else None),
            games=log[t],
        )
    # league averages for the stat strip
    avg = {}
    for side in ("off", "def_"):
        avg[side] = {}
        for k, _, _ in STAT_KEYS:
            vals = [x["stats"][side][k] for x in teams.values() if x["stats"] and x["stats"][side].get(k) is not None]
            avg[side][k] = round(float(np.mean(vals)), 2) if vals else None
    # the production curve as a table
    sd = ir.sigma_for(1)
    curve = load_curve("model", sd=sd)
    margins = np.arange(-60, 60.5, 0.5)
    table = [[float(m), round(float(p), 4)] for m, p in zip(margins, curve.win_prob(margins))]
    return dict(
        as_of=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), through_week=week,
        rule=dict(hfa=hfa, to_pts=to_pts, cap=cap, lam=ir.RULE["lam"], sd=sd, mae="12.5"),
        shadow_week=shadow.get("week"), stat_keys=[[k, lab, hi] for k, lab, hi in STAT_KEYS], league=avg,
        curve=table, teams=teams,
    )


if __name__ == "__main__":
    d = build()
    OUT.write_text(json.dumps(d, separators=(",", ":")), encoding="utf-8")
    n_logo = sum(1 for t in d["teams"].values() if t["logo"])
    print(f"wrote {OUT.name}: {len(d['teams'])} teams, {n_logo} logos, through week {d['through_week']}, {OUT.stat().st_size // 1024} KB")
