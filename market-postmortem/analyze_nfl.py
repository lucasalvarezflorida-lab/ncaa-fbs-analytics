"""NFL market post-mortem, 2021-2025 closing lines (nflverse games data).

Reads ../../..(Fun Projects)/nfl_games.csv, writes:
  nfl_bets_2021_2025.csv   per-game dataset (Excel-ready)
  nfl_slice_results.csv    every strategy test with BH FDR + persistence
  nfl_results.json         calibration curves + headline stats

Conventions match the CFB run: spread stored home-perspective (negative =
home favored; nflverse's spread_line is sign-flipped on load), pushes
excluded, -110 break-even 52.38%. nflverse carries one line per game (the
close) — no open/steam analysis for NFL.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from pm_common import Report, line_calibration, ml_calibration, wlp, grade

HERE = Path(__file__).resolve().parent
SRC = Path(r"C:\Users\lucas\Fun Projects\nfl_games.csv")
SEASONS = [2021, 2022, 2023, 2024, 2025]


def load() -> pd.DataFrame:
    raw = pd.read_csv(SRC, low_memory=False)
    raw = raw[(raw.season >= SEASONS[0]) & (raw.season <= SEASONS[-1])
              & raw.result.notna() & raw.spread_line.notna()].copy()

    df = pd.DataFrame(dict(
        game_id=raw.game_id, season=raw.season.astype(int),
        game_type=raw.game_type, week=raw.week.astype(int),
        date=raw.gameday, weekday=raw.weekday, gametime=raw.gametime,
        home=raw.home_team, away=raw.away_team,
        neutral=(raw.location == "Neutral").astype(int),
        div_game=raw.div_game.astype(int),
        roof=raw.roof, temp=raw.temp, wind=raw.wind,
        home_rest=raw.home_rest, away_rest=raw.away_rest,
        spread_close=-raw.spread_line,      # home persp: negative = home fav
        total_close=raw.total_line,
        home_ml=raw.home_moneyline, away_ml=raw.away_moneyline,
        margin=raw.result, total_points=raw.total,
    ))
    df["playoff"] = (df.game_type != "REG").astype(int)
    df["home_cover_margin"] = df.margin + df.spread_close
    df["home_covered"] = np.where(df.home_cover_margin == 0, "P",
                          np.where(df.home_cover_margin > 0, "W", "L"))
    df["over_margin"] = df.total_points - df.total_close
    df["over_result"] = np.where(df.over_margin == 0, "P",
                         np.where(df.over_margin > 0, "O", "U"))
    df["home_won"] = (df.margin > 0).astype(int)

    hour = pd.to_numeric(df.gametime.str.slice(0, 2), errors="coerce")
    df["primetime"] = (df.weekday.isin(["Monday", "Thursday"])
                       | ((df.weekday == "Sunday") & (hour >= 20))).astype(int)

    df["abs_spread"] = df.spread_close.abs()
    df["dog_is_home"] = df.spread_close > 0
    df["has_fav"] = df.spread_close != 0
    hcm = df.home_cover_margin
    df["dog_res"] = wlp(df.has_fav, (hcm > 0) == df.dog_is_home, hcm == 0)
    df["home_res"] = df.home_covered
    df["over_res"] = pd.Series(df.over_result, index=df.index).map(
        {"O": "W", "U": "L", "P": "P"})
    df["under_res"] = pd.Series(df.over_result, index=df.index).map(
        {"U": "W", "O": "L", "P": "P"})

    from pm_common import american_return
    fav_home = df.home_ml < df.away_ml
    df["ml_fav"] = np.where(fav_home, df.home_ml, df.away_ml)
    df["ml_dog"] = np.where(fav_home, df.away_ml, df.home_ml)
    fav_won = np.where(fav_home, df.home_won == 1, df.home_won == 0)
    df["ret_fav"] = np.where(fav_won, df.ml_fav.map(
        lambda x: american_return(x) if pd.notna(x) else np.nan), -1.0)
    df["ret_dog"] = np.where(~fav_won, df.ml_dog.map(
        lambda x: american_return(x) if pd.notna(x) else np.nan), -1.0)
    df.loc[df.home_ml.isna() | df.away_ml.isna() | (df.home_ml == df.away_ml),
           ["ret_fav", "ret_dog", "ml_fav", "ml_dog"]] = np.nan
    return df


def run_tests(df: pd.DataFrame) -> Report:
    rep = Report(SEASONS, seed=20260715)
    nn = df.neutral == 0
    reg = df.playoff == 0

    rep.add_binary("ATS home/away", "Home ATS — all (non-neutral)",
                   df, df.home_res[nn])
    rep.add_binary("ATS fav/dog", "Dog ATS — all", df, df.dog_res)
    rep.add_binary("ATS fav/dog", "Home dog ATS", df,
                   df.dog_res[nn & df.dog_is_home])
    rep.add_binary("ATS fav/dog", "Away dog ATS", df,
                   df.dog_res[nn & ~df.dog_is_home & df.has_fav])
    for lo, hi, label in [(0.5, 3, "0.5-3"), (3.5, 6.5, "3.5-6.5"),
                          (7, 9.5, "7-9.5"), (10, 30, "10+")]:
        m = (df.abs_spread >= lo) & (df.abs_spread <= hi)
        rep.add_binary("ATS by spread size", f"Dog ATS — spread {label}",
                       df, df.dog_res[m])
    rep.add_binary("ATS division", "Dog ATS — division games",
                   df, df.dog_res[df.div_game == 1])
    rep.add_binary("ATS division", "Dog ATS — non-division",
                   df, df.dog_res[df.div_game == 0])

    bye_h, bye_a = df.home_rest >= 13, df.away_rest >= 13
    short_h, short_a = df.home_rest <= 5, df.away_rest <= 5
    hcm = df.home_cover_margin
    rep.add_binary("ATS rest", "Off-bye side ATS — vs non-bye",
                   df, wlp(bye_h ^ bye_a, (hcm > 0) == bye_h, hcm == 0))
    rep.add_binary("ATS rest", "Short-rest side ATS (<=5 days) — vs normal",
                   df, wlp(short_h ^ short_a, (hcm > 0) == short_h, hcm == 0))
    adv_h = df.home_rest - df.away_rest >= 3
    adv_a = df.away_rest - df.home_rest >= 3
    rep.add_binary("ATS rest", "Rest-advantage side ATS (3+ days)",
                   df, wlp(adv_h | adv_a, (hcm > 0) == adv_h, hcm == 0))

    for label, m in [("weeks 1-4", reg & (df.week <= 4)),
                     ("weeks 5-12", reg & (df.week >= 5) & (df.week <= 12)),
                     ("weeks 13+", reg & (df.week >= 13)),
                     ("playoffs", df.playoff == 1)]:
        rep.add_binary("ATS by phase", f"Dog ATS — {label}", df, df.dog_res[m])
    rep.add_binary("ATS by phase", "Home ATS — weeks 1-4",
                   df, df.home_res[nn & reg & (df.week <= 4)])
    rep.add_binary("ATS primetime", "Dog ATS — primetime (Thu/Mon/SNF)",
                   df, df.dog_res[df.primetime == 1])
    rep.add_binary("ATS primetime", "Home ATS — primetime",
                   df, df.home_res[nn & (df.primetime == 1)])

    rep.add_binary("Totals", "Over — all", df, df.over_res)
    rep.add_binary("Totals", "Under — all", df, df.under_res)
    for lo, hi, label in [(0, 41, "<=41"), (41.5, 44.5, "41.5-44.5"),
                          (45, 47.5, "45-47.5"), (48, 50.5, "48-50.5"),
                          (51, 80, "51+")]:
        m = (df.total_close >= lo) & (df.total_close <= hi)
        rep.add_binary("Totals by size", f"Under — total {label}",
                       df, df.under_res[m])
    dome = df.roof.isin(["dome", "closed"])
    rep.add_binary("Totals venue", "Under — dome/closed roof",
                   df, df.under_res[dome])
    rep.add_binary("Totals venue", "Under — outdoors", df,
                   df.under_res[df.roof == "outdoors"])
    windy = pd.to_numeric(df.wind, errors="coerce") >= 15
    rep.add_binary("Totals weather", "Under — wind 15+ mph",
                   df, df.under_res[windy])
    rep.add_binary("Totals by phase", "Under — weeks 1-4",
                   df, df.under_res[reg & (df.week <= 4)])
    rep.add_binary("Totals by phase", "Under — weeks 13+ (regular)",
                   df, df.under_res[reg & (df.week >= 13)])
    rep.add_binary("Totals primetime", "Under — primetime",
                   df, df.under_res[df.primetime == 1])

    rep.add_roi("Moneyline", "All favorites ML", df, df.ret_fav)
    rep.add_roi("Moneyline", "All dogs ML", df, df.ret_dog)
    rep.add_roi("Moneyline", "Home dogs ML", df,
                df.ret_dog[nn & (df.ml_dog == df.home_ml)])
    rep.add_roi("Moneyline", "Away dogs ML", df,
                df.ret_dog[nn & (df.ml_dog == df.away_ml)])
    for lo, hi, label in [(100, 150, "+100 to +150"), (151, 250, "+151 to +250"),
                          (251, 10000, "+251 and up")]:
        rep.add_roi("Moneyline dogs by price", f"Dogs ML {label}",
                    df, df.ret_dog[(df.ml_dog >= lo) & (df.ml_dog <= hi)])
    for lo, hi, label in [(-150, -100, "-101 to -150"),
                          (-250, -151, "-151 to -250"),
                          (-10000, -251, "-251 and heavier")]:
        rep.add_roi("Moneyline favs by price", f"Favorites ML {label}",
                    df, df.ret_fav[(df.ml_fav >= lo) & (df.ml_fav <= hi)])
    return rep


def main() -> None:
    df = load()
    df.to_csv(HERE / "nfl_bets_2021_2025.csv", index=False)

    rep = run_tests(df)
    res = rep.finish_bh(q=0.10)
    res.to_csv(HERE / "nfl_slice_results.csv", index=False)

    cal = {}
    cal["spread"] = line_calibration(
        -df.spread_close, df.margin,
        [-30, -14, -10, -7, -3.5, 0, 3.5, 7, 10, 14, 30],
        df.home_covered, "home_cover_pct")
    cal["total"] = line_calibration(
        df.total_close, df.total_points,
        [30, 39, 42, 45, 48, 51, 60],
        pd.Series(df.over_result, index=df.index).map(
            {"O": "W", "U": "L", "P": "P"}), "over_pct")
    cal["ml"], _ = ml_calibration(df.home_ml, df.away_ml, df.home_won)
    cal["bias_by_season"] = [
        dict(season=int(yr),
             spread_bias=round(float(df[df.season == yr].home_cover_margin.mean()), 3),
             total_bias=round(float(df[df.season == yr].over_margin.mean()), 3),
             n=int((df.season == yr).sum()))
        for yr in SEASONS]
    json.dump(dict(calibration=cal, n_tests=len(rep.rows)),
              open(HERE / "nfl_results.json", "w", encoding="utf-8"), indent=1)

    print(f"NFL dataset: {len(df)} games | tests: {len(rep.rows)}")
    s, t = cal["spread"], cal["total"]
    print(f"spread bias {s['bias_pts']:+.3f} (SE {s['bias_se']}), slope "
          f"{s['slope']} (SE {s['slope_se']}); total bias {t['bias_pts']:+.3f}, "
          f"slope {t['slope']} (SE {t['slope_se']}); Brier {cal['ml']['brier']}")
    print("\nBH-significant (q=0.10):")
    sig = res[res.bh_significant == 1]
    if sig.empty:
        print("  (none)")
    for _, r in sig.iterrows():
        print(f"  [{r.family}] {r.strategy}: {r.record} = {r.win_pct}% "
              f"p={r.p_value} persistent={'YES' if r.persistent else 'no'}")
    print("\nPersistent but not BH-significant:")
    for _, r in res[(res.bh_significant == 0) & (res.persistent == 1)].iterrows():
        print(f"  [{r.family}] {r.strategy}: {r.record} = {r.win_pct}% "
              f"p={r.p_value} seasons={r.seasons_agree}")


if __name__ == "__main__":
    main()
