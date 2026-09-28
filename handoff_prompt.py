"""After the shoot: draft the takeover prompt for the next Sunday session.

    python handoff_prompt.py                 -> internal/TAKEOVER_PROMPT_<today>.md
    python handoff_prompt.py --shoot-done    -> same, plus the post-shoot checklist block at the top

The prompt = the fixed frame Lucas pastes into a new session (read order,
rules, routine, what stays on his word) + the current internal/STATE.md +
a blank "WHAT I WANT TO EXPAND" section for him. STATE.md is the thing to
keep current; this file only assembles it.
"""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATE = HERE / "internal" / "STATE.md"

FRAME = """# Takeover prompt — Man vs Machine (written {date})

Paste everything below the line into a new session. Add your own goals in the
"WHAT I WANT TO EXPAND" section before you send it.

* * *

You are continuing my "Man vs Machine — College Football Podcast" project
(co-host Corey Reddy) in `C:\\Users\\lucas\\Fun Projects\\Sports Data Analysis\\ncaa-fbs-model`.
Read, in this order: the project `CLAUDE.md` (autonomy split + hard rules),
`internal/STATE.md` (where everything stands — the whole state, kept short),
and the `cfb-pipeline` skill (commands, gotchas). Dated history is in
`internal/HANDOFF_*.md` and the result files (`internal/*_2026.md`) — read
those only when a thread needs its history. Your memory files cover the
presentation rules (podcast-deck-vs-notes), Corey's files (read-only), the
Carnival boundary, and the dossiers.

{shoot}
WEEKLY ROUTINE (do without asking, report after; each writes a summary in internal/)

* Sunday: `python sunday.py --week N` (N = the week just played) — finals,
  score tracker, pre-mortem grades, superdog ledger (machine), rebuild,
  weekly change, hot seat / Heisman (MARKET by hand first), next-week card
  data, superdog board, old-rule shadow, playoff summary, RECAP_ROWS snippet,
  AP check. Then: RECAP_ROWS / WEEK0_MISS / PRIOR_GAMES into make_episode_deck.py,
  the card from me, `notes_skeleton.py --week N+1 --ep E --games "..."` and
  `--boards`, write the reads and keys, push OneNote with -Prefix "Week N+1 - "
  into new sections (never overwrite a week).
* Tuesday: the 7:30 refresh runs itself; `python tuesday.py --week N+1`
  (availability news in first), refresh the notes' numbers, OneNote in place.
* Recording day, on my word: `python recording.py --week N+1` (publish ->
  freeze -> stat packages -> pre-mortems -> totals shadow -> availability ->
  deck -> lint -> review-before-air candidates), then push_deck -> merge_flow
  on Corey's CURRENT export -> push the merged file -> share_deck only if new.
  Give me the "review before air" list (5-10 least-certain numbers).
* After the shoot, when I say the shoot is done: Corey's picks into the
  ledger and tracker, then `python handoff_prompt.py --shoot-done` and hand me
  the prompt for Sunday.

STILL ON MY WORD, EVERY TIME
git push (public repo), anything that reaches the show or Corey (push_deck,
merge, share), switching what the on-air machine says, sharing files,
anything outside the folder. Corey's Google files are read-only unless his
email says exactly "Claude, I approve you to make changes".

STATE (internal/STATE.md as of {date})

{state}

WHAT I WANT TO EXPAND

(write it)

How to work: one-paragraph plan and the files you will touch before each
piece, then build it; measure anything that claims to predict through
backtest.py; report plainly when it does not beat the current machine;
commit locally as you go; ask only when two readings of my ask would lead to
materially different work.
"""

SHOOT_DONE = """POST-SHOOT CHECKLIST (the shoot is done)

* Corey's calls off his score slides -> score_tracker.json `man` (each
  number under that team's logo, his winner in green); his superdogs at the
  lines we recorded -> superdog_ledger.json; his Top 25 / Heisman five / Hot
  Seat ten into the boards notes; his off-by column is his to fill.
* Export the merged deck as recorded (decks/ + the Slides file id) so the
  receipts grade what was said, not what was regenerated.
* Confirm the frozen card (card_data_week{week}_frozen.json) is the one on
  air; nothing regenerates until the Ep switch.
* Sunday is `python sunday.py --week {week}`.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shoot-done", action="store_true")
    ap.add_argument("--week", type=int, help="the card week just recorded (for the checklist)")
    a = ap.parse_args()
    state = STATE.read_text(encoding="utf-8") if STATE.exists() else "(internal/STATE.md missing)"
    today = dt.date.today().strftime("%a %b %d, %Y")
    shoot = SHOOT_DONE.format(week=a.week or "N") if a.shoot_done else ""
    txt = FRAME.format(date=today, shoot=shoot, state=state)
    out = HERE / "internal" / f"TAKEOVER_PROMPT_{dt.date.today().isoformat()}.md"
    out.write_text(txt, encoding="utf-8")
    print(f"wrote {out.relative_to(HERE)}  ({len(txt.splitlines())} lines)")


if __name__ == "__main__":
    main()
