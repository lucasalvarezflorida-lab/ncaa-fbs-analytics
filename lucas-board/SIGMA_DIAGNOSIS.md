# σ-13.5 diagnosis — lucas_board_sim (2026-08-18)

**Diagnosis only. Nothing in this folder has been changed or re-run; the
frozen artifacts (`lucas_board_2026.json`, `lucas_board_sim_2026.csv`) are
untouched.** Context: on 2026-08-18 the workbook Season Sim, sim decks, and
episode deck moved from `NormalDist(0, 13.5)` to the empirical margin curve
(`margin_prob_curve.json`, residual sd 17.94, fit 2021-25). This note is the
handoff for deciding what, if anything, to do about the board sim.

## Finding 1 — the frozen deltas are inflated ~30%, not just the levels

`lucas_board_sim.py` runs all three priors (ESPN / tier-swap / rank-swap)
through Normal(0, 13.5). Because every prior uses the same conversion, the
*sign and ordering* of the deltas (the artifact's headline: who gains/loses
wins under Lucas's boards) are preserved. Their *magnitude* is not: the
win-prob slope near pick'em is 0.0295/pt under Normal(13.5) vs 0.0228/pt
under the empirical curve — a 1.30x steepness ratio. A +3 rating-point board
disagreement moves a close game +8.8pp under the old conversion vs +6.7pp
under the curve. The frozen "teams moving >= +/-1 win" counts and per-team
deltas are therefore overstated by roughly 25-35% in close-game-heavy
slates (less in blowout regimes, where both conversions flatten).

## Finding 2 — the frozen CSV is no longer reproducible from the code

`lucas_board_sim.py` imports `UNRATED_MARGIN` from `build_conference_book`,
which changed 24.0 → 29.0 on 2026-08-18 (recalibrated to the actual 94.4%
FBS-over-FCS rate). A re-run today would therefore match **neither** the
frozen CSV (it would use +29, the CSV was built with +24) **nor** the new
methodology (it still uses σ 13.5). The docstring's "unrated +24" is stale
too. If reproducibility of the frozen artifact matters, the constant needs
pinning locally (`UNRATED_MARGIN = 24.0`) with a freeze note.

## Finding 3 — what is NOT affected

- **LUCAS_CALL paper-bet grading** (Watch List): pure ATS vs first-seen
  lines. No σ anywhere in that path. The betting ledger is clean.
- **The board itself** (`lucas_board_2026.json`): tier/rank assertions,
  frozen 7/25. No probability math involved.
- **Relative story**: which teams the boards like/fade vs ESPN survives;
  only the win-count magnitudes shrink.

## Finding 4 — narrative consistency

The CSV's `espn_wins` column no longer matches the live workbook Season Sim
tab (e.g. Notre Dame 11.1 in the frozen CSV vs 10.5 in the workbook). If
both get quoted on air, the discrepancy needs a one-line explanation.

## Options (decision for the dedicated session)

1. **Pin + annotate (minimum).** Hardcode `UNRATED_MARGIN = 24.0` in
   `lucas_board_sim.py` with a freeze comment so the frozen CSV stays
   reproducible; add a README line noting deltas are ~30% inflated under
   the retired conversion, equally across priors.
2. **Pre-kickoff sensitivity companion (recommended, only before Aug 29).**
   Re-run under the empirical curve to a NEW file
   (`lucas_board_sim_2026_curve.csv`), clearly labeled a methodology
   sensitivity check. The original stays the pre-registered headline; the
   companion shows the conclusions survive a better conversion. Amending
   before any 2026 data exists is defensible; after first kickoff it is not.
3. **Do nothing.** Defensible too — the artifact is internally consistent
   and its comparative claims hold. Costs finding 2 (reproducibility) and
   finding 4 (on-air consistency).

Option 2 requires deciding before the Aug 29 opener; options 1 and 3 have
no deadline.
