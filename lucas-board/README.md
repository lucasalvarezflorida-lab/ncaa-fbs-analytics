# lucas-board — the boards as a bet

Betting-side artifacts derived from the podcast's per-conference Big Boards.
The boards themselves (content) live in the repo-root prep files; this folder
is what happens when they're held to a market standard.

| file | what it is |
|---|---|
| `build_lucas_board.py` | Freezes the boards vs ESPN preseason FPI: within-conference ranks, tiers (derived from the boards' own numeric columns), and ±3-spot disagreement flags |
| `lucas_board_2026.json` | The frozen output: 136 teams, 20 LUCAS_CALL flags. **Frozen 2026-07-25 — no edits after Week 1** |
| `lucas_board_sim.py` | 10k-run season sim under three priors: ESPN FPI, tier-swap (headline), rank-swap (reference) |
| `lucas_board_sim_2026.csv` | Sim output: wins / bowl / 10-win probabilities per team under each prior |

The LUCAS_CALL paper rule in the workbook's Watch List tab reads
`lucas_board_2026.json` from here (see `build_conference_book.py`), paper-bets
every flagged team's games at first-seen lines, and grades all season.
2026 is the first sample — no backtest exists by construction.

Rerun order after a (pre-Week-1) board edit:
`build_lucas_board.py` → `lucas_board_sim.py` → workbook refresh.
