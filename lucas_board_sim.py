"""Season sim with Lucas's podcast boards as the prior, vs the ESPN FPI sim.

The boards are ordinal, so the prior is built by RANK-SWAP within each board
group: the group's actual ESPN preseason FPI values are redistributed
according to Lucas's order (his #1 gets the group's best FPI value, etc.).
No magnitudes are invented; only the ordering changes. Teams not on a board
(MAC, independents) keep their ESPN FPI. Same engine as the workbook's
Season Sim tab: 10k Monte Carlo, sigma 13.5, HFA 2.5, unrated +24, seed
2026 — identical in both runs, so every delta is the boards' doing.

Output: lucas_board_sim_2026.csv + console highlights.
"""
import json
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

from build_conference_book import (HFA, UNRATED_MARGIN, fetch_games,
                                   load_fpi_2026, norm)

HERE = Path(__file__).resolve().parent
SIGMA = 13.5
N_SIMS = 10_000


def simulate(games: list[dict], fpi: dict[str, dict],
             teams: list[str]) -> dict[str, dict]:
    nd = NormalDist(0, SIGMA)
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
            win_probs[team].append(nd.cdf(margin))
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
    fpi = load_fpi_2026()
    board = json.load(open(HERE / "lucas_board_2026.json", encoding="utf-8"))

    # rank-swap within each board group
    lucas_fpi = dict(fpi)
    groups: dict[str, list] = {}
    for v in board["teams"].values():
        groups.setdefault(v["group"], []).append(v)
    for group, members in groups.items():
        rated = [m for m in members if norm(m["team"]) in fpi]
        values = sorted((fpi[norm(m["team"])] for m in rated), reverse=True)
        for m in sorted(rated, key=lambda m: m["lucas_rank"]):
            lucas_fpi[norm(m["team"])] = values.pop(0)

    ranked = sorted(fpi.items(), key=lambda kv: -kv[1])
    wrapped = {k: {"fpi": v, "rank": i + 1}
               for i, (k, v) in enumerate(ranked)}
    games = fetch_games(False, wrapped)
    teams = sorted({g["home"] for g in games} | {g["away"] for g in games})
    teams = [t for t in teams if norm(t) in fpi]

    base = simulate(games, fpi, teams)
    yours = simulate(games, lucas_fpi, teams)

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
            delta=round(yours[t]["mean"] - base[t]["mean"], 2),
            espn_bowl=round(base[t]["bowl"], 3),
            lucas_bowl=round(yours[t]["bowl"], 3),
            espn_10w=round(base[t]["ten"], 3),
            lucas_10w=round(yours[t]["ten"], 3),
            flag=flags.get(norm(t), "")))
    df = pd.DataFrame(rows).sort_values("delta", ascending=False)
    df.to_csv(HERE / "lucas_board_sim_2026.csv", index=False)

    print(f"simulated {len(df)} teams x {N_SIMS} runs, both priors "
          f"(seed 2026)\n")
    show = ["team", "espn_wins", "lucas_wins", "delta", "flag"]
    print("=== biggest gainers under Lucas's boards ===")
    print(df.head(10)[show].to_string(index=False))
    print("\n=== biggest losers ===")
    print(df.tail(10)[show].to_string(index=False))
    up = df[df.delta >= 1].shape[0]
    dn = df[df.delta <= -1].shape[0]
    print(f"\nteams moving >= +/-1 win: {up} up, {dn} down; "
          f"CSV: lucas_board_sim_2026.csv")


if __name__ == "__main__":
    main()
