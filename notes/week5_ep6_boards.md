# Ep6 · Week 5 — BOARDS

Outline notes: topic → the points → the facts under each point. Read the
level you need. Drafted Sun Sep 27 from the Sunday rebuild, numbers re-checked Tue Sep 29 night (215 rated games; AP Week 5
poll of Sun Sep 27 evening). MACHINE-DRAFTED — review before air. Corey's sections are
placeholders until his deck updates (his file is read-only for us).
Betting-line context for this episode is kept out of this file on purpose -
it lives in the internal folder, which is not in the repo.

- **Receipts (Week 4)** — man vs machine
  - Winners: machine 5–0, man 5–0 — first clean sweep of the year for both; all five favorites won
  - Margin miss, lower is better: Machine 78.0 · Man 79.0 — a dead heat
    - Machine closer on two (Texas 6 vs 4 is HIS, so: Florida 21 vs 23, LSU 23.5 vs 25); man closer on two (Texas 4 vs 6, Oregon 13 vs 13.5); Georgia a tie at 14
    - Three of the five were blowouts nobody had: Florida by 24, Georgia by 28, LSU by 29
  - Points off the FINAL SCORE (both teams' points added up): Machine 89 · Man 93
    - Per team (score_tracker.md): the machine closer on 5 teams, Corey on 5 — Ole Miss 28 was called on the nose
    - Corey's calls, read off his score slides (his winner in green): Texas 31–24 · Florida 35–34 · Georgia 34–20 · Oregon 35–34 · LSU 31–27
  - Machine's season: 289.5 points off across 25 games (11.6 a game)
    - Man's season total still needs his Weeks 0–2 calls re-read under the right convention — ask him for them
  - Game by game
    - Texas 20 at Tennessee 17 — called Texas 32–23; our line Texas −9, off by 6
      - Deserved Tennessee +4.4: Tennessee out-gained Texas per play; Texas won on the turnover and the sacks — 8 sacks of Brandon in 40 dropbacks
      - The pre-mortem held: "wrong if Tennessee runs for more than 5.0 a carry" — Tennessee ran 44 times for 70 (1.6)
    - Ole Miss 28 at Florida 52 — called Florida 31–28; our line Florida −3, off by 21
      - Deserved Florida +19.6 — it was as lopsided as the score; Florida ran 53 times for 302
      - The pre-mortem FIRED (Philo under 9.9 a throw: 8.5) and the pick still won — the run game made the passing number irrelevant
    - Oklahoma 13 at Georgia 41 — called Georgia 29–15; our line Georgia −14, off by 14
      - Deserved Georgia +19.4; Georgia 4.96 a carry, right at the 4.5 pre-mortem line and over it
    - Oregon 41 at USC 27 — called Oregon 32–31; our line Oregon −0.5, off by 13.5
      - Deserved Oregon +8.4; USC 2-of-11 on third down (18%) against a pre-mortem set at 46%
    - Texas A&M 6 at LSU 35 — called LSU 29–23; our line LSU −5.5, off by 23.5
      - Deserved LSU +33.9 — the machine's worst miss of the year and the score UNDERSOLD it; A&M 2.76 a carry, under the 2.8 pre-mortem line by a hair
  - Pre-mortems, first grades: 5 written, 1 fired, 0 picks lost — the machine has not been wrong yet, so it has not been tested yet
  - Superdogs: machine Georgia Southern +18.5 covered (lost by 14), Charlotte +10 did not (lost 34–7) → Machine 20. Corey: Air Force +5.5 WON outright 36–33 (5 + 5.5), Iowa State +8 lost by 14 → Man 39.5 at the lines we recorded — CONFIRM his

- **The rule change — say it once, on the Top 25 slide**
  - What changed (from this week's refresh): the machine now grades a game on what the teams did, not on who fumbled
    - Each result is de-lucked before it goes in: the margin minus 3 points for every turnover the winner was handed. A 35–6 with three interceptions the wrong way counts as a 26-point win, not 29
    - Why 3: over four seasons the machine's misses moved about 4 points per turnover, and turnover margin is mostly noise week to week — the rating was learning luck
    - The cap that limits how much one game can move a team widened from 28 to 42 points of evidence; everything else (July prior worth three games, 2.5 for home) is the same
  - Backtested 2022–25 (the same harness that graded every other change): better in all four seasons, closer to the closing line in the under-14 games by a third, favorites over-rated less. First change that has cleared the bar; the September ones did not
  - What it did to the board: Georgia 30.5 → 29.0 (still #1), Notre Dame 29.7 → 27.7, Ohio State 28.5 → 27.5, Texas 27.9 → 27.0; LSU 25.2 → 26.1 (#7 → #5), Alabama 27.1 → 24.9 (#5 → #6); Penn State 16.1 → 13.3 (#14 → #20); Oklahoma 14.3 → 16.2 (#18 → #14); Texas A&M 16.7 → 17.8 (#13 → #11)
    - Say: "the level of the whole board came down a point or two — a de-lucked margin is a smaller margin — the order barely moved except where a team had been winning or losing the turnover battle"
    - The weekly-change column is computed under the new rule on both ends, so it shows Saturday, not the rule

- **Top 25 (machine)**
  - What the number means (say it once if there is a new listener)
    - Points better than an average FBS team on a neutral field; a line = the difference + 2.5 for home
    - July prior is worth three games; FCS games count nothing; every game goes in de-lucked (see above), one game moves a team by at most 42 points of evidence
  - Georgia No. 1 at 29.0 — beat Oklahoma by 28 as a 14-point favorite, the biggest beat in the top ten this week
    - Ohio State 27.5 (#1 → #3) and Texas 27.0 (#2 → #4) both won and both slipped: Ohio State by 23 as a 27-point favorite, Texas by 3 as a 9-point favorite
    - Say: "the machine grades the win against the expectation — three points at Tennessee was not the No. 1 team's day"
  - The ten: Georgia 29.0 · Notre Dame 27.7 · Ohio State 27.5 · Texas 27.0 · LSU 26.1 · Alabama 24.9 · Miami 24.6 · Indiana 21.4 · Florida 20.4 · Oregon 19.1
  - Risers (the week's games alone, rule held constant)
    - Florida +3.4, #12 → #9: beat Ole Miss by 24 as a 3-point favorite; 1,040 rushing yards through four games
    - Notre Dame +3.2, #4 → #2: 49–10 at Purdue
    - Oregon +2.8, #13 → #10: won by 14 at USC as a half-point favorite
    - LSU +2.4 (stays #5): 35–6 over A&M as a 5.5-point favorite — the efficiency said it deserved 34
    - Georgia +1.9, #3 → #1 (above); Alabama +1.6, #7 → #6: 49–18 over South Carolina; Nebraska +1.3, #24 → #18: 31–13 at Michigan State
  - Fallers
    - Ole Miss −2.9, #10 → #15: lost by 24 at Florida as a 3-point dog — a 21-point miss two weeks after beating LSU
    - Penn State −2.9, #15 → #20: LOST 24–20 at home to Wisconsin as a two-touchdown favorite
    - Texas A&M −2.1, #9 → #11: lost 35–6 at LSU — that is −7.4 in two weeks
    - Indiana −1.9 (stays #8): 29–23 over Northwestern as a 19-point favorite; South Carolina −1.8, #19 → #22; Oklahoma −1.7, #11 → #14
  - Into the 25: Iowa #25 (won 20–19 at Michigan) · Out: SMU (#23 → #30, only 34–24 over Missouri State) · Louisville (#28 → #41 after the home loss to Wake Forest) and Pittsburgh (#26) sit just outside
  - The Texas question — expect it: No. 1 in the AP again, No. 4 here
    - Four games, three of them decided by 8 or fewer (Ohio State by 1, Texas at Tennessee by 3); the machine has Texas 1.9 points behind Georgia and rates the Ohio State win as the whole résumé
    - The efficiency side says Tennessee out-played them (deserved Tennessee +4.4) — Texas won on 8 sacks and the turnover, and the new rule takes the turnover out
    - Say: "voters rank wins, the machine rates margins — Texas is 4–0 with two one-score wins over top-ten teams; both can be right"
  - Voters vs us (AP Week 5, Sun 9/27)
    - Oklahoma State 19 vs our 38 · Houston 20 vs our 35 · Kentucky 24 vs our 39 · BYU 10 vs our 21 · Iowa 14 vs our 25 · SMU 21 vs our 30 · Boise State 22 vs our 29
    - Ours not theirs: Texas A&M, Oklahoma, Nebraska, Penn State, South Carolina, Auburn, Michigan · Theirs not ours: Oklahoma State, Houston, SMU, Boise State, UCLA, Kentucky, Missouri
    - Agree on the top four in some order (Texas / Georgia / Notre Dame / Ohio State); the voters have Miami 4th, we have it 7th; Penn State and Michigan fell out of their poll, Penn State is still our #20
  - Playoff picture (the machine's simulator, 10,000 seasons from these ratings — internal column, not on the slide unless Lucas says)
    - Texas 96% to make the field, Georgia 95%, Notre Dame 90%, Alabama 88%, LSU 84%, Ohio State 84%, Miami 81% (ACC title 72%), Florida 68%
    - Indiana 56%, Boise State 44% (the G5 bid), Utah 44%, Texas Tech 35%, Oregon 34%, Ole Miss 33%, Mississippi State 30%, Tennessee 22%
    - National title: Georgia 20%, Texas 14%, Notre Dame 14%, Ohio State 14%, LSU 10%, Alabama 9%, Miami 7%
    - Say: "Ole Miss went from 55% to 33% in one Saturday — that is what a 24-point loss to a division rival does to a résumé"

- **Top 25 (Corey's)** — PLACEHOLDER until his Week 5 deck posts (read-only export)
  - Last week's top ten for reference: Texas · Georgia · Notre Dame · Indiana · Miami · Alabama · Tennessee · Penn State · Ohio State · Ole Miss
  - Expect: Tennessee and Penn State down after home losses; Ole Miss down; Florida and LSU up

- **Heisman board (machine) — ALL POSITIONS from this week (Lucas, Tue 9/29)**
  - How it works: index = points added per game × team factor, any position
    - Points added = CFBD PPA per play, shrunk toward the player's 2025 rate (150 plays of prior for a QB, 40 for a receiver or back), × plays ÷ games; team factor = 0.5 + half the team's odds of 10+ wins
    - Why per game and not per play: a receiver adds about 1.0 a touch and a passer about 0.5 a throw — per play is not comparable across positions; per game is what the voters see
  - The five: Sayin 15.5 · Mensah 14.4 · Carr 12.3 · Dampier 11.1 · Russell 11.1
    - Sayin over Mensah is volume: 19.1 points a game on 131 plays against 16.2 on 112 — Mensah is the more efficient passer (0.86 a play to 0.63) and Miami has thrown less
    - Next: Leavitt 11.0 · Maiava 10.0 · Jeremiah Smith 9.5 (WR, 8th — 11.7 points a game on 47 touches, the market's favorite) · Hoover 9.3 · Hammond 9.3 · Kamario Taylor 9.2 · Chambliss 9.0
    - Say: "regardless of position the machine still lands on quarterbacks — the best receiver in the country touches it 12 times a game, his quarterback 33"
    - Frame it (the slide says it too): this is the machine's best-player board — who is playing the best football so far — not a prediction of the December vote; the index has never been tested against who wins, and a study to do that is queued
  - The QB efficiency board (per play, the index we used through Week 4): Mensah 51.4 · Carr 47.6 · Sayin 47.3 · Hoover 41.3 · Dampier 33.4
    - Mensah +4.6 and back to a clear No. 1: 27-of-34 for 10.9 a throw against Central Michigan; per-play 0.86 on 112 plays; 94-of-106 on the season, 11 TD, 0 INT, sacked three times all year
    - Carr +1.4, #3 → #2: 49–10 at Purdue; Notre Dame 91% for ten wins — the team factor is the highest on the board
    - Sayin +1.9, #4 → #3: 27-of-36 for 10.2 against Illinois; 0.63 per play — and Jeremiah Smith is the market's favorite off his back (12 catches, 217, 4 TD)
    - Hoover −5.2, #2 → #4: Indiana only 29–23 over Northwestern; Indiana's ten-win odds and his per-play both fell
    - Dampier holds #5 at 33.4: Utah 58% for ten wins after the win at Iowa State
  - Risers below the five
    - Sam Leavitt +6.6, #13 → #9: 35–6 over A&M; LSU's ten-win odds 51%
    - Keelon Russell +4.5, #9 → #6: 21-of-27 for 13.5 a throw against South Carolina, 7 explosive passes; 0.58 per play, no 2025 line so the prior is the FBS average — Alabama's ten-win odds (40%) hold him under Dampier
    - Dante Moore +1.3, #10: won at USC, 0.44 per play
  - Fallers
    - Lincoln Kienholz, #8 → out of the twelve: Louisville lost at home to Wake Forest
    - Kamario Taylor −1.7, #11: won 31–24 over Missouri, 27-of-38; Mississippi State's ten-win odds are 3% and that is what holds him down — the market disagrees loudly (+480, third choice)
    - Arch Manning off the board (#16 last week, lower now): won at Tennessee but the passing game did not show — the machine's index and the market (+3000) agree he is off it for now
  - Card quarterbacks: Russell (#6) and Taylor (#11) meet in Starkville; Sayin (#3) plays at Iowa; Byrum Brown (Auburn) at Tennessee; Becht (Penn State), Chiles (Northwestern), Heintschel (Pitt) and Grunkemeyer (Virginia Tech) are not on the board — check the starters against the stat package
  - Non-QB watch: Jeremiah Smith (33 catches, 617 yards, 7 TD — 1.04 per play, the market's favorite at +245; plays at Iowa), Malachi Toney (34 for 564, 6 TD), Jadan Baugh (54 carries, 458, 8 TD)

- **Heisman (Corey's five)** — PLACEHOLDER until his deck posts. Last week: Hawkins Jr (WVU) · Sheppard (Duke) · Kamario Taylor · Maiava · Kienholz

- **Hot Seat (machine)**
  - How the score works (0–100): 60 × (CBS rating ÷ 5) + 40 × chance of MISSING the bar
    - CBS half frozen since Aug 29 → every move is the machine reacting to a game; the bars are ours — say so
  - The ten: Norvell 91.2 · Locksley 90.7 · Aranda 76.0 · Beamer 73.6 · Vincent 72.6 · Swinney 70.5 · Mason 69.2 · O'Brien 68.0 · Schiano 67.9 · Creighton 67.5
  - Into the ten
    - Derek Mason, Middle Tennessee, #17 → #7 (+8.0): lost 23–13 at Jacksonville State; six wins is the bar and the sim gives him 35%
  - Out of the ten
    - Luke Fickell, Wisconsin, #9 → off the list: WON 24–20 at Penn State as a two-touchdown dog. CBS 5.0 keeps him rated, the machine keeps pulling him off the board
  - Order changes inside the ten
    - Locksley #2 (+12.9): lost 54–3 at home to UCLA — the worst loss on the board; bowl odds 53% → 20%
    - Beamer #8 → #4 (+5.0): lost 49–18 at Alabama; seven wins is the bar, 45% to get there
    - Swinney #3 → #6 (−4.6): won 24–10 at Cal — the third straight win, but nine wins is the bar and he is at 17%
    - Schiano #5 → #9 (−5.2): 58–7 over Howard, an FCS game — the move is the new rule reading Rutgers' September better
    - Aranda #4 → #3 (+1.0): beat Colorado 23–13, third straight win; seven wins is the bar, 60%
  - Knocking: Deion Sanders #11 (13–23 at Baylor) · Belichick #12 · Venables #13 (13–41 at Georgia; eight wins is the bar, 33%) · Riley #14 (lost to Oregon; nine wins is the bar, 33%)
  - Norvell still #1 at 91.2: beat Central Arkansas 34–7 (an FCS game, no rating move); eight wins is the bar, 22%
  - Card coaches: DeBoer (off the board — 49–18 over South Carolina) at Mississippi State; Campbell (Penn State, year 1) is not on the list despite the Wisconsin loss; Franklin (Virginia Tech, year 1, 3–1) and Narduzzi (Pitt, 4–0) off the board

- **Hot Seat (Corey's ten)** — PLACEHOLDER until his deck posts. Last week: Norvell · Doeren · Fran Brown · Leipold · Sean Lewis · Kinne · Schiano · Calhoun · Cumbie · Rahne

- **Superdog rules and standings**
  - ONE rulebook (Corey's): 3.5-point dogs or more · Superdog = any game, Giant Killer = unranked dog vs a Top 25 team · 5 for a cover, 5 + the spread for a win, 1 for a push
  - Standings: Man 39.5 · Machine 20 — CONFIRM his Week 4 with him
    - Machine Week 4: Georgia Southern +18.5 lost 42–28 → cover, 5 · Charlotte +10 lost 34–7 → nothing
    - Man Week 4 at the lines we recorded: Air Force +5.5 WON 36–33 → 5 + 5.5 = 10.5 · Iowa State +8 lost 31–17 → nothing. He grades at the line he took
    - Say: "he has an outright winner and the machine has none — 10.5 points in one pick is the whole gap"
  - How the machine picks: expected points under the rulebook (5 × chance to cover + spread × chance to win), home dog breaks ties
    - Guard rails: spreads 3.5 to 28, and the machine skips the games where its own number is furthest from the posted spread

- **Superdog picks (Tuesday night's lines — the recording-day pull decides; both Sunday picks moved off the top)**
  - Machine Giant Killer: Boston College +21 at #21 SMU (road dog) — the machine has it SMU by 15
    - Sunday's pick, Clemson, went from +17.5 to +16.5 and is third on the board (machine has Miami by 13); next: UCF +12.5 at #20 Houston · Clemson +16.5 vs #4 Miami · Utah State +20.5 at #22 Boise State
    - Say the caveat: "the machine's number, not ours"
  - Machine Superdog: Charlotte +20.5 vs Memphis (home dog) — machine has it Memphis by 12
    - Sunday's pick, Buffalo, went from +15.5 to +13.5 and is second (machine has Western Michigan by 7.5); next: Wyoming +18.5 at North Dakota State · UCF +12.5 at Houston
  - Pitt +3.5 at Virginia Tech is ON OUR CARD Friday, and the machine has Pitt as the favorite by a hair; Auburn +7 at Tennessee is also on the card
  - Corey's picks: PLACEHOLDER until his deck posts
