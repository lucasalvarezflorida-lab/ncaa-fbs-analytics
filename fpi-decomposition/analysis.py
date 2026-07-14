"""Analysis layer: feature construction, OLS fit, residual analysis.

CFBD has shipped both camelCase and snake_case field names over time, so
every column lookup goes through pick_col() with a candidate list instead
of hardcoding one spelling.
"""

from __future__ import annotations

import pandas as pd
import statsmodels.api as sm

import cfbd_client as cfbd
from name_mapping import add_merge_key, merge_features

FEATURE_COLS = ["prior_sp", "returning_prod", "talent", "recruiting_4yr"]


def pick_col(df: pd.DataFrame, candidates: list[str], context: str) -> str:
    for c in candidates:
        if c in df.columns:
            return c
    raise KeyError(
        f"None of {candidates} found in {context} response "
        f"(columns: {list(df.columns)})"
    )


def _frame(records: list, context: str) -> pd.DataFrame:
    if not records:
        raise ValueError(f"CFBD returned no rows for {context}")
    return pd.DataFrame(records)


def load_fpi(year: int, refresh: bool = False) -> tuple[pd.DataFrame, int]:
    """Load FPI for `year`, falling back to `year - 1` if not published yet."""
    for y in (year, year - 1):
        records = cfbd.fetch_fpi(y, refresh)
        if records:
            df = _frame(records, "/ratings/fpi")
            team = pick_col(df, ["team", "school"], "/ratings/fpi")
            fpi = pick_col(df, ["fpi", "rating"], "/ratings/fpi")
            conf = pick_col(df, ["conference", "conf"], "/ratings/fpi")
            out = df[[team, fpi, conf]].rename(
                columns={team: "team", fpi: "fpi", conf: "conference"}
            )
            out = out.dropna(subset=["fpi"])
            return add_merge_key(out, "team"), y
    raise ValueError(f"No FPI data on CFBD for {year} or {year - 1}")


def load_prior_sp(year: int, refresh: bool = False) -> pd.DataFrame:
    df = _frame(cfbd.fetch_sp(year - 1, refresh), "/ratings/sp")
    team = pick_col(df, ["team", "school"], "/ratings/sp")
    rating = pick_col(df, ["rating", "overall"], "/ratings/sp")
    out = df[df[team] != "nationalAverages"][[team, rating]].rename(
        columns={team: "team_sp", rating: "prior_sp"}
    )
    return add_merge_key(out, "team_sp").drop(columns="team_sp")


def load_returning(year: int, refresh: bool = False) -> pd.DataFrame:
    df = _frame(cfbd.fetch_returning(year, refresh), "/player/returning")
    team = pick_col(df, ["team", "school"], "/player/returning")
    ppa = pick_col(
        df,
        ["totalPPA", "total_ppa", "totalPpa", "percentPPA", "percent_ppa"],
        "/player/returning",
    )
    out = df[[team, ppa]].rename(columns={team: "team_ret", ppa: "returning_prod"})
    return add_merge_key(out, "team_ret").drop(columns="team_ret")


def load_talent(year: int, refresh: bool = False) -> pd.DataFrame:
    df = _frame(cfbd.fetch_talent(year, refresh), "/talent")
    team = pick_col(df, ["team", "school"], "/talent")
    talent = pick_col(df, ["talent", "composite"], "/talent")
    out = df[[team, talent]].rename(columns={team: "team_tal", talent: "talent"})
    out["talent"] = pd.to_numeric(out["talent"], errors="coerce")
    return add_merge_key(out, "team_tal").drop(columns="team_tal")


def load_recruiting_4yr(year: int, refresh: bool = False) -> pd.DataFrame:
    frames = []
    for y in range(year - 3, year + 1):
        df = _frame(cfbd.fetch_recruiting(y, refresh), "/recruiting/teams")
        team = pick_col(df, ["team", "school"], "/recruiting/teams")
        points = pick_col(df, ["points", "score"], "/recruiting/teams")
        part = df[[team, points]].rename(columns={team: "team_rec", points: "points"})
        part["points"] = pd.to_numeric(part["points"], errors="coerce")
        frames.append(part)
    allyears = pd.concat(frames)
    avg = (
        allyears.groupby("team_rec", as_index=False)["points"]
        .mean()
        .rename(columns={"points": "recruiting_4yr"})
    )
    return add_merge_key(avg, "team_rec").drop(columns="team_rec")


def load_portal(year: int, refresh: bool = False) -> pd.DataFrame:
    """Net portal rating: sum of incoming transfer ratings minus outgoing."""
    df = _frame(cfbd.fetch_portal(year, refresh), "/player/portal")
    origin = pick_col(df, ["origin", "from"], "/player/portal")
    dest = pick_col(df, ["destination", "to"], "/player/portal")
    rating = pick_col(df, ["rating", "stars"], "/player/portal")
    df = df.copy()
    df["rating_num"] = pd.to_numeric(df[rating], errors="coerce").fillna(0)

    incoming = df.groupby(dest)["rating_num"].sum().rename("in_rating")
    outgoing = df.groupby(origin)["rating_num"].sum().rename("out_rating")
    net = pd.concat([incoming, outgoing], axis=1).fillna(0)
    net["net_portal"] = net["in_rating"] - net["out_rating"]
    net = net.reset_index().rename(columns={"index": "team_portal"})
    return add_merge_key(net[["team_portal", "net_portal"]], "team_portal").drop(
        columns="team_portal"
    )


def build_dataset(
    year: int, refresh: bool = False, transfer: bool = False
) -> tuple[pd.DataFrame, dict, int]:
    fpi, fpi_year = load_fpi(year, refresh)
    features = {
        "prior_sp": load_prior_sp(fpi_year, refresh),
        "returning_prod": load_returning(fpi_year, refresh),
        "talent": load_talent(fpi_year, refresh),
        "recruiting_4yr": load_recruiting_4yr(fpi_year, refresh),
    }
    if transfer:
        features["net_portal"] = load_portal(fpi_year, refresh)
    merged, coverage = merge_features(fpi, features)
    return merged, coverage, fpi_year


def standardize(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        out[c] = (out[c] - out[c].mean()) / out[c].std(ddof=0)
    return out


def fit_ols(df: pd.DataFrame, feature_cols: list[str]):
    """Fit fpi ~ standardized(features) on complete cases."""
    data = df.dropna(subset=["fpi"] + feature_cols)
    data = standardize(data, feature_cols)
    X = sm.add_constant(data[feature_cols])
    model = sm.OLS(data["fpi"], X).fit()
    data = data.assign(
        predicted=model.predict(X), residual=data["fpi"] - model.predict(X)
    )
    # Keep raw feature values alongside for output readability.
    raw = df.loc[data.index, feature_cols]
    data[[f"{c}_raw" for c in feature_cols]] = raw
    return model, data


def top_bottom_residuals(fitted: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    ranked = fitted.sort_values("residual", ascending=False)
    keep = ["team", "conference", "fpi", "predicted", "residual"]
    top = ranked.head(n).assign(group="FPI higher than public inputs explain")
    bottom = ranked.tail(n).assign(group="FPI lower than public inputs explain")
    return pd.concat([top, bottom])[keep + ["group"]].round(2)
