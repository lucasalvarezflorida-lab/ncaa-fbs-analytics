# NCAA FBS Analytics System

A self-refreshing college football analytics system: an FPI decomposition model,
a one-button Excel scouting workbook covering all 138 FBS teams, an upset-alert
engine graded against the betting market, and a Monte Carlo season simulator.

## What's here

| Piece | What it does |
|---|---|
| [`fpi-decomposition/`](fpi-decomposition/) | The model: how much of ESPN's FPI can be rebuilt from public data? **Answer: ~70%** (R² 0.705 across 132 teams). Methodology, findings, and limitations in its [README](fpi-decomposition/README.md). |
| `NCAA_FBS_Teams.xlsm` | The workbook. One tab per conference with a team dropdown → unit ratings, FPI decomposition numbers, 2026 schedule with sportsbook lines and opponent FPI ranks, full roster. Plus an **Upset Board** and **Season Sim** tab, and a REFRESH button that rebuilds everything. |
| `refresh_all.py` | The pipeline behind the button: re-pulls 138 official-site rosters, CFBD portal/schedules/betting lines, re-fits the model, rebuilds the workbook, recalculates via Excel. |
| `build_conference_book.py` | Workbook builder: hidden data sheets, conference viewer tabs, upset flagging (first-seen-line ledger in `alerts_log.json` so alerts are graded honestly), 10,000-run season simulation. |
| `rosters/` | Roster acquisition from every school's official athletics site (four site platforms handled), with archive fallback and per-team coverage reporting. |
| [`METHODOLOGY.md`](METHODOLOGY.md) | The 0–10 unit-rating methodology behind the team ratings (SP+ rescaling, five sub-ratings, returning-production prior, QB modifiers). |
| `NCAA_FBS_Analytics_System.pptx` | Nine-slide summary deck of the whole system. |

## The upset alert

FPI is denominated in points, so `FPI gap + 2.5 home field` is a model-implied margin.
Compare it to the spread:

- 🔴 **Upset watch** — the model likes the underdog *outright* and the spread is 3+.
- 🟡 **Line disagreement** — same side as the market, 6+ points of daylight.

Every alert is logged with the line at alert time and graded against *that* line when
the game completes — a running ATS record the model can't retroactively flatter.

## Backtested — and honest about the result

The alert rules were replayed against 2023–2025 (1,147 alerts, prior-year FPI as the
model — exactly the information the live system has): **49.7% ATS, below the 52.38%
break-even**. Notably, the *biggest* disagreements with the market (15+ point edges)
performed worst (46.8%) — when a stale prior and the market disagree loudly, the market
is usually right, because it knows about roster and coaching changes the prior doesn't.
Full slicing in [`BACKTEST_RESULTS.md`](BACKTEST_RESULTS.md).

That's the point of the ledger: this system surfaces *where* a major public model and
the betting market disagree — a research shortlist and narrative engine, not a picks
service. Making it profitable would require features the prior lacks (coaching changes,
QB status, portal flows) — which is the roadmap.

## Honest limitations

Public proxies aren't ESPN's inputs; coefficients aren't causal (the features are
heavily collinear); SP+ and FPI share schedule-strength circularity; and CFBD mirrors
*final* FPI, so 2025 residuals partly measure in-season surprises. The pipeline
auto-snapshots 2026 preseason FPI the moment ESPN publishes it, which fixes the
vintage problem for the season ahead. Until then, treat July alerts as a homework
shortlist, not a bet slip.

## Running it

```
pip install -r fpi-decomposition/requirements.txt
# set CFBD_API_KEY in your environment (free key: https://collegefootballdata.com/key)
python refresh_all.py                 # full refresh (~3 min)
python refresh_all.py --import-only   # rebuild sheets from cached data
pytest fpi-decomposition/test_merge.py
```

Raw API responses cache locally (`fpi-decomposition/data/`, `rosters/data/` — both
gitignored); a weekly Windows scheduled task runs the refresh Tuesday mornings
in-season.
