# Pre-Registered NFL Watch List — 2026 Season

**Registered 2026-07-21, before any 2026 NFL line existed.** The git commit
containing this file is the timestamp. Nothing here may be added, dropped,
re-defined, or re-thresholded after Week 1 kicks off — that's the entire point.
This is the NFL counterpart of the CFB Watch List tab in
`NCAA_FBS_Teams.xlsm` (paper bets, first-seen principle, graduation bar), with
its priors drawn from [MARKET_POSTMORTEM_PHASE2.md](MARKET_POSTMORTEM_PHASE2.md)
/ `nfl_slice_results.csv`.

**Status: paper only.** None of these cleared Benjamini–Hochberg on 2021–25
data (the NFL battery went 0-for-42). They are the four persistent,
top-of-battery patterns worth *tracking*, not betting. The 2021–25 numbers
below are priors, not evidence of an edge.

## The four rules

Definitions are copied verbatim from `analyze_nfl.py` so 2026 grading is the
same measurement as the 2021–25 backtest. Spread convention is
home-perspective (negative = home favored), same as the rest of the repo.

| id | rule | exact eligibility | 2021–25 prior |
|---|---|---|---|
| `PRIME_UNDER` | Under in primetime | weekday is Monday or Thursday, or Sunday with kickoff ≥ 20:00 ET (nflverse `gametime`); playoffs included | 162-129-4, 55.7%, p=.060, +6.3% ROI, 5/5 seasons |
| `DOG_7_95` | Dog ATS getting 7–9.5 | closing spread magnitude in [7, 9.5]; all game types | 123-97-2, 55.9%, p=.092, +6.7% ROI, 4/5 seasons |
| `EARLY_UNDER` | Under in weeks 1–4 | regular season, week ≤ 4 | 175-144-1, 54.9%, p=.093, +4.7% ROI, 5/5 seasons |
| `MID_TOTAL_UNDER` | Under on totals 41.5–44.5 | closing total in [41.5, 44.5]; all game types | 253-214-4, 54.2%, p=.079, +3.4% ROI, 4/5 seasons |

A game can hit multiple rules (a Thursday game with a 43.5 total in week 3
logs three paper bets), same as the CFB ledger.

## Pre-registered exclusions

Declared now so they can't sneak in later as "we always meant to track that":

* **Wind 15+ mph unders** (57-36-2, 61.3%, +17% ROI). 93 games and only one
  eligible season under the persistence rule. The phase-2 report called it an
  anecdote with a pulse; an anecdote is not a rule. If it's ever promoted, it
  starts its own pre-registration from that date with zero accumulated bets.
* **Under — totals 48–50.5** (53.9%, p=.298) and everything else in
  `nfl_slice_results.csv`: weaker on every column than the four above.
* **No new rules mid-season, no re-bucketing** (e.g. widening 7–9.5 to 7–10
  because 10 "feels the same") — that's how backtests curdle into curve fits.

## Grading

* **Line source, declared up front:** the system has no live NFL line feed, so
  all 2026 grading uses **nflverse closing lines**, applied uniformly all
  season. This is the conservative choice — the close is the sharpest number
  in all three sports we tested, so clearing break-even against the close is
  *stronger* evidence than clearing it against an early number. If a live
  pre-kickoff feed ever joins, first-seen grading (the CFB `watchlist_log`
  standard) may begin only at a season boundary, declared in the log —
  never retroactively, never mixed within a season.
* Pushes excluded from win%; -110 both ways (nflverse's actual juice averages
  a shade under -110, so real ROI runs ~0.3% better than quoted — same note
  as the phase-2 report).
* Results are results: no dropping a rule mid-season because it's 4-12, no
  "the backup QB started so it doesn't count."

## Graduation

Same bar as the CFB Watch List: a rule earns real consideration only when it
clears **52.38% on 100+ decided bets accumulated from Week 1 of 2026 onward**.
Expected 2026 volumes (from 2021–25 averages): `PRIME_UNDER` ~58,
`DOG_7_95` ~44, `EARLY_UNDER` ~64, `MID_TOTAL_UNDER` ~93. Only
`MID_TOTAL_UNDER` can plausibly reach 100 in one season — **most rules cannot
graduate before the 2027 season, by design.** One NFL season of a 55% pattern
is ~30 games of signal; patience is the mechanism that separates persistence
from luck. At each season's end: report record, win%, and Wilson 95% CI per
rule; no interim graduations.

## Falsification

These double as falsifiable claims about the phase-2 conclusion. The report
says the NFL board prices everything; if all four rules land within noise of
50% (as pre-registered, graded, untouched), that conclusion holds and this
file becomes the receipt. If one clears the bar on 100+ bets, the
liquidity-gradient story has a documented, non-cherry-picked exception —
which would be the more interesting podcast episode anyway.
