"""
NCAA FBS Team Ratings — Phase 5: Ratings consolidation (LIVE pipeline)

Reads the merged SP+ + PPA-splits CSV and produces five sub-ratings plus
a composite per team, all on the 0-10 z-score scale.

Reads:
    data/raw/sp_plus.csv

Writes:
    data/team_ratings.json   (workbook contract)
    data/team_ratings.csv    (inspection)

This MVP computes sub-ratings from the PPA splits and ST from SP+.
Returning-production prior, QB modifier, and rest modifier are passthrough
(zero) until those phases are wired.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# Z-score normalization: z=+2.5 -> 10, z=0 -> 5, z=-2.5 -> 0
Z_RATING_SCALE = 5.0 / 2.5
RATING_MIN, RATING_MAX = 0.0, 10.0

COMPOSITE_WEIGHTS = {
    "rush_o": 0.25, "pass_o": 0.25, "rush_d": 0.25, "pass_d": 0.25, "st": 0.10,
}
COMPOSITE_DIVISOR = sum(COMPOSITE_WEIGHTS.values())

DATA_DIR = Path(__file__).parent / "data" / "raw"
OUTPUT_DIR = Path(__file__).parent / "data"


def z_score_to_rating(values: pd.Series, invert: bool = False) -> pd.Series:
    vals = values.dropna()
    if len(vals) == 0:
        return pd.Series([5.0] * len(values), index=values.index)
    mean = vals.mean()
    std = vals.std(ddof=0)
    if std == 0:
        return pd.Series([5.0] * len(values), index=values.index)
    z = (values - mean) / std
    if invert:
        z = -z
    rating = 5.0 + z * Z_RATING_SCALE
    return rating.clip(RATING_MIN, RATING_MAX).round(2)


def compute_sub_ratings(df: pd.DataFrame) -> pd.DataFrame:
    df["rush_o_rating"] = z_score_to_rating(df["ppa_rush_o"])
    df["pass_o_rating"] = z_score_to_rating(df["ppa_pass_o"])
    df["rush_d_rating"] = z_score_to_rating(df["ppa_rush_d"], invert=True)
    df["pass_d_rating"] = z_score_to_rating(df["ppa_pass_d"], invert=True)
    df["st_rating"]     = z_score_to_rating(df["sp_st"])
    df["sp_off_rating"] = z_score_to_rating(df["sp_off"])
    df["sp_def_rating"] = z_score_to_rating(df["sp_def"], invert=True)
    df["sp_overall_rating"] = z_score_to_rating(df["sp_overall"])
    return df


def compute_composite(df: pd.DataFrame) -> pd.DataFrame:
    w = COMPOSITE_WEIGHTS
    df["composite"] = (
        (w["rush_o"] * df["rush_o_rating"]
         + w["pass_o"] * df["pass_o_rating"]
         + w["rush_d"] * df["rush_d_rating"]
         + w["pass_d"] * df["pass_d_rating"]
         + w["st"]     * df["st_rating"]) / COMPOSITE_DIVISOR
    ).round(2)
    return df


def save_json(df: pd.DataFrame, path: Path, season: int) -> None:
    teams = {}
    for _, row in df.iterrows():
        teams[row["team"]] = {
            "conference": row.get("conference"),
            "sub_ratings": {
                "rush_o": float(row["rush_o_rating"]),
                "pass_o": float(row["pass_o_rating"]),
                "rush_d": float(row["rush_d_rating"]),
                "pass_d": float(row["pass_d_rating"]),
                "special_teams": float(row["st_rating"]),
            },
            "composite": float(row["composite"]),
            "sp_plus": {
                "overall_rating": None if pd.isna(row["sp_overall"]) else float(row["sp_overall"]),
                "offense_rating": None if pd.isna(row["sp_off"]) else float(row["sp_off"]),
                "defense_rating": None if pd.isna(row["sp_def"]) else float(row["sp_def"]),
                "st_rating":      None if pd.isna(row["sp_st"]) else float(row["sp_st"]),
            },
            "raw_ppa": {
                "rush_o": None if pd.isna(row["ppa_rush_o"]) else float(row["ppa_rush_o"]),
                "pass_o": None if pd.isna(row["ppa_pass_o"]) else float(row["ppa_pass_o"]),
                "rush_d": None if pd.isna(row["ppa_rush_d"]) else float(row["ppa_rush_d"]),
                "pass_d": None if pd.isna(row["ppa_pass_d"]) else float(row["ppa_pass_d"]),
            },
        }
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "season": season,
        "methodology": "SP+ context + PPA-split z-score sub-ratings",
        "composite_weights": COMPOSITE_WEIGHTS,
        "teams": teams,
    }
    path.write_text(json.dumps(payload, indent=2))


def main(season: int = 2025) -> None:
    df = pd.read_csv(DATA_DIR / "sp_plus.csv")
    print(f"Loaded {len(df)} teams from sp_plus.csv")

    df = compute_sub_ratings(df)
    df = compute_composite(df)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_DIR / "team_ratings.csv", index=False, float_format="%.3f")
    save_json(df, OUTPUT_DIR / "team_ratings.json", season=season)

    print("\nTop 15 by composite rating:")
    cols = ["team", "conference", "rush_o_rating", "pass_o_rating",
            "rush_d_rating", "pass_d_rating", "st_rating", "composite"]
    print(df.nlargest(15, "composite")[cols].to_string(index=False))

    print("\nMiami calibration check:")
    m = df[df["team"] == "Miami"].iloc[0]
    print(f"  Rush O: {m['rush_o_rating']}  (PPA {m['ppa_rush_o']:.3f})")
    print(f"  Pass O: {m['pass_o_rating']}  (PPA {m['ppa_pass_o']:.3f})")
    print(f"  Rush D: {m['rush_d_rating']}  (PPA {m['ppa_rush_d']:.3f})")
    print(f"  Pass D: {m['pass_d_rating']}  (PPA {m['ppa_pass_d']:.3f})")
    print(f"  ST:     {m['st_rating']}  (SP+ ST {m['sp_st']:.2f})")
    print(f"  Composite: {m['composite']}")
    print(f"  SP+ Overall: {m['sp_overall']:.2f} (rescaled: {m['sp_overall_rating']})")


if __name__ == "__main__":
    main()
