"""SUNDAY orchestrator - grade the week just played and set up the next one.

    python sunday.py --week 4          # 4 = the week that was just played (the card graded), 5 = the next card

Steps (each logged; a failure does not stop the rest; summary in internal/sunday_week4.md):
  1. pull finals + week-N box scores, play-by-play, player boxes
  2. score_tracker.py (fills finals, grades the score calls incl. Corey's + shadow)
  3. grade_premortems.py --week N --refresh
  4. superdog ledger: grade the machine's pending week-N picks from the finals (Corey's stay manual)
  5. refresh_all.py --no-rosters --wait-for-unlock (ratings, sheets, shadow ratings, playoff sim, team stats, mirror)
  6. weekly change: Top 25 / risers / fallers / in-out
  7. hot_seat_heisman.py --week N+1 --refresh   (reminder: MARKET / MARKET_DATE by hand first)
  8. edge_report.py --week N+1 --view ml --publish  (Sunday lines -> card_data_week{N+1}.json, NOT frozen)
  9. superdog_board.py --week N+1
 10. turnover_shadow.py --week N+1 (the replaced rule beside the on-air one)
 11. playoff sim summary
 12. RECAP_ROWS snippet for make_episode_deck.py (from the frozen card + tracker) - printed, paste it
 13. AP poll check
 14. social_pack.py --week N (data pack for mvm-social)
 15. efficiency_blend_check.py --cards (SHADOW: the cards graded machine / blend / efficiency, EFFICIENCY_BLEND_2026.md)
Then: notes_skeleton.py once the card is picked; OneNote pages with -Prefix "Week N+1 - ".
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from routine import Runner, ap_check, INTERNAL  # noqa: E402

PY = sys.executable


def grade_superdogs(week: int) -> str:
    """Machine picks for `week` with result null -> graded from the CFBD finals (cover / win / push / loss)."""
    led = json.loads((HERE / "superdog_ledger.json").read_text(encoding="utf-8"))
    games = json.loads((HERE / "fpi-decomposition" / "data" / "games_seasonType-regular_year-2026.json").read_text(encoding="utf-8"))
    finals = {}
    for g in games:
        if g.get("completed") and g.get("homePoints") is not None:
            finals[(g["awayTeam"], g["homeTeam"])] = (g["awayPoints"], g["homePoints"])
    out, added = [], 0.0
    for p in led["machine_picks"]:
        if p.get("week") != week or p.get("result") not in (None, "pending", ""):
            continue
        m = re.match(r"(.+?) \+([\d.]+) (at|vs) (?:#\d+ )?(.+)", p["pick"])
        if not m:
            out.append(f"could not parse pick: {p['pick']}"); continue
        dog, pts, at, opp = m.group(1), float(m.group(2)), m.group(3), m.group(4)
        key = (dog, opp) if at == "at" else (opp, dog)
        if key not in finals:
            out.append(f"no final yet: {p['pick']}"); continue
        a, h = finals[key]
        dog_pts, opp_pts = (a, h) if at == "at" else (h, a)
        margin = dog_pts - opp_pts
        if margin > 0:
            res, points = "win", 5 + pts
        elif margin + pts > 0:
            res, points = "cover", 5
        elif margin + pts == 0:
            res, points = "push", 1
        else:
            res, points = "loss", 0
        p.update(final=f"{opp if opp_pts > dog_pts else dog} {max(a, h)}-{min(a, h)}", result=res, points=points)
        added += points
        out.append(f"{p['pick']}: {res} ({points:g}) — final {p['final']}")
    if added or out:
        led["standings"]["machine"] = round(led["standings"].get("machine", 0) + added, 1)
        led["standings"]["as_of"] = f"through Week {week} (machine); Corey's week {week} picks still to grade at his lines"
        (HERE / "superdog_ledger.json").write_text(json.dumps(led, indent=1), encoding="utf-8")
    return "\n".join(out) + f"\nMACHINE standing now {led['standings'].get('machine')} (+{added:g}); MAN {led['standings'].get('man')} — grade Corey's picks by hand at the lines he took"


def recap_rows(week: int) -> str:
    """RECAP_ROWS text for make_episode_deck.py from the frozen card + score_tracker (man calls)."""
    fz = HERE / f"card_data_week{week}_frozen.json"
    if not fz.exists():
        return "no frozen card for this week"
    card = {(g["away"], g["home"]): g for g in json.loads(fz.read_text(encoding="utf-8"))["games"]}
    st = [r for r in json.loads((HERE / "score_tracker.json").read_text(encoding="utf-8")) if r["week"] == week]
    lines = [f"RECAP_ROWS = [   # Week {week} (auto from card_data_week{week}_frozen.json + score_tracker.json; on-air line = the rounded machine margin)"]
    for r in st:
        g = card.get((r["away"], r["home"]))
        if not g:
            continue
        m = g["model_margin"]; ma, mh = r["machine"]
        call = f"{r['home'] if mh > ma else r['away']} {max(ma, mh)}–{min(ma, mh)}"
        mk = g.get("mkt_spread", "")
        mm = re.match(r"(.+) (-?[\d.]+)$", mk or "")
        close = None
        if mm:
            sp = float(mm.group(2)); close = -sp if mm.group(1) == r["home"] else sp   # home-perspective line, negative = home favored
            close = -abs(sp) if mm.group(1) == r["home"] else abs(sp)
        man = ""
        if r.get("man"):
            ca, ch = r["man"]; man = f', "{r["home"] if ch > ca else r["away"]} {max(ca, ch)}–{min(ca, ch)}"'
        else:
            man = ', None'
        lines.append(f'    ("{r["away"][:4].upper()}", "{r["home"][:4].upper()}", "{r["away"]} at {r["home"]}", ("{r["away"]}", "{r["home"]}"), "{call}", {-round(m * 2) / 2:g}, {close if close is not None else "None"}{man}, {g.get("ou")}),')
    lines.append("]")
    return "\n".join(lines) + "\nHome-perspective lines: negative = home favored (matches the Week 3/4 rows). Check the abbreviations and the man calls before pasting."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True, help="the week just played")
    ap.add_argument("--skip-refresh", action="store_true")
    a = ap.parse_args()
    n, nxt = a.week, a.week + 1
    R = Runner("sunday", n)
    R.py("1 pull finals, box, plays, player boxes", f"""
import sys; sys.path.insert(0, r'{HERE}'); sys.path.insert(0, r'{HERE / "fpi-decomposition"}')
from refresh_all import load_env_key; load_env_key()
import cfbd_client as c
g = c.get('/games', {{'year': 2026, 'seasonType': 'regular'}}, True); print('games', len([x for x in g if x['week']=={n} and x.get('completed')]), 'completed in week {n}')
for ep, p in (('/games/teams', {{'year': 2026, 'week': {n}, 'seasonType': 'regular'}}), ('/plays', {{'year': 2026, 'week': {n}, 'seasonType': 'regular'}}), ('/games/players', {{'year': 2026, 'week': {n}}})):
    print(ep, len(c.get(ep, p, True)))
""")
    R.step("2 score tracker", [PY, "score_tracker.py"], tail=16)
    R.step(f"3 grade pre-mortems week {n}", [PY, "grade_premortems.py", "--week", str(n), "--refresh"], tail=10)
    R.note("## 4 superdog ledger (machine picks)\n```\n" + grade_superdogs(n) + "\n```")
    if not a.skip_refresh:
        R.step("5 refresh (no rosters)", [PY, "refresh_all.py", "--no-rosters", "--wait-for-unlock"], tail=8, timeout=3600)
    R.py("6 weekly change", f"""
import sys, json; sys.path.insert(0, r'{HERE}'); sys.path.insert(0, r'{HERE / "fpi-decomposition"}')
from refresh_all import load_env_key, load_fpi_2026; load_env_key()
import inseason_ratings as ir
r = json.load(open(r'{HERE / "ratings_current_2026.json"}'))
print('rule', r['params'])
print('TOP 25:', ' · '.join(f"{{i}} {{t['team']}} {{t['cur']}}" for i, t in enumerate(r['teams'][:25], 1)))
wc = ir.weekly_change(load_fpi_2026())['teams']
ups = sorted(wc.items(), key=lambda kv: -kv[1]['d_week'])
print('RISERS:', [(t, v['d_week'], v['prev_rank'], v['rank']) for t, v in ups[:8]])
print('FALLERS:', [(t, v['d_week'], v['prev_rank'], v['rank']) for t, v in ups[-8:][::-1]])
print('IN:', [(t, v['prev_rank'], v['rank']) for t, v in wc.items() if v['rank'] <= 25 < v['prev_rank']], 'OUT:', [(t, v['prev_rank'], v['rank']) for t, v in wc.items() if v['prev_rank'] <= 25 < v['rank']])
""", tail=8)
    R.note("> Reminder: update MARKET / MARKET_DATE in hot_seat_heisman.py by hand (DraftKings via Covers) BEFORE trusting the Heisman market column.")
    R.step(f"7 hot seat + Heisman week {nxt}", [PY, "hot_seat_heisman.py", "--week", str(nxt), "--refresh"], tail=30)
    R.step(f"8 edge report week {nxt} (publish, not frozen)", [PY, "edge_report.py", "--week", str(nxt), "--view", "ml", "--publish"], tail=45)
    R.step(f"9 superdog board week {nxt}", [PY, "superdog_board.py", "--week", str(nxt)], tail=12)
    R.step(f"10 old-rule shadow week {nxt}", [PY, "turnover_shadow.py", "--week", str(nxt)], tail=30)
    R.py("11 playoff sim summary", f"""
import json
ps = json.load(open(r'{HERE / "internal" / f"playoff_sim_week{nxt}.json"}'))['teams']
rows = sorted(ps, key=lambda v: -v['playoff'])
print(' · '.join(f"{{v['team']}} {{v['playoff']*100:.0f}}% (conf {{v['conf_title']*100:.0f}}, title {{v['national_title']*100:.1f}})" for v in rows[:16]))
""", tail=4)
    R.note("## 12 RECAP_ROWS snippet (paste into make_episode_deck.py, archive the old rows as _RECAP_ROWS_WK" + str(n - 1) + ")\n```\n" + recap_rows(n) + "\n```")
    R.note("## 13 AP poll\n" + ap_check(nxt))
    R.step(f"14 social pack week {n}", [PY, "social_pack.py", "--week", str(n)], tail=3)
    R.step("15 efficiency blend on the cards (SHADOW, pre-registered 10/8 - EFFICIENCY_BLEND_2026.md)", [PY, "efficiency_blend_check.py", "--cards"], tail=8)
    R.note(f"\n## Next\n- Update WEEK0_MISS / PRIOR_GAMES / LEANS_LINE in make_episode_deck.py from the receipts (running totals).\n- Card: ask Lucas; then `python notes_skeleton.py --week {nxt} --ep <E> --games \"A at B,...\"` and `--boards`, write the reads/keys, push OneNote with -Prefix \"Week {nxt} - \".\n- Corey's calls into score_tracker.json (man) and the ledger when his slides post.")
    R.finish()


if __name__ == "__main__":
    main()
