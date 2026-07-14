"""
NCAA FBS Team Ratings — Phase 3: Returning production

The biggest single preseason signal in college football, by a wide margin,
is how much production a team is returning. Returning production is
typically expressed as a percentage of the previous season's offensive
and defensive EPA-producing snaps that return to the roster (graduating
seniors, drafted underclassmen, and portal-out transfers all subtract;
fifth-year returners, portal-in transfers with prior production, and
rising recruits add).

The NHL model didn't need an analogue because hockey rosters are stable
year-to-year. College football has massive portal and graduation churn.

This phase's output feeds the **returning-production prior** in
`compute_ratings.py`, which blends current-season SP+ with a returning-
production-adjusted previous-season SP+ during Weeks 1-6. The prior
fully decays by Week 7.

Reads:
    CFBD /player/returning?year={season}  (one row per team)

Writes:
    data/raw/returning_production.csv with columns:
        team, conference,
        total_returning_pct,
        offense_returning_pct, defense_returning_pct,
        qb_returning   (boolean — is the QB1 a returner?)

Why the QB column is separate from offense_returning_pct:
    Returning EPA at QB is overweighted in real outcomes — the position
    carries more leverage than its raw EPA share. Tracking it separately
    lets `compute_qb_modifier.py` use it as a confidence input.
"""

import os
from pathlib import Path

import pandas as pd
import requests

CFBD_BASE = "https://api.collegefootballdata.com"
SEASON = 2025

DATA_DIR = Path(__file__).parent / "data" / "raw"


def fetch_returning_production(season: int) -> pd.DataFrame:
    """
    Pull per-team returning-production percentages for the season.

    CFBD's /player/returning endpoint returns one row per team with
    percentageOffense, percentagePassingPPA, percentageReceivingPPA,
    percentageRushingPPA, etc.
    """
    api_key = os.environ.get("CFBD_API_KEY")
    if not api_key:
        raise RuntimeError("CFBD_API_KEY not set")

    headers = {"Authorization": f"Bearer {api_key}"}
    url = f"{CFBD_BASE}/player/returning"
    print(f"Fetching CFBD returning production for {season}")
    resp = requests.get(url, params={"year": season}, headers=headers, timeout=30)
    resp.raise_for_status()
    raw = resp.json()
    print(f"  {len(raw)} teams in payload")

    rows = []
    for t in raw:
        rows.append({
            "team": t["team"],
            "conference": t.get("conference"),
            "total_returning_pct": t.get("totalPPA"),
            "offense_returning_pct": t.get("percentageOffense"),
            "defense_returning_pct": t.get("percentageDefense"),
            "passing_returning_pct": t.get("percentagePassingPPA"),
            "rushing_returning_pct": t.get("percentageRushingPPA"),
            "receiving_returning_pct": t.get("percentageReceivingPPA"),
            "qb_returning": bool(t.get("returningPassingProduction", 0) > 0.5),
        })
    return pd.DataFrame(rows)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rp = fetch_returning_production(SEASON)
    out = DATA_DIR / "returning_production.csv"
    rp.to_csv(out, index=False, float_format="%.3f")
    print(f"  Wrote {len(rp)} teams to {out}")


if __name__ == "__main__":
    main()
