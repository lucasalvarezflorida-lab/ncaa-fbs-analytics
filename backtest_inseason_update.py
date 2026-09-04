"""Backtest the in-season rating update ("our own FPI"), 2021-2025.

Model: each week, ratings r are the ridge / Bayesian-posterior solution
    minimize  sum_games (margin - (r_home - r_away + HFA))^2
            + lam * sum_teams (r_team - prior_team)^2
using every completed game so far that season. The prior is the prior-year
final FPI (the same stale-prior convention as fit_margin_curve.py and
backtest_upset_alert.py — the only prior CFBD's history lets us test
honestly; the live pipeline's preseason snapshot is strictly fresher).
lam = how many "games of evidence" the prior is worth: lam -> inf is the
frozen prior (today's machine), lam -> 0 is games-only.

Week w games are predicted with ratings fit on weeks < w. Scored on margin
MAE/RMSE, straight-up accuracy, and — on the subset with a closing spread in
market-postmortem/market_bets_2021_2025.csv — the same for the market, plus
model-vs-close ATS. Tuned on 2021-2024, validated out-of-sample on 2025.

Run:  python backtest_inseason_update.py        (cached data only)
Writes fpi-decomposition/output/inseason_backtest_weekly.csv (all configs)
and inseason_sigma_by_week.csv (chosen config, pooled residual sd by week).
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

HFA = 2.5
SEASONS = [2021, 2022, 2023, 2024, 2025]
TUNE, VALIDATE = [2021, 2022, 2023, 2024], [2025]
DATA = HERE / "fpi-decomposition" / "data"
OUT = HERE / "fpi-decomposition" / "output"
MARKET_CSV = HERE / "market-postmortem" / "market_bets_2021_2025.csv"
LAMBDAS = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, np.inf]
CAPS = [None, 28]            # margin cap applied to the FITTED games only
EVAL_WEEKS = range(2, 16)    # week 1 = prior only, identical for every lam


def _pick(g, *names):
    for n in names:
        if g.get(n) is not None:
            return g[n]
    return None


def load_prior(year):
    path = DATA / f"ratings_fpi_year-{year}.json"
    return {normalize_name(r["team"]): float(r["fpi"])
            for r in json.loads(path.read_text(encoding="utf-8"))
            if r.get("fpi") is not None}


def load_games(season, prior):
    """Completed regular-season games with both teams in the prior."""
    rows = []
    path = DATA / f"games_seasonType-regular_year-{season}.json"
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
        rows.append(dict(id=g.get("id"), week=int(_pick(g, "week") or 0), home=h, away=a,
                         neutral=bool(_pick(g, "neutralSite", "neutral_site")),
                         margin=float(hp - ap)))
    return pd.DataFrame(rows)


def fit_ratings(games, prior, teams, lam, cap):
    """Ridge posterior via the production implementation (single source of
    truth with inseason_ratings.ridge_update)."""
    from inseason_ratings import ridge_update
    sub = {t: prior[t] for t in teams}
    return ridge_update(sub, games.to_dict("records"), lam=lam, cap=cap, hfa=HFA)


def predict(games, ratings):
    hfa = np.where(games.neutral.to_numpy(), 0.0, HFA)
    return np.array([ratings[h] - ratings[a] for h, a in zip(games.home, games.away)]) + hfa


def run():
    market = pd.read_csv(MARKET_CSV, usecols=["game_id", "spread_close"]).dropna()
    market_pred = dict(zip(market.game_id.astype(int), -market.spread_close.astype(float)))
    rows = []
    for season in SEASONS:
        prior = load_prior(season - 1)
        games = load_games(season, prior)
        teams = sorted(set(games.home) | set(games.away))
        for cap in CAPS:
            for lam in LAMBDAS:
                for w in EVAL_WEEKS:
                    test = games[games.week == w]
                    if test.empty:
                        continue
                    ratings = fit_ratings(games[games.week < w], prior, teams, lam, cap)
                    pred = predict(test, ratings)
                    err = test.margin.to_numpy() - pred
                    mk = np.array([market_pred.get(int(i), np.nan) if pd.notna(i) else np.nan
                                   for i in test.id])
                    has = ~np.isnan(mk)
                    m_err = test.margin.to_numpy()[has] - mk[has]
                    # ATS vs close: side the model prefers relative to the market
                    diff = pred[has] - mk[has]
                    actual_vs_mkt = m_err
                    live = np.abs(diff) >= 0.5
                    wins = np.sign(diff[live]) == np.sign(actual_vs_mkt[live])
                    pushes = actual_vs_mkt[live] == 0
                    rows.append(dict(
                        season=season, cap=cap if cap else 0, lam=lam, week=w, n=len(test),
                        mae=np.mean(np.abs(err)), rmse=np.sqrt(np.mean(err ** 2)),
                        su=np.mean(np.sign(pred) == np.sign(test.margin.to_numpy())),
                        n_mkt=int(has.sum()),
                        mae_mkt=np.mean(np.abs(m_err)) if has.any() else np.nan,
                        mae_model_on_mkt=np.mean(np.abs(err[has])) if has.any() else np.nan,
                        ats_n=int(live.sum() - pushes.sum()),
                        ats_w=int((wins & ~pushes).sum()),
                    ))
    return pd.DataFrame(rows)


def summarize(df, seasons, label):
    sub = df[df.season.isin(seasons)]
    agg = (sub.groupby(["cap", "lam"])
              .apply(lambda g: pd.Series(dict(
                  mae=np.average(g.mae, weights=g.n),
                  rmse=np.sqrt(np.average(g.rmse ** 2, weights=g.n)),
                  su=np.average(g.su, weights=g.n),
                  mae_vs_mkt=np.average(g.mae_model_on_mkt, weights=g.n_mkt),
                  mae_mkt=np.average(g.mae_mkt, weights=g.n_mkt),
                  ats=g.ats_w.sum() / max(g.ats_n.sum(), 1),
                  ats_n=g.ats_n.sum())))
              .reset_index())
    print(f"\n=== {label}: seasons {seasons}, weeks {EVAL_WEEKS.start}-{EVAL_WEEKS.stop - 1} "
          f"(weighted by games) ===")
    print(f"{'cap':>4} {'lam':>5} {'MAE':>6} {'RMSE':>6} {'SU%':>6} | {'MAE(mkt games)':>15} "
          f"{'market MAE':>10} {'ATS vs close':>13} {'n':>6}")
    for _, r in agg.iterrows():
        lam = "froz" if not np.isfinite(r.lam) else f"{r.lam:g}"
        print(f"{int(r.cap):>4} {lam:>5} {r.mae:6.2f} {r.rmse:6.2f} {r.su*100:5.1f}% | "
              f"{r.mae_vs_mkt:15.2f} {r.mae_mkt:10.2f} {r.ats*100:12.1f}% {int(r.ats_n):>6}")
    return agg


def main():
    OUT.mkdir(exist_ok=True)
    df = run()
    df.to_csv(OUT / "inseason_backtest_weekly.csv", index=False)
    tune = summarize(df, TUNE, "TUNE")
    best = tune.loc[tune.mae.idxmin()]
    print(f"\nchosen on 2021-24 MAE: cap={int(best.cap)} lam={best.lam:g}")
    summarize(df, VALIDATE, "VALIDATE (out of sample)")

    # week-by-week for chosen vs frozen vs market, validation season
    print(f"\n=== 2025 week by week: chosen (cap={int(best.cap)}, lam={best.lam:g}) "
          "vs frozen prior vs closing market ===")
    print(f"{'wk':>3} {'n':>4} {'MAE chosen':>11} {'MAE frozen':>11} {'MAE market':>11} "
          f"{'sigma chosen':>13} {'ATS vs close':>13}")
    v = df[(df.season == 2025) & (df.cap == int(best.cap))]
    for w in EVAL_WEEKS:
        c = v[(v.lam == best.lam) & (v.week == w)]
        f = v[(~np.isfinite(v.lam)) & (v.week == w)]
        if c.empty:
            continue
        c, f = c.iloc[0], f.iloc[0]
        ats = f"{c.ats_w}/{c.ats_n}"
        print(f"{w:>3} {int(c.n):>4} {c.mae:11.2f} {f.mae:11.2f} {c.mae_mkt:11.2f} "
              f"{c.rmse:13.2f} {ats:>13}")

    # pooled residual sd by week for the chosen config (feeds the curve scaling)
    ch = df[(df.cap == int(best.cap)) & (df.lam == best.lam)]
    sig = (ch.groupby("week")
             .apply(lambda g: pd.Series(dict(n=g.n.sum(),
                                             sigma=np.sqrt(np.average(g.rmse ** 2, weights=g.n)),
                                             mae=np.average(g.mae, weights=g.n))))
             .reset_index())
    sig.to_csv(OUT / "inseason_sigma_by_week.csv", index=False)
    print("\npooled 2021-25 residual sd by week (chosen config):")
    print("  " + "  ".join(f"wk{int(r.week)}:{r.sigma:.1f}" for _, r in sig.iterrows()))
    print(f"\nwrote {OUT / 'inseason_backtest_weekly.csv'} and inseason_sigma_by_week.csv")


if __name__ == "__main__":
    main()
