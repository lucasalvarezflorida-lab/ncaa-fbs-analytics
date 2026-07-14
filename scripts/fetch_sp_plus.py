"""
NCAA FBS Team Ratings — Phase 1: SP+ ratings + PPA unit splits

Pulls two CFBD endpoints and merges into one per-team row:

  /ratings/sp?year={season}              — overall SP+ rating + ST rating
                                            (rushing/passing splits are
                                             null in this endpoint, so we
                                             go to advanced stats below)
  /stats/season/advanced?year={season}   — opponent-adjusted PPA splits
                                            (Rush O / Pass O / Rush D / Pass D)
                                            verified non-null for 138/138
                                            FBS teams in 2025.

PPA is CFBD's name for Predicted Points Added — their EPA implementation,
opponent-adjusted at the season level.

Writes:
    data/raw/sp_plus.csv with columns:
        team, conference,
        sp_overall, sp_off, sp_def, sp_st,
        ppa_rush_o, ppa_pass_o, ppa_rush_d, ppa_pass_d,
        epa_overall_o, epa_overall_d
"""

import os
from pathlib import Path

import pandas as pd
import requests

CFBD_BASE = "https://api.collegefootballdata.com"
SEASON = 2025

DATA_DIR = Path(__file__).parent / "data" / "raw"


def _headers() -> dict:
    api_key = os.environ.get("CFBD_API_KEY")
    if not api_key:
        raise RuntimeError(
            "CFBD_API_KEY not set. Get a free key at "
            "collegefootballdata.com/key and export it."
        )
    return {"Authorization": f"Bearer {api_key}"}


def fetch_sp_plus(season: int) -> pd.DataFrame:
    """Pull SP+ overall + ST ratings for every team."""
    print(f"Fetching CFBD /ratings/sp for {season}")
    resp = requests.get(
        f"{CFBD_BASE}/ratings/sp",
        params={"year": season},
        headers=_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    rows = []
    for t in resp.json():
        if t.get("team") in (None, "nationalAverages"):
            continue
        rows.append({
            "team": t["team"],
            "conference": t.get("conference"),
            "sp_overall": t.get("rating"),
            "sp_off":     (t.get("offense") or {}).get("rating"),
            "sp_def":     (t.get("defense") or {}).get("rating"),
            "sp_st":      (t.get("specialTeams") or {}).get("rating"),
        })
    return pd.DataFrame(rows)


def fetch_ppa_splits(season: int) -> pd.DataFrame:
    """Pull opponent-adjusted PPA unit splits."""
    print(f"Fetching CFBD /stats/season/advanced for {season}")
    resp = requests.get(
        f"{CFBD_BASE}/stats/season/advanced",
        params={"year": season},
        headers=_headers(),
        timeout=30,
    )
    resp.raise_for_status()
    rows = []
    for t in resp.json():
        off = t.get("offense") or {}
        deff = t.get("defense") or {}
        rows.append({
            "team": t["team"],
            "ppa_rush_o": (off.get("rushingPlays") or {}).get("ppa"),
            "ppa_pass_o": (off.get("passingPlays") or {}).get("ppa"),
            "ppa_rush_d": (deff.get("rushingPlays") or {}).get("ppa"),
            "ppa_pass_d": (deff.get("passingPlays") or {}).get("ppa"),
            "epa_overall_o": off.get("ppa"),
            "epa_overall_d": deff.get("ppa"),
        })
    return pd.DataFrame(rows)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    sp = fetch_sp_plus(SEASON)
    print(f"  SP+ rows: {len(sp)}")
    splits = fetch_ppa_splits(SEASON)
    print(f"  PPA-split rows: {len(splits)}")

    merged = sp.merge(splits, on="team", how="outer")
    print(f"  After outer-join: {len(merged)} rows ({merged['conference'].isna().sum()} missing conf)")

    out = DATA_DIR / "sp_plus.csv"
    merged.to_csv(out, index=False, float_format="%.4f")
    print(f"  Wrote {out}")


if __name__ == "__main__":
    main()
