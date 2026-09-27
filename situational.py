"""Situational layer (batch 3 of the 9/27 enhancement list): rest, byes,
Friday / weeknight kickoffs, travel distance, time zones crossed, elevation,
and a per-team home-field estimate - applied AFTER the ridge as a points
adjustment to the on-air prediction, never inside the rating.

    python backtest.py --seasons 2022-2025 --tune-sit      # fit 2022-24 residuals, test 2025

FEATURES per game (home perspective), from the games cache (every game the
team played, FCS included, for rest) plus /venues and /teams/fbs (cached):
  rest_diff   home rest days - away rest days (each capped at 14; opener = 14), clipped +-7
  bye_diff    (home off a bye) - (away off a bye); bye = 12+ days
  fri, wkn    Friday kickoff; Tue/Wed/Thu kickoff (local ~ UTC-5)
  dist_diff   (away travel - home travel) in 1,000 km; home travel is 0 unless neutral
  tz_diff     time zones the away team crossed - the home team crossed (longitude/15, absolute)
  elev_diff   venue elevation - away team's home elevation, minus the same for the home team, km
The residual (actual - on-air prediction) is regressed on those on the fit
seasons, weeks 2+; the fitted coefficients are then applied on the test
season. Per-team HFA: mean home residual per team on the fit seasons, shrunk
toward zero with K games of prior, applied as a delta on top of the 2.5.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

DATA = HERE / "fpi-decomposition" / "data"
FEATS = ["rest_diff", "bye_diff", "fri", "wkn", "dist_diff", "tz_diff", "elev_diff"]


def _pick(g, *names):
    for k in names:
        if g.get(k) is not None:
            return g[k]
    return None


def _hav(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


class Geo:
    def __init__(self):
        v = json.loads((DATA / "venues.json").read_text(encoding="utf-8"))
        self.venues = {x["id"]: x for x in v}
        t = json.loads((DATA / "teams_fbs_year-2026.json").read_text(encoding="utf-8"))
        self.home = {}
        for x in t:
            loc = x.get("location") or {}
            if loc.get("latitude") is not None:
                self.home[normalize_name(x["school"])] = dict(lat=loc["latitude"], lon=loc["longitude"],
                                                              elev=float(loc.get("elevation") or 0.0), vid=loc.get("id"))

    def venue(self, vid):
        x = self.venues.get(vid)
        if not x or x.get("latitude") is None:
            return None
        return dict(lat=x["latitude"], lon=x["longitude"], elev=float(x.get("elevation") or 0.0))


def features(season: int, games: list[dict], geo: Geo | None = None) -> dict[int, dict]:
    """games = backtest.SeasonCtx.games (rated games). Rest uses EVERY game in the cache."""
    geo = geo or Geo()
    raw = json.loads((DATA / f"games_seasonType-regular_year-{season}.json").read_text(encoding="utf-8"))
    sched = defaultdict(list)
    for g in raw:
        d = _pick(g, "startDate", "start_date")
        if not d:
            continue
        day = dt.datetime.fromisoformat(d.replace("Z", "+00:00")) - dt.timedelta(hours=5)
        for t in (_pick(g, "homeTeam", "home_team"), _pick(g, "awayTeam", "away_team")):
            if t:
                sched[normalize_name(t)].append(day.date())
    for t in sched:
        sched[t].sort()
    byid = {_pick(g, "id"): g for g in raw}
    out = {}
    for g in games:
        r = byid.get(g["id"])
        if not r:
            continue
        day = (dt.datetime.fromisoformat(r["startDate"].replace("Z", "+00:00")) - dt.timedelta(hours=5))
        f = {}
        rest = {}
        for side in ("home", "away"):
            days = sched.get(g[side], [])
            prev = [x for x in days if x < day.date()]
            rest[side] = min(14, (day.date() - prev[-1]).days) if prev else 14
        f["rest_h"], f["rest_a"] = rest["home"], rest["away"]
        f["rest_diff"] = float(max(-7, min(7, rest["home"] - rest["away"])))
        f["bye_diff"] = float((rest["home"] >= 12) - (rest["away"] >= 12))
        wd = day.weekday()
        f["fri"] = 1.0 if wd == 4 else 0.0
        f["wkn"] = 1.0 if wd in (1, 2, 3) else 0.0
        ven = geo.venue(_pick(r, "venueId", "venue_id"))
        hh, ah = geo.home.get(g["home"]), geo.home.get(g["away"])
        dist = {"home": 0.0, "away": 0.0}; tz = {"home": 0.0, "away": 0.0}; el = {"home": 0.0, "away": 0.0}
        if ven and hh and ah:
            for side, hm in (("home", hh), ("away", ah)):
                if side == "home" and not g["neutral"]:
                    continue
                dist[side] = _hav(hm["lat"], hm["lon"], ven["lat"], ven["lon"])
                tz[side] = abs(round((ven["lon"] - hm["lon"]) / 15.0))
                el[side] = (ven["elev"] - hm["elev"]) / 1000.0
        f["dist_h"], f["dist_a"] = dist["home"], dist["away"]
        f["dist_diff"] = (dist["away"] - dist["home"]) / 1000.0
        f["tz_diff"] = tz["away"] - tz["home"]
        f["elev_diff"] = el["away"] - el["home"]
        out[g["id"]] = f
    return out


def _design(feats: dict[int, dict], games, ids, names):
    X = np.array([[1.0] + [feats[i][k] for k in names] for i in ids])
    return X


def fit(ctxs: dict, fit_seasons, names=FEATS, weeks=range(2, 16)) -> dict:
    """OLS of the on-air residual (actual - predicted, home side) on the features."""
    import backtest as bt
    geo = Geo()
    rows, ys = [], []
    for s in fit_seasons:
        ctx = ctxs[s]
        F = features(s, ctx.games, geo)
        for w in weeks:
            pr = bt.ridge_predict(ctx, w, bt.MODELS["current"])
            for g in ctx.games:
                if g["week"] == w and g["id"] in pr and g["id"] in F:
                    rows.append([1.0] + [F[g["id"]][k] for k in names]); ys.append(g["margin"] - pr[g["id"]][0])
    X, y = np.array(rows), np.array(ys)
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ b
    s2 = resid @ resid / max(len(y) - X.shape[1], 1)
    cov = s2 * np.linalg.pinv(X.T @ X)
    se = np.sqrt(np.diag(cov))
    return dict(names=["intercept"] + list(names), coef=b.tolist(), se=se.tolist(), t=(b / se).tolist(), n=int(len(y)),
                mean_abs=[float(np.mean(np.abs(X[:, j]))) for j in range(X.shape[1])])


class SituationalModel:
    """backtest.py plug-in: on-air prediction + fitted situational adjustment (coef dict from fit())."""

    def __init__(self, coef: dict, names=FEATS, desc=""):
        self.coef, self.names = coef, list(names)
        self.desc = desc or f"SHADOW situational: {', '.join(names)}"
        self._F = {}
        self.geo = Geo()

    def F(self, ctx):
        if ctx.season not in self._F:
            self._F[ctx.season] = features(ctx.season, ctx.games, self.geo)
        return self._F[ctx.season]

    def __call__(self, ctx, week):
        import backtest as bt
        cur = bt.ridge_predict(ctx, week, bt.MODELS["current"])
        if not cur:
            return {}
        F = self.F(ctx)
        rows = np.flatnonzero(ctx.week == week)
        m = []
        for i in rows:
            g = ctx.games[i]
            f = F.get(g["id"])
            adj = sum(self.coef.get(k, 0.0) * f[k] for k in self.names) if f else 0.0
            m.append(cur[g["id"]][0] + adj)
        m = np.array(m)
        p = ctx.curve(week).win_prob(m)
        return {ctx.games[i]["id"]: (float(mm), float(pp)) for i, mm, pp in zip(rows, m, p)}


def team_hfa(ctxs: dict, seasons, K: float = 20.0, weeks=range(2, 16)) -> dict[str, float]:
    """Per-team home-field delta: mean home residual of the on-air machine at
    the team's home games over `seasons`, shrunk toward 0 with K games."""
    import backtest as bt
    acc = defaultdict(lambda: [0.0, 0])
    for s in seasons:
        ctx = ctxs[s]
        for w in weeks:
            pr = bt.ridge_predict(ctx, w, bt.MODELS["current"])
            for g in ctx.games:
                if g["week"] == w and g["id"] in pr and not g["neutral"]:
                    acc[g["home"]][0] += g["margin"] - pr[g["id"]][0]; acc[g["home"]][1] += 1
    return {t: v[0] / (v[1] + K) for t, v in acc.items()}


class TeamHFAModel:
    """on-air prediction + the home team's HFA delta (leave-one-season-out on fit seasons, prior seasons on test)."""

    def __init__(self, ctxs: dict, fit_seasons, K: float = 20.0, desc=""):
        self.K = K
        self.desc = desc or f"SHADOW per-team HFA delta, K={K:g}"
        self.deltas = {}
        for s in ctxs:
            src = [x for x in fit_seasons if x != s] if s in fit_seasons else list(fit_seasons)
            self.deltas[s] = team_hfa(ctxs, src, K)

    def __call__(self, ctx, week):
        import backtest as bt
        cur = bt.ridge_predict(ctx, week, bt.MODELS["current"])
        if not cur:
            return {}
        d = self.deltas.get(ctx.season, {})
        rows = np.flatnonzero(ctx.week == week)
        m = np.array([cur[ctx.games[i]["id"]][0] + (0.0 if ctx.games[i]["neutral"] else d.get(ctx.games[i]["home"], 0.0)) for i in rows])
        p = ctx.curve(week).win_prob(m)
        return {ctx.games[i]["id"]: (float(mm), float(pp)) for i, mm, pp in zip(rows, m, p)}
