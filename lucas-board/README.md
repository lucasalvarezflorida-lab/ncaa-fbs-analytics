# lucas-board — the boards as a bet

Betting-side artifacts derived from the podcast's per-conference Big Boards.
The boards themselves (content) live in the `podcast-prep/` docs; this folder
is what happens when they're held to a market standard.

| file | what it is |
|---|---|
| `build_lucas_board.py` | Freezes the boards vs ESPN preseason FPI: within-conference ranks, tiers (derived from the boards' own numeric columns), and ±3-spot disagreement flags |
| `lucas_board_2026.json` | The frozen output: 136 teams, 20 LUCAS_CALL flags. **Frozen 2026-07-25 — no edits after Week 1** |
| `lucas_board_sim.py` | 10k-run season sim under three priors: ESPN FPI, tier-swap (headline), rank-swap (reference) |
| `lucas_board_sim_2026.csv` | Sim output: wins / bowl / 10-win probabilities per team under each prior. **Frozen — reproducible via the pinned engine (verified byte-identical 2026-08-18)** |
| `lucas_board_sim_2026_curve.csv` | Methodology sensitivity companion (run 2026-08-18, pre-kickoff): identical sim under the empirical margin curve via `--curve`. Not the pre-registered headline |
| `SIGMA_DIAGNOSIS.md` | Why the companion exists: the frozen sim's Normal(0, 13.5) conversion was retired from the live workbook 2026-08-18 |

The LUCAS_CALL paper rule in the workbook's Watch List tab reads
`lucas_board_2026.json` from here (see `build_conference_book.py`), paper-bets
every flagged team's games at first-seen lines, and grades all season.
2026 is the first sample — no backtest exists by construction.

Rerun order after a (pre-Week-1) board edit:
`build_lucas_board.py` → `lucas_board_sim.py` → workbook refresh.

## Methodology freeze note (2026-08-18)

The frozen CSV was built with Normal(0, 13.5) and unrated +24 — both retired
from the live workbook on 2026-08-18 (empirical curve, sd 17.94; unrated +29).
Both are now pinned inside `lucas_board_sim.py` so the pre-registered artifact
stays reproducible. Near pick'em the retired conversion is ~1.30x steeper, so
the frozen per-team deltas are inflated ~20-30% — equally across all three
priors, so signs and orderings stand. The `--curve` companion confirms it:
same ≥±1-win counts (1 up: Central Michigan; 2 down: Sacramento State,
Southern Miss), 100% delta-sign agreement, magnitudes ~18% smaller on
average. The frozen CSV remains the pre-registered headline; quote the
companion only as a robustness check.
