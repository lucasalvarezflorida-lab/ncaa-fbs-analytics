"""Our own in-season rating update — "the machine's FPI".

Prior = ESPN's 2026 preseason FPI snapshot (frozen in July). Each refresh,
the current rating is the ridge / Bayesian-posterior solution over every
completed 2026 game between rated teams:
    minimize  sum_games (margin - (r_home - r_away + HFA))^2
            + LAM * sum_teams (r_team - prior_team)^2
LAM = how many games of evidence the prior is worth. Parameters were chosen
by backtest_inseason_update.py on 2021-24 (prior-year final FPI as the
prior) and validated out of sample on 2025 — see INSEASON_UPDATE.md.
Pre-registered 2026-09-04: LAM = 3, margins capped at ±28, HFA 2.5.

Consumers: build_conference_book (workbook prior), edge_report (card_data
-> deck), Season Sim. The preseason snapshot itself is never modified —
preseason artifacts stay frozen for grading.
"""

import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

LAM = 3.0
CAP = 28.0
HFA = 2.5
SIGMA_FROZEN = 17.94    # curve residual sd, frozen prior (fit_margin_curve)
SIGMA_INSEASON = 15.9   # pooled residual sd wks 2-14, chosen config (backtest)
OUT_JSON = HERE / "ratings_current_2026.json"


def ridge_update(prior: dict[str, float], games: list[dict], lam: float = LAM,
                 cap: float | None = CAP, hfa: float = HFA) -> dict[str, float]:
    """games: dicts with home/away (normalized names in `prior`), neutral,
    margin (home minus away). Returns {team: rating} for every prior team."""
    teams = sorted(prior)
    p = np.array([prior[t] for t in teams])
    games = [g for g in games if g["home"] in prior and g["away"] in prior]
    if not games or not np.isfinite(lam):
        return dict(zip(teams, p))
    idx = {t: i for i, t in enumerate(teams)}
    n = len(games)
    X = np.zeros((n, len(teams)))
    X[np.arange(n), [idx[g["home"]] for g in games]] = 1.0
    X[np.arange(n), [idx[g["away"]] for g in games]] = -1.0
    h = np.array([0.0 if g["neutral"] else hfa for g in games])
    y = np.array([float(g["margin"]) for g in games])
    if cap is not None:
        y = np.clip(y, -cap, cap)
    resid = y - (X @ p + h)
    d = np.linalg.solve(X.T @ X + lam * np.eye(len(teams)), X.T @ resid)
    return dict(zip(teams, p + d))


def _pick(g, *names):
    for k in names:
        if g.get(k) is not None:
            return g[k]
    return None


def completed_games_2026(refresh: bool = False) -> list[dict]:
    """Completed 2026 regular-season games with both scores, normalized names."""
    import cfbd_client as cfbd
    out = []
    for g in cfbd.get("/games", {"year": 2026, "seasonType": "regular"}, refresh):
        if not _pick(g, "completed"):
            continue
        hp, ap = _pick(g, "homePoints", "home_points"), _pick(g, "awayPoints", "away_points")
        home, away = _pick(g, "homeTeam", "home_team"), _pick(g, "awayTeam", "away_team")
        if hp is None or ap is None or not home or not away:
            continue
        out.append(dict(id=_pick(g, "id"), week=_pick(g, "week"),
                        home=normalize_name(home), away=normalize_name(away),
                        neutral=bool(_pick(g, "neutralSite", "neutral_site")),
                        margin=float(hp - ap)))
    return out


def machine_ratings(prior: dict[str, float], refresh: bool = False,
                    write: bool = True) -> dict[str, dict]:
    """{team: {pre, cur, delta, gp}} for every prior team; writes
    ratings_current_2026.json as the weekly receipt."""
    games = [g for g in completed_games_2026(refresh)
             if g["home"] in prior and g["away"] in prior]
    cur = ridge_update(prior, games)
    gp = {t: 0 for t in prior}
    for g in games:
        gp[g["home"]] += 1
        gp[g["away"]] += 1
    out = {t: dict(pre=round(prior[t], 1), cur=round(cur[t], 1),
                   delta=round(cur[t] - prior[t], 1), gp=gp[t]) for t in prior}
    if write:
        ranked = sorted(out.items(), key=lambda kv: -kv[1]["cur"])
        OUT_JSON.write_text(json.dumps(dict(
            as_of=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            params=dict(lam=LAM, cap=CAP, hfa=HFA, sigma=sigma_for(len(games))),
            games_used=len(games),
            teams=[dict(team=t, **v) for t, v in ranked]), indent=1),
            encoding="utf-8")
    return out


def sigma_for(games_played: int) -> float:
    """Residual sd to run the margin curve at: frozen-prior sd until any
    rated game has been played, then the in-season backtest sd."""
    return SIGMA_INSEASON if games_played > 0 else SIGMA_FROZEN


def espn_live_fpi(refresh: bool = True) -> dict[str, float]:
    """ESPN's CURRENT 2026 FPI (updates weekly in season) — the reference
    column only; the machine never uses it as its rating."""
    import cfbd_client as cfbd
    try:
        rows = cfbd.get("/ratings/fpi", {"year": 2026}, refresh)
    except Exception as e:  # network hiccup: fall back to the cache
        print(f"ESPN live FPI: pull failed ({e}); using cache")
        rows = cfbd.get("/ratings/fpi", {"year": 2026}, False)
    return {normalize_name(r.get("team") or r.get("school")): float(r["fpi"])
            for r in rows if r.get("fpi") is not None and (r.get("team") or r.get("school"))}


if __name__ == "__main__":
    from build_conference_book import load_fpi_2026
    pre = load_fpi_2026()
    mr = machine_ratings(pre, refresh="--refresh" in sys.argv)
    n_games = sum(v["gp"] for v in mr.values()) // 2
    print(f"machine ratings: {len(mr)} teams, {n_games} rated games used, "
          f"lam={LAM:g} cap={CAP:g} sigma={sigma_for(n_games)}")
    movers = sorted(mr.items(), key=lambda kv: -abs(kv[1]["delta"]))[:12]
    print("biggest movers vs preseason:")
    for t, v in movers:
        print(f"  {t:22} {v['pre']:6.1f} -> {v['cur']:6.1f}  ({v['delta']:+.1f}, gp {v['gp']})")
    print(f"wrote {OUT_JSON.name}")
