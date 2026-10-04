"""TUESDAY orchestrator - after the 7:30 AM scheduled refresh has run.

    python tuesday.py --week 5          # 5 = the upcoming card's week

Steps: (0) refresh only if the ratings file is older than today, (1) AP poll
check, (2) hot seat + Heisman (MARKET by hand first), (3) edge report publish
(Tuesday lines, not frozen), (4) superdog board, (5) old-rule shadow,
(6) availability shadow (add injury news first: availability.py add ...),
(7) stat packages for the card teams (from make_episode_deck GAMES),
(8) playoff summary. Summary in internal/tuesday_week{N}.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from routine import Runner, ap_check, card_teams_from_deck  # noqa: E402

PY = sys.executable


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True, help="the upcoming card's week")
    ap.add_argument("--refresh", action="store_true", help="force refresh_all --no-rosters")
    a = ap.parse_args()
    n = a.week
    R = Runner("tuesday", n)
    rp = HERE / "ratings_current_2026.json"
    stale = True
    if rp.exists():
        as_of = json.loads(rp.read_text(encoding="utf-8")).get("as_of", "")
        stale = not as_of.startswith(dt.date.today().isoformat())
    if a.refresh or stale:
        R.step("0 refresh (no rosters) — ratings were not from today", [PY, "refresh_all.py", "--no-rosters", "--wait-for-unlock"], tail=8, timeout=3600)
    else:
        R.note("## 0 refresh — skipped (ratings already from today: " + as_of + ")")
    R.note("## 1 AP poll\n" + ap_check(n))
    R.note("> MARKET / MARKET_DATE in hot_seat_heisman.py by hand first (DraftKings via Covers).")
    R.step(f"2 hot seat + Heisman week {n}", [PY, "hot_seat_heisman.py", "--week", str(n), "--refresh"], tail=30)
    R.step(f"3 edge report week {n} (publish, not frozen)", [PY, "edge_report.py", "--week", str(n), "--view", "ml", "--publish"], tail=45)
    R.step(f"4 superdog board week {n}", [PY, "superdog_board.py", "--week", str(n)], tail=12)
    R.step(f"5 old-rule shadow week {n}", [PY, "turnover_shadow.py", "--week", str(n)], tail=30)
    R.note("> Injury news goes in first: `python availability.py add \"Team\" \"Player\" QB out --return N --note \"...\"`")
    R.step(f"6 availability shadow week {n}", [PY, "availability.py", "--week", str(n)], tail=20)
    pairs, ep, wk = card_teams_from_deck()
    if pairs and wk == n:
        teams = ",".join(t for p in pairs for t in p)
        R.step(f"7 stat packages ({len(pairs)} games)", [PY, "stat_package.py", "--week", str(n), "--teams", teams, "--refresh"], tail=6)
    else:
        R.note(f"## 7 stat packages — skipped: make_episode_deck.py GAMES is week {wk}, not {n} (set the card first)")
    R.py("8 playoff sim summary", f"""
import json
ps = json.load(open(r'{HERE / "internal" / f"playoff_sim_week{n}.json"}'))['teams']
rows = sorted(ps, key=lambda v: -v['playoff'])
print(' · '.join(f"{{v['team']}} {{v['playoff']*100:.0f}}%" for v in rows[:16]))
""", tail=3)
    R.note(f"\n## Next\n- Re-run `notes_skeleton.py --week {n} --ep {ep} --games ...` if the stat packages changed; refresh the notes' numbers; OneNote with -Prefix \"Week {n} - \".\n- Corey's slides -> his sections in the boards notes, score_tracker man calls, ledger.")
    R.finish()


if __name__ == "__main__":
    main()
