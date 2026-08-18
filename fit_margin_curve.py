"""Fit the margin -> win-probability curves from cached CFBD data, 2021-2025.

  model curve : residuals vs prior-year final FPI gap + 2.5 HFA — the same
                stale-prior convention as backtest_upset_alert.py, i.e. what
                the live board actually knows. FCS/unrated games excluded.
  market curve: residuals vs the closing spread, straight from
                market-postmortem/market_bets_2021_2025.csv.

Validation is out-of-sample: curves fit on 2021-2024 are scored on 2025
against the Season Sim's current conversion, Normal(0, 13.5), plus a
corrected-sigma normal (to separate the sigma error from the shape error).
The shipped curves are then refit on all five seasons and written to
margin_prob_curve.json.

Run:  python fit_margin_curve.py     (cached data only — no API calls)
Rerun once a year, or after changing the model-margin convention.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import ndtr

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "fpi-decomposition"))

from name_mapping import normalize_name  # noqa: E402

from margin_prob import CURVE_JSON, MarginCurve, save_curves  # noqa: E402

HFA = 2.5
SEASONS = [2021, 2022, 2023, 2024, 2025]
DATA = HERE / "fpi-decomposition" / "data"
MARKET_CSV = HERE / "market-postmortem" / "market_bets_2021_2025.csv"
SIM_SIGMA = 13.5  # the Season Sim's current assumption, used as the baseline


def _pick(g: dict, *names):
    for n in names:
        if g.get(n) is not None:
            return g[n]
    return None


def _load_fpi(year: int) -> dict[str, float]:
    path = DATA / f"ratings_fpi_year-{year}.json"
    return {normalize_name(r["team"]): float(r["fpi"])
            for r in json.loads(path.read_text(encoding="utf-8"))
            if r.get("fpi") is not None}


def model_rows(seasons: list[int]) -> pd.DataFrame:
    """One row per completed game with both teams in the prior-year FPI:
    (season, model_margin, actual_margin)."""
    rows = []
    for season in seasons:
        fpi = _load_fpi(season - 1)
        for stype in ("regular", "postseason"):
            path = DATA / f"games_seasonType-{stype}_year-{season}.json"
            if not path.exists():
                continue
            for g in json.loads(path.read_text(encoding="utf-8")):
                if not _pick(g, "completed"):
                    continue
                hp = _pick(g, "homePoints", "home_points")
                ap = _pick(g, "awayPoints", "away_points")
                home = _pick(g, "homeTeam", "home_team")
                away = _pick(g, "awayTeam", "away_team")
                if hp is None or ap is None or not home or not away:
                    continue
                fh = fpi.get(normalize_name(home))
                fa = fpi.get(normalize_name(away))
                if fh is None or fa is None:
                    continue
                neutral = bool(_pick(g, "neutralSite", "neutral_site"))
                model = fh - fa + (0 if neutral else HFA)
                rows.append((season, model, hp - ap))
    return pd.DataFrame(rows, columns=["season", "model", "actual"])


def brier(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((p - y) ** 2))


def logloss(p: np.ndarray, y: np.ndarray) -> float:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def validate(df: pd.DataFrame) -> dict:
    """Fit on 2021-2024, score 2025 home-win probabilities."""
    train = df[df.season <= 2024]
    test = df[df.season == 2025]
    curve = MarginCurve.fit(train.actual - train.model)
    m = test.model.to_numpy()
    y = (test.actual > 0).to_numpy().astype(float)
    sd_train = float((train.actual - train.model).std())

    candidates = {
        "empirical curve": curve.win_prob(m),
        f"Normal({SIM_SIGMA}) [Season Sim]": ndtr(m / SIM_SIGMA),
        f"Normal({sd_train:.1f}) [sigma fixed]": ndtr(m / sd_train),
    }
    print(f"\n=== out-of-sample validation: fit 2021-2024 (n={len(train)}), "
          f"score 2025 (n={len(test)}) ===")
    print(f"{'conversion':34} {'Brier':>8} {'log loss':>9}")
    scores = {}
    for name, p in candidates.items():
        scores[name] = dict(brier=round(brier(p, y), 5),
                            logloss=round(logloss(p, y), 5))
        print(f"{name:34} {scores[name]['brier']:8.5f} "
              f"{scores[name]['logloss']:9.5f}")

    print("\nreliability on 2025 (empirical curve):")
    p = candidates["empirical curve"]
    print(f"{'pred bucket':>12} {'n':>5} {'mean pred':>10} {'actual':>8}")
    buckets = []
    for lo in np.arange(0.0, 1.0, 0.1):
        mask = (p >= lo) & (p < lo + 0.1)
        if mask.sum() < 15:
            continue
        b = dict(bucket=f"{lo:.1f}-{lo + 0.1:.1f}", n=int(mask.sum()),
                 pred=round(float(p[mask].mean()), 3),
                 actual=round(float(y[mask].mean()), 3))
        buckets.append(b)
        print(f"{b['bucket']:>12} {b['n']:>5} {b['pred']:>10.3f} "
              f"{b['actual']:>8.3f}")

    print("\nbenchmark win probs (model margin -> P(win)):")
    print(f"{'margin':>7} {'empirical':>10} {'Normal(13.5)':>13} {'diff pp':>8}")
    bench = {}
    for mm in (-21, -14, -7, -3, 3, 7):
        pe = curve.win_prob(mm)
        pn = float(ndtr(mm / SIM_SIGMA))
        bench[mm] = dict(empirical=round(pe, 4), normal=round(pn, 4))
        print(f"{mm:>7} {pe:>10.1%} {pn:>13.1%} {100 * (pe - pn):>+7.1f}")

    resid = df.actual - df.model
    print("\nresidual sd by |model margin| (heteroskedasticity check, all seasons):")
    for lo, hi in ((0, 7), (7, 14), (14, 21), (21, 60)):
        mask = (df.model.abs() >= lo) & (df.model.abs() < hi)
        print(f"  |m| {lo:>2}-{hi:<2}: n={int(mask.sum()):4d} "
              f"sd={float(resid[mask].std()):.2f}")

    return dict(scores=scores, reliability=buckets,
                benchmarks={str(k): v for k, v in bench.items()},
                train_n=len(train), test_n=len(test))


def main() -> None:
    df = model_rows(SEASONS)
    per_season = df.groupby("season").size().to_dict()
    print(f"model-margin sample: {len(df)} games "
          f"(both teams in prior-year FPI) {per_season}")

    validation = validate(df)

    mkt = pd.read_csv(MARKET_CSV)
    mkt_resid = mkt["home_cover_margin"].dropna()

    model_curve = MarginCurve.fit(
        df.actual - df.model,
        meta=dict(kind="actual margin minus (prior-year FPI gap + 2.5 HFA)",
                  seasons=SEASONS, validation=validation))
    market_curve = MarginCurve.fit(
        mkt_resid,
        meta=dict(kind="actual margin minus closing-spread prediction",
                  seasons=SEASONS, source=MARKET_CSV.name))

    save_curves({"model": model_curve, "market": market_curve})
    print(f"\nmodel curve : n={model_curve.meta['n']} "
          f"sd={model_curve.meta['resid_sd']} bw={model_curve.meta['bandwidth']}")
    print(f"market curve: n={market_curve.meta['n']} "
          f"sd={market_curve.meta['resid_sd']} bw={market_curve.meta['bandwidth']}")
    print(f"wrote {CURVE_JSON}")


if __name__ == "__main__":
    main()
