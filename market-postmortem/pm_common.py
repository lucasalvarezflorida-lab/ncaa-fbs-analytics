"""Shared statistical machinery for the market post-mortems (CFB/NFL/NBA).

Same non-negotiables as the CFB run (analyze_market.py, which predates this
module and keeps its own embedded copy):
  * pushes excluded from win%; break-even at -110 juice is 52.38%
  * two-sided exact binomial test vs 50%
  * Benjamini-Hochberg FDR at q=0.10 across every test in a sport's battery
  * PERSISTENT = pooled direction repeated in >=80% of eligible seasons
    (a season is eligible with >=25 decided bets), with >=80% of seasons
    eligible; anything else is noise
  * moneyline strategies graded by ROI per $1 staked, bootstrap 95% CI
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
from scipy import stats

BREAK_EVEN = 100 / 210  # 52.38% at -110


def wilson_ci(w: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = w / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return center - half, center + half


def american_return(ml: float) -> float:
    """Profit per $1 staked on a winning bet at American odds."""
    return 100 / abs(ml) if ml < 0 else ml / 100


def grade(res: pd.Series) -> tuple[int, int, int]:
    return int((res == "W").sum()), int((res == "L").sum()), int((res == "P").sum())


def wlp(valid: pd.Series, win: pd.Series, push: pd.Series) -> pd.Series:
    """W/L/P result series (object dtype), NaN where the bet doesn't exist."""
    out = pd.Series(np.nan, index=valid.index, dtype=object)
    valid = valid.fillna(False).astype(bool)
    out[valid & push.fillna(False).astype(bool)] = "P"
    w = valid & ~push.fillna(False).astype(bool)
    out[w & win.fillna(False).astype(bool)] = "W"
    out[w & ~win.fillna(False).astype(bool)] = "L"
    return out


class Report:
    """Collects strategy tests, then applies BH FDR across all of them."""

    def __init__(self, seasons: list[int], seed: int,
                 min_per_season: int = 25, min_n: int = 40) -> None:
        self.seasons = seasons
        self.min_per_season = min_per_season
        self.min_n = min_n
        self.rng = np.random.default_rng(seed)
        self.rows: list[dict] = []

    def _persistence(self, per_season: dict[int, tuple[float | None, int]],
                     pooled_positive: bool) -> tuple[str, bool]:
        agree = eligible = 0
        for stat, n in per_season.values():
            if n >= self.min_per_season and stat is not None:
                eligible += 1
                if (stat >= 0) == pooled_positive:
                    agree += 1
        need_elig = math.ceil(0.8 * len(self.seasons))
        need_agree = math.ceil(0.8 * eligible) if eligible else 1
        return f"{agree}/{eligible}", (eligible >= need_elig
                                       and agree >= need_agree)

    def add_binary(self, family: str, name: str, df: pd.DataFrame,
                   res: pd.Series) -> None:
        res = res.dropna()
        w, l, p = grade(res)
        n = w + l
        if n < self.min_n:
            return
        pct = w / n
        lo, hi = wilson_ci(w, n)
        pval = stats.binomtest(w, n, 0.5).pvalue
        roi = (w * (10 / 11) - l) / n
        season_rec, per_season = {}, {}
        for yr in self.seasons:
            r = res[df.loc[res.index, "season"] == yr]
            sw, sl, sp = grade(r)
            season_rec[yr] = f"{sw}-{sl}-{sp}"
            per_season[yr] = ((sw / (sw + sl) - 0.5) if sw + sl else None,
                              sw + sl)
        agree, persistent = self._persistence(per_season, pct >= 0.5)
        self.rows.append(dict(
            family=family, strategy=name, n=n, record=f"{w}-{l}-{p}",
            win_pct=round(100 * pct, 2), ci_lo=round(100 * lo, 2),
            ci_hi=round(100 * hi, 2), p_value=pval,
            roi_at_110=round(100 * roi, 2),
            beats_breakeven=int(pct > BREAK_EVEN),
            ci_clears_breakeven=int(lo > BREAK_EVEN),
            seasons_agree=agree, persistent=int(persistent),
            **{f"s{yr}": season_rec[yr] for yr in self.seasons},
        ))

    def add_roi(self, family: str, name: str, df: pd.DataFrame,
                returns: pd.Series) -> None:
        returns = returns.dropna()
        n = len(returns)
        if n < self.min_n:
            return
        roi = returns.mean()
        boots = self.rng.choice(returns.values, size=(4000, n),
                                replace=True).mean(axis=1)
        lo, hi = np.percentile(boots, [2.5, 97.5])
        _, pval = stats.ttest_1samp(returns.values, 0.0)
        w = int((returns > 0).sum())
        l = int((returns < 0).sum())
        season_rec, per_season = {}, {}
        for yr in self.seasons:
            r = returns[df.loc[returns.index, "season"] == yr]
            season_rec[yr] = (f"{round(100 * r.mean(), 1)}% ({len(r)})"
                              if len(r) else "-")
            per_season[yr] = (r.mean() if len(r) else None, len(r))
        agree, persistent = self._persistence(per_season, roi >= 0)
        self.rows.append(dict(
            family=family, strategy=name, n=n, record=f"{w}-{l}-0",
            win_pct=round(100 * w / max(w + l, 1), 2), ci_lo=round(100 * lo, 2),
            ci_hi=round(100 * hi, 2), p_value=pval,
            roi_at_110=round(100 * roi, 2),
            beats_breakeven=int(roi > 0), ci_clears_breakeven=int(lo > 0),
            seasons_agree=agree, persistent=int(persistent),
            **{f"s{yr}": season_rec[yr] for yr in self.seasons},
        ))

    def finish_bh(self, q: float = 0.10) -> pd.DataFrame:
        m = len(self.rows)
        order = sorted(range(m), key=lambda i: self.rows[i]["p_value"])
        thresh = 0
        for rank, i in enumerate(order, start=1):
            if self.rows[i]["p_value"] <= q * rank / m:
                thresh = rank
        for rank, i in enumerate(order, start=1):
            self.rows[i]["bh_significant"] = int(rank <= thresh)
        for r in self.rows:
            r["p_value"] = round(r["p_value"], 5)
        out = pd.DataFrame(self.rows)
        return out.sort_values(["bh_significant", "persistent", "p_value"],
                               ascending=[False, False, True])


def line_calibration(line_pred: pd.Series, actual: pd.Series,
                     edges: list[float], cover_res: pd.Series,
                     cover_label: str) -> dict:
    """Bias/MAE/slope + bucket curve for one market (spread or total).

    line_pred = the market's prediction (predicted margin or the total),
    actual = what happened, cover_res = W/L/P of the reference side
    (home cover / over) for the bucket curve.
    """
    err = actual - line_pred
    fit = stats.linregress(line_pred, actual)
    slope_se = fit.stderr
    curve = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (line_pred > lo) & (line_pred <= hi)
        if m.sum() < 20:
            continue
        w, l, _p = grade(cover_res[m])
        curve.append(dict(bucket=f"({lo:g},{hi:g}]", n=int(m.sum()),
                          mean_line=round(float(line_pred[m].mean()), 2),
                          mean_actual=round(float(actual[m].mean()), 2),
                          **{cover_label: round(100 * w / max(w + l, 1), 1)}))
    return dict(
        n=int(len(err)), bias_pts=round(float(err.mean()), 3),
        bias_se=round(float(err.std() / np.sqrt(len(err))), 3),
        mae=round(float(err.abs().mean()), 2),
        rmse=round(float(np.sqrt((err ** 2).mean())), 2),
        slope=round(fit.slope, 4), slope_se=round(slope_se, 4),
        intercept=round(fit.intercept, 3), r2=round(fit.rvalue ** 2, 4),
        curve=curve,
    )


def ml_calibration(home_ml: pd.Series, away_ml: pd.Series,
                   home_won: pd.Series) -> dict:
    """Devigged (proportional) home-prob calibration curve + Brier."""
    dec_h = home_ml.map(lambda x: 1 + american_return(x) if pd.notna(x) else np.nan)
    dec_a = away_ml.map(lambda x: 1 + american_return(x) if pd.notna(x) else np.nan)
    qh, qa = 1 / dec_h, 1 / dec_a
    p = (qh / (qh + qa)).dropna()
    won = home_won.loc[p.index]
    curve = []
    for lo in np.arange(0.05, 0.95, 0.10):
        m = (p >= lo) & (p < lo + 0.10)
        if m.sum() < 30:
            continue
        curve.append(dict(bucket=f"{lo:.2f}-{lo + 0.10:.2f}", n=int(m.sum()),
                          implied=round(float(p[m].mean()), 3),
                          actual=round(float(won[m].mean()), 3)))
    return dict(n=int(len(p)),
                brier=round(float(((p - won) ** 2).mean()), 4),
                curve=curve), p
