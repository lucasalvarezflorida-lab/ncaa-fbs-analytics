"""card_page.py - "The Card": this week's five games as one private page, the on-air companion.

Per game, in the tracker's order (Corey's order once his deck posts): the machine's score call, margin and
win chance; the plays' number (the efficiency shadow, labelled) and the 50/50 blend; Corey's call once it is
in; the final and both grades once the game is played; a stat strip for both teams (season offense and
defense per game with FBS ranks from the Team Stats sheet, the current QB / RB / WR lines from the week's
stat package when it exists); the pre-mortem; and the honesty line from why.py (one source with Tale of
the Tape). The bottom carries the season receipts. NO MARKET NUMBERS anywhere on the page.

Which card: the latest week in score_tracker.json with a game still unplayed; if every row is final, the
last graded card with a note that the next one is not set. Numbers come from card_data_week{N}_frozen.json
when it exists (recording day), else card_data_week{N}.json (the Sunday publish).

    python card_page.py            # -> card/index.html (self-contained; logos from tape_data_2026.json)
Wired into sunday.py (16c) and recording.py (after the pre-mortems).
"""
from __future__ import annotations

import datetime as dt
import html
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

OUT = HERE / "card" / "index.html"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def esc(s) -> str:
    return html.escape("" if s is None else str(s))


def f1(x) -> str:
    return "—" if x is None else f"{x:.1f}"


def pick_week(tr: list[dict]) -> tuple[int, bool]:
    pending = sorted({g["week"] for g in tr if not g.get("final")})
    if pending:
        return pending[0], True
    return max(g["week"] for g in tr), False


def leaders(sp: dict | None, out_names: set[str]) -> dict:
    """QB / RB / WR lines from the stat package; skip a player marked OUT (first initial + last name)."""
    if not sp:
        return {}
    def ok(name):
        parts = name.split()
        tag = (parts[0][0] + ". " + parts[-1]).lower() if len(parts) > 1 else name.lower()
        return tag not in out_names and name.lower() not in out_names
    L = sp.get("leaders", {})
    out = {}
    for n, s in L.get("passing", []):
        if ok(n):
            out["qb"] = f"{esc(n)} {int(s.get('COMPLETIONS', 0))}-of-{int(s.get('ATT', 0))}, {int(s.get('YDS', 0))} yds, {int(s.get('TD', 0))}-{int(s.get('INT', 0))}"; break
    for n, s in L.get("rushing", []):
        if ok(n):
            out["rb"] = f"{esc(n)} {int(s.get('CAR', 0))} for {int(s.get('YDS', 0))} ({s.get('YPC', 0):.1f}), {int(s.get('TD', 0))} TD"; break
    for n, s in L.get("receiving", []):
        if ok(n):
            out["wr"] = f"{esc(n)} {int(s.get('REC', 0))} for {int(s.get('YDS', 0))}, {int(s.get('TD', 0))} TD"; break
    return out


def build() -> dict:
    tr = load(HERE / "score_tracker.json") or []
    week, pending = pick_week(tr)
    rows = [g for g in tr if g["week"] == week]
    frozen = HERE / f"card_data_week{week}_frozen.json"
    cd = load(frozen) or load(HERE / f"card_data_week{week}.json") or {}
    games = cd.get("games", cd) if isinstance(cd, dict) else cd
    cg = {(normalize_name(g["home"]), normalize_name(g["away"])): g for g in games} if games else {}
    tape = load(HERE / "tape_data_2026.json") or {"teams": {}}
    T = tape["teams"]
    sp = load(HERE / f"stat_package_week{week}.json")
    sp = {normalize_name(t["team"]): t for t in sp} if isinstance(sp, list) else {}
    pm = (load(HERE / "premortems.json") or {}).get(str(week), {})
    av = load(HERE / "internal" / "availability.json") or []
    out_names = {f"{e.get('player', '')}".lower() for e in av if e.get("status") == "out"}
    import why
    pre_rows = {}
    if not pending:   # graded card: the machine and the plays re-solved from the weeks BEFORE the card week (as efficiency_blend_check --cards does)
        try:
            import backtest as bt
            from efficiency_ratings import EfficiencyModel
            ctx = bt.SeasonCtx(2026)
            cw = max(week, 1)
            pc, pe = bt.ridge_predict(ctx, cw, bt.MODELS["current"]), EfficiencyModel()(ctx, cw)
            for g in ctx.games:
                if g["week"] == cw and g["id"] in pc and g["id"] in pe:
                    pre_rows[(week, g["home"], g["away"])] = dict(cur=pc[g["id"]][0], eff=pe[g["id"]][0])
        except Exception as e:  # noqa: BLE001
            print("pre-week numbers unavailable:", e)
    cards = []
    for r in rows:
        h, a = normalize_name(r["home"]), normalize_name(r["away"])
        c = cg.get((h, a), {})
        try:
            w = why.matchup(r["away"], r["home"], "N" if c.get("neutral") else "B")
        except Exception as e:  # noqa: BLE001
            w = dict(call=None, margin=None, p_a=None, plays_margin=None, blend=None, honesty=f"why.py: {e}")
        m = c.get("model_margin", (-w["margin"] if w.get("margin") is not None else None))   # home perspective
        p_home = c.get("model_p_home", (1 - w["p_a"] if w.get("p_a") is not None else None))
        plays = -w["plays_margin"] if w.get("plays_margin") is not None else None
        blend = -w["blend"] if w.get("blend") is not None else None
        fin = r.get("final")
        if fin and pre_rows:   # a graded card shows the numbers the plays had BEFORE the game, not today's
            pr = pre_rows.get((week, h, a))
            if pr:
                plays, blend = pr["eff"], 0.5 * (pr["cur"] + pr["eff"])
        def grade(call):
            if not (call and fin):
                return None
            mm, fm = call[1] - call[0], fin[1] - fin[0]
            return dict(off=abs(fm - mm), right=(mm > 0) == (fm > 0))
        pmg = pm.get(r["game"]) or next((v for k, v in pm.items() if normalize_name(v.get("home", "")) == h and normalize_name(v.get("away", "")) == a), None)
        cards.append(dict(
            game=r["game"], home=r["home"], away=r["away"], hk=h, ak=a, date=c.get("date"), neutral=bool(c.get("neutral")),
            machine=r.get("machine"), man=r.get("man"), final=fin, g_machine=grade(r.get("machine")), g_man=grade(r.get("man")),
            margin=m, p_home=p_home, plays=plays, blend=blend, honesty=w.get("honesty"),
            premortem=(dict(text=pmg.get("text"), why=pmg.get("why"), fired=pmg.get("fired"), result=pmg.get("result")) if pmg else None),
            th=T.get(h, {}), ta=T.get(a, {}), lh=leaders(sp.get(h), out_names), la=leaders(sp.get(a), out_names),
        ))
    # season receipts
    graded = [g for g in tr if g.get("final")]
    def tot(side):
        off = sum(abs((g["final"][1] - g["final"][0]) - (g[side][1] - g[side][0])) for g in graded if g.get(side))
        wins = sum(((g[side][1] - g[side][0]) > 0) == ((g["final"][1] - g["final"][0]) > 0) for g in graded if g.get(side))
        n = sum(1 for g in graded if g.get(side))
        return dict(off=off, w=wins, l=n - wins, n=n)
    return dict(week=week, pending=pending, frozen=frozen.exists(), lines_as_of=cd.get("lines_as_of") if isinstance(cd, dict) else None,
                built=dt.datetime.now().isoformat(timespec="minutes"), cards=cards, season=dict(machine=tot("machine"), man=tot("man"), games=len(graded)),
                stat_package=bool(sp))


CSS = """
:root {
  --bg: #f3f1ec; --paper: #fbfaf7; --fg: #1c1d1f; --muted: #686a70; --line: #d9d6cf; --line-soft: #e8e5de;
  --chalk: #e0b11a; --good: #2f7d4f; --bad: #b3372b; --shadow-tag: #6b5bd2;
  --display: "Barlow Condensed", "Arial Narrow", Impact, sans-serif; --body: "Source Sans 3", "Segoe UI", system-ui, sans-serif;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #16171a; --paper: #1f2024; --fg: #ecebe6; --muted: #9a9ca3; --line: #34363c; --line-soft: #2a2c31;
  --chalk: #f0c23a; --good: #5cc48a; --bad: #ef7a6c; --shadow-tag: #a89bff; color-scheme: dark; } }
:root[data-theme="dark"] {
  --bg: #16171a; --paper: #1f2024; --fg: #ecebe6; --muted: #9a9ca3; --line: #34363c; --line-soft: #2a2c31;
  --chalk: #f0c23a; --good: #5cc48a; --bad: #ef7a6c; --shadow-tag: #a89bff; color-scheme: dark; }
* { box-sizing: border-box; }
body { background: var(--bg); color: var(--fg); font-family: var(--body); font-size: 15px; line-height: 1.45; margin: 0; }
.wrap { max-width: 1000px; margin: 0 auto; padding-block: 18px 48px; padding-inline: 16px; }
h1, h2, h3 { font-family: var(--display); font-weight: 700; letter-spacing: .01em; text-wrap: balance; margin: 0; }
h1 { font-size: 34px; line-height: 1; text-transform: uppercase; }
.sub { color: var(--muted); font-size: 14px; margin-top: 4px; }
.eyebrow { font-family: var(--display); font-weight: 700; font-size: 13px; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); }
.num { font-variant-numeric: tabular-nums; }
.tag { display: inline-block; font-size: 11px; letter-spacing: .08em; text-transform: uppercase; font-weight: 600; padding: 2px 7px; border-radius: 3px; border: 1px solid var(--line); color: var(--muted); vertical-align: middle; }
.tag.shadow { color: var(--shadow-tag); border-color: var(--shadow-tag); }
.tag.good { color: var(--good); border-color: var(--good); } .tag.bad { color: var(--bad); border-color: var(--bad); }
.game { margin-top: 26px; border: 1px solid var(--line); border-radius: 10px; overflow: hidden; background: var(--paper); }
.strip { display: grid; grid-template-columns: 1fr 1.1fr 1fr; }
.side { padding: 16px; display: flex; flex-direction: column; gap: 4px; min-width: 0; color: #fff; background: var(--tc, #444); }
.side.h { align-items: flex-start; text-align: left; }
.side img { width: 52px; height: 52px; object-fit: contain; background: rgba(255,255,255,.92); border-radius: 50%; padding: 5px; }
.side .nm { font-family: var(--display); font-weight: 800; font-size: 26px; line-height: 1; text-transform: uppercase; }
.side .meta { font-size: 13px; opacity: .92; }
.mid { padding: 14px 12px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 2px; min-width: 0; }
.mid .call { font-family: var(--display); font-weight: 800; font-size: 34px; line-height: 1; text-transform: uppercase; }
.mid .score { font-family: var(--display); font-weight: 700; font-size: 22px; }
.mid .p { color: var(--muted); font-size: 14px; }
.mid .plays { margin-top: 6px; font-size: 14px; }
.mid .plays b { color: var(--shadow-tag); }
.mid .date { color: var(--muted); font-size: 12px; margin-top: 4px; }
.body { padding: 14px 16px; display: grid; gap: 12px; }
.res { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.res .box { border: 1px solid var(--line); border-radius: 6px; padding: 8px 10px; }
.res .box .lab { font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.res .box .v { font-family: var(--display); font-weight: 700; font-size: 22px; }
.res .box .g { font-size: 13px; }
.stats { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.stats .t { font-size: 13px; }
.stats .t .who { font-weight: 600; display: flex; align-items: center; gap: 6px; }
.stats .t .who img { width: 18px; height: 18px; object-fit: contain; }
.stats dl { margin: 4px 0 0; display: grid; grid-template-columns: max-content 1fr; gap: 2px 10px; }
.stats dt { color: var(--muted); } .stats dd { margin: 0; }
.stats small { color: var(--muted); }
.why { font-size: 14px; border-top: 1px solid var(--line-soft); padding-top: 10px; }
.why .lab { font-weight: 600; color: var(--chalk); text-transform: uppercase; font-size: 12px; letter-spacing: .08em; margin-right: 6px; }
.season { margin-top: 30px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.season .box { background: var(--paper); border: 1px solid var(--line); border-radius: 8px; padding: 12px 14px; }
.season .lab { font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.season .v { font-family: var(--display); font-weight: 700; font-size: 28px; }
.season .s { color: var(--muted); font-size: 13px; }
.foot { color: var(--muted); font-size: 13px; margin-top: 16px; max-width: 72ch; }
.note { margin-top: 16px; padding: 10px 14px; border-left: 3px solid var(--chalk); background: var(--paper); border-radius: 0 6px 6px 0; }
@media (max-width: 700px) { .strip { grid-template-columns: 1fr; } .res, .stats, .season { grid-template-columns: 1fr; } }
"""


def render(d: dict) -> str:
    P = []
    P.append('<meta charset="utf-8"><title>The Card</title>')
    P.append('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;700;800&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&display=swap">')
    P.append(f"<style>{CSS}</style>")
    P.append('<div class="wrap"><header><div class="eyebrow">Man vs Machine · this week\'s card</div><h1>The Card</h1>')
    status = ("frozen at recording" if d["frozen"] else "Sunday numbers, not frozen") if d["pending"] else "graded"
    P.append(f'<div class="sub">Week {d["week"]} · {status} · built {esc(d["built"].replace("T", " "))}</div></header>')
    if not d["pending"]:
        P.append(f'<div class="note">The Week {d["week"] + 1} card is not set yet. This is the last card, graded.</div>')
    for c in d["cards"]:
        th, ta = c["th"], c["ta"]
        m, p = c["margin"], c["p_home"]
        fav = c["home"] if (m or 0) >= 0 else c["away"]
        call = f"{esc(fav)} by {f1(abs(m))}" if m is not None else "no number yet"
        pwin = (p if (m or 0) >= 0 else (1 - p)) if p is not None else None
        sc = c["machine"]
        score = f"{esc(c['away'])} {sc[0]} · {esc(c['home'])} {sc[1]}" if sc else ""
        plays = ""
        if c["plays"] is not None:
            pf = c["home"] if c["plays"] >= 0 else c["away"]
            bf = c["home"] if (c["blend"] or 0) >= 0 else c["away"]
            plays = f'<div class="plays"><span class="tag shadow">plays</span> <b>{esc(pf)} by {f1(abs(c["plays"]))}</b> · blend {esc(bf)} by {f1(abs(c["blend"]))}</div>'
        P.append(f'<article class="game"><div class="strip">')
        P.append(f'<div class="side a" style="--tc:{esc(ta.get("color") or "#444")}">{"<img src=\"" + ta["logo"] + "\" alt=\"\">" if ta.get("logo") else ""}<div class="nm">{esc(c["away"])}</div><div class="meta">{esc(ta.get("record", ""))} · #{ta.get("rank", "—")} · {f1(ta.get("now"))}</div></div>')
        P.append(f'<div class="mid"><div class="eyebrow">the machine</div><div class="call">{call}</div><div class="score num">{score}</div><div class="p num">{"" if pwin is None else f"{pwin * 100:.0f}% to win"}</div>{plays}<div class="date">{esc(c.get("date") or "")}{" · neutral site" if c["neutral"] else ""}</div></div>')
        P.append(f'<div class="side h" style="--tc:{esc(th.get("color") or "#444")}">{"<img src=\"" + th["logo"] + "\" alt=\"\">" if th.get("logo") else ""}<div class="nm">{esc(c["home"])}</div><div class="meta">{esc(th.get("record", ""))} · #{th.get("rank", "—")} · {f1(th.get("now"))}</div></div>')
        P.append('</div><div class="body">')
        # results row
        boxes = []
        man = c["man"]
        boxes.append(f'<div class="box"><div class="lab">Corey</div><div class="v num">{(esc(c["away"]) + " " + str(man[0]) + " · " + esc(c["home"]) + " " + str(man[1])) if man else "—"}</div><div class="g">{"" if not c["g_man"] else ("<span class=\"tag " + ("good" if c["g_man"]["right"] else "bad") + "\">" + ("winner" if c["g_man"]["right"] else "wrong side") + "</span> off by " + f"{c['g_man']['off']:g}")}</div></div>')
        boxes.append(f'<div class="box"><div class="lab">Final</div><div class="v num">{(esc(c["away"]) + " " + str(c["final"][0]) + " · " + esc(c["home"]) + " " + str(c["final"][1])) if c["final"] else "not played"}</div><div class="g">{"" if not c["g_machine"] else ("machine <span class=\"tag " + ("good" if c["g_machine"]["right"] else "bad") + "\">" + ("winner" if c["g_machine"]["right"] else "wrong side") + "</span> off by " + f"{c['g_machine']['off']:g}")}</div></div>')
        pmv = c["premortem"]
        pmtxt = "—" if not pmv else esc(pmv["text"]) + ("" if pmv.get("fired") is None else (' <span class="tag bad">fired</span>' if pmv.get("fired") else ' <span class="tag good">held</span>'))
        boxes.append(f'<div class="box"><div class="lab">Pre-mortem · the loss would look like</div><div class="g">{pmtxt}</div><div class="g"><small>{esc((pmv or {}).get("why") or "")}</small></div></div>')
        P.append('<div class="res">' + "".join(boxes) + "</div>")
        # stat strip
        def tcol(t, lead, name):
            s = t.get("stats", {}) if t else {}
            o, dd = s.get("off", {}), s.get("def_", {})
            L = []
            L.append(f'<div class="who">{"<img src=\"" + t["logo"] + "\" alt=\"\">" if t.get("logo") else ""}{esc(name)} <small>{esc(t.get("record", ""))}</small></div><dl>')
            if lead.get("qb"): L.append(f'<dt>QB</dt><dd>{lead["qb"]}</dd>')
            if lead.get("rb"): L.append(f'<dt>RB</dt><dd>{lead["rb"]}</dd>')
            if lead.get("wr"): L.append(f'<dt>WR</dt><dd>{lead["wr"]}</dd>')
            if o: L.append(f'<dt>Offense</dt><dd class="num">{f1(o.get("ppg"))} a game <small>#{o.get("ppg_rk", "—")}</small> · {f1(o.get("ypa"))} an attempt <small>#{o.get("ypa_rk", "—")}</small> · {f1(o.get("rush_ypc"))} a carry <small>#{o.get("rush_ypc_rk", "—")}</small></dd>')
            if dd: L.append(f'<dt>Defense</dt><dd class="num">{f1(dd.get("ppg"))} allowed <small>#{dd.get("ppg_rk", "—")}</small> · {f1(dd.get("ypa"))} an attempt <small>#{dd.get("ypa_rk", "—")}</small> · {f1(dd.get("rush_ypc"))} a carry <small>#{dd.get("rush_ypc_rk", "—")}</small></dd>')
            L.append("</dl>")
            return '<div class="t">' + "".join(L) + "</div>"
        P.append('<div class="stats">' + tcol(ta, c["la"], c["away"]) + tcol(th, c["lh"], c["home"]) + "</div>")
        P.append(f'<div class="why"><span class="lab">Honesty</span>{esc(c["honesty"] or "")}</div>')
        P.append("</div></article>")
    s = d["season"]
    P.append('<div class="season">')
    P.append(f'<div class="box"><div class="lab">Season · winners</div><div class="v num">machine {s["machine"]["w"]}–{s["machine"]["l"]}</div><div class="s num">Corey {s["man"]["w"]}–{s["man"]["l"]} · {s["games"]} card games</div></div>')
    P.append(f'<div class="box"><div class="lab">Season · margin miss (score call)</div><div class="v num">machine {s["machine"]["off"]:g}</div><div class="s num">Corey {s["man"]["off"]:g} · lower is better</div></div>')
    P.append(f'<div class="box"><div class="lab">This page</div><div class="v">no market</div><div class="s">the plays number is the efficiency shadow, not the on-air number{"" if d["stat_package"] else " · player lines appear once the stat package is built"}</div></div>')
    P.append("</div>")
    P.append('<div class="foot">The machine\'s call is its score call; "off by" is that margin against the final, the same for both sides. The plays number is the play-by-play efficiency rating\'s margin (a shadow rating); the blend is the 50/50 of the two, a test that is being graded on these cards. Honesty lines are drafted by the machine from the same source as Tale of the Tape.</div></div>')
    return "\n".join(P)


if __name__ == "__main__":
    d = build()
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(render(d), encoding="utf-8")
    print(f"wrote {OUT.relative_to(HERE)} ({OUT.stat().st_size // 1024} KB): week {d['week']} ({'pending' if d['pending'] else 'graded'}), {len(d['cards'])} games, stat package {'yes' if d['stat_package'] else 'no'}")
