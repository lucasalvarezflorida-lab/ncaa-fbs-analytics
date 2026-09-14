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

## Amendment 2026-09-14 — the cap artifact (cap the residual, not the margin)

**What was wrong.** The pre-registered rule clipped the *observed margin* at
±28 before fitting. A team the prior expects to win by 44 that wins 52–0 is
scored as 28 − 44 = −16: the ridge reads a blowout as under-performance.
Through Week 2 of 2026, 26 of the 100 rated games hit the ±28 margin cap, and
the machine docked Notre Dame 2.5 for 52–0 over Rice, Georgia 2.2 for its
Week 2 blowout, Ohio State for 56–3 over Ball State (expected +48.5 → capped
residual −20.5), Texas for 52–7 over Texas State. The mirror image pays
cupcakes for losing big. The penalty depends on the schedule, not the team:
an elite team that plays a cupcake loses rating; one that plays a peer does
not.

**The fix.** `inseason_ratings.ridge_update(cap_mode="residual")` clips the
*residual* (margin minus the prior expectation, `y − (Xp + h)`) at ±28
instead. One game still carries at most 28 points of evidence — the
robustness the cap was for — but beating the expectation is never a
penalty. Under the residual cap only 6 of the same 100 games touch the cap.

**2026 effect (100 rated games, Sun 9/13 solve).** Top of the table under
the fix: Ohio State 30.0, Texas 30.0, Notre Dame 28.8, Georgia 27.3, Miami
25.4, Indiana 25.2, Alabama 24.8, Texas A&M 24.6, LSU 24.4, Oklahoma 18.3.
Biggest gains: South Carolina +5.8, Texas +5.0, Ohio State +5.0, Georgia
+4.8, Notre Dame +4.0. Biggest losses: Kent State −5.8, Rice −5.0, Ball
State −5.0, UTEP −4.8, Missouri State −4.6. Week 3 card lines move too:
South Carolina −4.9 → −7.1, LSU −5.2 → −6.6, Florida–Auburn flips from
Auburn +0.8 to Florida −1.6; Houston–Texas Tech and SMU–Louisville are
unchanged — which is why the flip waits until Ep4 has recorded.

**Backtest (same harness, `backtest_inseason_update.py`, configs m28 =
margin cap, r21/r28/r35 = residual cap, none).** λ = 3 column:

| config | tune MAE 2021–24 | tune RMSE | tune SU | validate MAE 2025 | validate RMSE | validate SU |
|---|---|---|---|---|---|---|
| margin ±28 (live) | 12.81 | 16.04 | 69.8% | 12.37 | 15.82 | 74.1% |
| residual ±28 (fix) | 12.88 | 16.13 | 69.7% | 12.43 | 15.82 | 74.4% |
| residual ±35 | 12.85 | 16.09 | 70.2% | 12.40 | 15.75 | 73.8% |
| no cap | 12.84 | 16.06 | 70.0% | 12.36 | 15.71 | 73.8% |

Accuracy is identical within noise (0.07 MAE across five seasons); the
cap style is a calibration question, not an accuracy one.

**Calibration (`cap_bias_check.py`).** Mean signed error from the favorite
side (actual − predicted; negative = the machine over-rates its favorites):

| bucket of predicted margin | margin ±28, 2021–24 | residual ±28, 2021–24 | margin ±28, 2025 | residual ±28, 2025 |
|---|---|---|---|---|
| 14–28 | −0.5 | −2.2 | +1.5 | −0.3 |
| 28+ | +0.6 | −4.4 | +3.6 | +1.4 |
| all games | −0.6 | −1.6 | +1.2 | +0.2 |

In the tune years big favorites won by *less* than the rating gap said, and
the margin cap happened to shrink them the right amount. In 2025 the sign
flipped — big favorites won by *more* — and the margin cap under-rated them
by 3.6 while the residual cap was the better-calibrated fit overall (+0.2).
The favorite bias is season-dependent, so no cap style calibrates it
reliably; a uniform gap-shrink factor tuned on 2021–24 (least squares k =
0.88) makes 2025 worse (+7.2 on 28+ favorites) and is rejected.

**Decision.** Adopt the residual cap: same accuracy, schedule-neutral, no
penalty for beating the expectation, and the better out-of-sample
calibration. It is date-gated (`CAP_SWITCH_DATE = 2026-09-20`, the Week 4
cycle) so the Ep4 / Week 3 card and its frozen grading lines stay on the
rule they were published under; Week 4 onward is graded on the residual cap.
`ratings_current_2026.json` records `cap_mode` so every receipt says which
rule produced it. Residual RMSE is within 0.1 of the margin cap (tune 16.13 vs 16.04,
validate 15.82 vs 15.82), so the curve keeps running at sd 15.9. Caveat carried forward: the favorite-margin bias flips sign between
seasons and is the next thing to study in the 2026 post-mortem.

## Amendment 2026-09-14 (b) — the efficiency layer (deserved margins)

**Idea.** Score margins carry turnover luck, special-teams scores and
garbage time; per-play efficiency carries less of it. CFBD's
`/stats/game/advanced` gives each team, each game, its total PPA (predicted
points added summed over its plays), success rate and explosiveness. From
the home side, `net_tppa` = home offense total PPA − away offense total PPA
and `net_sr` = the success-rate difference. The **deserved margin** is a
linear model of the two, fit once on 2021–24 rated FBS games (2,890 games)
and frozen in `efficiency_model.json`:

    deserved = 0.98 + 0.887 · net_tppa + 20.8 · net_sr     R² 0.815, rmse 8.75
    2025 out of sample: R² 0.806, rmse 9.00

The update can then fit `y = EFF_W · actual margin + (1 − EFF_W) · deserved
margin` per game (`efficiency.py`, `inseason_ratings.machine_ratings(eff_w=)`),
with games missing a box score falling back to the actual margin. Coverage is
99–100% of rated games every season.

**Backtest (`backtest_efficiency.py`, same harness, λ = 3, residual cap ±28,
weeks 2–15, scored on the actual margin).**

| config | tune MAE 2021–24 | tune SU | validate MAE 2025 | validate SU | validate ATS |
|---|---|---|---|---|---|
| margin cap, actual margin (live) | 12.81 | 69.8% | 12.37 | 74.1% | 51.4% |
| residual cap, actual margin (Week 4 rule) | 12.88 | 69.7% | 12.43 | 74.4% | 50.1% |
| residual cap, 75% actual / 25% deserved | 12.82 | 69.9% | 12.44 | 73.3% | 50.8% |
| residual cap, 50 / 50 | 12.80 | 69.7% | 12.48 | 72.5% | 50.1% |
| residual cap, 25 / 75 | 12.80 | 70.0% | 12.55 | 72.0% | 49.8% |
| residual cap, deserved only | 12.84 | 69.9% | 12.64 | 71.7% | 49.1% |

Re-tuning λ with the blend (1.5–4) changes nothing: the best out-of-sample
number is still the actual margin (12.37–12.38 at λ 1.5–2 vs 12.38–12.42
blended). By week group in 2025 the blend is worse in every block (weeks 2–5:
11.95 actual vs 12.01 at 50/50; weeks 11–15: 12.18 vs 12.34).

**Why it does not help.** Within a game, efficiency and margin are the same
information (R² 0.8, slope ≈ 1); the part of the margin that efficiency
strips out — turnovers, special teams, finishing drives — is noise for the
*next* game only if it is unrepeatable, and the prior + λ = 3 already shrink
each game's evidence enough that de-noising it further buys nothing. The
model has no shortage of per-game signal; it has a shortage of information
about *who is playing* (injuries, quarterback changes), which no box score
carries.

**Decision.** `EFF_W = 1.0` — the rating keeps fitting actual margins. The
layer stays wired (`--eff-w 0.5` re-runs the solve with it) and the deserved
margins ARE used, as information rather than as the rating:
- **Receipts:** every graded game shows the deserved margin next to the
  final, so a right read on a wrong result is visible. Week 2: the machine
  was off 40.5 points against the finals and 23.5 against the deserved
  margins (Texas deserved +5.6 and won by 1; A&M deserved +15.1 and won by
  28; BYU deserved +16.4 and won by 11; Alabama deserved +22.4 and won by 28;
  Michigan deserved +0.8 and won by 7).
- **Luck column:** season-to-date actual minus deserved margin per rated
  game, for the Top 25 notes (Texas +12.5, Texas Tech +14.1, Oregon −7.5
  through Week 2).
Caveat carried forward: re-test the blend at the post-mortem with a full
2026 season and the live preseason prior; if it stays neutral, it stays off.
