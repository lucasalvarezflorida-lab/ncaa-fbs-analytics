# market-postmortem

Grades betting markets themselves (closing spreads, totals, moneylines vs
results) rather than any one strategy. Findings:
[MARKET_POSTMORTEM.md](MARKET_POSTMORTEM.md) (CFB 2021–2025) and
[MARKET_POSTMORTEM_PHASE2.md](MARKET_POSTMORTEM_PHASE2.md) (NFL 2021–2025,
NBA 2011–2021).

CFB pipeline (each step reads the previous step's output; CFBD key comes from
the `CFBD_API_KEY` env var via the shared `../fpi-decomposition/cfbd_client.py`
cache — never printed or committed):

```
python fetch_data.py       # warm the CFBD cache (lines/games/rankings)
python build_dataset.py    # -> market_bets_2021_2025.csv (per-bet, Excel-ready)
python analyze_market.py   # -> slice_results.csv + results.json (57 tests, BH FDR)
python make_charts.py      # -> charts/*.png (4 headline charts)
```

Phase 2 (self-contained loaders over local files in "Fun Projects";
shared stats in `pm_common.py`):

```
python analyze_nfl.py            # nfl_games.csv    -> nfl_bets/slices/results
python analyze_nba.py            # nba_archive.json -> nba_bets/slices/results
python make_charts_phase2.py     # -> charts/nfl_*, nba_*, phase2_*
python build_phase2_workbooks.py # -> NFL_Postmortem.xlsx + NBA_Postmortem.xlsx
                                 #    (then recalc via Excel COM, never LibreOffice)
```

The two .xlsx workbooks are browse-friendly versions of the same outputs:
Summary (live formulas over the Bets tab), Slice Results (BH/persistence
flags), Bets (filterable per-game data), Charts.

Conventions match the rest of the repo: home-perspective spreads (negative =
home favored; nflverse's sign is flipped on load), pushes excluded from win%,
52.38% break-even at -110, line movement always open→close within one book.
The NBA loader repairs 933 swapped spread/total pairs in the archive
(recovered totals validated; unrecoverable spread signs become NaN).
