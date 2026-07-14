"""Residual chart: horizontal bars by team, colored by conference."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

OUT_DIR = Path(__file__).parent / "output"

CONF_COLORS = {
    "SEC": "#1f4e8c",
    "Big Ten": "#c0392b",
    "Big 12": "#b7791f",
    "ACC": "#2e7d5b",
    "Pac-12": "#6b5b95",
    "American Athletic": "#d35400",
    "Mountain West": "#5d6d7e",
    "Sun Belt": "#16a085",
    "Conference USA": "#8e44ad",
    "Mid-American": "#7f8c8d",
    "FBS Independents": "#2c3e50",
}
FALLBACK_COLOR = "#95a5a6"


def residual_chart(residuals: pd.DataFrame, year: int, suffix: str = "") -> Path:
    df = residuals.sort_values("residual")
    colors = [CONF_COLORS.get(c, FALLBACK_COLOR) for c in df["conference"]]

    fig, ax = plt.subplots(figsize=(10, max(6, 0.32 * len(df))))
    ax.barh(df["team"], df["residual"], color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("FPI residual (actual − predicted from public inputs)")
    ax.set_title(
        f"{year} FPI vs public-input model: biggest over/under-rated teams\n"
        "positive = ESPN rates higher than public data explains"
    )

    seen = dict.fromkeys(df["conference"])
    handles = [
        plt.Rectangle((0, 0), 1, 1, color=CONF_COLORS.get(c, FALLBACK_COLOR))
        for c in seen
    ]
    ax.legend(handles, seen, fontsize=8, loc="lower right", title="Conference")
    fig.tight_layout()

    OUT_DIR.mkdir(exist_ok=True)
    path = OUT_DIR / f"residuals_{year}{suffix}.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
