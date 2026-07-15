"""Market post-mortem analysis: grade the CFB closing line, 2021-2025.

Reads market_bets_2021_2025.csv (build_dataset.py) and produces:
  slice_results.csv  — every strategy test: N, W-L-P, win%, Wilson CI,
                       exact binomial p vs 50%, ROI at -110, per-season
                       records, Benjamini-Hochberg flag, persistence flag
  results.json       — calibration curves + headline numbers for charts/report

Statistical rules (non-negotiable):
  * Pushes excluded from win%; break-even at -110 juice is 52.38%.
  * Two-sided exact binomial test vs 50% (the calibration null).
  * Benjamini-Hochberg FDR at q=0.10 across ALL slice tests.
  * PERSISTENT = pooled direction repeated in >=4 of 5 seasons, each with
    n>=25 decided bets. Anything else is treated as noise.
  * Moneyline strategies graded by ROI per $1 staked, bootstrap 95% CI
    (fixed seed), t-test p vs 0.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
SEASONS = [2021, 2022, 2023, 2024, 2025]
BREAK_EVEN = 100 / 210  # 52.38% at -110
RNG = np.random.default_rng(20260715)


# ---------------------------------------------------------------- helpers
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
    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add_binary(self, family: str, name: str, df: pd.DataFrame,
                   res: pd.Series) -> None:
        """A W/L/P strategy graded against the closing number."""
        res = res.dropna()
        w, l, p = grade(res)
        n = w + l
        if n < 40:  # too thin to say anything
            return
        pct = w / n
        lo, hi = wilson_ci(w, n)
        pval = stats.binomtest(w, n, 0.5).pvalue
        roi = (w * (10 / 11) - l) / n  # per $1 staked at -110
        seasons = {}
        agree = 0
        eligible = 0
        pooled_dir = pct >= 0.5
        for yr in SEASONS:
            r = res[df.loc[res.index, "season"] == yr]
            sw, sl, sp = grade(r)
            sn = sw + sl
            seasons[yr] = f"{sw}-{sl}-{sp}"
            if sn >= 25:
                eligible += 1
                if (sw / sn >= 0.5) == pooled_dir:
                    agree += 1
        persistent = eligible >= 4 and agree >= 4
        self.rows.append(dict(
            family=family, strategy=name, n=n, record=f"{w}-{l}-{p}",
            win_pct=round(100 * pct, 2), ci_lo=round(100 * lo, 2),
            ci_hi=round(100 * hi, 2), p_value=pval,
            roi_at_110=round(100 * roi, 2),
            beats_breakeven=int(pct > BREAK_EVEN),
            ci_clears_breakeven=int(lo > BREAK_EVEN),
            seasons_agree=f"{agree}/{eligible}", persistent=int(persistent),
            **{f"s{yr}": seasons[yr] for yr in SEASONS},
        ))

    def add_roi(self, family: str, name: str, df: pd.DataFrame,
                returns: pd.Series) -> None:
        """A moneyline strategy graded by ROI per $1 staked."""
        returns = returns.dropna()
        n = len(returns)
        if n < 40:
            return
        roi = returns.mean()
        boots = RNG.choice(returns.values, size=(4000, n), replace=True).mean(axis=1)
        lo, hi = np.percentile(boots, [2.5, 97.5])
        tstat, pval = stats.ttest_1samp(returns.values, 0.0)
        w = int((returns > 0).sum())
        l = int((returns < 0).sum())
        seasons = {}
        agree = 0
        eligible = 0
        pooled_dir = roi >= 0
        for yr in SEASONS:
            r = returns[df.loc[returns.index, "season"] == yr]
            seasons[yr] = f"{round(100 * r.mean(), 1)}% ({len(r)})" if len(r) else "-"
            if len(r) >= 25:
                eligible += 1
                if (r.mean() >= 0) == pooled_dir:
                    agree += 1
        persistent = eligible >= 4 and agree >= 4
        self.rows.append(dict(
            family=family, strategy=name, n=n, record=f"{w}-{l}-0",
            win_pct=round(100 * w / max(w + l, 1), 2), ci_lo=round(100 * lo, 2),
            ci_hi=round(100 * hi, 2), p_value=pval,
            roi_at_110=round(100 * roi, 2),
            beats_breakeven=int(roi > 0), ci_clears_breakeven=int(lo > 0),
            seasons_agree=f"{agree}/{eligible}", persistent=int(persistent),
            **{f"s{yr}": seasons[yr] for yr in SEASONS},
        ))

    def finish_bh(self, q: float = 0.10) -> None:
        """Benjamini-Hochberg across every test collected."""
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


# ---------------------------------------------------------------- load
def load() -> pd.DataFrame:
    df = pd.read_csv(HERE / "market_bets_2021_2025.csv")
    df["abs_spread"] = df.spread_close.abs()
    df["dog_is_home"] = df.spread_close > 0
    df["has_fav"] = df.spread_close != 0

    hcm = df.home_cover_margin
    df["dog_res"] = wlp(df.has_fav, (hcm > 0) == df.dog_is_home, hcm == 0)
    df["home_res"] = df.home_covered
    df["over_res"] = df.over_result.map({"O": "W", "U": "L", "P": "P"})
    df["under_res"] = df.over_result.map({"U": "W", "O": "L", "P": "P"})

    # Moneyline returns per $1 staked
    fav_home = df.home_ml < df.away_ml
    df["ml_fav"] = np.where(fav_home, df.home_ml, df.away_ml)
    df["ml_dog"] = np.where(fav_home, df.away_ml, df.home_ml)
    fav_won = np.where(fav_home, df.home_won == 1, df.home_won == 0)
    dog_won = ~fav_won
    df["ret_fav"] = np.where(fav_won, df.ml_fav.map(
        lambda x: american_return(x) if pd.notna(x) else np.nan), -1.0)
    df["ret_dog"] = np.where(dog_won, df.ml_dog.map(
        lambda x: american_return(x) if pd.notna(x) else np.nan), -1.0)
    df.loc[df.home_ml.isna() | df.away_ml.isna() |
           (df.home_ml == df.away_ml), ["ret_fav", "ret_dog", "ml_fav", "ml_dog"]] = np.nan

    # Devigged home win probability (proportional method)
    dec_h = df.home_ml.map(lambda x: 1 + american_return(x) if pd.notna(x) else np.nan)
    dec_a = df.away_ml.map(lambda x: 1 + american_return(x) if pd.notna(x) else np.nan)
    qh, qa = 1 / dec_h, 1 / dec_a
    df["p_home_implied"] = qh / (qh + qa)

    # Line movement (within one provider). move<0 = market moved TOWARD home.
    move = pd.to_numeric(df.spread_move, errors="coerce")
    df["spread_move"] = move
    df["steam_side_home"] = pd.Series(np.nan, index=df.index, dtype=object)
    df.loc[move <= -1, "steam_side_home"] = True
    df.loc[move >= 1, "steam_side_home"] = False
    # Dog graded against the OPENING number (CLV check)
    open_cm = df.margin + df.spread_open
    df["dog_res_open"] = wlp(df.spread_open.notna() & (df.spread_open != 0),
                             (open_cm > 0) == (df.spread_open > 0),
                             open_cm == 0)
    return df


# ---------------------------------------------------------------- tests
def run_tests(df: pd.DataFrame) -> Report:
    rep = Report()
    non_neutral = df.neutral == 0

    # --- spreads: sides
    rep.add_binary("ATS home/away", "Home ATS — all (non-neutral)",
                   df, df.home_res[non_neutral])
    rep.add_binary("ATS fav/dog", "Dog ATS — all", df, df.dog_res)
    rep.add_binary("ATS fav/dog", "Home dog ATS", df,
                   df.dog_res[non_neutral & df.dog_is_home])
    rep.add_binary("ATS fav/dog", "Away dog ATS", df,
                   df.dog_res[non_neutral & ~df.dog_is_home & df.has_fav])
    for lo, hi, label in [(0.5, 3, "0.5-3"), (3.5, 7, "3.5-7"),
                          (7.5, 10, "7.5-10"), (10.5, 14, "10.5-14"),
                          (14.5, 21, "14.5-21"), (21.5, 99, "21.5+")]:
        m = (df.abs_spread >= lo) & (df.abs_spread <= hi)
        rep.add_binary("ATS by spread size", f"Dog ATS — spread {label}",
                       df, df.dog_res[m])

    # --- spreads: segments
    for seg, m in [("P4vP4", df.power_matchup == "P4vP4"),
                   ("G5vG5", df.power_matchup == "G5vG5"),
                   ("P4vG5", df.power_matchup == "P4vG5")]:
        rep.add_binary("ATS by matchup", f"Dog ATS — {seg}", df, df.dog_res[m])
    g5_side_res = wlp(df.power_matchup == "P4vG5",
                      (df.home_cover_margin > 0) == (df.home_power == 0),
                      df.home_cover_margin == 0)
    rep.add_binary("ATS by matchup", "G5 side ATS — P4vG5", df, g5_side_res)
    rep.add_binary("ATS conference", "Dog ATS — conference games",
                   df, df.dog_res[df.conference_game == 1])
    rep.add_binary("ATS conference", "Dog ATS — non-conference",
                   df, df.dog_res[df.conference_game == 0])

    ranked_h = df.home_rank.notna()
    ranked_a = df.away_rank.notna()
    one_ranked = ranked_h ^ ranked_a
    unranked_side = wlp(one_ranked,
                        (df.home_cover_margin > 0) == ~ranked_h,
                        df.home_cover_margin == 0)
    rep.add_binary("ATS rankings", "Unranked side ATS — vs AP-ranked",
                   df, unranked_side)
    rep.add_binary("ATS rankings", "Dog ATS — both ranked",
                   df, df.dog_res[ranked_h & ranked_a])

    for label, m in [("weeks 1-4", df.week <= 4),
                     ("weeks 5-9", (df.week >= 5) & (df.week <= 9)),
                     ("weeks 10+", (df.week >= 10) & (df.season_type == "regular")),
                     ("postseason", df.season_type == "postseason")]:
        rep.add_binary("ATS by phase", f"Dog ATS — {label}", df, df.dog_res[m])
        rep.add_binary("ATS by phase", f"Home ATS — {label}",
                       df, df.home_res[m & non_neutral])

    # --- rest
    rest_h = pd.to_numeric(df.home_rest_days, errors="coerce")
    rest_a = pd.to_numeric(df.away_rest_days, errors="coerce")
    bye_h, bye_a = rest_h >= 13, rest_a >= 13
    short_h, short_a = rest_h <= 5, rest_a <= 5
    bye_side = wlp(bye_h ^ bye_a, (df.home_cover_margin > 0) == bye_h,
                   df.home_cover_margin == 0)
    rep.add_binary("ATS rest", "Off-bye side ATS — vs non-bye", df, bye_side)
    short_side = wlp(short_h ^ short_a, (df.home_cover_margin > 0) == short_h,
                     df.home_cover_margin == 0)
    rep.add_binary("ATS rest", "Short-rest side ATS (<=5 days) — vs normal",
                   df, short_side)

    # --- rivalry
    rep.add_binary("ATS rivalry", "Dog ATS — rivalry games (curated)",
                   df, df.dog_res[df.rivalry == 1])
    rep.add_binary("Totals rivalry", "Under — rivalry games (curated)",
                   df, df.under_res[df.rivalry == 1])

    # --- line movement
    has_steam = df.steam_side_home.notna()
    steam_home = df.steam_side_home == True  # noqa: E712 (object dtype)
    steam_res = wlp(has_steam, (df.home_cover_margin > 0) == steam_home,
                    df.home_cover_margin == 0)
    rep.add_binary("Line movement", "Follow spread steam (move >=1) vs close",
                   df, steam_res)
    big_steam = df.spread_move.abs() >= 2.5
    rep.add_binary("Line movement", "Follow BIG spread steam (move >=2.5) vs close",
                   df, steam_res[big_steam])
    both = df.dog_res.notna() & df.dog_res_open.notna()
    rep.add_binary("Line movement", "Dog ATS vs OPENING line (CLV check)",
                   df, df.dog_res_open[both])
    rep.add_binary("Line movement", "Dog ATS vs CLOSING line (same games)",
                   df, df.dog_res[both])

    # --- totals
    rep.add_binary("Totals", "Over — all", df, df.over_res)
    rep.add_binary("Totals", "Under — all", df, df.under_res)
    for lo, hi, label in [(0, 44.5, "<45"), (45, 49.5, "45-49.5"),
                          (50, 54.5, "50-54.5"), (55, 59.5, "55-59.5"),
                          (60, 200, "60+")]:
        m = (df.total_close >= lo) & (df.total_close <= hi)
        rep.add_binary("Totals by size", f"Under — total {label}",
                       df, df.under_res[m])
    for seg, m in [("P4vP4", df.power_matchup == "P4vP4"),
                   ("G5vG5", df.power_matchup == "G5vG5")]:
        rep.add_binary("Totals by matchup", f"Under — {seg}", df, df.under_res[m])
    rep.add_binary("Totals by phase", "Under — weeks 1-4",
                   df, df.under_res[df.week <= 4])
    rep.add_binary("Totals by phase", "Under — weeks 10+ (regular)",
                   df, df.under_res[(df.week >= 10) & (df.season_type == "regular")])
    tmove = pd.to_numeric(df.total_move, errors="coerce")
    tsteam = pd.Series(np.nan, index=df.index, dtype=object)
    tsteam[tmove >= 1] = "O"
    tsteam[tmove <= -1] = "U"
    tsteam_res = wlp(tsteam.notna() & df.over_result.notna(),
                     df.over_result == tsteam, df.over_result == "P")
    rep.add_binary("Line movement", "Follow total steam (move >=1) vs close",
                   df, tsteam_res)

    # --- moneylines
    rep.add_roi("Moneyline", "All favorites ML", df, df.ret_fav)
    rep.add_roi("Moneyline", "All dogs ML", df, df.ret_dog)
    rep.add_roi("Moneyline", "Home dogs ML", df,
                df.ret_dog[non_neutral & (df.ml_dog == df.home_ml)])
    rep.add_roi("Moneyline", "Away dogs ML", df,
                df.ret_dog[non_neutral & (df.ml_dog == df.away_ml)])
    for lo, hi, label in [(100, 150, "+100 to +150"), (151, 250, "+151 to +250"),
                          (251, 400, "+251 to +400"), (401, 10000, "+401 and up")]:
        m = (df.ml_dog >= lo) & (df.ml_dog <= hi)
        rep.add_roi("Moneyline dogs by price", f"Dogs ML {label}",
                    df, df.ret_dog[m])
    for lo, hi, label in [(-150, -100, "-101 to -150"), (-250, -151, "-151 to -250"),
                          (-400, -251, "-251 to -400"), (-10000, -401, "-401 and heavier")]:
        m = (df.ml_fav >= lo) & (df.ml_fav <= hi)
        rep.add_roi("Moneyline favs by price", f"Favorites ML {label}",
                    df, df.ret_fav[m])

    rep.finish_bh(q=0.10)
    return rep


# ---------------------------------------------------------------- calibration
def calibration(df: pd.DataFrame) -> dict:
    out: dict = {}

    pred = -df.spread_close  # predicted home margin
    err = df.margin - pred
    fit = stats.linregress(pred, df.margin)
    out["spread"] = dict(
        n=int(len(df)), bias_pts=round(float(err.mean()), 3),
        bias_se=round(float(err.std() / np.sqrt(len(err))), 3),
        mae=round(float(err.abs().mean()), 2),
        rmse=round(float(np.sqrt((err ** 2).mean())), 2),
        slope=round(fit.slope, 4), intercept=round(fit.intercept, 3),
        r2=round(fit.rvalue ** 2, 4),
    )
    edges = [-60, -28, -21, -14, -10, -7, -3.5, 0, 3.5, 7, 10, 14, 21, 28, 60]
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (pred > lo) & (pred <= hi)
        if m.sum() < 20:
            continue
        sub = df[m]
        hw, hl, hp = grade(sub.home_covered)
        rows.append(dict(bucket=f"({lo},{hi}]", n=int(m.sum()),
                         mean_pred=round(float(pred[m].mean()), 2),
                         mean_actual=round(float(sub.margin.mean()), 2),
                         home_cover_pct=round(100 * hw / max(hw + hl, 1), 1)))
    out["spread_curve"] = rows

    tdf = df[df.total_close.notna()]
    terr = tdf.total_points - tdf.total_close
    tfit = stats.linregress(tdf.total_close, tdf.total_points)
    out["total"] = dict(
        n=int(len(tdf)), bias_pts=round(float(terr.mean()), 3),
        bias_se=round(float(terr.std() / np.sqrt(len(terr))), 3),
        mae=round(float(terr.abs().mean()), 2),
        rmse=round(float(np.sqrt((terr ** 2).mean())), 2),
        slope=round(tfit.slope, 4), intercept=round(tfit.intercept, 3),
        r2=round(tfit.rvalue ** 2, 4),
    )
    tedges = [30, 42, 46, 50, 54, 58, 62, 66, 90]
    rows = []
    for lo, hi in zip(tedges[:-1], tedges[1:]):
        m = (tdf.total_close > lo) & (tdf.total_close <= hi)
        if m.sum() < 20:
            continue
        sub = tdf[m]
        ow, ol, op = grade(sub.over_res)
        rows.append(dict(bucket=f"({lo},{hi}]", n=int(m.sum()),
                         mean_line=round(float(sub.total_close.mean()), 2),
                         mean_actual=round(float(sub.total_points.mean()), 2),
                         over_pct=round(100 * ow / max(ow + ol, 1), 1)))
    out["total_curve"] = rows

    mdf = df[df.p_home_implied.notna()]
    rows = []
    for lo in np.arange(0.05, 0.95, 0.10):
        m = (mdf.p_home_implied >= lo) & (mdf.p_home_implied < lo + 0.10)
        if m.sum() < 30:
            continue
        sub = mdf[m]
        rows.append(dict(bucket=f"{lo:.2f}-{lo + 0.10:.2f}", n=int(m.sum()),
                         implied=round(float(sub.p_home_implied.mean()), 3),
                         actual=round(float(sub.home_won.mean()), 3)))
    brier = float(((mdf.p_home_implied - mdf.home_won) ** 2).mean())
    out["ml_calibration"] = dict(n=int(len(mdf)), brier=round(brier, 4), curve=rows)

    # per-season spread/total bias for persistence framing
    out["bias_by_season"] = [
        dict(season=int(yr),
             spread_bias=round(float((df[df.season == yr].margin
                                      + df[df.season == yr].spread_close).mean()), 3),
             total_bias=round(float((df[(df.season == yr) & df.total_close.notna()].total_points
                                     - df[(df.season == yr) & df.total_close.notna()].total_close).mean()), 3),
             n=int((df.season == yr).sum()))
        for yr in SEASONS
    ]
    return out


def main() -> None:
    df = load()
    rep = run_tests(df)
    cal = calibration(df)

    res = pd.DataFrame(rep.rows)
    res = res.sort_values(["bh_significant", "persistent", "p_value"],
                          ascending=[False, False, True])
    res.to_csv(HERE / "slice_results.csv", index=False)

    with open(HERE / "results.json", "w", encoding="utf-8") as f:
        json.dump(dict(calibration=cal, n_tests=len(rep.rows)), f, indent=1)

    print(f"dataset: {len(df)} games | tests run: {len(rep.rows)}")
    print(f"spread bias {cal['spread']['bias_pts']:+.3f} pts "
          f"(MAE {cal['spread']['mae']}), "
          f"total bias {cal['total']['bias_pts']:+.3f} pts "
          f"(MAE {cal['total']['mae']}), ML Brier {cal['ml_calibration']['brier']}")
    print("\nBH-significant after FDR (q=0.10):")
    sig = res[res.bh_significant == 1]
    if sig.empty:
        print("  (none)")
    for _, r in sig.iterrows():
        print(f"  [{r.family}] {r.strategy}: {r.record} = {r.win_pct}% "
              f"(CI {r.ci_lo}-{r.ci_hi}), p={r.p_value}, "
              f"persistent={'YES' if r.persistent else 'no'}")
    print("\nPersistent (>=4/5 seasons same direction) but not BH-significant:")
    for _, r in res[(res.bh_significant == 0) & (res.persistent == 1)].iterrows():
        print(f"  [{r.family}] {r.strategy}: {r.record} = {r.win_pct}% "
              f"p={r.p_value} seasons={r.seasons_agree}")


if __name__ == "__main__":
    main()
