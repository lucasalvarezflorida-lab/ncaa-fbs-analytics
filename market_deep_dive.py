"""INTERNAL season deep dive: the machine vs the closing market, every rated
FBS-vs-FBS game to date. Walk-forward: each week is predicted from a re-solve
on the games BEFORE it (today's cap rule), so no game grades itself.

  python market_deep_dive.py            -> prints the tables, writes internal/market_deep_dive_data.json

Close = CFBD's final line (DraftKings -> Bovada); open = first-seen in our
line ledger. Never slide material: the market is internal (Lucas 9/21)."""
import collections, contextlib, io, json, os, statistics as st, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "fpi-decomposition"))
from refresh_all import load_env_key, load_fpi_2026  # noqa: E402
import build_conference_book as b  # noqa: E402
import inseason_ratings as ir  # noqa: E402
import line_ledger  # noqa: E402
from name_mapping import normalize_name as norm  # noqa: E402

load_env_key()
with contextlib.redirect_stdout(io.StringIO()):
    games = b.fetch_games(False, {})
f26 = load_fpi_2026()
prior = {t: (v["fpi"] if isinstance(v, dict) else v) for t, v in f26.items()}
cg = [g for g in ir.completed_games_2026(False) if g["home"] in prior and g["away"] in prior]
by_id = {g["id"]: g for g in games}
weeks = sorted({g["week"] for g in cg})
rated = {}
for w in weeks:
    r = ir.ridge_update(prior, [g for g in cg if g["week"] < w], cap_mode="residual")
    for g in cg:
        if g["week"] == w:
            rated[g["id"]] = r[g["home"]] - r[g["away"]] + (0 if g["neutral"] else 2.5)

rows = []
for g in cg:
    fg = by_id.get(g["id"])
    if not fg or fg["spread"] is None:
        continue
    series = line_ledger.series(g["id"]) if hasattr(line_ledger, "series") else []
    first = series[0]["spread"] if series else None
    close = float(fg["spread"])
    rows.append(dict(id=g["id"], wk=g["week"], home=fg["home"], away=fg["away"], neutral=g["neutral"],
                     margin=g["margin"], model=rated[g["id"]], mkt=-close, first=(-float(first) if first is not None else None),
                     pre=prior[g["home"]] - prior[g["away"]] + (0 if g["neutral"] else 2.5),
                     ou=fg["ou"], total=fg["home_pts"] + fg["away_pts"], ou_tail=fg.get("ou_tail"),
                     conf=(fg["home_conf"], fg["away_conf"])))
N = len(rows)
mae = lambda xs: st.mean(abs(x) for x in xs) if xs else float("nan")
out = dict(n=N)
print(f"{N} rated FBS-vs-FBS games with a closing line, weeks {weeks[0]}-{weeks[-1]}\n")

print("== 1. Accuracy (average miss on the margin, points) ==")
print(f"{'':10s} {'n':>4} {'preseason':>10} {'machine':>8} {'market':>7} {'mach closer':>12}")
tab = []
for w in weeks + ["ALL", "wk2+"]:
    R = [r for r in rows if (w == "ALL" or (w == "wk2+" and r["wk"] >= 2) or r["wk"] == w)]
    mc = sum(abs(r["margin"] - r["model"]) < abs(r["margin"] - r["mkt"]) for r in R)
    kc = sum(abs(r["margin"] - r["model"]) > abs(r["margin"] - r["mkt"]) for r in R)
    line = dict(week=w, n=len(R), pre=mae([r["margin"] - r["pre"] for r in R]), machine=mae([r["margin"] - r["model"] for r in R]),
                market=mae([r["margin"] - r["mkt"] for r in R]), machine_closer=mc, market_closer=kc)
    tab.append(line)
    print(f"{str(w):10s} {line['n']:>4} {line['pre']:>10.2f} {line['machine']:>8.2f} {line['market']:>7.2f} {mc:>5}-{kc:<5}")
out["accuracy"] = tab

print("\n== 2. Where the machine loses to the market: by size of the closing spread ==")
bk = []
for lo, hi in ((0, 3), (3.5, 7), (7.5, 14), (14.5, 21), (21.5, 28), (28.5, 99)):
    R = [r for r in rows if lo <= abs(r["mkt"]) <= hi]
    if not R: continue
    d = dict(bucket=f"{lo}-{hi}", n=len(R), machine=mae([r["margin"] - r["model"] for r in R]), market=mae([r["margin"] - r["mkt"] for r in R]),
             model_shorter=st.mean(abs(r["mkt"]) - abs(r["model"]) for r in R))
    bk.append(d)
    print(f"  spread {d['bucket']:>8s}: n={d['n']:3d} machine {d['machine']:5.2f} market {d['market']:5.2f} gap {d['machine'] - d['market']:+5.2f} | machine's number is {d['model_shorter']:+.1f} pts SHORTER than the market's on the favorite")
out["by_spread"] = bk

print("\n== 3. Bias (signed error; + = the home team / favorite did better than the number) ==")
nn = [r for r in rows if not r["neutral"]]
sgn = lambda x: 1 if x > 0 else -1
print(f"  home teams vs machine {st.mean(r['margin'] - r['model'] for r in nn):+.2f} | vs market {st.mean(r['margin'] - r['mkt'] for r in nn):+.2f}")
print(f"  market favorites vs machine {st.mean((r['margin'] - r['model']) * sgn(r['mkt']) for r in rows if r['mkt']):+.2f} | vs market {st.mean((r['margin'] - r['mkt']) * sgn(r['mkt']) for r in rows if r['mkt']):+.2f}")
out["bias"] = dict(home_vs_machine=st.mean(r["margin"] - r["model"] for r in nn), home_vs_market=st.mean(r["margin"] - r["mkt"] for r in nn),
                   fav_vs_machine=st.mean((r["margin"] - r["model"]) * sgn(r["mkt"]) for r in rows if r["mkt"]),
                   fav_vs_market=st.mean((r["margin"] - r["mkt"]) * sgn(r["mkt"]) for r in rows if r["mkt"]))

print("\n== 4. When we disagree with the close, who is right? (machine's side against the closing spread) ==")
eg = []
for lo, hi in ((0, 1.5), (1.5, 3), (3, 6), (6, 10), (10, 99)):
    R = [r for r in rows if lo <= abs(r["model"] - r["mkt"]) < hi]
    w = sum(((r["margin"] - r["mkt"]) * sgn(r["model"] - r["mkt"])) > 0 for r in R)
    l = sum(((r["margin"] - r["mkt"]) * sgn(r["model"] - r["mkt"])) < 0 for r in R)
    d = dict(edge=f"{lo}-{hi}", n=len(R), w=w, l=l, pct=(100 * w / (w + l) if w + l else None),
             side_dog=sum((r["model"] - r["mkt"]) * sgn(r["mkt"]) < 0 for r in R))
    eg.append(d)
    print(f"  disagreement {d['edge']:>7s} pts: n={d['n']:3d} machine side {w}-{l} ({d['pct'] or 0:.0f}%) | on the underdog in {d['side_dog']} of {d['n']}")
allw = sum(d["w"] for d in eg); alll = sum(d["l"] for d in eg)
print(f"  ALL: {allw}-{alll} ({100 * allw / (allw + alll):.1f}%) - break-even at -110 is 52.4%")
out["edge"] = eg

print("\n== 5. Line movement: does the market move toward the machine? (first-seen -> close) ==")
mv = [r for r in rows if r["first"] is not None and abs(r["mkt"] - r["first"]) >= 1]
toward = sum(abs(r["model"] - r["mkt"]) < abs(r["model"] - r["first"]) for r in mv)
print(f"  lines that moved 1+ point: {len(mv)} | moved TOWARD the machine's number: {toward} ({100 * toward / max(len(mv), 1):.0f}%)")
op = [r for r in rows if r["first"] is not None]
print(f"  first-seen line miss {mae([r['margin'] - r['first'] for r in op]):.2f} vs close {mae([r['margin'] - r['mkt'] for r in op]):.2f} vs machine {mae([r['margin'] - r['model'] for r in op]):.2f} (n={len(op)})")
wf = sum(((r["margin"] - r["first"]) * sgn(r["model"] - r["first"])) > 0 for r in op if abs(r["model"] - r["first"]) >= 3)
lf = sum(((r["margin"] - r["first"]) * sgn(r["model"] - r["first"])) < 0 for r in op if abs(r["model"] - r["first"]) >= 3)
print(f"  machine side vs the FIRST-SEEN line when 3+ apart: {wf}-{lf}")
out["movement"] = dict(moved=len(mv), toward=toward, first_mae=mae([r["margin"] - r["first"] for r in op]), vs_first_3plus=(wf, lf))

print("\n== 6. Totals ==")
T = [r for r in rows if r["ou"] is not None]
o = sum(r["total"] > float(r["ou"]) for r in T); u = sum(r["total"] < float(r["ou"]) for r in T)
print(f"  overs {o}-{u} | scored {st.mean(r['total'] for r in T):.1f} vs posted {st.mean(float(r['ou']) for r in T):.1f} | total miss {mae([r['total'] - float(r['ou']) for r in T]):.1f}")
mu = [r for r in T if r["ou_tail"]]
print(f"  Monster Under games (current top-decile flag): unders {sum(r['total'] < float(r['ou']) for r in mu)}-{sum(r['total'] > float(r['ou']) for r in mu)}")
for w in weeks:
    W = [r for r in T if r["wk"] == w]
    print(f"    wk{w}: overs {sum(r['total'] > float(r['ou']) for r in W)}-{sum(r['total'] < float(r['ou']) for r in W)}")
out["totals"] = dict(over=o, under=u)

print("\n== 7. Biggest machine-vs-market disagreements so far ==")
for r in sorted(rows, key=lambda r: -abs(r["model"] - r["mkt"]))[:10]:
    side = r["home"] if r["model"] > r["mkt"] else r["away"]
    won = (r["margin"] - r["mkt"]) * sgn(r["model"] - r["mkt"]) > 0
    print(f"  wk{r['wk']} {r['away']} at {r['home']}: machine {r['model']:+.1f} vs close {r['mkt']:+.1f} (home margin) -> actual {r['margin']:+.0f} | machine side {side} {'COVERED' if won else 'lost'}")

os.makedirs("internal", exist_ok=True)
json.dump(dict(out, rows=rows), open(os.path.join("internal", "market_deep_dive_data.json"), "w", encoding="utf-8"), indent=1, default=float)
