"""doctor.py - preflight for the show: every number that can go stale or drift, checked before it reaches a slide.

    python doctor.py --week N              # the card week (N = the week being previewed)
    python doctor.py --week N --recording  # recording-day mode: the frozen card and the deck file are required
    python doctor.py --week N --strict     # exit 1 on WARN as well as FAIL

Checks (PASS / WARN / FAIL, written to internal/doctor_weekN.md):
  1. make_episode_deck.py EPISODE, WEEK match the week.
  2. The published card exists and is fresh; the frozen card exists on recording day.
  3. Frozen card vs live ratings: a game whose live margin has drifted 1+ points from the freeze (a midweek final,
     a QB-out change) is flagged - the notes' 'The number' lines must say what the slide says.
  4. Stat packages: present for every card team and built from EVERY game the team has played (the Week 5
     Stockton bug: a cached season line showed 38-of-45 instead of 77-of-102).
  5. Availability: expired manual entries still on file; the QB-out points in force.
  6. ratings_current_2026.json: solved recently, from every completed rated game.
  7. Notes: the week's games file exists and its 'The number' lines match the card.
  8. Workbook: no formula on the Matchup sheet carries an unsubstituted {placeholder} (the 10/9 bug that made
     Excel refuse to open the file).
  9. Tale of the Tape data is through the last full week.
 10. Recording day: the deck file exists and is newer than the frozen card.
Nothing here changes a number. Wired into recording.py (step 0) and tuesday.py.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

INTERNAL = HERE / "internal"
NUMBER_LINE = re.compile(r"- The number: (.+?) [−-]([\d.]+), (\d+)% · Call")


class Report:
    def __init__(self):
        self.rows: list[tuple[str, str, str]] = []

    def add(self, level: str, check: str, detail: str = ""):
        self.rows.append((level, check, detail))
        print(f"[{level:4s}] {check}" + (f" - {detail}" if detail else ""))

    ok = lambda self, c, d="": self.add("PASS", c, d)      # noqa: E731
    warn = lambda self, c, d="": self.add("WARN", c, d)    # noqa: E731
    fail = lambda self, c, d="": self.add("FAIL", c, d)    # noqa: E731

    def counts(self):
        return {k: sum(1 for r in self.rows if r[0] == k) for k in ("PASS", "WARN", "FAIL")}


def _age_days(p: Path) -> float:
    return (time.time() - p.stat().st_mtime) / 86400.0


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def run(week: int, recording: bool = False) -> Report:
    R = Report()
    from routine import card_teams_from_deck
    pairs, ep, wk = card_teams_from_deck()

    # 1 deck constants
    if wk == week:
        R.ok("deck constants", f"EPISODE, WEEK = {ep}, {wk}; {len(pairs)} games in GAMES")
    else:
        R.fail("deck constants", f"make_episode_deck.py says WEEK = {wk}, you asked for {week} - fix EPISODE, WEEK and GAMES first")

    # 2 card files
    pub = HERE / f"card_data_week{week}.json"
    frz = HERE / f"card_data_week{week}_frozen.json"
    if pub.exists():
        age = _age_days(pub)
        (R.ok if age < 3 else R.warn)("published card", f"{pub.name} is {age:.1f} days old")
    else:
        R.fail("published card", f"{pub.name} missing - run edge_report.py --week {week} --view ml --publish")
    card_src = frz if frz.exists() else pub
    if recording:
        (R.ok if frz.exists() else R.fail)("frozen card", f"{frz.name} {'present' if frz.exists() else 'missing - run freeze_card.py'}")

    # 3 frozen vs live
    card = {}
    if card_src.exists():
        try:
            cd = _load(card_src)
            card = {(normalize_name(g["away"]), normalize_name(g["home"])): g for g in cd["games"]}
            rc = _load(HERE / "ratings_current_2026.json")
            cur = {t["team"]: t["cur"] for t in rc["teams"]}
            hfa = rc["params"]["hfa"]
            drift = []
            for a, h in pairs:
                g = card.get((normalize_name(a), normalize_name(h)))
                if not g or normalize_name(a) not in cur or normalize_name(h) not in cur:
                    continue
                live = cur[normalize_name(h)] - cur[normalize_name(a)] + (0.0 if g.get("neutral") else hfa)
                if abs(live - g["model_margin"]) >= 1.0:
                    drift.append(f"{a} at {h}: card {g['model_margin']:+.1f}, live {live:+.1f}")
            if frz.exists():
                (R.ok if not drift else R.warn)("frozen vs live", "; ".join(drift) if drift else "every card game within a point of the live ratings")
            else:
                (R.ok if not drift else R.warn)("published vs live", "; ".join(drift) if drift else "every card game within a point of the live ratings")
        except Exception as e:  # noqa: BLE001
            R.warn("frozen vs live", f"could not compare: {e}")

    # 4 stat packages
    sp = HERE / f"stat_package_week{week}.json"
    if sp.exists():
        try:
            import inseason_ratings as ir
            games = ir.completed_games_2026()
            played = {}
            for g in games:
                if (g["week"] or 0) < week:
                    played[g["home"]] = played.get(g["home"], 0) + 1
                    played[g["away"]] = played.get(g["away"], 0) + 1
            pk = {normalize_name(x["team"]): x for x in _load(sp)}
            missing = [t for pr in pairs for t in pr if normalize_name(t) not in pk]
            stale = []
            for pr in pairs:
                for t in pr:
                    x = pk.get(normalize_name(t))
                    if x and len(x.get("games", [])) != played.get(normalize_name(t), 0):
                        stale.append(f"{t}: package has {len(x.get('games', []))} games, {played.get(normalize_name(t), 0)} played")
            age = _age_days(sp)
            if missing:
                R.fail("stat packages", f"missing: {', '.join(missing)} - run stat_package.py --week {week} --teams ... --refresh")
            elif stale:
                R.fail("stat packages", "; ".join(stale) + " - rerun with --refresh")
            else:
                (R.ok if age < 3 else R.warn)("stat packages", f"all {len(pairs) * 2} card teams present with every game; file {age:.1f} days old")
        except Exception as e:  # noqa: BLE001
            R.warn("stat packages", f"could not check: {e}")
    else:
        (R.fail if recording else R.warn)("stat packages", f"{sp.name} missing")

    # 5 availability
    av = INTERNAL / "availability.json"
    if av.exists():
        rows = _load(av)
        expired = [f"{e['team']} {e['player']} (return {e['return']})" for e in rows if e.get("return") is not None and int(e["return"]) <= week]
        qb_out = [f"{e['team']} {e['player']} {e.get('points') if e.get('points') is not None else 'default'} pts" for e in rows
                  if str(e.get("pos", "")).upper() == "QB" and e.get("status") == "out" and (e.get("return") is None or int(e["return"]) > week)]
        (R.ok if not expired else R.warn)("availability expiries", ("; ".join(expired) + " - the layer already ignores them; clear them or extend the return week if the player is still out") if expired else f"{len(rows)} entries, none expired")
        R.ok("QB-out in force", "; ".join(qb_out) if qb_out else "none")
    else:
        R.warn("availability", "internal/availability.json missing")

    # 6 ratings receipt
    rcp = HERE / "ratings_current_2026.json"
    if rcp.exists():
        rc = _load(rcp)
        asof = dt.datetime.fromisoformat(rc["as_of"].replace("Z", "+00:00"))
        age = (dt.datetime.now(dt.timezone.utc) - asof).total_seconds() / 86400
        try:
            import inseason_ratings as ir
            prior = {t["team"] for t in rc["teams"]}
            n = sum(1 for g in ir.completed_games_2026() if g["home"] in prior and g["away"] in prior)
            if n != rc["games_used"]:
                R.warn("ratings receipt", f"solved {age:.1f} days ago from {rc['games_used']} games; the cache now has {n} rated games - refresh before the card")
            else:
                (R.ok if age < 3 else R.warn)("ratings receipt", f"solved {age:.1f} days ago from all {n} rated games")
        except Exception as e:  # noqa: BLE001
            R.warn("ratings receipt", f"could not compare: {e}")
    else:
        R.fail("ratings receipt", "ratings_current_2026.json missing")

    # 7 notes
    notes = sorted((HERE / "notes").glob(f"week{week}_ep*_games.md"))
    if notes and card:
        txt = notes[-1].read_text(encoding="utf-8")
        mism = []
        n_found = 0
        for m in NUMBER_LINE.finditer(txt):
            fav, line = m.group(1).strip(), float(m.group(2))
            n_found += 1
            g = next((g for g in card.values() if fav in (g["home"], g["away"])), None)
            if not g:
                continue
            cfav = g["home"] if g["model_margin"] >= 0 else g["away"]
            cline = abs(g["model_margin"])
            if cfav != fav or abs(cline - line) > 0.05:
                mism.append(f"{g['away']} at {g['home']}: notes say {fav} -{line:.1f}, card says {cfav} -{cline:.1f}")
        if n_found == 0:
            R.warn("notes numbers", f"{notes[-1].name}: no 'The number' lines found")
        else:
            (R.ok if not mism else R.warn)("notes numbers", "; ".join(mism) if mism else f"{notes[-1].name}: {n_found} 'The number' lines match the card")
    elif not notes:
        (R.warn if recording else R.ok)("notes", f"no notes/week{week}_ep*_games.md yet")

    # 8 workbook formulas
    book = HERE / "NCAA_FBS_Teams.xlsm"
    try:
        import openpyxl
        wb = openpyxl.load_workbook(book, read_only=True, keep_vba=False)
        bad = []
        if "Matchup" in wb.sheetnames:
            for row in wb["Matchup"].iter_rows(values_only=False):
                for c in row:
                    v = c.value
                    if isinstance(v, str) and v.startswith("=") and ("{" in v or "}" in v):
                        bad.append(c.coordinate)
            (R.ok if not bad else R.fail)("workbook formulas", ("placeholders in " + ", ".join(bad[:8])) if bad else "Matchup sheet formulas clean")
        else:
            R.warn("workbook formulas", "no Matchup sheet in the workbook")
        wb.close()
    except Exception as e:  # noqa: BLE001
        R.warn("workbook formulas", f"could not open the workbook: {e}")

    # 9 tape data
    td = HERE / "tape_data_2026.json"
    if td.exists():
        d = _load(td)
        (R.ok if d.get("through_week") == week - 1 else R.warn)("tale of the tape", f"data through week {d.get('through_week')} (card week {week}); updated {d.get('as_of', '')[:10]}")
    else:
        R.warn("tale of the tape", "tape_data_2026.json missing - python tape.py --data")

    # 10 deck file
    if recording:
        deck = HERE / "decks" / f"2026_Week{week}_Episode{ep}.pptx"
        if deck.exists() and frz.exists():
            (R.ok if deck.stat().st_mtime >= frz.stat().st_mtime else R.warn)("deck file", f"{deck.name} {'newer than' if deck.stat().st_mtime >= frz.stat().st_mtime else 'OLDER than'} the frozen card")
        else:
            R.warn("deck file", f"{deck.name} {'present' if deck.exists() else 'missing'}")
    return R


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--recording", action="store_true")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    R = run(a.week, a.recording)
    c = R.counts()
    INTERNAL.mkdir(exist_ok=True)
    out = INTERNAL / f"doctor_week{a.week}.md"
    lines = [f"# doctor - week {a.week}{' (recording)' if a.recording else ''} - {dt.datetime.now().isoformat(timespec='minutes')}", "",
             f"PASS {c['PASS']} · WARN {c['WARN']} · FAIL {c['FAIL']}", ""]
    lines += [f"- **{lvl}** {chk}" + (f": {det}" if det else "") for lvl, chk, det in R.rows]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nPASS {c['PASS']} · WARN {c['WARN']} · FAIL {c['FAIL']}  -> {out.relative_to(HERE)}")
    return 1 if c["FAIL"] or (a.strict and c["WARN"]) else 0


if __name__ == "__main__":
    sys.exit(main())
