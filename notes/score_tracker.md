# Score tracker — who was closer to each team's final score (INTERNAL)

Season: **man closer on 14 teams · machine on 12 · 4 tie** — points off, all teams: man 250 · machine 253 — games (both teams added up): man 5 · machine 6 · 4 tie

The machine predicts the margin, not the points - it has no totals model - so its team-score
misses are mostly a points-total miss. Corey's totals are his own.

| Wk | Game | Team | Final | Machine | off | Man | off | Closer |
|---|---|---|---|---|---|---|---|---|
| 3 | Houston at Texas Tech | Houston | 26 | 20 | 6 | 24 | 2 | man |
| 3 | Houston at Texas Tech | Texas Tech | 28 | 33 | 5 | 35 | 7 | machine |
| 3 | SMU at Louisville | SMU | 31 | 29 | 2 | 34 | 3 | machine |
| 3 | SMU at Louisville | Louisville | 41 | 30 | 11 | 35 | 6 | man |
| 3 | Mississippi State at South Carolina | Mississippi State | 41 | 27 | 14 | 27 | 14 | tie |
| 3 | Mississippi State at South Carolina | South Carolina | 34 | 32 | 2 | 31 | 3 | machine |
| 3 | Florida at Auburn | Florida | 44 | 26 | 18 | 27 | 17 | man |
| 3 | Florida at Auburn | Auburn | 39 | 27 | 12 | 28 | 11 | man |
| 3 | LSU at Ole Miss | LSU | 24 | 32 | 8 | 34 | 10 | machine |
| 3 | LSU at Ole Miss | Ole Miss | 32 | 27 | 5 | 28 | 4 | man |
| 4 | Texas at Tennessee | Texas | 20 | 32 | 12 | 31 | 11 | man |
| 4 | Texas at Tennessee | Tennessee | 17 | 23 | 6 | 24 | 7 | machine |
| 4 | Ole Miss at Florida | Ole Miss | 28 | 28 | 0 | 34 | 6 | machine |
| 4 | Ole Miss at Florida | Florida | 52 | 31 | 21 | 35 | 17 | man |
| 4 | Oklahoma at Georgia | Oklahoma | 13 | 15 | 2 | 20 | 7 | machine |
| 4 | Oklahoma at Georgia | Georgia | 41 | 29 | 12 | 34 | 7 | man |
| 4 | Oregon at USC | Oregon | 41 | 32 | 9 | 35 | 6 | man |
| 4 | Oregon at USC | USC | 27 | 31 | 4 | 34 | 7 | machine |
| 4 | Texas A&M at LSU | Texas A&M | 6 | 23 | 17 | 27 | 21 | machine |
| 4 | Texas A&M at LSU | LSU | 35 | 29 | 6 | 31 | 4 | man |
| 5 | Pitt at Virginia Tech | Pittsburgh | 35 | 28 | 7 | 28 | 7 | tie |
| 5 | Pitt at Virginia Tech | Virginia Tech | 33 | 27 | 6 | 27 | 6 | tie |
| 5 | Penn State at Northwestern | Penn State | 13 | 24 | 11 | 27 | 14 | machine |
| 5 | Penn State at Northwestern | Northwestern | 34 | 22 | 12 | 24 | 10 | man |
| 5 | Alabama at Mississippi State | Alabama | 56 | 34 | 22 | 38 | 18 | man |
| 5 | Alabama at Mississippi State | Mississippi State | 23 | 26 | 3 | 28 | 5 | machine |
| 5 | Auburn at Tennessee | Auburn | 14 | 24 | 10 | 21 | 7 | man |
| 5 | Auburn at Tennessee | Tennessee | 24 | 31 | 7 | 31 | 7 | tie |
| 5 | Ohio State at Iowa | Ohio State | 31 | 30 | 1 | 31 | 0 | man |
| 5 | Ohio State at Iowa | Iowa | 14 | 16 | 2 | 20 | 6 | machine |

Shadow score call (machine margin over the MODELED total, Phase 2 - not on air): 169 points off across 20 team scores vs 170 for the on-air call.

| Wk | Game | Team | Final | On-air call | off | Shadow call | off |
|---|---|---|---|---|---|---|---|
| 4 | Texas at Tennessee | Texas | 20 | 32 | 12 | 31 | 11 |
| 4 | Texas at Tennessee | Tennessee | 17 | 23 | 6 | 23 | 6 |
| 4 | Ole Miss at Florida | Ole Miss | 28 | 28 | 0 | 31 | 3 |
| 4 | Ole Miss at Florida | Florida | 52 | 31 | 21 | 34 | 18 |
| 4 | Oklahoma at Georgia | Oklahoma | 13 | 15 | 2 | 18 | 5 |
| 4 | Oklahoma at Georgia | Georgia | 41 | 29 | 12 | 32 | 9 |
| 4 | Oregon at USC | Oregon | 41 | 32 | 9 | 28 | 13 |
| 4 | Oregon at USC | USC | 27 | 31 | 4 | 27 | 0 |
| 4 | Texas A&M at LSU | Texas A&M | 6 | 23 | 17 | 19 | 13 |
| 4 | Texas A&M at LSU | LSU | 35 | 29 | 6 | 24 | 11 |
| 5 | Pitt at Virginia Tech | Pittsburgh | 35 | 28 | 7 | 28 | 7 |
| 5 | Pitt at Virginia Tech | Virginia Tech | 33 | 27 | 6 | 27 | 6 |
| 5 | Penn State at Northwestern | Penn State | 13 | 24 | 11 | 27 | 14 |
| 5 | Penn State at Northwestern | Northwestern | 34 | 22 | 12 | 25 | 9 |
| 5 | Alabama at Mississippi State | Alabama | 56 | 34 | 22 | 33 | 23 |
| 5 | Alabama at Mississippi State | Mississippi State | 23 | 26 | 3 | 25 | 2 |
| 5 | Auburn at Tennessee | Auburn | 14 | 24 | 10 | 23 | 9 |
| 5 | Auburn at Tennessee | Tennessee | 24 | 31 | 7 | 30 | 6 |
| 5 | Ohio State at Iowa | Ohio State | 31 | 30 | 1 | 32 | 1 |
| 5 | Ohio State at Iowa | Iowa | 14 | 16 | 2 | 17 | 3 |
