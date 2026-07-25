# "What the Books Actually Miss" — Podcast Prep

*Compiled July 21, 2026 (updated July 25 with the identity batteries),
entirely from the repo's own studies:
[MARKET_POSTMORTEM.md](market-postmortem/MARKET_POSTMORTEM.md) (CFB 2021–25,
3,944 games, 57 slices),
[MARKET_POSTMORTEM_PHASE2.md](market-postmortem/MARKET_POSTMORTEM_PHASE2.md)
(NFL 2021–25, 1,424 games; NBA 2011–21, 13,893 games), and the four
team/coach/ranking batteries in `market-postmortem/*trends*.py`. Every claim
below has a receipt in those files or their CSVs. Methodology in one breath:
exact binomial tests, Benjamini–Hochberg false-discovery correction at q=0.10,
and a persistence rule — a pattern must repeat in ~80% of seasons or it's
dead. Break-even at -110 juice is 52.38%.*

---

## Cold open (the hook)

We graded the sportsbooks' closing lines against five years of college
football, five years of NFL, and a decade of NBA — about nineteen thousand
games. Not "did my system win" — did *the market's own number* miss in any
repeatable direction. The answer: almost never. Out of 141 strategy slices
across three sports, a **handful** survive honest statistics, every one of
them is in college football, and they all tell the same story: **the books
don't misprice football, they misprice attention.** Then we went hunting for
the angles fans actually ask about — is my team cursed, does this coach
always go over — and ran another 804 team-, coach-, and ranking-based tests.
Survivors: **zero.**

## Segment 1 — CFB: the two real misses

**The spread market is boring and perfect.** Five-year systematic bias:
+0.05 points. Home ATS 50.4%. No bye-week, rivalry, favorite-size, or
conference angle survives. Line for air: *"If someone's selling you a college
ATS system, they're selling you a coin with extra steps."*

**Miss #1 — shootout totals are set too high.** Regress actual points on the
closing total: slope 0.84, five standard errors below fair. At a 70 total the
market overshoots reality by ~2 points. Totals of 60+ went **Under 55.1%**
(413–337–11, +5.1% ROI), over 50% in all five seasons, survives correction.
Mirror image at the bottom: totals ≤42 went Over 57.5% (small sample,
exploratory). The market expects chaos and overprices the chaos.

**Miss #2 — lottery-ticket moneylines.** Flat-betting every +401-or-longer
dog lost **22.9 cents on the dollar** (101 winners in 1,035 bets). Heavy
favorites (-401+) lost only 3% — less than the vig. Dogs the market said were
10% actually won 8.3%. Sub-plot that survived correction: road dog MLs bled
-10.9% while home dogs lost just -1.2%. *"The books' worst-priced product is
exactly the bet that feels like a free shot."*

**Honest caveats to say on air:** the 60+ bucket is shrinking (212 games in
2021 → 87 in 2025) as scoring fell and books adjust — assume decay. And 2022
was the one year the longshots hit (+41.9%); someone in the comments will
remember 2022.

## Segment 2 — NFL: the sharpest board in sports

42 slices — primetime, byes, rest, division games, weather, every spread and
total bucket — and **zero** survive correction. Every famous angle is priced.
The favorite–longshot bias that torched college longshots? NFL +251 dogs lost
-9.4% — not significant. Totals slope 0.93 with fair inside the error bars.

What's *close*: primetime unders 55.7% (5/5 seasons), 7–9.5-point dogs 55.9%
ATS, weeks-1–4 unders 54.9% (5/5). All fail correction. New this summer:
those are now **pre-registered** for 2026
([NFL_WATCHLIST_2026_PREREG.md](market-postmortem/NFL_WATCHLIST_2026_PREREG.md),
committed in July, before a single 2026 line existed) — paper bets, graded
against the close, nothing graduates before 52.38% on 100+ bets. The tracker
(`nfl_watchlist.py`) is already live: **89 provisional paper bets logged off
July lookahead lines**, starting with the Thursday opener (Broncos–Chiefs
under 42.5). *"We wrote the rules down in July so we can't cheat in
December — most of these can't even mathematically graduate until 2027."*

Fun anecdote, clearly labeled as one: unders in 15+ mph wind went 57-36-2
(61.3%) — but that's 93 games, and it's excluded from the watch list on
purpose.

## Segment 3 — NBA: the market that knows things

Ten seasons, 13,893 games. No favorite–longshot bias — dogs and favorites
both lose roughly the vig. The decade's quirks:

* **Totals steam was real information.** Follow any 1+ point total move and
  you beat the close 51.4% of the time (10,471 moves, 9 of 11 seasons). Real,
  persistent, significant — and still unprofitable after juice. The market
  moved for a reason; it just didn't leave you any of the reason.
* **Openers shade the wrong way — opposite of college.** CFB openers are too
  chalky (dogs beat the open 51.3%); NBA openers shade toward dogs, and
  favorites gained value by tip. Both markets fix themselves by kickoff/tipoff.
* Home ATS 49.3% — the market *over*-rated home court all decade, and knew it
  by the close.

Data-honesty war story worth telling on air: 933 archive games had spread and
total swapped in the source. Before the repair, the data showed home dogs
covering 55.9% — a career-making "edge" that was literally a file bug. *"The
most exciting result in any dataset is usually a typo."*

## Segment 4 — the synthesis (the actual thesis)

Rank the boards by money and attention per game: NFL > NBA > CFB. Every bias
shrinks in that exact order:

| bias | CFB | NFL | NBA |
|---|---|---|---|
| longshot ML overpricing | **-22.9% ROI** | -9.4% (noise) | -3.3% (noise) |
| totals tail compression (slope, 1.00 = fair) | **0.84** | 0.93 | 0.98 |

The market doesn't misprice a *sport* — it misprices **thin markets**:
hundreds of college games a weekend, and the only public money on lopsided
ones is chasing lottery tickets and overs. Sixteen NFL games a week under
industrial sharp action have none of it. *"Edges don't live where the games
are — they live where the crowds aren't."*

## Segment 5 — "but what about MY team?" (the identity batteries)

The questions every listener actually has: does Miami always blow the over,
does Kiffin always go under, fade the preseason hype? We tested all of it —
every NFL team (96 tests), every CFB program with 30+ graded games (399),
every coach pooled across schools (299), and preseason AP / FPI / model
rankings (10). **804 tests, raw hits almost exactly what a fair coin
predicts, zero survive correction.** Your team is not cursed and your coach
is not a system.

The two showpieces, because they're perfect radio:

* **Lane Kiffin's Ole Miss went UNDER 70.8% of the time, 2021–24** — under
  in all four seasons, best totals number in the whole coach battery. The
  points-machine reputation, priced; the actual slow-tempo teams, not.
* **Lincoln Riley's USC went OVER 70.0%, 2022–24.** Elite offense, no
  defense, every casual's prior.

Then the punchline: both had knowable 2025 attributions, so we graded 2025
as a true out-of-sample year. **Kiffin 2025: 6 overs, 5 unders. Riley 2025:
7 overs, 6 unders.** Two coin flips. *"A 70% trend on 45 games is what noise
looks like — and even if some of it was real, the books had re-priced it by
year five."* (Also: Kiffin's 'trend' was fit entirely on Ole Miss personnel,
and he's at LSU now. The sample wouldn't even transfer.)

Honest color for the segment: the team batteries' top hits were mostly
*one-possession-game* rates — Ohio State in close games 17.9% of the time,
Nebraska 58.6% (the famous curse) — but those describe team quality, not
market error. Ohio State blows teams out AND the market prices it; their ATS
record is a coin flip. Notre Dame covering 66.7% and Marcus Freeman covering
70.7% are the same noise wearing two hats, and both were already regressing
by 2025.

One thread survived with an asterisk: **teams in the prior year's FPI top 30
failed to cover, all five seasons** — fading them won 53.7% (elite-vs-elite
excluded). The catch: it's a post-hoc slice that never faced the original
FDR battery, and 53.7% barely clears the 52.38% vig line. So it's now the
**fifth paper rule on the workbook's Watch List** (`FPI_FADE`, registered
preseason, 21 bets already logged) — 2026 is its trial year, not its victory
lap. *"The public buys last year's brand names; the books shade into it and
keep almost every cent."*

## Listener takeaways (rapid-fire closer)

1. Never buy a +400-or-longer college moneyline; if you must own a longshot,
   own the home team, and know it's entertainment.
2. In college, the 55–60% patterns live in totals, not spreads — and they're
   decaying as books adjust.
3. Chasing steam is dead money in all three sports (49.5% CFB, no edge
   anywhere vs the close). If you like a college dog, bet it *early* —
   openers lean chalky and the value is gone by kickoff.
4. The close is the best free forecast in sports. Grade yourself against it
   (closing-line value) before you grade yourself against results.
5. Anyone selling an NFL system is selling the vig. 0-for-42.
6. Team and coach trends are astrology with box scores — 804 tests, zero
   survivors, and the two prettiest ones (Kiffin unders, Riley overs) died
   the very next season. Situations persist; names get re-priced weekly.

## If asked "so what do you actually do with this?"

The two CFB findings are automated in the season workbook: a U-TAIL chip
flags top-decile totals, RED upset alerts suppress the moneyline framing on
+401 road dogs, every alert gets a CLV grade, and the maybe-patterns —
ranked-vs-ranked favorites, early unders, G5 dogs, and now the FPI-elite
fade — sit on a paper-bet Watch List with the same 52.38%-on-100+ graduation
bar as the NFL list, whose tracker is already logging bets off July lines.
First 2026 grades start rolling in Week 1 (~Aug 29); ranked-favorite
tracking wakes up when the AP poll drops in late August. That's a natural
follow-up episode.
