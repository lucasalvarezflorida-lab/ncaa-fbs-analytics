# Episode 3 — Week 2 · "Man vs Machine" podcast notes

Status (Mon Sep 7, evening): Week 1 graded through Sunday; **SMU @ Florida
State kicks tonight** (7:30 ET) — the receipts slide grades it by itself
after Tuesday's 7:30 AM refresh (it reads the final from the CFBD cache).
Week 2 card is set: Ohio State–Texas, Oklahoma–Michigan, Arizona State–Texas
A&M, Arizona–BYU, Alabama–Kentucky. Lines below are the Mon Sep 7, 5:51 PM ET
pull — re-pull before recording (`edge_report.py --week 2 --view ml
--publish`, then `make_episode_deck.py`). The AP poll in the deck is still
the Week 1 poll; the Week 2 poll lands Tuesday and the deck picks it up from
the cache automatically.

Format rule (Lucas, 9/7): the deck stays the Ep2 template — lean. Everything
we say on air lives HERE. Every slide bullet and key gets its backing below.

---

## Segment 1 — Week 1: the receipts

Frozen Ep2 calls (recorded Tue Sep 1) vs finals vs the last pre-kick line
(the Fri 5 PM pull for the weekend games; the Mon 9:25 AM pull for SMU–FSU).
"Off by" = distance of each side's line from the actual margin.

| Game | We called | FINAL | Our line | Close | Off by (us / market) | Closer |
|---|---|---|---|---|---|---|
| Baylor vs Auburn | Auburn 33–27 | **Auburn 17–16** | AUB −5.5 | AUB −7.5 | **4.5** / 6.5 | machine |
| Clemson at LSU | LSU 30–21 | **LSU 51–10** | LSU −9 | LSU −10 | 32 / **31** | market (barely) |
| Louisville vs Ole Miss | Ole Miss 31–25 | **Ole Miss 41–38** | MISS −6.5 | MISS −6.5 | 3.5 / 3.5 | tie |
| Wisconsin vs Notre Dame | ND 34–13 | **ND 41–13** | ND −21 | ND −20.5 | **7** / 7.5 | machine |
| SMU at Florida State | FSU 27–26 | *tonight* | FSU −0.5 | SMU −2.5 | — | — |

Four graded: machine total miss **47.0**, closing market **48.5** — machine
closer in 2, market in 1, one dead tie. Two weeks in: machine 117.0 vs
market 118.5 across nine games. Still a coin flip with Vegas — which, for a
model that hadn't seen a 2026 snap until this week, is the whole point.

**Stated positions this week: 2–0.** Baylor +7.5 (a "1.5-point lean, not a
position") covered by 6.5; the **Monster Under on 59.5 cashed by 26.5 points**
(33 total). The three no-plays were all correct passes: Clemson +10 (our
"quibble") would have lost by 31; Ole Miss "machine = market" pushed nothing;
ND "watch, don't touch" — ND covered by 7.5, but we said don't touch.
**Paper record: stated leans 3–2 through two weeks** (Wk0 1–2, Wk1 2–0).

### Baylor vs Auburn — Auburn 17, Baylor 16 (Atlanta)

- **The number**: machine Auburn −5.5, market −7.5, actual Auburn by 1. We
  were 2 points closer than Vegas. The score call (33–27) was a total-side
  whiff — 60 projected, 33 scored — because projected scores ride the market
  total, and the market total was exactly what the Monster Under flagged.
- **Monster Under receipt**: 59.5 was a top-decile total; the game produced
  33. Say it plainly: "five years of closing lines said monster totals go
  under 55% of the time; this one went under by 26."
- **What the keys said vs what happened**:
  - Auburn "tempo without turnovers — install-week ball security": **failed,
    and they won anyway.** Auburn threw THREE interceptions (26-35, 259 yds).
    The install-week mistake we feared showed up exactly as predicted;
    Baylor couldn't cash it.
  - Baylor "attack the rebuilt secondary": half-right. Lagway went 27-54 for
    333 — volume, not efficiency (6.2 per attempt). Four new corners bent
    but held.
  - Baylor "keep Lagway upright": **failed** — Auburn's front produced 5
    sacks and 11 tackles for loss (the "top-10 DL talent" key on Auburn's
    side cashed). Baylor ran for 2.3 a carry (103 yds); Auburn 3.2.
  - Baylor "steal a possession with tempo": they lived on fourth down
    instead — **4-of-6 on fourth**, 7-of-22 on third. That's a desperate
    offense, not a tempo-stealing one.
  - Auburn "lean on the defense that didn't change": the Durkin carryover
    unit won the game — 16 allowed despite three gift possessions.
- **Machine reaction**: Auburn −0.9, Baylor +0.9. A one-point win at a
  5.5-point expectation is a modest underperformance; the ridge treats it
  as exactly that.

### Clemson at LSU — LSU 51, Clemson 10

- **The number**: machine LSU −9, market −10, actual LSU by 41. Everyone
  missed by 30+; the market was one point closer. The score call (30–21) got
  the winner and the shape, not the scale.
- **Kiffin's debut in one line**: 644 yards, 38 first downs, 36:09 of
  possession, 11-of-16 on third down. LSU ran for 309 at 5.3 a carry AND
  Leavitt threw for 335 (22-36). The "portal-built OL on a short runway" —
  the bet of the whole season — gave up zero sacks; LSU's defense took four.
- **Clemson's collapse in one line**: 145 total yards, 8 first downs,
  1-of-13 on third down, 1.5 yards per rush, 4 sacks taken. The "one unit
  that never stopped being Clemson" (Allen's defense) surrendered 644. The
  "pressure answers for Vizzina" key failed at the root — 14-22 for 105 net.
- **On air**: "We wrote that the loser burns a playoff mulligan. Clemson
  burned the mulligan and the tires." The honesty-box line that Clemson's
  offense was "just as new" turned out to be the understatement of the week.
- **Machine reaction**: LSU +3.8 (to #5), Clemson −3.8. With the ±28 margin
  cap, a 41-point win counts as a 28-point win — the cap is why LSU didn't
  vault to #2 off one game.

### Louisville vs Ole Miss — Ole Miss 41, Louisville 38 (Nashville)

- **The number**: machine −6.5, market −6.5, actual Ole Miss by 3. Both off
  by 3.5 — a literal tie with Vegas, and "agreement, not edge — no play" was
  the right call. The total (55.5) got obliterated: 79 points.
- **Chambliss vs Kienholz — both keys hit**: Chambliss 21-37 for 336 ("let
  him escape" — yes); Kienholz 18-29 for 307 at 10.6 a throw with ZERO
  turnovers. "Keep his menu short and let Brohm's system work" is exactly
  what Louisville did — the least-proven Brohm QB looked like the most
  efficient one.
- **The Louisville keys that failed**: "no coverage busts" — 41 allowed,
  336 passing; "win field position" — 9 penalties for 82 yards.
- **The Ole Miss keys that failed**: "interior line ends the run game" —
  Louisville ran for 162 at 4.2; "tempo Brohm into simple looks" —
  Louisville never turned it over. Ole Miss won on 3 sacks and two stops,
  and Golding's first game as the head man was a three-point sweat — which
  the honesty box said no preseason prior could price.
- **Machine reaction**: Ole Miss −0.7, Louisville +0.7.

### Wisconsin vs Notre Dame — ND 41, Wisconsin 13 (Lambeau)

- **The number**: machine ND −21, market −20.5, actual ND by 28. Machine
  half a point closer. **The score call nailed Wisconsin's 13 exactly**
  (34–13 called, 41–13 actual).
- **The tite-front key was the game**: "find counters vs a tite front built
  to erase the run-first pivot" — Wisconsin ran for **67 yards at 2.2 a
  carry**. The league's most veteran OL did not earn it. Joseph's
  dual-threat spark: 19-30 for 217, two turnovers.
- **ND's keys all hit**: zero turnovers; Carr 19-29 for 239 at 8.2 — "in
  rhythm, nothing forced" to the letter; 284 allowed with the explosives
  erased; and "no scoreboard mercy" — 41.
- **Machine reaction**: ND +1.4 → **#1 in our rankings** (27.3). AP has
  them #4.

### Superdog receipts — 0 for 2, both covered by a mile

- **★ Coastal Carolina +21 at West Virginia: lost 31–24.** Covered by 14
  (the machine's read that WVU was mispriced at −21 was dead right), but the
  superdog needs the outright win. Coastal threw for 373 and ran for 52 (1.9
  a carry), lost two fumbles, went 2-of-10 on third down. WVU ran for 281.
  The 21% outright shot missed; the 21 points stay on the table.
- **★ Washington State +23.5 at #17 Washington: lost 24–10.** Covered by
  9.5. Wazzu: three turnovers, **0-for-9 on third down**. Washington took 12
  penalties for 130 yards and still won by two scores.
- **On air**: "Both dogs beat the number by double digits and earned zero
  points. That's the superdog game — the model can be right about the price
  and still get nothing, because we're paid on the win."

### SMU at Florida State — tonight, and a machine split worth staging

- **Frozen call (for grading)**: FSU 27–26, FSU 52%, machine FSU −0.5.
- **The in-season machine has already moved**: FSU −2.1 for beating New
  Mexico State by only 17 (its rating implied ~27), so the live machine now
  says **SMU by 1.4** — the RED flag would be off today.
- **Market**: opened SMU −3, closed **SMU −2.5** (FSU +124) — the market
  moved a half point *toward* FSU while our machine moved away from it.
- **How to grade it Tuesday**: the frozen call is the one on the record.
  Whichever way it goes, the story is the split: "the machine we recorded
  with picked FSU; the machine we have now picks SMU; the market moved toward
  FSU. One night, three opinions."

---

## Segment 2 — The machine after Week 1 (Our Rankings tab)

*Slide 1 of the deck is now "Our Top 25" — built from ratings_current_2026.json
at deck time (rating, Δ vs preseason, AP column, and a footer with the biggest
machine-vs-voters splits). It refreshes itself every rebuild.*

50 rated games in. **Top 10**: 1 Notre Dame 27.3 · 2 Texas 25.8 · 3 Georgia
24.8 · 4 Ohio State 24.6 · 5 LSU 23.8 · 6 Miami 23.2 · 7 Indiana 22.3 ·
8 Oregon 21.9 · 9 Alabama 21.1 · 10 Texas Tech 20.0.

Machine vs the AP voters (the weekly Man vs Machine column): Ohio State AP
#1 / machine #4 (−4.1 after Week 1); LSU AP #11 / machine #5; Notre Dame
machine #1 / AP #4.

Biggest movers: UMass +7.4, Nevada +6.5, San Jose State +4.9, UCLA +4.8,
Tulsa +4.8, NDSU +4.7 · Rutgers −7.4, Western Kentucky −6.5, Cal −4.8,
Oklahoma State −4.8, Jax State −4.7, Michigan −4.3, Hawai'i −4.3.

How to explain the update on air: "Preseason FPI is worth about three games
of evidence — that's what the backtest said. So after one game a team moves
roughly a quarter of the way toward what it just showed you. By November the
games run the machine, not the July guess."

### Machine housekeeping — two blind spots to say out loud this week

1. **The cap punishes blowouts of bad teams.** Margins are capped at ±28
   before the update (pre-registered, tuned on 2021–24). Ohio State beat Ball
   State 56–3; the machine expected ~48 (28.7 + 17.3 + 2.5 home), counted it
   as a 28-point win, and docked the Buckeyes **4.1 points** for winning by
   53. Same mechanism: Oregon −3.4, Oklahoma −1.8, Texas −1.1, Texas A&M
   −1.0. It's a bookkeeping artifact, not a judgment — and it is why the
   machine's Ohio State–Texas number is 3 points more Texas than everyone
   else's. We don't change pre-registered rules mid-season; the fix (cap the
   *residual* instead of the raw margin) goes on the postseason backtest list.
2. **FCS games are invisible.** Only games between two rated FBS teams enter
   the update, so Arizona State's 70–7, BYU's 63–7, Arizona's 35–7 and
   Kentucky's 45–13 changed nothing — those four ratings are still the July
   prior. The market saw those games; we didn't. (It cuts the other way on
   the superdog board — see Buffalo below.)

---

## Segment 3 — Week 2: the card

Machine line = our rating gap + 2.5 for the home team, then the empirical
margin curve (σ 15.9) turns the margin into a win probability. Projected
scores lay the machine margin over the *market* total (we have no totals
model — say so). Superdog EV = P(dog wins outright) × spread.

| Game (kick, ET) | Machine | Market (DK / Bov) | Score call | Machine win % | Read |
|---|---|---|---|---|---|
| Ohio State at Texas (7:30) | TEX −3.7 | TEX −1.5 / −2 · O/U 48.5 | Texas 26–22 | TEX 60% | agreement once you strip the cap artifact — no play |
| Oklahoma at Michigan (12:00) | OU −1.9 | OU −5.5 / −5.5 · O/U 43.5 | OU 23–21 | MICH 46% | **lean Michigan +5.5** — widest gap on the card (11.6 pp) |
| Arizona State at Texas A&M (12:00) | TAMU −16.7 | TAMU −14.5 / −14 · O/U 51.5 | A&M 34–17 | TAMU 85% | agreement — no play |
| Arizona at BYU (3:30) | BYU −8.4 | BYU −7.5 / −7.5 · O/U 50.5 | BYU 29–21 | BYU 70% | machine = market — no play |
| Alabama at Kentucky (3:30) | BAMA −13.2 | BAMA −10.5 / −10.5 · O/U 49.5 | Bama 31–18 | BAMA 79% | 2.7 to Alabama — quibble, not a position |

Reference column ("the man uses ESPN FPI"): ESPN's live FPI has Ohio State
28.7 / Texas 26.9 (Texas −0.7 at home), Oklahoma 18.8 / Michigan 15.9 (OU
−0.4), Texas A&M 20.0 / Arizona State 4.8 (−17.7), BYU 13.1 / Arizona 7.2
(−8.4), Alabama 20.1 / Kentucky 5.4 (−12.2). SP+ 2026: Ohio State #1, Texas
#6, A&M #9, Oklahoma #11, Alabama #13, Michigan #15, BYU #21, Arizona #31,
Kentucky #47, Arizona State #51.

No Monster Under this week: the top-decile threshold is 58.5 and none of
our five totals (43.5 to 51.5) is close. Say that — "the tool has nothing to
say on this card, which is the tool working."

---

### Ohio State at Texas — Sat Sep 12, 7:30 ET, DKR (Austin)

**The arithmetic.** Texas 25.8 (machine #2) vs Ohio State 24.6 (#4); +2.5
for Austin → Texas by 3.7 → 60% on the curve → fair Texas −150 / Ohio State
+150. Market: DK Texas −1.5 (−120 / +100), Bovada −2; total 48.5. Score call
26–22 is that 3.7 laid over 48.5.

**Why the machine is 2 points "too Texas" — the cap.** In July the same two
ratings were Ohio State 28.7 / Texas 26.9 → *Texas by 0.7* at home. Week 1
moved Ohio State −4.1 (56–3 capped to 28 against a −17 team = a 20-point
"miss") and Texas −1.1 (59–7 capped, Texas State a −4 team). ESPN's live FPI
still says Texas by 0.7; the market says 1.5. Our 3.7 minus the artifact is
the same pick'em-plus-home-field everyone has. **No position, and be the
first to say why.**

**Stakes (slide bullets, backed).**
- *Rematch of the year*: Ohio State beat Texas 14–7 in last year's Columbus
  opener and 28–14 in the 2024 CFP semifinal (AT&T Stadium). Texas hasn't
  beaten Ohio State in this three-game run; Arch Manning is almost certainly
  in his final college season (the deep dive: "Arch likely leaves after this
  year").
- *One coordinator gamble each*: Ohio State hired **Arthur Smith** (Falcons
  HC, Steelers OC) after Hartline left for USF — first-year college OC, and
  the scouting file's own flag is "NFL-to-CFB transitions are not
  automatic." Texas replaced Pete Kwiatkowski with **Will Muschamp**, whose
  last top-10 defense was 2014, on a unit that outranked Sark's offense two
  years running — "the single riskiest coordinator hire in the league."
- *Continuity*: Texas 72% of offensive production back (CFBD PPA), 22
  portal adds — Coleman (No. 1 portal WR), Smothers (No. 2 RB, 4.4 yards
  after contact), Biles (No. 3 LB), Siani (No. 3 OT), Brown (No. 5 RB).
  Ohio State 68% back on offense, 17 adds — but **two of nine every-game
  defensive starters return** (McClain, Mathews); three defenders went in
  the first 11 picks. Eight defensive transfers: Russaw and Smith (Alabama),
  Moore (Duke), Little (FSU), Kelly (Georgia).
- *Week 1*: Ohio State 56–3 Ball State — 671 yards, Sayin 21-of-25 for 320
  and 3 TD, Bo Jackson 83 on 9 carries, 237 rushing at 6.8; but **9
  penalties for 81** and 5-of-11 on third down. Texas 59–7 Texas State — 516
  yards, Arch 20-of-27 for 305, 4 TD, 1 INT, Coleman 2 TD, 11-of-15 on third
  down, a defensive score; but **349 yards and 18 first downs allowed** to a
  Sun Belt team.

**COACH / QB / ROSTER (the band).** Ohio State: Day year 8, Smith OC,
Patricia year two (back-to-back No. 1 SP+ defenses). Sayin year two —
first nationally in success rate as a freshman, "trained-wheels version."
Texas: Sarkisian year 6, Muschamp DC. Arch year two as the starter, Heisman
favorite; "lone remaining flaw is accuracy throwing on the run."

**Ohio State keys, explained.**
1. *Make Arthur Smith's run game real.* Smith's NFL identity is wide zone
   plus play-action; 2025 Ohio State was "slow-tempo, short-throw efficiency
   ball" that died in the two games that mattered. 237 at 6.8 vs Ball State
   is the first data point; against Texas's front (Simmons, Geffrard, Biles)
   it's the test. If the run game travels, Sayin plays on schedule.
2. *Sayin-to-Smith vs the back end.* Jeremiah Smith: 2,558 yards, 29 TD in
   two seasons — "the best QB-WR axis in the sport." Texas's secondary
   (McDonald, nickel Littleton, portal CB Mascoe, sophomore Kade Phillips)
   held this offense to 14 last year under Kwiatkowski; same players, new
   caller.
3. *Prove the eight-transfer defense.* Two of nine starters back; the
   sophomore wave (Grady, Pettijohn, Sanchez, Roker) plus the transfers meet
   Coleman/Wingo/Mosley/Smothers — "the deepest skill corps in the sport."
   Ball State managed 165 yards; that told us nothing.
4. *Urgency.* Connelly's sharpest point: the schedule and defensive turnover
   might *force* the urgency that's been missing. Nine flags in Week 1 is
   the discipline note.

**Texas keys, explained.**
1. *Arch on the move.* Sark's 2026 wrinkle is designed Manning movement;
   accuracy on the run is the one flaw. Patricia's multiple front disguises
   coverage shells — that is exactly the thing that punishes a QB throwing
   late off movement.
2. *Protect the interior.* The 2025 story: OL regression and drops, not
   Manning, sank a preseason No. 1 (offensive SP+ slid from 6th to 30th
   since 2023). Ohio State's front is now Russaw, James Smith and the
   sophomores. Texas allowed 1 sack in Week 1.
3. *Explosives over efficiency.* Patricia's defense "rally-tackles and
   squeezes explosives"; Texas's edge is matchup wins at every skill spot.
   The game is the big-play count, not the drive count.
4. *Muschamp's first real test.* 349 to Texas State is the flag. Simmons (12
   sacks in 2025) and Biles (15 TFL, 4.5 sacks at Pitt) are the two players
   who can make Sayin uncomfortable early.

**Honesty box on air.** "Three numbers: we say Texas by 3.7, Vegas says 1.5,
ESPN says 0.7. Three points of ours is the cap doing bookkeeping on a 56–3
game. This is a pick'em plus home field. We have no position, and if we're
honest, nobody should."

---

### Oklahoma at Michigan — Sat Sep 12, 12:00 ET, Michigan Stadium

**The arithmetic.** Oklahoma 16.0 (#12) vs Michigan 11.6 (#21); +2.5 for
Ann Arbor → Oklahoma by 1.9 → Michigan 46% → fair OU −118 / Michigan +118.
Market: DK Oklahoma −5.5 (−218 / +180), Bovada −5.5; total 43.5. Score call
OU 23–21. **The machine has Michigan at 46%; the market has 34% — 11.6
points of win probability, the widest gap on the card (EDGE_FLIP flag).**

**The line story.** Michigan opened −1.5, was first-seen in our ledger at
−2.5 on Aug 18, and is now **+5.5** — an eight-point swing, seven of it
after Saturday's 13–12 escape against Western Michigan. Our machine moved
Michigan −4.3 for the same game (expected ~22-point win, got 1) and
Oklahoma −1.8 (the cap on 51–0). Preseason the machine had *Michigan* by 0.6
at home; now Oklahoma by 1.9. So both moved the same direction — the market
just moved 7 and we moved 4.

**Stakes.**
- *The market re-priced a program on one game.* WMU had the ball for 40:08;
  Michigan 19:52 of possession, **three turnovers** (two fumbles, an
  Underwood pick), 9 penalties for 80, 3-of-10 on third down, 276 total
  yards. Underwood 12-of-22 for 170, 1 TD, 1 INT, plus 47 rushing yards on 9
  carries. Buchanan (Utah transfer) 126 receiving yards — the entire passing
  game.
- *Two rebuilds at opposite speeds.* Michigan: Sherrone Moore fired for cause
  Dec 10 (arrested and charged days later); **Kyle Whittingham** hired Dec
  26 after the DeBoer pursuit fizzled — 21 seasons, 177 wins at Utah, never
  coached east of the Rockies. He brought OC Jason Beck (top-6 Utah offense
  around dual-threat Devon Dampier), DC Jay Hill (from BYU), OL coach Jim
  Harding and three Utah starters (DE John Henry Daley — back from an
  October Achilles — DT Lea'ea, nickel Snowden) plus WR Buchanan. Oklahoma:
  Venables year five, calling the defense himself since 2025, when it was the
  SEC's best (4th in SP+); Arbuckle's Air Raid in year two.
- *The QBs.* Underwood: No. 1 recruit in the 2025 class, 506 non-sack
  rushing yards on 68 carries as a freshman. Mateer: returned for a senior
  year after rebuilding his throwing motion post-thumb injury; 2025 was 62%
  completions, 14 TD / 11 INT through the injury; Week 1 11-of-17 for 225, 3
  TD, 0 INT vs UTEP.
- *Payback.* Oklahoma 24, Michigan 13 in Norman last September (Week 2,
  2025). The deep dive's Michigan prediction was 8–4 "competitive in
  everything" — a home loss to open the era makes the floor the story.

**COACH / QB / ROSTER.** OU: Venables yr 5; Mateer RETURNS; 63% back, 16
adds — five OL transfers (E'Marion Harris from Arkansas), RB Avant (CSU), WR
room rebuilt around Sategna with Trell Harris (UVA), Livingstone (Texas),
TEs Hansen (Florida) and Beers. Michigan: NEW Whittingham; Underwood RETURNS;
69% back, 17 adds (the Utah pipeline). Michigan's out-transfers included
three QBs (Warren, Davis, Keene) — Underwood is the whole enterprise.

**Oklahoma keys, explained.**
1. *Mateer's legs vs Hill's sim pressures.* Hill's defense (BYU 2025: top-20
   havoc, "blitzes hit home because the back end holds") shows pressure and
   drops out; the designed QB run (Mateer 8 rushing TD in 2025) is the
   built-in answer, and it's the part of his game the hand injury never
   touched.
2. *The five-transfer OL.* 2025 OU ran for the 124th-best yards per carry in
   the country "which is nearly impossible with this talent level." 170 at
   4.4 vs UTEP proved nothing. Michigan's DL two-deep (Pierce, Daley if
   healthy, Lea'ea) is "championship-grade" per the scouting file.
3. *Erase the bad-QB day.* Venables' back seven — Guillory, Eli and Peyton
   Bowen, Kip Lewis, Heinecke (eligibility via injunction) — vs a QB coming
   off 12-of-22 with a pick. The 2025 identity: havoc without busts.
4. *Hidden yards.* Week 1: 115 punt-return yards, a defensive touchdown, 4
   sacks, 10 TFL. At noon on the road a 2-point machine number becomes a
   cover in the return game.

**Michigan keys, explained.**
1. *Own the ball.* 19:52 of possession is disqualifying against a real
   opponent; Beck's Utah offense was built on long drives and the nation's
   best red-zone TD rate. Zero gifts — three turnovers vs a MAC team is the
   Week 1 sin.
2. *Run Underwood like Dampier.* Dampier carried it about twice as often as
   Underwood did in Week 1 (9 carries, 47 yards). Connelly's question for
   the season is whether Beck builds Dampier's offense or a conventional one
   around a five-star arm; against Venables, the legs are the safer bet.
3. *Receiver No. 2.* Buchanan 126, everyone else 31 combined. Andrew Marsh
   (sophomore, "budding star") has to be a real target or Venables squeezes
   one side of the field.
4. *Hill's defense without the busts.* Held WMU to 221 yards and 4.2 per
   pass; the scouting file's warning is "boom-bust by design — explosive
   concessions when the pressure loses." Mateer's Air Raid is designed to
   find those.

**Honesty box on air.** "The market moved seven points on one MAC game; the
machine moved four. That three-point gap is the whole edge, and it's a bet
that 13–12 was noise — about a first-year head coach and a year-two
quarterback the July prior can't see. The backtest never paid us for chasing
chaos. Lean Michigan +5.5 as research, not a position." Note for the
superdog segment: Michigan +5.5 vs #10 Oklahoma is fifth on the Giant Killer
board (EV 2.5) — it's a lean on the spread, not the outright.

---

### Arizona State at Texas A&M — Sat Sep 12, 12:00 ET, Kyle Field

**The arithmetic.** Texas A&M 19.0 (#11) vs Arizona State 4.8 (#48); +2.5
for Kyle Field → A&M by 16.7 → 85% → fair −560 / +560. Market: DK A&M −14.5
(−625 / +455), Bovada −14; total 51.5. Score call A&M 34–17. Gap: 2.2 points
in A&M's favor — agreement on a two-touchdown spread.

**Zero 2026 evidence in this number.** ASU beat Morgan State (FCS), A&M
beat Missouri State (FCS) — neither game entered the update. A&M's −1.0 is
the cap on 50–0 (Missouri State is rated, barely, at −9.3; expected ~33).
ASU's rating is the July prior to the decimal.

**Stakes.**
- *The post-Leavitt reboot*: Sam Leavitt left for LSU in the spring portal
  (he threw for 335 in Baton Rouge on Saturday). ASU returns 16% of its
  offensive production — least on this card — 11 of 34 regulars, 24
  transfers in. Cutter Boley (Kentucky) won a four-way derby over Keene,
  Dyer and Fette; his debut: **21-of-27, 387 yards, 6 TD** (Morgan State;
  ASU 681 total yards, 70 points, 4-of-5 on fourth down).
- *A&M's lines*: six of the top seven OL and five of seven DL gone; four
  projected transfer OL starters with 42 combined SEC starts; five DL
  transfers headlined by Ryan Henderson (SDSU) and Anto Saka (Northwestern,
  12.5% pressure rate). Two new coordinators: Holmon Wiggins (OC), Lyle
  Hemphill (DC). Week 1: 505 yards, 236 rushing at 5.0, **43:03 of
  possession**, Reed 21-of-30 for 233 and 2 TD, 0 INT; Missouri State held
  to 67 yards. But 8 penalties for 75.
- *Reed's profile*: one of three SEC QBs with 3,000 passing and 550 rushing
  in 2025 (Chambliss, Pavia the others) — and seventh in the league in QBR
  because of 12 INT, 4 fumbles, a 15th-of-16 catchable-ball rate, and 0 TD /
  4 INT across the two losses.
- *Why it's on the card*: SEC–Big 12 crossover at noon, a 2024 Big 12
  champion's rebuild against an 11-win team whose 2025 schedule was
  "schedule-flavored" (CBS). ASU then plays Kansas at Wembley on Sept 19.

**COACH / QB / ROSTER.** ASU: Dillingham yr 4 ("develops QBs regardless of
the name"); Boley NEW; 16% back, 24 adds (Omarion Miller from Colorado, Reed
Harris from BC, edge Jalen Thompson from Michigan State). A&M: Elko yr 3,
GM Derek Miller, No. 1 2027 recruiting class; Reed RETURNS; 73% back, 19
adds (Horton WR from Alabama, Gibson CB from Tennessee, Formby OT from
Alabama, Saka).

**Arizona State keys, explained.**
1. *Tempo the transfer DL.* Dillingham's tempo "stresses thin two-deeps";
   A&M's front is the one unit with no shared history. 4-of-5 on fourth
   down says he'll keep the foot down.
2. *Boley's second start vs disguise.* Elko's coverage rotates late in the
   down; the secondary is Ricks, Ratcliffe, Brooks plus portal CB Rickey
   Gibson. Six TDs against Morgan State is the résumé; this is the audition.
3. *Contain before you gamble.* Brian Ward's 3-3-5 is "undersized, fast,
   gambling" (#34 rush / #37 pass PPA allowed in 2025 — it worked, at a
   cost). Reed's designed red-zone run is what a light box concedes.
4. *Special teams.* ASU was #125 in 2025 and "actively leaking." At Kyle
   Field a +14.5 cover is a field-position problem.

**Texas A&M keys, explained.**
1. *Reed's ball security.* 12 picks; 4 in the two losses. The gambling
   defense wants the hero throw. 0 INT in Week 1 is the right start.
2. *Prove the portal OL.* Connelly's warning — "rebuilding a line through
   the portal is how otherwise-good teams die." 236 at 5.0 and 43 minutes
   of possession is the template: run it 45 times.
3. *Havoc from the new front.* Saka and Henderson vs a QB in his second
   start; Elko's signature is "steal one possession a game."
4. *Finish and stay clean.* 8 flags for 75 last week; the spread is 14.5,
   so style points are the whole grade.

**Honesty box on air.** "Two points apart on a fourteen-point spread is
agreement. Neither team has a 2026 snap in its rating — those FCS blowouts
were invisible to the machine. The thing the prior can't price is Reed's
turnover habit against a defense built to bait it. No play."

---

### Arizona at BYU — Sat Sep 12, 3:30 ET, LaVell Edwards Stadium (Provo)

**The arithmetic.** BYU 13.1 (#18) vs Arizona 7.2 (#37); +2.5 → BYU by 8.4
→ 70% → fair −239 / +239. Market: DK BYU −7.5 (−285 / +230; opened −6.5,
first-seen −7 on Sep 4), Bovada −7.5; total 50.5. Score call BYU 29–21.
Machine = market to within a point. Both ratings are the July prior — Utah
Tech and Northern Arizona are FCS, so 63–7 and 35–7 moved nothing.

**Stakes.**
- *Continuity kings*: BYU returns 79% of its offensive production (most on
  this card) and 177 starts (tops in the Big 12), 9 portal adds — "nobody
  retains like BYU." Arizona: 65% back, Fifita in year four (9,183 career
  yards, 73 TD — "the most undersold player in the West"), 11 defensive
  starters back for DC Danny Gonzales (21 different starters in 2025's
  injury lottery).
- *Provo's biggest home game* until Notre Dame in October: BYU went 12–2,
  lost only to Texas Tech (twice, by 49 combined) and the deep dive's season
  goals were "win the two biggest home games in program memory: Arizona
  Sept 12 and Notre Dame." Arizona "plays everybody" — its schedule is the
  connectivity tax the top three avoid.
- *The coordinator change is BYU's*: Jay Hill took the 3-3-5 to Michigan;
  Kelly Poppinga inherits ten rotation defenders (LBs Glasker and Esera,
  CBs Johnson and Alexander, S Satuala). The scouting file's BYU weaknesses:
  pass-catching proof, pass-rush conversion, the Hill departure.
- *Series*: BYU 24–16 (2021, Las Vegas), 41–19 (2024, Provo), 33–27 (2025,
  Tucson) — three straight.
- *Week 1*: BYU 63–7 — 521 yards, **308 rushing at 6.7**, Bachmeier 16-of-20
  for 198 and 3 TD, Eka 59, 9-of-11 on third down, 4 takeaways, 110 KR + 73
  PR yards, a defensive TD. Arizona 35–7 — 520 yards, Fifita 22-of-29 for
  262 and 2 TD, 206 rushing at 5.9, 5 sacks and 11 TFL on defense, NAU held
  to −7 rushing yards; but **3 turnovers** (two lost fumbles, a backup INT).

**COACH / QB / ROSTER.** Arizona: Brennan yr 3 ("stabilized a sinking
program"); Fifita RETURNS; leading rusher and top two receivers gone —
transfers Antwan Roberts (Marshall), Cole Rusk (Illinois), slot Gio
Richardson; 22 adds incl. Daylen Austin (Oregon), Matai Tagoa'i (USC). BYU:
Sitake yr 11; Bachmeier RETURNS ("the safest QB bet in the conference");
LJ Martin 1,300 yards behind four returning linemen and all-conference C
Bruce Mitchell plus Washington OT Paki Finau; top three pass targets gone
(Walker Lyons from USC, Kyler Kasper from Oregon are the replacements).

**Arizona keys, explained.**
1. *Attack Poppinga early.* First game plan as the coordinator; Fifita's
   quick game to the corners before the disguises settle.
2. *Front-six physicality.* The file's Arizona weakness is "front-six
   physicality vs the league's power runs"; BYU ran for 308 last week and
   Martin is a 1,300-yard back. If the run game isn't slowed, the
   play-action never has to be tested.
3. *Ball security.* Three giveaways vs NAU; BYU's defense made four
   takeaways and scored. Hill's old identity — "turnover manufacturing" —
   is what Poppinga inherited.
4. *Field position.* Arizona's hidden 2025 identity: the defense fed an
   inefficient offense great starting spots and Brennan's fourth-down
   aggression cashed them. A 7.5-point spread in Provo lives there.

**BYU keys, explained.**
1. *Run first, then punish.* Bachmeier's QB-run married to deep
   play-action "punished single-high all season." Arizona's secondary
   (Cole, Hunter, Austin, Tagoa'i) is "Big 12 top-tier" — the first one that
   makes him earn it.
2. *Martin and Eka behind the veteran line.* 6.7 a carry in Week 1; 177
   returning starts is the continuity edge in one number.
3. *Prove the receivers.* Glasker 65 yards and 2 TD, Kasper 42 — the
   replacements for the departed top three. The scouting file calls the
   skill-position ceiling "modest by top-10 standards."
4. *The hidden margin.* 183 return yards and a defensive score last week;
   against a team that turned it over three times, takeaways are the cover.

**Honesty box on air.** "Eight-four and seven-and-a-half — that's
agreement. Neither number has moved since July because both teams played
FCS opponents. BYU's 79% continuity is the most reliable fact on the card;
the thing we can't price is a first-time coordinator running the side of the
ball that made BYU the last two years. No play."

---

### Alabama at Kentucky — Sat Sep 12, 3:30 ET, Kroger Field (Lexington)

**The arithmetic.** Alabama 21.1 (#9) vs Kentucky 5.4 (#42); Kentucky gets
the 2.5 → Alabama by 13.2 → 79% → fair −380 / +380. Market: DK Alabama −10.5
(−410 / +320), Bovada −10.5; total 49.5. Score call Alabama 31–18. Gap 2.7 to
Alabama — right at the noise line. Alabama +1.0 after Week 1 (ECU is rated;
48–10 capped to 28 beat a ~23 expectation); Kentucky unchanged (Youngstown
State is FCS).

**Stakes.**
- *DeBoer's referendum, on the road, with a teenager*: Keelon Russell (No. 2
  overall prospect in the 2025 class) got the job over Austin Mack; DeBoer
  "deliberately skipped the veteran-QB portal market." Week 1: 18-of-30 for
  256, **0 TD, 0 INT** (Ryan Williams 130 yards); Alabama scored five
  rushing TDs, ran 49 times for 227, held the ball 38:53, and held ECU to 2
  rushing yards and 0-for-9 on third down. DeBoer has lost as many games in
  two years (8) as Saban did in his final five; Alabama lost its 2025 opener
  (at FSU).
- *Stein's anti-Stoops*: Will Stein (Oregon OC; built the transfer class
  while coordinating a CFP semifinal run) replaced Mark Stoops after 5–7.
  Kenny Minchey (Notre Dame) at QB — "accurate, mobile, unproven" — debuted
  18-of-27, **301 yards, 4 TD, 0 INT**, 11.1 per attempt. The line: six
  transfers averaging 6-5, 323 with 49 combined FBS starts (Lance Heard from
  Tennessee, Tegra Tshabola from Ohio State, Coleton Price from Baylor).
  Backfield: CJ Baxter (Texas, 48 yards and 2 TD) and Jovantae Barnes
  (Oklahoma); Jason Patterson 78 on 11.
- *Continuity, both sides the lowest on the card*: Alabama 26% of offensive
  production back (35% by the deep dive's measure — "dead last in the
  conference tier"), 17 adds; Kentucky 19% back, **31 adds** (most of any
  team we cover this week; 13 on defense incl. Florida S Jordan Castell).
- *The landmine*: the SEC deep dive listed "Kentucky Week 2" as one of
  Alabama's three early traps (with FSU Week 3 and South Carolina Week 4).
  Kentucky's last win in the series: 1997. Last meeting: Alabama 49–21 at
  Kroger (2023).

**COACH / QB / ROSTER.** Alabama: DeBoer yr 3, Wommack yr 3 (4-2-5 "swarm";
"maybe the best secondary in America": Zabien Brown, Dijon Lee, nickel Red
Morgan, Hubbard, Sabb; All-American edge candidate Yhonzae Pierre); Russell
NEW; six of the top seven OL gone, four of the top five interior DL gone
(transfers Thompkins from USC, Bingley-Jones, Green from Oregon). Kentucky:
Stein NEW; Minchey NEW; ten of 19 defensive starters back (Humphrey-Grace,
Bryant, Nichols, Grayton) — the receiver room is "the void" (TE Willie
Rodriguez the one sure thing; Kenny Darby 74 yards in Week 1).

**Alabama keys, explained.**
1. *Russell's first road start.* Zero passing TDs vs ECU; DeBoer's
   rhythm-and-spacing game wants the intermediate middle. The 2025 offense
   finished 36th in SP+ with the country's worst high-volume drop rate at
   WR1 — the scheme needs a QB who attacks, not one who survives.
2. *Run it 49 times again.* 227 yards, five rushing scores; the rebuilt OL
   vs Kentucky's returning front (plus 13 defensive transfers) is where an
   SEC road game is decided. Short-yardage/goal-line is the file's listed
   weakness — 5 rushing TDs is a good first answer.
3. *Wommack's secondary vs the void.* Minchey threw for 301 on Youngstown
   State's secondary; Brown/Lee/Sabb should make him hold the ball, and the
   Alabama pass rush (3 sacks Week 1) does the rest.
4. *Special teams.* 107th in 2025, projected 109th; SP+ ST −1.30 last year
   "actively lost them field position all season." A 10.5-point spread on
   the road dies in hidden yards.

**Kentucky keys, explained.**
1. *The mauling line.* Six transfers, 49 FBS starts, three all-conference
   honorees vs an Alabama interior that lost four of its top five tackles
   and patched with transfers. Baxter/Patterson/Barnes downhill; 205 rushing
   at 6.0 in Week 1.
2. *Minchey's profile.* Four TD, no picks, 11.1 a throw. Keep it clean
   against the best secondary in America and the spread stays live; a
   Wommack disguise pick is how it gets away.
3. *The defense is the strength.* "Veteran, solid, unspectacular" — ten of
   19 starters back plus Castell (2 TFL in Week 1). Make a redshirt freshman
   beat you from the pocket on third-and-long.
4. *Clean up the leaks.* 3-of-8 on third down and 6 penalties for 70 against
   an FCS team — those are the two stats that lose to Alabama.

**Honesty box on air.** "Thirteen-two against ten-and-a-half is 2.7 points to
Alabama — noise. And it comes with two hedges the prior can't price: a
redshirt freshman's first road start and a first-year head coach whose
rating has zero 2026 snaps in it. Quibble, not a position. The real
information arrives at 3:30."

---

## Segment 4 — Superdogs (one per category, computed from the live card)

Rule: dog wins outright → we bank the spread. EV = P(win) × spread from the
machine's win probability; boards exclude played games. Ranks are the AP
poll in the cache (Week 1 poll until Tuesday — re-check after the refresh).

**★ SUPERDOG (any game): Buffalo +10.5 at Florida International** — machine
45.5% (ML +340, market 22%), EV 4.8. Runners-up: Sacramento State +18.5 at
Fresno State (23%, EV 4.3), Washington State +17.5 at Kansas State (24%, EV
4.2), Southern Miss +32.5 at Auburn (12.5%, EV 4.1).

*The caveat to say out loud*: the machine has FIU −1 and the market has FIU
−10.5 — the biggest disagreement on the whole board. Why: Buffalo beat
UAlbany (FCS) 21–17, which the market saw and the machine can't (FCS games
don't enter the update), while FIU lost 19–9 at USF and *gained* 0.8 for
covering. So half the "edge" is a blind spot. It stays the pick because the
rule is the rule; the honest framing is "the machine likes a team it hasn't
watched yet."

**★ GIANT KILLER (vs an AP top-25 favorite): Arkansas +13.5 at #21 Utah** —
machine 33% (ML +400, market 19%), EV 4.5. Runners-up: Georgia Tech +12.5
vs #20 Tennessee (29%, EV 3.6), Utah State +26.5 at #17 Washington (13%, EV
3.4), Iowa State +14.5 at #22 Iowa (19%, EV 2.8), Michigan +5.5 vs #10
Oklahoma (46%, EV 2.5).

*Why Arkansas*: Utah is Morgan Scalley's first year with five new OL
starters and OC Beck gone to Michigan; the machine's Utah number is still
the July prior (66–14 over Idaho, FCS, didn't count) and Arkansas is a
near-total teardown under Silverfield (31–14 over North Alabama, also
uncounted). The market's −13.5 vs our −6.6 says the market has already
priced the Utah transition as smoother than our prior does. It's a 1-in-3
shot at 13.5 points — the best ratio on the ranked board.

*Week 1 superdog receipts to reference*: Coastal +21 covered by 14, Wazzu
+23.5 covered by 9.5, zero points banked. "Right about the price, paid on
the win."

---

## Pre-record checklist (Tuesday)

1. Confirm the 7:30 AM refresh ran (ratings_current_2026.json `as_of`
   Tuesday; 51 rated games if SMU–FSU counted).
2. Grade SMU–FSU in Segment 1 (frozen FSU −0.5 vs close SMU −2.5) and
   update the "stated leans" line only if it changes (it shouldn't — RED
   flag was research, not a position).
3. `python edge_report.py --week 2 --view ml --publish` then
   `python make_episode_deck.py` — re-check the superdog boards (the Week 2
   AP poll may move the Giant Killer) and the Oklahoma–Michigan line (it was
   still moving Monday).
4. Push: `python push_deck.py --pptx decks\2026_Week2_Episode3.pptx
   --file-id 1TxsZ9dG3JQ5yuHaPC-T10UZPq_WbH5rTXKU84GXzvUI` (the Ep3 Slides
   file, created Mon 9/7 in Lucas's Drive — NOT shared with Corey yet).

*Drafted 2026-09-07 from card_data_week2.json (Mon 5:51 PM ET pull),
ratings_current_2026.json, CFBD box scores, scouting_top25.json and the
conference deep-dive prep files. Machine-drafted — review before air.*
