"""Hypothetical matchup page: one team's most common offensive set against the
other team's defense in two lineups - the one the last game box shows and a
hypothetical with a named player back (INTERNAL, local HTML, no libs).

  python matchup_page.py --offense Clemson --defense Miami --week 4 --returning "Xavier Lucas" \
      --now "LCB:Ethan O'Connor,RCB:Bryce Fitzgerald,NB:Omar Thornton,FS:Zechariah Poyser,SS:JJ Dunnigan" \
      --hypo "LCB:Ethan O'Connor,RCB:Xavier Lucas,NB:Omar Thornton,FS:Zechariah Poyser,SS:Bryce Fitzgerald" \
      --note "Lucas expected back ~a month after the Sep 5 injury (Yahoo, Sep 2026); Fitzgerald moved from safety to corner in his absence"

Needs both teams' dossier JSON for the week (team_dossier.py). What is DATA:
the offense's tendencies, the defense's numbers with and without the player
(the --split halves), each player's season lines (CFBD season stats, this year
and last). What is NOT data and is labelled so: the lineups (depth chart +
news), the coverage (the card's words), and every "would" in the read.
"""
import argparse, html, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "fpi-decomposition"))
from refresh_all import load_env_key  # noqa: E402
import cfbd_client as cfbd  # noqa: E402
import dossier_page as dp  # noqa: E402
import team_dossier as td  # noqa: E402

OUT = os.path.join(HERE, "film_study", "dossiers")


def season_line(team, year, names):
    out = {n: {} for n in names}
    for cat in ("defensive", "interceptions"):
        try:
            rows = cfbd.get("/stats/player/season", {"year": year, "team": team, "category": cat}, False)
        except Exception:
            rows = []
        for r in rows:
            for n in names:
                if td.same_person(r["player"], n):
                    out[n][("INT" if cat == "interceptions" and r["statType"] == "INT" else r["statType"])] = r["stat"]
    return out


def default_lineup(Dd):
    """Depth-chart starters at the five DB slots who appear in the LAST game box;
    a missing starter is filled by the box DB with the most tackles there."""
    last = Dd["games"][-1]["label"] if Dd["games"] else None
    box = [p for p in Dd["personnel"]["players"] if p["pos"] == "DB"]
    used, out = set(), []
    tk = lambda p: int(m.group(1)) if (m := re.match(r"(\d+)", p["by_game"].get(last, ""))) else 0
    for slot in ("LCB", "RCB", "NB", "FS", "SS"):
        st = next((x for x in Dd["personnel"]["starters"] if x["slot"] == slot and x["rank"] == 1), None)
        name = st["box_name"] if st and st["box_name"] and last in st["by_game"] else None
        if name is None:
            cands = sorted([p for p in box if last in p["by_game"] and not any(td.same_person(p["name"], n) for n in used)], key=lambda p: -tk(p))
            name = cands[0]["name"] if cands else (st["name"] if st else "?")
        used.add(name); out.append((slot, name))
    return out


def parse_lineup(s):
    return [(slot.strip(), name.strip()) for slot, name in (x.split(":", 1) for x in s.split(",") if ":" in x)]


def fmt(v, s=""):
    return "n/a" if v is None else f"{v}{s}"


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>__OFF__ offense vs __DEF__ defense — hypothetical</title>
<style>
:root{--bg:#0f1418;--panel:#161d23;--ink:#e8edf1;--mute:#9aa7b2;--line:#2a3640;--card:#e07a7a;--data:#7bd88f;--hypo:#f2b544}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,Segoe UI,Roboto,sans-serif}
header{padding:18px 20px 6px}h1{margin:0;font-size:22px}h2{font-size:16px;margin:0 0 8px}h3{font-size:14px;margin:10px 0 4px;color:var(--mute)}
.sub{color:var(--mute);font-size:13px}.wrap{display:grid;grid-template-columns:1fr;gap:14px;padding:12px 20px 30px;max-width:1200px}
@media(min-width:980px){.wrap{grid-template-columns:1fr 1fr}.span{grid-column:1/-1}}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px}
canvas{width:100%;height:auto;background:#1d5a2b;border-radius:8px;display:block}
.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:10px;margin-right:6px;font-weight:600}
.tag.data{background:#1e3a29;color:var(--data)}.tag.card{background:#3a1e1e;color:var(--card)}.tag.hypo{background:#3a2f14;color:var(--hypo)}
.ctl{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}button{background:#223040;color:var(--ink);border:1px solid var(--line);border-radius:6px;padding:5px 10px;cursor:pointer;font-size:13px}
button.on{background:#2f4f6f;border-color:#4b7fb3}ul{margin:6px 0 0 0;padding-left:18px}li{margin:3px 0}.why{color:var(--mute);font-size:13px}
table{border-collapse:collapse;width:100%;font-size:13px}td,th{border-bottom:1px solid var(--line);padding:4px 6px;text-align:left;vertical-align:top}th{color:var(--mute);font-weight:600}
.num{font-variant-numeric:tabular-nums}.hl{color:var(--hypo);font-weight:600}
</style></head><body>
<header><h1>__OFF__'s most common set vs __DEF__'s defense — now, and with __RET__ back</h1>
<div class="sub">INTERNAL, hypothetical. <span class="tag data">DATA</span> tendencies and season lines from CFBD. <span class="tag card">CARD</span> the July card's words (coverage). <span class="tag hypo">HYPOTHETICAL</span> the lineups and every "would": depth chart + news, not film. __NOTE__</div></header>
<div class="wrap">
 <div class="panel span"><h2>The picture</h2>
  <canvas id="c" width="900" height="520"></canvas>
  <div class="ctl" id="btns"></div><div id="why" class="why"></div></div>
 <div class="panel"><h2>__OFF__ — the set the numbers say it lives in <span class="tag data">DATA</span></h2><div id="offNums"></div></div>
 <div class="panel"><h2>__DEF__ — with and without __RET__ <span class="tag data">DATA</span></h2><div id="defNums"></div></div>
 <div class="panel"><h2>The secondary, player by player <span class="tag data">DATA</span> <span class="tag hypo">lineup</span></h2><div id="players"></div></div>
 <div class="panel"><h2>The read</h2><div id="read"></div></div>
</div>
<script>
const CFG = __CONFIG__;
__JSCORE__
const off=offense(CFG.off.base,CFG.off.personnel);
let mode='now', conIdx=0;
const btns=document.getElementById('btns');
function mk(label,fn,cls){const b=document.createElement('button');b.textContent=label;b.className=cls||'';b.onclick=fn;btns.appendChild(b);return b;}
const bNow=mk(CFG.plain?'Defense (last box)':'Defense now (last box)',()=>{mode='now';refresh();},'on');
const bHyp=CFG.plain?{className:''}:mk('With '+CFG.ret_short+' back',()=>{mode='hypo';refresh();});
CFG.off.concepts.forEach((c,i)=>mk(c.name,()=>{conIdx=i;refresh();}));
mk('Replay',()=>{replay();});
function refresh(){bNow.className=mode==='now'?'on':'';if(!CFG.plain)bHyp.className=mode==='hypo'?'on':'';replay=animate(document.getElementById('c'),draw);showWhy();}
function lineup(){return mode==='now'?CFG.now:CFG.hypo;}
function dbSpots(){const sh=coverageShell(CFG.coverage,CFG.front);const spots={};sh.db.forEach(p=>{spots[p[2]]=spots[p[2]]||[];spots[p[2]].push(p);});return {sh,spots};}
function draw(t){const ctx=document.getElementById('c').getContext('2d');const c=CFG.off.concepts[conIdx];const lib=CONCEPTS[c.name];
 field(ctx,`${CFG.off_team}: ${c.name} · ${CFG.def_team}: ${CFG.front} · ${CFG.coverage}`+(CFG.plain?'':` · ${mode==='now'?'lineup now':'with '+CFG.ret_short+' back'}`),mode==='now'?'DATA / CARD':'HYPOTHETICAL');
 const d=defense(CFG.front);const {sh}=dbSpots();const L=lineup();
 d.dl.forEach(p=>dot(ctx,p.x,p.y,'#5ab0ff',p.l,9));d.lb.forEach(p=>dot(ctx,p.x,p.y,'#5ab0ff',p.l,9));
 // DBs: assign lineup names to the shell spots (LCB left, RCB right, N, FS, SS)
 const order={LCB:0,RCB:1,NB:2,N:2,FS:3,SS:4,S:3};const cbs=sh.db.filter(p=>p[2]==='CB'),n=sh.db.find(p=>p[2]==='N'),ss=sh.db.filter(p=>p[2]==='S'||p[2]==='FS'||p[2]==='SS');
 const used=new Set();
 L.forEach(([slot,name])=>{let p=null;if(slot==='LCB')p=cbs[0];else if(slot==='RCB')p=cbs[1];else if(slot==='NB'||slot==='N')p=n;else if(slot==='FS')p=ss.find(x=>x[2]==='FS')||ss[0];else if(slot==='SS')p=ss.find(x=>x[2]==='SS')||ss[1]||ss[0];
  if(!p)return;const dv=sh.drop[p[2]]||[0,3];const sur=name.split(' ').filter(w=>!/^(Jr\.?|Sr\.?|II|III|IV)$/.test(w)).pop();
  const isRet=name===CFG.returning, moved=(mode==='hypo'&&CFG.moved.includes(name));
  dot(ctx,lerp(p[0],p[0]+dv[0],t),lerp(p[1],p[1]+dv[1],t),isRet?'#f2b544':(moved?'#ffd98a':'#5ab0ff'),sur,13);});
 const ease=t;const all=[...off.ol.map(p=>({...p,k:'OL'})),{...off.qb,k:'QB'},{...off.rb,k:'RB'},...off.skill.map(p=>({...p,k:p.l}))];
 all.forEach(p=>{let path=lib.routes[p.k];if(p.k==='OL'){const m=lib.routes.OL;path=m==='zoneL'?[[p.x,p.y],[p.x-1.2,p.y+1.5]]:m==='zoneWide'?[[p.x,p.y],[p.x-3,p.y+1.2]]:m==='power'?(p.l==='LG'?[[p.x,p.y],[p.x+6,p.y-0.5],[p.x+7,p.y+2]]:[[p.x,p.y],[p.x+0.8,p.y+1.2]]):m==='screen'?[[p.x,p.y],[p.x+0.5,p.y-2.5],[p.x+8,p.y+3]]:[[p.x,p.y],[p.x,p.y-1.2]];}
  if(!path){path=[[p.x,p.y],[p.x,p.y]];}
  ctx.strokeStyle='rgba(242,181,68,.85)';ctx.lineWidth=2.5;ctx.beginPath();const steps=30;for(let i=0;i<=steps;i++){const q=along(path,ease*i/steps);if(i===0)ctx.moveTo(fx(q[0]),fy(q[1]));else ctx.lineTo(fx(q[0]),fy(q[1]));}ctx.stroke();
  const q=along(path,ease);dot(ctx,q[0],q[1],p.k==='QB'?'#ffd98a':'#f2b544',p.l);});
 ctx.fillStyle='rgba(255,255,255,.9)';ctx.font='12px system-ui';ctx.fillText(`${CFG.off_team}: shotgun ${CFG.off.shotgun_pct}% · ${CFG.off.personnel} personnel · median ${CFG.off.tempo_median} s between snaps · deep-tag ${CFG.off.deep_pct}%`,12,H-12);}
function showWhy(){const c=CFG.off.concepts[conIdx];const lib=CONCEPTS[c.name]||{note:''};
 document.getElementById('why').innerHTML=`<b>${c.name}</b> — <span class="tag ${c.why.startsWith('CARD')?'card':'data'}">${c.why.startsWith('CARD')?'CARD':'DATA'}</span> ${c.why}. ${lib.note}<br>`+
 `Defense: front <span class="tag data">depth chart</span> ${CFG.front}; coverage <span class="tag card">CARD</span> ${CFG.coverage_why}. Lineup <span class="tag hypo">${mode==='now'?'now: '+CFG.now_src:'hypothetical: '+CFG.hypo_src}</span>.`+(CFG.plain?'':` Gold dot = ${CFG.ret_short}; pale dot = a player moved back to his depth-chart slot.`);}
let replay=animate(document.getElementById('c'),draw);showWhy();
document.getElementById('offNums').innerHTML=CFG.off_html;document.getElementById('defNums').innerHTML=CFG.def_html;
document.getElementById('players').innerHTML=CFG.players_html;document.getElementById('read').innerHTML=CFG.read_html;
</script></body></html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offense", required=True); ap.add_argument("--defense", required=True)
    ap.add_argument("--week", type=int, required=True, help="dossier week (games before it)")
    ap.add_argument("--returning", help="player who comes back in the hypothetical (omit for a plain matchup)")
    ap.add_argument("--now", help="SLOT:Name,... (default: depth-chart starters seen in the last box; missing ones filled by the box)")
    ap.add_argument("--hypo", help="SLOT:Name,... for the hypothetical lineup (needs --returning)")
    ap.add_argument("--split", default="after 1", help="the defense's split for with/without (team_dossier --split syntax)")
    ap.add_argument("--note", default="")
    a = ap.parse_args()
    load_env_key()
    slug = lambda t: re.sub(r"[^A-Za-z0-9]+", "_", t).strip("_")
    O = json.load(open(os.path.join(HERE, "internal", "dossiers", f"{slug(a.offense)}_week{a.week}.json"), encoding="utf-8"))
    Dd = json.load(open(os.path.join(HERE, "internal", "dossiers", f"{slug(a.defense)}_week{a.week}.json"), encoding="utf-8"))
    CO = dp.choose(O); CD = dp.choose(Dd)
    # the defense with / without: rebuild the split halves
    games = td.team_games(a.defense, a.week)
    label, is_after = td.parse_split(a.split, games)
    before = td.build(a.defense, a.week, False, [g for g in games if not is_after(g)])
    after = td.build(a.defense, a.week, False, [g for g in games if is_after(g)])
    now = parse_lineup(a.now) if a.now else default_lineup(Dd)
    hypo = parse_lineup(a.hypo) if (a.hypo and a.returning) else now
    plain = not a.returning
    names = sorted({n for _, n in now + hypo})
    this_yr, last_yr = season_line(a.defense, td.YEAR, names), season_line(a.defense, td.YEAR - 1, names)
    box = {p["name"]: p for p in Dd["personnel"]["players"]}
    moved = [n for s, n in hypo if any(s2 != s and n2 == n for s2, n2 in now)]
    ret_short = (a.returning.split()[-1] if len(a.returning.split()) < 3 else a.returning.split()[1]) if a.returning else ""

    # ---- html blocks
    os_, ot = O["offense"]["summary"], O["offense"]["targets"]
    dd = O["offense"]["by_down_distance"]
    off_rows = [("Shotgun / no-huddle tags", f"{fmt(O['offense']['formation']['shotgun_pct'], '%')} / {fmt(O['offense']['formation']['no_huddle_pct'], '%')}"),
                ("Personnel (TE target share)", f"{CO['personnel']} ({CO['te_share']}%)"), ("Median s between snaps", fmt(O['offense']['tempo']['median'])),
                ("Run rate / on 1st down", f"{fmt(round(100 * os_['pbp_runs'] / max(os_['plays'], 1), 1), '%')} / {fmt((dd.get('1st') or {}).get('run_pct'), '%')}"),
                ("Passing", f"{os_['comp']}-of-{os_['att']}, {fmt(os_['ypa'])} per attempt, {os_['p20']} of 20+ in {os_['dropbacks']} dropbacks ({fmt(os_['p20_pct'], '%')}), sacked {os_['sacks']} ({fmt(os_['sack_pct'], '%')})"),
                ("Deep-tag share / where the throws go", f"{fmt(ot['deep_pct'], '%')} / " + ", ".join(f"{k} {v}" for k, v in list(ot['by_direction'].items())[:4])),
                ("Rushing (box)", f"{os_['box_att']}-{os_['box_yds']} ({fmt(os_['box_ypc'])}), runs tagged middle {CO['run_mid_pct']}%"),
                ("Third-and-6+", f"{(dd.get('3rd & 6+') or {}).get('conv', 'n/a')} converted on {(dd.get('3rd & 6+') or {}).get('n', 0)} plays, {fmt((dd.get('3rd & 6+') or {}).get('run_pct'), '%')} run")]
    tg = "".join(f"<tr><td>{html.escape(nm)}</td><td class=num>{t['targets']}</td><td class=num>{t['catches']}-{t['yds']}</td><td class=num>{t['short']}/{t['deep']}</td><td class=num>{t['p20']}</td></tr>" for nm, t in ot["receivers"][:6])
    qbs = [(p["name"], p["by_game"]) for p in O["personnel"]["players"] if p["pos"] == "QB"]
    off_html = ("<table>" + "".join(f"<tr><th>{html.escape(k)}</th><td>{html.escape(v)}</td></tr>" for k, v in off_rows) + "</table>"
                + "<h3>Target tree (targets · catches-yards · short/deep tags · 20+)</h3><table><tr><th>Receiver</th><th>Tgt</th><th>Rec-Yds</th><th>S/D</th><th>20+</th></tr>" + tg + "</table>"
                + "<h3>Quarterbacks by game (player box)</h3><ul>" + "".join(f"<li>{html.escape(n)}: " + " · ".join(f"{g}: {v}" for g, v in bg.items()) + "</li>" for n, bg in qbs) + "</ul>"
                + f"<div class=why>Card: {html.escape(O['card'].get('ob') or '')}</div>")
    bs, as_ = before["defense"]["summary"], after["defense"]["summary"]
    bt, at = before["defense"]["targets"], after["defense"]["targets"]
    b3, a3 = before["defense"]["third_long"].get("3rd & 6+", {}), after["defense"]["third_long"].get("3rd & 6+", {})
    def row(k, x, y):
        return f"<tr><th>{k}</th><td class=num>{x}</td><td class=num>{y}</td></tr>"
    ds, dt = Dd["defense"]["summary"], Dd["defense"]["targets"]
    d3 = Dd["defense"]["third_long"].get("3rd & 6+", {}); sbd = Dd["defense"]["sacks_by_down"]; dz = Dd["defense"]["by_zone"]; drz = Dd["defense"]["red_zone"]
    plain_def_html = ("<table>" + "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in [
        ("Front / coverage", f"{CD['front']} (depth chart) / {html.escape(CD['coverage'])} (card)"),
        ("Passing allowed", f"{ds['comp']}-of-{ds['att']}, {fmt(ds['ypa'])} per attempt, {fmt(ds['ypc'])} per completion, {ds['p20']} of 20+ in {ds['dropbacks']} dropbacks ({fmt(ds['p20_pct'], '%')}), INT {ds['ints']}"),
        ("Deep-tag share faced / where", f"{fmt(dt['deep_pct'], '%')} / " + ", ".join(f"{k} {v}" for k, v in list(dt['by_direction'].items())[:4])),
        ("Sacks", f"{ds['sacks']} ({fmt(ds['sack_pct'], '%')}); by down " + " · ".join(f"{k}: {v['sacks']}/{v['dropbacks']}" for k, v in sbd.items())),
        ("Rush allowed (box) / stuffs / 10+", f"{ds['box_att']}-{ds['box_yds']} ({fmt(ds['box_ypc'])}) / {fmt(ds['stuff_pct'], '%')} / {fmt(ds['r10_pct'], '%')}"),
        ("Third-and-6+ allowed", f"{d3.get('conv', 'n/a')} on {d3.get('n', 0)} plays, explosive {fmt(d3.get('expl_pct'), '%')}, sack {fmt(d3.get('sack_pct'), '%')}"),
        ("Red zone allowed", f"{drz['td']} TD on {drz['trips']} trips ({fmt(drz['td_pct'], '%')})"),
        ("By field zone (yds/play / stuff %)", " · ".join(f"{k}: {fmt(v['ypp'])} / {fmt(v['stuff_pct'], '%')}" for k, v in dz.items()))]) + "</table>"
        + f"<div class=why>Card: {html.escape(Dd['card'].get('db') or '')} {html.escape(Dd['card'].get('dt') or '')}</div>")
    def_html = (f"<table><tr><th></th><th>with ({html.escape('; '.join(g['label'] for g in before['games']))})</th><th>without ({html.escape('; '.join(g['label'] for g in after['games']))})</th></tr>"
                + row("Dropbacks faced", bs["dropbacks"], as_["dropbacks"]) + row("Per attempt allowed", fmt(bs["ypa"]), fmt(as_["ypa"]))
                + row("Per completion", fmt(bs["ypc"]), fmt(as_["ypc"])) + row("20+ passes allowed (rate)", f"{bs['p20']} ({fmt(bs['p20_pct'], '%')})", f"{as_['p20']} ({fmt(as_['p20_pct'], '%')})")
                + row("Deep-tag share faced", fmt(bt["deep_pct"], "%"), fmt(at["deep_pct"], "%")) + row("Sack rate / INT", f"{fmt(bs['sack_pct'], '%')} / {bs['ints']}", f"{fmt(as_['sack_pct'], '%')} / {as_['ints']}")
                + row("3rd-and-6+ allowed", b3.get("conv", "n/a"), a3.get("conv", "n/a")) + row("Rush allowed (box)", f"{bs['box_att']}-{bs['box_yds']} ({fmt(bs['box_ypc'])})", f"{as_['box_att']}-{as_['box_yds']} ({fmt(as_['box_ypc'])})")
                + "</table>" + f"<div class=why>Split: {html.escape(label)}. {bs['dropbacks']} vs {as_['dropbacks']} dropbacks against different opponents; one game per side is a description, not a conclusion.</div>")
    if plain:
        def_html = plain_def_html
    def pl(n):
        ty, ly = this_yr.get(n, {}), last_yr.get(n, {})
        bg = box.get(n, {}).get("by_game", {})
        line = lambda s: (f"{s.get('TOT', '0')} tkl, {s.get('PD', '0')} PD, {s.get('INT', '0')} INT, {s.get('TFL', '0')} TFL" if s else "no line")
        return f"<tr><td><b>{html.escape(n)}</b></td><td>{line(ty)}</td><td>{line(ly)}</td><td>{html.escape(' · '.join(f'{g}: {v}' for g, v in bg.items()) or 'not in any box')}</td></tr>"
    def lu(L, src):
        return "<ul>" + "".join(f"<li>{s}: <span class='{'hl' if n == a.returning or n in moved else ''}'>{html.escape(n)}</span></li>" for s, n in L) + f"</ul><div class=why>{html.escape(src)}</div>"
    now_src = "now = who the last game box shows plus the news; slots are inferred, CFBD has no alignment"
    hypo_src = f"hypothetical = {a.returning} in his depth-chart slot, {', '.join(moved) or 'nobody'} back to his own"
    players_html_plain = (f"<h3>Lineup now <span class='tag hypo'>inferred</span></h3>{lu(now, now_src)}"
                          + f"<h3>Season lines</h3><table><tr><th>Player</th><th>{td.YEAR}</th><th>{td.YEAR - 1}</th><th>{td.YEAR} game by game</th></tr>" + "".join(pl(n) for n in names) + "</table>")
    players_html = (f"<h3>Lineup now <span class='tag hypo'>inferred</span></h3>{lu(now, now_src)}<h3>With {html.escape(ret_short)} back <span class='tag hypo'>hypothetical</span></h3>{lu(hypo, hypo_src)}"
                    + f"<h3>Season lines</h3><table><tr><th>Player</th><th>{td.YEAR}</th><th>{td.YEAR - 1}</th><th>{td.YEAR} game by game</th></tr>" + "".join(pl(n) for n in names) + "</table>")
    # the read - built from the numbers, hedged where it must be
    deep_now = at["deep_pct"] or 0
    read = [f"<ul><li><span class='tag data'>DATA</span> {html.escape(a.offense)} is a {CO['base']}, {CO['personnel']}-personnel offense that throws short: {fmt(ot['deep_pct'], '%')} deep tags, {fmt(os_['ypa'])} a throw, {os_['p20']} passes of 20+ in {os_['dropbacks']} dropbacks. The corners' job against it is tackling short throws to the boundary and fitting the quarterback run, not defending shots.</li>",
            f"<li><span class='tag data'>DATA</span> {html.escape(a.defense)} without {html.escape(ret_short)}: {fmt(as_['ypa'])} a throw allowed, {as_['p20']} of 20+ in {as_['dropbacks']} dropbacks, opponents took deep shots on {fmt(deep_now, '%')} of throws (was {fmt(bt['deep_pct'], '%')} with him, one game).</li>",
            f"<li><span class='tag hypo'>HYPOTHETICAL</span> With {html.escape(a.returning or "")} back the second-order move is the one the numbers care about: {html.escape(', '.join(moved) or 'nobody')} returns to his own slot. Last year's lines say what each does: " + "; ".join(f"{html.escape(n)} {last_yr.get(n, {}).get('PD', '0')} PD / {last_yr.get(n, {}).get('INT', '0')} INT" for n in (([a.returning] if a.returning else []) + moved)) + ".</li>",
            f"<li><span class='tag card'>CARD</span> {html.escape(Dd['card'].get('db') or '')} Whether that shell changes with the personnel is a film question; nothing in CFBD says.</li>",
            f"<li>Sample: one game with him, {as_['dropbacks']} dropbacks without. Nothing here is a prediction, and the machine's number for the game is untouched.</li></ul>"]
    if plain:
        players_html = players_html_plain
        pct_run = round(100 * os_['pbp_runs'] / max(os_['plays'], 1), 1)
        read = [f"<ul><li><span class='tag data'>DATA</span> {html.escape(a.offense)} lives in {CO['base']}, {CO['personnel']} personnel ({CO['te_share']}% of targets to tight ends), {pct_run}% run, runs tagged middle {CO['run_mid_pct']}%; passing {fmt(os_['ypa'])} a throw with {fmt(ot['deep_pct'], '%')} deep tags and {os_['p20']} of 20+ in {os_['dropbacks']} dropbacks.</li>",
                f"<li><span class='tag data'>DATA</span> {html.escape(a.defense)} allows {fmt(ds['ypa'])} a throw and {fmt(ds['p20_pct'], '%')} explosive passes per dropback, {fmt(ds['box_ypc'])} a carry with a {fmt(ds['stuff_pct'], '%')} stuff rate; {ds['sacks']} sacks, {sbd['3']['sacks']} of them on third down; third-and-6+ {d3.get('conv', 'n/a')}.</li>",
                f"<li><span class='tag data'>DATA</span> Where the two meet: the offense runs middle {CO['run_mid_pct']}% of the time into a front stuffing {fmt(ds['stuff_pct'], '%')} of runs; its deep-tag rate is {fmt(ot['deep_pct'], '%')} against a defense that has faced {fmt(dt['deep_pct'], '%')} deep and allowed {ds['p20']} of 20+.</li>",
                f"<li><span class='tag card'>CARD</span> {html.escape(Dd['card'].get('db') or '')} Coverage on the picture is the card's word, or Cover 3 as a stated default.</li>",
                f"<li>Nothing here is a prediction; the machine's number for the game is untouched.</li></ul>"]
    cfg = dict(off_team=a.offense, def_team=a.defense, off=CO, front=CD["front"], coverage=CD["coverage"], coverage_why=CD["coverage_why"],
               now=now, hypo=hypo, returning=a.returning or "", ret_short=ret_short, moved=moved, now_src=now_src, hypo_src=hypo_src, plain=plain,
               off_html=off_html, def_html=def_html, players_html=players_html, read_html="".join(read))
    tpl = TEMPLATE
    if plain:
        tpl = (tpl.replace("\u2014 now, and with __RET__ back", "\u2014 the sets the numbers say each lives in")
                  .replace('<h2>__DEF__ \u2014 with and without __RET__ <span class="tag data">DATA</span></h2>', '<h2>__DEF__ \u2014 what it does <span class="tag data">DATA</span></h2>')
                  .replace("hypothetical. <span", "matchup. <span").replace("<title>__OFF__ offense vs __DEF__ defense — hypothetical</title>", "<title>__OFF__ offense vs __DEF__ defense</title>"))
    page = (tpl.replace("__OFF__", html.escape(a.offense)).replace("__DEF__", html.escape(a.defense)).replace("__RET__", html.escape(ret_short))
            .replace("__NOTE__", html.escape(a.note)).replace("__CONFIG__", json.dumps(cfg)).replace("__JSCORE__", dp.JS_CORE))
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, f"{slug(a.offense)}_off_vs_{slug(a.defense)}_def" + ("" if plain else "_hypo") + ".html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print("wrote", os.path.relpath(out, HERE))


if __name__ == "__main__":
    main()
