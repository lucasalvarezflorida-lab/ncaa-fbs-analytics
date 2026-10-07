"""Composite human hot-seat prior (Lucas 10/6/2026: "one writer, one morning in August" -> the median of several lists).

Every published list is mapped onto CBS's 0-5 scale by tier / rank (the mapping is ours and is written next to each
source). A coach a source does not mention gets that source's floor (1.0 = CBS's 'safe and secure' band), so the median
over sources is defined for every FBS coach. Entries are validated against CFBD's 2026 coach table: a coach-school pair
a source got wrong (sites do) is dropped and printed.

    python hot_seat_sources.py          # prints the composite next to CBS for every coach either rates above the floor
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / "fpi-decomposition"))

FLOOR = 1.0

# ---- preseason lists (coach, school, score on the 0-5 scale) ----
PRESEASON = {
 "CBS 8/29": {   # exact ratings; the 27 on the published list (hot_seat_heisman.CBS) + the 5 prep estimates are NOT used here
  ("Mike Norvell", "Florida State"): 5.0, ("Luke Fickell", "Wisconsin"): 5.0, ("Dave Aranda", "Baylor"): 5.0, ("Mike Locksley", "Maryland"): 4.9,
  ("Shane Beamer", "South Carolina"): 4.3, ("Bill Belichick", "North Carolina"): 4.1, ("Derek Mason", "Middle Tennessee"): 3.6,
  ("Bill O'Brien", "Boston College"): 3.5, ("Scott Satterfield", "Cincinnati"): 3.5, ("Jeff Lebby", "Mississippi State"): 3.3,
  ("Dell McGee", "Georgia State"): 3.3, ("Sonny Cumbie", "Louisiana Tech"): 3.2, ("Deion Sanders", "Colorado"): 3.1,
  ("Clay Helton", "Georgia Southern"): 3.1, ("Dabo Swinney", "Clemson"): 3.1, ("Kalen DeBoer", "Alabama"): 3.0, ("Dave Doeren", "NC State"): 3.0,
  ("Matt Rhule", "Nebraska"): 3.0, ("Chris Creighton", "Eastern Michigan"): 2.8, ("Jamey Chadwell", "Liberty"): 2.7,
  ("Tony Sanchez", "New Mexico State"): 2.7, ("Butch Jones", "Arkansas State"): 2.4, ("Lance Leipold", "Kansas"): 2.3,
  ("Michael Desormeaux", "Louisiana"): 2.2, ("Joe Moorhead", "Akron"): 2.2, ("Jeff Choate", "Nevada"): 2.2, ("P.J. Fleck", "Minnesota"): 2.1},
 "ESPN tiers 3/2": {   # Hottest of hot 5 · We want this to work 4 · It's going to cost us 3.5 · Progress needed 3 · Retirement watch 2.5 · Group of 6 3.5
  ("Mike Norvell", "Florida State"): 5.0, ("Luke Fickell", "Wisconsin"): 5.0, ("Dave Aranda", "Baylor"): 5.0, ("Mike Locksley", "Maryland"): 5.0,
  ("Shane Beamer", "South Carolina"): 4.0, ("Bill O'Brien", "Boston College"): 4.0, ("Lincoln Riley", "USC"): 3.5, ("Jeff Lebby", "Mississippi State"): 3.0,
  ("Bill Belichick", "North Carolina"): 2.5, ("Kirk Ferentz", "Iowa"): 2.5, ("Deion Sanders", "Colorado"): 2.5,
  ("Derek Mason", "Middle Tennessee"): 3.5, ("Chris Creighton", "Eastern Michigan"): 3.5, ("Dell McGee", "Georgia State"): 3.5},
 "SportsGrid top 20 (Sept)": {   # ranks 1-5 -> 5, 6-10 -> 4, 11-15 -> 3, 16-20 -> 2.5
  ("Mike Norvell", "Florida State"): 5.0, ("Bill Belichick", "North Carolina"): 5.0, ("Mike Locksley", "Maryland"): 5.0, ("Dave Aranda", "Baylor"): 5.0,
  ("Luke Fickell", "Wisconsin"): 5.0, ("Dell McGee", "Georgia State"): 4.0, ("Shane Beamer", "South Carolina"): 4.0, ("Jeff Lebby", "Mississippi State"): 4.0,
  ("Bill O'Brien", "Boston College"): 4.0, ("Derek Mason", "Middle Tennessee"): 4.0, ("Chris Creighton", "Eastern Michigan"): 3.0,
  ("Lincoln Riley", "USC"): 3.0, ("Scott Satterfield", "Cincinnati"): 3.0, ("Brent Venables", "Oklahoma"): 3.0, ("Dabo Swinney", "Clemson"): 3.0,
  ("Lance Leipold", "Kansas"): 2.5, ("Scotty Walden", "UTEP"): 2.5, ("Sonny Cumbie", "Louisiana Tech"): 2.5, ("Kalen DeBoer", "Alabama"): 2.5,
  ("Deion Sanders", "Colorado"): 2.5},
 "2 Stripes 7/31": {   # Tier 1 / 1.5 -> 5, Tier 2 -> 4, Tier 2.5 -> 3.5, Tier 3 -> 3, 'own island' -> 3, Tier 4 -> 2.5
  ("Mike Norvell", "Florida State"): 5.0, ("Bill Belichick", "North Carolina"): 5.0, ("Luke Fickell", "Wisconsin"): 4.0, ("Shane Beamer", "South Carolina"): 4.0,
  ("Derek Mason", "Middle Tennessee"): 4.0, ("Scott Satterfield", "Cincinnati"): 4.0, ("Dell McGee", "Georgia State"): 4.0, ("Dave Aranda", "Baylor"): 4.0,
  ("Mike Locksley", "Maryland"): 4.0, ("Lincoln Riley", "USC"): 3.5, ("Kalen DeBoer", "Alabama"): 3.5, ("Bill O'Brien", "Boston College"): 3.0,
  ("Jay Sawvel", "Wyoming"): 3.0, ("Jeff Choate", "Nevada"): 3.0, ("Tim Albin", "Charlotte"): 3.0, ("Phil Longo", "Sam Houston"): 3.0,
  ("Tony Sanchez", "New Mexico State"): 3.0, ("Scotty Walden", "UTEP"): 3.0, ("Jeff Lebby", "Mississippi State"): 3.0, ("Dabo Swinney", "Clemson"): 3.0,
  ("Matt Rhule", "Nebraska"): 2.5, ("Deion Sanders", "Colorado"): 2.5},
 "Eh Gap 7/15": {   # P4 ranks 1-7 -> 5, 4.5, 4, 4, 3.5, 3.5, 3 · G6 ranks 1-4 -> 4, 4, 4, 3.5 · honorable mention 2.5 · SEC monitoring 3 · retirement watch 2.5
  ("Mike Norvell", "Florida State"): 5.0, ("Luke Fickell", "Wisconsin"): 4.5, ("Mike Locksley", "Maryland"): 4.0, ("Bill O'Brien", "Boston College"): 4.0,
  ("Scott Satterfield", "Cincinnati"): 3.5, ("Dave Aranda", "Baylor"): 3.5, ("Dave Doeren", "NC State"): 3.0,
  ("Jamey Chadwell", "Liberty"): 4.0, ("Dell McGee", "Georgia State"): 4.0, ("Derek Mason", "Middle Tennessee"): 4.0, ("Scotty Walden", "UTEP"): 3.5,
  ("Jay Sawvel", "Wyoming"): 2.5, ("Jeff Choate", "Nevada"): 2.5, ("Sonny Cumbie", "Louisiana Tech"): 2.5, ("Joe Harasymiak", "Massachusetts"): 2.5,
  ("Shane Beamer", "South Carolina"): 3.0, ("Jeff Lebby", "Mississippi State"): 3.0,
  ("Deion Sanders", "Colorado"): 2.5, ("Bill Belichick", "North Carolina"): 2.5, ("Dabo Swinney", "Clemson"): 2.5},
}
# ---- the in-season read (re-pulled weekly; a site that ranks 'expectations vs results') ----
MIDSEASON = {
 "Coaches Hot Seat wk6": {   # ranks 1-5 -> 5, 6-10 -> 4, 11-18 -> 3
  ("Mike Locksley", "Maryland"): 5.0, ("Greg Schiano", "Rutgers"): 5.0, ("Shane Beamer", "South Carolina"): 5.0, ("Mike Norvell", "Florida State"): 5.0,
  ("Sonny Dykes", "TCU"): 5.0, ("Jedd Fisch", "Arizona"): 4.0, ("Lincoln Riley", "USC"): 4.0, ("Dave Aranda", "Baylor"): 4.0, ("Luke Fickell", "Wisconsin"): 4.0,
  ("Deion Sanders", "Colorado"): 4.0, ("Phil Longo", "Sam Houston"): 3.0, ("Barry Odom", "Purdue"): 3.0, ("Bill O'Brien", "Boston College"): 3.0,
  ("Ryan Silverfield", "Arkansas"): 3.0, ("Matt Campbell", "Penn State"): 3.0, ("Tim Albin", "Charlotte"): 3.0, ("Sonny Cumbie", "Louisiana Tech"): 3.0,
  ("Bill Belichick", "North Carolina"): 3.0},
}


def coach_table_2026():
    from hot_seat_study import coach_table
    T = coach_table()
    return {s: v["coach"] for (s, y), v in T.items() if y == 2026}


def _last(n):
    return n.split()[-1].lower()


def validate(lists, coaches):
    """Drop entries whose coach is not the school's 2026 coach (sites get these wrong); print what was dropped."""
    out = {}
    for src, d in lists.items():
        ok = {}
        for (coach, school), v in d.items():
            actual = coaches.get(school)
            if actual and _last(actual) == _last(coach):
                ok[school] = v
            else:
                print(f"  dropped {src}: {coach} / {school} (CFBD has {actual})")
        out[src] = ok
    return out


def composite(coaches, include_midseason=False):
    """{school: (median over sources, n sources that named him)} for every 2026 FBS coach."""
    lists = validate(dict(PRESEASON, **(MIDSEASON if include_midseason else {})), coaches)
    out = {}
    for school in coaches:
        vals = [d.get(school, FLOOR) for d in lists.values()]
        out[school] = (float(np.median(vals)), sum(school in d for d in lists.values()))
    return out


if __name__ == "__main__":
    from refresh_all import load_env_key
    load_env_key()
    coaches = coach_table_2026()
    pre = composite(coaches); mid = composite(coaches, True)
    cbs = {s: v for s, v in PRESEASON["CBS 8/29"].items()}
    cbs = {school: v for (c, school), v in PRESEASON["CBS 8/29"].items()}
    rows = sorted(coaches, key=lambda s: -max(pre[s][0], mid[s][0], cbs.get(s, 0)))
    print(f"\n{'school':20} {'coach':20} {'CBS':>4} {'pre-season median':>18} {'n':>2} {'with midseason':>15} {'n':>2}")
    for s in rows:
        if max(pre[s][0], mid[s][0], cbs.get(s, 0)) <= FLOOR:
            continue
        print(f"{s:20} {coaches[s]:20} {cbs.get(s, FLOOR):4.1f} {pre[s][0]:18.1f} {pre[s][1]:2d} {mid[s][0]:15.1f} {mid[s][1]:2d}")
