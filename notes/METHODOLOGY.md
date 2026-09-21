# NCAA FBS Football Analytics Model

A team-profile and ratings system covering every D1 FBS football program. Built
as the football counterpart to the existing NHL model, mirroring its data
fetch → compute → output pipeline architecture but with a methodology purpose-
built for descriptive analysis (what each team is) rather than the NHL model's
predictive purpose (what a closing line is missing).

**This project is for statistical analysis only — not for betting.** The NHL
model exists for that. Where the NHL model produces value picks vs. closing
lines, this model produces team profiles, unit-level sub-ratings, and
historical context for season-long study.

The deliverable is a single Excel workbook (`NCAA_FBS_Teams.xlsx`) with one
sheet per program (~134 teams when complete) plus a league overview sheet
ranking all teams by composite rating.

---

## What it does

Every Monday morning, the orchestrator runs five Python phases in sequence:

1. **Fetch SP+ ratings** — pulls Bill Connelly's season-to-date opponent-
   adjusted SP+ from the CollegeFootballData (CFBD) API. SP+ is the most
   widely cited public FBS rating system and is opponent-adjusted by
   construction, so we don't have to re-derive that wheel.
2. **Fetch unit splits** — pulls rushing/passing offense and rushing/passing
   defense from CFBD's stats endpoints so we can compute five sub-ratings
   per team instead of one offense and one defense.
3. **Fetch QB context** — pulls the projected QB1 plus their previous-
   school production for the transfer regression prior, and recruiting
   rank for any true freshman starters.
4. **Fetch returning production** — pulls each team's percentage of
   returning EPA from the previous season. This is the strongest single
   preseason signal in college football and serves as the prior for
   early-season ratings.
5. **Consolidate ratings** — blends current-season SP+ with the returning-
   production prior, applies the QB modifier and rest modifier, computes
   sub-ratings, and writes the JSON contract the workbook consumes.

The workbook then reads the JSON to refresh each team sheet's ratings,
roster, and stat tables.

---

## The 0-10 rating methodology

This is the heart of the model. Read this before changing parameters.

### Base rating: SP+ rescaled

The base unit rating comes directly from **Bill Connelly's SP+** (offense
and defense components, plus rushing/passing splits) pulled from CFBD.
SP+ is opponent-adjusted, pace-adjusted, and uses a 30-year body of
peer-reviewed methodology. We don't try to beat it — we lift it as the
input and add value with the football-context modifiers that follow.

SP+ comes on its native scale (a normal-distributed adjusted points-per-
game number; ~0 is FBS average, positive is above). We rescale to 0-10
using **z-score normalization with fixed bounds**:

    rating = 5 + (z_score × 5 / 2.5)
    # then clipped to [0, 10]

So z = 0 (FBS median) → 5.0; z = +2.5 → 10.0; z = −2.5 → 0.0.

**Why z-score instead of min-max** (the NHL model's approach): min-max
re-scales to the season's distribution each year, so a 7.5 in 2025 might
represent different absolute performance than a 7.5 in 2026. That makes
historical comparison meaningless. Z-score with fixed bounds keeps ratings
comparable across seasons — important since the team-sheet "History"
section is one of the project's main use cases.

### Sub-ratings: five units, not two

The composite hides too much information for a descriptive use case.
Miami's 2025 offense was the textbook example: Pass O #24, Rush O #88.
A single "offense" rating of ~6.5 (the average) would have masked both
the strength and the weakness. So each team sheet exposes five sub-ratings
on the 0-10 scale:

- **Rush O** — SP+ rushing offense component
- **Pass O** — SP+ passing offense component
- **Rush D** — SP+ rushing defense component
- **Pass D** — SP+ passing defense component
- **Special Teams** — SP+ ST rating, or a fallback computed from FG%,
  punt net yards, and return value when ST is sparse

Plus a **composite** that rolls them up:

    composite = (0.25×rush_o + 0.25×pass_o + 0.25×rush_d + 0.25×pass_d
                  + 0.1×st_rating) / 1.1

The 4-way split across O/D phases reflects empirical phase-impact studies;
the 0.1 weight on ST reflects its smaller (but non-trivial) contribution
to scoring margin variance.

### Modifiers (additive on top of base)

Three modifiers can adjust the base rating. All are capped so short-term
signals can refine the base but cannot override it.

**QB modifier** (offense sub-ratings only, capped at ±1.5):
The Mensah-at-Miami problem is what this addresses. A QB's previous-school
EPA doesn't transfer one-to-one to a new team's offense. The modifier is:

    qb_modifier = α × (qb_prior_epa_per_pass − league_avg_epa)

where α is **regression-to-mean weighting** based on context:
- Established Power 4 starter, same school: α = 0.90
- Power 4 transfer (e.g., Mensah from Duke to Miami): α = 0.55
- Group of 5 to Power 4 transfer: α = 0.35
- True freshman or first-time starter: α = 0.20, applied to a
  recruiting-rank-derived prior rather than EPA

This explicitly handles the case where a QB's previous production was
inflated or deflated by a different supporting cast.

**Rest modifier** (offense + defense, split evenly, capped at ±0.25):
Short week (Thursday after Saturday, 4-5 days): -0.25. Normal week
(7 days): 0.00. Bye week (14 days): +0.15. Less granular than NHL's
per-day-of-rest table because the cadence is weekly.

**Form modifier** — *demoted, currently inactive*:
The original design (last-3-games vs. season) was a betting-model
holdover. For descriptive analysis, season-long opponent-adjusted SP+
already captures team quality; a 3-game form blip mostly adds variance.
The script still exists as a stub for future use but is multiplied
by 0.0 in the consolidation phase.

### Returning-production prior (early-season weeks only)

The biggest single preseason signal in college football is **how much
EPA-producing talent a team is returning**. The NHL model didn't need
this because hockey rosters are stable; college football has massive
portal and graduation churn.

For Weeks 1-6, the rating is a weighted blend of current-season SP+
and a returning-production-adjusted previous-season SP+:

    blend_weight_current = min(week_number / 6, 1.0)
    rated_value = (blend_weight × current_sp_plus
                   + (1 − blend_weight) × prior_adjusted_sp_plus)

The prior adjustment scales the previous season's SP+ by the returning-
production percentage, so a team returning 25% of EPA-producing snaps
gets pulled toward FBS average; a team returning 85% sees little
adjustment. By Week 6, the prior has fully decayed and current-season
SP+ stands on its own.

This prevents the Week 1 — "Alabama lost to UL-Monroe by 3, are they
suddenly a Group of 5 program?" — overreaction problem.

### Putting it together

For a Week 8 rating after the prior has faded:

    base = sp_plus_unit_rescaled_to_0_10
    offensive_unit_rating = clip(base + qb_modifier + 0.5×rest_modifier, 0, 10)
    defensive_unit_rating = clip(base + 0.5×rest_modifier, 0, 10)
    composite = weighted_sum_of_subratings

For a Week 3 rating during the prior-blending period, the `base` term
is the blended (current, prior) value before modifiers apply.

---

## Architecture (4 layers)

**Data layer.** Five fetch scripts, each owning one external data source.
If CFBD changes their schema, only that script breaks; everything
downstream keeps working off the previous week's snapshot.

**Ratings layer.** Builds sub-ratings from SP+ unit splits, applies QB
and rest modifiers, blends with returning-production prior during early
weeks. Same caps-and-modifiers shape as the NHL model but every parameter
re-derived for the descriptive purpose.

**Projection layer.** Pure math, no I/O. Takes two team rating objects
and produces an expected margin and total points — for reference in the
sheet, not for betting. Sigma calibrated against the previous season's
games.

**Integration layer.** Writes the JSON the workbook reads; weekly
orchestrator runs everything in sequence with atomic rollback on failure.

---

## Key technical decisions

### Why lift SP+ rather than recompute our own blend
SP+ is publicly available via CFBD, peer-reviewed, opponent-adjusted by
construction, and is what other public-domain analysts in this space use
as their baseline. The earlier draft of this README blended our own
EPA-and-points ratings 75/25 — a ratio inherited from the NHL model's
backtest-tuned blend, with no defensible reason to be that ratio here.
SP+ saves us from re-deriving validated methodology and gives credibility.

### Why z-score normalization, not min-max
Min-max (the NHL model's approach) anchors 0 and 10 to the worst and
best teams each season. A team's rating then swings year-to-year just
because the distribution moved. Z-score with fixed bounds preserves
absolute meaning across seasons — a 7.5 in 2025 and a 7.5 in 2026
represent the same SP+ z-score. The history sections need this.

### Why five sub-ratings instead of one composite
Same reason a real scout's evaluation doesn't reduce to one number.
Miami 2025: Pass O #24 vs. Rush O #88 / Rush D #3 vs. Pass D #28.
Bundling these as "offense ~6.5, defense ~8.5" loses 70% of the story.
The composite is still there for ranking; the sub-ratings are there
for the strengths/weaknesses use case the project explicitly cares about.

### Why a returning-production prior
The biggest preseason signal in college football, by a wide margin, is
how much production a team is bringing back. A team returning 9 starters
is in a fundamentally different place than a team returning 4 starters
with the same prior-season rating. The prior fades from Week 0 to Week 6,
so by midseason the current-year sample is large enough to stand alone.

### Why regression-weighted QB modifier
A QB's previous-school EPA reflects their previous supporting cast.
Mensah at Duke ≠ Mensah at Miami; Beck at Georgia ≠ Beck at Miami.
A fixed regression weight by context (same school / P4 transfer / G5
transfer / first-time starter) handles this without requiring per-player
hand-tuning.

### Why we ship without confirmed-lineup automation
Same reason as the NHL model. No clean public API for confirmed QB
starts. The CFBD `/roster` endpoint covers the roster but not the
depth chart; manual override CSVs handle in-season changes.

---

## Stack

Python 3.11 (pandas, requests, openpyxl) · Excel workbook as primary
deliverable · Windows Task Scheduler for the weekly cron.

Data sources: CollegeFootballData.com (CFBD — free with API key,
documented at api.collegefootballdata.com) covering SP+, unit splits,
roster, returning production, and schedule. Sports-Reference college
football pages for historical program records. Individual school
athletics sites (e.g., miamihurricanes.com) for depth charts where
CFBD lags.

---

## What's in the workbook

Each team sheet has six sections:

1. **Header** — program identity, conference, head coach, year of tenure.
2. **Ratings (0-10)** — five sub-ratings (Rush O, Pass O, Rush D, Pass D,
   Special Teams) plus composite, each with a national rank and notes.
3. **Depth chart** — current projected starters and key backups on
   offense and defense, plus K/P. Refreshed weekly during the season.
4. **Team stats** — current season and previous three, side-by-side
   for trend comparison.
5. **Strengths & weaknesses** — analyst notes, tied to the sub-rating
   profile so the narrative is anchored in the numbers.
6. **Program history & coaching** — championships, bowl record, head
   coach tenure, notable alumni.

The overview sheet ranks all teams by composite rating with a
strength-of-schedule column.

---

## Status

- **Methodology:** revised to SP+ base + sub-ratings + returning-production
  prior + regression-weighted QB modifier. Form modifier demoted.
- **Template:** Miami (FL) rebuilt against the new methodology as the
  pilot.
- **Pipeline:** scripts updated to reflect the new methodology; not yet
  wired to CFBD. The stubs document the function contract so the actual
  fetch logic can be filled in incrementally.
- **MLB / NFL workbooks:** will replicate this structure once NCAA
  template is fully validated.
