# Ep5 · Week 4 — BOARDS

Outline notes: topic → the points → the facts under each point. Read the
level you need. Drafted Sun Sep 20 from the Sunday rebuild (157 rated games,
AP Week 4 poll). MACHINE-DRAFTED — review before air. Corey's sections are
placeholders until his deck updates (his file is read-only for us).
Betting-line context for this episode is kept out of this file on purpose -
it lives in the internal folder, which is not in the repo.

- **Receipts (Week 3)** — man vs machine
  - Margin miss, lower is better: Man 49.0 · Machine 50.5
    - Man closer on two (Tech 9 vs 11, South Carolina 11 vs 12), machine on two (Auburn 5.5 vs 6, LSU 13 vs 14), Louisville a dead tie at 9
  - Points off the FINAL SCORE (both teams' points added up): Man 77 · Machine 83
    - Corey closer on three (Tech 9 vs 11, Louisville 9 vs 13, Auburn 28 vs 30), the machine on two (South Carolina 16 vs 17, LSU 13 vs 14)
    - Per team (score_tracker.md): he was closer on 5 teams, the machine on 4, 1 tie (both had Mississippi State at 27)
    - Why he wins this one: the machine has no totals model — it predicts the margin, not the points — and four of the five games were shootouts; Corey's numbers ran higher (35–34, 34–28)
    - Florida 44, Auburn 39 was 28+ points off for both of us: everybody had it in the 50s
  - Corey's calls, read off his score slides (each number sits under that team's logo, his winner in green): Tech 35–24 · Louisville 35–34 · South Carolina 31–27 · Auburn 28–27 · LSU 34–28
    - CORRECTION to last week's notes: he had TEXAS TECH, not Houston — the "top number = home team" reading was wrong. We did not split on a winner all week
  - Winners: machine 2–3, man 2–3 — the same five picks (Tech, Louisville right · South Carolina, Auburn, LSU wrong)
  - Machine's season: 211.5 points off across 20 games (10.6 a game)
    - Man's season total needs his Weeks 0–2 calls re-read under the right convention — ask him for them
  - Game by game
    - Houston 26 at Texas Tech 28 — called Tech 33–20; our line −13, off by 11
      - Deserved Houston +4.9: Houston ran 77 plays to 61 and went 9-of-15 on third down
      - Tech won on six passes of 20+ in 29 dropbacks, four of them Hammond to K. Johnson
    - SMU 31 at Louisville 41 — called Louisville 30–29; our line −1, off by 9
      - Deserved Louisville +24.3 — the score flattered SMU
    - Mississippi State 41 at South Carolina 34 — called SC 32–27; our line −5, off by 12
      - Deserved Mississippi State +6.4; State is the season's biggest riser (+10.7 since July)
    - Florida 44 at Auburn 39 — called Auburn 27–26; our line −0.5, off by 5.5
      - Deserved Florida +9.3
    - LSU 24 at Ole Miss 32 — called LSU 32–27; our line LSU −5, off by 13
      - Deserved Ole Miss +6.3; Ole Miss 10-of-15 on third down, 6-of-11 on third-and-long, 4-for-4 in the red zone

- **The rating rule change — say it once, on the Top 25 slide**
  - What changed: the cap now limits how far a result can beat or miss EXPECTATION (28 points), not the raw margin
    - Old rule: Ohio State wins 59–3 as a 44.6-point favorite → counted as a 28-point win → read as a 16-point miss → Ohio State FELL 3.0, #1 → #6
    - New rule: 56 vs an expectation of 44.6 is +11.4 → a good day, as it should be
    - Backtested 2021–25: same accuracy, better calibration; decided Sep 14, date-gated to this week so Ep4's card stayed on the old rule
  - What it did to the board: Ohio State 25.0 → 29.1, Texas 25.0 → 28.6, Georgia 22.6 → 27.8, Notre Dame 24.8 → 27.7
    - Say: "most of the jump at the top is the rule, not Saturday — the weekly-change column strips the rule out"

- **Top 25 (machine)**
  - What the number means
    - Points better than an average FBS team on a neutral field — think Minnesota or NC State (both at 0); Colorado is exactly 0.0 today
    - Ohio State 29.1 = four touchdowns better than Minnesota; a line = the difference + 2.5 for home
    - July prior is worth three games; FCS games count nothing
  - The ten: Ohio State 29.1 · Texas 28.6 · Georgia 27.8 · Notre Dame 27.7 · Alabama 24.9 · Indiana 24.2 · Miami 23.7 · LSU 22.4 · Texas A&M 19.3 · Penn State 18.5
  - Risers (the week's games alone, rule held constant)
    - Ole Miss +2.7, #18 → #12: beat LSU by 8 when the machine expected to lose by 6.7 — a 14.7-point beat
    - Mississippi State +2.6, up seven to #18: won 41–34 at South Carolina as a 5-point dog; +10.7 since July, the biggest rise in FBS
    - Utah +2.2, up seven to #16: 33–0 over Utah State
    - Louisville +2.1, up five to #25: 41–31 over SMU, and the efficiency said it should have been 24
    - Penn State +1.8, up five to #10: 55–13 over Buffalo
  - Fallers
    - Texas A&M −5.3, the biggest drop in the 25: lost 31–21 at home to Kentucky as a 16.5-point favorite — a 31-point miss, capped at 28
    - South Carolina −2.4 (down five), LSU −2.0, USC −2.1 (42–35 at Rutgers as a 21.5-point favorite), Oklahoma −1.8 (down five: 14–6 over New Mexico)
    - Miami −1.7: won by 13 at Wake Forest as a 17-point favorite
    - Out of the 25: Missouri (#27), SMU (#29), Virginia (#37 — lost 38–27 at home to West Virginia as a 10.5-point favorite)
  - The LSU / Ole Miss question — expect it
    - LSU #8 (22.4), Ole Miss #12 (17.9), and Ole Miss just beat them
    - The rating is the whole body of work: LSU's 51–10 over Clemson is still in there; so is Ole Miss needing 41–38 to beat Louisville at home
    - The gap went from 9.2 to 4.5 in one game; a neutral-field rematch is LSU by 4.5
    - Say: "voters rank wins, the machine rates how well you've played — one more Saturday like that and they flip"
  - Voters vs us (AP Week 4)
    - Ohio State 7 vs our 1 · Ole Miss 4 vs 12 · BYU 9 vs 23 · Florida 21 vs 11 · Texas A&M 23 vs 9 · Oregon 20 vs 14
    - Ours not theirs: Oklahoma, South Carolina, Nebraska, Auburn · Theirs not ours: Iowa, Missouri, SMU, Houston
    - Agree on the new face: Mississippi State, their 24 and our 18
  - Corey's question: when does the record go into the number?
    - It never does directly — the machine grades every game against the spread it set, not the scoreboard
    - Each game: actual margin minus the expected margin, capped at 28; one week's surprise moves a team about a quarter of the way
    - A&M is the example: expected to beat Kentucky by 16.5, lost by 5 → a 21.5-point miss → −5.3
    - If A&M loses at LSU by about 6 (the machine's number), it goes 2–2 and the rating barely moves; lose by 20 and it drops another 3.5; win by 3 and it gains 2
    - Say: "a loss you were supposed to take costs you nothing — a win you were supposed to get by 17 and got by 3 costs you"
    - The record lives in two other places: the AP column, and the playoff sim's committee model (losses, strength of record, quality wins)
  - Playoff picture (the machine's simulator, 10,000 seasons from these ratings)
    - Texas 95% to make the field, Georgia 89%, Ohio State 87%, Notre Dame 86%, Alabama 82%
    - Miami 76%, with a 66% shot at the ACC title — its most likely season is 12–1 as champion; at 11–2 without the title it is in 71% of the time, at 10–3 without it 3%
    - Texas A&M 26%: the path is 9–3 with a top-25 win — Our Rankings say #9, the résumé says outside the twelve
    - Florida 44%, Ole Miss 55%, LSU 55%; the G5 bid runs through Boise State (31%) and James Madison (15%)
    - Say: "Our Rankings answer how good you are; the playoff column answers what you've done — both can be true about A&M"

- **Top 25 (Corey's)** — from his Week 4 deck (read Wed 9/23)
  - His top ten: Texas · Georgia · Notre Dame · Indiana · Miami · Alabama · Tennessee · Penn State · Ohio State · Ole Miss
  - 11–25: Utah · Florida · Texas Tech · LSU · Oregon · USC · BYU · Michigan · Texas A&M · Nebraska · Oklahoma · Miss State · Pitt · Iowa · Virginia Tech
  - Biggest splits vs ours: Ohio State his 9, our 1 · Tennessee his 7, our 14 · Texas A&M his 19, our 9 · Alabama his 6, our 5 (agree) · LSU his 14, our 8
  - Where we agree: Texas and Georgia top two; Mississippi State in (his 22, our 18); Indiana and Miami top seven
  - His moves: A&M 7 → 19 after Kentucky; LSU 8 → 14; Ole Miss 15 → 10; Oregon 22 → 15; Utah 17 → 11; four new: Virginia Tech, Iowa, Pitt, Miss State

- **Heisman board (machine)**
  - How it works: index = team factor × blended efficiency
    - Team factor = 0.5 + half the team's odds of 10+ wins; efficiency = 2026 PPA per play with 150 plays of 2025 as a prior
  - The five: Mensah 46.8 · Hoover 46.5 · Carr 46.2 · Sayin 45.4 · Dampier 33.4
    - Four quarterbacks inside a point and a half — the race tightened because the top two came back to the pack
    - Mensah −1.7: 30-of-34 at Wake but 220 yards and a second-half stall; per-play 1.13 → 0.84. Still 71-of-79, 11 TD, 0 INT
    - Hoover −0.6: per-play 1.42 → 1.02 on a bigger sample
    - Carr +1.8 and Sayin +2.3 are team factor: Notre Dame 92% for ten wins, Ohio State 52% → 66% under the new rule
    - Dampier +1.9, #6 → #5: Utah's ten-win odds 33% → 52%
  - Risers
    - Keelon Russell +3.8, #14 → #9: per-play 0.32 → 0.45
    - Dante Moore +2.1, #13 → #10 — off 84–0 over Portland State; he plays on this card
    - Avery Johnson +2.5, #18 → #14
  - Fallers
    - Marcel Reed −6.8, #17 → #20: 26-of-49 for 5.0 a throw against Kentucky — plays on this card
    - Kevin Jennings −5.8, #8 → #13: the Louisville loss
    - Arch Manning −3.9, #10 → #16: 0.21 per play, 18-of-37 against UTSA — the biggest name the machine is lowest on, and he plays on this card
    - Maiava −3.0, #5 → #6: all team factor — USC's ten-win odds fell to 9%
  - Card quarterbacks not on the board: Stockton (38-of-45, 9 TD, 0 INT — the board is a candidate list, add him), Philo, Brandon
  - Non-QB watch: Jeremiah Smith, Malachi Toney (1.20 per play), Jadan Baugh (458 yards, 8 TD — on this card)

- **Heisman (Corey's five)** — from his deck: 1 Michael Hawkins Jr (WVU, new) · 2 Nate Sheppard (Duke) · 3 Kamario Taylor (Miss State) · 4 Jayden Maiava (USC, down from 1) · 5 Lincoln Kienholz (Louisville)

- **Hot Seat (machine)**
  - How the score works (0–100): 60 × (CBS rating ÷ 5) + 40 × chance of MISSING the bar
    - CBS half frozen since Aug 29 → every move is the machine reacting to a game
  - Into the ten
    - Bryant Vincent, UL Monroe, #13 → #7 (+7.1): lost 38–35 at home to SE Louisiana, an FCS team; five-win odds 35% → 17%
    - Chris Creighton, Eastern Michigan, #15 → #10 (+6.1): 54–10 at Wisconsin, 1–3; six-win odds 30% → 15%
  - Out of the ten: Derek Mason (#9 → #17), Dave Doeren (#10 → #15)
  - Order changes inside the ten
    - Locksley #5 → #2 (+5.0): lost 35–26 at home to Virginia Tech; bowl odds 65% → 53%
    - Swinney #7 → #3 (+4.6): BEAT North Carolina 28–20 and still rose — nine wins is the bar and he is at 5% to get there
    - Fickell #4 → #9 (−5.0): 54–10 over Eastern Michigan; 80% to make six wins — the machine says he is fine, CBS 5.0 keeps him on the board
    - Beamer #6 → #8 (−3.0) after LOSING at home to Mississippi State: the new rating rule lifted South Carolina's number more than the loss cost — say that, it sounds wrong otherwise
    - Schiano #2 → #5: 0–3, but he kept it to 42–35 against USC
  - Knocking: Belichick #11 · Deion Sanders #22 → #12, the biggest jump on the board (+12.8: lost 41–7 at Northwestern, six-win odds 63% → 30%) · Riley #13 (+6.1 — 9% for the nine wins, on this card) · Venables #14 (on this card, at Georgia)
  - Norvell still #1 at 91: lost 50–36 at Alabama, 22% for eight wins
  - Caveat, say it: the bars are ours; the CBS ratings are three weeks old

- **Hot Seat (Corey's ten)** — from his deck: Norvell (FSU) · Doeren (NC State) · Fran Brown (Syracuse) · Leipold (Kansas) · Sean Lewis (SDSU) · Kinne (Texas State) · Schiano (Rutgers) · Calhoun (Air Force) · Cumbie (La Tech) · Rahne (ODU)

- **Superdog rules and standings**
  - ONE rulebook now (Corey's, settled Sat 9/19): 3.5-point dogs or more · Superdog = any game, Giant Killer = unranked dog vs a Top 25 team · 5 for a cover, 5 + the spread for a win, 1 for a push
  - Standings: Man 29 · Machine 15 — CONFIRM his Week 3 with him
    - Machine Week 3: Sacramento State +27.5 lost 31–10 → cover, 5 · Utah State +28.5 lost 33–0 → nothing
    - Man Week 3 at the lines we recorded: FIU +7 lost 16–10 → cover, 5 · Colorado State +18 lost 41–23 → a PUSH, 1. He grades at the line he took
  - How the machine picks now: expected points under the rulebook (5 × chance to cover + spread × chance to win), home dog breaks ties
    - Guard rails: spreads 3.5 to 28, and the machine skips the games where its own number is furthest from the posted spread
    - Why home dogs: they have won 27% outright this year, road dogs 13%

- **Superdog picks**
  - Machine Superdog: Charlotte +10 vs Louisiana (home) — the line came in four points since Sunday
    - Say the caveat: "the machine's number, not ours"
  - Machine Giant Killer: Georgia Southern +18.5 vs #25 Houston (home)
    - Next on the board: Iowa State +8.5 vs #15 Utah · Wake Forest +12.5 at #16 Louisville
  - Oklahoma +14 at #2 Georgia is fifth on the Giant Killer board — it's on our card, mention it
  - Corey's picks (his deck): Superdog Air Force +5.5 at Nevada · Giant Killer Iowa State +8 vs #15 Utah
  - Picks re-read off the recording-day pull (Wed 9/23, 17:09 UTC)
