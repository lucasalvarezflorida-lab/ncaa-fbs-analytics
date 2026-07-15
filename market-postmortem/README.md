# market-postmortem

Grades the CFB betting market itself (closing spreads, totals, moneylines vs
results, 2021–2025) rather than any one strategy. Findings:
[MARKET_POSTMORTEM.md](MARKET_POSTMORTEM.md).

Pipeline (each step reads the previous step's output; CFBD key comes from the
`CFBD_API_KEY` env var via the shared `../fpi-decomposition/cfbd_client.py`
cache — never printed or committed):

```
python fetch_data.py       # warm the CFBD cache (lines/games/rankings)
python build_dataset.py    # -> market_bets_2021_2025.csv (per-bet, Excel-ready)
python analyze_market.py   # -> slice_results.csv + results.json (57 tests, BH FDR)
python make_charts.py      # -> charts/*.png (4 headline charts)
```

Conventions match the rest of the repo: home-perspective spreads, pushes
excluded from win%, 52.38% break-even at -110, provider preference
DraftKings → Bovada → ESPN Bet, line movement always open→close within one
book. Phase 2 candidates: NFL/NBA via the local CSV/JSON archives in
"Fun Projects".
