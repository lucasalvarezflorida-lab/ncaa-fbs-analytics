"""
NCAA FBS Team Ratings — Phase 4: QB modifier with transfer regression

The football analogue of the NHL model's goalie modifier. Quarterback is
the highest-leverage individual position in the sport, but unlike the
NHL where a goalie's GSAx travels with them, a QB's EPA depends on
supporting cast. Mensah at Duke ≠ Mensah at Miami; Beck at Georgia ≠
Beck at Miami.

This phase pulls the projected QB1 for each program and computes a
context-regressed additive modifier on offensive sub-ratings.

Reads:
    CFBD /roster?year={season}            (active roster per team)
    CFBD /stats/player/season             (passer EPA, snaps, completion %)
    CFBD /recruiting/players              (recruiting rank for true frosh)

Optionally reads:
    data/manual/qb_overrides.csv          (confirmed weekly starters)

Writes:
    data/raw/qb_modifiers.csv with columns:
        team, qb_name, qb_status, prior_epa_per_pass,
        regression_alpha, offense_modifier

The regression formula:

    qb_modifier = alpha × (qb_prior_epa − league_avg_epa) × MODIFIER_SCALE
    where alpha depends on QB status:

        Established starter, same school:        alpha = 0.90
        Power 4 → Power 4 transfer:              alpha = 0.55
        Group of 5 → Power 4 transfer:           alpha = 0.35
        First-time starter, returning at school: alpha = 0.30
        True freshman or first-time portal-in:   alpha = 0.20

    Then clipped to ±MODIFIER_CAP.

For true freshmen, prior_epa_per_pass is derived from a recruiting-rank
mapping (5-star ≈ +0.10, 4-star ≈ +0.03, 3-star ≈ -0.05, vs. FBS QB
baseline) rather than from actual snaps the QB doesn't have yet.
"""

import os
from pathlib import Path

import pandas as pd
import requests

CFBD_BASE = "https://api.collegefootballdata.com"
SEASON = 2025

MODIFIER_SCALE = 2.0
MODIFIER_CAP = 1.5

# Regression weights by QB context
ALPHA_RETURNING_STARTER  = 0.90
ALPHA_P4_TRANSFER        = 0.55
ALPHA_G5_TO_P4_TRANSFER  = 0.35
ALPHA_FIRST_TIME_STARTER = 0.30
ALPHA_FRESHMAN           = 0.20

# 5-star ≈ top-50 nationally; 4-star ≈ top-300; 3-star ≈ rest
RECRUIT_RANK_PRIORS = {
    "5-star": 0.10,
    "4-star": 0.03,
    "3-star": -0.05,
    "2-star": -0.12,
    "unrated": -0.15,
}

POWER_4_CONFERENCES = {"SEC", "Big Ten", "ACC", "Big 12"}

DATA_DIR = Path(__file__).parent / "data" / "raw"
OVERRIDES_PATH = Path(__file__).parent / "data" / "manual" / "qb_overrides.csv"


def fetch_qb_stats(season: int) -> pd.DataFrame:
    """All FBS passer stats for the season (>=100 attempts qualifying)."""
    api_key = os.environ.get("CFBD_API_KEY")
    if not api_key:
        raise RuntimeError("CFBD_API_KEY not set")

    headers = {"Authorization": f"Bearer {api_key}"}
    url = f"{CFBD_BASE}/stats/player/season"
    print(f"Fetching CFBD passer stats for {season}")
    resp = requests.get(
        url,
        params={"year": season, "category": "passing"},
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    return pd.DataFrame(resp.json())


def classify_qb_status(qb_row: dict, prior_school_conf: str | None) -> tuple[str, float]:
    """
    Determine the regression weight (alpha) for a QB based on their context.

    Returns: (status_label, alpha)
    """
    if qb_row.get("is_freshman", False):
        return ("freshman", ALPHA_FRESHMAN)
    if qb_row.get("prior_school") and qb_row["prior_school"] != qb_row["team"]:
        # Transferred — figure out source-level
        if prior_school_conf in POWER_4_CONFERENCES:
            return ("p4_transfer", ALPHA_P4_TRANSFER)
        return ("g5_to_p4_transfer", ALPHA_G5_TO_P4_TRANSFER)
    if qb_row.get("attempts", 0) >= 200:
        return ("returning_starter", ALPHA_RETURNING_STARTER)
    return ("first_time_starter", ALPHA_FIRST_TIME_STARTER)


def compute_modifier(
    prior_epa: float, alpha: float, league_avg_epa: float
) -> float:
    """Apply the regression-weighted modifier formula."""
    raw = (prior_epa - league_avg_epa) * MODIFIER_SCALE * alpha
    return round(max(-MODIFIER_CAP, min(MODIFIER_CAP, raw)), 2)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Implementation pending — needs the CFBD /roster + /recruiting joins
    # to resolve transfer history and recruiting rank for the alpha lookup.
    # The function contracts above are what compute_ratings.py expects.
    raise NotImplementedError("Wire CFBD endpoints; see docstring for the flow.")


if __name__ == "__main__":
    main()
