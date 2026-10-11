# Score tracker — who was closer to each team's final score (INTERNAL)

Season: **man closer on 26 teams · machine on 33 · 11 tie** — points off, all teams: man 615 · machine 573 — games (both teams added up): man 11 · machine 15 · 9 tie

The machine predicts the margin, not the points - it has no totals model - so its team-score
misses are mostly a points-total miss. Corey's totals are his own.

| Wk | Game | Team | Final | Machine | off | Man | off | Closer |
|---|---|---|---|---|---|---|---|---|
| 0 | North Carolina vs TCU | North Carolina | 15 | 23 | 8 | 24 | 9 | machine |
| 0 | North Carolina vs TCU | TCU | 10 | 24 | 14 | 26 | 16 | machine |
| 0 | NC State at Virginia | NC State | 8 | 23 | 15 | 24 | 16 | machine |
| 0 | NC State at Virginia | Virginia | 34 | 30 | 4 | 31 | 3 | man |
| 0 | Jacksonville State at North Dakota State | Jacksonville State | 7 | 22 | 15 | 25 | 18 | machine |
| 0 | Jacksonville State at North Dakota State | North Dakota State | 33 | 25 | 8 | 28 | 5 | man |
| 0 | Hawai'i at Stanford | Hawai'i | 27 | 24 | 3 | 24 | 3 | tie |
| 0 | Hawai'i at Stanford | Stanford | 37 | 26 | 11 | 26 | 11 | tie |
| 0 | Memphis at UNLV | Memphis | 27 | 26 | 1 | 26 | 1 | tie |
| 0 | Memphis at UNLV | UNLV | 21 | 32 | 11 | 33 | 12 | machine |
| 1 | Baylor vs Auburn | Baylor | 16 | 27 | 11 | 24 | 8 | man |
| 1 | Baylor vs Auburn | Auburn | 17 | 33 | 16 | 31 | 14 | man |
| 1 | Clemson at LSU | Clemson | 10 | 21 | 11 | 17 | 7 | man |
| 1 | Clemson at LSU | LSU | 51 | 30 | 21 | 27 | 24 | machine |
| 1 | Louisville vs Ole Miss | Louisville | 38 | 25 | 13 | 24 | 14 | machine |
| 1 | Louisville vs Ole Miss | Ole Miss | 41 | 31 | 10 | 31 | 10 | tie |
| 1 | Wisconsin vs Notre Dame | Wisconsin | 13 | 13 | 0 | 13 | 0 | tie |
| 1 | Wisconsin vs Notre Dame | Notre Dame | 41 | 34 | 7 | 34 | 7 | tie |
| 1 | SMU at Florida State | SMU | 27 | 26 | 1 | 27 | 0 | man |
| 1 | SMU at Florida State | Florida State | 24 | 27 | 3 | 24 | 0 | man |
| 2 | Oklahoma at Michigan | Oklahoma | 10 | 23 | 13 | 21 | 11 | man |
| 2 | Oklahoma at Michigan | Michigan | 17 | 21 | 4 | 17 | 0 | man |
| 2 | Arizona State at Texas A&M | Arizona State | 20 | 17 | 3 | 24 | 4 | machine |
| 2 | Arizona State at Texas A&M | Texas A&M | 48 | 34 | 14 | 41 | 7 | man |
| 2 | Arizona at BYU | Arizona | 17 | 20 | 3 | 24 | 7 | machine |
| 2 | Arizona at BYU | BYU | 28 | 28 | 0 | 34 | 6 | machine |
| 2 | Alabama at Kentucky | Alabama | 45 | 31 | 14 | 38 | 7 | man |
| 2 | Alabama at Kentucky | Kentucky | 17 | 18 | 1 | 24 | 7 | machine |
| 2 | Ohio State at Texas | Ohio State | 23 | 23 | 0 | 31 | 8 | machine |
| 2 | Ohio State at Texas | Texas | 24 | 27 | 3 | 34 | 10 | machine |
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
| 6 | Indiana at Nebraska | Indiana | 20 | 27 | 7 | 31 | 11 | machine |
| 6 | Indiana at Nebraska | Nebraska | 17 | 21 | 4 | 24 | 7 | machine |
| 6 | Texas A&M at Missouri | Texas A&M | 6 | 25 | 19 | 27 | 21 | machine |
| 6 | Texas A&M at Missouri | Missouri | 27 | 24 | 3 | 28 | 1 | man |
| 6 | UCLA at Oregon | UCLA | 17 | 24 | 7 | 27 | 10 | machine |
| 6 | UCLA at Oregon | Oregon | 15 | 34 | 19 | 41 | 26 | machine |
| 6 | Georgia at Alabama | Georgia | 20 | 24 | 4 | 34 | 14 | machine |
| 6 | Georgia at Alabama | Alabama | 17 | 27 | 10 | 35 | 18 | machine |
| 6 | USC at Penn State | USC | 31 | 27 | 4 | 27 | 4 | tie |
| 6 | USC at Penn State | Penn State | 23 | 28 | 5 | 31 | 8 | machine |

Shadow score call (machine margin over the MODELED total, Phase 2 - not on air): 253 points off across 30 team scores vs 252 for the on-air call.

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
| 6 | Indiana at Nebraska | Indiana | 20 | 27 | 7 | 29 | 9 |
| 6 | Indiana at Nebraska | Nebraska | 17 | 21 | 4 | 23 | 6 |
| 6 | Texas A&M at Missouri | Texas A&M | 6 | 25 | 19 | 25 | 19 |
| 6 | Texas A&M at Missouri | Missouri | 27 | 24 | 3 | 24 | 3 |
| 6 | UCLA at Oregon | UCLA | 17 | 24 | 7 | 21 | 4 |
| 6 | UCLA at Oregon | Oregon | 15 | 34 | 19 | 33 | 18 |
| 6 | Georgia at Alabama | Georgia | 20 | 24 | 4 | 25 | 5 |
| 6 | Georgia at Alabama | Alabama | 17 | 27 | 10 | 28 | 11 |
| 6 | USC at Penn State | USC | 31 | 27 | 4 | 27 | 4 |
| 6 | USC at Penn State | Penn State | 23 | 28 | 5 | 28 | 5 |
