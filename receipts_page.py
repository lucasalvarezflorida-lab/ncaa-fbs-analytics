"""receipts_page.py - "The Receipts": the season's Man vs Machine record as one private page.

Built from the files the Sunday run already grades (Lucas 10/9: the show's credibility is the running record):
  * score_tracker.json      every card game: the machine's score call, Corey's, the final
  * superdog_ledger.json    superdog / giant-killer standings and every pick
  * premortems.json         the pre-mortems and whether they fired
Convention (Lucas 10/6): 'off by' = the SCORE-CALL margin vs the final, same for both sides. NO MARKET
numbers - the closing line and its miss stay in internal/receipts_weekN.md.

    python receipts_page.py          # -> receipts/index.html (self-contained); republish the artifact in session
Wired into sunday.py (step 17).
"""
from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "receipts" / "index.html"


def load(name):
    p = HERE / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def esc(s) -> str:
    return html.escape(str(s))


def build() -> dict:
    tr = load("score_tracker.json") or []
    led = load("superdog_ledger.json") or {}
    pm = load("premortems.json") or {}
    weeks = sorted({r["week"] for r in tr})
    rows_by_week = {w: [r for r in tr if r["week"] == w] for w in weeks}
    graded = [r for r in tr if r.get("final")]

    def margin(call):
        return call[1] - call[0] if call else None

    def grade(r):
        fin = margin(r["final"]); out = {}
        for side in ("machine", "man"):
            c = r.get(side)
            if c and fin is not None:
                m = margin(c)
                out[side] = dict(off=abs(fin - m), winner=(m > 0) == (fin > 0) if fin != 0 else None, margin=m)
        out["final_margin"] = fin
        return out

    season = dict(games=len(graded), machine=dict(off=0.0, w=0, n=0), man=dict(off=0.0, w=0, n=0))
    by_week = []
    for w in weeks:
        wk = dict(week=w, games=[], machine=dict(off=0.0, w=0, n=0), man=dict(off=0.0, w=0, n=0), pending=0)
        for r in rows_by_week[w]:
            g = dict(game=r["game"], away=r["away"], home=r["home"], machine=r.get("machine"), man=r.get("man"), final=r.get("final"))
            if r.get("final"):
                gr = grade(r); g["grade"] = gr
                for side in ("machine", "man"):
                    if side in gr:
                        for tot in (wk[side], season[side]):
                            tot["off"] += gr[side]["off"]; tot["n"] += 1; tot["w"] += 1 if gr[side]["winner"] else 0
            else:
                wk["pending"] += 1
            wk["games"].append(g)
        pw = pm.get(str(w), {})
        res = [v.get("result") for v in pw.values() if isinstance(v, dict)]
        wk["premortems"] = dict(n=len(pw), graded=sum(1 for x in res if x), fired=sum(1 for x in res if x and x.get("fired")),
                                lost=sum(1 for x in res if x and x.get("pick_lost")))
        by_week.append(wk)
    return dict(as_of=dt.datetime.now().isoformat(timespec="minutes"), weeks=by_week, season=season,
                ledger=dict(standings=led.get("standings", {}), rules=led.get("rules", {}),
                            machine=led.get("machine_picks", []),
                            man=[dict(p, week=int(k.rsplit("week", 1)[1])) for k, v in led.items() if k.startswith("man_picks_week") for p in v]))


CSS = """
:root { --bg:#f4f2ed; --paper:#fbfaf7; --fg:#1c1d1f; --muted:#696b71; --line:#d9d6cf; --soft:#ebe8e1; --machine:#1f5f8b; --man:#b5541c; --good:#2f7d4f; --bad:#b3372b; --chalk:#e0b11a;
  --display:"Barlow Condensed","Arial Narrow",Impact,sans-serif; --body:"Source Sans 3","Segoe UI",system-ui,sans-serif; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#16171a; --paper:#1f2024; --fg:#ecebe6; --muted:#9a9ca3; --line:#34363c; --soft:#2a2c31; --machine:#6fb3e0; --man:#f0945a; --good:#5cc48a; --bad:#ef7a6c; --chalk:#f0c23a; color-scheme:dark; } }
:root[data-theme="dark"] { --bg:#16171a; --paper:#1f2024; --fg:#ecebe6; --muted:#9a9ca3; --line:#34363c; --soft:#2a2c31; --machine:#6fb3e0; --man:#f0945a; --good:#5cc48a; --bad:#ef7a6c; --chalk:#f0c23a; color-scheme:dark; }
* { box-sizing:border-box } body { margin:0; background:var(--bg); color:var(--fg); font-family:var(--body); font-size:15px; line-height:1.45 }
.wrap { max-width:1040px; margin:0 auto; padding-block:18px 48px; padding-inline:16px }
h1,h2,h3 { font-family:var(--display); font-weight:700; margin:0; text-wrap:balance } h1 { font-size:34px; line-height:1; text-transform:uppercase } h2 { font-size:24px; text-transform:uppercase; margin-top:28px }
.sub { color:var(--muted); font-size:14px; margin-top:4px } .num { font-variant-numeric:tabular-nums }
.tiles { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin-top:18px }
.tile { background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:12px 14px } .tile .k { font-size:11px; letter-spacing:.1em; text-transform:uppercase; color:var(--muted); font-weight:600 }
.tile .v { font-family:var(--display); font-size:34px; font-weight:800; line-height:1.05; margin-top:4px } .tile .s { font-size:13px; color:var(--muted) }
.machine { color:var(--machine) } .man { color:var(--man) }
table { width:100%; border-collapse:collapse; font-size:14px; background:var(--paper) } th,td { padding:6px 8px; border-bottom:1px solid var(--soft); text-align:right; white-space:nowrap }
th { font-size:11px; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); font-weight:600 } td.l,th.l { text-align:left } .tscroll { overflow-x:auto; border:1px solid var(--line); border-radius:8px }
.pill { display:inline-block; min-width:40px; padding:1px 7px; border-radius:10px; font-size:12px; font-weight:700; color:#fff } .pill.good { background:var(--good) } .pill.bad { background:var(--bad) } .pill.flat { background:var(--muted) }
.wk { display:flex; justify-content:space-between; align-items:baseline; gap:10px; flex-wrap:wrap; margin:22px 0 8px } .wk h3 { font-size:20px; text-transform:uppercase } .wk .sum { font-size:13px; color:var(--muted) }
.chart { background:var(--paper); border:1px solid var(--line); border-radius:8px; padding:12px; margin-top:12px } svg text { fill:var(--fg); font-family:var(--body); font-size:12px } svg .ax { stroke:var(--line) }
.foot { margin-top:30px; font-size:13px; color:var(--muted); max-width:80ch }
"""


def render(d: dict) -> str:
    s = d["season"]; M, N = s["machine"], s["man"]
    def pg(t): return (t["off"] / t["n"]) if t["n"] else 0.0
    tiles = f"""
    <div class="tiles">
      <div class="tile"><div class="k">Card games graded</div><div class="v num">{s['games']}</div><div class="s">through Week {max((w['week'] for w in d['weeks'] if w['pending'] == 0), default='-')}</div></div>
      <div class="tile"><div class="k">Winners</div><div class="v num"><span class="machine">{M['w']}</span> · <span class="man">{N['w']}</span></div><div class="s">machine · man, of {M['n']}</div></div>
      <div class="tile"><div class="k">Points off the final margin</div><div class="v num"><span class="machine">{M['off']:.0f}</span> · <span class="man">{N['off']:.0f}</span></div><div class="s">machine · man ({pg(M):.1f} · {pg(N):.1f} a game)</div></div>
      <div class="tile"><div class="k">Superdog standings</div><div class="v num"><span class="man">{d['ledger']['standings'].get('man', 0):g}</span> · <span class="machine">{d['ledger']['standings'].get('machine', 0):g}</span></div><div class="s">man · machine, {esc(d['ledger']['standings'].get('as_of', ''))}</div></div>
    </div>"""
    # running-miss chart (cumulative points off, both sides, by week)
    cm = cn = 0.0; pts = []
    for w in d["weeks"]:
        if w["machine"]["n"]:
            cm += w["machine"]["off"]; cn += w["man"]["off"]; pts.append((w["week"], cm, cn))
    chart = ""
    if pts:
        W, H, L, B = 640, 220, 44, 28; top = max(max(a, b) for _, a, b in pts) * 1.08 or 1
        xs = lambda i: L + i * (W - L - 12) / max(len(pts) - 1, 1); ys = lambda v: H - B - v / top * (H - B - 12)
        def path(idx): return "M" + " L".join(f"{xs(i):.1f},{ys(p[idx]):.1f}" for i, p in enumerate(pts))
        ticks = "".join(f'<text x="{xs(i):.1f}" y="{H - 8}" text-anchor="middle">Wk {p[0]}</text>' for i, p in enumerate(pts))
        chart = f"""<div class="chart"><div class="k" style="font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted);font-weight:600">Running points off the final margin</div>
        <svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Running miss by week">
          <line class="ax" x1="{L}" y1="{H - B}" x2="{W - 12}" y2="{H - B}"/><line class="ax" x1="{L}" y1="12" x2="{L}" y2="{H - B}"/>
          <text x="{L - 6}" y="{ys(top / 1.08):.1f}" text-anchor="end">{top / 1.08:.0f}</text><text x="{L - 6}" y="{H - B}" text-anchor="end">0</text>
          <path d="{path(1)}" fill="none" stroke="var(--machine)" stroke-width="2.5"/><path d="{path(2)}" fill="none" stroke="var(--man)" stroke-width="2.5"/>
          {"".join(f'<circle cx="{xs(i):.1f}" cy="{ys(p[1]):.1f}" r="3" fill="var(--machine)"/><circle cx="{xs(i):.1f}" cy="{ys(p[2]):.1f}" r="3" fill="var(--man)"/>' for i, p in enumerate(pts))}
          {ticks}
          <text x="{W - 12}" y="{ys(pts[-1][1]) - 6:.1f}" text-anchor="end" fill="var(--machine)">machine {pts[-1][1]:.0f}</text><text x="{W - 12}" y="{ys(pts[-1][2]) + 14:.1f}" text-anchor="end" fill="var(--man)">man {pts[-1][2]:.0f}</text>
        </svg></div>"""
    weeks_html = []
    for w in reversed(d["weeks"]):
        rows = []
        for g in w["games"]:
            def call(c, side):
                if not c: return "–"
                win = g["home"] if c[1] > c[0] else g["away"]
                return f'<span class="{side}">{esc(win)}</span> {max(c)}–{min(c)}'
            if g.get("grade"):
                gr = g["grade"]; fin = g["final"]
                fwin = g["home"] if fin[1] > fin[0] else g["away"]
                cells = ""
                for side in ("machine", "man"):
                    x = gr.get(side)
                    if x:
                        cls = "good" if x["winner"] else "bad"
                        cells += f'<td class="num">{call(g[side], side)}</td><td><span class="pill {cls} num">{x["off"]:.0f}</span></td>'
                    else:
                        cells += '<td>–</td><td>–</td>'
                rows.append(f'<tr><td class="l">{esc(g["game"])}</td><td class="num"><b>{esc(fwin)}</b> {max(fin)}–{min(fin)}</td>{cells}</tr>')
            else:
                rows.append(f'<tr><td class="l">{esc(g["game"])}</td><td class="num" style="color:var(--muted)">pending</td><td class="num">{call(g["machine"], "machine")}</td><td>–</td><td class="num">{call(g["man"], "man")}</td><td>–</td></tr>')
        pm = w["premortems"]
        summ = (f"machine {w['machine']['w']}-{w['machine']['n'] - w['machine']['w']} · {w['machine']['off']:.0f} off · man {w['man']['w']}-{w['man']['n'] - w['man']['w']} · {w['man']['off']:.0f} off"
                if w["machine"]["n"] else f"{w['pending']} games pending")
        if pm["n"]:
            summ += f" · pre-mortems {pm['graded']}/{pm['n']} graded, {pm['fired']} fired, {pm['lost']} picks lost"
        weeks_html.append(f"""<div class="wk"><h3>Week {w['week']}</h3><span class="sum">{summ}</span></div>
        <div class="tscroll"><table><thead><tr><th class="l">Game</th><th>Final</th><th class="machine">Machine call</th><th>Off by</th><th class="man">Man call</th><th>Off by</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>""")
    def picks(lst, side):
        rr = []
        for p in sorted(lst, key=lambda p: -(p.get("week") or 0)):
            res = p.get("result") or "pending"; cls = "good" if res in ("win", "cover") else ("bad" if res in ("loss", "lost", "miss") else "flat")
            rr.append(f'<tr><td class="num">{p.get("week", "")}</td><td class="l">{esc(p["pick"])}{(" · " + esc(p["slot"])) if p.get("slot") else ""}</td><td class="l" style="color:var(--muted)">{esc(p.get("final") or "")}</td><td><span class="pill {cls}">{esc(res)}</span></td><td class="num">{p.get("points") if p.get("points") is not None else ""}</td></tr>')
        return f'<div class="tscroll"><table><thead><tr><th>Wk</th><th class="l {side}">Pick</th><th class="l">Final</th><th>Result</th><th>Pts</th></tr></thead><tbody>{"".join(rr)}</tbody></table></div>'
    rules = d["ledger"]["rules"]
    return f"""<meta charset="utf-8">
<title>The Receipts</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;800&family=Source+Sans+3:wght@400;600&display=swap">
<style>{CSS}</style>
<div class="wrap">
  <h1>The Receipts</h1>
  <div class="sub">Man vs Machine, every card game graded the same way: the score call's margin against the final. Updated {esc(d['as_of'][:16].replace('T', ' '))}. No market numbers.</div>
  {tiles}
  {chart}
  <h2>Card by card</h2>
  {"".join(weeks_html)}
  <h2>Superdogs</h2>
  <div class="sub" style="margin-bottom:10px">{esc(rules.get('points', ''))} · superdog: {esc(rules.get('superdog', ''))} · giant killer: {esc(rules.get('giant_killer', ''))}. Standings {esc(d['ledger']['standings'].get('as_of', ''))}: man {d['ledger']['standings'].get('man', 0):g}, machine {d['ledger']['standings'].get('machine', 0):g}.</div>
  <div class="wk"><h3 class="machine">Machine</h3></div>{picks(d['ledger']['machine'], 'machine')}
  <div class="wk"><h3 class="man">Man</h3></div>{picks(d['ledger']['man'], 'man')}
  <div class="foot"><p><b>How to read it.</b> Both sides call a score for every card game. "Off by" is the distance between that call's margin and the final margin, the same arithmetic for the machine and for Corey. Winners count straight up. Superdog points follow Corey's rulebook (cover 5, push 1, outright win 5 plus the spread). Pre-mortems are the one stat per game the machine said would decide its pick, graded after the fact.</p></div>
</div>
"""


if __name__ == "__main__":
    d = build()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(render(d), encoding="utf-8")
    s = d["season"]
    print(f"wrote {OUT.relative_to(HERE)}: {s['games']} graded games, machine {s['machine']['w']}/{s['machine']['n']} winners {s['machine']['off']:.0f} off, man {s['man']['w']}/{s['man']['n']} {s['man']['off']:.0f} off")
