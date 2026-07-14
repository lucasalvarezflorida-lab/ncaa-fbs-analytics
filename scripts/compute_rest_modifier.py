"""
NCAA FBS Team Ratings — Phase 5: Rest modifier

The only between-week modifier kept in the rewrite. The original
`compute_weekly_adjustments.py` had two components — rest and a last-3-
games form modifier. The form modifier was demoted because it was a
betting-model holdover: for descriptive analysis, season-long opponent-
adjusted SP+ already captures team quality, and a 3-game form blip just
adds variance.

Rest stays because the effect is real and physiological — a team on a
short week (Thursday after Saturday) is meaningfully fatigued; a team
coming off a bye is fresher.

Reads:
    CFBD /games?year={season}&seasonType=regular  (schedule)

Writes:
    data/raw/rest_modifier.csv with columns:
        team, week, days_since_last_game, rest_modifier
"""

from datetime import date, timedelta
from pathlib import Path

import os
import pandas as pd
import requests

CFBD_BASE = "https://api.collegefootballdata.com"
SEASON = 2025

REST_MODIFIERS = {
    "short_week": -0.25,
    "normal":      0.00,
    "bye_week":   +0.15,
    "extended":   +0.20,
}

DATA_DIR = Path(__file__).parent / "data" / "raw"


def fetch_schedule(season: int) -> pd.DataFrame:
    api_key = os.environ.get("CFBD_API_KEY")
    if not api_key:
        raise RuntimeError("CFBD_API_KEY not set")
    headers = {"Authorization": f"Bearer {api_key}"}
    url = f"{CFBD_BASE}/games"
    resp = requests.get(
        url,
        params={"year": season, "seasonType": "regular"},
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    return pd.DataFrame(resp.json())


def compute_rest_modifier(days_since_last: int) -> float:
    if days_since_last < 6:
        return REST_MODIFIERS["short_week"]
    if days_since_last <= 8:
        return REST_MODIFIERS["normal"]
    if days_since_last <= 15:
        return REST_MODIFIERS["bye_week"]
    return REST_MODIFIERS["extended"]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    schedule = fetch_schedule(SEASON)
    print(f"  {len(schedule)} games in schedule")
    # Implementation pending — iterate teams, compute days-since-last, write CSV.
    raise NotImplementedError("See NHL model's compute_gameday_adjustments.py")


if __name__ == "__main__":
    main()
