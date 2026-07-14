# Film Study Sessions — design spec (build target: week 1, Sept 2026)

Post-game "tape session" for flagged games — data-driven film study from CFBD
play-by-play (no video; the numbers ARE the film here).

## Trigger

After any completed game Lucas flags (or automatically for every game that was
on the Upset Board), run:

    python film_study.py --game "<away> at <home>" [--week N]

## The session report (one page per game)

1. **The score vs the script** — final vs the spread/total at alert time and
   close; what the model expected vs what happened.
2. **Win probability chart** — CFBD `/metrics/wp` per play; annotate the 3-5
   biggest swings.
3. **Turning points** — top plays by |EPA| from `/plays`: down/distance, call
   type, result. This is the "pull up the play" list for the show.
4. **Unit report card** — each side's EPA/play, success rate, explosiveness
   THIS game vs their season profile (did Indiana's offense look like
   Indiana's offense?). Flag deviations > 1 sd.
5. **Tendency check** — run rate by down, tempo, personnel proxies vs the
   scouting dossier's stated tendencies; note where the plan deviated.
6. **Alert grading** — if the game was on the Upset Board: model side, line
   at alert, result, running ATS ledger update.
7. **Watch list** — timestamped YouTube search link for the official highlight
   (title-formatted query), since the data can say *which* plays to watch.

## Output

- `film_study/<year>_wk<N>_<away>_at_<home>.md` (+ PNG of the WP chart)
- Optionally rendered as an artifact for phone reading before taping.

## Data endpoints (all covered by current CFBD tier)

`/games` (score, context) · `/plays` (play-by-play with EPA) ·
`/metrics/wp` (win probability) · `/game/box/advanced` (unit splits) ·
existing `alerts_log.json` (alert grading).

## Not in scope

Actual video analysis. The session tells you *what to watch and why it
mattered*; the film itself stays on YouTube/DVR.
