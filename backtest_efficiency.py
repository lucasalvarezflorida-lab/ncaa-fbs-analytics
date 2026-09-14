"""Backtest the efficiency layer (efficiency.py) inside the in-season update.

Same harness as backtest_inseason_update.py: prior = prior-year final FPI,
week-w games predicted from ratings fit on weeks < w, scored on the ACTUAL
margin (MAE / RMSE / straight-up) and, where a closing spread exists, vs the
market. What changes is the y the ridge fits per game:

    y = w * actual margin + (1 - w) * deserved margin

with the deserved-margin model fit on the TUNE seasons only (2021-24) and
frozen to efficiency_model.json; 2025 is the out-of-sample check. The cap
is the residual cap (Week 4 rule); the margin-cap live machine (w = 1) is
the baseline row.

    python backtest_efficiency.py            # cached data only
Writes fpi-decomposition/output/efficiency_backtest_weekly.csv and
efficiency_model.json (tune-season fit).
"""

import numpy as np
import pandas as pd

from backtest_inseason_update import (EVAL_WEEKS, HFA, MARKET_CSV, OUT, SEASONS,
                                      TUNE, VALIDATE, load_games, load_prior, predict)
from efficiency import (FEATURES, blend, deserved, fit_model, game_efficiency,
                        save_model)
from inseason_ratings import ridge_update

LAM = 3
CAP = 28
WEIGHTS = [1.0, 0.75, 0.5, 0.25, 0.0]
CONFIGS = [("margin", 1.0)] + [("residual", w) for w in WEIGHTS]


def attach_efficiency(games: pd.DataFrame, season: int) -> pd.DataFrame:
    eff = game_efficiency(season)
    feats = [eff.get(int(i)) if pd.notna(i) else None for i in games.id]
    games = games.copy()
    games["feats"] = feats
    games["has_eff"] = [f is not None for f in feats]
    return games


def fit_blended(games: pd.DataFrame, prior, teams, lam, cap, mode, w, model):
    sub = {t: prior[t] for t in teams}
    recs = []
    for r in games.itertuples(index=False):
        recs.append(dict(home=r.home, away=r.away, neutral=r.neutral,
                         margin=blend(r.margin, r.feats, model, w)))
    return ridge_update(sub, recs, lam=lam, cap=cap, hfa=HFA, cap_mode=mode)


def main():
    OUT.mkdir(exist_ok=True)
    market = pd.read_csv(MARKET_CSV, usecols=["game_id", "spread_close"]).dropna()
    market_pred = dict(zip(market.game_id.astype(int), -market.spread_close.astype(float)))

    data = {}
    for season in SEASONS:
        prior = load_prior(season - 1)
        games = attach_efficiency(load_games(season, prior), season)
        data[season] = (prior, games)
        print(f"{season}: {len(games)} rated games, {games.has_eff.sum()} with efficiency "
              f"({games.has_eff.mean():.0%})")

    # deserved-margin model on the TUNE seasons only
    tune_rows = pd.concat([data[s][1] for s in TUNE])
    tune_rows = tune_rows[tune_rows.has_eff]
    model = fit_model(tune_rows.margin.to_numpy(), list(tune_rows.feats))
    save_model(model, f"fit on {TUNE} rated FBS games with both advanced box scores; "
                      "deserved = intercept + sum(coef * net feature), home perspective")
    print(f"\ndeserved-margin model ({FEATURES}): " +
          ", ".join(f"{k}={model[k]:.3f}" for k in ["intercept"] + FEATURES) +
          f"  R2 {model['r2']:.3f}  rmse {model['rmse']:.2f}  n {model['n']}")
    v = data[VALIDATE[0]][1]
    v = v[v.has_eff]
    pred_v = np.array([deserved(f, model) for f in v.feats])
    r2v = 1 - np.sum((v.margin - pred_v) ** 2) / np.sum((v.margin - v.margin.mean()) ** 2)
    print(f"2025 out-of-sample: R2 {r2v:.3f}  rmse {np.sqrt(np.mean((v.margin - pred_v) ** 2)):.2f}")

    rows = []
    for season in SEASONS:
        prior, games = data[season]
        teams = sorted(set(games.home) | set(games.away))
        for mode, w in CONFIGS:
            for wk in EVAL_WEEKS:
                test = games[games.week == wk]
                if test.empty:
                    continue
                r = fit_blended(games[games.week < wk], prior, teams, LAM, CAP, mode, w, model)
                pred = predict(test, r)
                actual = test.margin.to_numpy()
                err = actual - pred
                mk = np.array([market_pred.get(int(i), np.nan) if pd.notna(i) else np.nan
                               for i in test.id])
                has = ~np.isnan(mk)
                diff = pred[has] - mk[has]
                live = np.abs(diff) >= 0.5
                m_err = actual[has] - mk[has]
                wins = np.sign(diff[live]) == np.sign(m_err[live])
                pushes = m_err[live] == 0
                rows.append(dict(season=season, cfg=f"{mode[0]}{CAP} w{w:g}", mode=mode, w=w,
                                 week=wk, n=len(test), mae=np.mean(np.abs(err)),
                                 rmse=np.sqrt(np.mean(err ** 2)),
                                 su=np.mean(np.sign(pred) == np.sign(actual)),
                                 n_mkt=int(has.sum()),
                                 mae_mkt=np.mean(np.abs(m_err)) if has.any() else np.nan,
                                 ats_n=int(live.sum() - pushes.sum()),
                                 ats_w=int((wins & ~pushes).sum())))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "efficiency_backtest_weekly.csv", index=False)

    def summarize(seasons, label):
        sub = df[df.season.isin(seasons)]
        agg = (sub.groupby("cfg")
                  .apply(lambda g: pd.Series(dict(
                      mae=np.average(g.mae, weights=g.n),
                      rmse=np.sqrt(np.average(g.rmse ** 2, weights=g.n)),
                      su=np.average(g.su, weights=g.n),
                      mae_mkt=np.average(g.mae_mkt, weights=g.n_mkt),
                      ats=g.ats_w.sum() / max(g.ats_n.sum(), 1),
                      ats_n=g.ats_n.sum())), include_groups=False)
                  .reset_index())
        print(f"\n=== {label}: seasons {seasons}, weeks {EVAL_WEEKS.start}-{EVAL_WEEKS.stop - 1}, "
              f"lam={LAM}, cap={CAP} ===")
        print(f"{'cfg':12} {'MAE':>6} {'RMSE':>6} {'SU%':>6} {'mkt MAE':>8} {'ATS':>6} {'n':>5}")
        for _, r in agg.iterrows():
            print(f"{r.cfg:12} {r.mae:6.2f} {r.rmse:6.2f} {r.su*100:5.1f}% {r.mae_mkt:8.2f} "
                  f"{r.ats*100:5.1f}% {int(r.ats_n):>5}")
        return agg

    summarize(TUNE, "TUNE")
    summarize(VALIDATE, "VALIDATE (out of sample)")
    print("\nper-season MAE by config:")
    piv = (df.groupby(["season", "cfg"]).apply(lambda g: np.average(g.mae, weights=g.n),
                                               include_groups=False)
             .unstack("cfg").round(2))
    print(piv.to_string())
    print(f"\nwrote {OUT / 'efficiency_backtest_weekly.csv'} and efficiency_model.json")


if __name__ == "__main__":
    main()
