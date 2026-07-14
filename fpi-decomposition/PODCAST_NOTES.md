# FPI Decomposition — data reference sheet

Raw numbers for on-air reference. 2025 backtest, 132 FBS teams.
Full 132-team table: `output/team_table_2025.csv` (FPI rank, all inputs,
residual rank). Rosters: `../rosters/FBS_Rosters_2026.xlsx`. Team workbook:
`../NCAA_FBS_Teams.xlsx`.

One factual note: CFBD mirrors ESPN's *final* 2025 FPI (not the preseason
snapshot), so residuals include in-season surprises.

## Model stats

| | baseline | + portal |
|---|---|---|
| R² | 0.705 | 0.708 |
| Adjusted R² | 0.696 | 0.696 |
| Residual std | 6.68 | 6.65 |
| Mean abs. residual, high-portal teams | 5.86 | 5.74 |

Standardized coefficients (baseline):

| feature | coef | p-value |
|---|---|---|
| prior-year SP+ | 7.01 | < 0.0001 |
| recruiting 4-yr avg | 5.06 | 0.004 |
| returning production (PPA) | 0.34 | 0.58 |
| talent composite | -1.14 | 0.49 |
| net portal rating (portal model) | 0.67 | 0.30 |

## Top 25 by FPI — with roster inputs

resid = FPI minus what public inputs predict. ret PPA = returning production
(PPA-weighted). talent = 247 composite. rec4 = 4-yr avg recruiting points.

| # | team | conf | FPI | pred | resid | prior SP+ | ret PPA | talent | rec4 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Indiana | B1G | 31.5 | 12.5 | +19.0 | 20.1 | 154 | 645 | 195 |
| 2 | Ohio State | B1G | 27.6 | 25.4 | +2.2 | 31.2 | 221 | 974 | 294 |
| 3 | Notre Dame | Ind | 25.3 | 19.9 | +5.3 | 23.9 | 212 | 912 | 274 |
| 4 | Oregon | B1G | 23.9 | 21.0 | +2.9 | 26.0 | 117 | 941 | 278 |
| 5 | Miami | ACC | 22.4 | 18.0 | +4.3 | 21.6 | 95 | 875 | 267 |
| 6 | Texas Tech | B12 | 21.5 | 5.3 | +16.2 | 4.3 | 333 | 758 | 214 |
| 7 | Georgia | SEC | 21.4 | 23.1 | -1.7 | 24.3 | 194 | 1003 | 314 |
| 8 | Utah | B12 | 20.1 | 6.2 | +13.8 | 7.7 | 36 | 708 | 210 |
| 9 | Ole Miss | SEC | 19.3 | 19.1 | +0.2 | 27.9 | 117 | 813 | 236 |
| 10 | Alabama | SEC | 19.0 | 23.7 | -4.7 | 25.0 | 188 | 994 | 315 |
| 11 | Texas | SEC | 18.6 | 21.8 | -3.2 | 24.1 | 173 | 974 | 299 |
| 12 | Texas A&M | SEC | 18.4 | 17.2 | +1.2 | 17.0 | 302 | 917 | 282 |
| 13 | USC | B1G | 18.0 | 10.7 | +7.3 | 11.9 | 193 | 848 | 239 |
| 14 | Vanderbilt | SEC | 17.0 | 4.5 | +12.5 | 4.9 | 319 | 685 | 197 |
| 15 | Oklahoma | SEC | 15.9 | 11.8 | +4.2 | 9.5 | 146 | 883 | 270 |
| 16 | Penn State | B1G | 15.9 | 20.2 | -4.3 | 24.6 | 355 | 910 | 267 |
| 17 | BYU | B12 | 15.3 | 10.0 | +5.4 | 15.3 | 346 | 649 | 190 |
| 18 | Iowa | B1G | 15.3 | 11.0 | +4.3 | 15.8 | 127 | 710 | 211 |
| 19 | Tennessee | SEC | 14.3 | 18.0 | -3.7 | 22.0 | 95 | 867 | 264 |
| 20 | Michigan | B1G | 14.2 | 11.6 | +2.7 | 10.6 | 99 | 907 | 265 |
| 21 | Washington | B1G | 14.0 | 3.0 | +11.0 | 3.1 | 207 | 721 | 198 |
| 22 | Missouri | SEC | 13.1 | 11.3 | +1.8 | 14.0 | 80 | 805 | 233 |
| 23 | SMU | ACC | 12.5 | 8.2 | +4.3 | 17.5 | 282 | 767 | 170 |
| 24 | Auburn | SEC | 11.1 | 10.5 | +0.6 | 9.5 | 98 | 892 | 259 |
| 25 | South Florida | AAC | 11.1 | -1.3 | +12.4 | -2.3 | 392 | 667 | 172 |

## Rankings: FPI above public inputs (top 15 residuals)

| resid rank | team | conf | FPI rank | FPI | pred | resid |
|---|---|---|---|---|---|---|
| 1 | Indiana | B1G | 1 | 31.5 | 12.5 | +19.0 |
| 2 | Kennesaw State | CUSA | 94 | -8.0 | -24.4 | +16.4 |
| 3 | Texas Tech | B12 | 6 | 21.5 | 5.3 | +16.2 |
| 4 | New Mexico | MWC | 77 | -2.7 | -17.8 | +15.1 |
| 5 | Utah | B12 | 8 | 20.1 | 6.2 | +13.8 |
| 6 | James Madison | SBC | 27 | 10.3 | -2.9 | +13.2 |
| 7 | Vanderbilt | SEC | 14 | 17.0 | 4.5 | +12.5 |
| 8 | South Florida | AAC | 25 | 11.1 | -1.3 | +12.4 |
| 9 | North Texas | AAC | 41 | 7.0 | -5.3 | +12.3 |
| 10 | Old Dominion | SBC | 49 | 4.8 | -7.1 | +11.9 |
| 11 | Virginia | ACC | 36 | 8.2 | -3.4 | +11.7 |
| 12 | Washington | B1G | 21 | 14.0 | 3.0 | +11.0 |
| 13 | Arizona | B12 | 29 | 10.1 | 0.3 | +9.8 |
| 14 | San Diego State | MWC | 67 | 0.6 | -8.8 | +9.4 |
| 15 | Houston | B12 | 50 | 4.4 | -3.5 | +7.9 |

## Rankings: FPI below public inputs (bottom 15 residuals)

| resid rank | team | conf | FPI rank | FPI | pred | resid |
|---|---|---|---|---|---|---|
| 132 | Sam Houston | CUSA | 131 | -24.3 | -7.8 | -16.4 |
| 131 | Oklahoma State | B12 | 110 | -12.1 | 0.2 | -12.3 |
| 130 | North Carolina | ACC | 90 | -5.9 | 6.3 | -12.1 |
| 129 | Syracuse | ACC | 97 | -9.3 | 2.8 | -12.1 |
| 128 | UMass | MAC | 132 | -30.5 | -19.2 | -11.3 |
| 127 | Louisiana | SBC | 101 | -10.6 | 0.3 | -10.9 |
| 126 | Northern Illinois | MAC | 118 | -14.3 | -3.4 | -10.9 |
| 125 | Buffalo | MAC | 112 | -13.3 | -3.7 | -9.6 |
| 124 | South Alabama | SBC | 103 | -10.7 | -1.4 | -9.3 |
| 123 | Colorado State | MWC | 111 | -13.2 | -4.2 | -8.9 |
| 122 | Coastal Carolina | SBC | 117 | -14.2 | -5.4 | -8.8 |
| 121 | Virginia Tech | ACC | 70 | -1.2 | 7.5 | -8.7 |
| 120 | Oregon State | P12 | 108 | -11.6 | -3.4 | -8.2 |
| 119 | San José State | MWC | 115 | -13.7 | -5.5 | -8.2 |
| 118 | Liberty | CUSA | 102 | -10.7 | -2.8 | -7.9 |

## Coverage / sample facts

- 132 of 136 FBS teams fit. Not in sample: Delaware, Missouri State (2025
  FBS newcomers — no prior-year SP+ or returning production), Air Force,
  Navy (no 247 talent composite).
- Data source: CollegeFootballData API. Inputs are all public/free.
- Charts: `output/residuals_2025.png`, `output/residuals_2025_portal.png`.
