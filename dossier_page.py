"""Per-team animation page from a dossier JSON (INTERNAL, local HTML, no libs).

  python dossier_page.py --week 4                 # every internal/dossiers/*_week4.json -> film_study/dossiers/<Team>.html + index.html
  python dossier_page.py --week 4 --team Miami

Each page: the base offensive formation (shotgun vs under center and the
personnel grouping are DECIDED BY THE DOSSIER'S NUMBERS), two signature
concepts (chosen from the tendencies; the card's words can add one), the base
defensive front (depth-chart label) and the coverage the CARD describes, the
season-to-date numbers that drove each choice, and the five plays to find on
film. Every drawing says whether it came from DATA or from the CARD - CFBD has
no alignment or coverage tags, so the defensive pictures are the card's
description, not film."""
import argparse, glob, html, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
IN = os.path.join(HERE, "internal", "dossiers")
OUT = os.path.join(HERE, "film_study", "dossiers")


def fmt(v, s=""):
    return "n/a" if v is None else f"{v}{s}"


def initial_key(nm):
    """'E.Lofton' / 'Mark Fletcher Jr.' -> ('e', 'lofton')"""
    t = re.sub(r"\b(Jr|Sr|II|III|IV)\b\.?", " ", html.unescape(nm))
    t = re.sub(r"[^A-Za-z\. ]", "", t).replace(".", " ").split()
    return (t[0][0].lower(), t[-1].lower()) if t else ("", "")


def positions(D):
    return {initial_key(p["name"]): p["pos"] for p in D["personnel"]["players"]}


def choose(D):
    """Turn the dossier's tendencies into drawing decisions, with the reason."""
    o, d = D["offense"], D["defense"]
    F, T, TT, S = o["formation"], o["tempo"], o["targets"], o["summary"]
    pos = positions(D)
    card = (D["card"].get("ob") or "") + " " + (D["card"].get("ot") or "")
    cardl = card.lower()
    # personnel: TE share of targets decides 11 vs 12; four wideouts if TEs get almost nothing
    tgt_total = sum(t["targets"] for _, t in TT["receivers"]) or 1
    te_tgts = sum(t["targets"] for nm, t in TT["receivers"] if pos.get(initial_key(nm)) == "TE")
    rb_tgts = sum(t["targets"] for nm, t in TT["receivers"] if pos.get(initial_key(nm)) == "RB")
    te_share = round(100 * te_tgts / tgt_total, 1)
    if te_share >= 18 or "12 personnel" in cardl:
        personnel, p_why = "12", f"tight ends draw {te_share}% of targets" + (" and the card says 12 personnel" if "12 personnel" in cardl else "")
    elif te_share < 6:
        personnel, p_why = "10", f"tight ends draw only {te_share}% of targets - four wideouts"
    else:
        personnel, p_why = "11", f"tight ends draw {te_share}% of targets - one TE, three WR"
    sg = F["shotgun_pct"] or 0
    base = "shotgun" if sg >= 70 else ("pistol/under center mix" if sg >= 40 else "under center")
    nh = F["no_huddle_pct"] or 0
    tempo_word = "tempo" if nh >= 60 else ("some tempo" if nh >= 30 else "huddle")
    # run concept
    rd = o["rush_dir"]; runs = sum(v for k, v in rd.items() if k != "untagged") or 1
    mid = round(100 * rd.get("middle", 0) / runs)
    qb_runs = any(pos.get(initial_key(w.split(" to ")[0])) == "QB" and " to " not in w for w, n in o["explosives"]["sources"])
    # national share of runs tagged middle is ~59% (week 3 file); read the team against that
    if "wide zone" in cardl or "outside zone" in cardl:
        run = ("Wide zone", f"CARD names wide zone; {mid}% of runs are tagged middle (FBS ~59%)")
    elif mid >= 65:
        run = ("Inside zone", f"DATA: {mid}% of runs tagged middle, well above the FBS ~59%")
    elif mid >= 50:
        run = ("Inside zone", f"DATA: {mid}% of runs tagged middle, near the FBS ~59% - a zone mix, drawn as inside zone")
    else:
        run = ("Outside zone / stretch", f"DATA: only {mid}% of runs tagged middle (FBS ~59%) - the run game gets to the edge")
    if ("qb run" in cardl or "legs" in cardl or qb_runs) and personnel != "12":
        run2 = ("QB power read", "CARD/DATA: the quarterback is a base part of the run game")
    else:
        run2 = None
    # pass concept
    deep = TT["deep_pct"] or 0
    byd = TT["by_direction"]
    side = sum(v for k, v in byd.items() if "left" in k or "right" in k); midp = sum(v for k, v in byd.items() if "middle" in k)
    if deep >= 16 or "vertical" in cardl and deep >= 12:
        pas = ("Four verticals (seam shot)", f"DATA: {deep}% of tagged throws are deep" + ("; CARD says vertical" if "vertical" in cardl else ""))
    elif "rpo" in cardl and deep < 12:
        pas = ("RPO glance", f"CARD names RPOs; deep-tag rate only {deep}%")
    elif "screen" in cardl:
        pas = ("Screen game", f"CARD names the screen game; deep-tag rate {deep}%")
    elif "play-action" in cardl or "play action" in cardl:
        pas = ("Play-action flood", f"CARD names play-action; deep-tag rate {deep}%")
    elif midp and midp / max(side + midp, 1) >= 0.25:
        pas = ("Mesh (crossers)", f"DATA: {round(100 * midp / (side + midp))}% of throws tagged middle")
    else:
        pas = ("Quick game to the boundary", f"DATA: {round(100 * side / max(side + midp, 1))}% of throws tagged left/right, deep-tag rate {deep}%")
    concepts = [run, pas] if not run2 else [run2, pas]
    # defensive front from the depth-chart label
    ds = (D["depth"].get("def_scheme") or "").lower()
    front = "3-4" if "3-4" in ds else ("3-3-5" if "3-3-5" in ds else ("4-3" if "4-3" in ds else "4-2-5"))
    front_why = f"depth-chart label '{D['depth'].get('def_scheme')}' (OurLads {D['depth'].get('updated')})"
    dcard = ((D["card"].get("db") or "") + " " + (D["card"].get("dt") or "")).lower()
    if re.search(r"\bman-heavy\b|\bman coverage\b|\bman-to-man\b|\bpress\b(?!ure)", dcard):
        cov = ("Cover 1 (man, single high)", "CARD: man-heavy")
    elif "split-safety" in dcard or "two-high" in dcard or "quarters" in dcard or "pattern-match" in dcard:
        cov = ("Quarters (pattern-match, two high)", "CARD: split-safety / pattern-match")
    elif "sim" in dcard or "simulated" in dcard:
        cov = ("Cover 3 behind a simulated pressure", "CARD: simulated pressures - the shell behind them is not described; Cover 3 drawn as the default")
    else:
        cov = ("Cover 3 (default - the card does not describe the shell)", "no coverage words on the card")
    sim = "sim" in dcard or "pressure" in dcard
    return dict(personnel=personnel, personnel_why=p_why, base=base, shotgun_pct=sg, no_huddle_pct=nh, tempo_word=tempo_word,
                tempo_median=T["median"], concepts=[dict(name=c[0], why=c[1]) for c in concepts], front=front, front_why=front_why,
                coverage=cov[0], coverage_why=cov[1], sim_pressure=sim, te_share=te_share, rb_share=round(100 * rb_tgts / tgt_total, 1),
                deep_pct=deep, run_mid_pct=mid, sack_pct=d["summary"]["sack_pct"], stuff_pct=d["summary"]["stuff_pct"],
                p20_allowed=d["summary"]["p20_pct"], deep_faced=d["targets"]["deep_pct"])


JS_CORE = r"""// ---------- field ----------
const W=900,H=520, YPX=9.5, XPX=W/53.33;            // yards -> px; x across the field, y = depth (0 = the ball)
function fx(x){return W/2 + x*XPX}  function fy(y){return 330 - y*YPX}    // y>0 is downfield
function field(ctx,title,tag){ctx.clearRect(0,0,W,H);ctx.fillStyle='#1d5a2b';ctx.fillRect(0,0,W,H);
 ctx.strokeStyle='rgba(255,255,255,.35)';ctx.lineWidth=1;
 for(let y=-15;y<=20;y+=5){ctx.beginPath();ctx.moveTo(0,fy(y));ctx.lineTo(W,fy(y));ctx.stroke();}
 ctx.strokeStyle='rgba(255,255,255,.7)';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(0,fy(0));ctx.lineTo(W,fy(0));ctx.stroke();
 ctx.setLineDash([4,6]);ctx.strokeStyle='rgba(255,255,255,.4)';[-6.2,6.2].forEach(h=>{ctx.beginPath();ctx.moveTo(fx(h),0);ctx.lineTo(fx(h),H);ctx.stroke();});ctx.setLineDash([]);
 ctx.fillStyle='rgba(255,255,255,.9)';ctx.font='bold 15px system-ui';ctx.fillText(title,12,22);
 if(tag){ctx.font='12px system-ui';ctx.fillStyle=tag==='CARD'?'#ffb3b3':'#b6f2c4';ctx.fillText(tag,12,40);}}
function dot(ctx,x,y,color,label,r=11){ctx.beginPath();ctx.arc(fx(x),fy(y),r,0,Math.PI*2);ctx.fillStyle=color;ctx.fill();ctx.strokeStyle='rgba(0,0,0,.5)';ctx.stroke();
 ctx.fillStyle='#111';ctx.font='bold 10px system-ui';ctx.textAlign='center';ctx.fillText(label,fx(x),fy(y)+4);ctx.textAlign='left';}
function lerp(a,b,t){return a+(b-a)*t}
function along(path,t){ // path = [[x,y],...], t in 0..1
 const n=path.length-1; if(n<1) return path[0]; const s=Math.min(t*n,n-1e-6), i=Math.floor(s), f=s-i;
 return [lerp(path[i][0],path[i+1][0],f), lerp(path[i][1],path[i+1][1],f)];}
// ---------- offensive formations (x across, y depth; negative y = behind the ball) ----------
function offense(base,personnel){
 const OL=[[-4.5,-0.6,'LT'],[-2.3,-0.6,'LG'],[0,-0.6,'C'],[2.3,-0.6,'RG'],[4.5,-0.6,'RT']].map(p=>({x:p[0],y:p[1],l:p[2]}));
 const gun=base==='shotgun'; const qb={x:0,y:gun?-5:-1.6,l:'QB'}; const rb={x:gun?1.6:0,y:gun?-5.2:-6.5,l:'RB'};
 let skill=[];
 if(personnel==='12'){skill=[{x:-6.5,y:-0.6,l:'TE'},{x:6.5,y:-0.6,l:'TE'},{x:-20,y:-0.8,l:'X'},{x:21,y:-1.2,l:'Z'}];}
 else if(personnel==='10'){skill=[{x:-22,y:-0.8,l:'X'},{x:-13,y:-1.4,l:'H'},{x:14,y:-1.4,l:'Y'},{x:22,y:-0.8,l:'Z'}];}
 else{skill=[{x:6.5,y:-0.6,l:'TE'},{x:-22,y:-0.8,l:'X'},{x:-13,y:-1.4,l:'SL'},{x:22,y:-0.8,l:'Z'}];}
 return {ol:OL,qb,rb,skill};}
// ---------- concepts: routes as waypoint paths keyed by label ----------
const CONCEPTS={
 'Inside zone':{routes:{RB:[[1.6,-5.2],[-1,-2],[-1,6],[0,14]],QB:[[0,-5],[0.8,-4.5],[0.8,-4.5]],OL:'zoneL'},note:'Combo blocks front side, back reads the first down lineman past the center; the cut is one gap at a time.'},
 'Wide zone':{routes:{RB:[[1.6,-5.2],[-6,-3],[-10,2],[-12,12]],QB:[[0,-5],[1,-4.5],[1,-4.5]],OL:'zoneWide'},note:'Whole line steps play side; the back aims at the tackle\'s outside hip and reads bounce, bang or bend.'},
 'Outside zone / stretch':{routes:{RB:[[1.6,-5.2],[-7,-3],[-12,3],[-15,12]],QB:[[0,-5],[1,-4.5],[1,-4.5]],OL:'zoneWide'},note:'Reach blocks on the edge; the back presses the sideline and cuts up when the alley opens.'},
 'QB power read':{routes:{QB:[[0,-5],[3,-4],[6,2],[9,12]],RB:[[1.6,-5.2],[-4,-3],[-8,-1],[-10,-1]],OL:'power'},note:'Backside guard pulls; the quarterback reads the end - give the sweep or keep inside the pull.'},
 'Four verticals (seam shot)':{routes:{X:[[-22,-0.8],[-20,20],[-19,30]],SL:[[-13,-1.4],[-8,12],[-6,30]],H:[[-13,-1.4],[-8,12],[-6,30]],Y:[[14,-1.4],[8,12],[6,30]],TE:[[6.5,-0.6],[8,12],[7,30]],Z:[[22,-0.8],[20,20],[19,30]],RB:[[1.6,-5.2],[3,-2],[10,-1]],QB:[[0,-5],[0,-7],[0,-7]]},note:'Two seams bend off the safeties; the quarterback throws the seam the safety leaves.'},
 'RPO glance':{routes:{X:[[-22,-0.8],[-18,7],[-10,12]],SL:[[-13,-1.4],[-10,5],[-10,5]],H:[[-13,-1.4],[-10,5],[-10,5]],Y:[[14,-1.4],[16,4],[16,4]],TE:[[6.5,-0.6],[7,3],[7,3]],Z:[[22,-0.8],[22,4],[22,4]],RB:[[1.6,-5.2],[-1,-2],[-1,5]],QB:[[0,-5],[0.5,-4.5],[0.5,-4.5]],OL:'zoneL'},note:'Inside zone with a glance (skinny post) attached; the quarterback reads the overhang or the safety and pulls the ball when the box is loaded.'},
 'Mesh (crossers)':{routes:{X:[[-22,-0.8],[-10,4],[10,5],[20,6]],Z:[[22,-0.8],[10,3],[-10,4],[-20,5]],SL:[[-13,-1.4],[-12,10],[-6,12]],H:[[-13,-1.4],[-12,10],[-6,12]],Y:[[14,-1.4],[14,8],[20,10]],TE:[[6.5,-0.6],[8,8],[12,10]],RB:[[1.6,-5.2],[6,-3],[12,-2]],QB:[[0,-5],[0,-6.5],[0,-6.5]]},note:'Two shallow crossers rub under a sit route; against man the crossers win, against zone the sit and the wheel do.'},
 'Quick game to the boundary':{routes:{X:[[-22,-0.8],[-22,4],[-25,5]],SL:[[-13,-1.4],[-13,5],[-8,6]],H:[[-13,-1.4],[-13,5],[-8,6]],Y:[[14,-1.4],[14,5],[19,6]],TE:[[6.5,-0.6],[7,5],[12,6]],Z:[[22,-0.8],[22,4],[25,5]],RB:[[1.6,-5.2],[3,-4],[10,-2]],QB:[[0,-5],[0,-5.5],[0,-5.5]]},note:'Three-step timing: hitch/out to the short side, the ball is out before the corner can squeeze.'},
 'Screen game':{routes:{RB:[[1.6,-5.2],[4,-4],[9,-2],[16,6]],X:[[-22,-0.8],[-20,6],[-18,10]],Z:[[22,-0.8],[16,1],[12,3]],Y:[[14,-1.4],[12,2],[9,4]],TE:[[6.5,-0.6],[9,2],[9,4]],SL:[[-13,-1.4],[-12,6],[-12,6]],H:[[-13,-1.4],[-12,6],[-12,6]],QB:[[0,-5],[-1,-8],[-1,-8]],OL:'screen'},note:'Linemen invite the rush and release; the back slips out behind a convoy.'},
 'Play-action flood':{routes:{RB:[[1.6,-5.2],[-1,-2],[-2,-1]],TE:[[6.5,-0.6],[9,8],[20,10]],Y:[[14,-1.4],[16,8],[24,12]],Z:[[22,-0.8],[22,15],[24,22]],X:[[-22,-0.8],[-18,12],[-8,16]],SL:[[-13,-1.4],[-8,4],[8,4]],H:[[-13,-1.4],[-8,4],[8,4]],QB:[[0,-5],[-1,-3],[4,-6],[6,-6]]},note:'Zone fake, quarterback boots; three levels to one side - go, out, flat - stretch a single defender.'}};
// ---------- defenses ----------
function defense(front){
 let dl=[],lb=[];
 if(front==='3-4'){dl=[[-4.2,1.2,'DE'],[0,1.2,'NT'],[4.2,1.2,'DE']];lb=[[-8,4,'OLB'],[-2.2,4.5,'ILB'],[2.2,4.5,'ILB'],[8,4,'OLB']];}
 else if(front==='3-3-5'){dl=[[-4.2,1.2,'DE'],[0,1.2,'NT'],[4.2,1.2,'DE']];lb=[[-5,4.5,'W'],[0,5,'M'],[5,4.5,'S']];}
 else if(front==='4-3'){dl=[[-6.5,1.2,'DE'],[-2.2,1.2,'DT'],[2.2,1.2,'DT'],[6.5,1.2,'DE']];lb=[[-5,4.5,'W'],[0,5,'M'],[5,4.5,'S']];}
 else {dl=[[-6.5,1.2,'DE'],[-2.2,1.2,'DT'],[2.2,1.2,'DT'],[6.5,1.2,'DE']];lb=[[-3,4.5,'W'],[3,4.5,'M']];}
 return {dl:dl.map(p=>({x:p[0],y:p[1],l:p[2]})),lb:lb.map(p=>({x:p[0],y:p[1],l:p[2]}))};}
function coverageShell(cov,front){
 const nickel = front!=='4-3' && front!=='3-4';
 if(cov.startsWith('Cover 1')) return {db:[[-20,6,'CB'],[20,6,'CB'],[-11,5,'N'],[0,13,'FS'],[8,7,'SS']].filter((p,i)=>nickel||i!==2),drop:{CB:[0,-1],N:[0,-1],FS:[0,4],SS:[-3,2]},label:'man on the receivers, one safety in the middle'};
 if(cov.startsWith('Quarters')) return {db:[[-20,7,'CB'],[20,7,'CB'],[-11,5,'N'],[-7,12,'S'],[7,12,'S']].filter((p,i)=>nickel||i!==2),drop:{CB:[0,6],N:[0,3],S:[0,4]},label:'two high, each safety reads the No. 2 receiver - pattern-match'};
 return {db:[[-20,7,'CB'],[20,7,'CB'],[-11,5,'N'],[0,13,'FS'],[9,8,'SS']].filter((p,i)=>nickel||i!==2),drop:{CB:[-2,6],N:[2,3],FS:[0,5],SS:[-4,0]},label:'three deep, four under'};}
// ---------- animation ----------
function animate(canvas,draw,dur=3200){let start=null;let raf;function frame(ts){if(!start)start=ts;const t=Math.min((ts-start)/dur,1);draw(t);if(t<1)raf=requestAnimationFrame(frame);}cancelAnimationFrame(raf);start=null;raf=requestAnimationFrame(frame);return()=>{cancelAnimationFrame(raf);start=null;raf=requestAnimationFrame(frame);};}
"""

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TEAM__ — scheme page</title>
<style>
:root{--bg:#0f1418;--panel:#161d23;--ink:#e8edf1;--mute:#9aa7b2;--line:#2a3640;--off:#f2b544;--def:#5ab0ff;--ball:#c9743a;--ok:#7bd88f;--card:#e07a7a;--data:#7bd88f}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,Segoe UI,Roboto,sans-serif}
header{padding:18px 20px 6px}h1{margin:0;font-size:22px}h2{font-size:16px;margin:0 0 8px;color:var(--ink)}
.sub{color:var(--mute);font-size:13px}.wrap{display:grid;grid-template-columns:1fr;gap:14px;padding:12px 20px 30px;max-width:1200px}
@media(min-width:980px){.wrap{grid-template-columns:1fr 1fr}}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:12px}
canvas{width:100%;height:auto;background:#1d5a2b;border-radius:8px;display:block}
.tag{display:inline-block;font-size:11px;padding:1px 7px;border-radius:10px;margin-right:6px;font-weight:600}
.tag.data{background:#1e3a29;color:var(--data)}.tag.card{background:#3a1e1e;color:var(--card)}
.ctl{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}button{background:#223040;color:var(--ink);border:1px solid var(--line);border-radius:6px;padding:5px 10px;cursor:pointer;font-size:13px}
button.on{background:#2f4f6f;border-color:#4b7fb3}ul{margin:6px 0 0 0;padding-left:18px}li{margin:3px 0}.why{color:var(--mute);font-size:13px}
table{border-collapse:collapse;width:100%;font-size:13px}td,th{border-bottom:1px solid var(--line);padding:4px 6px;text-align:left}th{color:var(--mute);font-weight:600}
.watch li{font-size:13px}.num{font-variant-numeric:tabular-nums}
</style></head><body>
<header><h1>__TEAM__ — base looks and signature concepts, through Week __WK__</h1>
<div class="sub">INTERNAL. Built from internal/dossiers/__SLUG___week__W__.json. <span class="tag data">DATA</span> = decided by the play-by-play numbers. <span class="tag card">CARD</span> = the July scouting card's words. CFBD has no alignment or coverage tags: the defensive pictures are the card's description, not film.</div></header>
<div class="wrap">
 <div class="panel"><h2>Offense — base formation <span class="tag data">DATA</span></h2>
  <canvas id="cOff" width="900" height="520"></canvas>
  <div class="ctl"><button id="bOff">Replay</button></div>
  <div id="offWhy" class="why"></div></div>
 <div class="panel"><h2>Signature concepts</h2>
  <canvas id="cCon" width="900" height="520"></canvas>
  <div class="ctl" id="conBtns"></div><div id="conWhy" class="why"></div></div>
 <div class="panel"><h2>Defense — base front <span class="tag data">depth chart</span> and coverage <span class="tag card">CARD</span></h2>
  <canvas id="cDef" width="900" height="520"></canvas>
  <div class="ctl"><button id="bDef">Replay</button><button id="bSim">Toggle sim pressure</button></div>
  <div id="defWhy" class="why"></div></div>
 <div class="panel"><h2>The numbers behind the drawings</h2><div id="nums"></div>
  <h2 style="margin-top:12px">What to watch for — five plays (game, quarter, clock)</h2><ul class="watch" id="watch"></ul></div>
</div>
<script>
const CFG = __CONFIG__;
__JSCORE__const off=offense(CFG.base,CFG.personnel);
function drawOff(t){const ctx=document.getElementById('cOff').getContext('2d');field(ctx,`Base look: ${CFG.base}, ${CFG.personnel} personnel`,'DATA');
 // players jog in from a huddle spot
 const hud=[0,-9];const ease=t<1?1-Math.pow(1-t,3):1;
 off.ol.forEach(p=>dot(ctx,lerp(hud[0],p.x,ease),lerp(hud[1],p.y,ease),'#f2b544',p.l));
 dot(ctx,lerp(hud[0],off.qb.x,ease),lerp(hud[1],off.qb.y,ease),'#ffd98a','QB');dot(ctx,lerp(hud[0],off.rb.x,ease),lerp(hud[1],off.rb.y,ease),'#f2b544','RB');
 off.skill.forEach(p=>dot(ctx,lerp(hud[0],p.x,ease),lerp(hud[1],p.y,ease),'#f2b544',p.l));
 ctx.beginPath();ctx.ellipse(fx(0),fy(0),5,3.5,0,0,Math.PI*2);ctx.fillStyle='#c9743a';ctx.fill();
 ctx.fillStyle='rgba(255,255,255,.9)';ctx.font='12px system-ui';ctx.fillText(`shotgun ${CFG.shotgun_pct}% · no-huddle ${CFG.no_huddle_pct}% · median ${CFG.tempo_median} s between snaps`,12,H-12);}
let offReplay=animate(document.getElementById('cOff'),drawOff);document.getElementById('bOff').onclick=()=>offReplay();
document.getElementById('offWhy').innerHTML=`<span class="tag data">DATA</span> ${CFG.base}: shotgun on ${CFG.shotgun_pct}% of tagged snaps. Personnel ${CFG.personnel}: ${CFG.personnel_why}. Tempo: ${CFG.tempo_word} (${CFG.no_huddle_pct}% no-huddle tags, median ${CFG.tempo_median} s of game clock between snaps in the same drive). The wideout splits and depths are a generic drawing; CFBD has no alignment data.`;
// concepts
let conIdx=0;const btns=document.getElementById('conBtns');
CFG.concepts.forEach((c,i)=>{const b=document.createElement('button');b.textContent=c.name;b.className=i===0?'on':'';b.onclick=()=>{conIdx=i;[...btns.children].forEach((x,j)=>x.className=j===i?'on':'');conReplay=animate(document.getElementById('cCon'),drawCon);showCon();};btns.appendChild(b);});
const rb2=document.createElement('button');rb2.textContent='Replay';rb2.onclick=()=>conReplay();btns.appendChild(rb2);
function showCon(){const c=CFG.concepts[conIdx];const lib=CONCEPTS[c.name]||{note:''};document.getElementById('conWhy').innerHTML=`<b>${c.name}</b> — <span class="tag ${c.why.startsWith('CARD')?'card':'data'}">${c.why.startsWith('CARD')?'CARD':'DATA'}</span> ${c.why}.<br>${lib.note}`;}
function drawCon(t){const ctx=document.getElementById('cCon').getContext('2d');const c=CFG.concepts[conIdx];const lib=CONCEPTS[c.name];field(ctx,c.name,c.why.startsWith('CARD')?'CARD':'DATA');
 const d=defense(CFG.front);const sh=coverageShell(CFG.coverage,CFG.front);
 d.dl.forEach(p=>dot(ctx,p.x,p.y,'#5ab0ff',p.l,9));d.lb.forEach(p=>dot(ctx,p.x,p.y,'#5ab0ff',p.l,9));sh.db.forEach(p=>dot(ctx,p[0],p[1],'#5ab0ff',p[2],9));
 const ease=t;const all=[...off.ol.map(p=>({...p,k:'OL'})),{...off.qb,k:'QB'},{...off.rb,k:'RB'},...off.skill.map(p=>({...p,k:p.l}))];
 all.forEach(p=>{let path=lib.routes[p.k];if(p.k==='OL'){const m=lib.routes.OL;path=m==='zoneL'?[[p.x,p.y],[p.x-1.2,p.y+1.5]]:m==='zoneWide'?[[p.x,p.y],[p.x-3,p.y+1.2]]:m==='power'?(p.l==='LG'?[[p.x,p.y],[p.x+6,p.y-0.5],[p.x+7,p.y+2]]:[[p.x,p.y],[p.x+0.8,p.y+1.2]]):m==='screen'?[[p.x,p.y],[p.x+0.5,p.y-2.5],[p.x+8,p.y+3]]:[[p.x,p.y],[p.x,p.y-1.2]];}
  if(!path){path=[[p.x,p.y],[p.x,p.y]];}
  // draw the route line then the player
  ctx.strokeStyle='rgba(242,181,68,.85)';ctx.lineWidth=2.5;ctx.beginPath();const steps=30;for(let i=0;i<=steps;i++){const q=along(path,ease*i/steps);if(i===0)ctx.moveTo(fx(q[0]),fy(q[1]));else ctx.lineTo(fx(q[0]),fy(q[1]));}ctx.stroke();
  const q=along(path,ease);dot(ctx,q[0],q[1],p.k==='QB'?'#ffd98a':'#f2b544',p.l);});
 // ball: from QB to the primary target at the end
 const prim=Object.entries(lib.routes).filter(([k])=>k!=='OL'&&k!=='QB').sort((a,b)=>b[1].length-a[1].length)[0];
 if(t>0.55&&prim&&off.skill.concat([off.rb]).some(p=>p.l===prim[0])){const q0=along(lib.routes.QB||[[0,-5],[0,-5]],1),q1=along(prim[1],1);const u=(t-0.55)/0.45;ctx.beginPath();ctx.ellipse(fx(lerp(q0[0],q1[0],u)),fy(lerp(q0[1],q1[1],u))-30*Math.sin(Math.PI*u),5,3.5,0,0,Math.PI*2);ctx.fillStyle='#c9743a';ctx.fill();}}
let conReplay=animate(document.getElementById('cCon'),drawCon);showCon();
// defense
let sim=CFG.sim_pressure;
function drawDef(t){const ctx=document.getElementById('cDef').getContext('2d');field(ctx,`${CFG.front} front · ${CFG.coverage}`,'CARD');
 off.ol.forEach(p=>dot(ctx,p.x,p.y,'rgba(242,181,68,.5)',p.l,9));dot(ctx,off.qb.x,off.qb.y,'rgba(255,217,138,.6)','QB',9);dot(ctx,off.rb.x,off.rb.y,'rgba(242,181,68,.5)','RB',9);off.skill.forEach(p=>dot(ctx,p.x,p.y,'rgba(242,181,68,.5)',p.l,9));
 const d=defense(CFG.front);const sh=coverageShell(CFG.coverage,CFG.front);const ease=t;
 d.dl.forEach((p,i)=>{let tx=p.x,ty=p.y-3.5; if(sim&&i===d.dl.length-1){tx=p.x+1;ty=p.y+3;} dot(ctx,lerp(p.x,tx,ease),lerp(p.y,ty,ease),'#5ab0ff',p.l);});
 d.lb.forEach((p,i)=>{let tx=p.x,ty=p.y+2; if(sim&&i===0){tx=-1;ty=-2;} dot(ctx,lerp(p.x,tx,ease),lerp(p.y,ty,ease),'#5ab0ff',p.l);});
 sh.db.forEach(p=>{const dv=sh.drop[p[2]]||[0,3];dot(ctx,lerp(p[0],p[0]+dv[0],ease),lerp(p[1],p[1]+dv[1],ease),'#5ab0ff',p[2]);});
 ctx.fillStyle='rgba(255,255,255,.9)';ctx.font='12px system-ui';ctx.fillText(`${sh.label}${sim?' · sim pressure: an end drops, a linebacker replaces him in the rush':''}`,12,H-12);}
let defReplay=animate(document.getElementById('cDef'),drawDef);document.getElementById('bDef').onclick=()=>defReplay();document.getElementById('bSim').onclick=()=>{sim=!sim;defReplay();};
document.getElementById('defWhy').innerHTML=`Front: <span class="tag data">depth chart</span> ${CFG.front_why}. Coverage: <span class="tag card">CARD</span> ${CFG.coverage_why}. What the numbers add (<span class="tag data">DATA</span>): sack rate ${CFG.sack_pct}%, stuff rate ${CFG.stuff_pct}%, explosive passes allowed ${CFG.p20_allowed}% of dropbacks, deep-tag share of throws faced ${CFG.deep_faced}%. None of that identifies a coverage.`;
document.getElementById('nums').innerHTML=CFG.numbers_html;
document.getElementById('watch').innerHTML=CFG.watch.map(w=>`<li><b>${w.side}</b> · ${w.game}, ${w.clock} — ${w.yards} yds, PPA ${w.ppa>0?'+':''}${w.ppa} — ${w.text}</li>`).join('');
</script></body></html>
"""


def numbers_html(D, C):
    o, d = D["offense"], D["defense"]
    rows = [("Shotgun rate (tagged snaps)", f"{fmt(o['formation']['shotgun_pct'], '%')}", "decides the base look"),
            ("No-huddle rate / median s between snaps", f"{fmt(o['formation']['no_huddle_pct'], '%')} / {fmt(o['tempo']['median'])}", "tempo word"),
            ("TE share of targets / RB share", f"{C['te_share']}% / {C['rb_share']}%", "personnel grouping"),
            ("Deep-tag share of throws", f"{fmt(C['deep_pct'], '%')}", "pass concept"),
            ("Runs tagged middle", f"{C['run_mid_pct']}%", "run concept"),
            ("Per attempt / explosive pass rate", f"{fmt(o['summary']['ypa'])} / {fmt(o['summary']['p20_pct'], '%')}", ""),
            ("Rush (box) / stuff rate", f"{o['summary']['box_att']}-{o['summary']['box_yds']} ({fmt(o['summary']['box_ypc'])}) / {fmt(o['summary']['stuff_pct'], '%')}", ""),
            ("Defense: sack / stuff / explosive-pass allowed", f"{fmt(d['summary']['sack_pct'], '%')} / {fmt(d['summary']['stuff_pct'], '%')} / {fmt(d['summary']['p20_pct'], '%')}", "front feel only"),
            ("Defense: deep-tag share faced", f"{fmt(d['targets']['deep_pct'], '%')}", "inference only")]
    return "<table><tr><th>Number</th><th class=num>Value</th><th>Drives</th></tr>" + "".join(
        f"<tr><td>{html.escape(a)}</td><td class=num>{html.escape(b)}</td><td>{html.escape(c)}</td></tr>" for a, b, c in rows) + "</table>"


def build(path):
    D = json.load(open(path, encoding="utf-8"))
    C = choose(D)
    C["numbers_html"] = numbers_html(D, C)
    C["watch"] = [dict(side=w["side"], game=w["game"], clock=w["clock"], yards=w["yards"], ppa=w["ppa"], text=html.escape(w["text"])) for w in D["watch"]]
    slug = re.sub(r"[^A-Za-z0-9]+", "_", D["team"]).strip("_")
    page = (TEMPLATE.replace("__TEAM__", html.escape(D["team"])).replace("__WK__", str(D["through_week"] - 1))
            .replace("__SLUG__", slug).replace("__W__", str(D["through_week"])).replace("__CONFIG__", json.dumps(C)).replace("__JSCORE__", JS_CORE))
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, f"{slug}.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    return D["team"], out, C


def index(rows, week):
    items = "".join(f'<li><a href="{html.escape(os.path.basename(p))}">{html.escape(t)}</a> — {html.escape(c["base"])}, {c["personnel"]} personnel; '
                    f'{html.escape(" / ".join(x["name"] for x in c["concepts"]))}; {html.escape(c["front"])} · {html.escape(c["coverage"])}</li>' for t, p, c in rows)
    page = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Dossier pages — Week {week}</title>
<style>body{{font:15px system-ui;background:#0f1418;color:#e8edf1;padding:24px}}a{{color:#8fc7ff}}li{{margin:6px 0}}</style></head>
<body><h1>Scheme pages through Week {week - 1}</h1><p>INTERNAL. One page per covered team; drawings decided by the dossier numbers, coverages by the card.</p><ul>{items}</ul></body></html>"""
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(page)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--team")
    a = ap.parse_args()
    files = sorted(glob.glob(os.path.join(IN, f"*_week{a.week}.json")))
    if a.team:
        slug = re.sub(r"[^A-Za-z0-9]+", "_", a.team).strip("_")
        files = [f for f in files if os.path.basename(f).startswith(slug + "_")]
    rows = []
    for f in files:
        t, out, C = build(f)
        rows.append((t, out, C))
        print(f"{t:12s} -> {os.path.relpath(out, HERE)} | {C['base']}, {C['personnel']} pers; {' / '.join(x['name'] for x in C['concepts'])}; {C['front']} · {C['coverage']}")
    index(rows, a.week)
