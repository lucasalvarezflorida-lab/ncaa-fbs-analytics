"""Per-game OBSERVATION features from the cached play-by-play, for the
alternative observations backtest.py can feed the ridge (item 1 of the
9/27 enhancement list, Lucas):

  * turnover margin (home takeaways - home giveaways) and NON-OFFENSIVE points
    (turnover-return touchdowns, safeties; punt/kick-return and blocked-kick
    touchdowns kept separately) so the observed margin can be de-lucked:
        y_adj = margin - b_to * to_home - b_st * nonoff_net
  * net total PPA and net success rate from the same plays (all scrimmage
    plays, like CFBD's advanced box; and a garbage-time-filtered copy), so the
    frozen deserved-margin model (efficiency_model.json) can price a
    "deserved" margin for every game 2022-2026 without the advanced box:
        y_blend = w * margin + (1 - w) * deserved   (only when |margin - deserved| > T)

Cached per season in fpi-decomposition/output/obs_features_{season}.json
({game_id: {...}}); rebuild with build(season, games, rebuild=True).
Nothing here touches the on-air number: these are backtest inputs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

OUT = HERE / "fpi-decomposition" / "output"
GARBAGE = {1: 43, 2: 37, 3: 27, 4: 21}      # same rule as efficiency_ratings.py: lead past this by period = garbage
TURNOVER = {"Interception", "Pass Interception Return", "Interception Return Touchdown",
            "Fumble Recovery (Opponent)", "Fumble Return Touchdown"}
TO_RETURN_TD = {"Interception Return Touchdown", "Fumble Return Touchdown"}
ST_TD = {"Punt Return Touchdown", "Kickoff Return Touchdown", "Blocked Punt Touchdown", "Blocked Field Goal Touchdown"}
SKIP = ("Kickoff", "Punt", "Field Goal", "Timeout", "End", "Penalty", "Extra Point", "Two Point", "Uncategorized")
PASS = ("Pass", "Sack", "Interception")


def _scrim(p):
    t = p["playType"]
    return (("Rush" in t) or any(s in t for s in PASS) or t == "Fumble Recovery (Opponent)") and not any(s in t for s in SKIP)


def _success(p):
    d, x, y = p.get("down") or 0, p.get("distance") or 0, p.get("yardsGained") or 0
    if "Touchdown" in p["playType"] and "Return" not in p["playType"]:
        return True
    if d == 1:
        return y >= 0.5 * x
    if d == 2:
        return y >= 0.7 * x
    return y >= x


def _garbage(p):
    per = p.get("period") or 0
    lead = abs((p.get("offenseScore") or 0) - (p.get("defenseScore") or 0))
    return per in GARBAGE and lead > GARBAGE[per]


def build(season: int, games: list[dict], rebuild: bool = False) -> dict[int, dict]:
    """games = backtest.SeasonCtx.games (normalized home/away, id, week)."""
    OUT.mkdir(exist_ok=True)
    path = OUT / f"obs_features_{season}.json"
    if path.exists() and not rebuild:
        cached = {int(k): v for k, v in json.loads(path.read_text(encoding="utf-8")).items()}
        if all(g["id"] in cached for g in games):
            return cached                                    # a new week's games force a rebuild
    import cfbd_client as cfbd
    by_id = {g["id"]: g for g in games}
    acc: dict[int, dict] = {}
    for w in sorted({g["week"] for g in games}):
        try:
            plays = cfbd.get("/plays", {"year": season, "week": w, "seasonType": "regular"}, False)
        except Exception as e:  # a missing week file: those games fall back to the actual margin
            print(f"obs_features {season} wk{w}: no plays ({e})")
            continue
        for p in plays:
            gid = p.get("gameId")
            g = by_id.get(gid)
            if not g:
                continue
            off = normalize_name(p.get("offense") or ""); de = normalize_name(p.get("defense") or "")
            if off not in (g["home"], g["away"]) or de not in (g["home"], g["away"]):
                continue
            a = acc.setdefault(gid, dict(to_home=0, nonoff_home=0, nonoff_away=0, st_home=0, st_away=0,
                                         tppa_home=0.0, tppa_away=0.0, sr_home=[0, 0], sr_away=[0, 0],
                                         tppa_home_ng=0.0, tppa_away_ng=0.0, sr_home_ng=[0, 0], sr_away_ng=[0, 0], plays=0))
            side = "home" if off == g["home"] else "away"
            dside = "away" if side == "home" else "home"
            t = p["playType"]
            if t in TURNOVER:
                a["to_home"] += -1 if side == "home" else 1        # offense gave it away
            if t in TO_RETURN_TD:
                a[f"nonoff_{dside}"] += 7
            if t == "Safety":
                a[f"nonoff_{dside}"] += 2
            if t in ST_TD:
                a[f"st_{dside}"] += 7                               # CFBD lists the kicking/punting team as the offense
            if _scrim(p):
                a["plays"] += 1
                if p.get("ppa") is not None:
                    a[f"tppa_{side}"] += float(p["ppa"])
                    a[f"sr_{side}"][0] += _success(p); a[f"sr_{side}"][1] += 1
                    if not _garbage(p):
                        a[f"tppa_{side}_ng"] += float(p["ppa"])
                        a[f"sr_{side}_ng"][0] += _success(p); a[f"sr_{side}_ng"][1] += 1
    out = {}
    for gid, a in acc.items():
        sr = lambda k: (a[k][0] / a[k][1]) if a[k][1] else None
        if a["sr_home"][1] < 20 or a["sr_away"][1] < 20:
            continue
        out[gid] = dict(to_home=a["to_home"], nonoff_net=a["nonoff_home"] - a["nonoff_away"], st_net=a["st_home"] - a["st_away"],
                        net_tppa=a["tppa_home"] - a["tppa_away"], net_sr=sr("sr_home") - sr("sr_away"),
                        net_tppa_ng=a["tppa_home_ng"] - a["tppa_away_ng"],
                        net_sr_ng=((sr("sr_home_ng") or 0) - (sr("sr_away_ng") or 0)), plays=a["plays"])
    path.write_text(json.dumps(out), encoding="utf-8")
    return out


def deserved(f: dict, model: dict, garbage_filtered: bool = False) -> float:
    if garbage_filtered:
        return model["intercept"] + model["net_tppa"] * f["net_tppa_ng"] + model["net_sr"] * f["net_sr_ng"]
    return model["intercept"] + model["net_tppa"] * f["net_tppa"] + model["net_sr"] * f["net_sr"]


def adjust(margin: float, f: dict | None, spec: dict, model: dict | None) -> float:
    """One game's observation under spec:
       to   : points per turnover taken off the margin (home takeaway - giveaway)
       st   : weight on non-offensive points (turnover-return TDs + safeties), 1 = remove them
       kick : weight on punt/kick-return + blocked-kick TDs
       des_w: weight on the ACTUAL margin in the deserved blend (1 = off)
       des_T: blend only when |actual - deserved| exceeds T (0 = always)
       des_ng: use the garbage-filtered deserved
    """
    y = float(margin)
    if f is None:
        return y
    y -= spec.get("to", 0.0) * f["to_home"]
    y -= spec.get("st", 0.0) * f["nonoff_net"]
    y -= spec.get("kick", 0.0) * f["st_net"]
    w = spec.get("des_w", 1.0)
    if w < 1.0 and model is not None:
        d = deserved(f, model, spec.get("des_ng", False))
        if abs(float(margin) - d) > spec.get("des_T", 0.0):
            y = w * y + (1.0 - w) * d
    return y
