"""Warm the CFBD cache for the market post-mortem (2021-2025).

Fetches /lines, /games (regular + postseason) and /rankings (regular) for each
season through the shared cached client, so downstream scripts never touch the
network. Prints row counts only — never the API key.

Usage: python fetch_data.py
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "fpi-decomposition"))

import cfbd_client as cfbd

SEASONS = [2021, 2022, 2023, 2024, 2025]


def main() -> None:
    for year in SEASONS:
        for stype in ("regular", "postseason"):
            games = cfbd.get("/games", {"year": year, "seasonType": stype})
            lines = cfbd.get("/lines", {"year": year, "seasonType": stype})
            with_line = sum(1 for g in lines if g.get("lines"))
            print(f"{year} {stype:<10} games={len(games):>4}  "
                  f"line-records={len(lines):>4} (with>=1 book: {with_line})")
        ranks = cfbd.get("/rankings", {"year": year, "seasonType": "regular"})
        print(f"{year} rankings   weeks={len(ranks)}")


if __name__ == "__main__":
    main()
