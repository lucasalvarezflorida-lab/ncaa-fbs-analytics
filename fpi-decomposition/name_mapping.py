"""Team-name normalization and cross-endpoint merge helpers.

CFBD endpoints are mostly consistent with each other, but a handful of
schools appear under different names depending on the data source that
endpoint mirrors (ESPN vs 247 vs CFBD's own team table). Everything is
normalized to a canonical key before merging, and merge coverage is
reported so silent drops are impossible to miss.
"""

from __future__ import annotations

import re
import unicodedata

import pandas as pd

# Alternate spellings -> canonical CFBD school name.
NAME_MAP = {
    "Mississippi": "Ole Miss",
    "Southern California": "USC",
    "Southern Cal": "USC",
    "Miami (FL)": "Miami",
    "Miami FL": "Miami",
    "Massachusetts": "UMass",
    "Appalachian State": "App State",
    "UT San Antonio": "UTSA",
    "Texas-San Antonio": "UTSA",
    "Hawaii": "Hawai'i",
    "San Jose State": "San José State",
    "Louisiana Monroe": "UL Monroe",
    "Louisiana-Monroe": "UL Monroe",
    "Southern Mississippi": "Southern Miss",
    "UConn": "Connecticut",
    "Central Florida": "UCF",
    "Florida International": "FIU",
    "Texas Christian": "TCU",
    "Brigham Young": "BYU",
    "Louisiana State": "LSU",
    "Southern Methodist": "SMU",
    "Middle Tennessee State": "Middle Tennessee",
    "Nevada-Las Vegas": "UNLV",
    "Army West Point": "Army",
    "Sam Houston State": "Sam Houston",
}


def normalize_name(name: str) -> str:
    """Canonical merge key: mapped name, accents stripped, lowercased."""
    name = str(name).strip()
    name = NAME_MAP.get(name, name)
    name = unicodedata.normalize("NFKD", name)
    name = "".join(c for c in name if not unicodedata.combining(c))
    name = re.sub(r"[^a-z0-9 ]", "", name.lower())
    return re.sub(r"\s+", " ", name).strip()


def add_merge_key(df: pd.DataFrame, team_col: str) -> pd.DataFrame:
    df = df.copy()
    df["team_key"] = df[team_col].map(normalize_name)
    return df


def merge_features(
    base: pd.DataFrame, features: dict[str, pd.DataFrame]
) -> tuple[pd.DataFrame, dict[str, dict]]:
    """Left-merge each feature frame onto base (both keyed on team_key).

    Returns the merged frame and a per-feature coverage report:
    matched count, base size, and the base teams that failed to match.
    """
    merged = base.copy()
    coverage = {}
    for name, feat in features.items():
        feat = feat.drop_duplicates(subset="team_key")
        cols = ["team_key"] + [c for c in feat.columns if c not in merged.columns]
        merged = merged.merge(feat[cols], on="team_key", how="left")
        value_cols = [c for c in cols if c != "team_key"]
        matched = merged[value_cols[0]].notna()
        coverage[name] = {
            "matched": int(matched.sum()),
            "total": len(merged),
            "unmatched_teams": sorted(merged.loc[~matched, "team"].tolist()),
        }
    return merged, coverage


def report_coverage(coverage: dict[str, dict]) -> str:
    lines = ["Merge coverage (vs FPI team list):"]
    for name, info in coverage.items():
        pct = 100 * info["matched"] / info["total"] if info["total"] else 0
        line = f"  {name:<16} {info['matched']}/{info['total']} ({pct:.0f}%)"
        if info["unmatched_teams"]:
            missing = ", ".join(info["unmatched_teams"][:8])
            extra = len(info["unmatched_teams"]) - 8
            line += f"  missing: {missing}" + (f" (+{extra} more)" if extra > 0 else "")
        lines.append(line)
    return "\n".join(lines)
