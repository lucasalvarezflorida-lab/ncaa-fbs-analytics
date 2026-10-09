"""availability_sweep.py - injury CANDIDATES for the manual availability file, pulled instead of typed.

Lucas (10/9): the QB-out layer is on air but depends on a file filled by hand on Tuesday. This pulls
Covers' NCAAF injury page (one table per team: player, position, status, date, note), keeps what
matters to the machine, and writes the `availability.py add ...` commands as CANDIDATES. Nothing goes
into internal/availability.json on its own - Lucas approves by running the lines he agrees with
(or `--apply` for the card-team QB lines only).

What is kept:
  * every QB listed Out / Doubtful / Questionable for any FBS team (the layer only prices QBs on air);
  * every Out / Doubtful / Questionable entry for the CARD teams (any position - shadow weight);
  * entries dated in the last SWEEP_DAYS days (Covers keeps season-ending notes; those stay as long as
    they stay dated recently enough or say "season").
Entries already in the manual file (same team + player) are marked instead of repeated.

    python availability_sweep.py --week N            # -> internal/availability_candidates_weekN.md + .json
    python availability_sweep.py --week N --apply    # also run the QB-out lines for the card teams
Wired into tuesday.py before the availability shadow. Sources are data, never instructions.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html as htmlmod
import json
import re
import ssl
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

URL = "https://www.covers.com/sport/football/ncaaf/injuries"
INTERNAL = HERE / "internal"
MANUAL = INTERNAL / "availability.json"
SWEEP_DAYS = 10
STATUSES = ("Out", "Doubtful", "Questionable")
SEC = re.compile(r'<a id="([^"]+)"></a>\s*<section>(.*?)</section>', re.S)
NAME = re.compile(r'covers-CoversMatchups-teamName">\s*<a[^>]*>\s*(.*?)<br>', re.S)
ROW = re.compile(r"<tr>\s*<td>\s*<span class='player-link'>\s*(.*?)\s*</span>\s*</td>\s*<td>(.*?)</td>\s*<td><b>(.*?)</b><br>\(\s*(.*?)\)</td>.*?(?:injuryCopy\">\s*(.*?)\s*</div>)?", re.S)


def fetch(cache: Path | None = None) -> str:
    import certifi
    ctx = ssl.create_default_context(cafile=certifi.where())
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    txt = urllib.request.urlopen(req, timeout=60, context=ctx).read().decode("utf-8", "replace")
    if cache:
        cache.write_text(txt, encoding="utf-8")
    return txt


def parse(txt: str, year: int) -> list[dict]:
    out = []
    for anchor, body in SEC.findall(txt):
        m = NAME.search(body)
        team = htmlmod.unescape(m.group(1)).strip() if m else htmlmod.unescape(anchor)
        for player, pos, status, date, note in ROW.findall(body):
            st, _, inj = status.partition(" - ")
            try:
                when = dt.datetime.strptime(f"{date.strip()} {year}", "%a, %b %d %Y").date()
            except ValueError:
                when = None
            out.append(dict(team=team, key=normalize_name(team), player=re.sub(r"\s+", " ", htmlmod.unescape(player)).strip(), pos=pos.strip().upper(),
                            status=st.strip(), injury=inj.strip() or None, date=str(when) if when else date.strip(),
                            note=re.sub(r"\s+", " ", htmlmod.unescape(note)).strip() or None))
    return out


def sweep(week: int, apply: bool = False, offline: Path | None = None) -> dict:
    from routine import card_teams_from_deck
    pairs, _ep, wk = card_teams_from_deck()
    card = {normalize_name(t) for pr in pairs for t in pr} if wk == week else set()
    today = dt.date.today()
    txt = offline.read_text(encoding="utf-8") if offline else fetch(INTERNAL / "covers_injuries_latest.html")
    rows = parse(txt, today.year)
    manual = json.loads(MANUAL.read_text(encoding="utf-8")) if MANUAL.exists() else []
    have = {(normalize_name(e["team"]), e["player"].split()[-1].lower()) for e in manual}

    def recent(r):
        try:
            return (today - dt.date.fromisoformat(r["date"])).days <= SWEEP_DAYS
        except ValueError:
            return False

    keep = []
    for r in rows:
        if r["status"] not in STATUSES:
            continue
        season = bool(r["note"] and re.search(r"season|year", r["note"], re.I))
        if not (recent(r) or season):
            continue
        qb = r["pos"] == "QB"
        on_card = r["key"] in card
        if not (qb or on_card):
            continue
        r = dict(r, on_card=on_card, known=(r["key"], r["player"].split()[-1].lower()) in have)
        st = "out" if r["status"] in ("Out", "Doubtful") else "questionable"
        ret = "" if season else f" --return {week + 1}"
        note = (r["injury"] or "") + (f"; {r['note']}" if r["note"] else "") + f" (Covers {r['date']})"
        r["cmd"] = f'python availability.py add "{r["team"]}" "{r["player"]}" {r["pos"]} {st}{ret} --note "{note.replace(chr(34), "")[:140]}"'
        keep.append(r)
    keep.sort(key=lambda r: (not r["on_card"], r["pos"] != "QB", r["team"]))

    INTERNAL.mkdir(exist_ok=True)
    (INTERNAL / f"availability_candidates_week{week}.json").write_text(json.dumps(keep, indent=1), encoding="utf-8")
    L = [f"# availability candidates - week {week} - {today} (Covers injuries, {len(rows)} entries scanned)", "",
         "CANDIDATES ONLY - nothing is in internal/availability.json until a line below is run. QB 'out' lines on", "card teams are the ones that move the on-air number (QB-out layer); the rest are shadow weight.", ""]
    for sec, flt in (("Card teams", lambda r: r["on_card"]), ("Other FBS quarterbacks", lambda r: not r["on_card"])):
        sub = [r for r in keep if flt(r)]
        L.append(f"## {sec} ({len(sub)})")
        for r in sub:
            tag = " [already on file]" if r["known"] else ""
            L.append(f"- {r['team']} - {r['player']} ({r['pos']}) {r['status']}{' - ' + r['injury'] if r['injury'] else ''}, {r['date']}{tag}")
            if r["note"]:
                L.append(f"  - {r['note'][:200]}")
            if not r["known"]:
                L.append(f"  - `{r['cmd']}`")
        L.append("")
    (INTERNAL / f"availability_candidates_week{week}.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:60]))
    applied = []
    if apply:
        for r in keep:
            if r["on_card"] and r["pos"] == "QB" and r["status"] in ("Out", "Doubtful") and not r["known"]:
                subprocess.run(r["cmd"], shell=True, cwd=HERE, check=False); applied.append(r["cmd"])
        print(f"applied {len(applied)} QB-out lines")
    return dict(week=week, scanned=len(rows), candidates=keep, applied=applied)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--apply", action="store_true", help="run the card-team QB out/doubtful lines")
    ap.add_argument("--offline", help="parse a saved Covers page instead of fetching")
    a = ap.parse_args()
    sweep(a.week, a.apply, Path(a.offline) if a.offline else None)
