"""Season sim with Lucas's podcast boards as the prior, vs the ESPN FPI sim.

Headline prior = TIER-SWAP: the boards assert tier membership (frozen in
lucas_board_2026.json from Lucas's own board columns), so each tier takes
the next block of its group's actual ESPN FPI value pool, and within a tier
values follow the market's own ordering — no within-tier claim, no invented
magnitudes. The full RANK-SWAP prior (his exact order) is kept as a
reference column. Independents keep ESPN FPI; the MAC participates via its
natively tiered board. Engine matches the workbook's Season Sim tab AS OF
THE 7/25 FREEZE: 10k Monte Carlo, sigma 13.5, HFA 2.5, unrated +24 (pinned
below), seed 2026 in every run, so every delta is the boards' doing.

Output: lucas_board_sim_2026.csv + console highlights.

--curve: methodology sensitivity companion (pre-Aug-29 only). Swaps ONLY
the margin->win-prob conversion for the empirical curve the live workbook
adopted 2026-08-18 (margin_prob_curve.json, residual sd 17.94); everything
else, including the +24 pin, stays frozen so exactly one variable moves.
Writes lucas_board_sim_2026_curve.csv — NEVER the frozen CSV.
--out PATH: redirect output (e.g. to verify the frozen CSV reproduces
without touching it).
"""
import json
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent   # lucas-board/
sys.path.insert(0, str(HERE.parent))     # repo root, for the workbook engine

from build_conference_book import HFA, fetch_games, load_fpi_2026, norm

SIGMA = 13.5
N_SIMS = 10_000
# FROZEN 2026-08-18: build_conference_book.UNRATED_MARGIN moved 24 -> 29 when
# the workbook adopted the empirical margin curve. The pre-registered CSV was
# built with +24; pinned here so it stays reproducible. Do not track the live
# constant.
UNRATED_MARGIN = 24.0


def simulate(games: list[dict], fpi: dict[str, dict], teams: list[str],
             conv) -> dict[str, dict]:
    win_probs: dict[str, list[float]] = {t: [] for t in teams}
    for g in games:
        for team, opp, is_home in ((g["home"], g["away"], True),
                                   (g["away"], g["home"], False)):
            if team not in win_probs:
                continue
            tf, of = fpi.get(norm(team)), fpi.get(norm(opp))
            if tf is None:
                continue
            margin = UNRATED_MARGIN if of is None else tf - of
            if not g["neutral"]:
                margin += HFA if is_home else -HFA
            win_probs[team].append(conv(margin))
    rng = np.random.default_rng(2026)
    out = {}
    for t in teams:
        ps = win_probs[t]
        if not ps:
            continue
        sims = (rng.random((N_SIMS, len(ps))) < np.array(ps)).sum(axis=1)
        out[t] = dict(games=len(ps), mean=float(sims.mean()),
                      bowl=float((sims >= 6).mean()),
                      ten=float((sims >= 10).mean()))
    return out


def main():
    args = sys.argv[1:]
    use_curve = "--curve" in args
    if use_curve:
        from margin_prob import load_curve
        curve = load_curve()
        conv = lambda m: float(curve.win_prob(m))
        conv_label = "empirical curve (sd 17.94) — SENSITIVITY COMPANION"
        out_path = HERE / "lucas_board_sim_2026_curve.csv"
    else:
        conv = NormalDist(0, SIGMA).cdf
        conv_label = f"Normal(0, {SIGMA:g}) — frozen 7/25 methodology"
        out_path = HERE / "lucas_board_sim_2026.csv"
    if "--out" in args:
        out_path = Path(args[args.index("--out") + 1])

    fpi = load_fpi_2026()
    board = json.load(open(HERE / "lucas_board_2026.json", encoding="utf-8"))

    groups: dict[str, list] = {}
    for v in board["teams"].values():
        groups.setdefault(v["group"], []).append(v)

    # rank-swap (reference): full Lucas order gets the group's value pool
    rank_fpi = dict(fpi)
    for group, members in groups.items():
        rated = [m for m in members
                 if norm(m["team"]) in fpi and m["lucas_rank"] is not None]
        values = sorted((fpi[norm(m["team"])] for m in rated), reverse=True)
        for m in sorted(rated, key=lambda m: m["lucas_rank"]):
            rank_fpi[norm(m["team"])] = values.pop(0)

    # tier-swap (headline): the board asserts TIER MEMBERSHIP only. Each
    # tier takes the next block of the group's value pool; within a tier,
    # values go by the market's own ordering (no within-tier claim).
    lucas_fpi = dict(fpi)
    for group, members in groups.items():
        rated = [m for m in members if norm(m["team"]) in fpi]
        values = sorted((fpi[norm(m["team"])] for m in rated), reverse=True)
        pos = 0
        for tier in sorted({m["tier"] for m in rated}):
            tm = [m for m in rated if m["tier"] == tier]
            block = values[pos:pos + len(tm)]
            pos += len(tm)
            for m, v in zip(sorted(tm, key=lambda m: -fpi[norm(m["team"])]),
                            block):
                lucas_fpi[norm(m["team"])] = v

    ranked = sorted(fpi.items(), key=lambda kv: -kv[1])
    wrapped = {k: {"fpi": v, "rank": i + 1}
               for i, (k, v) in enumerate(ranked)}
    games = fetch_games(False, wrapped)
    teams = sorted({g["home"] for g in games} | {g["away"] for g in games})
    teams = [t for t in teams if norm(t) in fpi]

    base = simulate(games, fpi, teams, conv)
    yours = simulate(games, lucas_fpi, teams, conv)
    ranky = simulate(games, rank_fpi, teams, conv)

    flags = {norm(v["team"]): v["flag"] for v in board["teams"].values()
             if v["flag"]}
    rows = []
    for t in teams:
        if t not in base or t not in yours:
            continue
        rows.append(dict(
            team=t,
            espn_fpi=round(fpi[norm(t)], 1),
            lucas_fpi=round(lucas_fpi[norm(t)], 1),
            espn_wins=round(base[t]["mean"], 2),
            lucas_wins=round(yours[t]["mean"], 2),
            rankswap_wins=round(ranky[t]["mean"], 2) if t in ranky else None,
            delta=round(yours[t]["mean"] - base[t]["mean"], 2),
            espn_bowl=round(base[t]["bowl"], 3),
            lucas_bowl=round(yours[t]["bowl"], 3),
            espn_10w=round(base[t]["ten"], 3),
            lucas_10w=round(yours[t]["ten"], 3),
            flag=flags.get(norm(t), "")))
    df = pd.DataFrame(rows).sort_values("delta", ascending=False)
    df.to_csv(out_path, index=False)

    print(f"simulated {len(df)} teams x {N_SIMS} runs, both priors "
          f"(seed 2026)\nconversion: {conv_label}\n")
    show = ["team", "espn_wins", "lucas_wins", "delta", "flag"]
    print("=== biggest gainers under Lucas's boards ===")
    print(df.head(10)[show].to_string(index=False))
    print("\n=== biggest losers ===")
    print(df.tail(10)[show].to_string(index=False))
    up = df[df.delta >= 1].shape[0]
    dn = df[df.delta <= -1].shape[0]
    print(f"\nteams moving >= +/-1 win: {up} up, {dn} down; "
          f"CSV: {out_path.name}")


if __name__ == "__main__":
    main()
