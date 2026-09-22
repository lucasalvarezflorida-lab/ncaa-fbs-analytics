"""backtest.py - THE SCOREBOARD for every rating the machine runs or shadows.

Walk-forward over whole seasons using the CFBD caches already on disk: before
each week's games the rating is re-solved from ONLY the earlier weeks of that
season, exactly the way the in-season machine does it on the show, and every
game is then scored against what actually happened.

    python backtest.py --seasons 2022-2025 --model current        # the on-air machine
    python backtest.py --seasons 2022-2026 --model current,frozen  # several models side by side
    python backtest.py --seasons 2022-2025 --tune                  # grid search, fit 2022-24 / test 2025
    python backtest.py --seasons 2026 --model current --rows out.json   # per-game rows (deep dive)

WHAT "EXACTLY" MEANS
  * prior: for 2026 the July ESPN preseason FPI snapshot (what the machine
    really used); for 2022-2025 the prior-year FINAL FPI, the only preseason
    prior CFBD's history allows. That prior is staler than a real preseason
    number, so the historical error is a ceiling on what the live machine
    would have shown, not the live number itself.
  * games: completed regular-season games between two rated (prior) teams.
    FCS games never enter, as in production. CFBD's week numbering (Week 0
    games sit in week 1) is used as is.
  * rule: ridge update, lam 3, HFA 2.5, cap 28, cap on the MARGIN before the
    switch week and on the RESIDUAL from it (the 2026-09-20 rule change =
    week 4 of 2026). Week 1 is the prior alone for every configuration.
  * win probability: the production margin curve (margin_prob_curve.json,
    'model'), rescaled to sd 15.9 once a rated game has been played, 17.94
    before - sigma_for() in inseason_ratings.
  * closing line: CFBD /lines cache, one book per game by the production
    preference (DraftKings > Bovada > ESPN Bet > ...). Market win probability
    = the 'market' curve on the closing spread (moneylines are not posted for
    every game / book / year, so the curve keeps the comparison uniform).

BASELINES on every table: the preseason prior held constant ("frozen"), the
closing line, and a coin flip (margin 0, p 0.5).

MODELS are plug-ins (MODELS dict): a name -> config for the ridge family, or
a callable(ctx, week) -> {game_id: (home margin, p_home)} for anything else
(efficiency rating, availability layer, ...). Shadow ratings register here
and are graded on the same tables as the on-air number.

The market is INTERNAL (Lucas 9/21): this script prints market numbers; its
outputs go to internal/, never to a slide or the public notes.
"""
from __future__ import annotations

import argparse
import datetime as dt
import itertools
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402
import inseason_ratings as ir  # noqa: E402
from margin_prob import load_curve  # noqa: E402

DATA = HERE / "fpi-decomposition" / "data"
BOOK_PREF = ["DraftKings", "Draft Kings", "Bovada", "ESPN Bet", "William Hill (New Jersey)",
             "consensus", "teamrankings", "Caesars Sportsbook (Colorado)", "numberfire"]
WEEKS = range(1, 16)

# ---- model registry -------------------------------------------------------
# ridge family: lam, hfa, cap, switch (first week that uses the residual cap;
# 1 = residual always, 99 = margin cap always)
CURRENT = dict(lam=ir.LAM, hfa=ir.HFA, cap=ir.CAP, switch=4)   # the on-air machine
MODELS = {
    "current": dict(CURRENT, desc="on-air: lam 3, HFA 2.5, cap 28, margin cap wks 1-3 then residual"),
    "frozen": dict(lam=float("inf"), hfa=ir.HFA, cap=None, switch=99, desc="preseason FPI held constant"),
    "residual": dict(CURRENT, switch=1, desc="residual cap from week 1"),
    "margin": dict(CURRENT, switch=99, desc="margin cap all season"),
    "nocap": dict(CURRENT, cap=None, desc="no cap"),
}


def _register_shadow_models():
    """Shadow ratings (Phase 1+) register here so they are graded on the same tables."""
    try:
        from efficiency_ratings import EfficiencyModel
    except Exception as e:  # play caches missing etc. - the ridge family still runs
        print("efficiency model not registered:", e)
        return
    MODELS["efficiency"] = EfficiencyModel(desc="SHADOW play-level efficiency ridge (lam 3, st 8, HFA 2.5)")
    MODELS["eff_blend"] = EfficiencyModel(blend=0.5, desc="SHADOW 50/50 blend of efficiency and the on-air machine")
    try:
        from availability import AvailabilityModel
        MODELS["availability"] = AvailabilityModel(desc="SHADOW: on-air machine minus the QB-out penalty on the flagged side")
    except Exception as e:
        print("availability model not registered:", e)


_register_shadow_models()


def desc(model):
    return model.get("desc", "") if isinstance(model, dict) else getattr(model, "desc", "")

# ---- data -----------------------------------------------------------------


def _pick(g, *names):
    for k in names:
        if g.get(k) is not None:
            return g[k]
    return None


def load_prior(season: int) -> dict[str, float]:
    if season >= 2026:
        from refresh_all import load_fpi_2026
        p = load_fpi_2026()
        if p:
            return p
    path = DATA / f"ratings_fpi_year-{season - 1}.json"
    return {normalize_name(r["team"]): float(r["fpi"])
            for r in json.loads(path.read_text(encoding="utf-8")) if r.get("fpi") is not None}


def load_games(season: int, prior: dict) -> list[dict]:
    path = DATA / f"games_seasonType-regular_year-{season}.json"
    out = []
    for g in json.loads(path.read_text(encoding="utf-8")):
        if not _pick(g, "completed"):
            continue
        hp, ap = _pick(g, "homePoints", "home_points"), _pick(g, "awayPoints", "away_points")
        home, away = _pick(g, "homeTeam", "home_team"), _pick(g, "awayTeam", "away_team")
        if hp is None or ap is None or not home or not away:
            continue
        h, a = normalize_name(home), normalize_name(away)
        if h not in prior or a not in prior:
            continue
        out.append(dict(id=_pick(g, "id"), week=int(_pick(g, "week") or 0), home=h, away=a,
                        home_raw=home, away_raw=away,
                        neutral=bool(_pick(g, "neutralSite", "neutral_site")),
                        margin=float(hp - ap), total=float(hp + ap), date=_pick(g, "startDate", "start_date"),
                        home_conf=_pick(g, "homeConference", "home_conference"),
                        away_conf=_pick(g, "awayConference", "away_conference")))
    return sorted(out, key=lambda g: (g["week"], g["date"] or ""))


def load_lines(season: int) -> dict[int, dict]:
    """{game_id: {spread (home, negative = home favored), ou, book, spread_open}}."""
    path = DATA / f"lines_seasonType-regular_year-{season}.json"
    if not path.exists():
        return {}
    out = {}
    for g in json.loads(path.read_text(encoding="utf-8")):
        books = {ln.get("provider"): ln for ln in g.get("lines", []) if ln.get("spread") is not None}
        if not books:
            continue
        book = next((b for b in BOOK_PREF if b in books), next(iter(books)))
        ln = books[book]
        ou = ln.get("overUnder")
        if ou is None:
            ou = next((b.get("overUnder") for b in books.values() if b.get("overUnder") is not None), None)
        out[g["id"]] = dict(spread=float(ln["spread"]), ou=(float(ou) if ou is not None else None),
                            book=book, spread_open=ln.get("spreadOpen"))
    return out


class SeasonCtx:
    """Everything one season's walk-forward needs, with the design matrix and
    its Gram matrix cached per week so a tuning grid is cheap."""

    def __init__(self, season: int):
        self.season = season
        self.prior = load_prior(season)
        self.games = load_games(season, self.prior)
        self.lines = load_lines(season)
        self.teams = sorted(self.prior)
        self.idx = {t: i for i, t in enumerate(self.teams)}
        self.p = np.array([self.prior[t] for t in self.teams])
        n, m = len(self.games), len(self.teams)
        self.X = np.zeros((n, m))
        self.X[np.arange(n), [self.idx[g["home"]] for g in self.games]] = 1.0
        self.X[np.arange(n), [self.idx[g["away"]] for g in self.games]] = -1.0
        self.y = np.array([g["margin"] for g in self.games])
        self.home = np.array([0.0 if g["neutral"] else 1.0 for g in self.games])
        self.week = np.array([g["week"] for g in self.games])
        self._gram = {}
        self.curve_in = load_curve("model", sd=ir.SIGMA_INSEASON)
        self.curve_frozen = load_curve("model", sd=ir.SIGMA_FROZEN)
        self.curve_mkt = load_curve("market")

    def before(self, week: int) -> np.ndarray:
        return np.flatnonzero(self.week < week)

    def gram(self, week: int) -> np.ndarray:
        if week not in self._gram:
            rows = self.before(week)
            Xw = self.X[rows]
            self._gram[week] = Xw.T @ Xw
        return self._gram[week]

    def ridge(self, week: int, lam: float, hfa: float, cap: float | None, mode: str) -> np.ndarray:
        """Ratings vector before `week` (weeks < week only)."""
        rows = self.before(week)
        if not len(rows) or not np.isfinite(lam):
            return self.p.copy()
        Xw, y, h = self.X[rows], self.y[rows], self.home[rows] * hfa
        if cap is not None and mode == "margin":
            y = np.clip(y, -cap, cap)
        resid = y - (Xw @ self.p + h)
        if cap is not None and mode == "residual":
            resid = np.clip(resid, -cap, cap)
        d = np.linalg.solve(self.gram(week) + lam * np.eye(len(self.teams)), Xw.T @ resid)
        return self.p + d

    def curve(self, week: int):
        return self.curve_in if len(self.before(week)) else self.curve_frozen


def ridge_predict(ctx: SeasonCtx, week: int, cfg: dict) -> dict[int, tuple[float, float]]:
    mode = "residual" if week >= cfg["switch"] else "margin"
    r = ctx.ridge(week, cfg["lam"], cfg["hfa"], cfg["cap"], mode)
    rows = np.flatnonzero(ctx.week == week)
    if not len(rows):
        return {}
    m = ctx.X[rows] @ r + ctx.home[rows] * cfg["hfa"]
    p = ctx.curve(week).win_prob(m)
    return {ctx.games[i]["id"]: (float(mm), float(pp)) for i, mm, pp in zip(rows, m, p)}


def predict(ctx: SeasonCtx, week: int, model) -> dict[int, tuple[float, float]]:
    if callable(model):
        return model(ctx, week)
    return ridge_predict(ctx, week, model)


def season_rows(season: int, model, ctx: SeasonCtx | None = None, weeks=WEEKS) -> list[dict]:
    """Per-game rows for one season under one model: id, wk, teams, margin,
    model margin + p_home, closing spread as a home margin (mkt) + market
    p_home, the prior alone (pre), total + closing total."""
    ctx = ctx or SeasonCtx(season)
    out = []
    for w in weeks:
        pr = predict(ctx, w, model)
        if not pr:
            continue
        pre = ridge_predict(ctx, w, MODELS["frozen"])
        for g in ctx.games:
            if g["week"] != w or g["id"] not in pr:
                continue
            ln = ctx.lines.get(g["id"], {})
            mkt = -ln["spread"] if ln.get("spread") is not None else None
            out.append(dict(id=g["id"], season=season, wk=w, home=g["home_raw"], away=g["away_raw"],
                            neutral=g["neutral"], margin=g["margin"], total=g["total"],
                            model=pr[g["id"]][0], p=pr[g["id"]][1],
                            pre=pre[g["id"]][0], p_pre=pre[g["id"]][1],
                            mkt=mkt, p_mkt=(float(ctx.curve_mkt.win_prob(mkt)) if mkt is not None else None),
                            ou=ln.get("ou"), book=ln.get("book"),
                            conf=(g["home_conf"], g["away_conf"])))
    return out


# ---- scoring --------------------------------------------------------------


def _clip(p):
    return min(max(p, 1e-6), 1 - 1e-6)


def score(rows: list[dict], key="model", pkey="p") -> dict:
    """Scoreboard for one predictor over rows. key/pkey: which margin / p column."""
    R = [r for r in rows if r.get(key) is not None]
    if not R:
        return dict(n=0)
    e = np.array([r["margin"] - r[key] for r in R])
    win = np.array([1.0 if r["margin"] > 0 else 0.0 for r in R])   # ties count as home losses
    p = np.array([_clip(r[pkey]) for r in R])
    L = [r for r in R if r.get("mkt") is not None]
    mm = np.array([r[key] for r in R])
    out = dict(n=len(R), mae=float(np.mean(np.abs(e))), rmse=float(np.sqrt(np.mean(e ** 2))),
               bias=float(np.mean(e)),
               su=(float(np.mean(np.sign(mm) == np.sign([r["margin"] for r in R]))) if np.any(mm) else None),
               brier=float(np.mean((p - win) ** 2)),
               logloss=float(-np.mean(win * np.log(p) + (1 - win) * np.log(1 - p))),
               n_mkt=len(L))
    if L and np.any(mm):
        em = np.array([r["margin"] - r[key] for r in L]); ek = np.array([r["margin"] - r["mkt"] for r in L])
        out.update(mae_on_mkt=float(np.mean(np.abs(em))), mae_mkt=float(np.mean(np.abs(ek))),
                   dist_mkt=float(np.mean(np.abs([r[key] - r["mkt"] for r in L]))),
                   closer=int(np.sum(np.abs(em) < np.abs(ek))), farther=int(np.sum(np.abs(em) > np.abs(ek))))
        # ATS vs the close: side the model prefers, when it differs from the close by >= 0.5
        d = np.array([r[key] - r["mkt"] for r in L]); live = np.abs(d) >= 0.5
        res = ek[live] * np.sign(d[live])
        out.update(ats_w=int(np.sum(res > 0)), ats_l=int(np.sum(res < 0)), ats_p=int(np.sum(res == 0)))
        out["ats_pct"] = out["ats_w"] / max(out["ats_w"] + out["ats_l"], 1)
        d15 = np.abs(d) >= 1.5; res15 = ek[d15] * np.sign(d[d15])
        out.update(ats15_w=int(np.sum(res15 > 0)), ats15_l=int(np.sum(res15 < 0)))
    return out


def calibration(rows, pkey="p", edges=(0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1.0001)):
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        R = [r for r in rows if r.get(pkey) is not None and lo <= r[pkey] < hi]
        if R:
            out.append(dict(bucket=f"{lo:.0%}-{min(hi, 1):.0%}", n=len(R), pred=float(np.mean([r[pkey] for r in R])),
                            actual=float(np.mean([1.0 if r["margin"] > 0 else 0.0 for r in R]))))
    return out


def by_spread(rows, key="model"):
    out = []
    for lo, hi in ((0, 3), (3.5, 7), (7.5, 14), (14.5, 21), (21.5, 28), (28.5, 99)):
        R = [r for r in rows if r.get("mkt") is not None and lo <= abs(r["mkt"]) <= hi]
        if R:
            out.append(dict(bucket=f"{lo:g}-{hi:g}", n=len(R),
                            model=float(np.mean([abs(r["margin"] - r[key]) for r in R])),
                            market=float(np.mean([abs(r["margin"] - r["mkt"]) for r in R]))))
    return out


def fav_bias(rows, key="model"):
    """Mean signed error from the FAVORITE'S side (actual - predicted, times the
    sign of the prediction) by size of the predicted margin; negative = the
    model's favorites win by less than it says."""
    out = []
    for lo, hi in ((0, 3), (3, 7), (7, 14), (14, 28), (28, 99)):
        R = [r for r in rows if r.get(key) is not None and lo <= abs(r[key]) < hi]
        if R:
            e = [(r["margin"] - r[key]) * (1 if r[key] > 0 else -1) for r in R]
            out.append(dict(bucket=f"{lo}-{hi}", n=len(R), bias=float(np.mean(e)),
                            fav_won=float(np.mean([(r["margin"] > 0) == (r[key] > 0) for r in R]))))
    return out


def baselines(rows):
    R = [dict(r, model=0.0, p=0.5) for r in rows]
    coin = score(R)
    M = [dict(r, model=r["mkt"], p=r["p_mkt"]) for r in rows if r.get("mkt") is not None]
    mkt = score(M)
    fro = score(rows, key="pre", pkey="p_pre")
    return dict(coin=coin, market=mkt, frozen=fro)


# ---- tuning ---------------------------------------------------------------

GRID = dict(lam=[1, 2, 3, 4, 6, 8, 12], hfa=[1.5, 2.0, 2.5, 3.0, 3.5],
            cap=[14, 21, 28, 35, None], switch=[1, 4, 99])


def tune(ctxs: dict[int, SeasonCtx], fit_seasons, test_seasons, grid=GRID, weeks=range(2, 16)):
    """Grid search on MAE (weeks 2+, fit seasons); every config is also scored
    on the test seasons so the table shows the out-of-sample cost of the
    choice. Returns rows sorted by fit MAE."""
    combos = list(itertools.product(grid["lam"], grid["hfa"], grid["cap"], grid["switch"]))
    res = []
    for lam, hfa, cap, sw in combos:
        cfg = dict(lam=lam, hfa=hfa, cap=cap, switch=sw)
        fit_rows, test_rows = [], []
        for s, ctx in ctxs.items():
            rows = []
            for w in weeks:
                pr = ridge_predict(ctx, w, cfg)
                for g in ctx.games:
                    if g["week"] == w and g["id"] in pr:
                        ln = ctx.lines.get(g["id"], {})
                        rows.append(dict(margin=g["margin"], model=pr[g["id"]][0], p=pr[g["id"]][1],
                                         mkt=(-ln["spread"] if ln.get("spread") is not None else None)))
            (fit_rows if s in fit_seasons else test_rows).extend(rows)
        f, t = score(fit_rows), score(test_rows)
        res.append(dict(lam=lam, hfa=hfa, cap=cap, switch=sw, fit_mae=f["mae"], fit_brier=f["brier"],
                        fit_ats=f.get("ats_pct"), test_mae=t.get("mae"), test_brier=t.get("brier"),
                        test_ats=t.get("ats_pct"), test_mae_mkt=t.get("mae_mkt")))
    return sorted(res, key=lambda r: r["fit_mae"])


def compare(ctxs: dict[int, SeasonCtx], models: dict, fit_seasons, test_seasons, weeks=range(2, 16)):
    """Score named models (any kind) on fit and test seasons, weeks 2+. Rows sorted by fit MAE."""
    res = []
    for name, model in models.items():
        fit_rows, test_rows = [], []
        for s, ctx in ctxs.items():
            rows = season_rows(s, model, ctx, weeks)
            (fit_rows if s in fit_seasons else test_rows).extend(rows)
        f, t = score(fit_rows), score(test_rows)
        res.append(dict(name=name, fit_mae=f.get("mae"), fit_brier=f.get("brier"), fit_mae_mkt=f.get("mae_mkt"),
                        fit_ats=f.get("ats_pct"), test_mae=t.get("mae"), test_brier=t.get("brier"),
                        test_mae_mkt=t.get("mae_mkt"), test_ats=t.get("ats_pct"), fit_n=f.get("n"), test_n=t.get("n")))
    return sorted(res, key=lambda r: r["fit_mae"] if r["fit_mae"] is not None else 99)


# ---- report ---------------------------------------------------------------


def fmt_score(name, s):
    if not s or not s.get("n"):
        return f"{name:14s}   -"
    su = f"{100 * s['su']:5.1f}%" if s.get("su") is not None else "     -"
    a = f"{name:14s} {s['n']:5d} {s['mae']:6.2f} {s['rmse']:6.2f} {s['bias']:+6.2f} {su} {s['brier']:.4f} {s['logloss']:.4f}"
    if s.get("n_mkt") and "closer" in s:
        a += (f" | {s['n_mkt']:4d} {s.get('mae_on_mkt', float('nan')):6.2f} {s.get('mae_mkt', float('nan')):6.2f}"
              f" {s.get('closer', 0):4d}-{s.get('farther', 0):<4d} {s.get('ats_w', 0)}-{s.get('ats_l', 0)}-{s.get('ats_p', 0)} ({100 * s.get('ats_pct', 0):.1f}%)")
    return a


HEAD = (f"{'model':14s} {'n':>5} {'MAE':>6} {'RMSE':>6} {'bias':>6} {'SU%':>6} {'Brier':>6} {'logL':>6}"
        f" | {'n$':>4} {'MAE':>6} {'mkt':>6} {'closer':>9} {'ATS vs close':>14}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seasons", default="2022-2025")
    ap.add_argument("--model", default="current", help="comma list of MODELS keys")
    ap.add_argument("--tune", action="store_true")
    ap.add_argument("--tune-eff", action="store_true", help="grid over the efficiency model's lam / st / HFA / blend")
    ap.add_argument("--rows", help="write per-game rows (first model) to this json")
    ap.add_argument("--json", help="write the scoreboard to this json")
    ap.add_argument("--weeks", default="1-15")
    a = ap.parse_args()
    lo, _, hi = a.seasons.partition("-")
    seasons = list(range(int(lo), int(hi or lo) + 1))
    wlo, _, whi = a.weeks.partition("-")
    weeks = range(int(wlo), int(whi or wlo) + 1)
    ctxs = {s: SeasonCtx(s) for s in seasons}
    for s, c in ctxs.items():
        print(f"{s}: {len(c.teams)} rated teams, {len(c.games)} rated games, {sum(g['id'] in c.lines for g in c.games)} with a closing line")

    report = dict(generated=dt.datetime.now().isoformat(timespec="seconds"), seasons=seasons, weeks=[weeks.start, weeks.stop - 1], models={})
    models = [m.strip() for m in a.model.split(",") if m.strip()]
    all_rows = {}
    for name in models:
        model = MODELS[name]
        rows = {s: season_rows(s, model, ctxs[s], weeks) for s in seasons}
        all_rows[name] = rows
        pooled = [r for s in seasons for r in rows[s]]
        print(f"\n=== {name}: {desc(model)} ===")
        print(HEAD)
        rep = dict(desc=desc(model), seasons={}, pooled=None, baselines=None)
        for s in seasons:
            sc = score(rows[s]); rep["seasons"][s] = sc
            print(fmt_score(str(s), sc))
        sc = score(pooled); rep["pooled"] = sc
        print(fmt_score("POOLED", sc))
        b = baselines(pooled); rep["baselines"] = b
        for k, v in b.items():
            print(fmt_score("  " + k, v))
        wk2 = [r for r in pooled if r["wk"] >= 2]
        rep["pooled_wk2plus"] = score(wk2); rep["baselines_wk2plus"] = baselines(wk2)
        print(fmt_score("POOLED wk2+", rep["pooled_wk2plus"]))
        for k, v in rep["baselines_wk2plus"].items():
            print(fmt_score("  " + k, v))
        rep["calibration"] = calibration(pooled)
        rep["calibration_mkt"] = calibration([r for r in pooled if r.get("p_mkt") is not None], "p_mkt")
        print("\ncalibration (home win prob buckets):  model                | market")
        cm = {c["bucket"]: c for c in rep["calibration_mkt"]}
        for c in rep["calibration"]:
            k = cm.get(c["bucket"], {})
            print(f"  {c['bucket']:>9s}  n={c['n']:5d} pred {c['pred']:.3f} actual {c['actual']:.3f}   | n={k.get('n', 0):5d} pred {k.get('pred', float('nan')):.3f} actual {k.get('actual', float('nan')):.3f}")
        rep["fav_bias"] = {s: fav_bias(rows[s]) for s in seasons}; rep["fav_bias"]["pooled"] = fav_bias(pooled)
        rep["fav_bias_mkt"] = fav_bias([r for r in pooled if r.get("mkt") is not None], "mkt")
        print("\nfavorite-side bias by predicted margin (actual - predicted from the favorite's side; - = favorites over-rated):")
        print("  bucket   " + "  ".join(f"{str(s):>12s}" for s in list(seasons) + ["pooled"]) + "      market")
        for i, c in enumerate(rep["fav_bias"]["pooled"]):
            cells = []
            for s in list(seasons) + ["pooled"]:
                row = next((x for x in rep["fav_bias"][s] if x["bucket"] == c["bucket"]), None)
                cells.append(f"{row['bias']:+6.2f} (n{row['n']:3d})" if row else "           -")
            km = next((x for x in rep["fav_bias_mkt"] if x["bucket"] == c["bucket"]), None)
            print(f"  {c['bucket']:>6s}   " + "  ".join(cells) + (f"   {km['bias']:+6.2f}" if km else ""))
        rep["by_spread"] = by_spread(pooled)
        print("\nby closing spread (MAE model vs market):")
        for c in rep["by_spread"]:
            print(f"  {c['bucket']:>7s} n={c['n']:5d} model {c['model']:6.2f} market {c['market']:6.2f} gap {c['model'] - c['market']:+5.2f}")
        rep["by_week"] = {}
        print("\nby week (pooled MAE model / frozen / market, n):")
        for w in weeks:
            W = [r for r in pooled if r["wk"] == w]
            if not W:
                continue
            L = [r for r in W if r.get("mkt") is not None]
            d = dict(n=len(W), mae=float(np.mean([abs(r["margin"] - r["model"]) for r in W])),
                     frozen=float(np.mean([abs(r["margin"] - r["pre"]) for r in W])),
                     market=(float(np.mean([abs(r["margin"] - r["mkt"]) for r in L])) if L else None),
                     mae_on_mkt=(float(np.mean([abs(r["margin"] - r["model"]) for r in L])) if L else None))
            rep["by_week"][w] = d
            print(f"  wk{w:2d} n={d['n']:4d} model {d['mae']:6.2f} frozen {d['frozen']:6.2f} market {d['market'] if d['market'] is None else round(d['market'], 2)} (model on those {d['mae_on_mkt'] if d['mae_on_mkt'] is None else round(d['mae_on_mkt'], 2)})")
        report["models"][name] = rep

    if a.tune:
        fit = [s for s in seasons if s <= 2024]; test = [s for s in seasons if s == 2025]
        print(f"\n=== TUNE: fit {fit} / test {test}, weeks 2-15, {len(list(itertools.product(*GRID.values())))} configs ===")
        res = tune(ctxs, fit, test)
        report["tune"] = dict(fit=fit, test=test, grid=GRID, top=res[:25], all=res,
                              current=next(r for r in res if r["lam"] == CURRENT["lam"] and r["hfa"] == CURRENT["hfa"]
                                           and r["cap"] == CURRENT["cap"] and r["switch"] == CURRENT["switch"]),
                              current_rank=1 + next(i for i, r in enumerate(res) if r["lam"] == CURRENT["lam"] and r["hfa"] == CURRENT["hfa"]
                                                    and r["cap"] == CURRENT["cap"] and r["switch"] == CURRENT["switch"]),
                              n=len(res))
        print(f"{'rank':>4} {'lam':>4} {'hfa':>4} {'cap':>4} {'sw':>3} | {'fit MAE':>8} {'Brier':>6} {'ATS':>6} | {'test MAE':>8} {'Brier':>6} {'ATS':>6}")
        for i, r in enumerate(res[:15], 1):
            print(f"{i:4d} {r['lam']:4g} {r['hfa']:4g} {str(r['cap']):>4} {r['switch']:3d} | {r['fit_mae']:8.3f} {r['fit_brier']:.4f} {100 * (r['fit_ats'] or 0):5.1f}% | {r['test_mae']:8.3f} {r['test_brier']:.4f} {100 * (r['test_ats'] or 0):5.1f}%")
        c = report["tune"]["current"]
        print(f"hand-picked (lam 3, hfa 2.5, cap 28, switch 4): rank {report['tune']['current_rank']} of {len(res)} | fit {c['fit_mae']:.3f} test {c['test_mae']:.3f}")
        # marginal view: best per value of each parameter
        for k in ("lam", "hfa", "cap", "switch"):
            print(f"  best fit MAE by {k}: " + "  ".join(f"{v}:{min(r['fit_mae'] for r in res if r[k] == v):.3f}" for v in GRID[k]))
        for k in ("lam", "hfa", "cap", "switch"):
            print(f"  best fit Brier by {k}: " + "  ".join(f"{v}:{min(r['fit_brier'] for r in res if r[k] == v):.4f}" for v in GRID[k]))
        for k in ("cap", "switch"):
            print(f"  best TEST MAE by {k}: " + "  ".join(f"{v}:{min(r['test_mae'] for r in res if r[k] == v):.3f}" for v in GRID[k])
                  + f"   best TEST Brier by {k}: " + "  ".join(f"{v}:{min(r['test_brier'] for r in res if r[k] == v):.4f}" for v in GRID[k]))

    if a.tune_eff:
        from efficiency_ratings import EfficiencyModel
        fit = [s for s in seasons if s <= 2024]; test = [s for s in seasons if s == 2025]
        grid = {"current": MODELS["current"]}
        for lam in (1, 2, 3, 4, 6, 8):
            for hfa in (2.0, 2.5, 3.0):
                grid[f"eff lam{lam} hfa{hfa}"] = EfficiencyModel(lam=lam, hfa=hfa)
        for st in (4, 16, 1e9):
            grid[f"eff lam3 st{st:g}"] = EfficiencyModel(lam_st=st)
        for b in (0.25, 0.5, 0.75):
            grid[f"blend {b:g} (lam3)"] = EfficiencyModel(blend=b)
        for lam in (2, 4):
            grid[f"blend 0.5 lam{lam}"] = EfficiencyModel(lam=lam, blend=0.5)
        print(f"\n=== TUNE efficiency: fit {fit} / test {test}, weeks 2-15, {len(grid)} models ===")
        res = compare(ctxs, grid, fit, test)
        report["tune_eff"] = res
        print(f"{'model':24s} | {'fit MAE':>8} {'Brier':>6} {'ATS':>6} | {'test MAE':>8} {'Brier':>6} {'ATS':>6}")
        for r in res:
            print(f"{r['name']:24s} | {r['fit_mae']:8.3f} {r['fit_brier']:.4f} {100 * (r['fit_ats'] or 0):5.1f}% | "
                  f"{r['test_mae']:8.3f} {r['test_brier']:.4f} {100 * (r['test_ats'] or 0):5.1f}%")

    if a.rows:
        Path(a.rows).write_text(json.dumps([r for s in seasons for r in all_rows[models[0]][s]], indent=0, default=float), encoding="utf-8")
        print(f"wrote {a.rows}")
    if a.json:
        Path(a.json).write_text(json.dumps(report, indent=1, default=float), encoding="utf-8")
        print(f"wrote {a.json}")


if __name__ == "__main__":
    main()
