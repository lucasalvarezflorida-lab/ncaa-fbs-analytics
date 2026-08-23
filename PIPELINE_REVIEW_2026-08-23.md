# Pipeline review — Week 0 card vs. the live market (audit of Aug 22, 2026)

**Scope.** Logic and data-flow audit of the CFB pipeline in `ncaa-fbs-model`
(CFBD client → `build_conference_book.py` → `edge_report.py` / `margin_prob.py` →
`make_episode_deck.py`; decomposition in `fpi-decomposition/`). No style
changes proposed. Every claim below was traced to a file:line or reproduced by
running the code on Aug 23. Line numbers are as of commit `e39edbb`.

**How it was checked.** Three read-only code traces (lines, probabilities,
decomposition inputs) plus hands-on reproduction: `edge_report.py --week 1
--view ml` run without `--refresh` printed the Aug 18 lines (TCU −6.5, UVA −3,
NDSU −10); a direct CFBD `/lines` pull one minute later returned TCU −7.5/−8,
UVA −5.5/−5.5, NDSU −7/−7, Stanford −5.5 (opened −3), UNLV −5.5 (opened −3).
That single comparison reproduces audit finding #1 and explains it.

---

## 0. The root cause behind findings 1, 2 and 7 (and half of 3–6)

**The card is hand-keyed.** `make_episode_deck.py` imports nothing from the
pipeline — `os` and `python-pptx` only (`:9-15`). Every number on the card is a
string literal in the `GAMES` list: machine spread, market spread, the gap
text, the win-probability split tuple, unit ranks inside the bullets, the UNC
residual in the honesty line, player stat lines, the σ in the footer.

Consequences, in order of the audit's findings:

- The card is a snapshot of whatever was typed on Aug 18. Nothing can tell it
  the market moved, because nothing it displays is read back from the
  pipeline at build time. (Finding 1.)
- `edge_report.py --view ml` **already** computes moneyline-implied win
  probability with vig removal (`odds.novig`, proportional default; shin/power
  available) and prints `MODEL%` vs `MKT%`. On Aug 18 its own output showed UNC
  45.9% vs 31.5% — i.e. TCU 54% vs 68.5% — a 14.5-pt gap that was already
  flaggable. The card never consumed it. Today at −310/−235 the market says
  TCU ≈ 71–75%. The 22-pt disagreement did not go unflagged because the
  pipeline lacked the number; it went unflagged because the card does not read
  the pipeline. (Finding 2.)
- The same number exists in three vintages: UNC's residual is **−12.1** on the
  deck (hand-typed), **−11.8** in the workbook `_Teams` sheet (the `--transfer`
  refit), **−12.13** in `fpi-decomposition/output/team_table_2025.csv` (the
  base fit). Pribula 1,946 vs 1,941 is the same disease. (Finding 7.)

Everything in sections A–F is built around one contract change: **the deck
reads a `card_data_week{N}.json` that the pipeline writes at publish time.**
That is the structural change; most of A–F are then small.

---

## 1. Finding-by-finding audit

### F1 — Lines were Aug 18; market moved by Aug 22
- `fetch_lines()` — `build_conference_book.py:118-143` — one season-wide
  `/lines?year=2026&seasonType=regular` call (no `week`), cached to
  `fpi-decomposition/data/lines_seasonType-regular_year-2026.json` (gitignored,
  overwritten on refresh). Refreshed only by `refresh_all.py` (the Tuesday
  7:30 task) or `edge_report.py --refresh`. There is **no publish-time pull**.
- Book merge is **per field, not per book** (`:127-135`): `spread` may come from
  DraftKings while `home_ml` comes from Bovada, with no provenance field. The
  devig in `--view ml` can therefore pair one book's spread with another's
  moneyline.
- Persistence: `alerts_log.json` (`update_alerts_log`, `:1182-1208`) stores an
  immutable first-seen `spread` and an overwritten `close_spread` — **RED/YEL
  games only**. CLV is computed at render (`:1294-1297`) and never persisted.
  `watchlist_log.json` is insert-only: no current line, no CLV.
- **Non-alert games persist nothing.** NC State @ Virginia had a 3.7-pt edge,
  below `EDGE_YEL = 6.0` (`:97`), so no row was ever created. There was no
  mechanism that *could* have flagged "edge gone — market converged."
- `spread_open` is fetched and displayed (`:221`) but never logged — the one
  free opening-line datapoint is discarded.

### F2 — 54% vs ~76%, only spreads compared
- Model win prob: `model_curve.win_prob(model_margin)` (`edge_report.py:180`).
- Market prob: `novig(home_ml, away_ml)` when both MLs exist and overround ≤
  15% (`:182-184`; the Bovada −100000 placeholder guard), else the market curve
  at the spread, tagged `*` (`:186-188`).
- `EDGE` = signed `100·(p_model − q_market)` on the model's side (`:193-196`).
  There is no **unsigned** "how far apart are the two worldviews" flag, and the
  Upset Board path (`fetch_games` `:200-209`) never looks at a moneyline at all
  — RED/YEL are pure spread-gap tiers.

### F3 — Preseason FPI carried Virginia's 2025 rating; no churn signal
- The 2026 prior is ESPN's preseason FPI snapshot, overlaid verbatim
  (`load_fpi_2026`, `:104-115`; overlay `:334-343`). It is the *only* rating
  input to alerts, sims and the edge report.
- The 2026 `/player/returning` file has **136 rows cached and zero consumers**
  outside a gate boolean (`refresh_all.py:361-367`).
- The decomposition (prior SP+, returning PPA, talent, 4-yr recruiting,
  `--transfer` portal quality — `analysis.py:16, 185-199`) is **blocked for
  2026** by `if not (ret and tal)` (`refresh_all.py:367`): CFBD's 2026 `/talent`
  is 0 rows. A two-line year-fallback in `load_talent` (`analysis.py:101-107`,
  mirroring `load_fpi` at `:64-65`) unblocks it.
- No per-team churn aggregate exists anywhere. Portal in/out are per-player
  note strings (`build_official.py:53-57, :70, :99`) rendered as a `•`.
- **The UVA warning already existed.** The 2025-fit residual for Virginia is
  **+11.67 (11th-highest in FBS)** — "ESPN's rating ran 11.7 points ahead of what
  public inputs explain." It is in `_Teams` (`Residual`, `Resid Rank`) and in
  `team_table_2025.csv`. It was never rendered on the card.
- Caveat for the fix: ESPN's preseason FPI **already prices** returning
  production and recruiting. Adding returning production as a rating modifier
  double-counts. The right cheap signal is a *staleness warning* (+ a σ
  widen); the right rating fix is the 2026 decomposition residual.

### F4 — Qualitative risk has no representation
Confirmed: no flag field in `GAMES`, in `alerts_log`/`watchlist_log` entries,
in `_Teams`, or in card output. Nothing to extend — it must be added.

### F5 — NDSU emitted at full confidence
- `MarginCurve.win_prob(m)` = `ndtr((m + residuals)/bandwidth).mean()` over
  3,844 stored residuals (`margin_prob.py:36-51`). One global residual pool;
  `bandwidth` (Silverman, 3.65) is *smoothing*, not variance. **No σ-scaling
  parameter exists anywhere.** `fit_margin_curve.py:143-148` computes a
  heteroskedasticity check by |margin| bucket and discards it.
- The curve was fit only on games where **both** teams had a prior-year FPI
  (`fit_margin_curve.py:76-78`). Transitioning programs are outside the fitted
  population; the 17.9-sd curve is literally not evidence about them.
- NDSU has ESPN −8.3 in the snapshot (rank 100), so `UNRATED_MARGIN` never
  fires; nothing in the data model says "no history" — `teams_fbs_2026.json`
  has `classification: "fbs"` for all 138 and no first-FBS-year field. The only
  special-casing is the hardcoded `TITLE_INELIGIBLE` set (`:1593-1594`), used
  solely for conference-title seeding.

### F6 — Team ST rank hid a player-level outlier
- `ST Rk` in `_Teams` is the SP+ special-teams component (note strings like
  "SP+ ST 1.20"). Team-level by construction.
- Player-level return data lives in the same CFBD season-stats endpoint the
  player lines came from (`puntReturns`, `kickReturns` categories). Today's
  pull surfaced exactly the cases F6 describes: Hawai'i's #8 unit was
  Matsuzawa (27/29 FG) + Barfield (28.7 KR avg, TD) — the kicker is gone;
  Memphis's #16 was Sutton Smith's 99-yd KR TD — gone. Nothing in the
  pipeline reads those categories.

### F7 — Pribula 1,946 vs 1,941
- No source-of-truth file; stat strings were typed from a scratchpad fetch.
- CFBD's season totals are play-by-play derived and routinely differ by a few
  yards from official box totals. This is a **source disagreement**, not a
  transcription error — the fix is to declare one source canonical (CFBD,
  since everything else on the card is CFBD) and print it in the footer.
- Same class: J'Mond Tapp 13 TFL (deep-dive prose) vs 12.0 (CFBD); UNC residual
  in three vintages (§0).

---

## 2. Proposals A–F (minimal changes)

### A. Lines: publish-time re-pull, first-seen + current per book, auto-CLV, decay flag
1. **`line_ledger.py`** (new, ~80 lines). `record(games)` appends one row per
   game per book to `lines_history.jsonl`: `{ts, game_id, book, spread,
   spread_open, ou, home_ml, away_ml}`. Append-only; ~300 rows per pull. Call
   it from `build_data_sheets` right after `fetch_lines` **and** from the new
   publish step. First row for a game = first-seen; last row = current.
2. **Provenance in the merge** (`fetch_lines :131-135`): add `spread_book`,
   `ml_book` to the merged dict; in `--view ml`, prefer a same-book spread/ML
   pair before falling back to the merged one.
3. **CLV for every game**, not just alerts: lift the formula at `:1294-1297`
   into `line_ledger.clv(game_id, model_side)` and persist `clv` on the
   card-data row. Store `first_seen_edge` and `current_edge` next to it.
4. **Decay flag**: `EDGE_GONE` when `first_seen_edge ≥ EDGE_MIN (3.0)` and
   `current_edge < EDGE_DECAY (1.5)`; `CLV+` when the line moved ≥ 2.0 toward
   the model side. Thresholds in one config dict at the top of `edge_report.py`.
   Against today's data: UVA first-seen 3.7 → current 1.2 → `EDGE_GONE` fires;
   JSU/NDSU −10 → −7 → `CLV+3.0`; Memphis/UNLV −3 → −5.5 → `CLV+2.5`.
5. **Publish step**: `python edge_report.py --week N --refresh --publish`
   re-pulls `/lines`, records the ledger, and writes `card_data_week{N}.json`
   (per game: model margin, model wp, per-book spread/ML, ML-implied wp, CLV,
   flags, tier). Task Scheduler: clone `refresh_headless.bat` into
   `publish_friday.bat` (Fridays 17:00, same pattern as the NHL job).

### B. Moneyline-implied win probability + "structural disagreement"
- `edge_report.build_ml_rows` (`:169-221`): add `wp_gap = abs(p_model −
  q_market)` and flag **`STRUCT`** when `wp_gap ≥ STRUCT_PP (15)` **and**
  `mkt_src == "ml"` (never on the spread-derived fallback). Keep `EDGE`
  signed and side-based as it is; `STRUCT` is unsigned and about the matchup.
- Add `mkt_wp` to `fetch_games` game dicts (`build_conference_book.py:~200`)
  so the Upset Board's RED/YEL rows carry the market's win prob too; show it
  as a column on the Upset Board.
- Card treatment: `card_data` carries the flag; the deck renders a red ribbon
  and swaps the lean template — "the market disagrees about the *matchup*, not
  the number; research, not a play" — which is exactly what UNC/TCU needed.

### C. Cheapest viable roster-churn signal
- **Step 1 (quick, no model change):** `load_returning(2026)` next to
  `:321` in `build_data_sheets`; two new `_Teams` columns `RetPPA26` /
  `RetPPA26 Rk` from `percentPPA`. Card shows "Returning production: 44%
  (#130)" per team; `STALE_PRIOR` warning when rank ≥ 100 (UNC, Memphis at
  111th, UVA). Goes into `card_data`.
- **Step 2 (the real fix, ~10 lines):** year-fallback in
  `analysis.load_talent` (`:101-107`) exactly like `load_fpi` (`:64-65`);
  loosen the gate at `refresh_all.py:367` to `if not ret:`; run
  `fpi_decomposition.py --year 2026 --transfer`. The output residual is "ESPN
  preseason minus what public inputs explain" — the UVA-shaped warning, for
  every team, computed instead of remembered. Render `Resid26` on the card.
- **Do not** add returning production as a rating modifier (double-counts
  ESPN's own preseason inputs). If you want a number to move, widen σ by churn
  tier (E), which changes confidence, not the point estimate.

### D. Qualitative overlay sidecar
- `cards/week{N}_flags.json` (JSON — the repo has no PyYAML dependency and no
  reason to add one):
  ```json
  {"401520123": {"North Carolina": [
      {"type": "coaching", "text": "DC on medical leave; GM suspended"},
      {"type": "qb_tier",  "text": "Edwards: injury-lost 2025", "sigma_mult": 1.1}],
    "TCU": [{"type": "qb_tier", "text": "Craig: zero FBS snaps", "sigma_mult": 1.15}]}}
  ```
- `edge_report --publish` merges flags into `card_data`; the product of any
  `sigma_mult` values becomes the game's `scale` (E). The model does not price
  the flag text; the deck renders a FLAGS strip under the score bug. Missing
  file = no flags; unknown `type` = warning, not error.

### E. Uncertainty tiers
- `MarginCurve.win_prob(margin, scale=1.0)`: `ndtr((m + scale*residuals) /
  (scale*bandwidth)).mean()` — exact widening of the residual distribution by
  `scale` under the existing KDE (`margin_prob.py:45-51`, one-line change).
- Tier rule needs **no new data**: count the seasons a team appears in the
  prior-year FPI files the curve fit already uses
  (`fpi-decomposition/data/fpi_year-*.json`). 0 seasons → tier 2 (`scale
  1.5`); 1 season → tier 1 (`1.25`); else 1.0. Tier 2 today: NDSU, Sac State,
  Delaware, Missouri State, Kennesaw.
- Output for tier ≥ 1: a **range** — `win_prob` at scale 1.0 and at the tier
  scale — labelled `MAX UNCERTAINTY`. JSU/NDSU would print "NDSU 55–57%"
  instead of "57%". Season Sim uses the same `scale` per game.

### F. Stat validation
- Promote this session's fetch into the repo as `fetch_player_stats.py` →
  `player_stats_2025.json` keyed `(player, 2025 team)` — the single source of
  truth; mark CFBD canonical in the deck footer ("stats: CFBD").
- Deck notes reference stats by key and the generator formats them, so
  generated lines cannot disagree with the source by construction.
- `validate_deck_stats.py`: for any note that still carries hand-typed
  numbers, extract numeric tokens and assert each appears in that player's
  source record; non-zero exit on mismatch; run as the last step of the deck
  build (and before upload). Extend to residuals: read from
  `team_table_2025.csv` rather than typing −12.1.

---

## 3. Quick wins vs. structural, and the sequence before Week 1 (Sept 3–5)

**Quick wins (each ≤ half a day, no model change):** A1–A4 (ledger, CLV,
decay flag), B (`STRUCT` flag), C-step-1 (returning-production column +
warning), D (sidecar + render), E (`scale` param + tier from existing files),
F (source file + validator).

**Structural:** the `card_data` contract (deck consumes the pipeline — fixes
the root cause; touches `edge_report.py` and `make_episode_deck.py`), A2
(book provenance — touches the merge everything downstream uses), A5 (publish
task), C-step-2 (2026 decomposition + reviewing its output).

| When | Do | Why this order |
|---|---|---|
| Mon Aug 24 | A1, A3, A4 + A2 | Start the ledger **today** so Week 0 gets a first-seen baseline for all 53 games (Aug 23 becomes first-seen for non-alert games — note it in the ledger). |
| Tue Aug 25 (after the 7:30 refresh) | B, E | Re-run `--view ml`; confirm UNC/TCU → `STRUCT`, JSU/NDSU → tier 2 range, UVA → `EDGE_GONE`. |
| Wed Aug 26 | `card_data` contract + D | Regenerate the Week 0 deck from pipeline data — the first deck that cannot drift. |
| Thu Aug 27 | F + C-step-1 | Validator gates the build; returning-production warning on the card. |
| Fri Aug 28 | A5 publish pull → final Week 0 card | Lines as of publish time, CLV vs first-seen, flags live. |
| Aug 31 – Sep 2 | C-step-2 | Unblock the 2026 decomposition; check residuals_2026 against the UVA/UNC cases; add `Resid26` to the card. Schedule `publish_friday.bat`. |

Deferred on purpose: a week-dependent (heteroskedastic) curve, any rating
modifier, and unifying the two sim conversions (below).

---

## 4. Also found (not on the audit list)

- **Two live conversions.** The per-team Season Sim draws independent
  Bernoullis per game (`:1766`); the conference joint sim bootstraps residuals
  (`:1684-1685`). Per-team win totals ignore within-team correlation.
- **`load_fpi_2026` returns `{}` silently** if the snapshot glob misses
  (`:108-109`); everything downstream would run on 2025 values. Only
  `edge_report.py:70-71` guards it.
- **Run-once sentinel** for the 2026 decomposition keys on file existence
  (`refresh_all.py:357`); a failed partial run would permanently suppress
  retries.
- **"2025's biggest ACC market-overrating"** — UNC −12.13 vs Syracuse −12.06.
  True, but within rounding; say "one of the two."
- `scripts/fetch_returning_production.py` reads fields that don't exist
  (`percentageOffense`, …); orphaned, fails silently.
- The Upset Board `GUARD` only fires for RED dogs +401 on road/neutral; your
  own post-mortem's longshot finding applies to YEL and non-alert games too.
- Path note: this repo is `Fun Projects\Sports Data Analysis\ncaa-fbs-model`
  (git, GitHub remote), not OneDrive; the Tuesday Task Scheduler job already
  exists (`refresh_headless.bat`) and is the template for the Friday publish job.

## 5. Where the Week 0 card stands after today's re-pull (deck v6, lines Aug 23)

| Game | Machine | Market (DK/Bov) | First-seen → now | What would have flagged |
|---|---|---|---|---|
| UNC vs TCU (N) | TCU −1.5 (54%) | −7.5 / −8, ML −310/−235 (~71%) | −6.5 → −7.5 | `STRUCT` (17 pp), `STALE_PRIOR` (UNC 44% ret. prod.) |
| NC State @ UVA | UVA −6.7 (65%) | −5.5 / −5.5 | −3 → −5.5 | `EDGE_GONE` (3.7 → 1.2), `Resid +11.7` |
| JSU @ NDSU | NDSU −2.7 (57%) | −7 / −7 | −10 → −7 | `CLV +3.0`, tier 2 → "55–57%" |
| Hawai'i @ Stanford | Stanford −1.6 (54%) | −5.5 / −5.5 | −3 → −5.5 | none (4-pt gap, 7 pp); QB-tier flag (Warren) |
| Memphis @ UNLV | UNLV −6.2 (64%) | −5.5 / −5.5 | −3 → −5.5 | `CLV +2.5`, `STALE_PRIOR` (Memphis 111th) |
