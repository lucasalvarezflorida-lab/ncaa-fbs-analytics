# FPI Decomposition

How much of ESPN's preseason FPI can you reconstruct from public data — and
which teams does ESPN's model rate higher or lower than public inputs explain?

ESPN publishes FPI but not its ingredients. This project regresses FPI on four
public proxies from the CollegeFootballData API and treats the residual as
"the part of ESPN's opinion you can't buy off the shelf." For a betting
operation, that residual is the interesting part: it's a proxy for where
ESPN's model (which moves public perception and, indirectly, markets)
disagrees with a naive public-data prior.

## Method

Target: team-level FPI rating (`/ratings/fpi`).

Features, each z-scored before fitting:

| Feature | Source | Proxy for |
|---|---|---|
| `prior_sp` | `/ratings/sp`, prior year | How good the program just was |
| `returning_prod` | `/player/returning` (PPA-weighted) | How much of that production is back |
| `talent` | `/talent` (247 Team Talent Composite) | Current roster talent |
| `recruiting_4yr` | `/recruiting/teams`, 4-year avg points | Sustained talent acquisition |

Fit: OLS, `fpi ~ prior_sp + returning_prod + talent + recruiting_4yr`, on the
intersection of teams present in all sources. Residual = actual FPI minus
model prediction. Positive residual = ESPN rates the team higher than public
inputs explain.

Optional `--transfer` extension adds a **net portal rating** (sum of incoming
transfer ratings minus outgoing, `/player/portal`) and reports whether it
improves adjusted R-squared and shrinks residuals for high-portal-turnover
teams.

Team names are normalized through an alias map before merging (CFBD endpoints
mirror different upstream sources — "Ole Miss" vs "Mississippi", "USC" vs
"Southern California", etc.), and merge coverage is printed on every run so a
name mismatch can never silently drop a team.

## Usage

```
pip install -r requirements.txt
# set CFBD_API_KEY in your environment (free key: https://collegefootballdata.com/key)
python fpi_decomposition.py --year 2025
python fpi_decomposition.py --year 2025 --transfer
python fpi_decomposition.py --year 2025 --refresh   # bypass the disk cache
pytest test_merge.py
```

Raw API responses are cached in `data/`; residual CSVs and charts land in
`output/`. If FPI for the requested year isn't on CFBD yet (e.g. next
season's preseason ratings), the script falls back to the prior year and says
so.

## Findings — 2025 backtest

Fit on 132 of 136 FBS teams (merge coverage 99–100%; the four gaps are
structural, not name mismatches — Delaware and Missouri State were 2025 FBS
newcomers with no prior-year SP+ or returning-production data, and the
service academies have no 247 Talent Composite entry).

**Four public inputs explain ~70% of FPI** (R-squared 0.705, adjusted 0.696).
Standardized coefficients:

| feature | std. coef | p-value |
|---|---|---|
| prior_sp | 7.01 | < 0.0001 |
| recruiting_4yr | 5.06 | 0.004 |
| returning_prod | 0.34 | 0.58 |
| talent | -1.14 | 0.49 |

Prior-year SP+ carries most of the load, with 4-year recruiting adding a
significant talent-pipeline signal. Returning production and the talent
composite are statistically indistinguishable from zero *given the other two*
— not because they don't matter, but because they're heavily collinear with
recruiting and prior performance (see Limitations).

**The transfer portal: construction matters more than the data.** A RAW net
portal rating (sum of incoming transfer ratings minus outgoing) adds nothing —
adjusted R-squared 0.6960 → 0.6962, p = 0.30. It turns out to measure roster
churn, not talent: coaching-transition bulk shoppers dominate raw sums. But a
QUALITY-WEIGHTED version — value above a 0.75 replacement level, 247-style
Gaussian diminishing returns so a team's top arrivals dominate, unrated
players imputed from star grades — is significant: **adjusted R-squared
0.6960 → 0.7119, coef 1.83, p = 0.005**, residual std 6.68 → 6.47. Same
underlying data, different measurement, opposite conclusion — a tidy lesson
in feature construction.

**The residuals are the story.** Teams FPI rates far above the public-input
model: Indiana (+19.0), Kennesaw State (+16.4), Texas Tech (+16.2), New
Mexico (+15.2), Utah (+13.8), Vanderbilt (+12.5). Far below: Sam Houston
(-16.4), Oklahoma State (-12.3), North Carolina (-12.1), Syracuse (-12.1).
Anyone who watched 2025 will recognize that list — it's the season's
over/under-performers. That's the FPI-vintage limitation in action: CFBD
mirrors *final* 2025 FPI, so these residuals largely measure what happened
during the season that preseason-style inputs couldn't know, rather than
pure "ESPN secret sauce." A true preseason test needs a preseason FPI
snapshot captured before week 1 (or the 2026 ratings once ESPN publishes
them and CFBD mirrors the preseason vintage).

Full ranked lists: `output/residuals_2025.csv` and the chart at
`output/residuals_2025.png` (plus `_portal` variants).

## Limitations

- **Public proxies aren't ESPN's inputs.** ESPN's FPI uses its own returning
  production, Vegas-informed priors, and coaching-change adjustments. A low
  R-squared means "not reconstructable from these four proxies," not "FPI is
  wrong"; residuals mix genuine ESPN insight with plain proxy mismatch.
- **Coefficients are not causal.** Prior SP+, talent, and recruiting are
  heavily correlated (good programs recruit well and were good last year), so
  individual coefficients are unstable even when the fit is good. Read the
  R-squared and the residuals, not the coefficient magnitudes.
- **SOS circularity.** FPI and SP+ both bake in schedule strength derived
  from the ratings themselves. Using prior-year SP+ as a feature means some
  of the "explained" variance is two systems agreeing on the same circular
  construct, which flatters R-squared.
- **FPI vintage.** CFBD mirrors ESPN's current FPI for a season, which for a
  completed year is the end-of-season rating, not the preseason snapshot. A
  backtest on a completed season therefore measures how much of *final* FPI
  the preseason-style inputs explain — a harder target that inflates
  residuals for teams that dramatically over/under-performed expectations.
- **Portal ratings are sparse.** Many portal entries carry no 247 rating and
  are counted at zero, biasing net portal ratings toward teams whose
  transfers happen to be rated.
