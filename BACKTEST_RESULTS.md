# Upset Alert Backtest — 2023-2025

Prior = previous season's final FPI (exactly what the live alert knows in July).
Model side graded ATS vs the recorded line. Break-even at -110: **52.38%**.

| slice | W-L-P | win% |
|---|---|---|
| ALL alerts | 558-564-25 | 49.7% |
|   2023 | 178-161-9 | 52.5% |
|   2024 | 178-211-9 | 45.8% |
|   2025 | 202-192-7 | 51.3% |
| RED only | 170-177-12 | 49.0% |
| YELLOW only | 388-387-13 | 50.1% |
| edge 6-10 | 249-259-9 | 49.0% |
| edge 10-15 | 181-178-11 | 50.4% |
| edge 15-+ | 101-115-2 | 46.8% |
| early season (wks 1-4) | 121-127-5 | 48.8% |
| late season (wks 10+) | 238-237-8 | 50.1% |

**Red-alert dogs outright:** 116-243 (32.3% — dogs at +3 or longer, so outright win% well below 50 can still be profitable at moneyline prices).

## Honest read

The prior is *stale by construction* (last season's final FPI applied to a new
roster year, all season long). If this shows edge, it's despite that handicap;
in-season the live system upgrades to current-year FPI as CFBD mirrors it.
Slippage, line-shopping, and closing-line movement are not modeled.

Per-alert detail: `backtest_alerts.csv` (1147 alerts).