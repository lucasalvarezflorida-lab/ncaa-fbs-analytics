"""efficiency_blend_check.py - re-measure the efficiency blend WHERE IT MATTERS.

Lucas (10/8): "re-measure the efficiency blend on the A&M-type card games."
The 9/22 study (EFFICIENCY_2026.md) graded the blend on every game against
the OLD machine (the 9/20 rule). Two things changed since: the on-air machine
now de-lucks turnovers itself (9/27), which is part of what the efficiency
number was adding; and the blend only matters where the two ratings
disagree, so grading it on all 2,700 games (most of them agreeing within a
point or two) buries the signal. This script walks 2022-2026 forward with
both, keeps the per-game rows, and scores machine / efficiency / blends on:

  * ALL rated games (the 9/22 table, redone against the current machine);
  * DISAGREE: |machine margin - efficiency margin| >= 3 / 5 / 7 (A&M-type:
    the scoreboard and the plays tell different stories about a team);
  * CARD-LIKE: both teams in the machine's top 40 that week and the closing
    spread inside 14 (the games that make the podcast card);
  * CARD-LIKE and DISAGREE >= 3 together.

Plus the direct answer: regress (actual - machine) on (efficiency - machine)
on the fit seasons, so the best blend weight is a fitted number, not a grid
guess; apply it to 2025 and 2026.

    python efficiency_blend_check.py                  # writes internal/efficiency_blend_rows.json + prints the tables

Nothing on air. Result file: internal/EFFICIENCY_BLEND_2026.md.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
import backtest as bt  # noqa: E402
from efficiency_ratings import EfficiencyModel  # noqa: E402

SEASONS = (2022, 2023, 2024, 2025, 2026)
FIT, TEST = (2022, 2023, 2024), (2025,)
WEEKS = range(2, 16)
TOP = 40
BLENDS = (0.25, 0.5, 0.75)


def build_rows() -> list[dict]:
    eff = EfficiencyModel()
    cur = bt.MODELS["current"]
    rows = []
    for s in SEASONS:
        ctx = bt.SeasonCtx(s)
        for w in WEEKS:
            pc = bt.ridge_predict(ctx, w, cur)
            if not pc:
                continue
            pe = eff(ctx, w)
            mode = "residual" if w >= cur["switch"] else "margin"
            r = ctx.ridge(w, cur["lam"], cur["hfa"], cur["cap"], mode, cur.get("obs"))
            rank = {t: i + 1 for i, t in enumerate(sorted(range(len(ctx.teams)), key=lambda i: -r[i]))}
            rank = {ctx.teams[i]: k for i, k in rank.items()}
            for g in ctx.games:
                if g["week"] != w or g["id"] not in pc or g["id"] not in pe:
                    continue
                ln = ctx.lines.get(g["id"], {})
                mkt = -ln["spread"] if ln.get("spread") is not None else None
                rows.append(dict(season=s, wk=w, home=g["home"], away=g["away"], margin=g["margin"],
                                 cur=pc[g["id"]][0], eff=pe[g["id"]][0], mkt=mkt,
                                 rank_h=rank[g["home"]], rank_a=rank[g["away"]],
                                 curve=w))
        # win probabilities for Brier: the production curve at the week's sd
        for row in rows:
            if row["season"] == s and "p_cur" not in row:
                c = ctx.curve(row["wk"])
                row["p_cur"] = float(c.win_prob(np.array([row["cur"]]))[0])
                row["p_eff"] = float(c.win_prob(np.array([row["eff"]]))[0])
                for b in BLENDS:
                    row[f"p_b{b:g}"] = float(c.win_prob(np.array([(1 - b) * row["cur"] + b * row["eff"]]))[0])
    for row in rows:
        for b in BLENDS:
            row[f"b{b:g}"] = (1 - b) * row["cur"] + b * row["eff"]
        row["gap"] = row["eff"] - row["cur"]
    return rows


def sc(rows: list[dict], key: str, pkey: str) -> dict:
    if not rows:
        return dict(n=0)
    e = np.array([r["margin"] - r[key] for r in rows])
    win = np.array([1.0 if r["margin"] > 0 else 0.0 for r in rows])
    p = np.clip(np.array([r[pkey] for r in rows]), 1e-6, 1 - 1e-6)
    L = [r for r in rows if r["mkt"] is not None]
    out = dict(n=len(rows), mae=float(np.mean(np.abs(e))), brier=float(np.mean((p - win) ** 2)),
               su=float(np.mean(np.sign([r[key] for r in rows]) == np.sign([r["margin"] for r in rows]))))
    if L:
        d = np.array([r[key] - r["mkt"] for r in L]); ek = np.array([r["margin"] - r["mkt"] for r in L])
        live = np.abs(d) >= 0.5; res = ek[live] * np.sign(d[live])
        w, l = int(np.sum(res > 0)), int(np.sum(res < 0))
        out.update(mae_mkt=float(np.mean(np.abs(ek))), ats=w / max(w + l, 1), ats_n=w + l)
    return out


CUTS = {
    "all": lambda r: True,
    "disagree >=3": lambda r: abs(r["gap"]) >= 3,
    "disagree >=5": lambda r: abs(r["gap"]) >= 5,
    "disagree >=7": lambda r: abs(r["gap"]) >= 7,
    "card-like": lambda r: r["rank_h"] <= TOP and r["rank_a"] <= TOP and r["mkt"] is not None and abs(r["mkt"]) <= 14,
    "card-like & disagree >=3": lambda r: r["rank_h"] <= TOP and r["rank_a"] <= TOP and r["mkt"] is not None and abs(r["mkt"]) <= 14 and abs(r["gap"]) >= 3,
}
PREDS = [("machine", "cur", "p_cur")] + [(f"blend {b:g}", f"b{b:g}", f"p_b{b:g}") for b in BLENDS] + [("efficiency", "eff", "p_eff")]


def fitted_weight(rows: list[dict]) -> tuple[float, float]:
    """OLS of (actual - machine) on (eff - machine), no intercept: the blend weight the data want, with its se."""
    x = np.array([r["gap"] for r in rows]); y = np.array([r["margin"] - r["cur"] for r in rows])
    if len(x) < 10 or not np.any(x):
        return float("nan"), float("nan")
    w = float(x @ y / (x @ x))
    resid = y - w * x
    se = float(np.sqrt(resid @ resid / (len(x) - 1) / (x @ x)))
    return w, se


def report(rows: list[dict]) -> str:
    L = []
    groups = {"fit 2022-24": [r for r in rows if r["season"] in FIT], "test 2025": [r for r in rows if r["season"] in TEST],
              "2026 wk2-5": [r for r in rows if r["season"] == 2026]}
    for cut, f in CUTS.items():
        L.append(f"\n### {cut}")
        L.append("| predictor | " + " | ".join(f"{g} n / MAE / Brier / ATS" for g in groups) + " |")
        L.append("|---|" + "---|" * len(groups))
        for name, key, pkey in PREDS:
            cells = []
            for g, R in groups.items():
                S = sc([r for r in R if f(r)], key, pkey)
                cells.append(f"{S['n']} / {S['mae']:.2f} / {S['brier']:.4f} / {100 * S.get('ats', 0):.1f}%" if S["n"] else "-")
            L.append(f"| {name} | " + " | ".join(cells) + " |")
        ws = []
        for g, R in groups.items():
            w, se = fitted_weight([r for r in R if f(r)])
            ws.append(f"{g}: {w:+.2f} (se {se:.2f})")
        L.append("fitted blend weight (0 = machine is right, 1 = efficiency is right): " + "; ".join(ws))
        # which side does the truth fall on when they disagree?
        for g, R in groups.items():
            D = [r for r in R if f(r) and abs(r["gap"]) >= 3]
            if D:
                toward = np.mean([np.sign(r["gap"]) * (r["margin"] - r["cur"]) for r in D])
                L.append(f"  {g}: on {len(D)} disagreements >=3, the final landed {toward:+.2f} pts from the machine TOWARD the efficiency number (gap avg {np.mean([abs(r['gap']) for r in D]):.1f})")
    return "\n".join(L)


def cards(week: int | None = None) -> str:
    """The podcast card games (score_tracker.json) graded machine / blend 0.5 / efficiency / market as they
    resolve, plus the coming week's card under each view. Appends to internal/efficiency_blend_cards.md.
    The pre-registered weekly check (EFFICIENCY_BLEND_2026.md): nothing on air until Lucas says."""
    import datetime as dt
    from name_mapping import normalize_name
    import efficiency_ratings as er
    tr = json.loads((HERE / "score_tracker.json").read_text(encoding="utf-8"))
    ctx = bt.SeasonCtx(2026)
    eff = EfficiencyModel(); cur = bt.MODELS["current"]
    L = [f"## efficiency blend on the cards - {dt.date.today()}"]
    tot = dict(m=0.0, b=0.0, e=0.0, k=0.0, n=0, wm=0, wb=0, we=0)
    for w in sorted({g["week"] for g in tr}):
        pc, pe = bt.ridge_predict(ctx, w, cur), eff(ctx, w)
        by = {(g["home"], g["away"]): g for g in ctx.games if g["week"] == w}
        for g in [g for g in tr if g["week"] == w]:
            h, a = normalize_name(g["home"]), normalize_name(g["away"])
            gg = by.get((h, a))
            if gg is None or gg["id"] not in pc or gg["id"] not in pe:
                continue
            m, e = pc[gg["id"]][0], pe[gg["id"]][0]; b = 0.5 * (m + e)
            ln = ctx.lines.get(gg["id"], {}); k = -ln["spread"] if ln.get("spread") is not None else None
            if g.get("final"):
                act = float(g["final"][1] - g["final"][0])
                tot["m"] += abs(act - m); tot["b"] += abs(act - b); tot["e"] += abs(act - e); tot["n"] += 1
                tot["k"] += abs(act - k) if k is not None else 0
                tot["wm"] += int(np.sign(act) == np.sign(m)); tot["wb"] += int(np.sign(act) == np.sign(b)); tot["we"] += int(np.sign(act) == np.sign(e))
                L.append(f"wk{w} {g['game']}: final {act:+.0f} | machine {m:+.1f} blend {b:+.1f} eff {e:+.1f} mkt {k}")
            else:
                L.append(f"wk{w} {g['game']}: PENDING | machine {m:+.1f} blend {b:+.1f} eff {e:+.1f} mkt {k}")
    # the coming card is not in the completed-games cache: frozen (or published) card + the shadow ratings before that week
    for w in sorted({g["week"] for g in tr if not g.get("final")}):
        cf = next((f for f in (HERE / f"card_data_week{w}_frozen.json", HERE / f"card_data_week{w}.json") if f.exists()), None)
        sf = HERE / "internal" / f"shadow_ratings_week{w}.json"
        if cf is None or not sf.exists():
            L.append(f"wk{w}: no card / shadow file yet"); continue
        c = json.loads(cf.read_text(encoding="utf-8")); games = c.get("games", c) if isinstance(c, dict) else c
        sh = json.loads(sf.read_text(encoding="utf-8"))
        R = {t["team"]: dict(off=t["off"], def_=t["def_"], st=t["st"]) for t in sh["teams"]}
        want = {(normalize_name(g["home"]), normalize_name(g["away"])): g["game"] for g in tr if g["week"] == w and not g.get("final")}
        for cg in games:
            key = (normalize_name(cg["home"]), normalize_name(cg["away"]))
            if key not in want or key[0] not in R or key[1] not in R:
                continue
            m = float(cg["model_margin"]); e = er.predict_margin(R, key[0], key[1], bool(cg.get("neutral")))
            L.append(f"wk{w} {want[key]}: PENDING ({cf.name}) | machine {m:+.1f} blend {0.5 * (m + e):+.1f} eff {e:+.1f} mkt {cg.get('mkt_spread')}")
    if tot["n"]:
        L.append(f"{tot['n']} graded: total miss machine {tot['m']:.1f} / blend 0.5 {tot['b']:.1f} / efficiency {tot['e']:.1f} / market {tot['k']:.1f}; "
                 f"per game machine {tot['m']/tot['n']:.2f} blend {tot['b']/tot['n']:.2f} eff {tot['e']/tot['n']:.2f}; winners {tot['wm']} / {tot['wb']} / {tot['we']}")
    out = "\n".join(L)
    with (HERE / "internal" / "efficiency_blend_cards.md").open("a", encoding="utf-8") as f:
        f.write(out + "\n\n")
    return out


if __name__ == "__main__":
    if "--cards" in sys.argv:
        print(cards()); sys.exit(0)
    rows = build_rows()
    (HERE / "internal").mkdir(exist_ok=True)
    (HERE / "internal" / "efficiency_blend_rows.json").write_text(json.dumps(rows, default=float), encoding="utf-8")
    print(f"{len(rows)} rows, {sum(1 for r in rows if abs(r['gap']) >= 3)} with |gap| >= 3, {sum(1 for r in rows if abs(r['gap']) >= 5)} >= 5")
    print(report(rows))
