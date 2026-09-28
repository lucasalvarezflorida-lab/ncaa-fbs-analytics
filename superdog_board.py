"""Superdog / Giant Killer board for a week, the same rule the deck uses
(make_episode_deck.superdog_boards): expected rulebook points
    5 x P(cover) + spread x P(win)
with P(win) = the margin curve at the dog's model margin and P(cover) at that
margin plus the points; dogs of 3.5 to 28; skip games where the machine is
15+ from the line; FBS-vs-FBS only; ties within a quarter point go to the
home dog. Giant Killer = an UNRANKED dog vs an AP Top 25 team.

    python superdog_board.py --week 5              -> prints the board, writes internal/superdog_board_week5.json
    python superdog_board.py --week 5 --ap-file internal/ap_week5.json   (when CFBD has not ingested the poll)

Reads card_data_week{N}.json (edge_report --publish), ratings_current_2026.json
(curve sd), the AP poll from CFBD's rankings cache (latest week <= N) or
--ap-file. INTERNAL until the picks are read on air.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

MIN_SPREAD, MAX_SPREAD, MAX_EDGE, TIE_PTS, COVER_PTS = 3.5, 28.0, 15.0, 0.25, 5.0


def ap_ranks(week: int, ap_file: str | None) -> tuple[dict, str]:
    if ap_file:
        d = json.loads(Path(ap_file).read_text(encoding="utf-8"))
        ranks = d["ranks"] if isinstance(d, dict) else d
        return {normalize_name(s): i for i, s in enumerate(ranks, 1)}, f"{ap_file}"
    import glob
    best, src = {}, "none"
    for f in sorted(glob.glob(str(HERE / "fpi-decomposition" / "data" / "rankings_*year-2026.json"))):
        m = re.search(r"week-(\d+)", f)
        w = int(m.group(1)) if m else 0
        if w > week:
            continue
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        for wk in d:
            for poll in wk.get("polls", []):
                if poll.get("poll") == "AP Top 25":
                    best, src = {normalize_name(r["school"]): r["rank"] for r in poll["ranks"]}, f"CFBD rankings week {w}"
    return best, src


def home_dog_tiebreak(rows):
    if not rows:
        return rows
    band = [r for r in rows if rows[0]["exp_pts"] - r["exp_pts"] <= TIE_PTS]
    home = [r for r in band if r["at"] == "vs"]
    if home and rows[0]["at"] != "vs":
        rows.remove(home[0]); rows.insert(0, home[0])
    return rows


def board(week: int, ap_file: str | None = None):
    from margin_prob import load_curve
    c = json.loads((HERE / f"card_data_week{week}.json").read_text(encoding="utf-8"))
    r = json.loads((HERE / "ratings_current_2026.json").read_text(encoding="utf-8"))
    curve = load_curve("model").rescaled(r["params"]["sigma"])
    ap, ap_src = ap_ranks(week, ap_file)
    fbs = set()
    for g in json.loads((HERE / "fpi-decomposition" / "data" / "games_seasonType-regular_year-2026.json").read_text(encoding="utf-8")):
        if g.get("homeClassification") == "fbs" and g.get("awayClassification") == "fbs":
            fbs.add(g["id"])
    rows = []
    for g in c["games"]:
        if g.get("game_id") not in fbs:
            continue
        b = g["books"].get("DraftKings") or g["books"].get("Bovada") or {}
        sp = b.get("spread")
        if sp is None or not MIN_SPREAD <= abs(sp) <= MAX_SPREAD:
            continue
        ph = g["model_p_home"]
        dog, fav, p = (g["away"], g["home"], 1 - ph) if sp < 0 else (g["home"], g["away"], ph)
        mm = g["model_margin"]
        edge = abs(sp) + (-mm if dog == g["away"] else mm)
        if edge >= MAX_EDGE:
            continue
        rows.append(dict(dog=dog, fav=fav, at=("at" if dog == g["away"] else "vs"), pts=abs(sp), p_win=round(p, 3),
                         p_cover=round(float(curve.win_prob(edge)), 3), model_margin_dog=round(-mm if dog == g["away"] else mm, 1),
                         fav_rank=ap.get(normalize_name(fav)), dog_rank=ap.get(normalize_name(dog)), date=g.get("date"),
                         ml=(b.get("away_ml") if dog == g["away"] else b.get("home_ml"))))
    for x in rows:
        x["exp_pts"] = round(COVER_PTS * x["p_cover"] + x["pts"] * x["p_win"], 2)
    rows.sort(key=lambda x: -x["exp_pts"])
    giant = home_dog_tiebreak([x for x in rows if x["fav_rank"] and not x["dog_rank"]])
    gk = giant[0] if giant else None
    any_rows = home_dog_tiebreak([x for x in rows if not gk or x is not gk])
    return dict(week=week, generated=dt.datetime.now().isoformat(timespec="minutes"), lines_as_of=c.get("lines_as_of"), ap_source=ap_src,
                giant_killer=gk, superdog=(any_rows[0] if any_rows else None), any_board=any_rows[:8], giant_board=giant[:8])


def line(x):
    tag = f" #{x['fav_rank']}" if x.get("fav_rank") else ""
    return f"{x['dog']} +{x['pts']:g} {x['at']}{tag} {x['fav']}  exp {x['exp_pts']:.2f}  P(cover) {x['p_cover']:.2f}  P(win) {x['p_win']:.2f}  machine {x['model_margin_dog']:+.1f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--ap-file")
    a = ap.parse_args()
    b = board(a.week, a.ap_file)
    (HERE / "internal").mkdir(exist_ok=True)
    out = HERE / "internal" / f"superdog_board_week{a.week}.json"
    out.write_text(json.dumps(b, indent=1), encoding="utf-8")
    print(f"superdog board week {a.week} (lines {b['lines_as_of']}, AP: {b['ap_source']})")
    print("GIANT KILLER:", line(b["giant_killer"]) if b["giant_killer"] else "none")
    print("SUPERDOG:    ", line(b["superdog"]) if b["superdog"] else "none")
    print("next, any game:"); [print("   ", line(x)) for x in b["any_board"][1:5]]
    print("next, vs Top 25:"); [print("   ", line(x)) for x in b["giant_board"][1:5]]
    print(f"wrote {out.relative_to(HERE)}")


if __name__ == "__main__":
    main()
