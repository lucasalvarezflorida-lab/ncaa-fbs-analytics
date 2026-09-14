"""Cap-artifact diagnostic: does clipping the MARGIN bias big favorites?

For 2021-25, lam=3, week-by-week fits (same harness as
backtest_inseason_update.py), bucket the test games by the model's predicted
|margin| and report the mean SIGNED error (actual - predicted, from the
favorite's side) under three caps: margin ±28 (pre-registered rule),
residual ±28 (the fix), none. A systematic negative number in the 21+
buckets means the model under-predicts its own big favorites — the
signature of docking elite teams for cupcake blowouts.

    python cap_bias_check.py
"""

import numpy as np
import pandas as pd

from backtest_inseason_update import (EVAL_WEEKS, SEASONS, fit_ratings,
                                      load_games, load_prior, predict)

LAM = 3
CONFIGS = [("margin", 28), ("residual", 28), ("margin", None)]
EDGES = [0, 7, 14, 21, 28, 99]


def main():
    rows = []
    for season in SEASONS:
        prior = load_prior(season - 1)
        games = load_games(season, prior)
        teams = sorted(set(games.home) | set(games.away))
        for mode, cap in CONFIGS:
            for w in EVAL_WEEKS:
                test = games[games.week == w]
                if test.empty:
                    continue
                r = fit_ratings(games[games.week < w], prior, teams, LAM, cap, mode)
                pred = predict(test, r)
                sign = np.where(pred >= 0, 1.0, -1.0)
                rows.append(pd.DataFrame(dict(
                    season=season, cfg=f"{mode}{'' if cap is None else int(cap)}",
                    pred_abs=np.abs(pred),
                    err_fav=(test.margin.to_numpy() - pred) * sign)))
    df = pd.concat(rows)
    df["bucket"] = pd.cut(df.pred_abs, EDGES, right=False,
                          labels=["0-7", "7-14", "14-21", "21-28", "28+"])
    out = (df.groupby(["bucket", "cfg"], observed=True).err_fav
             .agg(n="size", mean_err="mean").reset_index())
    print("mean signed error from the favorite's side (actual - predicted), "
          f"2021-25 pooled, lam={LAM}; negative = the model over-rates its favorites, "
          "positive = it under-rates them\n")
    piv = out.pivot(index="bucket", columns="cfg", values="mean_err").round(2)
    cnt = out.pivot(index="bucket", columns="cfg", values="n")
    print(pd.concat({"mean err": piv, "n": cnt}, axis=1).to_string())
    print("\nall games:")
    print(df.groupby("cfg").err_fav.agg(["mean", "std", "size"]).round(2).to_string())


if __name__ == "__main__":
    main()
