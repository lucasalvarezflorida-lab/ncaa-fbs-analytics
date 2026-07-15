"""NBA market post-mortem, 2011-2021 seasons (local nba_archive.json).

That archive is what we have — 13,903 games with open+close spreads/totals
and closing moneylines, seasons 2011-12 through 2021-22 (playoffs included,
no playoff flag). Because opens exist, the NBA gets the steam/CLV treatment
CFB got. Totals rose ~30 points across the decade, so total-size slices use
WITHIN-SEASON quintiles, never absolute numbers.

Writes: nba_bets_2011_2021.csv, nba_slice_results.csv, nba_results.json
Conventions: spread home-perspective (negative = home favored, as shipped),
pushes excluded, -110 break-even 52.38%.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from pm_common import Report, american_return, line_calibration, \
    ml_calibration, wlp

HERE = Path(__file__).resolve().parent
SRC = Path(r"C:\Users\lucas\Fun Projects\nba_archive.json")
SEASONS = list(range(2011, 2022))

# franchise-consistent labels (archive mixes city/nickname in a few spots)
TEAM_FIX = {"Golden State": "Warriors", "LA Clippers": "Clippers",
            "Oklahoma City": "Thunder", "NewJersey": "Nets"}


def _spread_like(v) -> bool:
    return v is not None and abs(v) <= 30


def _total_like(v) -> bool:
    return v is not None and 60 <= abs(v) <= 300


def repair_pair(spread, total) -> tuple:
    """Fix the archive's swapped spread/total columns (933 close pairs).

    Magnitude disambiguates. Validated empirically (scratch nba_repair_test):
    recovered totals behave exactly like clean ones (corr .61 with actual),
    but the sign of a spread found in the total slot is uninformative
    (corr .01 with margins) — so swapped-row spreads become NaN, never
    guessed. Values that fit neither slot also become NaN.
    """
    if _spread_like(spread) and _total_like(total):
        return float(spread), float(abs(total))
    if _total_like(spread) and _spread_like(total):
        return np.nan, float(abs(spread))
    return (float(spread) if _spread_like(spread) else np.nan,
            float(abs(total)) if _total_like(total) else np.nan)


def load() -> pd.DataFrame:
    raw = json.load(open(SRC, encoding="utf-8"))
    rows = []
    dropped = 0
    for g in raw:
        home = TEAM_FIX.get(g.get("home_team"), g.get("home_team"))
        away = TEAM_FIX.get(g.get("away_team"), g.get("away_team"))
        try:
            hp, ap = int(g["home_final"]), int(g["away_final"])
        except (TypeError, ValueError, KeyError):
            dropped += 1
            continue
        if not isinstance(home, str) or not isinstance(away, str):
            dropped += 1
            continue
        sc, tc = repair_pair(g.get("home_close_spread"), g.get("close_over_under"))
        so, to = repair_pair(g.get("home_open_spread"), g.get("open_over_under"))
        if pd.isna(sc) and pd.isna(tc):
            dropped += 1
            continue
        rows.append(dict(
            season=int(g["season"]),
            date=pd.to_datetime(str(int(g["date"])), format="%Y%m%d"),
            home=home, away=away, home_pts=hp, away_pts=ap,
            spread_close=sc, spread_open=so, total_close=tc, total_open=to,
            home_ml=g.get("home_close_ml"), away_ml=g.get("away_close_ml"),
        ))
    n_no_spread = sum(1 for r in rows if pd.isna(r["spread_close"]))
    print(f"loaded {len(rows)} games ({dropped} dropped; {n_no_spread} with "
          "swapped/unusable close spread -> spread NaN, total recovered)")
    df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)

    # rest days per franchise (1 = back-to-back); first game of season -> NaN
    last: dict[tuple, pd.Timestamp] = {}
    rest_h, rest_a = [], []
    for r in df.itertuples():
        for team, bucket in ((r.home, rest_h), (r.away, rest_a)):
            key = (r.season, team)
            prev = last.get(key)
            bucket.append((r.date - prev).days if prev is not None else np.nan)
            last[key] = r.date
    df["home_rest"], df["away_rest"] = rest_h, rest_a

    df["margin"] = df.home_pts - df.away_pts
    df["total_points"] = df.home_pts + df.away_pts
    df["home_cover_margin"] = df.margin + df.spread_close
    df["over_margin"] = df.total_points - df.total_close
    df["over_result"] = np.where(df.total_close.isna(), None,
                         np.where(df.over_margin == 0, "P",
                         np.where(df.over_margin > 0, "O", "U")))
    df["home_won"] = (df.margin > 0).astype(int)

    df["abs_spread"] = df.spread_close.abs()
    df["dog_is_home"] = df.spread_close > 0
    df["has_fav"] = df.spread_close.notna() & (df.spread_close != 0)
    hcm = df.home_cover_margin
    df["dog_res"] = wlp(df.has_fav, (hcm > 0) == df.dog_is_home, hcm == 0)
    df["home_res"] = wlp(df.spread_close.notna(), hcm > 0, hcm == 0)
    df["home_covered"] = df.home_res
    df["over_res"] = pd.Series(df.over_result, index=df.index).map(
        {"O": "W", "U": "L", "P": "P"})
    df["under_res"] = pd.Series(df.over_result, index=df.index).map(
        {"U": "W", "O": "L", "P": "P"})

    # within-season total quintile (era-proof size buckets)
    df["total_q"] = df.groupby("season").total_close.transform(
        lambda s: pd.qcut(s, 5, labels=False, duplicates="drop"))

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

    # steam + CLV vs the open
    df["spread_move"] = df.spread_close - df.spread_open
    open_cm = df.margin + df.spread_open
    df["dog_res_open"] = wlp(df.spread_open.notna() & (df.spread_open != 0),
                             (open_cm > 0) == (df.spread_open > 0),
                             open_cm == 0)
    return df


def run_tests(df: pd.DataFrame) -> Report:
    rep = Report(SEASONS, seed=20260715, min_per_season=50)
    hcm = df.home_cover_margin

    rep.add_binary("ATS home/away", "Home ATS — all", df, df.home_res)
    rep.add_binary("ATS fav/dog", "Dog ATS — all", df, df.dog_res)
    rep.add_binary("ATS fav/dog", "Home dog ATS", df,
                   df.dog_res[df.dog_is_home])
    rep.add_binary("ATS fav/dog", "Away dog ATS", df,
                   df.dog_res[~df.dog_is_home & df.has_fav])
    for lo, hi, label in [(0.5, 3, "0.5-3"), (3.5, 6, "3.5-6"),
                          (6.5, 9, "6.5-9"), (9.5, 12, "9.5-12"),
                          (12.5, 30, "12.5+")]:
        m = (df.abs_spread >= lo) & (df.abs_spread <= hi)
        rep.add_binary("ATS by spread size", f"Dog ATS — spread {label}",
                       df, df.dog_res[m])

    sp_ok = df.spread_close.notna()
    b2b_h, b2b_a = df.home_rest == 1, df.away_rest == 1
    rep.add_binary("ATS rest", "Back-to-back side ATS — vs rested opponent",
                   df, wlp(sp_ok & (b2b_h ^ b2b_a), (hcm > 0) == b2b_h,
                           hcm == 0))
    rep.add_binary("ATS rest", "Fade the back-to-back road team ATS",
                   df, wlp(sp_ok & b2b_a & ~b2b_h, hcm > 0, hcm == 0))
    long_h = df.home_rest >= 3
    long_a = df.away_rest >= 3
    rep.add_binary("ATS rest", "3+ days rest side ATS — vs shorter",
                   df, wlp(sp_ok & (long_h ^ long_a), (hcm > 0) == long_h,
                           hcm == 0))

    month = df.date.dt.month
    early = month.isin([10, 11])
    late = month.isin([3, 4])
    rep.add_binary("ATS by phase", "Dog ATS — Oct-Nov", df, df.dog_res[early])
    rep.add_binary("ATS by phase", "Dog ATS — Mar-Apr", df, df.dog_res[late])
    rep.add_binary("ATS by phase", "Home ATS — Oct-Nov", df, df.home_res[early])

    rep.add_binary("Totals", "Over — all", df, df.over_res)
    rep.add_binary("Totals", "Under — all", df, df.under_res)
    qlab = {0: "Q1 lowest", 1: "Q2", 2: "Q3", 3: "Q4", 4: "Q5 highest"}
    for q, label in qlab.items():
        rep.add_binary("Totals by size (season quintile)",
                       f"Under — totals {label}",
                       df, df.under_res[df.total_q == q])
    either_b2b = b2b_h | b2b_a
    rep.add_binary("Totals rest", "Under — either team on back-to-back",
                   df, df.under_res[either_b2b])
    rep.add_binary("Totals by phase", "Under — Oct-Nov", df,
                   df.under_res[early])
    rep.add_binary("Totals by phase", "Under — Mar-Apr", df,
                   df.under_res[late])

    move = df.spread_move
    steam_home = pd.Series(np.nan, index=df.index, dtype=object)
    steam_home[move <= -1] = True
    steam_home[move >= 1] = False
    has_steam = steam_home.notna()
    steam_res = wlp(has_steam, (hcm > 0) == (steam_home == True),  # noqa: E712
                    hcm == 0)
    rep.add_binary("Line movement", "Follow spread steam (move >=1) vs close",
                   df, steam_res)
    rep.add_binary("Line movement", "Follow BIG spread steam (>=2) vs close",
                   df, steam_res[move.abs() >= 2])
    both = df.dog_res.notna() & df.dog_res_open.notna()
    rep.add_binary("Line movement", "Dog ATS vs OPENING line (CLV check)",
                   df, df.dog_res_open[both])
    rep.add_binary("Line movement", "Dog ATS vs CLOSING line (same games)",
                   df, df.dog_res[both])
    tmove = df.total_close - df.total_open
    tsteam = pd.Series(np.nan, index=df.index, dtype=object)
    tsteam[tmove >= 1] = "O"
    tsteam[tmove <= -1] = "U"
    over_result = pd.Series(df.over_result, index=df.index)
    rep.add_binary("Line movement", "Follow total steam (move >=1) vs close",
                   df, wlp(tsteam.notna() & over_result.notna(),
                           over_result == tsteam, over_result == "P"))

    rep.add_roi("Moneyline", "All favorites ML", df, df.ret_fav)
    rep.add_roi("Moneyline", "All dogs ML", df, df.ret_dog)
    rep.add_roi("Moneyline", "Home dogs ML", df,
                df.ret_dog[df.ml_dog == df.home_ml])
    rep.add_roi("Moneyline", "Away dogs ML", df,
                df.ret_dog[df.ml_dog == df.away_ml])
    for lo, hi, label in [(100, 150, "+100 to +150"), (151, 250, "+151 to +250"),
                          (251, 400, "+251 to +400"), (401, 10000, "+401 and up")]:
        rep.add_roi("Moneyline dogs by price", f"Dogs ML {label}",
                    df, df.ret_dog[(df.ml_dog >= lo) & (df.ml_dog <= hi)])
    for lo, hi, label in [(-150, -100, "-101 to -150"),
                          (-250, -151, "-151 to -250"),
                          (-400, -251, "-251 to -400"),
                          (-10000, -401, "-401 and heavier")]:
        rep.add_roi("Moneyline favs by price", f"Favorites ML {label}",
                    df, df.ret_fav[(df.ml_fav >= lo) & (df.ml_fav <= hi)])
    return rep


def main() -> None:
    df = load()
    df.to_csv(HERE / "nba_bets_2011_2021.csv", index=False)

    rep = run_tests(df)
    res = rep.finish_bh(q=0.10)
    res.to_csv(HERE / "nba_slice_results.csv", index=False)

    cal = {}
    sdf = df[df.spread_close.notna()]
    cal["spread"] = line_calibration(
        -sdf.spread_close, sdf.margin,
        [-25, -12, -9, -6, -3, 0, 3, 6, 9, 12, 25],
        sdf.home_covered, "home_cover_pct")
    tdf = df[df.total_close.notna()]
    cal["total"] = line_calibration(
        tdf.total_close, tdf.total_points,
        list(np.quantile(tdf.total_close, np.arange(0, 1.01, 0.125))),
        pd.Series(tdf.over_result, index=tdf.index).map(
            {"O": "W", "U": "L", "P": "P"}), "over_pct")
    cal["ml"], _ = ml_calibration(df.home_ml, df.away_ml, df.home_won)
    cal["bias_by_season"] = [
        dict(season=int(yr),
             spread_bias=round(float(df[df.season == yr].home_cover_margin.mean()), 3),
             total_bias=round(float(df[df.season == yr].over_margin.mean()), 3),
             n=int((df.season == yr).sum()))
        for yr in SEASONS]
    json.dump(dict(calibration=cal, n_tests=len(rep.rows)),
              open(HERE / "nba_results.json", "w", encoding="utf-8"), indent=1)

    print(f"NBA dataset: {len(df)} games | tests: {len(rep.rows)}")
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
