# Ep7 · Week 6 — BOARDS

Outline notes: topic → the points → the facts under each point. MACHINE-DRAFTED —
review before air. Drafted Sun Oct 4 from the Sunday rebuild (271 rated games). Corey's sections are
placeholders until his deck updates. Betting-line context stays in the internal folder.

- **Receipts (Week 5)** — man vs machine
  - Winners: machine 4–1, man 4–1 — the same miss: both had Penn State, Northwestern won by 21
  - Margin miss, lower is better: Man 54 · Machine 55 — a dead heat for the second week running
    - Two games were most of it for both: Northwestern by 21 (called Penn State by 2 and 3) and Alabama by 33 (called by 8.5 and 10)
    - The other three were inside a field goal for the machine: Pitt 1.5, Tennessee 3, Ohio State 3
  - Points off the FINAL SCORE (both teams' points added up): Man 80 · Machine 81
    - Per team (score_tracker.md): Corey closer on 4, the machine on 3, three ties — Corey had Ohio State's 31 on the nose and the identical Pitt 28–27 call
  - Game by game
    - Pittsburgh 35 at Virginia Tech 33 — called Pittsburgh 28–27; off by 1.5 · Corey Pittsburgh 28–27, off by 1
    - Penn State 13 at Northwestern 34 — called Penn State 24–22; off by 23 · Corey Penn State 27–24, off by 24
    - Alabama 56 at Mississippi State 23 — called Alabama 34–26; off by 24.5 · Corey Alabama 38–28, off by 23
    - Auburn 14 at Tennessee 24 — called Tennessee 31–24; off by 3 · Corey Tennessee 31–21, off by 0
    - Ohio State 31 at Iowa 14 — called Ohio State 30–16; off by 3 · Corey Ohio State 31–20, off by 6
  - Pre-mortems: 10 graded on the season, 1 fired, 1 pick lost — and the loss was not the one the pre-mortem named
    - Penn State: "wrong if Northwestern throws for more than 7.4 an attempt" — Northwestern threw for 6.6 and ran 55 times for 413. The machine watched the wrong door
    - The other four held: Virginia Tech 2.03 a carry (line 3.0), Mississippi State 0.6 a carry (line 4.2), Tennessee 4.84 a carry (floor 4.0), Ohio State 12.0 a throw (floor 9.1)
  - Superdogs: Man 48.5 · Machine 25.0
    - Machine: Boston College +21 covered (lost 25–16), Charlotte +20.5 did not (lost 59–8) → +5
    - Corey: Baylor +4 WON outright 55–19 (5 + 4), Colorado +13 lost 29–7 → +9 at the lines we recorded — CONFIRM his

- **The model change — say it once, on the Top 25 slide**
  - What changed (Sun Oct 4): a quarterback confirmed OUT now comes off his team's rating
    - Only a starting quarterback, only when the news is confirmed; the entry expires the week he returns. Other injuries and "questionable" tags stay out of the number
    - Why now: Pitt's Mason Heintschel tore his ACL at Virginia Tech and is out for the season
  - The evidence (2022–25, 542 team-games where the season's starter did not play): those teams fell 2.9 points short of the machine's number beyond the normal shortfall
    - First game without him: 4.1 points. After the machine has seen one game of the backup: 1.7
    - A flat penalty cut the miss on the 141 games of 2025 from 13.26 to 12.95
    - What did NOT predict the size: the backup's recruiting rating (top third 3.6, middle 1.0, bottom 4.4) or how good the starter was. Say: "we can tell you losing the quarterback costs about four points the first week; we cannot tell you which backups beat that"
  - What it did to the board: Pitt 8.9 → 4.9, No. 38 → No. 51. Nobody else has an entry
    - Pitt's backup is Holden Geriner, a fifth-year senior making his first career start against North Carolina; Heintschel was the lowest-rated recruit of Pitt's three quarterbacks
    - It is graded in the open: every game with a flagged team is scored with and without the quarterback points, and the layer comes off the air if it does not win

- **Top 25 (machine)**
  - Rule: residual cap 42, lam 3, de-lucked 3 a turnover; 271 rated games
  - Alabama No. 1 at 27.9 — 56–23 at Mississippi State as an 8.5-point favorite; four teams are inside eight tenths of a point at the top
    - Say: "one through four is a coin toss — Alabama 27.9, Georgia 27.8, Ohio State 27.6, Texas 27.1 — and two of them play Saturday"
  - The ten: Alabama 27.9 · Georgia 27.8 · Ohio State 27.6 · Texas 27.1 · Notre Dame 26.7 · Miami 26.2 · LSU 25.9 · Indiana 23.0 · Oregon 19.0 · Texas A&M 18.0
  - Risers (this week's games alone): Missouri +5.3 (#31 → #17); Florida State +5.0 (#36 → #19); Wake Forest +4.3 (#50 → #35); Baylor +3.8 (#43 → #28); Northwestern +3.5 (#33 → #25); Alabama +2.9 (#6 → #1)
    - Missouri: 45–17 over Florida; Florida State: 38–7 over Virginia; Northwestern: 34–13 over Penn State with 413 rushing yards
  - Fallers: Florida -4.8 (#9 → #15); Virginia -4.2 (#29 → #49); Michigan -2.1 (#24 → #32); Penn State -1.8 (#20 → #27); Ole Miss -1.4 (#15 → #16); USC -1.2 (#17 → #20)
  - Into the 25: Florida State #19, Missouri #17, Northwestern #25, Wisconsin #22 · Out: Auburn (#23 → #26), Iowa (#25 → #30), Michigan (#24 → #32), Penn State (#20 → #27)
    - Florida is the week's biggest loser: playoff odds 68% → 25%
  - Playoff picture (internal): Alabama 98% · Texas 97% · Georgia 94% · Notre Dame 93% · Miami 91% · Ohio State 87% · LSU 82% · Indiana 72% · Boise State 46% · Texas Tech 39% · Utah 38% · Oregon 35%

- **Heisman board (machine)** — index = team factor × blended efficiency (market 2026-09-27)
  - Darian Mensah (Miami) 50.7 (-0.7, #1 → #1)
  - Julian Sayin (Ohio State) 46.7 (-0.6, #3 → #2)
  - C.J. Carr (Notre Dame) 46.4 (-1.2, #2 → #3)
  - Josh Hoover (Indiana) 43.6 (+2.3, #4 → #4)
  - Keelon Russell (Alabama) 38.4 (+6.4, #6 → #5)
  - Devon Dampier (Utah) 32.5 (-0.9, #5 → #6)
  - Dante Moore (Oregon) 27.4 (+0.1, #10 → #7)
  - Sam Leavitt (LSU) 27.2 (-0.7, #9 → #8)
  - Non-QB watch: Jeremiah Smith (Ohio State), Malachi Toney (Miami), Ryan Wingo (Texas), Trent Mosley (USC)
  - All positions (the slide board): Julian Sayin (QB) 15.5 · Darian Mensah (QB) 14.4 · Keelon Russell (QB) 12.8 · C.J. Carr (QB) 12.6 · Devon Dampier (QB) 10.8 · Josh Hoover (QB) 10.5 · Jeremiah Smith (WR) 10.0 · Sam Leavitt (QB) 9.9
  - Julian Sayin (Ohio State) 15.5 (+0.0, #1 → #1)
  - Darian Mensah (Miami) 14.4 (+0.0, #2 → #2)
  - Keelon Russell (Alabama) 12.8 (+1.7, #5 → #3)
  - C.J. Carr (Notre Dame) 12.6 (+0.3, #3 → #4)
  - Devon Dampier (Utah) 10.8 (-0.3, #4 → #5)
  - Josh Hoover (Indiana) 10.5 (+1.2, #9 → #6)
  - Jeremiah Smith (Ohio State) 10.0 (+0.5, #8 → #7)
  - Sam Leavitt (LSU) 9.9 (-1.1, #6 → #8)

- **Hot Seat (machine)** — 60 × (CBS ÷ 5) + 40 × P(miss the bar); CBS frozen 2026-08-29
  - Mike Locksley (Maryland) 90.7 (+0.0, #2 → #1)
  - Mike Norvell (Florida State) 78.6 (-12.6, #1 → #2)
  - Derek Mason (Middle Tennessee) 76.5 (+7.3, #7 → #3)
  - Dabo Swinney (Clemson) 72.2 (+1.7, #6 → #4)
  - Shane Beamer (South Carolina) 71.6 (-2.0, #4 → #5)
  - Greg Schiano (Rutgers) 69.9 (+2.0, #9 → #6)
  - Bryant Vincent (UL Monroe) 69.3 (-3.3, #5 → #7)
  - Dave Aranda (Baylor) 68.8 (-7.2, #3 → #8)
  - Scott Satterfield (Cincinnati) 67.0 (+9.0, #19 → #9)
  - Lincoln Riley (USC) 66.9 (+5.2, #14 → #10)
  - Bill O'Brien (Boston College) 66.0 (-2.0, #8 → #11)
  - Deion Sanders (Colorado) 62.2 (-3.7, #11 → #12)

- **Superdog picks** (lines as of 2026-10-04T15:03:58+00:00 — re-read at the freeze)
  - Machine Giant Killer: South Carolina +14.5 at Florida (#8) — exp 8.82, machine -5.4
  - Machine Superdog: Iowa State +14.5 at BYU (#10) — exp 6.77, machine -10.3
    - Next: Nebraska +8.5 vs Indiana (#6) — exp 5.82, machine -6.2 · Southern Miss +9.5 at Troy — exp 5.57, machine -8.1 · UCLA +12.5 at Oregon (#15) — exp 5.54, machine -11.6
  - Corey's picks: PLACEHOLDER (Week 6)
