# ncaa-fbs-model — working rules

Man vs Machine college football podcast model (Lucas + co-host Corey Reddy).
Read `internal/HANDOFF_*.md` (newest) for the state of the pipeline and
`internal/NEXT_LEVEL_PROMPT_2026-09-22.md` for the build program.

## Autonomy (Lucas, 2026-09-22)

Lucas asked for more autonomy on this project. The split:

**Do without asking, then report what changed:**
- Anything nobody outside this folder sees: workbook rebuilds, grading,
  weekly-change columns, shadow ratings, backtests, internal research,
  notes drafts, OneNote reading copies (personal "Podcast" notebook only),
  the private mirror (`internal\backup.bat`).
- Local git commits, as you go, one concern per commit, clear messages.
- Scheduled / weekly pipeline steps (refresh, grade, reports) and leaving a
  summary for Lucas.
- Fixing a wrong number: fix it everywhere it appears (notes, OneNote page,
  json, deck source), then report it. Do not ask first.
- Retrying failed steps, gathering missing data, reading Corey's files
  read-only.

**Still on Lucas's word, every time:**
- `git push` (the repo is public).
- Anything that reaches the show or Corey: `push_deck.py` to the Slides
  file, sharing it, `merge_deck.py`, and any number that will be read on air
  is spot-checked by him from the weekly "review before air" list.
- Switching what the on-air machine says (new ratings stay in shadow).
- Editing Corey's Google files (never, unless his email says exactly
  "Claude, I approve you to make changes").
- Anything outside this folder, money, accounts, contest entries.

**Every week produce** a short "review before air" list in the handoff or
notes: the 5–10 numbers least certain (new stat, hand-typed, or
eye-catching per-attempt figures), so Lucas checks those instead of all of it.

## Hard rules (unchanged)
- Market numbers, line moves, Heisman prices, handoffs and research live in
  `internal/` (gitignored, mirrored to the private repo). Public notes and
  slides carry only what the presentation memory allows.
- Notes `.md` in `notes/` are the master copy; Lucas hand-edits them and the
  Slides file. `git diff notes/` and export the live Slides before any
  regeneration; never overwrite his edits or markers.
- Stats: rushing totals = official box score; per-attempt = completions
  only; stuff / explosive rates = play-by-play. Every number traces to
  `stat_package_weekN.json` or the box score, never memory.
- Global rules in `~/.claude/CLAUDE.md` (Carnival boundary) always apply.
