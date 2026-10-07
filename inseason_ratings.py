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

Cap-artifact fix (built 2026-09-14, see INSEASON_UPDATE.md amendment): the
original cap clipped the MARGIN, so a 52-0 win by a team expected to win by
44 became "28 - 44 = -16" — elite teams were docked for cupcake blowouts and
cupcakes were paid for losing big. CAP_MODE = "residual" clips the
RESIDUAL (margin minus the prior expectation) at ±CAP instead: one game can
still move a rating by at most CAP points of evidence, but beating the
expectation is never a penalty. Backtest 2021-25: accuracy identical to the
margin cap (MAE within 0.07), schedule-neutral, better-calibrated out of
sample. Date-gated so the Ep4 / Week 3 card (frozen on the margin cap) is
not re-solved: from CAP_SWITCH_DATE every refresh runs the residual cap.

Efficiency layer (built 2026-09-14, efficiency.py / backtest_efficiency.py):
each game's fitted y can be EFF_W * actual margin + (1 - EFF_W) * deserved
margin (a per-game linear model of net total PPA and net success rate from
CFBD /stats/game/advanced, fit on 2021-24). Backtest 2021-25: neutral -
never better than the actual margin out of sample (2025 MAE 12.43 at EFF_W
1.0 vs 12.44-12.64 below it), so EFF_W stays 1.0 (off) for the rating. The
deserved margins are still produced (deserved_margins) for the receipts and
the luck column in the notes. Override with --eff-w for experiments.

De-lucked observations (built and measured 2026-09-27, internal/TURNOVER_2026.md;
Lucas switched it on the same day): from TO_SWITCH_DATE the ridge learns from
    margin - TO_PTS x (home takeaways - home giveaways)
instead of the raw margin (turnovers counted from the play-by-play,
obs_features.py), with the residual cap widened to 42; LAM 3 and HFA 2.5
unchanged. Backtest 2022-25: better than the 9/20 rule in every season and
on the held-out 2025 (pooled MAE 12.52 vs 12.70), gap to the market in the
under-14 buckets cut by a third. The grid optimum (lam 2, MARGIN cap 42)
scores 0.05 better still but brings back a mild cupcake-blowout penalty
(the artifact the 9/20 change removed) and drops Ohio State four places on
the day of the switch - not taken; one constant to flip if Lucas wants it. Week 4 and earlier were
graded on the rule of their day; nothing is regraded.

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
CAP_SWITCH_DATE = dt.date(2026, 9, 20)   # Week 4 cycle: first refresh after Ep4 records (INSEASON_UPDATE.md amendment)


def cap_mode_today(today: dt.date | None = None) -> str:
    """'margin' (pre-registered 2026-09-04) until CAP_SWITCH_DATE, then
    'residual' (the cap-artifact fix). Override with --cap-mode."""
    today = today or dt.date.today()
    return "residual" if CAP_SWITCH_DATE and today >= CAP_SWITCH_DATE else "margin"


CAP_MODE = cap_mode_today()
EFF_W = 1.0   # weight on the actual margin; 1.0 = efficiency layer off (backtest: neutral)
SIGMA_FROZEN = 17.94    # curve residual sd, frozen prior (fit_margin_curve)
SIGMA_INSEASON = 15.9   # pooled residual sd wks 2-14, the 9/20 rule (backtest)
SIGMA_DELUCKED = 15.8   # same, the de-lucked rule (backtest 2022-25, to3 / residual cap 42 / lam 3) - set below from the harness
OUT_JSON = HERE / "ratings_current_2026.json"

# De-lucked rule (TURNOVER_2026.md), on air from TO_SWITCH_DATE (Lucas 9/27).
TO_SWITCH_DATE = dt.date(2026, 9, 27)
RULE_DELUCKED = dict(lam=3.0, cap=42.0, cap_mode="residual", to_pts=3.0)   # the 9/20 residual-cap story stays true; only the observation changes (and the cap widens)
RULE_920 = dict(lam=3.0, cap=28.0, cap_mode="residual", to_pts=0.0)
RULE_PRESEASON = dict(lam=3.0, cap=28.0, cap_mode="margin", to_pts=0.0)


def rule_today(today: dt.date | None = None) -> dict:
    """The on-air rule by date: pre-registered margin cap -> residual cap
    (9/20) -> de-lucked observations (9/27). Every consumer solves through
    solve_2026 so a rule change lands everywhere at once."""
    today = today or dt.date.today()
    if TO_SWITCH_DATE and today >= TO_SWITCH_DATE:
        return dict(RULE_DELUCKED)
    if CAP_SWITCH_DATE and today >= CAP_SWITCH_DATE:
        return dict(RULE_920)
    return dict(RULE_PRESEASON)


RULE = rule_today()

# QB-out layer, on air from QB_SWITCH_DATE (Lucas 10/4: "the project is to find the most accurate model;
# the podcast shows the work"). ONLY manual QB entries with status "out" count (a confirmed absence, e.g. a
# season-ending injury, which the automatic flag cannot tell from a benching). The points come from the
# entry (--points, else QB_PEN) and come straight off that team's rating, so the Top 25, the card, the
# sim and the workbook all see them. Non-QB entries, "questionable" and the automatic flag stay in
# shadow (availability.py). QB_2026.md records the evidence and the grading plan.
QB_SWITCH_DATE = dt.date(2026, 10, 4)


def qb_out_adjust(week: int | None = None, today: dt.date | None = None) -> dict[str, float]:
    """{team: points taken off the rating} for QBs marked out in internal/availability.json that have not
    returned by `week` (default: the week after the last completed one). {} before QB_SWITCH_DATE."""
    today = today or dt.date.today()
    if not QB_SWITCH_DATE or today < QB_SWITCH_DATE:
        return {}
    f = HERE / "internal" / "availability.json"
    if not f.exists():
        return {}
    if week is None:
        week = latest_full_week(completed_games_2026()) + 1
    out: dict[str, float] = {}
    for e in json.loads(f.read_text(encoding="utf-8")):
        if str(e.get("pos", "")).upper() != "QB" or e.get("status") != "out":
            continue
        if e.get("return") is not None and week >= int(e["return"]):
            continue
        pts = float(e["points"]) if e.get("points") is not None else 3.0
        t = normalize_name(e["team"])
        out[t] = out.get(t, 0.0) + pts
    return out



def latest_full_week(games: list[dict], min_games: int = 20) -> int:
    """The last week with at least `min_games` completed games. A midweek game from the NEXT week
    (e.g. a Wednesday MAC/Sun Belt game) must not roll 'this week' forward: on 10/7 one Week-6 final
    made max(week) = 6, which dropped the QB-out penalty (return 7) and zeroed the Top 25 delta column."""
    from collections import Counter
    c = Counter((g["week"] or 0) for g in games)
    full = [w for w, n in c.items() if n >= min_games]
    return max(full) if full else max(c, default=0)

def turnover_margins(games: list[dict]) -> dict[int, float]:
    """{game_id: home takeaways - home giveaways} for 2026 games from the
    cached play-by-play (obs_features.py); empty if the plays are missing."""
    try:
        import obs_features as of
        f = of.build(2026, [dict(id=g["id"], week=g.get("week") or 0, home=g["home"], away=g["away"]) for g in games])
        return {gid: v["to_home"] for gid, v in f.items()}
    except Exception as e:  # noqa: BLE001
        print("turnover margins unavailable:", e)
        return {}


def solve_2026(prior: dict[str, float], games: list[dict], rule: dict | None = None) -> dict[str, float]:
    """The on-air solve for a set of 2026 games under today's rule (or `rule`)."""
    r = rule or RULE
    tm = turnover_margins(games) if r.get("to_pts") else {}
    return ridge_update(prior, games, lam=r["lam"], cap=r["cap"], cap_mode=r["cap_mode"],
                        to_pts=r.get("to_pts", 0.0), to_margin=tm)


def ridge_update(prior: dict[str, float], games: list[dict], lam: float = LAM,
                 cap: float | None = CAP, hfa: float = HFA,
                 cap_mode: str = "margin", to_pts: float = 0.0,
                 to_margin: dict | None = None) -> dict[str, float]:
    """games: dicts with home/away (normalized names in `prior`), neutral,
    margin (home minus away). Returns {team: rating} for every prior team.
    cap_mode: 'margin' clips the observed margin at ±cap (original rule);
    'residual' clips margin minus the prior expectation at ±cap (the
    cap-artifact fix: a blowout by a team expected to blow out is not a
    penalty, but no single game carries more than `cap` points of evidence)."""
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
    if to_pts and to_margin:
        y = y - to_pts * np.array([float(to_margin.get(g["id"], 0.0)) for g in games])
    if cap is not None and cap_mode == "margin":
        y = np.clip(y, -cap, cap)
    resid = y - (X @ p + h)
    if cap is not None and cap_mode == "residual":
        resid = np.clip(resid, -cap, cap)
    elif cap_mode not in ("margin", "residual"):
        raise ValueError(f"cap_mode must be 'margin' or 'residual', got {cap_mode!r}")
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


def deserved_margins(refresh: bool = False) -> dict[int, dict]:
    """{game_id: {deserved, home, away, net_tppa, net_sr}} for every 2026
    regular-season game with both advanced box scores (home perspective).
    Empty if efficiency_model.json is missing."""
    from efficiency import deserved, game_efficiency, load_model
    model = load_model()
    if model is None:
        return {}
    out = {}
    for gid, f in game_efficiency(2026, refresh).items():
        out[gid] = dict(deserved=round(deserved(f, model), 1), home=f["home"], away=f["away"],
                        net_tppa=round(f["net_tppa"], 1), net_sr=round(f["net_sr"], 3))
    return out


def machine_ratings(prior: dict[str, float], refresh: bool = False,
                    write: bool = True, cap_mode: str | None = None,
                    eff_w: float | None = None) -> dict[str, dict]:
    """{team: {pre, cur, delta, gp}} for every prior team; writes
    ratings_current_2026.json as the weekly receipt. cap_mode defaults to
    the date-gated CAP_MODE; eff_w to EFF_W (1.0 = actual margins only)."""
    cap_mode = cap_mode or CAP_MODE
    eff_w = EFF_W if eff_w is None else float(eff_w)
    games = [g for g in completed_games_2026(refresh)
             if g["home"] in prior and g["away"] in prior]
    fit_games = games
    if eff_w < 1.0:
        from efficiency import blend, load_model
        model = load_model()
        dm = deserved_margins(refresh) if model else {}
        fit_games = [dict(g, margin=blend(g["margin"], dm.get(g["id"]) and
                                          dict(net_tppa=dm[g["id"]]["net_tppa"],
                                               net_sr=dm[g["id"]]["net_sr"]),
                                          model, eff_w)) for g in games]
    rule = dict(RULE, cap_mode=cap_mode) if cap_mode != CAP_MODE else RULE
    cur = solve_2026(prior, fit_games, rule)
    qb = qb_out_adjust(latest_full_week(games) + 1)
    for t, pts in qb.items():
        if t in cur:
            cur[t] -= pts
    gp = {t: 0 for t in prior}
    for g in games:
        gp[g["home"]] += 1
        gp[g["away"]] += 1
    out = {t: dict(pre=round(prior[t], 1), cur=round(cur[t], 1),
                   delta=round(cur[t] - prior[t], 1), gp=gp[t],
                   **({"qb_out": round(qb[t], 1)} if qb.get(t) else {})) for t in prior}
    if write:
        ranked = sorted(out.items(), key=lambda kv: -kv[1]["cur"])
        OUT_JSON.write_text(json.dumps(dict(
            as_of=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            params=dict(lam=rule["lam"], cap=rule["cap"], cap_mode=rule["cap_mode"], to_pts=rule.get("to_pts", 0.0),
                        eff_w=eff_w, hfa=HFA, sigma=sigma_for(len(games)), rule_date=str(dt.date.today())),
            games_used=len(games),
            teams=[dict(team=t, **v) for t, v in ranked]), indent=1),
            encoding="utf-8")
    return out


def weekly_change(prior: dict[str, float], refresh: bool = False,
                  cap_mode: str | None = None) -> dict:
    """Week-over-week move: the current rating minus a re-solve WITHOUT the
    latest completed week's games, both under today's cap rule - so the column
    shows what the week's results did, never a rule change. Returns
    {"week": N, "teams": {team: {prev, d_week, prev_rank, rank, d_rank}}};
    d_rank is positive when a team climbed."""
    cap_mode = cap_mode or CAP_MODE
    games = [g for g in completed_games_2026(refresh)
             if g["home"] in prior and g["away"] in prior]
    if not games:
        return dict(week=None, teams={})
    week = latest_full_week(games)                     # not max(): a midweek game from next week must not move the column
    games = [g for g in games if (g["week"] or 0) <= week]
    rule = dict(RULE, cap_mode=cap_mode) if cap_mode != CAP_MODE else RULE
    cur = solve_2026(prior, games, rule)
    prev = solve_2026(prior, [g for g in games if (g["week"] or 0) < week], rule)
    for t, pts in qb_out_adjust(week + 1).items():     # same QB-out points on both sides: the column shows results, not the news
        if t in cur:
            cur[t] -= pts
            prev[t] -= pts
    rank = {t: i + 1 for i, t in enumerate(sorted(cur, key=lambda t: -cur[t]))}
    prev_rank = {t: i + 1 for i, t in enumerate(sorted(prev, key=lambda t: -prev[t]))}
    return dict(week=week, teams={
        t: dict(prev=round(prev[t], 1), d_week=round(cur[t] - prev[t], 1),
                prev_rank=prev_rank[t], rank=rank[t], d_rank=prev_rank[t] - rank[t])
        for t in cur})


def sigma_for(games_played: int) -> float:
    """Residual sd to run the margin curve at: frozen-prior sd until any
    rated game has been played, then the in-season backtest sd."""
    if games_played <= 0:
        return SIGMA_FROZEN
    return SIGMA_DELUCKED if RULE.get("to_pts") else SIGMA_INSEASON


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


def latest_rankings(refresh: bool = True) -> dict:
    """Latest available polls this season: {'week', 'season_type',
    'ap': {team: rank}, 'cfp': {team: rank}}. 'cfp' stays empty until the
    committee's first release (early November) and then fills on its own."""
    import cfbd_client as cfbd
    try:
        weeks = cfbd.get("/rankings", {"year": 2026}, refresh)
    except Exception as e:  # network hiccup: fall back to the cache
        print(f"rankings: pull failed ({e}); using cache")
        weeks = cfbd.get("/rankings", {"year": 2026}, False)
    out = dict(week=None, season_type=None, ap={}, cfp={})
    if not weeks:
        return out
    order = {"regular": 0, "postseason": 1}
    # CFBD sometimes lists the new week before the AP poll is attached to it
    # (e.g. only the coaches poll on Sunday morning) - use the latest week
    # that actually carries an AP poll.
    with_ap = [w for w in weeks if any((p.get("poll") or "").lower().startswith("ap")
                                       for p in w.get("polls", []))]
    pool = with_ap or weeks
    latest = max(pool, key=lambda w: (order.get(w.get("seasonType"), 0), w.get("week") or 0))
    out["week"], out["season_type"] = latest.get("week"), latest.get("seasonType")
    for poll in latest.get("polls", []):
        name = (poll.get("poll") or "").lower()
        key = "ap" if name.startswith("ap") else (
            "cfp" if ("playoff" in name or "committee" in name) else None)
        if key:
            for r in poll.get("ranks", []):
                team = r.get("school") or r.get("team")
                if team and r.get("rank") is not None:
                    out[key][normalize_name(team)] = int(r["rank"])
    return out


if __name__ == "__main__":
    from build_conference_book import load_fpi_2026
    pre = load_fpi_2026()
    mode = CAP_MODE
    if "--cap-mode" in sys.argv:
        mode = sys.argv[sys.argv.index("--cap-mode") + 1]
    eff_w = EFF_W
    if "--eff-w" in sys.argv:
        eff_w = float(sys.argv[sys.argv.index("--eff-w") + 1])
    mr = machine_ratings(pre, refresh="--refresh" in sys.argv, cap_mode=mode, eff_w=eff_w)
    n_games = sum(v["gp"] for v in mr.values()) // 2
    print(f"machine ratings: {len(mr)} teams, {n_games} rated games used, "
          f"lam={LAM:g} cap={CAP:g} ({mode}) eff_w={eff_w:g} sigma={sigma_for(n_games)}")
    movers = sorted(mr.items(), key=lambda kv: -abs(kv[1]["delta"]))[:12]
    print("biggest movers vs preseason:")
    for t, v in movers:
        print(f"  {t:22} {v['pre']:6.1f} -> {v['cur']:6.1f}  ({v['delta']:+.1f}, gp {v['gp']})")
    print(f"wrote {OUT_JSON.name}")
