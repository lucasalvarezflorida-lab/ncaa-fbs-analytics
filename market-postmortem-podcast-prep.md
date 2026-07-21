# "What the Books Actually Miss" — Podcast Prep

*Compiled July 21, 2026, entirely from the repo's own studies:
[MARKET_POSTMORTEM.md](market-postmortem/MARKET_POSTMORTEM.md) (CFB 2021–25,
3,944 games, 57 slices) and
[MARKET_POSTMORTEM_PHASE2.md](market-postmortem/MARKET_POSTMORTEM_PHASE2.md)
(NFL 2021–25, 1,424 games; NBA 2011–21, 13,893 games). Every claim below has a
receipt in those files or their CSVs. Methodology in one breath: exact binomial
tests, Benjamini–Hochberg false-discovery correction at q=0.10, and a
persistence rule — a pattern must repeat in ~80% of seasons or it's dead.
Break-even at -110 juice is 52.38%.*

---

## Cold open (the hook)

We graded the sportsbooks' closing lines against five years of college
football, five years of NFL, and a decade of NBA — about nineteen thousand
games. Not "did my system win" — did *the market's own number* miss in any
repeatable direction. The answer: almost never. Out of 141 strategy slices
across three sports, a **handful** survive honest statistics, every one of
them is in college football, and they all tell the same story: **the books
don't misprice football, they misprice attention.**

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
against the close, nothing graduates before 52.38% on 100+ bets. *"We wrote
the rules down in July so we can't cheat in December — most of these can't
even mathematically graduate until 2027."*

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

## If asked "so what do you actually do with this?"

The two CFB findings are automated in the season workbook: a U-TAIL chip
flags top-decile totals, RED upset alerts suppress the moneyline framing on
+401 road dogs, every alert gets a CLV grade, and the maybe-patterns
(ranked-vs-ranked favorites, early unders, G5 dogs) sit on a paper-bet Watch
List with the same 52.38%-on-100+ graduation bar as the new NFL list. First
2026 grades start rolling in Week 1 (~Aug 29); ranked-favorite tracking wakes
up when the AP poll drops in late August. That's a natural follow-up episode.
