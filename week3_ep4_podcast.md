# Episode 4 — Week 3 · "Man vs Machine" podcast notes

Status (Tue Sep 15, 6:18 PM MT, pre-record pull): Week 2 graded (5 of 5 plus both
superdogs), the machine re-solved on **100 rated games** (Sun 12:21 PM MT),
the workbook rebuilt, and the Week 3 AP poll is in (pulled from the wire;
CFBD hadn't attached it yet — the deck falls back to the hand-typed Week 3
list until the cache catches up). Lines are the Tue 6:18 PM MT pull:
**Houston at Texas Tech has a total (Bovada 53) and a moneyline**, so every
score call is filled in; DK has Tech −7.5 and South Carolina −4, and the
Monster Under line moved to 59.5 (State–South Carolina's 58.5 dropped out). Re-pull
once more before recording: `edge_report.py --week 3 --view ml --publish`,
`hot_seat_heisman.py --week 3 --refresh`, `make_episode_deck.py` — the market
numbers below move by the half point; the machine's lines don't. The full
Week 3 board (every rated game, with score calls) is the appendix at the end.

Format rule: slides carry the headline, this file carries the sentence.
Every slide line has its backing below, in deck order.

**Order below = the MERGED deck, slide by slide** (Corey's Ep4 order with
our current slides swapped in — decks/2026_Week3_Episode4_merged.pptx;
his blank divider slides are counted, so the numbers match the file — if
they drift, follow the section names). 2 Receipts · 3
Week 2 Winners and Losers · 4 Our Heisman board · 5 Corey's Heisman five ·
6 Our Top 25 · 7–11 Corey's Top 25 · 12 Hot Seat · 13 Corey's Hot Seat ten
· 14 Five Games, One Card · 16–49 the five games (a blank divider slide,
then his keys, our team slide, his keys, our team slide, his score, our
number) · 50 Superdog rules and standings · 51 Superdog picks · 52 Our
predictions. Kiffin's return to
Oxford closes the games.

---

## Slide 2 — Week 2: the receipts

Frozen Ep3 calls (recorded Wed Sep 9) vs finals vs the Friday 5 PM ET pull.

| Game | We called | FINAL | Our line | Close | Off by (us / market) | Closer |
|---|---|---|---|---|---|---|
| Ohio State at Texas | Texas 27–23 | **Texas 24–23** | TEX −3.5 | TEX −1.5 | 2.5 / **0.5** | market |
| Oklahoma at Michigan | Oklahoma 23–21 | **Michigan 17–10** | OU −2 | OU −5.5 | **9** / 12.5 | machine |
| Arizona State at Texas A&M | A&M 34–17 | **A&M 48–20** | TAMU −16.5 | TAMU −14.5 | **11.5** / 13.5 | machine |
| Arizona at BYU | BYU 28–20 | **BYU 28–17** | BYU −8.5 | BYU −7.5 | **2.5** / 3.5 | machine |
| Alabama at Kentucky | Alabama 31–18 | **Alabama 45–17** | BAMA −13 | BAMA −10 | **15** / 18 | machine |

**Machine 40.5, market 48.0 — closer in four of five.** Season: machine
161.0 vs market 167.0 across 15 games — the machine leads for the first
time. Two score calls were near-exact: Texas 27–23 vs 24–23, and BYU 28–20
vs 28–17 (BYU's 28 on the nose).

**Deserved margins (new — the efficiency layer).** Next to each final,
what the game looked like per play: Texas deserved +5.6 (won by 1) — the
machine's Texas −3.7 was the right read of the game; Michigan deserved +0.8
(won by 7) — Oklahoma −2 was two points off the deserved number; Texas A&M
deserved +15.1 (won by 28) — the machine's 16.7 was almost exactly the
efficiency; BYU deserved +16.4 (won by 11); Alabama deserved +22.4 (won by
28). Against the deserved margins the machine was off **23.6**, not 40.5.
Same caveat as Slide 6: we grade on the scoreboard, this is the explanation.

**Stated positions: 1–0.** Michigan +5.5 ("lean, research") won outright
17–10. The Alabama "quibble" (−13 vs −10.5) also covered by 18, but it was
called a quibble, not a position. **Season leans 4–2.**

### Ohio State at Texas — Texas 24, Ohio State 23

- **The number**: machine Texas −3.5, close −1.5, actual Texas by 1. The
  market's cleanest read of the week. Our 27–23 was three total points off.
- **The game**: Ohio State led 23–3 through three quarters (10, 10, 3) and
  Texas scored 21 in the fourth on three straight touchdown drives. Texas
  336 total yards; Arch 23-of-37 for 195, one touchdown, one pick, 5.3 per
  attempt; Smothers 74 and two scores. Ohio State 372; Sayin 17-of-32 for
  278, one and one; Jeremiah Smith 164; the run game 94 yards at 3.0.
- **Keys vs reality — Ohio State**: "make the run game real" FAILED (3.0 a
  carry); "Sayin-to-Smith" HIT (164); "prove the eight-transfer defense" hit
  for 45 minutes — three points allowed through three quarters — then 21;
  "play with pace, cut the flags" — four flags (hit), but the fourth-quarter
  offense scored zero, the same disease as the Miami quarterfinal.
- **Keys vs reality — Texas**: "Arch on the move" — 24 rushing yards and a
  fourth quarter that was the whole case; "protect the interior" — two
  sacks; "explosives over efficiency" FAILED (5.3 per attempt) and they won
  on efficiency instead (9-of-16 on third down); "Muschamp's first real
  test" — 23 allowed, then a shutout fourth quarter.
- **Machine reaction**: Ohio State +0.4, Texas −0.8 — a one-point loss at a
  3.7-point expectation is a small win for the machine's Ohio State. The
  voters went the other way by five spots.

### Oklahoma at Michigan — Michigan 17, Oklahoma 10

- **The number**: machine OU −2, close −5.5, actual Michigan by 7. Machine
  off by 9, market by 12.5. **Our lean, Michigan +5.5, won outright** — the
  first stated position to win a game outright this season.
- **The game**: Michigan 263 yards, 152 rushing at 3.7, 33:17 of possession,
  zero turnovers; Underwood 9-of-17 for 111 and no touchdowns — but 18
  carries for 87 and a score. Oklahoma 289; Mateer 17-of-33 for 189, one
  and one; 3-of-13 on third down; two turnovers; three sacks taken.
- **Keys vs reality — Michigan**: "own the ball" HIT (33 minutes, no
  giveaways); "run Underwood like Dampier" HIT — 18 carries, the most of his
  career; "find receiver No. 2" — nobody over 48 yards, and it didn't
  matter; "pressure without the busts" HIT — three sacks, 5.7 per pass
  allowed.
- **Keys vs reality — Oklahoma**: "Mateer's legs" — 45 yards, not enough;
  "the portal line has to prove it" FAILED (three sacks, 3.4 a carry);
  "erase Underwood's bad day" — they did (111 passing) and lost anyway;
  "win the hidden yards" FAILED — nine penalties for 76.
- **Machine reaction**: Michigan +1.6 (to #20, back in the AP at 19),
  Oklahoma −1.5 (to #15, AP 24). The market's seven-point swing on the WMU
  game was the overreaction; the machine's four-point move was closer.

### Arizona State at Texas A&M — A&M 48, ASU 20

- **The number**: machine −16.5, close −14.5, actual A&M by 28. Machine
  closer by two. The 34–17 call had the shape and not the scale.
- **The game**: A&M gained only 255 yards and scored 48 — two defensive
  touchdowns and four ASU turnovers (Boley 21-of-34 for 254, two and two;
  two lost fumbles). Reed 15-of-25 for 163 and three scores. The portal OL
  ran for 92 at 2.6.
- **Keys vs reality — A&M**: "havoc from the new front" HIT (four
  takeaways, two scores); "Reed's ball security" — one pick; "prove the
  portal OL" FAILED (2.6 a carry); "finish drives" — 3-of-12 on third down
  and it didn't matter.
- **Keys vs reality — ASU**: "Boley vs real disguise" FAILED (two picks);
  "tempo the transfer front" — 369 yards, four giveaways; Reed Harris 189
  receiving was the bright spot.
- **Machine reaction**: A&M +1.9 (to #9), ASU −2.3.

### Arizona at BYU — BYU 28, Arizona 17

- **The number**: machine −8.5, close −7.5, actual BYU by 11. Machine
  closer by one. **BYU 28 exact.**
- **The game**: Arizona led 17–14 at halftime and scored zero after. BYU
  365 yards; Bachmeier 16-of-26 for 217 and three scores, Kasper two of
  them; Martin 98 on 20. Arizona 327; Fifita 23-of-31 for 230, one and one;
  97 rushing at 3.1.
- **Keys vs reality — Arizona**: "attack Poppinga early" HIT (17 in the
  first half) and then the adjustments won; "hold the line vs Martin" — 98
  on 20, held; "ball security" — one pick; the second-half shutout is the
  story.
- **Keys vs reality — BYU**: "run first, then punish" HIT (148 at 4.9,
  three passing scores off it); "prove the new receivers" HIT (Kasper two
  TDs, Glasker 74); "win the hidden margin" HIT (zero turnovers).
- **Machine reaction**: BYU +0.5, Arizona −0.5.

### Alabama at Kentucky — Alabama 45, Kentucky 17

- **The number**: machine −13, close −10, actual Alabama by 28. Both way
  under; machine closer by three.
- **The game**: Alabama scored 45 on 343 yards with THREE turnovers
  (Russell 16-of-23 for 188, one and two) — a defensive touchdown and
  Kentucky's own three giveaways did the rest. Daniel Hill 104 on 18.
  Kentucky 209 yards, **1-of-14 on third down**, 63 rushing at 2.0.
- **Keys vs reality — Kentucky**: "the mauling line" FAILED completely
  (2.0 a carry, four sacks allowed); "Minchey keeps it clean" FAILED (a pick
  and 146 yards); "the defense is the strength" — 45 allowed, though three
  of Alabama's scores came off short fields.
- **Keys vs reality — Alabama**: "Wommack's secondary vs the void" HIT
  (146 passing allowed); "run it 49 times again" — 40 carries, 155 yards;
  "Russell's first road start" — two picks and a win; "special teams can't
  leak" — no leak.
- **Machine reaction**: Alabama +1.9 (to #6), Kentucky −3.2 (to #55).

### Superdog + Giant Killer receipts — 0 for 2 outright, 0 for 2 against the spread

| Pick | Line at pick | Machine / market P(dog) | FINAL | Spread | Outright | Points |
|---|---|---|---|---|---|---|
| ★ SUPERDOG — Buffalo +10.5 at FIU | +10.5 (ML +340) | 46% / 22% | FIU 33–20 | lost by 13, no cover | lost | 0 |
| ★ GIANT KILLER — Arkansas +12.5 at #20 Utah | +12.5 (ML +390) | 33% / 20% | Utah 43–10 | lost by 33, no cover | lost | 0 |

- **Buffalo**: the caveat we wrote came true — the machine liked a team it
  hadn't watched. FIU 540 yards (Kohl 367); Buffalo three turnovers,
  4-of-17 on third down, 2.4 a carry. FIU went +2.0 in the machine, Buffalo
  −2.4.
- **Arkansas**: 22-of-48 passing across two quarterbacks, 2.2 a carry; Utah
  +4.3 (to #21) and Arkansas −4.3. The machine's Utah number was the July
  prior; the market's −12.5 knew better.
- **Season: 0-for-4 outright, 2-for-4 against the spread, 0 points.** Say
  it: "two 20-percent shots and two 30-percent shots have all missed; the
  expected count of wins through four picks is about one, so we're one miss
  behind the math, not broken."

### Alert-tier receipts — Week 2

- **RED: South Florida +3 at Army WON 28–24** — the machine's outright pick
  cashed. RED dogs are **2–2 outright** on the season (UNC and USF won;
  Sacramento State and FSU lost).
- **YEL: 2–5 against the spread, 0–7 outright** — the Week 1 16–4 came back
  to earth exactly as the 49.7% backtest said it would. The big dogs (Wazzu
  +17.5, Sac State +18.5, SDSU +12.5, Buffalo +10) all lost by more than the
  number. Say both weeks together: **YEL 18–9 ATS through two weeks**, and
  the base rate is 52%.

**Corey's column (his slide, "man off by"): 2, 11, 11, 1, 14 = 39.0.** Three-way
read: Man 39.0 · Machine 40.5 · Market 48.0; by his numbers the man was
closer than the machine in three of five (A&M, BYU, Alabama), the machine
closer in the Michigan game, and both lost the Texas game to the market
(0.5). Check one number with him: if his Michigan call was Michigan 21–17
(home team on top, as the rest of his score slides read), the miss is 3, not
11, and his week is 31.0 — better than the machine. Weeks 1–2 combined (10
games): Man 87.0 · Machine 91.0 · Market 97.0 as his column stands.

---

## Slide 3 — Week 2 Winners and Losers

Corey's slide: **Man — Winner North Texas, Loser Washington. Machine —
Winner "Upset Weekend", Loser "Preseason top QB draft stock falling."**

The machine's data behind his two lines:
- *Upset weekend* — AP top-25 teams losing, by the poll in force that
  Saturday (the AP Week 2 poll, released Sept 7). Three ranked teams lost,
  two of them to unranked opponents: **#6 Oregon** lost 39–31 at unranked
  Oklahoma State; **#11 Oklahoma** lost 17–10 at unranked Michigan; and
  **#1 Ohio State** lost 24–23 at #4 Texas — a ranked-on-ranked game, so the
  No. 1 team going down but not an upset by the definition. The machine's
  read on each: Oregon fell 4.6 (the biggest fall in the 25; Oklahoma State
  rose 5.0, the biggest rise in FBS), Oklahoma fell 1.5 (the machine had it
  −2, so a seven-point loss was a nine-point miss; Michigan is back in the
  Week 3 poll at 19), Ohio State moved UP 0.4 (it expected to lose by 3.7 and
  lost by one). The near-misses that held: #19 Washington by two over Utah
  State, #21 Iowa by three over Iowa State.
- *QB draft stock*: on the Heisman index Manning −5.2 (#8 → #10), Moore −7.4
  (#6 → #13, the biggest fall), Leavitt −4.5 (#9 → #16), Hammond −4.7. The
  index graded the games; the market only moved on Leavitt (+1500 → +2500).
- *Machine's own winner / loser if asked*: Utah (+4.3, the only new team in
  the 25) and Oregon (−4.6, the biggest fall in the 25; the voters dropped
  them 15 spots). On the man's two: North Texas, his winner, is the machine's
  too — +5.9 for 44–6 over UNLV, the biggest single-week rating gain
  anywhere; Washington, his loser, fell 9.4 → 6.1 (#29 → #44) for beating
  Utah State by two.

---

## Slide 4 — Our Heisman board

Index = team factor (0.5 + half the machine's odds of 10+ wins) × blended
efficiency (2026 PPA per play with 150 plays of the 2025 line as prior).
Market = DraftKings, Sunday Sep 13 (Covers).

| # | QB · team | 2026 PPA (plays) | 2025 prior | Blend | Team P(10+) | Index | Market |
|---|---|---|---|---|---|---|---|
| 1 | **Darian Mensah · Miami** | 1.133 (48) | 0.371 | 0.556 | 75% | **48.5** | +550 (#1) |
| 2 | Josh Hoover · Indiana | 1.424 (29) | 0.353 | 0.526 | 79% | 47.1 | +1700 (#8) |
| 3 | C.J. Carr · Notre Dame | 0.614 (51) | 0.433 | 0.479 | 86% | 44.4 | +1050 (#4) |
| 4 | Julian Sayin · Ohio State | 0.616 (64) | 0.545 | 0.566 | 52% | 43.1 | +1500 (#7) |
| 5 | Jayden Maiava · USC | 0.651 (90) | 0.517 | 0.567 | 16% | 32.9 | +1900 (#9) |

**Box-score lines (what the slide row says now):** Mensah 41-of-45, 653,
8 TD, 0 INT · Hoover 19-of-27, 376, 8 TD, 0 INT · Carr 35-of-49, 492, 6 TD,
0 INT · Sayin 38-of-57, 598, 4 TD, 1 INT · Maiava 67-of-83, 896, 10 TD, 1 INT
(three games) · Manning 43-of-64, 500, 5 TD, 2 INT · Hammond 46-of-60, 487,
2 TD, 1 INT · Dampier 31-of-42, 437, 5 TD + 81 rushing, 2 TD · Jennings
40-of-52, 767, 8 TD, 2 INT · Kienholz 34-of-50, 639, 4 TD + 111 rushing, 3 TD
· Kamario Taylor 38-of-56, 581, 7 TD, 0 INT + 145 rushing · Leavitt 41-of-66,
574, 2 TD, 4 INT + 135 rushing, 5 TD. (CFBD box scores through Week 2.)

Next up: Dampier 31.5 (unpriced), Hammond 29.8, Jennings 29.3, Kienholz
27.2, **Arch Manning 25.4 (market #3 at +1000)**, Bachmeier 24.5, Kamario
Taylor 24.4.

**The segment: biggest movers, up or down.** Index = team factor (0.5 +
half the team's odds of 10+ wins) × blended efficiency (2026 PPA per play
with 150 plays of the 2025 line as a prior). Two things move it week to
week: what the quarterback did per play, and what the sim now thinks of
his team. Week 2 board → Week 3 board. Say the direction, the game, and
which of the two inputs did it.

*Risers:*
1. **Hoover, Indiana — +6.5, the biggest rise** (40.6 → 47.1, #4 → #2).
   1.424 per play on 29 plays — the best line on the board — and Indiana's
   P(10+) went 73% → 79%. Both inputs up. The market moved him +1900 →
   +1700 and still has him eighth.
2. **Jennings, SMU — +6.4** (22.9 → 29.3, #13 → #8). 14-of-16 for 337 and
   five touchdowns vs UC Davis took his season line 0.611 → 0.914 per play
   on 58. All quarterback: SMU's P(10+) sat at 20%. Unpriced.
3. **Dampier, Utah — +6.3** (25.2 → 31.5, #10 → #6). His line barely moved
   (0.654 → 0.632); Utah's P(10+) went 13% → 33% after 43–10 over Arkansas.
   All team factor. Unpriced — the market's blind spot on this board.
4. **Mensah, Miami — +5.3** (43.2 → 48.5, #2 → #1). 41-of-45 for 653 and
   eight touchdowns through two, 1.133 per play on 48; Miami's P(10+) 75%.
   Market +600 → +550, No. 1 both places.
5. **Carr, Notre Dame — +3.5** (40.9 → 44.4, held #3). 253 and four scores
   vs Rice lifted him 0.398 → 0.614 per play; Notre Dame's P(10+) slipped
   91% → 86% (the cap docked the 52–0). Quarterback up, team down.

*Fallers:*
1. **Moore, Oregon — −7.4, the biggest fall** (31.3 → 23.9, #6 → #13).
   0.293 per play on 74 — and Oregon's P(10+) collapsed 57% → 29% after
   the 39–31 home loss to Oklahoma State. Both inputs down. The market
   pulled his price entirely (+1300 → unpriced).
2. **Manning, Texas — −5.2** (30.6 → 25.4, #8 → #10). 0.808 → 0.417 per play
   on 75: 23-of-37 for 195, one touchdown, one pick, 5.3 an attempt against
   Ohio State. Texas's P(10+) 47% → 40% on the loss. The market bought the
   fourth quarter (+950 → +1000, still No. 3); the index graded the game.
3. **Hammond, Texas Tech — −4.7** (34.5 → 29.8, #5 → #7). 0.335 per play on
   68, the lowest of the ten Week 3 starters, after 20-of-27 for 189 at
   Oregon State; Tech's P(10+) 80% → 64%. He plays Friday — slide 21.
4. **Leavitt, LSU — −4.5** (25.9 → 21.4, #9 → #16). Three picks and five
   sacks against Louisiana Tech: 0.506 → 0.320 per play on 88. LSU's P(10+)
   47% → 35%. The market went +1500 → +2500. He plays Saturday night —
   slide 49.
5. **Sayin, Ohio State — −1.6, but #1 → #4.** 0.934 → 0.616 per play (17-of-32
   for 278 in Austin); the 2025 prior holds him top four. Ohio State's
   P(10+) actually rose 47% → 52% because losing by one was better than
   the machine expected. Small fall, big rank move — three quarterbacks
   passed him.
6. Also down: Mateer (Oklahoma, −3.0, #18 → #22, 0.337 per play at Michigan,
   price pulled).

*New to the board:* **Kienholz, Louisville, straight in at #9** (27.2; 0.718
per play on 71, no 2025 prior — the least-proven Brohm QB playing like the
most efficient; slide 28), **Kamario Taylor, Mississippi State, #12** (24.4;
0.642 per play, 86 rushing at Minnesota; slide 35), Sellers, South
Carolina, #20 (15.3 — he hasn't thrown yet).

**★ Our favorite: Darian Mensah — and the machine now agrees with the
market.** Last week we had Sayin first and the market had him eighth. Two
things changed:
1. **Sayin's 2026 column caught up with reality.** 17-of-32 for 278, one
   touchdown, one pick in the loss at Texas: his season line is 0.616 per
   play on 64 plays. The 2025 prior (0.545) still keeps him top four, but
   Ohio State's P(10+) fell to 52% after the loss and that's the team-factor
   drag.
2. **Mensah did it again.** 41-of-45 for 653 yards and eight touchdowns
   through two games — 90% completions in both. His 2025 Duke prior (0.371)
   is the only thing holding the blend at 0.556; Miami's 75% P(10+) is the
   second-best team factor on the board. Index 48.5, and he's +550.

**Hoover is the market's mistake (No. 2 for us, No. 8 for them).** 1.424
per play on 29 plays is still a small sample, but Indiana's 79% P(10+) is
the second-highest on the board and the offense made a Heisman winner out of
a transfer last year. +1700 for a quarterback the machine has within 1.4
index points of the favorite.

**Arch is the market's No. 3 and our No. 10.** The market bought the
fourth quarter (three straight touchdown drives to beat No. 1); the machine
graded the whole game: 23-of-37 for 195, one touchdown, one interception,
5.3 yards per attempt. His season line is 0.417 per play on 75 plays, the
worst of the ten priced quarterbacks. Say both things — the comeback was
real, and so is the efficiency.

**Jeremiah Smith (+650, market No. 2)** is the non-QB story: 164 yards and a
score in Austin, 1.19 PPA per target on the season with a 0.94 prior. He
doesn't go on the QB board (per-target isn't per-play), but if a receiver
wins it, it's him.

**Caveats:** two games of data; the team factor uses the sim, which inherits
the cap artifact (Ohio State's 52% would be higher without it); and the index
can't see a highlight — the Heisman is a vote.

---

## Slide 5 — Corey's Heisman five

His slide: **Maiava (stayed at 1), Nate Sheppard RB Duke (new), Kamario
Taylor (stayed at 3), Kienholz (new), Leavitt (new).** Where the machine has
each: Maiava #5 (32.9 — the best blended line on the board, USC's 16% P(10+)
is the drag); Sheppard not on the board (the index is quarterbacks only —
per-play efficiency for a back isn't the same scale); Kamario Taylor #12
(24.4, State's 1% P(10+) is the whole gap between his ranking and ours);
Kienholz #9 (27.2, straight onto the board this week); Leavitt #16 (21.4,
−4.5 this week after the three picks). The man is ranking the players; the
machine is ranking player × team, which is how the vote actually goes.
Mensah, our #1 and the market's #1, is not on his five — ask him why.

---

## Slide 6 — Our Top 25

100 rated games in. **Top 10**: 1 Ohio State 25.0 · 2 Texas 25.0 · 3 Notre
Dame 24.8 · 4 Indiana 23.8 · 5 Miami 23.1 · 6 Alabama 23.0 · 7 Georgia 22.6
· 8 LSU 22.3 · 9 Texas A&M 20.9 · 10 Tennessee 17.6.

**What the number means (say this once, early — it explains every row).**
The rating is points: how many points better than an average FBS team the
machine thinks you are on a neutral field. Ohio State 25.0 means "beats an
average team by 25." Zero is average (Wake Forest, #50, is 3.3; the median
team is −1.1; UL Monroe, last, is −18.6). The rank is just the order of the
ratings, and a game line is the difference plus 2.5 for the home team —
LSU 22.3 at Ole Miss 14.6 is 7.7 minus 2.5 = LSU by 5.2.

*Where it comes from.* It starts as ESPN's preseason FPI, frozen in July.
Then every game against a rated FBS opponent moves it — not by win or loss,
but by how much you beat or missed the margin the machine expected. The
July number is worth three games of evidence, so two games in, the prior is
still most of the rating; by mid-October the games outweigh July. FCS games
count for nothing (the opponent has no rating).

*Oregon, the example — 11th with a −8.0.* July had Oregon at 25.3, fourth in
the country. Week 1: the machine expected Oregon to beat Boise State by 23.8;
they won by 7, a 16.8-point miss. Week 2: it expected Oregon by 19.5 at
Oklahoma State; they lost by 8, a 27.5-point miss. Two games, 44 points
short of expectation, diluted by the prior, and the rating falls 8.0 to
17.3 — the biggest fall in the 25 since August. But 17.3 still says "beats an
average team by 17," and only ten teams say more. Texas Tech is 17.2, USC
14.7. To fall out of the 25 Oregon would need to reach South Carolina's
10.9 — another 6.4 points, roughly two more 20-point misses. The voters
dropped them 15 spots to 21 because a poll ranks the résumé and a loss is a
loss; the machine ranks the margin against the expectation, and Oregon's
expectation was set very high in July. The Δ PRE column (−8.0) is the
machine's version of "how far they have fallen"; the rating is "how good
they still are."

*The same rule, the other direction.* Ohio State is No. 1 after losing
because the machine expected to lose at Texas by 0.7 and lost by 1 — no
news, and its Week 1 (expected +48.5, won by 53) was a small plus. Utah
went from #31 to #21 on one game: expected to beat Arkansas by 6.6, won by
33, a 26-point miss in its favor. Texas Tech won at Oregon State by 11 and
fell 2.8, because the machine expected 25.6. Same arithmetic every time:
result minus expectation, then shrunk toward July.

**The headline: the machine's No. 1 lost on Saturday.** Ohio State lost
24–23 in Austin and moved UP 0.4, Texas won and moved DOWN 0.8, and they now
sit 25.0 and 25.0 with the Buckeyes ahead on decimals. Why: the machine
expected Texas by 3.7 at home. Losing by one is 2.7 points better than
expected for Ohio State and 2.7 worse for Texas. The voters flipped them
(Texas AP 1, Ohio State AP 6). Say it plainly: "the voters grade the
scoreboard; the machine grades the margin against the expectation."

**Machine vs the AP voters (Week 3 poll), the weekly column:**
- Ohio State machine #1 / AP #6 · Texas machine #2 / AP #1.
- Oregon machine #11 / AP #21 — the 39–31 home loss to Oklahoma State cost
  4.6 rating points (−8.0 on the season, the biggest fall in the top 25);
  the voters dropped them 15 spots.
- Oklahoma machine #15 / AP #24 after the 17–10 loss at Michigan.
- BYU machine #19 / AP #11 — the voters like 2–0 with a Big 12 win more than
  the machine likes a 13.6 rating.
- In our 25, not theirs: Florida (#16, 14.4), Auburn (#22), South Carolina
  (#25). In theirs, not ours: Iowa (AP 18), Houston (AP 22), Louisville
  (AP 23).

**The segment: biggest movers in the Top 25, up or down.** Rating points
and rank, Week 2 board (51 games) → Week 3 board (100 games). The machine
moves a team on one thing only: the margin against what it expected. Say
the direction, the game, and whether the team beat or missed the number.

*Risers:*
1. **Utah — +4.3, the biggest rise in the 25** (8.5 → 12.8, #32 → #21, the
   only new team in the 25). 43–10 over Arkansas against an expectation
   around 10. Giant Killer board has Utah State at +28.5 there Saturday.
2. **Tennessee — +2.5** (15.1 → 17.6, #15 → #10). 45–24 at Georgia Tech, a
   rated road win by three touchdowns; back in the top ten.
3. **Missouri — +2.0** (12.2 → 14.2, #19 → #17). 38–21 at Kansas — the game
   that put Leipold on the hot-seat movers.
4. **Alabama — +1.9** (21.1 → 23.0, #9 → #6) and **Texas A&M — +1.9** (19.0 →
   20.9, #11 → #9). 45–17 at Kentucky and 48–20 over Arizona State: both
   beat the number by two touchdowns, both climb three spots.
5. **Indiana — +1.5** (22.3 → 23.8, #7 → #4) and **Michigan — +1.6** (11.6 →
   13.2, #21 → #20). Indiana's 55–0 was FCS and moved nothing — its climb
   is the teams above it falling; Michigan's is real, 17–10 over Oklahoma
   as a home dog on the machine's number.

*Fallers:*
1. **Oregon — −4.6, the biggest fall in the 25** (21.9 → 17.3, #8 → #11; −8.0
   on the season, the biggest fall from preseason in the 25). 39–31 at home
   to Oklahoma State, a team the machine had at −1.5. The voters dropped
   them 15 spots; the machine three. (Internal: luck −7.5 — the efficiency
   says it was closer than the score.)
2. **Texas Tech — −2.8** (20.0 → 17.2, #10 → #12). WON 35–24 at Oregon State
   and fell, because the machine expected ~27 against a −7.2 team. Friday's
   opponent. (Internal: luck +14.1 — the efficiency says it deserved to lose
   by 3.)
3. **Notre Dame — −2.5** (27.3 → 24.8, #1 → #3) and **Georgia — −2.2** (24.8 →
   22.6, #3 → #7). 52–0 over Rice and 70–20 over Western Kentucky. The cap
   artifact, both of them: a blowout by a team expected to blow out reads
   as under-performance. Say the housekeeping line below; the fix goes live
   next week.
4. **Oklahoma — −1.5** (16.0 → 14.5, #12 → #15). 17–10 at Michigan; the
   machine had it Oklahoma −2, so a seven-point loss is a nine-point miss.
5. **LSU — −1.5** (23.8 → 22.3, #5 → #8). Won 45–14 over Louisiana Tech and
   fell: expected ~34 against a −9.6 team, and Leavitt threw three picks.
6. **Iowa — −1.9, out of the 25** (10.7 → 8.8, #25 → #29). Beat Iowa State
   16–13 and dropped out; the voters have them AP 18.

*Unmoved at the top:* **Ohio State 25.0 (#4 → #1) and Texas 25.0 (#2 → #2).**
The Buckeyes lost 24–23 in Austin and moved UP 0.4; Texas won and moved
DOWN 0.8 — the machine expected Texas by 3.7. That's the whole Slide 6
argument: the voters grade the scoreboard, the machine grades the margin
against the expectation.

*Elsewhere in FBS (the biggest moves anywhere):* North Texas +5.9 (44–6
over UNLV), Oklahoma State +5.0 (the Oregon win), Georgia State +4.5,
Mississippi State +4.0 (38–13 at Minnesota — Saturday's opponent for South
Carolina) · UNLV −5.1, Minnesota −4.9, Kennesaw State −4.5, Arkansas −4.3.

**New this week — the luck column (efficiency layer).** We now compute a
*deserved margin* for every game from per-play efficiency (total PPA and
success rate, CFBD box scores; a model fit on 2021–24 that explains 80% of
margins). Season to date, actual minus deserved per rated game: Texas +12.5
(deserved +14.0 a game, actual +26.5 — Texas State was a 52–7 that played
like 30), Indiana +13.0, Tennessee +8.8, Texas A&M +8.3, Miami +8.4, Notre
Dame +6.6; Ohio State −3.6 (deserved +29.6 a game — the efficiency says the
Buckeyes have been the best team on the field), LSU −4.3, Oregon −7.5 (the
Oklahoma State loss was closer than 39–31 by the efficiency: deserved +7.0 a
game). And the one that matters Friday: **Texas Tech +14.1** — the 35–24 at
Oregon State had a deserved margin of −3.1. Say the caveat: the backtest
says deserved margins do NOT predict next week better than the score (five
seasons, never better out of sample), so the rating still uses the score.
This column is information about the games that happened, not the rating.

**What luck means (internal — the slides stay simple; this is the
explanation to have in your head).** Luck is the gap between a team's
scoreboard results and what its play-by-play efficiency says it earned.

- *How it's computed.* For every game with a box score, the efficiency layer
  produces a deserved margin from two things: net total predicted points
  added (how many points each team's plays were worth) and net success rate
  (how often each team's plays kept it on schedule). A model fit on 2021–24
  turns those into the margin the game "should" have had; it explains about
  80% of real margins. Luck for one game is the actual margin minus the
  deserved margin, from that team's side. A team's luck number is the
  average over its rated games so far.
- *Positive* = the scoreboard has been kinder than the play. Texas at +12.5
  won its two games by 26.5 a game while its efficiency was worth about 14.
  Texas Tech at +14.1 beat Oregon State by 11 in a game its efficiency says
  it should have lost by 3.
- *Negative* = the team has played better than its results. Oregon at −7.5
  lost to Oklahoma State by 8, but by efficiency it played like a 7-point
  favorite across its two games. Ohio State at −3.6 has been the most
  efficient team on the field even though it lost in Austin.
- *Near zero* = the results are earned. Georgia at +1.2 won by 50 and
  deserved 49.
- *Where the gap comes from.* The parts of a game efficiency doesn't credit:
  turnovers and where they happened, special-teams scores, red-zone
  finishing, garbage time. Those are mostly unrepeatable, which is why a big
  positive number is a caution flag about a record and a big negative number
  is an argument that the record undersells the team.
- *What it isn't.* A forecast. The backtest showed that fitting the rating on
  deserved margins instead of scores does not predict next week any better,
  five seasons running, so the rating still uses the score. Luck is the
  explanation you carry into the conversation: it says when a result was
  earned and when it wasn't — the machine's honest answer to "were they
  really that good on Saturday."

**Machine housekeeping (say it once).** The ±28 cap keeps docking elite
teams for cupcake blowouts: Notre Dame −2.5 for 52–0 over Rice, Georgia
−2.2 for its Week 2 blowout, Texas A&M's 50–0 last week. It's a
pre-registered rule and this card was built on it, so it stands through
Saturday. The fix is built and backtested (cap the residual — the miss
against the expectation — not the margin, so 52–0 when you're expected to
win by 44 is +8, not −16). Same accuracy over five seasons, no more docking
for cupcakes; under it Ohio State and Texas sit at 30.0, Notre Dame 28.8,
Georgia 27.3, South Carolina climbs to #15. It goes live with the Week 4
refresh, after this episode records, so next week's Top 25 will look
different for that reason — say so now. FCS games are still invisible — Houston's 77–6 over
Southern, South Carolina's 45–9 over Towson and Florida's 52–3 over Campbell
moved nothing.

### Lucas's Top 25 — EDIT ME (prefilled with the machine's order)

Reorder, swap, cut. Columns: your rank · team · (machine rank, last week's machine rank) · last week · this week.

1. **Ohio State** (up from 4) · machine #1 25.0 · last week: L 23-24 at Texas · this week: vs Kent State
2. **Texas** (unchanged) · machine #2 25.0 · last week: W 24-23 vs Ohio State · this week: vs UTSA
3. **Notre Dame** (down from 1) · machine #3 24.8 · last week: W 52-0 vs Rice · this week: vs Michigan State
4. **Indiana** (up from 7) · machine #4 23.8 · last week: W 55-0 vs Howard · this week: vs Western Kentucky
5. **Miami** (up from 6) · machine #5 23.1 · last week: W 77-7 vs Florida A&M · this week: at Wake Forest
6. **Alabama** (up from 9) · machine #6 23.0 · last week: W 45-17 at Kentucky · this week: vs Florida State
7. **Georgia** (down from 3) · machine #7 22.6 · last week: W 70-20 vs Western Kentucky · this week: at Arkansas
8. **LSU** (down from 5) · machine #8 22.3 · last week: W 45-14 vs Louisiana Tech · this week: at Ole Miss
9. **Texas A&M** (up from 11) · machine #9 20.9 · last week: W 48-20 vs Arizona State · this week: vs Kentucky
10. **Tennessee** (up from 15) · machine #10 17.6 · last week: W 45-24 at Georgia Tech · this week: vs Kennesaw State
11. **Oregon** (down from 8) · machine #11 17.3 · last week: L 31-39 at Oklahoma State · this week: vs Portland State
12. **Texas Tech** (down from 10) · machine #12 17.2 · last week: W 35-24 at Oregon State · this week: vs Houston
13. **USC** (up from 14) · machine #13 14.7 · last week: W 49-30 vs Louisiana · this week: at Rutgers
14. **Ole Miss** (down from 13) · machine #14 14.6 · last week: W 41-9 vs Charlotte · this week: vs LSU
15. **Oklahoma** (down from 12) · machine #15 14.5 · last week: L 10-17 at Michigan · this week: vs New Mexico
16. **Florida** (up from 17) · machine #16 14.4 · last week: W 52-3 vs Campbell · this week: at Auburn
17. **Missouri** (up from 19) · machine #17 14.2 · last week: W 38-21 at Kansas · this week: vs Troy
18. **Penn State** (down from 16) · machine #18 13.7 · last week: W 27-9 at Temple · this week: vs Buffalo
19. **BYU** (down from 18) · machine #19 13.6 · last week: W 28-17 vs Arizona · this week: at Colorado State
20. **Michigan** (up from 21) · machine #20 13.2 · last week: W 17-10 vs Oklahoma · this week: vs UTEP
21. **Utah** (up from unranked) · machine #21 12.8 · last week: W 43-10 vs Arkansas · this week: vs Utah State
22. **Auburn** (up from 23) · machine #22 12.6 · last week: W 43-8 vs Southern Miss · this week: vs Florida
23. **Virginia** (down from 20) · machine #23 11.8 · last week: W 59-3 vs Norfolk State · this week: vs West Virginia
24. **SMU** (down from 22) · machine #24 11.4 · last week: W 56-10 vs UC Davis · this week: at Louisville
25. **South Carolina** (down from 24) · machine #25 10.9 · last week: W 45-9 vs Towson · this week: vs Mississippi State

Just outside the machine's 25: Nebraska (#26), Louisville (#27), Virginia Tech (#28), Iowa (#29), Mississippi State (#30).

---

## Slides 7–11 — Corey's Top 25 (five slides, 25 → 1)

His top ten: Texas, Notre Dame, Georgia, Miami, Indiana, Alabama, Texas
A&M, LSU, Tennessee, Ohio State. **Biggest splits vs the machine:** Ohio
State (Man 10 / machine 1 — the whole Slide 6 argument in one row), Oregon
(Man 22 / machine 11), Nebraska (Man 18 / machine 26, not in our 25),
Penn State (Man 12 / machine 18), South Carolina (Man 20 / machine 25),
Georgia (Man 3 / machine 7), Oklahoma (Man 19 / machine 15), Utah (Man 17 /
machine 21). **Agreements:** Alabama 6 / 6, LSU 8 / 8, SMU 24 / 24, and 15
of his 25 are within three spots of ours. In his 25, not ours: Nebraska. In
ours, not his: Missouri (#17). Both of us have Florida, Auburn and South
Carolina, which the voters don't.

---

## Slide 12 — Hot Seat Top 10

Seat score = 60% the man (CBS Sports' preseason hot-seat rating, 0–5, Aug 29
— no new CBS list has published, so the ratings are unchanged) + 40% the
machine (season-sim odds of missing the win total that keeps the job; the
bars are our judgment from the deep-dive "how he escapes" write-ups).

| # | Coach · school | Tenure | CBS | Needs | P(gets it) | Machine wins | Score | Week 2 |
|---|---|---|---|---|---|---|---|---|
| 1 | Norvell · Florida State | 38–34, yr 7 | 5.0 | 8 | 20% | 6.2 (4–8) | 92 | off (L 24–27 SMU last) |
| 2 | Schiano · Rutgers | 31–41 2nd stint | 3.0* | 6 | 4% | 3.4 (2–5) | 74 | L 21–28 at Boston College |
| 3 | Aranda · Baylor | 36–37, yr 7 | 5.0 | 7 | 65% | 7.1 (5–9) | 74 | W 44–3 Prairie View |
| 4 | Fickell · Wisconsin | 17–21, yr 4 | 5.0 | 6 | 67% | 6.2 (4–8) | 73 | W 36–9 Western Illinois |
| 5 | Locksley · Maryland | 37–49, yr 8 | 4.9 | 6 | 65% | 6.1 (4–8) | 73 | W 38–14 at UConn |
| 6 | Beamer · South Carolina | 33–30, yr 6 | 4.3 | 7 | 50% | 6.5 (5–8) | 72 | W 45–9 Towson |
| 7 | Swinney · Clemson | 186–53, yr 18 | 3.1 | 9 | 17% | 7.0 (5–9) | 70 | W 22–7 Georgia Southern |
| 8 | O'Brien · Boston College | 9–16, yr 3 | 3.5 | 5 | 35% | 3.9 (2–6) | 68 | W 28–21 Rutgers |
| 9 | Mason · Middle Tennessee | 3–9 in 2024, yr 3 | 3.6 | 6 | 40% | 5.1 (3–7) | 67 | L 26–28 at Marshall |
| 10 | Doeren · NC State | yr 14 | 3.0 | 7 | 30% | 5.7 (4–8) | 64 | W 73–0 Richmond |

Next three: Fleck (Minnesota, 62 — lost 38–13 at home to Mississippi State;
7% for seven wins), Belichick (62 — dropped off the ten after 35–3 over ETSU;
67% for six), Vincent (UL Monroe, 62*). *Rutgers's CBS number is our
estimate.

**The segment: who moved into the ten, who fell out, who moved inside it.**
Seat score = 60% CBS rating + 40% the machine's odds of missing the win
total that keeps the job. The CBS half hasn't changed since Aug 29, so
every move is the machine reacting to a game. Week 2 board → Week 3 board.

*INTO the top ten — Doeren, NC State (#12 → #10).* He didn't move at all —
63.8 both weeks, 30% for the seven wins the job needs, 73–0 over Richmond
was FCS and counted for nothing. He is tenth because the man above him
fell past him. That is the honest read: NC State's seat is exactly as warm
as it was; the list around it cooled.

*OUT of the top ten — Belichick, North Carolina (#10 → #12).* 64.2 → 62.3.
35–3 over East Tennessee State didn't count (FCS), but the Week 1 win at
TCU keeps the sim at 67% for the six wins that make a bowl, projected 6.2.
The machine has said since Week 1 that he's fine; the CBS 4.1 is what keeps
him near the line. Two spots outside, and one bad Saturday puts him back.

*Inside the ten, the order changed:*
1. **Schiano up to No. 2 (#4 → #2, 73.9 → 74.5).** Rutgers lost 28–21 at
   Boston College — to the coach who is eighth on this list — and sits at
   −7.7, last in FBS. 4% for six wins, projected 3.4. His score barely
   moved; he rose because Locksley fell past him.
2. **Locksley down to No. 5 (#2 → #5, 78.8 → 72.8, the biggest drop inside
   the ten).** 38–14 at UConn; rating +2.9; 50% → 65% for six wins,
   projected 6.1. Winning a road game cooled the seat six points.
3. **Swinney up to No. 7 (#9 → #7, 68.4 → 70.5).** Won 22–7 over Georgia
   Southern and got hotter anyway — the machine expected ~24 and docked
   Clemson 1.2. 17% for the nine wins that make a redemption year. The rare
   seat that heats up on a win.
4. **Mason down to No. 9 (#7 → #9, 71.0 → 67.2).** Lost 28–26 at Marshall
   and cooled: the machine expected worse, rating +1.5, 30% → 40% for six.
5. **Fickell up one to No. 4** on Locksley's fall, score unchanged at 73.1
   (67% for six). Norvell (#1, 91.9, FSU idle), Aranda (#3), Beamer (#6 —
   plays Lebby on Saturday, slide 35) and O'Brien (#8) held their spots.

*Knocking on the door:* **Fleck, Minnesota, #11 (from #22, +6.0, the
biggest jump on the board)** — 38–13 at home to Mississippi State, 7% for
the seven wins that keep him, projected 4.2; one more loss and he's in.
Then Belichick #12, Vincent (UL Monroe) #13, Venables #14 (from #17 after
the loss at Michigan, 33% for eight).

*Biggest moves anywhere, for the record:* hotter — Leipold (Kansas, +7.9,
#31 → #25, 67% → 47% for six after 38–21 to Missouri), Fleck +6.0,
Venables +3.9; cooler — McGee (Georgia State, −10.9, bowl odds 53% → 80%),
Lebby (Mississippi State, −8.9, 58% → 80%, Saturday's opponent for Beamer),
Locksley −6.0, DeBoer (Alabama, −3.8, 30% → 40% for ten).

**Caveat, said out loud:** the bars are ours; the CBS ratings are three weeks
old. The formula is transparent so Corey can argue the inputs.

---

## Slide 13 — Corey's Hot Seat ten

His slide: **Venables, Aranda, Norvell, Dykes, Swinney, Fickell, Doeren,
Brent Key, Fran Brown, Leipold.** Where the machine has each: Venables #14
(score 61.7 — 33% for eight wins; the man has him first, the machine says
the schedule, not the seat, is the story); Aranda #3 (65% for seven);
Norvell #1 (91.9, 20% for eight); Swinney #7 (17% for nine); Fickell #4
(67% for six); Doeren #10 (30% for seven); Leipold #25 but the biggest riser
on the board (+7.9). Dykes, Key and Fran Brown are not on the machine's
board at all — it only scores coaches CBS rated in August, so the man is
covering three seats the machine can't see. The machine's ten he doesn't
list: Schiano (#2, 4% for six), Locksley (#5), Beamer (#6 — plays Saturday),
O'Brien (#8), Mason (#9).

---

## Slide 14 — Five Games, One Card

| Game (kick, ET) | Machine | Market (DK) | Score call | Machine win % | Read |
|---|---|---|---|---|---|
| Houston at Texas Tech (Fri 8:00) | TTU −13.0 | TTU −7.5 · O/U 53 (Bovada; DK total not up) | Texas Tech 33–20 | TTU 79% | 5.5 to Tech — a small lean (5.7 pp) |
| SMU at Louisville (Sat 3:30) | LOU −1.1 | LOU −1.5 · O/U 59.5 ⚑ | Louisville 30–29 | LOU 54% | machine = market · MONSTER UNDER |
| Mississippi State at South Carolina (Sat 4:15) | SC −4.9 | SC −4 · O/U 58.5 | SC 32–27 | SC 63% | 0.9 to SC — no play |
| Florida at Auburn (Sat 7:00) | AUB −0.7 | FLA −2.5 · O/U 53.5 | Auburn 27–26 | AUB 52% | **lean Auburn +2.5** — the home dog, 8.8 pp gap |
| LSU at Ole Miss (Sat 7:30) | LSU −5.2 | LSU −3 · O/U 59.5 ⚑ | LSU 32–27 | LSU 62% | 2.2 to LSU — quibble · MONSTER UNDER |

**Two Monster Unders on one card.** The top-decile threshold is 59.5 this
week (it was 58.5 on Monday). LSU–Ole Miss 59.5 and SMU–Louisville 59.5
qualify; State–South Carolina's 58.5 fell just under the line on the
Tuesday pull, so it is no longer a Monster Under. The rule: totals in the season's top decile
went under 55.1% of the time across 2021–25, the only spread-or-total bias
that survived the post-mortem. Week 1's Monster Under (59.5 → 33) cashed;
say the record (1–0) and the base rate in the same breath.

**Line movement, all one direction.** Four of the five have moved four to
six points since first-seen — Houston +6 (−13.5 → −7.5, toward the dog),
LSU +4.5, Florida +4, State +3.5. The machine's side got the CLV on all four.
SMU–Louisville hasn't moved off −1.5.

**No stated position of size this week.** The Auburn lean (+2.5) is the
widest machine-market gap on the card at 8.8 points of win probability; the
Tech lean is 5.7 points — 5.5 points of spread now, but the moneyline (Tech
−300) keeps the win-prob gap under the 6-point flag. Everything else is
agreement.

---

## Slides 16–21 — Houston at Texas Tech — Fri Sep 18, 8:00 ET, Jones AT&T Stadium (Lubbock)

Corey's block: his keys for Houston → our Houston team slide → his keys for Texas Tech →
our Texas Tech team slide → his score → our number slide.

### Slides 16–17 — Houston

**Corey's keys (Houston):** Stop the Run · Defend the Pass · Convert on 3rd Down.

**COACH / QB / ROSTER.** Houston: Fritz year 3; Weigman returns (0.600 PPA
per play through two — 8th among the quarterbacks we track); 81% back, 18
adds — the Tulane band (Hughes, Hurst, White) plus all-conference OL
transfers Terrill and Boswell.

**Houston keys, explained.**
1. *Weigman's legs vs the rebuilt front* — 795 rushing yards last year,
   but Houston would rather he run on broken plays than on designed ones
   (the injury history is why the designed runs stay off him). The value is
   the threat: when Tech's portal front (Trick, White), the best pass rush on
   the card, gets home, Weigman turns a sack into a scramble and a first
   down. That is what makes the ends play contain instead of pinning their
   ears back, and it is the only thing that slows this rush down.
2. *Run it 45 times* — 388 on the ground last week (three backs over 55);
   the prep's line is "possibly the league's best combined trench play."
3. *Make Hammond throw* — 189 yards on 27 attempts in Corvallis; force the
   pocket game and let the secondary (Webb, Allen, James) play.
4. *Win the trenches* — line play on both sides of the ball, and the game.
   Houston's transfer offensive line (all-conference adds Terrill and
   Boswell; 388 rushing last week, against Southern) vs Tech's portal-built
   front (Trick, White, Laventure, Johnson), the best pass rush on the card:
   if Terrill and Boswell hold up, Weigman gets his 45 carries and the
   play-action off them; if Tech's front wins, Houston is throwing into the
   best rush it sees this month. Flip it: Tech's line couldn't run on Oregon
   State (155 at 3.4) and Houston's front is better than Oregon State's.

### Slides 18–19 — Texas Tech

**Corey's keys (Texas Tech):** Score in the Red Zone · Defend the Pass · Stop the Run.

**COACH / QB / ROSTER — Texas Tech.** McGuire year 5; Hammond (0.335
per play on 68 — the lowest of the ten Week 3 starters); 53% back, 23
adds — the DL two-deep bought in the portal again (Trick, White, Laventure,
Johnson) after Bailey and Rodriguez left for the NFL.

**Texas Tech keys, explained (the deep dive).**
1. *Hammond's second real start.* The background: Kirk Francis (Tulsa, 12
   career starts) was the projected Week 1 starter while Will Hammond came
   back from the October ACL; Hammond won the job and has two starts. Week 1
   vs Abilene Christian (FCS): 26-of-33 for 298, a touchdown, a pick, 9.0 an
   attempt — the 64-yard Malcolm Simmons touchdown was the highlight. Week 2
   at Oregon State: 20-of-27 for 189, one touchdown, no picks, 7.0 an
   attempt, QBR 64. Season line 46-of-60, 487 yards, 2 TD, 1 INT: accurate,
   short, and the least productive of the ten Week 3 starters at 0.335 PPA
   per play. The tell inside the numbers: Tech's passing success rate on
   schedule was fine (50%) but on passing downs it was 29% — when a drive got
   behind the chains, he didn't get it back. He was also sacked four times
   in Corvallis. Friday is the first real front he has faced since the knee,
   at home, on a short week, with Trick and White on the other sideline
   watching a quarterback who has thrown 60 college passes since surgery.
   Tech also carries a short-yardage package for Thomas Castellanos (five
   carries, a touchdown, and a throw at Oregon State) — watch for it near
   the goal line.
2. *J'Koby Williams downhill.* At Oregon State: 20 carries, 116 yards, 5.8 a
   carry, a 38-yard run and a touchdown. Now the rest of the backfield: the
   other 26 carries went for 39 yards, 1.5 a carry — Dickey 10 for 21,
   Joyner 5 for 25. The line yards were 2.8 (3.3 vs the FCS team) and the
   rushing success rate 36%, so the offensive line — three returning
   starters, the Louisville guard Church, the five-star freshman tackle Ojo —
   is not creating push yet; Williams is creating it himself. The
   three-headed backfield (Williams and Dickey had 1,992 yards and 20
   touchdowns between them last year; Joyner averaged 7.6 at USC in 2024) is
   the offense's floor only if the line gets Williams to the second level.
   Houston's run defense against a real team (Oregon State, Week 1) allowed a
   33% rushing success rate and almost no stuffs — there is room, if Tech
   commits to it.
3. *The portal defense vs a real offense.* Oregon State threw for 417 on
   Shiel Wood's rebuilt front seven: Braden Atkinson 31-of-51 for 413,
   Jesse Legree 8 catches for 240 with a 75-yarder and two scores. The two
   sides of that: Tech's defense allowed only a 30% success rate and got off
   the field on third down (Oregon State 4-of-15), but its explosiveness
   allowed was 2.05 — the worst number on the card — so it was
   bend-don't-break with busts. The pass rush that is supposed to be the best
   on the card produced two sacks (Roberts, Holmes) and single hurries from
   Trick, Mathis and Romaine; Mathis had 2.5 sacks against the FCS team. Now
   Houston: against the same Oregon State team in Week 1 it ran a 45%
   rushing success rate and a 53% passing success rate, and converted 48% of
   its passing downs — it is the balanced version of what Oregon State did
   to Tech, with a quarterback who can run. Houston's 8-of-8 on third down
   last week was against Southern; the Oregon State number is the honest
   one, and it says Houston stays on schedule.
4. *Finish drives.* The machine expected Tech to win at Oregon State by
   about 27; it won by 11, and the box score says why: 8-of-16 on third
   down, 46 carries for 155 at 3.4, four sacks taken, seven penalties for 70,
   a turnover, and an offensive success rate that fell from 50% in Week 1 to
   40%. On passing downs the offense succeeded 29% of the time. That is what
   "finish drives" means here — Tech moved the ball (22 first downs, 352
   yards) and stalled: drives that reached Oregon State territory ended in
   field-goal tries and punts instead of touchdowns. Against Houston, a team
   that converted 48% of its own passing downs, stalled drives are how a
   13-point favorite ends up in a one-score game in the fourth quarter.

### Slide 20 — the score calls

Corey's slide shows **24 / 35** (top / bottom). If the top number is
the home team — the Week 2 receipts fit that reading — his call is
**Houston 35–24 (the upset)**; read the other way it is Texas Tech 35–24.
Confirm with him before air. Machine: **Texas Tech 33–20**.

### Slide 21 — the number


**The arithmetic.** Texas Tech 17.2 (machine #12) vs Houston 6.7 (#40);
+2.5 for Lubbock → Tech by 13.0 → 79% on the curve → fair Tech −380 /
Houston +380. Market: DK Tech −7.5 (Bovada −7.5, Tech −300 / Houston +270;
**total 53 at Bovada — DK hasn't posted one**). First-seen −13.5 on Aug 23,
−9.5 on Sunday, −7.5 today: six points toward Houston, and the machine hasn't
moved off 13. **Score call Texas Tech 33–20** (13 laid over 53).

**Why it's on the card.** The Big 12 prep flagged this game in July as "the
league's first great litmus test — cover the 'Houston is the sleeper' take
now." Houston is the AP's No. 22 and unranked in ours (#40); Texas Tech is
AP 13 and our #12.

**Stakes (the four headlines).**
- *The Big 12's first litmus test*: Tech is the defending champion (12–2,
  both losses to Tech's own ceiling — ASU without a QB and the Oregon
  shutout). Houston's 10–3 in 2025 was Fritz's year-two rocket. Winner owns
  the early Big 12 narrative.
- *Fritz's year three*: his career pattern is .507 in year ones, .730 in
  year twos, .725 in year threes — Tulane went from 2 wins to 12 on that
  curve. Weigman is back (2,705 pass / 795 rush / 36 TD), and five-star
  Keisean Henderson is the backup (6-of-7 for 83 and two scores vs
  Southern). 81% of production back, the most on the card.
- *Hammond after the scare in Corvallis*: 35–24 at Oregon State (a −7.2
  team) cost Tech 2.8 rating points — the machine expected ~27. Hammond
  20-of-27 for 189; J'Koby Williams 116 on 20; 8-of-16 on third down.
- *Four straight for Tech in the series*: 38–21, 33–30, 49–28, 35–11 —
  three of the four by double digits, and the machine's 13 says the pattern
  holds. Internal, not for the slide: the market has moved six points toward
  Houston since August (−13.5 → −9.5 → −7.5) on the 33–20 over Oregon State
  and the 77–6 over Southern (388 rushing at 8.6, 8-of-8 on third down); the
  machine only saw the Oregon State game (Houston −0.4 for winning by 13 at
  home against a −7 team).

**Honesty box: "5.5 to Tech — a small lean."** Machine 13, market 7.5:
5.5 points of spread but 5.7 points of win probability, still under the
6-point flag — the moneyline (Tech −300, 73.5% no-vig) prices Tech higher
than the spread does, so the gap sits where it did Sunday. Tech has won four
straight in the series (38–21, 33–30, 49–28, 35–11), three by double
digits. If DK posts a total under 53, the score call tightens on rebuild.

---

## Slides 23–28 — SMU at Louisville — Sat Sep 19, 3:30 ET, L&N Federal Credit Union Stadium

Corey's block: his keys for SMU → our SMU team slide → his keys for Louisville →
our Louisville team slide → his score → our number slide.

### Slides 23–24 — SMU

**Corey's keys (SMU):** Kevin Jennings wins the day · Win the time of possession battle · Stay strong on 3rd Down.

**COACH / QB / ROSTER.** SMU: Lashlee year 5, 38–17, both coordinators gone
(Woods to Missouri State, Symons to the Cowboys) — co-coordinator troikas on
both sides; Jennings, third-year starter; 57% back, 15 adds — All-ACC OT PJ
Williams fronts a line that needed no portal help.

**SMU keys, explained (the deep dive).**
1. *Jennings vs the bust-prone back end.* Louisville's first real test was
   Ole Miss in Nashville, and Chambliss threw for 336 on it (21-of-36, three
   touchdowns) with a 66-yard Caleb Odom score; the defense allowed a 47%
   success rate and 41 points. Jennings is the better version of that
   problem: 26-of-36 for 430 at Florida State in the opener (Pittman 5-75-1,
   Hale 2-70), then 14-of-16 for 337 and five touchdowns against UC Davis —
   40-of-52, 767 yards, 8 TD on the season, a 61% and then 67% passing
   success rate. Louisville's pass defense on passing downs was actually
   good against Ole Miss (19% allowed), so the busts come on standard downs,
   which is exactly where SMU's play-action lives.
2. *Protect Jennings.* The ledger says the line is holding: zero sacks
   allowed at Florida State, one against UC Davis (he also took a hit that
   forced two fumbles in Tallahassee — see key 3). Louisville's rush against
   Ole Miss produced zero sacks, and one against Villanova; Clev Lubin's 8.5
   from last year hasn't shown up yet. The line yards tell the honest story
   about SMU's front — 3.3 at FSU, 2.5 against an FCS team — it is a
   pass-protection line, not a run-blocking one.
3. *Win the takeaway ledger.* Four giveaways at Florida State (Jennings's
   two interceptions and two lost fumbles) and SMU still won 27–24 because
   the defense held FSU to 2-of-15 on third down and 125 passing. Zero
   turnovers against UC Davis. Louisville has zero giveaways in two games
   and Kienholz has zero picks; the Ole Miss loss came with Louisville
   winning the turnover count 2–0 and still losing, which is the Brohm
   coin-flip story in one line.
4. *Explosives, not long drives.* SMU's explosiveness was 1.29 at FSU and
   1.60 against UC Davis — top of the card — and it ran for only 93 yards
   on 24 carries last week, so the offense is built on chunk plays, not
   14-play drives. Louisville allowed a 1.31 explosiveness to Ole Miss and
   1.48 the other way is what SMU brings. The game is who hits more 30-yard
   plays; the total (59.5) says the market agrees.

### Slides 25–26 — Louisville

**Corey's keys (Louisville):** Score in the Red Zone · Defend the Pass · Attack through the air.

**COACH / QB / ROSTER — Louisville.** Brohm year 4,
28–12; Kienholz, the third QB1 in three years; 35% back, 33 adds — the RB
duo Isaac Brown / Keyjuan Brown (1,588 combined at 8.1 per carry last year)
is the elite returning unit; Marquise Davis 86 and two scores vs Villanova.

**Louisville keys, explained (the deep dive).**
1. *Ride the Browns.* Against Ole Miss it was Keyjuan Brown 7 for 56 (8.0)
   and Isaac Brown 16 for 36 (2.3) — the run game was Keyjuan and Kienholz
   (14 carries, 69 yards, a 41-yard touchdown run). Against Villanova the
   third back, Marquise Davis, went 7 for 86 with two scores and the team
   ran for 260 at 6.8. The line yards were 2.2 against Ole Miss and 3.9
   against the FCS team, so the real-game version of this run game is
   modest. SMU's run defense against FSU allowed 199 yards at 4.4 and a 41%
   rushing success rate — the softest thing on SMU's side of the ball, and
   the reason the run is the plan.
2. *No coverage busts.* Ole Miss threw for 336 and Louisville lost 41–38
   while winning the turnover battle 2–0 and out-gaining nothing — it was
   the explosives. Nine penalties for 82 helped. SMU's offense is the exact
   shape that punishes it: 585 yards at FSU, an explosiveness of 1.29 and
   then 1.60, Jennings averaging 12 yards an attempt in the opener. The
   question for Brohm's defense is whether the standard-down busts against
   Ole Miss were Week 1 rust or the tradeoff the prep file described.
3. *Kienholz keeps it clean.* 18-of-29 for 307 and two touchdowns against
   Ole Miss, 16-of-21 for 332 and two against Villanova; zero
   interceptions, 34-of-50 for 639 on the season, plus 111 rushing yards
   and three rushing touchdowns. Third quarterback in three years under
   Brohm and so far the most efficient: 0.718 PPA per play, ninth on the
   Heisman board straight from unranked. SMU's defense forced four
   takeaways in two games and held FSU to 2-of-15 on third down, so the
   clean sheet gets its first real test.
4. *Win the one-score game.* Three ACC losses by seven combined points last
   year, then 41–38 to Ole Miss with a 7-of-16 third-down day and nine
   flags. The machine has this at Louisville by 1.1, the market by 1.5 —
   everyone agrees it's a coin flip, and the program's recent coin flips
   have landed the wrong way. Field goals, penalties and the last
   possession decide it; the run game (key 1) is how Louisville shortens
   the game and keeps Jennings on the sideline.

### Slide 27 — the score calls

Corey's slide shows **35 / 34** (top / bottom). If the top number is
the home team — the Week 2 receipts fit that reading — his call is
**Louisville 35–34**; read the other way it is SMU 35–34.
Confirm with him before air. Machine: **Louisville 30–29**.

### Slide 28 — the number


**The arithmetic.** Louisville 10.0 (#27) vs SMU 11.4 (#24); +2.5 for
Louisville → Louisville by 1.1 → 53.5% → fair −115 / +115. Market: DK
Louisville −1.5 (−115 / SMU −105; Bovada −1); **total 59.5 — Monster Under**. First-seen
−1.5 on Aug 23, unmoved. Score call Louisville 30–29 (the machine's 1.1
laid over a 59.5 total).

**Stakes.**
- *The ACC's biggest non-Miami game*: the ACC prep's exact phrase for this
  trip. SMU is the AP's No. 16, Louisville No. 23; the loser is chasing
  Charlotte by Week 3 in a league where neither plays Miami.
- *Jennings, year three*: 430 yards at FSU in the opener (with two picks
  and two lost fumbles, and a win anyway), then 14-of-16 for 337 and five
  touchdowns against UC Davis. 0.914 PPA per play through two — the
  second-best line among the ten Week 3 starters. SMU is 12–1 in his starts
  when his QBR clears 76.
- *Brohm's coin-flip problem*: three 2025 ACC losses by a combined seven
  points, and the 41–38 loss to Ole Miss in Nashville already this year.
  Kienholz: 307 vs Ole Miss, 332 vs Villanova, zero picks; 0.718 per play.
- *Both offenses score fast*: three straight top-25 offenses under Lashlee,
  Brohm's system top-25 every year, and two defenses that bust — SMU's is
  "havoc-rich, bust-prone," Louisville's "top-20 havoc, bottom-40
  explosives." One coverage bust a game is the Brohm tradeoff; SMU's offense
  is built to cash exactly that. (Internal: the total is 59.5, a Monster
  Under number — top-decile totals went under 55% of the time, 2021–25.)

**Honesty box: "Machine = market · Monster Under 59.5."** No side. The
total is the talking point: three straight top-25 offenses under Lashlee,
Brohm's system top-25 every year, and a 59.5 that sits in the decile where
unders hit 55%.

---

## Slides 30–35 — Mississippi State at South Carolina — Sat Sep 19, 4:15 ET, Williams-Brice Stadium

Corey's block: his keys for Mississippi State → our Mississippi State team slide → his keys for South Carolina →
our South Carolina team slide → his score → our number slide.

### Slides 30–31 — Mississippi State

**Corey's keys (Mississippi State):** Stand Tall in the Red Zone · Slow the game down · Win on the ground.

**COACH / QB / ROSTER.** State: Lebby year 3, 7–18; Zach Arnett back as DC
(the man Lebby replaced); Taylor, sophomore; 34% back, 28 adds — six of the
top seven OL gone, eight transfers in.

**Mississippi State keys, explained (the deep dive).**
1. *Taylor's legs and arm.* Week 1 vs UL Monroe: 22-of-34 for 354 and four
   touchdowns plus 6 carries for 59. Week 2 at Minnesota: 16-of-22 for 227
   and three touchdowns plus 13 carries for 86 (a 26-yard run), zero
   turnovers, 6-of-10 on third down. Season: 38-of-56, 581 yards, 7 TD, 0
   INT, 145 rushing. Anthony Evans III (7-121-1) and Zion Ragins are the
   targets. State's offense converted 50% of its passing downs at Minnesota,
   which is the number that says the offense doesn't stall when Taylor
   has to throw on third-and-6. Twelfth on the Heisman board, and the man
   has him third.
2. *Bothwell downhill.* Fluff Bothwell 18 for 113 (6.3) and two touchdowns
   at Minnesota, a 30-yard run; State 46 carries for 252 at 5.5 with a 61%
   rushing success rate and 3.5 line yards against a Big Ten front. Add
   Taylor's 86 and Kolin Wilson's 34 and it's a run game that had three
   options. South Carolina's run defense has faced Kent State and Towson
   (25 carries for 100, then 29 for 21); the honest number is that nobody
   has tested it, and a 61% rushing success rate would.
3. *Arnett's defense vs Sellers.* Zach Arnett, the head coach Lebby
   replaced, is back as the coordinator and his 4-2-5 held Minnesota to 15
   carries for 13 yards (0.9 a carry) and a 31% rushing success rate — but
   Drake Lindsey threw 48 times for 279 with a 40% passing success rate,
   so the soft spot is the back end, not the front. Sellers hasn't thrown
   yet (10-of-23 for 96 last week); if Briles makes him, State's 14%
   passing-downs rate allowed says the defense gets off the field on third
   down. State had two sacks at Minnesota; South Carolina's line allowed
   one to Towson.
4. *Win the turnover ledger.* One giveaway in two games (a fumble at
   Minnesota), 7 TD and 0 INT from the quarterback. South Carolina turned it
   over twice against Towson (a Sellers pick and a fumble) and not at all
   against Kent State. In a game the machine has at 4.9 and the market at 4,
   one extra possession is the spread.

### Slides 32–33 — South Carolina

**Corey's keys (South Carolina):** Attack with the run · Slow the game down · Convert on 3rd Down.

**COACH / QB / ROSTER — South Carolina.** Beamer year 6, 33–30
(16–24 SEC); fourth OC in five years (Kendal Briles); Sellers returns (0.459
per play); 69% back, 26 adds — eight new offensive linemen, five of them FBS
starters.

**South Carolina keys, explained (the deep dive).**
1. *Let Sellers throw.* Two games, two different quarterbacks: 19-of-23 for
   270 and three touchdowns against Kent State (a 70% passing success
   rate), then 10-of-23 for 96, no touchdowns and a pick against Towson (a
   23% passing success rate) while the team ran for 405. Season 0.459 PPA
   per play, 20th on the Heisman board. State's defense just allowed 279
   passing on 48 attempts to Minnesota with a 40% passing success rate;
   its run defense allowed 13 yards. The matchup says throw. Briles's
   offense (the fourth coordinator in five years) has to show the tempo and
   the vertical shots that made him the hire.
2. *Protect Sellers.* Eight new offensive linemen, five of them FBS
   starters elsewhere. The correction to the earlier note: the line has
   allowed one sack in two games (one against Towson, one against Kent
   State) — the four sacks last week were South Carolina's defense, not
   its problem. The scouting file's one weakness is still "the OL must stop
   getting Sellers hit," and Arnett's front produced two sacks and a 31%
   stuff rate against Minnesota; this is the first front that will test the
   rebuilt line.
3. *Harbor deep.* Nyck Harbor: 2 catches for 35 against Towson, the top
   target on a day the team threw for 97. The 4.2 speed is the one thing
   State's secondary — six transfer defensive backs behind Arnett's 4-2-5 —
   hasn't seen. Minnesota's receivers averaged 12.6 a catch on it; the shot
   plays are there, and key 1 is whether Briles calls them.
4. *Stewart off the edge.* The defense had four sacks against Towson and
   one against Kent State, and it held Towson to 21 rushing yards on 29
   carries (a 12% rushing success rate) — the front is winning against
   FCS lines. Last year the problem was converting pressure into sacks
   (97th in sack rate); Dylan Stewart is the player who fixes that. Taylor
   has been sacked twice in two games and runs when the pocket breaks (145
   yards), so the edge has to rush with contain — the same problem Tech's
   ends have with Weigman on Friday.

### Slide 34 — the score calls

Corey's slide shows **31 / 27** (top / bottom). If the top number is
the home team — the Week 2 receipts fit that reading — his call is
**South Carolina 31–27**; read the other way it is Mississippi State 31–27.
Confirm with him before air. Machine: **South Carolina 32–27**.

### Slide 35 — the number


**The arithmetic.** South Carolina 10.9 (#25) vs Mississippi State 8.5
(#30); +2.5 for Columbia → South Carolina by 4.9 → 62.8% → fair −169 / +169.
Market: DK South Carolina −4 (−180 / +150; Bovada −3.5); total 58.5 — no
longer a Monster Under after the decile line moved to 59.5 on Tuesday. The
line opened −7.5 on Friday and is −4 today: three and a half points toward
State. Score call SC 32–27.

**Stakes.**
- *Two hot seats, one game*: Beamer is sixth on our board (CBS 4.3, the
  SEC's hottest; 50% for the seven wins that buy year seven). Lebby was
  second in the SEC's preseason seat ranking (3.3, 7–18, one SEC win in two
  years) and fell off our ten after last week. One of them is 0–1 in the
  league by Saturday night.
- *Kamario Taylor's breakout*: 16-of-22 for 227 and three scores plus 86
  rushing at Minnesota (a rated team, at their place, 38–13). 0.642 PPA per
  play through two — third among the ten Week 3 starters. State gained 4.0
  rating points this week; the prep called him "the league's quiet breakout
  pick."
- *Sellers hasn't thrown yet*: 10-of-23 for 96 against Towson while the
  team ran for 405 (Sellers 119 of it). LaNorris Sellers came back as a
  projected top-five pick; the scouting file's one weakness is still "the OL
  must stop getting Sellers hit — same sentence as last July."
- *Arnett's defense, back in Starkville*: Zach Arnett — the head coach
  Lebby replaced — is State's defensive coordinator again. His 4-2-5 held
  Minnesota to 13 rushing yards and allowed 279 through the air, and it
  faces a quarterback who hasn't thrown yet (Sellers 10-of-23 for 96 against
  Towson). Whether Briles makes Sellers throw into that soft spot, or State
  makes him beat the front, is the game. (Internal: the market moved four
  points toward State in 48 hours after the Minnesota game, −7.5 → −3.5.)

**Honesty box: "0.9 to South Carolina — no play."** Machine 4.9, market 4.
Both sides have real 2026 evidence now. The seats are the story; the total
(58.5) slipped under the Monster Under line on Tuesday, so it is just a
number now.

---

## Slides 37–42 — Florida at Auburn — Sat Sep 19, 7:00 ET, Jordan-Hare Stadium

Corey's block: his keys for Florida → our Florida team slide → his keys for Auburn →
our Auburn team slide → his score → our number slide.

### Slides 37–38 — Florida

**Corey's keys (Florida):** Protect Philo · Make stops on 3rd Down · Score in the Red Zone.

**COACH / QB / ROSTER.** Florida: Sumrall NEW; Philo NEW; 69% back (11th
nationally, the quiet continuity play), 27 adds; Jadan Baugh kept (1,170
yards; 136 and two scores last week); new DC Brad White (from Kentucky).

**Florida keys, explained (the deep dive).**
1. *Philo's first road start.* 16-of-21 for 275, three touchdowns and a pick
   against FAU; 16-of-21 for 242 and two against Campbell. Season 32-of-42,
   517 yards, 5 TD, 1 INT — the best per-play line among the ten Week 3
   starters (0.753) on 42 career attempts, all at home, against a
   Conference USA defense and an FCS one. Dallas Wilson
   (5-104-1) and Vernell Brown are the targets. The number to carry: on
   passing downs Florida succeeded 36% and then 22% of the time — when the
   drive gets behind schedule, the redshirt freshman hasn't yet shown he
   gets it back. Jordan-Hare at night against Durkin's disguises (Baylor's
   Lagway went 27-of-54 on it) is where that gets tested.
2. *Baugh downhill.* 14 for 136 (9.7) and two touchdowns with a 75-yard run
   against Campbell; Florida 214 rushing at 7.1 that day, 281 at 6.9 against
   FAU, a 50% rushing success rate both weeks. Auburn's run defense allowed
   103 at 2.3 to Baylor and 50 at 2.0 to Southern Miss — 29% and 40%
   rushing success rates — so it has held up; Baugh is the first
   1,100-yard back it sees. The machine's Auburn lean (key 3 below, the
   home bump) survives only if Durkin's front does this again.
3. *White's front vs Brown's legs.* Byrum Brown: 13 carries for 88 (a
   20-yard run) against Southern Miss, part of a 343-yard, 6.7-a-carry
   rushing day with Mabson (15-108) and Cobb (12-85); against Baylor the
   same offense ran for 130 at 3.2 and Brown threw three picks. Florida's
   interior — the defensive-tackle vault Napier stockpiled, now under Brad
   White from Kentucky — allowed 120 rushing at 3.2 to FAU and 62 to
   Campbell but let FAU throw 53 times for 276 with a 44% passing success
   rate. The front is the strength; the back end is the question, and
   Brown's legs are what turn a covered play into a first down.
4. *Fourth-down conviction.* The Sumrall trait: at Tulane he went for it
   and won 20 games in two years. Florida's third-down numbers are
   5-of-9 and 3-of-9 — the offense has been so explosive it hasn't needed
   long drives. Auburn went 4-of-5 on fourth down against Southern Miss and
   10-of-18 on third down against Baylor: Golesh keeps the ball too. In a
   game the machine has at 0.7, one fourth-and-2 call at Jordan-Hare is
   the difference between the home bump mattering and not.

### Slides 39–40 — Auburn

**Corey's keys (Auburn):** Start scoring in the Red Zone · Stop the run · Protect Byrum Brown.

**COACH / QB / ROSTER — Auburn.** Golesh NEW, Durkin retained; Brown NEW; 14% back, 39 adds — both
lines are transfer science experiments (top five OL gone, nine transfers).

**Auburn keys, explained (the deep dive).**
1. *Brown's legs.* Byrum Brown followed Golesh from USF (3,158 passing,
   1,121 rushing, 42 touchdowns last year). Week 1 vs Baylor: 26-of-35 for
   259, no touchdowns, three interceptions, sacked five times, the offense
   at a 39% success rate and 2.7 line yards. Week 2 vs Southern Miss:
   17-of-28 for 223 and two scores, 13 carries for 88, zero turnovers, the
   offense at 52% with a 61% rushing success rate. The designed
   quarterback run is the identity — Golesh's offense ran it 51 times last
   week — and Florida's interior is built to stop exactly that. Whether
   the Southern Miss version of Brown shows up against an SEC front is the
   game.
2. *Ball security.* Three picks and five sacks against Baylor, and Auburn
   won 17–16 anyway because Baylor went 7-of-22 on third down. Zero
   turnovers, one sack allowed against Southern Miss. The trend line is two
   games long. Florida's defense forced three FAU turnovers and two from
   Campbell; if Brown throws it to Florida twice, the 2.5-point home bump
   is gone and so is the machine's lean.
3. *Durkin's defense at home.* 16 allowed to Baylor (103 rushing at 2.3,
   Lagway 27-of-54, Baylor 7-of-22 on third down) and 8 to Southern Miss
   (50 rushing at 2.0, four sacks,
   two picks, a 6% passing-downs rate allowed). The carryover unit under a
   retained coordinator, and the reason Auburn is 2–0 with a quarterback
   who threw three picks in the opener. Florida's offense is the first one
   it sees that runs for 6.9 a carry and throws for 275 in the same game.
4. *Tempo without turnovers.* 610 yards on 84 plays against Southern Miss —
   343 rushing, 267 passing — with ten penalties for 73 and one giveaway.
   That's the Golesh offense at the pace he ran at USF. The two things that
   break it are the two things Baylor did: sack the quarterback (five) and
   take the ball (three). Florida had two sacks in each game and five
   takeaways in two; the pace only helps Auburn if the ball stays with
   Auburn.

### Slide 41 — the score calls

Corey's slide shows **28 / 27** (top / bottom). If the top number is
the home team — the Week 2 receipts fit that reading — his call is
**Auburn 28–27**; read the other way it is Florida 28–27.
Confirm with him before air. Machine: **Auburn 27–26**.

### Slide 42 — the number


**The arithmetic.** Auburn 12.6 (#22) vs Florida 14.4 (#16); +2.5 for
Jordan-Hare → Auburn by 0.7 → 52.5% → fair Auburn −110 / Florida +110.
Market: DK Florida −2.5 (Auburn +120 / Florida −142); total 53.5. First-seen
Auburn −1.5 on Aug 23, now Florida −2.5: four points to Florida. **The machine
takes the home dog** — 52.5% vs a market 44%, an 8.8-point gap, the widest on
the card. Score call Auburn 27–26.

**Stakes.**
- *Two first-year coaches*: Sumrall (Troy 10–13 to 23–5; Tulane 20 wins, an
  American title and a CFP berth in two years) vs Golesh (USF 114th to 30th
  in SP+ in three years). The prep's Florida line: "Sumrall's floor at every
  stop has been immediately better." The Auburn line: "Jordan-Hare in
  year-one-energy mode is worth a home upset."
- *Auburn's rebuilt lines vs Florida's front*: 14% of production back and
  39 adds — the top five offensive linemen gone, nine transfer linemen in —
  against the one thing Napier stockpiled, Florida's interior defensive
  line. Auburn ran for 343 at 6.7 last week, against Southern Miss; Baylor
  held it to 103. Whether the transfer line holds is the game, because
  Brown's legs (88 on 13) only work behind blocking. (Internal: the machine
  has Auburn by 0.7 — Florida's 14.4 has one rated game in it, 66–21 over
  FAU; Auburn's 12.6 has two — and the 2.5 home bump flips it.)
- *Byrum Brown vs Aaron Philo*: Brown followed Golesh from USF (3,158 pass
  / 1,121 rush / 42 TD) — three picks in the opener, then 17-of-28 for 223
  and 13 carries for 88 with zero turnovers. Philo is a redshirt freshman
  Georgia Tech transfer reunited with OC Buster Faulkner: 16-of-21 for 242
  vs Campbell, 0.753 PPA per play through two — the best line among the ten
  Week 3 starters, on 32 career attempts... against FAU and Campbell.
- *Jordan-Hare at night*: Auburn's Week 2 was 610 yards, 343 rushing at
  6.7, 4-of-5 on fourth down.

**Honesty box: "Lean Auburn +2.5 — research, not a position."** The
machine's case is the 2.5 home bump and Brown's legs. The risk is that
Florida's rating is one game old and Auburn's ball security is a coin flip.
Home dogs are the one place the post-mortem said the machine is honest (−1.2%
ROI, not −22.9%).

---

## Slides 44–49 — LSU at Ole Miss — Sat Sep 19, 7:30 ET, Vaught-Hemingway Stadium (Oxford)

Corey's block: his keys for LSU → our LSU team slide → his keys for Ole Miss →
our Ole Miss team slide → his score → our number slide.

### Slides 44–45 — LSU

**Corey's keys (LSU):** Stop the run · Stay disciplined · Make stops on 3rd down.

**COACH / QB / ROSTER.** LSU: Kiffin NEW (Weis Jr. OC, Baker DC — SP+'s
projected No. 2 defense); Leavitt NEW (0.320 per play through two, the
second-lowest on the card after the three picks); 21% back, 44 adds. Ole
Miss: Golding NEW, promoted, kept the defensive spine (Echoles, Perkins) and
Lacy (87 and two scores vs Charlotte); Chambliss returns; 50% back, 28 adds
— the secondary returned three of nine and was patched with Aguero (Georgia)
and Joseph (FSU).

**LSU keys, explained (the deep dive).**
1. *Leavitt's ball security.* Week 1 vs Clemson: 16-of-28 for 230, a
   touchdown and a pick, plus 12 carries for 113 and two rushing scores in
   a 51–10 rout. Week 2 vs Louisiana Tech: 25-of-38 for 344 (Trey'Dez Green
   6-104-1, Wilson 6-93, Harris 3-80), one touchdown, THREE interceptions,
   three rushing touchdowns; LSU had four giveaways and won by 31 because
   Louisiana Tech ran 31 times for minus-3 yards. Season: 41-of-66, 574
   yards, 2 TD, 4 INT, 135 rushing, 5 rushing TD; 0.320 PPA per play,
   second-lowest on the card, 16th on the Heisman board after falling from
   9th. Ole Miss's patched secondary (Aguero, Joseph) allowed 307 to
   Louisville's Kienholz and then 179 to Charlotte. The picks are the whole
   LSU key: the receivers are the
   best group on the card and it doesn't matter if the ball goes to the
   other team.
2. *Protect Leavitt in a hostile building.* Zero sacks taken against
   Clemson (LSU ran for 309 on 58 carries, 3.5 line yards), FIVE taken
   against Louisiana Tech (147 rushing at 3.3, 2.0 line yards, ten
   penalties for 101). Two different offensive lines in two weeks. Ole
   Miss's defense had three sacks against Louisville and one against
   Charlotte, a 34% stuff rate last week. In the Vaught, with the crowd the
   SEC prep called a "hostile-environment record attempt," the Louisiana
   Tech line loses.
3. *Baker's front vs Chambliss's escapes.* LSU's defense: four sacks and a
   1-of-13 third-down day against Clemson (145 total yards allowed, a 5%
   passing-downs rate), then seven sacks against Louisiana Tech (140 total
   yards, 3-of-14, minus-3 rushing). Eleven sacks, a 24% and then 14%
   success rate allowed — SP+'s projected No. 2 defense is playing like it.
   Chambliss is the counter: 21-of-36 for 336 and three touchdowns against
   Louisville, 23-of-26 for 225 against Charlotte, "statistically the best
   in the country at turning dead plays into first downs." Ole Miss
   converted 67% of its passing downs last week; LSU has allowed 5% and
   12%. Something gives.
4. *Kiffin's tempo in his old house.* The tempo-and-leverage passing game
   is what Kiffin built in Oxford, and the LSU version so far has run 94
   plays against Clemson and 85 against Louisiana Tech — 644 and 528
   yards. Golding called Kiffin's defenses for years and kept the spine
   (Echoles, Perkins); he knows the concepts. The tell will be third down:
   LSU is 11-of-16 and 8-of-17, Ole Miss's defense held Louisville to
   7-of-16 and Charlotte to 3-of-14. Whoever owns third down owns the
   tempo.

### Slides 46–47 — Ole Miss

**Corey's keys (Ole Miss):** Score in the Red Zone · Slow the game down · Protect Trinidad Chambliss.



**Ole Miss keys, explained (the deep dive).**
1. *Let Chambliss escape.* 21-of-36 for 336, three touchdowns and a pick
   against Louisville (Odom 3-66-1, Fields 5-47), then 23-of-26 for 225 and
   two scores against Charlotte with an 8-catch day from Deuce Alexander.
   Season 44-of-62, 561 yards, 5 TD, 1 INT; 0.494 PPA per play. He was
   sacked three times by Louisville — the escapes are how a sack becomes a
   completion — and LSU's front has eleven sacks in two games. The whole
   Ole Miss offense on Saturday is Chambliss buying time against the best
   pass rush he has faced; the 2025 SEC Newcomer of the Year did it for a
   season, and Kiffin knows exactly how, because he coached it.
2. *Lacy runs it.* Kewan Lacy: 17 for 61 (3.6) and a touchdown against
   Louisville, 13 for 87 (6.7) with a 28-yard run and two touchdowns
   against Charlotte; 300 carries last year. Ole Miss ran for 152 at 3.7
   against Louisville with 2.8 line yards — the real-game number — and 127
   at 5.3 against Charlotte. LSU's run defense: Clemson 26 carries for 40,
   Louisiana Tech 31 for minus-3, a 32% and 15% rushing success rate
   allowed. Lacy has to be enough of a threat to make the play-action
   honest; against this front that is the hardest key on the card.
3. *The patched secondary.* Three of nine returned; Aguero (Georgia) and
   Joseph (FSU) patched it. Louisville threw for 307 on it with Kienholz
   at 10.6 an attempt; Charlotte 179. Now LSU's receivers: Trey'Dez Green
   6-104-1 last week, Eugene Wilson 6-93 (4-35 the week before), Jackson
   Harris 3-80, Jayce Brown — the best group on the card, with a quarterback
   who threw for 344 and three picks. The picks (LSU key 1) are the
   secondary's chance; the 80- and 104-yard receivers are its risk.
4. *Special teams edge.* Ole Miss was No. 1 in SP+ special teams last year;
   LSU's were middle of the pack. In a game the machine has at 5.2 and the
   market at 3,
   a returned kick or a missed field goal is the whole gap between the two
   numbers. Ole Miss also gets the 2.5 for home and the crowd; the machine's
   number already includes the 2.5. The hidden yards are what it doesn't.

### Slide 48 — the score calls

Corey's slide shows **28 / 34** (top / bottom). If the top number is
the home team — the Week 2 receipts fit that reading — his call is
**LSU 34–28**; read the other way it is Ole Miss 34–28.
Confirm with him before air. Machine: **LSU 32–27**.

### Slide 49 — the number


**The arithmetic.** LSU 22.3 (#8) vs Ole Miss 14.6 (#14); Ole Miss gets the
2.5 → LSU by 5.2 → 62.4% → fair LSU −166 / Ole Miss +166. Market: DK LSU
−3 (−155 / Ole Miss +130); **total 59.5 — Monster Under**. First-seen Ole
Miss −1.5 on Aug 23, now LSU −3: four and a half points to LSU. Score call LSU 32–27.

**Stakes.**
- *Kiffin returns to Oxford*: the roster he built (44 transfers, the
  Portal King's magnum opus, Umanmielen and Dottery and Watkins poached from
  this very locker room) against the quarterback who refused to follow him
  (Chambliss, via lawsuit and injunction). The SEC prep called it "the most
  emotionally charged game of the 2026 season anywhere" and predicted "a
  hostile-environment record attempt."
- *Home team five straight*: Ole Miss 31–17 (2021), LSU 45–20 (2022), Ole
  Miss 55–49 (2023), LSU 29–26 (2024), Ole Miss 24–19 (2025). Every one of
  them at home.
- *Leavitt's three picks*: 25-of-38 for 344 and three interceptions against
  Louisiana Tech, sacked five times by a −9.6 team. LSU won 45–14 and lost
  1.5 rating points because the machine expected ~34. Chambliss went
  23-of-26 for 225 against Charlotte; 0.494 per play through two.
- *55–49 or 24–19*: the last three in this series were a 104-point shootout
  (2023) and two grinders (29–26, 24–19). LSU has 11 sacks in two games,
  Golding kept the defensive spine (Echoles, Perkins), and Leavitt has three
  picks on his card — the two fronts decide which version shows up.
  (Internal: the total is 59.5, a Monster Under number; this series has gone
  over as often as not.)

**Honesty box: "2.2 to LSU — quibble · Monster Under 59.5."** Machine 5.2,
market 3. The machine's LSU number still carries the 51–10 Clemson game;
five straight home wins in the series and a first-year coach on each
sideline are the hedges. The total is the play to talk about.

---

## Slide 50 — Superdog / Giant Killer rules and standings

Corey's slide: **3.5-point dogs or more; Superdog is any matchup, Giant
Killer is unranked vs Top 25; 5 points for a cover, 5 + the spread for a
win, 1 for a push. Standings: Man 23 (Duke beat Illinois), Machine 10.**

**The ledger going in**: superdogs 0-for-4 outright, 0 points under our rule
(the dog has to win; points = the spread at the pick). Corey's deck scores it
his way — 3.5-point dogs or more, 5 for a cover, 5 + the spread for a win, 1
for a push — and has it Man 23 (Colorado beat Georgia Tech in Week 1, Duke
beat Illinois in Week 2), Machine 10 (Coastal Carolina and Washington State
covered in Week 1; nothing in Week 2). Settle on one rulebook on air before
the Week 3 picks so next week's receipts grade cleanly.

---

## Slide 51 — Superdog / Giant Killer picks

Corey's picks: **Superdog FIU +7 at Florida Atlantic · Giant Killer Colorado
State +18 vs BYU.** The machine on his two: FIU–FAU is the one place the
machine is closer to him than to the market — machine FAU −3.6, FIU 40% to
win outright, against a market FAU −6.5 (that game's total, 62.5, is the
second-highest on the board); Colorado State it does not like — machine BYU
−19.7, Colorado State 11% to win, and the market agrees (BYU −17.5).
Machine picks: Sacramento State +27.5 vs North Dakota State and Utah State
+28.5 at #17 Utah — the reasoning is on the next slide.

---

## Slide 52 — Our predictions (the closer)

Scores are the machine margin laid over the market total, in kickoff order:
Texas Tech 33–20 (Bovada's 53; DK hasn't posted a total), Louisville 30–29,
South Carolina 32–27, Auburn 27–26, LSU 32–27.

**★ SUPERDOG (any FBS game): Sacramento State +27.5 vs North Dakota State**
— machine 24% (ML +2200, market 4%), EV 6.5. Runners-up: Charlotte +17.5 at
App State (27.5%, EV 4.8), Tulane +20.5 at Kansas State (23%, EV 4.7), Ball
State +14.5 at Liberty (30%, EV 4.4), Akron +24.5 at Minnesota (18%, EV 4.4).

*Say the caveat first*: this is the widest machine-market disagreement on the
whole board — 20 points. The machine has NDSU at −3.6 (an FCS power carrying
a July FPI prior, one rated game, +4.7 for beating Jacksonville State) and
Sacramento State at −13.5 (two rated losses, 49–3 at Fresno State); NDSU by
about 7 at Sacramento. The market says 27.5 (26.5 on Sunday; DK opened
23.5). When the machine and the market are 20 points apart, one of them is wrong about who these teams are, and the
market has watched more of both. It stays the pick because the rule is the
rule (CFBD lists both as FBS in 2026); the honest framing is "the machine's
number, not ours." If you'd rather talk about a real one, Charlotte +17.5 at
App State is next: Charlotte covered at Ole Miss (41–9 against a −47.5), App
State hasn't played a rated team the machine trusts, and it's a 1-in-4 shot at
17.5 points.

**★ GIANT KILLER (vs an AP top-25 favorite): Utah State +28.5 at #17 Utah**
— machine 12.5% (ML +2200, market 4%), EV 3.6. Runners-up: New Mexico +22.5
at #24 Oklahoma (14%, EV 3.2), Wake Forest +20.5 vs #5 Miami (14%, EV 2.9),
Arkansas +24.5 vs #2 Georgia (11%, EV 2.7), Rutgers +23.5 vs #12 USC (11%,
EV 2.5).

*Why Utah State*: a one-in-eight shot at 28.5 points beats a one-in-seven
shot at 22.5. It's the rivalry game (the Battle of the Brothers), Utah is
+4.3 in our ratings after 43–10 over Arkansas, and Utah State was +3.3 last
week. Say the honest thing: 12.5% is the machine's number and the market's
5% is probably closer.

**Man vs Machine, the five calls side by side** (his score slides read
home team on top; confirm): Houston–Texas Tech — Man Houston 35–24, Machine
Texas Tech 33–20 (**the one disagreement on a winner**); SMU–Louisville —
Man Louisville 35–34, Machine Louisville 30–29; State–South Carolina — Man
South Carolina 31–27, Machine South Carolina 32–27; Florida–Auburn — Man
Auburn 28–27, Machine Auburn 27–26; LSU–Ole Miss — Man LSU 34–28, Machine
LSU 32–27. Four of five winners agree and three of the four are within a
point on the margin; Friday night is the split.

---

## Pre-record checklist

1. Re-pull lines (`edge_report.py --week 3 --view ml --publish`) — Bovada's
   Houston–Texas Tech total (53) is up; if DK posts one, the score call
   re-computes on rebuild, as do the Monster Under flags and the superdog
   points.
2. `hot_seat_heisman.py --week 3 --refresh` if DraftKings moves the Heisman
   board again; update MARKET/MARKET_DATE in the module by hand.
3. `make_episode_deck.py` → push with `push_deck.py --pptx
   decks\2026_Week3_Episode4.pptx --file-id <Ep4 id>` (the Ep4 file is shared with Corey -
   the last_modifier guard runs before every push; Ep3's file is the record and never gets pushed again).
4. The AP fallback in the deck is the Week 3 poll; once CFBD attaches it,
   the cache takes over automatically.
5. Frozen for next week's grading: TTU −13, LOU −1, SC −5, AUB −0.5, LSU −5
   (machine lines as posted) + Sacramento State +27.5 / Utah State +28.5 (the
   spread at the pick — whatever the pre-record pull shows).

*Drafted 2026-09-13, numbers synced 2026-09-15 to card_data_week3.json (Tue
6:18 PM MT pre-record pull),
ratings_current_2026.json (100 games), boards_week3.json, CFBD box scores,
the conference deep-dive prep files and scouting_top25.json. Machine-drafted
— review before air.*

---

## Appendix — the machine's full Week 3 board (every rated FBS game)

Every game the machine can price this week, in kickoff order — 57 games with a rating on both sides and a line at DraftKings or Bovada (lines as of the Tue Sep 15, 6:18 PM MT pull; FCS and unrated opponents are skipped, 254 of them). Machine = in-season rating gap + 2.5 HFA, posted to the half point. Score call = the machine margin laid over the market total (no totals model). ⚑ = Monster Under total (top decile, ≥58.5). Gap = machine win prob minus the no-vig market. Use it for any game Corey adds to his card; the five on ours are in bold.

| Kick (ET) | Game | Machine | Market (DK) | O/U | Machine win % | Score call | Gap (pp) | Flags |
|---|---|---|---|---|---|---|---|---|
| Thu 7:30 PM | Syracuse at Pittsburgh | Pittsburgh −13 | Pittsburgh −10.5 | 51.5 | Pittsburgh 80% | Pittsburgh 32–Syracuse 19 | +1.8 Pittsburgh | — |
| Fri 7:30 PM | Miami at Wake Forest | Miami −17.5 | Miami −20.5 | 56.5 | Miami 86% | Miami 37–Wake Forest 20 | +3.6 Wake Forest | — |
| Fri 8:00 PM | **Houston at Texas Tech** | Texas Tech −13 | Texas Tech −7.5 | 53 | Texas Tech 79% | Texas Tech 33–Houston 20 | +5.7 Texas Tech | CLV+6 |
| Sat 11:30 AM | Coastal Carolina at Delaware | Delaware −8 | Delaware −4.5 | 57.5 | Delaware 70% | Delaware 33–Coastal Carolina 25 | +4.3 Delaware | — |
| Sat 12:00 PM | Tulane at Kansas State | Kansas State −12 | Kansas State −20.5 | 49.5 | Kansas State 77% | Kansas State 31–Tulane 19 | +14.0 Tulane | YEL |
| Sat 12:00 PM | North Texas at Texas State | North Texas −2.5 | Texas State −3 | 63.5 ⚑ | North Texas 56% | North Texas 33–Texas State 30 | +13.2 North Texas | RED |
| Sat 12:00 PM | Arizona State vs Kansas (N) | Arizona State −1.5 | Arizona State −5.5 | 50.5 | Arizona State 54% | Arizona State 26–Kansas 24 | +12.3 Kansas | — |
| Sat 12:00 PM | Akron at Minnesota | Minnesota −15 | Minnesota −24.5 | 49.5 | Minnesota 82% | Minnesota 32–Akron 17 | +10.9 Akron | YEL CLV+2 |
| Sat 12:00 PM | Bowling Green at Iowa State | Iowa State −18 | Iowa State −23.5 | 44.5 | Iowa State 86% | Iowa State 31–Bowling Green 13 | +6.1 Bowling Green | — |
| Sat 12:00 PM | Georgia at Arkansas | Georgia −20 | Georgia −24.5 | 54.5 | Georgia 89% | Georgia 37–Arkansas 17 | +4.4 Arkansas | CLV+7 |
| Sat 12:00 PM | Buffalo at Penn State | Penn State −29.5 | Penn State −40.5 | 49.5 | Penn State 96% | Penn State 39–Buffalo 10 | +3.0 Buffalo | YEL |
| Sat 12:00 PM | North Carolina at Clemson | Clemson −4.5 | Clemson −3.5 | 43.5 | Clemson 62% | Clemson 24–North Carolina 19 | +1.4 Clemson | EDGE_FLIP CLV+5 |
| Sat 12:00 PM | Kent State at Ohio State | Ohio State −44.5 | Ohio State −52.5 | 59.5 ⚑ | Ohio State 100% | Ohio State 52–Kent State 7 | +0.3 Kent State | YEL |
| Sat 12:30 PM | Eastern Michigan at Wisconsin | Wisconsin −21.5 | Wisconsin −24.5 | 45.5 | Wisconsin 91% | Wisconsin 34–Eastern Michigan 12 | +2.3 Eastern Michigan | — |
| Sat 12:45 PM | NC State at Vanderbilt | Vanderbilt −10 | Vanderbilt −3.5 | 50.5 | Vanderbilt 74% | Vanderbilt 30–NC State 20 | +13.1 Vanderbilt | YEL |
| Sat 1:00 PM | Wyoming at Central Michigan | Central Michigan −3.5 | Central Michigan −1.5 | 39.5 | Central Michigan 59% | Central Michigan 21–Wyoming 18 | +7.1 Central Michigan | — |
| Sat 3:00 PM | Temple at Toledo | Toledo −7.5 | Toledo −5.5 | 50.5 | Toledo 68% | Toledo 29–Temple 22 | +2.4 Toledo | — |
| Sat 3:30 PM | Utah State at Utah | Utah −18.5 | Utah −28.5 | 56.5 | Utah 87% | Utah 38–Utah State 19 | +8.3 Utah State | YEL |
| Sat 3:30 PM | Kentucky at Texas A&M | Texas A&M −21 | Texas A&M −16.5 | 50.5 | Texas A&M 90% | Texas A&M 36–Kentucky 15 | +4.5 Texas A&M | — |
| Sat 3:30 PM | USC at Rutgers | USC −20 | USC −23.5 | 59.5 ⚑ | USC 89% | USC 40–Rutgers 20 | +3.9 Rutgers | — |
| Sat 3:30 PM | Miami (OH) at Cincinnati | Cincinnati −18.5 | Cincinnati −14.5 | 49.5 | Cincinnati 87% | Cincinnati 34–Miami (OH) 16 | +3.1 Cincinnati | — |
| Sat 3:30 PM | Florida State at Alabama | Alabama −18.5 | Alabama −19.5 | 48.5 | Alabama 87% | Alabama 34–Florida State 15 | +2.6 Florida State | EDGE_FLIP CLV+4 |
| Sat 3:30 PM | **SMU at Louisville** | Louisville −1 | Louisville −1.5 | 59.5 ⚑ | Louisville 54% | Louisville 30–SMU 29 | +2.4 Louisville | — |
| Sat 3:30 PM | UTEP at Michigan | Michigan −31 | Michigan −35.5 | 49.5 | Michigan 97% | Michigan 40–UTEP 9 | +1.6 UTEP | — |
| Sat 4:00 PM | Ball State at Liberty | Liberty −8 | Liberty −14.5 | 49.5 | Liberty 70% | Liberty 29–Ball State 21 | +13.3 Ball State | YEL |
| Sat 4:00 PM | Louisiana Tech at Baylor | Baylor −18.5 | Baylor −19.5 | 53.5 | Baylor 87% | Baylor 36–Louisiana Tech 18 | +2.4 Louisiana Tech | CLV+2 |
| Sat 4:00 PM | Stanford at Duke | Duke −12.5 | Duke −9.5 | 50.5 | Duke 78% | Duke 31–Stanford 19 | +2.3 Duke | — |
| Sat 4:00 PM | Western Kentucky at Indiana | Indiana −36 | Indiana −44.5 | 60.5 ⚑ | Indiana 99% | Indiana 48–Western Kentucky 12 | +1.1 Western Kentucky | YEL |
| Sat 4:15 PM | **Mississippi State at South Carolina** | South Carolina −5 | South Carolina −4 | 58.5 | South Carolina 63% | South Carolina 32–Mississippi State 27 | +1.2 South Carolina | CLV+3.5 |
| Sat 6:00 PM | Charlotte at App State | App State −9.5 | App State −17.5 | 51.5 | App State 73% | App State 30–Charlotte 21 | +14.7 Charlotte | YEL CLV+2 |
| Sat 6:00 PM | Florida International at Florida Atlantic | Florida Atlantic −3.5 | Florida Atlantic −7 | 62.5 ⚑ | Florida Atlantic 60% | Florida Atlantic 33–Florida International 29 | +10.8 Florida International | — |
| Sat 6:00 PM | East Carolina at Old Dominion | East Carolina −0.5 | Old Dominion −3 | 49.5 | East Carolina 50% | East Carolina 25–Old Dominion 25 | +7.3 East Carolina | RED |
| Sat 6:30 PM | Marshall at Missouri State | Missouri State −4.5 | Marshall −3.5 | 51.5 | Missouri State 61% | Missouri State 28–Marshall 24 | +21.4 Missouri State | RED · STRUCT |
| Sat 7:00 PM | UConn at Southern Miss | Southern Miss −9.5 | UConn −3 | 54.5 | Southern Miss 73% | Southern Miss 32–UConn 22 | +31.2 Southern Miss | RED · STRUCT |
| Sat 7:00 PM | Georgia Southern at Jacksonville State | Georgia Southern −2 | Jacksonville State −3 | 52.5 | Georgia Southern 55% | Georgia Southern 27–Jacksonville State 25 | +16.6 Georgia Southern | RED · STRUCT |
| Sat 7:00 PM | **Florida at Auburn** | Auburn −0.5 | Florida −2.5 | 53.5 | Auburn 52% | Auburn 27–Florida 26 | +8.8 Auburn | CLV+4 |
| Sat 7:00 PM | Western Michigan at Rice | Western Michigan −8.5 | Western Michigan −9.5 | 43.5 | Western Michigan 70% | Western Michigan 26–Rice 18 | +6.1 Rice | EDGE_GONE CLV+2 |
| Sat 7:00 PM | Nevada at Middle Tennessee | Nevada −7 | Nevada −3.5 | 50.5 | Nevada 67% | Nevada 29–Middle Tennessee 22 | +5.2 Nevada | CLV-3 |
| Sat 7:00 PM | Ohio at South Alabama | South Alabama −4.5 | South Alabama −5.5 | 51.5 | South Alabama 61% | South Alabama 28–Ohio 24 | +5.0 Ohio | — |
| Sat 7:00 PM | Georgia State at UCF | UCF −16 | UCF −18.5 | 50.5 | UCF 84% | UCF 33–Georgia State 17 | +4.6 Georgia State | CLV+2.5 |
| Sat 7:00 PM | Troy at Missouri | Missouri −26 | Missouri −26.5 | 50.5 | Missouri 94% | Missouri 38–Troy 12 | +0.9 Troy | — |
| Sat 7:30 PM | Colorado at Northwestern | Colorado −0.5 | Northwestern −3.5 | 48.5 | Colorado 51% | Colorado 25–Northwestern 24 | +12.8 Colorado | RED |
| Sat 7:30 PM | New Mexico at Oklahoma | Oklahoma −17.5 | Oklahoma −22.5 | 46.5 | Oklahoma 86% | Oklahoma 32–New Mexico 15 | +6.9 New Mexico | — |
| Sat 7:30 PM | **LSU at Ole Miss** | LSU −5 | LSU −3 | 59.5 ⚑ | LSU 62% | LSU 32–Ole Miss 27 | +4.1 LSU | CLV+4.5 |
| Sat 7:30 PM | West Virginia vs Virginia (N) | Virginia −13 | Virginia −10 | 53.5 | Virginia 80% | Virginia 33–West Virginia 20 | +2.9 Virginia | — |
| Sat 7:30 PM | Michigan State at Notre Dame | Notre Dame −24.5 | Notre Dame −29.5 | 52.5 | Notre Dame 93% | Notre Dame 39–Michigan State 14 | +2.0 Michigan State | — |
| Sat 7:30 PM | BYU at Colorado State | BYU −19.5 | BYU −17.5 | 52.5 | BYU 89% | BYU 36–Colorado State 16 | +1.6 BYU | CLV+3.5 |
| Sat 7:30 PM | Virginia Tech at Maryland | Virginia Tech −2.5 | Virginia Tech −3 | 53.5 | Virginia Tech 56% | Virginia Tech 28–Maryland 25 | +0.1 Maryland | — |
| Sat 7:45 PM | Kennesaw State at Tennessee | Tennessee −33.5 | Tennessee −35.5 | 59.5 ⚑ | Tennessee 98% | Tennessee 47–Kennesaw State 13 | +0.1 Kennesaw State | — |
| Sat 8:00 PM | UAB at Louisiana | Louisiana −10.5 | Louisiana −7.5 | 56.5 | Louisiana 75% | Louisiana 34–UAB 23 | +2.3 Louisiana | CLV-2.5 |
| Sat 8:00 PM | Arkansas State at TCU | TCU −18.5 | TCU −20.5 | 56.5 | TCU 87% | TCU 38–Arkansas State 19 | +2.1 Arkansas State | — |
| Sat 8:00 PM | UTSA at Texas | Texas −31 | Texas −30.5 | 58.5 | Texas 97% | Texas 45–UTSA 14 | +1.2 Texas | — |
| Sat 10:00 PM | James Madison at San Diego State | San Diego State −3.5 | San Diego State −2.5 | 46.5 | San Diego State 60% | San Diego State 25–James Madison 21 | +4.8 San Diego State | — |
| Sat 10:30 PM | North Dakota State at Sacramento State | North Dakota State −11.5 | North Dakota State −27.5 | 51.5 | North Dakota State 76% | North Dakota State 32–Sacramento State 20 | +19.6 Sacramento State | YEL STRUCT |
| Sat 10:30 PM | Northern Illinois at Arizona | Arizona −24 | Arizona −34.5 | 49.5 | Arizona 93% | Arizona 37–Northern Illinois 13 | +4.9 Northern Illinois | YEL |
| Sat 11:00 PM | Purdue at UCLA | UCLA −11 | UCLA −14 | 52.5 | UCLA 76% | UCLA 32–Purdue 21 | +7.5 Purdue | — |
| Sat 11:00 PM | Fresno State at San José State | Fresno State −5.5 | Fresno State −6.5 | 50.5 | Fresno State 63% | Fresno State 28–San José State 23 | +5.4 San José State | — |

Flags: RED = the machine picks the dog outright against a spread of 3+; YEL = same side, 6+ point edge; STRUCT = machine and no-vig moneyline win probs differ by 15+ pp; CLV±x = the line has moved x points toward (+) or against (−) the machine's side since first-seen; EDGE_GONE / EDGE_FLIP = a first-seen edge decayed or reversed.
