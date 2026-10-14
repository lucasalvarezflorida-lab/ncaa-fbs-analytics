"""performance.py - ATS record and closing-line value of the show's calls, week by week (Lucas 10/14, the
+EV track). INTERNAL: market numbers -> internal/performance_2026.json + internal/PERFORMANCE_2026.md only.

    python performance.py              # every graded card game; writes both files; prints the season table
    python performance.py --week 6     # also prints the week-6 block (the receipts' betting line)

What it grades, per card game with a final (score_tracker.json rows):
  side       the team each caller's score-call margin favours against the line at the FREEZE (the card as
             said on air; weeks without a frozen card use the closing line as the reference)
  ATS        that side against the closing spread (cover / push / loss); and against the freeze line
  CLV        closing spread minus freeze spread, signed to the side (positive = the market moved toward us),
             the same convention as line_ledger.assess; open -> close too
  off        |call margin - market margin| at the close (the receipts slide's "off the spread")
Market: CFBD's /lines cache (DraftKings > Bovada > ESPN Bet, the workbook's preference), the game's last line
in the cache being the close. Freeze line: card_data_week{N}_frozen.json (mkt_spread / now_spread / first_spread).
Superdogs: the ledger's standings. Totals: not graded (no totals call on the card yet).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "fpi-decomposition"))
from name_mapping import normalize_name as norm  # noqa: E402

LINE_PROVIDERS = ["DraftKings", "Bovada", "ESPN Bet"]
TRACKER = os.path.join(HERE, "score_tracker.json")
LINES = os.path.join(HERE, "fpi-decomposition", "data", "lines_seasonType-regular_year-2026.json")
LEDGER = os.path.join(HERE, "superdog_ledger.json")
OUT_JSON = os.path.join(HERE, "internal", "performance_2026.json")
OUT_MD = os.path.join(HERE, "internal", "PERFORMANCE_2026.md")


def _load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def closing_lines() -> dict:
    """{(home, away) normalized: {spread, spread_open, book, ou}} - home spread (negative = home favoured)."""
    out = {}
    for g in _load(LINES):
        lines = g.get("lines") or []
        if not lines:
            continue
        ranked = sorted(lines, key=lambda ln: LINE_PROVIDERS.index(ln["provider"]) if ln.get("provider") in LINE_PROVIDERS else 99)
        ln = next((x for x in ranked if x.get("spread") is not None), None)
        if ln is None:
            continue
        out[(norm(g["homeTeam"]), norm(g["awayTeam"]))] = dict(spread=float(ln["spread"]), spread_open=ln.get("spreadOpen"),
                                                            book=ln.get("provider"), ou=ln.get("overUnder"))
    return out


def freeze_lines(week: int) -> dict:
    """{(home, away): {spread (home, at the freeze), first_spread, opener, frozen_at}} from the frozen card."""
    p = os.path.join(HERE, f"card_data_week{week}_frozen.json")
    if not os.path.exists(p):
        return {}
    c = _load(p); games = c.get("games", c) if isinstance(c, dict) else c
    out = {}
    for g in games:
        sp = g.get("now_spread")
        if sp is None and g.get("mkt_spread"):
            team, num = g["mkt_spread"].rsplit(" ", 1)
            sp = float(num) if norm(team) == norm(g["home"]) else -float(num)
        if sp is None:
            continue
        out[(norm(g["home"]), norm(g["away"]))] = dict(spread=float(sp), first_spread=g.get("first_spread"), opener=g.get("opener"),
                                                        frozen_at=(c.get("frozen_at") if isinstance(c, dict) else None), book=g.get("spread_book"))
    return out


def _ats(side: str | None, final_margin: float, spread: float | None) -> str | None:
    """side 'home'/'away' vs a home spread: cover / push / loss."""
    if side is None or spread is None:
        return None
    mkt = -spread                          # market's home margin
    if final_margin == mkt:
        return "push"
    home_covers = final_margin > mkt
    return "cover" if (home_covers == (side == "home")) else "loss"


def _clv(side: str | None, from_spread, to_spread) -> float | None:
    if side is None or from_spread is None or to_spread is None:
        return None
    moved = float(from_spread) - float(to_spread)     # > 0: the market moved toward the home side
    return round(moved if side == "home" else -moved, 1)


def grade() -> list[dict]:
    close = closing_lines()
    rows = []
    for r in _load(TRACKER):
        if not r.get("final") or not r.get("machine"):
            continue
        key = (norm(r["home"]), norm(r["away"]))
        cl = close.get(key)
        fz = freeze_lines(r["week"]).get(key)
        f = r["final"][1] - r["final"][0]
        ref = fz["spread"] if fz else (cl["spread"] if cl else None)      # the line each side is taken against
        row = dict(week=r["week"], game=r["game"], home=r["home"], away=r["away"], final=r["final"], final_margin=f,
                   close=cl["spread"] if cl else None, close_book=cl["book"] if cl else None, open=(cl["spread_open"] if cl else None),
                   freeze=fz["spread"] if fz else None, reference=("freeze" if fz else ("close" if cl else None)))
        for who, key2 in (("machine", "machine"), ("man", "man")):
            call = r.get(key2)
            if not call:
                row[who] = None
                continue
            c = call[1] - call[0]
            side = None
            if ref is not None and c != -ref:
                side = "home" if c > -ref else "away"
            row[who] = dict(margin=c, side=side,
                            side_team=(r["home"] if side == "home" else r["away"] if side == "away" else None),
                            ats_close=_ats(side, f, cl["spread"] if cl else None),
                            ats_freeze=_ats(side, f, fz["spread"] if fz else None),
                            clv=_clv(side, fz["spread"] if fz else None, cl["spread"] if cl else None),
                            clv_open=_clv(side, cl["spread_open"] if cl else None, cl["spread"] if cl else None),
                            off_close=(round(abs(c + cl["spread"]), 1) if cl else None),
                            su=("win" if (c > 0) == (f > 0) else "loss"))
        rows.append(row)
    return rows


def _rec(rows, who, field):
    w = sum(1 for r in rows if r.get(who) and r[who][field] == "cover"); l = sum(1 for r in rows if r.get(who) and r[who][field] == "loss")
    p = sum(1 for r in rows if r.get(who) and r[who][field] == "push")
    return w, l, p


def _su(rows, who):
    w = sum(1 for r in rows if r.get(who) and r[who]["su"] == "win"); l = sum(1 for r in rows if r.get(who) and r[who]["su"] == "loss")
    return w, l


def _sum(rows, who, field):
    v = [r[who][field] for r in rows if r.get(who) and r[who][field] is not None]
    return (round(sum(v), 1), len(v)) if v else (None, 0)


def summary(rows: list[dict]) -> dict:
    out = {}
    for who in ("machine", "man"):
        su = _su(rows, who); ac = _rec(rows, who, "ats_close"); af = _rec(rows, who, "ats_freeze")
        clv, n = _sum(rows, who, "clv"); clvo, no = _sum(rows, who, "clv_open"); off, noff = _sum(rows, who, "off_close")
        out[who] = dict(games=sum(1 for r in rows if r.get(who)), su=f"{su[0]}-{su[1]}",
                        ats_close=f"{ac[0]}-{ac[1]}" + (f"-{ac[2]}" if ac[2] else ""), ats_freeze=f"{af[0]}-{af[1]}" + (f"-{af[2]}" if af[2] else ""),
                        ats_close_pct=(round(100 * ac[0] / (ac[0] + ac[1]), 1) if ac[0] + ac[1] else None),
                        clv_total=clv, clv_per_pick=(round(clv / n, 2) if n else None), clv_games=n,
                        clv_open_total=clvo, off_close_total=off, off_close_per_game=(round(off / noff, 2) if noff else None))
    return out


def week_block(rows, week) -> str:
    wk = [r for r in rows if r["week"] == week]
    if not wk:
        return f"week {week}: nothing graded"
    s = summary(wk)
    lines = [f"## Week {week} - vs the market ({len(wk)} games)"]
    lines.append(f"ATS at the close: man {s['man']['ats_close']} · machine {s['machine']['ats_close']}   |   at the freeze line: man {s['man']['ats_freeze']} · machine {s['machine']['ats_freeze']}")
    lines.append(f"CLV (freeze -> close, signed to the side): man {s['man']['clv_total']} · machine {s['machine']['clv_total']}   |   off the spread: man {s['man']['off_close_total']} · machine {s['machine']['off_close_total']}")
    for r in wk:
        bits = []
        for who in ("man", "machine"):
            x = r.get(who)
            if x:
                bits.append(f"{who} {x['side_team'] or '-'} {x['ats_close'] or '-'}" + (f" CLV {x['clv']:+g}" if x['clv'] is not None else ""))
        lines.append(f"- {r['game']} {r['final'][0]}-{r['final'][1]} (close {r['close']:+g} {r['close_book']}" + (f", freeze {r['freeze']:+g}" if r['freeze'] is not None else "") + ") · " + " · ".join(bits))
    return "\n".join(lines)


def write(rows: list[dict]) -> None:
    led = _load(LEDGER) if os.path.exists(LEDGER) else {}
    s = summary(rows)
    weeks = sorted({r["week"] for r in rows})
    per_week = {w: summary([r for r in rows if r["week"] == w]) for w in weeks}
    doc = dict(generated=dt.datetime.now().isoformat(timespec="seconds"), convention=__doc__.strip().splitlines()[0], season=s,
               per_week=per_week, superdogs=led.get("standings"), rows=rows)
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
    md = ["# Man vs Machine vs the market - 2026 (INTERNAL)", "",
          f"Generated {doc['generated']}. Side = the team the score call favours against the freeze line (weeks 0-3: the close). "
          "ATS at the close is the betting record; CLV = close minus freeze, signed to the side, positive when the market came to us. "
          "Spreads are home spreads (negative = home favoured). Not slide material.", "",
          "## Season", "", "| | games | SU | ATS (close) | ATS % | ATS (freeze) | CLV total | CLV / pick | off the spread / game |", "|---|--:|--:|--:|--:|--:|--:|--:|--:|"]
    for who in ("man", "machine"):
        x = s[who]
        md.append(f"| {who} | {x['games']} | {x['su']} | {x['ats_close']} | {x['ats_close_pct']} | {x['ats_freeze']} | {x['clv_total']} | {x['clv_per_pick']} | {x['off_close_per_game']} |")
    if led.get("standings"):
        md += ["", f"Superdogs (the ledger): man {led['standings'].get('man')} · machine {led['standings'].get('machine')} - {led['standings'].get('as_of', '')}"]
    md += ["", "## By week", "", "| week | games | man SU | man ATS | man CLV | machine SU | machine ATS | machine CLV |", "|--:|--:|--:|--:|--:|--:|--:|--:|"]
    for w in weeks:
        x = per_week[w]
        md.append(f"| {w} | {x['machine']['games']} | {x['man']['su']} | {x['man']['ats_close']} | {x['man']['clv_total']} | {x['machine']['su']} | {x['machine']['ats_close']} | {x['machine']['clv_total']} |")
    md.append("")
    for w in weeks:
        md.append(week_block(rows, w)); md.append("")
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int)
    a = ap.parse_args()
    rows = grade()
    write(rows)
    s = summary(rows)
    print(f"{len(rows)} graded card games -> {os.path.relpath(OUT_JSON, HERE)}, {os.path.relpath(OUT_MD, HERE)}")
    for who in ("man", "machine"):
        x = s[who]
        print(f"  {who:8s} SU {x['su']:6s} ATS(close) {x['ats_close']:8s} ({x['ats_close_pct']}%)  ATS(freeze) {x['ats_freeze']:8s} CLV {x['clv_total']} over {x['clv_games']} ({x['clv_per_pick']}/pick)  off/game {x['off_close_per_game']}")
    if a.week is not None:
        print(); print(week_block(rows, a.week))


if __name__ == "__main__":
    main()
