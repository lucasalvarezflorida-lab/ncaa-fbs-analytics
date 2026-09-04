# In-season rating update — "our own FPI" (pre-registered 2026-09-04)

The machine's rating was the frozen ESPN 2026 preseason FPI snapshot all
season. From this commit it is the snapshot **updated with every completed
2026 game** — a Bayesian/ridge posterior anchored to the preseason prior:

    minimize  Σ_games (margin − (r_home − r_away + HFA))²
            + λ · Σ_teams (r_team − prior_team)²

λ is "how many games of evidence the prior is worth". λ → ∞ is the old
frozen machine; λ → 0 ignores the prior. Home field 2.5, 0 at neutral sites.
Games vs unrated (FCS) opponents are not used. Implementation:
`inseason_ratings.py`; weekly receipt: `ratings_current_2026.json`.

## Backtest (backtest_inseason_update.py)

Prior = prior-year **final** FPI (the only prior CFBD's history allows —
strictly staler than the live preseason snapshot, so λ is a floor, not a
ceiling). Week-w games predicted from ratings fit on weeks < w. Tuned on
2021–2024, validated out of sample on 2025. Market = closing spread from
`market-postmortem/market_bets_2021_2025.csv`.

Tune (2021–24, weeks 2–15, weighted by games):

| config | MAE | RMSE | SU% | market MAE | ATS vs close |
|---|---|---|---|---|---|
| frozen prior (today's machine) | 14.23 | 17.88 | 65.9% | 12.24 | 49.6% |
| λ=3, cap 28 (**chosen**) | 12.81 | 16.04 | 69.8% | 12.24 | 48.8% |
| λ=2, no cap | 12.88 | 16.13 | 70.4% | 12.24 | 47.6% |
| λ=8, cap 28 | 13.05 | 16.34 | 69.3% | 12.24 | 49.7% |

Validate (2025, never used for tuning):

| config | MAE | RMSE | SU% | market MAE | ATS vs close |
|---|---|---|---|---|---|
| frozen prior | 14.05 | 18.04 | 68.4% | 11.88 | 51.0% |
| λ=3, cap 28 | **12.37** | **15.82** | **74.1%** | 11.88 | 51.4% (617) |

2025 week by week (chosen vs frozen vs market MAE): the update beats the
frozen prior every week from week 3 on and the gap widens — wk 10: 14.35 vs
17.31 (market 12.81); wk 13: 12.76 vs 15.48 (12.35). It ties or edges the
closing market in weeks 2, 11 and 14.

Pooled 2021–25 residual sd by week for the chosen config: 15.2–16.5 from
week 2 on (vs 17.9 frozen) → the margin curve runs **rescaled to sd 15.9**
once any rated game has been played (`MarginCurve.rescaled`).

## Rules (frozen — no mid-season edits)

- λ = 3, margin cap ±28 (fitted games only), HFA 2.5, curve sd 15.9.
- Ratings recompute on every refresh from all completed rated games; the
  preseason snapshot is never modified. Preseason artifacts (Season Sim
  decks, boards, Ep1/Ep2 predictions) stay frozen for grading.
- Consumers: workbook (`_Teams` D/C = machine current; AQ..AV = preseason,
  Δ, games used, ESPN live), Upset Board, edge_report → card_data → deck,
  Season Sim.
- ESPN's live FPI is a **reference column only** ("the man uses ESPN FPI");
  the machine never reads it.
- Caveat to revisit in the 2026 post-mortem: the live prior is fresher than
  the backtest's, so λ=3 may over-react early; keep λ fixed this season and
  test the preseason-snapshot prior once a full season of it exists.
- Beating the closing market ATS is **not** claimed (48–51% in both sets);
  the gain is accuracy and calibration, not a betting edge.
