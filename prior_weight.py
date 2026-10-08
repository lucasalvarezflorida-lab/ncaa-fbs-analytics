"""prior_weight.py - how much should the July number still count in October?

Lucas (10/8): the machine keeps quoting July (the FPI prior) next to what a
team has shown since; is a CONSTANT prior weight still the best way to say
who is best on paper? (Texas A&M: 9th at 18.0 after a home loss to Kentucky
and 6-35 at LSU.)

The on-air ridge (inseason_ratings.RULE) solves
    min  sum_games (y_g - (r_home - r_away + HFA))^2 + LAM * sum_teams (r - prior)^2
with LAM = 3 all season: the prior is always worth three games of evidence,
so after four rated games it still carries 3/7 of a team's rating. The
tuning grid (BACKTEST_2026.md) only ever tried CONSTANT lambdas. This module
is the same ridge (de-lucked observations, residual cap 42, HFA 2.5) with
three knobs the grid never had, as a backtest.py plug-in:

  * prior decay: lam_w = max(lam_min, lam0 * 0.5 ** ((w - 2) / half)) when
    predicting week w (week 2 = the first week with any evidence, lam0 there;
    the prior's weight halves every `half` weeks down to lam_min).
  * recency: a game played in week j counts rho ** (w - 1 - j) when
    predicting week w (last week's games count 1, the week before rho, ...).
  * shrink: the prior's spread scaled toward its mean, p' = mean + s (p - mean),
    in case the July numbers are over- or under-dispersed.

lam0 = 3, no decay, rho = 1, shrink = 1 reproduces the on-air machine exactly
(the "pw_current" row on every table is the check).

    python backtest.py --seasons 2022-2025 --tune-prior      # the grid, fit 2022-24 / test 2025
    python prior_weight.py --today                             # 2026 as of today under the candidates (Top 25 + named teams)

Nothing here touches the on-air number; this is a backtest input until Lucas
says otherwise. Result file: internal/PRIOR_WEIGHT_2026.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
import inseason_ratings as ir  # noqa: E402

OBS = dict(to=3.0)       # the on-air observation (margin - 3 x turnover margin)


class PriorWeightModel:
    """backtest.py plug-in: callable(ctx, week) -> {game_id: (margin, p_home)}."""

    def __init__(self, lam0=3.0, half=None, lam_min=0.0, rho=1.0, shrink=1.0, mismatch=None,
                 hfa=ir.HFA, cap=42.0, switch=4, obs=OBS, desc=""):
        self.lam0, self.half, self.lam_min, self.rho, self.shrink = float(lam0), half, float(lam_min), float(rho), float(shrink)
        self.mismatch = mismatch   # K: a game the PRIOR expected to be decided by E counts 1 / (1 + (E/K)^2) - cupcakes tell less
        self.hfa, self.cap, self.switch, self.obs_spec = hfa, cap, switch, obs   # switch: first week on the residual cap (margin cap before it), as on air
        self.desc = desc or self.label()

    def label(self):
        s = f"lam0 {self.lam0:g}"
        if self.half:
            s += f" half {self.half:g}wk floor {self.lam_min:g}"
        if self.rho != 1.0:
            s += f" rho {self.rho:g}"
        if self.shrink != 1.0:
            s += f" shrink {self.shrink:g}"
        if self.mismatch:
            s += f" mismatch K{self.mismatch:g}"
        return s

    def lam_at(self, week: int) -> float:
        if not self.half:
            return self.lam0
        return max(self.lam_min, self.lam0 * 0.5 ** ((week - 2) / float(self.half)))

    def ratings(self, ctx, week: int) -> np.ndarray:
        """Ratings vector before `week` (games from weeks < week only)."""
        p = ctx.p
        if self.shrink != 1.0:
            p = p.mean() + self.shrink * (p - p.mean())
        rows = ctx.before(week)
        if not len(rows):
            return p.copy()
        Xw = ctx.X[rows]
        y = ctx.obs(self.obs_spec)[rows]
        h = ctx.home[rows] * self.hfa
        if self.cap is not None and week < self.switch:
            y = np.clip(y, -self.cap, self.cap)
        resid = y - (Xw @ p + h)
        if self.cap is not None and week >= self.switch:
            resid = np.clip(resid, -self.cap, self.cap)
        w = self.rho ** (week - 1 - ctx.week[rows]) if self.rho != 1.0 else np.ones(len(rows))
        if self.mismatch:
            w = w / (1.0 + ((Xw @ p + h) / float(self.mismatch)) ** 2)
        lam = self.lam_at(week)
        A = Xw.T @ (w[:, None] * Xw) + lam * np.eye(Xw.shape[1])
        d = np.linalg.solve(A, Xw.T @ (w * resid))
        return p + d

    def __call__(self, ctx, week: int) -> dict:
        rows = np.flatnonzero(ctx.week == week)
        if not len(rows):
            return {}
        r = self.ratings(ctx, week)
        m = ctx.X[rows] @ r + ctx.home[rows] * self.hfa
        pr = ctx.curve(week).win_prob(m)
        return {ctx.games[i]["id"]: (float(mm), float(pp)) for i, mm, pp in zip(rows, m, pr)}


def grid() -> dict:
    """The --tune-prior grid: decay x floor x lam0, recency alone, shrink alone, and a few combinations."""
    g = {"pw_current": PriorWeightModel(desc="CHECK: lam 3 constant = the on-air machine")}
    for lam0 in (3.0, 4.0, 6.0):
        for half in (3.0, 5.0, 8.0, 12.0):
            for lam_min in (0.5, 1.0, 1.5):
                g[f"decay l{lam0:g} h{half:g} f{lam_min:g}"] = PriorWeightModel(lam0=lam0, half=half, lam_min=lam_min)
    for lam0 in (2.0, 4.0):
        g[f"const l{lam0:g}"] = PriorWeightModel(lam0=lam0)
    for rho in (0.80, 0.85, 0.90, 0.95):
        g[f"recency rho{rho:g}"] = PriorWeightModel(rho=rho)
    for s in (0.8, 0.9, 1.1, 1.2):
        g[f"shrink {s:g}"] = PriorWeightModel(shrink=s)
    for K in (14.0, 21.0, 28.0, 42.0):
        g[f"mismatch K{K:g}"] = PriorWeightModel(mismatch=K)
    g["mismatch K28 lam2"] = PriorWeightModel(lam0=2.0, mismatch=28.0)
    for rho in (0.90, 0.95):
        g[f"decay l4 h5 f1 + rho{rho:g}"] = PriorWeightModel(lam0=4.0, half=5.0, lam_min=1.0, rho=rho)
        g[f"decay l3 h8 f1 + rho{rho:g}"] = PriorWeightModel(lam0=3.0, half=8.0, lam_min=1.0, rho=rho)
    return g


# ---------------- 2026 as of today ----------------

def today(models: dict, names=("texas am", "oregon", "alabama", "ohio state", "georgia", "miami", "lsu", "indiana",
                               "utah", "northwestern", "usc", "penn state", "texas tech", "kentucky"), top=25) -> dict:
    """Solve 2026 with every completed rated game under each model; returns {name: {team: rating}}."""
    import backtest as bt
    ctx = bt.SeasonCtx(2026)
    week = int(ctx.week.max()) + 1          # everything completed counts, as machine_ratings does
    out = {}
    for name, m in models.items():
        r = m.ratings(ctx, week)
        out[name] = dict(zip(ctx.teams, map(float, r)))
    ranks = {n: {t: i + 1 for i, t in enumerate(sorted(r, key=lambda t: -r[t]))} for n, r in out.items()}
    cols = list(models)
    print(f"2026 through week {week - 1} ({len(ctx.before(week))} rated games), no QB-out layer applied")
    print(f"{'team':20s} {'July':>6} " + " ".join(f"{c[:14]:>14s}" for c in cols))
    base = cols[0]
    order = sorted(ctx.teams, key=lambda t: -out[base][t])
    for t in order[:top]:
        print(f"{t:20s} {ctx.prior[t]:6.1f} " + " ".join(f"{out[c][t]:7.1f} (#{ranks[c][t]:3d})" for c in cols))
    print("named teams:")
    for t in names:
        if t in ctx.prior:
            print(f"{t:20s} {ctx.prior[t]:6.1f} " + " ".join(f"{out[c][t]:7.1f} (#{ranks[c][t]:3d})" for c in cols))
    return out


def team_card(team: str, model: PriorWeightModel | None = None) -> None:
    """Why a team sits where it sits under the on-air rule: each rated game's expected (from the
    CURRENT ratings) vs de-lucked margin, the capped residual, and the per-game pull."""
    import backtest as bt
    import obs_features as of
    model = model or PriorWeightModel()
    ctx = bt.SeasonCtx(2026)
    week = int(ctx.week.max()) + 1
    r = dict(zip(ctx.teams, map(float, model.ratings(ctx, week))))
    feats = of.build(2026, ctx.games)
    rank = {t: i + 1 for i, t in enumerate(sorted(r, key=lambda t: -r[t]))}
    print(f"\n{team}: July {ctx.prior[team]:.1f} -> now {r[team]:.1f} (#{rank[team]}) under {model.label()}")
    print(f"{'wk':>2} {'opponent':22s} {'site':4s} {'opp now':>7} {'expect':>7} {'actual':>7} {'TO':>3} {'de-luck':>7} {'resid':>6}")
    for g in ctx.games:
        if team not in (g["home"], g["away"]):
            continue
        home = g["home"] == team
        opp = g["away"] if home else g["home"]
        h = 0.0 if g["neutral"] else model.hfa
        exp = (r[team] - r[opp] + h) if home else (r[team] - r[opp] - h)
        to = feats.get(g["id"], {}).get("to_home", 0.0)
        act = g["margin"] if home else -g["margin"]
        to_t = to if home else -to
        dl = act - model.obs_spec.get("to", 0.0) * to_t
        resid = dl - exp
        capped = max(-model.cap, min(model.cap, resid)) if model.cap else resid
        site = "home" if home else ("neut" if g["neutral"] else "away")
        print(f"{g['week']:2d} {opp:22s} {site:4s} {r[opp]:7.1f} {exp:+7.1f} {act:+7.1f} {to_t:+3.0f} {dl:+7.1f} {capped:+6.1f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--today", action="store_true", help="2026 as of today under the named candidates")
    ap.add_argument("--models", default="pw_current,decay l4 h5 f1,recency rho0.9,decay l4 h5 f1 + rho0.9",
                    help="comma list of grid() keys for --today")
    ap.add_argument("--team", help="team card (normalized name) under the on-air rule")
    a = ap.parse_args()
    G = grid()
    if a.team:
        team_card(a.team)
    if a.today:
        today({k: G[k] for k in [s.strip() for s in a.models.split(",")]})
