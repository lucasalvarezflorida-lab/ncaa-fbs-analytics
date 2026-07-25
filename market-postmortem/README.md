# market-postmortem

Grades betting markets themselves (closing spreads, totals, moneylines vs
results) rather than any one strategy. Findings:
[MARKET_POSTMORTEM.md](MARKET_POSTMORTEM.md) (CFB 2021–2025) and
[MARKET_POSTMORTEM_PHASE2.md](MARKET_POSTMORTEM_PHASE2.md) (NFL 2021–2025,
NBA 2011–2021). The four persistent-but-unproven NFL patterns are
pre-registered for 2026 paper tracking in
[NFL_WATCHLIST_2026_PREREG.md](NFL_WATCHLIST_2026_PREREG.md) (committed
July 2026, before any 2026 line existed).

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

Identity/ranking batteries (July 2026, all negative — kept as receipts;
each prints its own battery size, BH verdict, and season splits):

```
python team_trends_nfl.py       # per-NFL-team over/ATS/one-score, 96 tests, 0 survive
python team_trends_cfb.py       # per-CFB-team (30+ games), 399 tests, 0 survive
python coach_trends_cfb.py      # per-coach pooled across schools (CFBD /coaches;
                                #   split team-seasons excluded), 299 tests, 0 survive
python preseason_rank_trends.py # preseason AP top 25 / prior-year FPI top 30 proxy /
                                #   model predicted top 25, 10 tests, 0 survive
```

2026 in-season tracking:

```
python nfl_watchlist.py   # paper-bet loop for the four pre-registered NFL rules
                          #   (NFL_WATCHLIST_2026_PREREG.md): downloads current
                          #   nflverse games.csv, logs provisional bets, grades
                          #   completed games vs CLOSING lines into
                          #   nfl_watchlist_log.json + a "Watch List 2026" tab
                          #   in NFL_Postmortem.xlsx. Rerun after
                          #   build_phase2_workbooks.py (which recreates the book).
                          #   Scheduled: Windows task "NFL Watchlist Weekly"
                          #   (../nfl_watchlist_weekly.bat, Tuesdays 8:00 AM from
                          #   2026-08-25, logs to nfl_watchlist_run.log).
```

The two .xlsx workbooks are browse-friendly versions of the same outputs:
Summary (live formulas over the Bets tab), Slice Results (BH/persistence
flags), Bets (filterable per-game data), Charts.

Conventions match the rest of the repo: home-perspective spreads (negative =
home favored; nflverse's sign is flipped on load), pushes excluded from win%,
52.38% break-even at -110, line movement always open→close within one book.
The NBA loader repairs 933 swapped spread/total pairs in the archive
(recovered totals validated; unrecoverable spread signs become NaN).
