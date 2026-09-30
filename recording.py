"""RECORDING-DAY orchestrator - everything up to the push, which stays on Lucas's word.

    python recording.py --week 5

Steps: (1) edge_report publish (the pre-record pull), (2) freeze_card,
(3) stat packages for the card teams, (4) pre-mortems, (5) totals-model
shadow score call, (6) availability shadow, (7) make_episode_deck,
(8) deck_lint, (9) review-before-air candidates (the extreme per-attempt /
stuff / sack numbers in the stat package), (10) the machine numbers that
must match the notes. Summary in internal/recording_week{N}.md.
Then, on Lucas's word only: push_deck.py to the episode's Slides file. NO merged
file since 9/30: Lucas imports our slides into Corey's deck himself; Corey's deck
is exported READ-ONLY only to read his calls / boards / superdogs.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from routine import Runner, card_teams_from_deck  # noqa: E402

PY = sys.executable
TOTALS_CALIB = "16.22,0.665"   # TOTALS_2026.md


def review_candidates(week: int, pairs) -> str:
    p = HERE / f"stat_package_week{week}.json"
    if not p.exists():
        return "no stat package"
    pk = {x["team"]: x for x in json.loads(p.read_text(encoding="utf-8"))}
    teams = [t for pr in pairs for t in pr if t in pk]
    rows = []
    for t in teams:
        o, d, of, df = pk[t]["offense"], pk[t]["defense"], pk[t]["offense_vs_fbs"], pk[t]["defense_vs_fbs"]
        rows.append((abs(o["ypa"] - 8.0), f"{t} offense {o['ypa']} a throw (vs FBS {of['ypa']})"))
        rows.append((abs(d["ypa"] - 7.0), f"{t} defense {d['ypa']} a throw allowed (vs FBS {df['ypa']})"))
        rows.append((abs(o["box_ypc"] - 4.5) * 2, f"{t} rush {o['box_att']}-{o['box_yds']} ({o['box_ypc']}) — box score"))
        rows.append((abs(d["box_ypc"] - 4.0) * 2, f"{t} run D {d['box_att']}-{d['box_yds']} ({d['box_ypc']}) — box score"))
        rows.append((abs(d["sack_rate"] - 6.5) / 2, f"{t} sack rate {d['sack_rate']}% ({d['sacks']} in {d['dropbacks']})"))
        rows.append((abs(d["stuff_rate"] - 18) / 3, f"{t} stuff rate {d['stuff_rate']}% (pbp)"))
        rows.append((abs(o["p20_rate"] - 10) / 2, f"{t} explosive pass rate {o['p20_rate']}% ({o['p20']} in {o['dropbacks']})"))
    rows.sort(key=lambda x: -x[0])
    return "\n".join(f"{i}) {r[1]}" for i, r in enumerate(rows[:12], 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--no-freeze", action="store_true", help="rehearsal: skip freeze_card")
    a = ap.parse_args()
    n = a.week
    pairs, ep, wk = card_teams_from_deck()
    R = Runner("recording", n)
    if wk != n:
        R.note(f"WARNING: make_episode_deck.py GAMES is week {wk}, not {n} — fix EPISODE, WEEK and GAMES first.")
    R.step(f"1 pre-record pull (edge report publish)", [PY, "edge_report.py", "--week", str(n), "--view", "ml", "--publish"], tail=45)
    if not a.no_freeze:
        R.step(f"2 freeze card week {n}", [PY, "freeze_card.py", "--week", str(n)], tail=14)
    else:
        R.note("## 2 freeze — skipped (--no-freeze)")
    teams = ",".join(t for p in pairs for t in p)
    R.step(f"3 stat packages ({len(pairs)} games)", [PY, "stat_package.py", "--week", str(n), "--teams", teams], tail=6, timeout=2400)
    R.step(f"4 pre-mortems week {n}", [PY, "premortems.py", "--week", str(n), "--force", "--show"], tail=12)
    R.step(f"5 totals-model shadow call", [PY, "totals_model.py", "--week", str(n), "--calib", TOTALS_CALIB], tail=12)
    R.step(f"6 availability shadow", [PY, "availability.py", "--week", str(n)], tail=16)
    R.step("7 build the deck", [PY, "make_episode_deck.py"], tail=14, timeout=1200)
    R.step("8 deck lint", [PY, "deck_lint.py"], tail=30)
    R.note("## 9 review-before-air candidates (extreme numbers — pick 5-10 for the list)\n```\n" + review_candidates(n, pairs) + "\n```")
    fz = HERE / f"card_data_week{n}_frozen.json"
    if fz.exists():
        card = json.loads(fz.read_text(encoding="utf-8"))
        want = {(a_, h_) for a_, h_ in pairs}
        out = []
        for g in card["games"]:
            if (g["away"], g["home"]) in want:
                out.append(f"{g['away']} at {g['home']}: machine {g['model_spread']} (P home {g['model_p_home']:.2f}) · total {g.get('ou')} · market {g.get('mkt_spread')}")
        R.note(f"## 10 frozen numbers (lines_as_of {card.get('lines_as_of')}) — these must match the notes' 'The number' lines\n```\n" + "\n".join(out) + "\n```")
    R.note("\n## On Lucas's word only\n- `python push_deck.py --pptx decks\\<file>.pptx --file-id <EpN file>` (or --new)\n- NO merged file (Lucas 9/30): he imports our slides into Corey's deck himself; export Corey's deck READ-ONLY only to read his calls / boards / superdogs\n- notes 'The number' lines + OneNote game pages in place if any number moved at the freeze")
    R.finish()


if __name__ == "__main__":
    main()
