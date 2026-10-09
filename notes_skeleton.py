"""Notes SKELETON generator - the numeric lines of the episode notes in
Lucas's outline layout, so the session writes only the reads and the keys.

  python notes_skeleton.py --week 5 --ep 6 --games "Pitt at Virginia Tech,Penn State at Northwestern,..."
      -> notes/week5_ep6_games_skeleton.md   (one block per game: header, read placeholders, the number +
         score call, honesty placeholder, three key placeholders per team each with the WHY line and the
         evidence bullets filled from stat_package_week5.json, "What X brings" lines, reserve, Corey line)
  python notes_skeleton.py --week 5 --ep 6 --boards
      -> notes/week5_ep6_boards_skeleton.md  (receipts from the tracker + frozen card, Top 25 + weekly
         change, Heisman / hot seat with the deltas vs last week's board, playoff sim, superdog board
         and standings - every number computed, the "say:" lines left for the session)

Conventions (CLAUDE.md): rushing totals = box score; per attempt = completions
only; stuff / 10+ / explosive = play-by-play; quarterback lines name the
player first with the team line as its child. Market numbers never enter the
notes; the machine line, the win probability and the score call do.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

TITLE = {"texas am": "Texas A&M", "ole miss": "Ole Miss", "lsu": "LSU", "usc": "USC", "byu": "BYU", "smu": "SMU", "ucla": "UCLA",
         "ucf": "UCF", "tcu": "TCU", "utsa": "UTSA", "unlv": "UNLV", "utep": "UTEP", "uab": "UAB"}


def title(t):
    return TITLE.get(t, t.title())


def frac(s):
    a, b = s.split("/")
    return int(a), int(b)


def pct(n, d):
    return f"{100 * n / d:.0f}%" if d else "n/a"


def score_call(margin, total):
    hp, ap = (total + margin) / 2, (total - margin) / 2
    h, a = int(hp + 0.5), int(ap + 0.5)
    if h == a and margin:
        h, a = (h + 1, a) if margin > 0 else (h, a + 1)
    return a, h


def load_stat_package(week, teams):
    p = HERE / f"stat_package_week{week}.json"
    have = {}
    if p.exists():
        have = {pk["team"]: pk for pk in json.loads(p.read_text(encoding="utf-8"))}
    missing = [t for t in teams if t not in have]
    if missing:
        print("building stat packages for", missing)
        subprocess.run([sys.executable, str(HERE / "stat_package.py"), "--week", str(week), "--teams", ",".join(teams), "--refresh"], check=True, cwd=HERE)
        have = {pk["team"]: pk for pk in json.loads(p.read_text(encoding="utf-8"))}
    return have


def qb_lines(pk, side_key="offense"):
    """Quarterback first, team line as its child (Lucas 9/23)."""
    o = pk[side_key]
    L = pk["leaders"]["passing"]
    out = []
    if L:
        nm, st = L[0]
        out.append(f"        - {nm}: {st.get('COMPLETIONS', 0):.0f}-of-{st.get('ATT', 0):.0f} for {st.get('YDS', 0):,.0f} — {st.get('YPA', 0)} per attempt; {st.get('TD', 0):.0f} TD, {st.get('INT', 0):.0f} INT")
        diff = ""
        if len(L) > 1:
            n2, s2 = L[1]
            diff = f" — the difference is {n2}, {s2.get('COMPLETIONS', 0):.0f}-of-{s2.get('ATT', 0):.0f} for {s2.get('YDS', 0):.0f}"
        ypc = round(o["pass_yds"] / max(o["comp"], 1), 1)
        out.append(f"          - {pk['team']} as a team: {o['comp']}-of-{o['att']} for {o['pass_yds']:,} ({o['ypa']} an attempt, {ypc} per completion){diff}")
    return out


def off_lines(pk):
    o, f = pk["offense"], pk["offense_vs_fbs"]
    L = pk["leaders"]
    fbs_note = f" (vs FBS: {f['ypa']} a throw, {f['box_ypc']} a carry)" if f.get("att") and (f["ypa"] != o["ypa"] or f["box_ypc"] != o["box_ypc"]) else ""
    rec = "; ".join(f"{nm} {st.get('REC', 0):.0f} for {st.get('YDS', 0):.0f}" + (f" and {st.get('TD', 0):.0f} TD" if st.get("TD") else "") for nm, st in L["receiving"][:3])
    rush = "; ".join(f"{nm} {st.get('CAR', 0):.0f} for {st.get('YDS', 0):.0f}" + (f" and {st.get('TD', 0):.0f} TD" if st.get("TD") else "") for nm, st in L["rushing"][:3])
    t3n, t3d = frac(o["t3"]); tln, tld = frac(o["t3_long"]); tsn, tsd = frac(o["t3_short"]); rzn, rzd = frac(o["rz"])
    return qb_lines(pk) + [
        f"        - {o['p20']} explosive passes in {o['dropbacks']} dropbacks ({o['p20_rate']}%), {o['deep_comp']}-of-{o['deep_att']} on deep throws; sacked {o['sacks']} times ({o['sack_rate']}%); {o['ints']} INT{fbs_note}",
        f"        - Receivers: {rec}",
        f"        - Rushing (box): {o['box_att']} for {o['box_yds']:,} ({o['box_ypc']}); {o['r10']} runs of 10+ ({o['r10_rate']}%), {o['stuff_rate']}% stuffed — {rush}",
        f"        - Third down {t3n}-of-{t3d} ({pct(t3n, t3d)}); third-and-long {tln}-of-{tld}; third-and-short {tsn}-of-{tsd}; red zone {rzn} TD in {rzd} trips ({pct(rzn, rzd)})",
    ]


def def_lines(pk):
    d, f = pk["defense"], pk["defense_vs_fbs"]
    L = pk["leaders"]
    fbs_note = f" (vs FBS: {f['ypa']} a throw allowed, {f['box_ypc']} a carry)" if f.get("att") and (f["ypa"] != d["ypa"] or f["box_ypc"] != d["box_ypc"]) else ""
    sacks = "; ".join(f"{nm} {float(v.get('SACKS', 0)):g}" for nm, v in L["sacks"][:3])
    t3n, t3d = frac(d["t3"]); tln, tld = frac(d["t3_long"]); tsn, tsd = frac(d["t3_short"]); rzn, rzd = frac(d["rz"])
    ypc = round(d["pass_yds"] / max(d["comp"], 1), 1)
    return [
        f"        - Passing allowed: {d['comp']}-of-{d['att']} for {d['pass_yds']:,} — {d['ypa']} a throw, {ypc} per completion; {d['p20']} explosive passes in {d['dropbacks']} dropbacks ({d['p20_rate']}%), {d['deep_comp']}-of-{d['deep_att']} on deep throws; {d['ints']} picks{fbs_note}",
        f"        - Sacks {d['sacks']} in {d['dropbacks']} dropbacks ({d['sack_rate']}%) — {sacks}",
        f"        - Rushing allowed (box): {d['box_att']} for {d['box_yds']:,} ({d['box_ypc']}); {d['r10']} runs of 10+ against it ({d['r10_rate']}%), {d['stuff_rate']}% stuffed",
        f"        - Opponents {t3n}-of-{t3d} on third down ({pct(t3n, t3d)}); {tln}-of-{tld} on third-and-long; {tsn}-of-{tsd} on third-and-short; {rzn} TD allowed in {rzd} red-zone trips ({pct(rzn, rzd)})",
    ]


def game_lines(pk):
    out = []
    for g in pk["games"]:
        o, d = g["offense"], g["defense"]; bo = o.get("box_rush") or {}; bd = d.get("box_rush") or {}
        out.append(f"        - wk{g['week']} {g['site']} {g['opp']} ({g['opp_class'].upper()}) {g['result']}: {o['comp']}-of-{o['att']} for {o['ypa']} a throw, {o['p20']} of 20+, sacked {o['sacks']}; ran {bo.get('att')} for {bo.get('yds')}; allowed {d['ypa']} a throw and {bd.get('att')} for {bd.get('yds')}")
    return out


def team_block(name, pk, opp_pk):
    L = [f"  - {name} keys",
         "    - KEY ONE (write it)",
         "      - Why: (write it)"] + off_lines(pk) + [
         f"      - What {opp_pk['team']} brings:"] + def_lines(opp_pk) + [
         "    - KEY TWO (write it)",
         "      - Why: (write it)"] + def_lines(pk) + [
         f"      - What {opp_pk['team']} brings:"] + off_lines(opp_pk)[:2] + [
         "    - KEY THREE (write it)",
         "      - Why: (write it)",
         "      - Game by game:"] + game_lines(pk) + [
         "    - Reserve: (write it)"]
    return L


def games_skeleton(week, ep, games):
    card = {}
    cp = HERE / f"card_data_week{week}.json"
    if cp.exists():
        for g in json.loads(cp.read_text(encoding="utf-8"))["games"]:
            card[(g["away"], g["home"])] = g
    ap = {}
    apf = HERE / "internal" / f"ap_week{week}.json"
    if apf.exists():
        ap = {normalize_name(s): i for i, s in enumerate(json.loads(apf.read_text(encoding="utf-8"))["ranks"], 1)}
    r = json.loads((HERE / "ratings_current_2026.json").read_text(encoding="utf-8"))
    rank = {t["team"]: i for i, t in enumerate(r["teams"], 1)}
    sigma = r["params"]["sigma"]
    from margin_prob import load_curve
    curve = load_curve("model").rescaled(sigma)
    teams = [t for pair in games for t in pair]
    pks = load_stat_package(week, teams)
    L = [f"# Ep{ep} · Week {week} — GAMES (SKELETON: numbers filled, reads and keys to write)", "",
         "Outline notes: game → the read, the number, each team's three keys with the",
         "WHY and the numbers under them, a reserve key, Corey's call. Lines are the",
         "publish pull's; re-read them off the freeze. MACHINE-DRAFTED — review before air.", "",
         "Stats are each team's 2026 games to date (CFBD box scores and play-by-play,",
         f"stat_package_week{week}.json), never from a game against each other. Rushing totals",
         "are the official box score (sacks and fumbled snaps count as rushes); stuff",
         "rates and 10+ rates come from the play-by-play, sacks excluded. \"Dropbacks\"",
         "= pass plays including sacks; \"explosive pass\" = 20+ yards; \"stuffed\" = a run",
         "for zero or less; \"third-and-long\" = third-and-6 or more. Betting-line",
         "context is kept out of this file on purpose - it lives in the internal folder.", ""]
    for away, home in games:
        g = card.get((away, home))
        ra, rh = ap.get(normalize_name(away)), ap.get(normalize_name(home))
        tag = " · ".join(x for x in [f"No. {ra} {away}" if ra else away, f"No. {rh} {home}" if rh else home])
        when = f"{g['date'].replace(' ET', ' ET')}, {g['venue']}" if g else "(kickoff / venue)"
        L.append(f"- **{away} at {home} — {when} · {tag} (machine #{rank.get(normalize_name(away), '?')} at #{rank.get(normalize_name(home), '?')})**")
        L.append("  ")
        L += ["  - The read", "    - (write it)", "    - (write it)", "    - (write it)"]
        if g:
            m = g["model_margin"]; ph = g["model_p_home"]
            fav, line, p = (home, -m, ph) if m >= 0 else (away, m, 1 - ph)
            a_pts, h_pts = score_call(m, g["ou"]) if g.get("ou") else ("?", "?")
            winner = home if m >= 0 else away
            call = f"{winner} {max(a_pts, h_pts) if isinstance(a_pts, int) else '?'}–{min(a_pts, h_pts) if isinstance(a_pts, int) else '?'}"
            L.append(f"  - The number: {fav} −{abs(line):.1f}, {100 * p:.0f}% · Call {call}")
            try:   # machine draft of the honesty line from why.py (one source with Tale of the Tape); edit before air
                from why import matchup as _why
                w = _why(away, home, "N" if g.get("neutral") else "B")
                L.append(f"    - Honesty (machine draft — edit): {w['honesty']}")
            except Exception as e:  # noqa: BLE001 - no tape data yet, or an unrated team
                L.append(f"    - Honesty: (write it — the number's source, what the machine has not seen) [why.py: {e}]")
            L.append("    - Pre-mortem — written on recording day from the frozen card")
        else:
            L.append("  - The number: (run edge_report --publish first)")
        L += team_block(away, pks[away], pks[home])
        L += team_block(home, pks[home], pks[away])
        L.append("  - Corey: PLACEHOLDER")
        L.append("")
    return "\n".join(L) + "\n"


def boards_skeleton(week, ep):
    L = [f"# Ep{ep} · Week {week} — BOARDS (SKELETON: numbers filled, the say-lines to write)", "",
         "Outline notes: topic → the points → the facts under each point. MACHINE-DRAFTED —",
         "review before air. Betting-line context stays in the internal folder.", ""]
    prev = week - 1
    # receipts
    st = json.loads((HERE / "score_tracker.json").read_text(encoding="utf-8"))
    rows = [r for r in st if r["week"] == prev and r.get("final")]
    frozen = HERE / f"card_data_week{prev}_frozen.json"
    cardf = {}
    if frozen.exists():
        for g in json.loads(frozen.read_text(encoding="utf-8"))["games"]:
            cardf[(g["away"], g["home"])] = g
    L.append(f"- **Receipts (Week {prev})** — man vs machine")
    mm = cm = 0; mw = cw = 0; gm = []; line_rows = []
    for r in rows:
        a, h = r["final"]; ma, mh = r["machine"]; actual = h - a; mach = mh - ma
        g = cardf.get((r["away"], r["home"]))
        if g and g.get("model_margin") is not None:          # the on-air LINE's miss stays INTERNAL (Lucas 10/6): internal/receipts_week{N}.md
            lm = round(g["model_margin"] * 2) / 2; line_rows.append(f"| {r['away']} at {r['home']} | {h - a:+d} | {lm:+g} | {abs(actual - lm):g} | {mach:+d} | {abs(actual - mach):g} |")
        mm += abs(actual - mach); mw += (actual > 0) == (mach > 0)        # the machine is graded on its SCORE CALL, same as Corey
        line = f"  - {r['away']} {a} at {r['home']} {h} — called {r['home'] if mach > 0 else r['away']} {max(ma, mh)}–{min(ma, mh)}; off by {abs(actual - mach):g}"
        if r.get("man"):
            ca, ch = r["man"]; man = ch - ca; cm += abs(actual - man); cw += (actual > 0) == (man > 0)
            line += f" · Corey {r['home'] if man > 0 else r['away']} {max(ca, ch)}–{min(ca, ch)}, off by {abs(actual - man):g}"
        gm.append(line)
    L.append(f"  - Winners: machine {mw}–{len(rows) - mw}, man {cw}–{len(rows) - cw}")
    L.append(f"  - Margin miss, lower is better: Machine {mm:g} · Man {cm:g}")
    if line_rows:
        (HERE / "internal" / f"receipts_week{prev}.md").write_text(
            f"# Week {prev} receipts — INTERNAL: how our SPREAD was off (the on-air line vs the final margin; the show grades the score call)

"
            "| game | final margin (home) | our line | line off by | score-call margin | call off by |
|---|--:|--:|--:|--:|--:|
" + "
".join(line_rows) + "
", encoding="utf-8")
    L.append("  - Points off the FINAL SCORE: see notes/score_tracker.md (both teams' points, per team)")
    L += ["  - Game by game"] + ["  " + g for g in gm]
    L.append("  - Pre-mortems: see notes/premortems.md (fired / lost / named the reason)")
    led = json.loads((HERE / "superdog_ledger.json").read_text(encoding="utf-8"))
    L.append(f"  - Superdogs: Man {led['standings'].get('man')} · Machine {led['standings'].get('machine')} ({led['standings'].get('as_of')}) — confirm Corey's at the lines he took")
    L.append("")
    # Top 25 + weekly change
    from refresh_all import load_env_key, load_fpi_2026
    load_env_key()
    import inseason_ratings as ir
    prior = load_fpi_2026()
    wc = ir.weekly_change(prior)["teams"]
    r = json.loads((HERE / "ratings_current_2026.json").read_text(encoding="utf-8"))
    L.append("- **Top 25 (machine)**")
    L.append(f"  - Rule: {r['params']['cap_mode']} cap {r['params']['cap']:g}, lam {r['params']['lam']:g}, de-lucked {r['params'].get('to_pts', 0):g} a turnover; {r['games_used']} rated games")
    L.append("  - The ten: " + " · ".join(f"{title(t['team'])} {t['cur']}" for t in r["teams"][:10]))
    ups = sorted([kv for kv in wc.items() if min(kv[1]["rank"], kv[1]["prev_rank"]) <= 40], key=lambda kv: -kv[1]["d_week"])
    L.append("  - Risers (this week's games alone): " + "; ".join(f"{title(t)} {v['d_week']:+.1f} (#{v['prev_rank']} → #{v['rank']})" for t, v in ups[:6]))
    L.append("  - Fallers: " + "; ".join(f"{title(t)} {v['d_week']:+.1f} (#{v['prev_rank']} → #{v['rank']})" for t, v in ups[-6:][::-1]))
    L.append("  - Into the 25: " + ", ".join(f"{title(t)} #{v['rank']}" for t, v in wc.items() if v["rank"] <= 25 < v["prev_rank"]) + " · Out: " + ", ".join(f"{title(t)} (#{v['prev_rank']} → #{v['rank']})" for t, v in wc.items() if v["prev_rank"] <= 25 < v["rank"]))
    apf = HERE / "internal" / f"ap_week{week}.json"
    if apf.exists():
        ap = json.loads(apf.read_text(encoding="utf-8"))["ranks"]
        rank = {t["team"]: i for i, t in enumerate(r["teams"], 1)}
        apn = {normalize_name(s): i for i, s in enumerate(ap, 1)}
        splits = sorted([(s, apn[normalize_name(s)], rank.get(normalize_name(s))) for s in ap if rank.get(normalize_name(s))], key=lambda x: -abs(x[1] - x[2]))
        top25 = [t["team"] for t in r["teams"][:25]]
        L.append(f"  - Voters vs us (AP Week {week}): " + " · ".join(f"{s} {a} vs our {o}" for s, a, o in splits[:7]))
        L.append("    - Ours not theirs: " + ", ".join(title(t) for t in top25 if t not in apn) + " · Theirs not ours: " + ", ".join(s for s in ap if normalize_name(s) not in top25))
    ps = HERE / "internal" / f"playoff_sim_week{week}.json"
    if ps.exists():
        tt = sorted(json.loads(ps.read_text(encoding="utf-8"))["teams"], key=lambda v: -v["playoff"])
        L.append("  - Playoff picture (internal): " + " · ".join(f"{title(v['team'])} {v['playoff'] * 100:.0f}%" for v in tt[:12]))
    L.append("")
    # Heisman / hot seat
    b = json.loads((HERE / f"boards_week{week}.json").read_text(encoding="utf-8"))
    bp = HERE / f"boards_week{prev}.json"
    b0 = json.loads(bp.read_text(encoding="utf-8")) if bp.exists() else {"heisman": [], "hot_seat": []}
    def deltas(cur, old, key, val):
        oldi = {r[key]: (i + 1, r[val]) for i, r in enumerate(old)}
        out = []
        for i, r in enumerate(cur, 1):
            o = oldi.get(r[key])
            out.append(f"{r[key]} ({r.get('team', '')}) {r[val]}" + (f" ({r[val] - o[1]:+.1f}, #{o[0]} → #{i})" if o else " (new)"))
        return out
    L.append("- **Heisman board (machine)** — index = team factor × blended efficiency (market " + str(b.get("market_date")) + ")")
    L += ["  - " + x for x in deltas(b["heisman"][:8], b0.get("heisman", []), "name", "index")]
    L.append("  - Non-QB watch: " + ", ".join(f"{r['name']} ({r.get('team', '')})" for r in b.get("heisman_non_qb", [])[:4]))
    if b.get("heisman_all"):     # Lucas 9/29: the slide board is ALL positions (points added per game x team factor)
        L.append("  - All positions (the slide board): " + " · ".join(
            f"{r['name']} ({r['pos']}) {r['index']:.1f}" for r in b["heisman_all"][:8]))
        L += ["  - " + x for x in deltas(b["heisman_all"][:8], b0.get("heisman_all", []), "name", "index")]
    L.append("")
    L.append("- **Hot Seat (machine)** — 60 × (CBS ÷ 5) + 40 × P(miss the bar); CBS frozen " + str(b.get("cbs_date")))
    L += ["  - " + x for x in deltas(b["hot_seat"][:12], b0.get("hot_seat", []), "coach", "score")]
    L.append("")
    sb = HERE / "internal" / f"superdog_board_week{week}.json"
    if sb.exists():
        s = json.loads(sb.read_text(encoding="utf-8"))
        f = lambda x: f"{x['dog']} +{x['pts']:g} {x['at']} {x['fav']}" + (f" (#{x['fav_rank']})" if x.get("fav_rank") else "") + f" — exp {x['exp_pts']:.2f}, machine {x['model_margin_dog']:+.1f}"
        L.append("- **Superdog picks** (lines as of " + str(s.get("lines_as_of")) + " — re-read at the freeze)")
        L.append("  - Machine Giant Killer: " + (f(s["giant_killer"]) if s.get("giant_killer") else "none"))
        L.append("  - Machine Superdog: " + (f(s["superdog"]) if s.get("superdog") else "none"))
        L.append("    - Next: " + " · ".join(f(x) for x in s["any_board"][1:4]))
        L.append("  - Corey's picks: PLACEHOLDER")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--ep", type=int, required=True)
    ap.add_argument("--games", help='"Away at Home,Away at Home,..." (CFBD names)')
    ap.add_argument("--boards", action="store_true")
    a = ap.parse_args()
    from refresh_all import load_env_key
    load_env_key()
    if a.boards:
        out = HERE / "notes" / f"week{a.week}_ep{a.ep}_boards_skeleton.md"
        out.write_text(boards_skeleton(a.week, a.ep), encoding="utf-8")
        print("wrote", out.relative_to(HERE))
    if a.games:
        games = [tuple(x.strip().split(" at ")) for x in a.games.split(",") if " at " in x]
        out = HERE / "notes" / f"week{a.week}_ep{a.ep}_games_skeleton.md"
        out.write_text(games_skeleton(a.week, a.ep, games), encoding="utf-8")
        print("wrote", out.relative_to(HERE))


if __name__ == "__main__":
    main()
