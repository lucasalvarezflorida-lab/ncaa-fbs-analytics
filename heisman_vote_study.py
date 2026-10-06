"""Heisman VOTE study (INTERNAL, Lucas 10/6/2026: "flip it to production -> the vote").

Fits the Heisman ballot 2014-2025: each season's top-10 vote shares (points / points of the top 10) against the season's
candidate pool - every QB, RB, WR and TE with 30+ plays in CFBD's /ppa/players/season - using what a voter sees at the end
of the regular season: points added per game, PPA per play, plays per game, team wins, final AP rank, position, conference.
MODEL   softmax over each season's pool (a ballot is a choice among candidates): P(i) ∝ exp(w · x_i); w fit by maximum
        likelihood on the vote shares (soft labels), L2-shrunk. Fit 2014-2021, test 2022-2025, then refit on all.
BASELINES  the on-air production board (points a game × team factor) and points a game alone, ranked the same way.
SCORED  on the test seasons: the winner's rank, winner log-likelihood, top-3 overlap, share-weighted log loss.
THEN    the 2026 board as of today: to-date PPA with the Season Sim's projected wins standing in for final wins, the
        current AP rank -> P(win) per player, next to DraftKings -> internal/HEISMAN_STUDY_2026.md.
LIMITS  defensive and two-way players (Hutchinson, Chase Young, Travis Hunter) are not in the pool: their votes are
        dropped from the denominator, so 2024 is fit on Jeanty/Gabriel/Ward shares. 2019, 2015 and 2024-25 carry only the
        places with published points. Features are end-of-season; in-season use needs projections (noted on the board).

    python heisman_vote_study.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

RAW = json.loads((HERE / "internal" / "heisman_pool_raw.json").read_text(encoding="utf-8"))
FIT, TEST, NOW = range(2014, 2022), range(2022, 2026), 2026
POWER = {"SEC", "Big Ten", "Big 12", "ACC", "Pac-12", "FBS Independents"}

# (player, school, position, points) - published results; defensive / two-way players left out of the pool
VOTES = {
 2025: [("Fernando Mendoza", "Indiana", "QB", 2362), ("Diego Pavia", "Vanderbilt", "QB", 1435), ("Jeremiyah Love", "Notre Dame", "RB", 719), ("Julian Sayin", "Ohio State", "QB", 432)],
 2024: [("Ashton Jeanty", "Boise State", "RB", 2017), ("Dillon Gabriel", "Oregon", "QB", 516), ("Cam Ward", "Miami", "QB", 229), ("Cam Skattebo", "Arizona State", "RB", 170), ("Bryson Daily", "Army", "QB", 69), ("Tyler Warren", "Penn State", "TE", 52)],
 2023: [("Jayden Daniels", "LSU", "QB", 2029), ("Michael Penix Jr.", "Washington", "QB", 1701), ("Bo Nix", "Oregon", "QB", 885), ("Marvin Harrison Jr.", "Ohio State", "WR", 352), ("Jordan Travis", "Florida State", "QB", 85), ("Jalen Milroe", "Alabama", "QB", 73), ("Ollie Gordon II", "Oklahoma State", "RB", 31), ("Cody Schrader", "Missouri", "RB", 29), ("Blake Corum", "Michigan", "RB", 28), ("J.J. McCarthy", "Michigan", "QB", 21)],
 2022: [("Caleb Williams", "USC", "QB", 2031), ("Max Duggan", "TCU", "QB", 1420), ("C.J. Stroud", "Ohio State", "QB", 539), ("Stetson Bennett", "Georgia", "QB", 349), ("Hendon Hooker", "Tennessee", "QB", 226), ("Bryce Young", "Alabama", "QB", 141), ("Blake Corum", "Michigan", "RB", 125), ("Michael Penix Jr.", "Washington", "QB", 114), ("Bijan Robinson", "Texas", "RB", 75), ("Drake Maye", "North Carolina", "QB", 42)],
 2021: [("Bryce Young", "Alabama", "QB", 2311), ("Kenny Pickett", "Pittsburgh", "QB", 631), ("C.J. Stroud", "Ohio State", "QB", 399), ("Kenneth Walker III", "Michigan State", "RB", 245), ("Matt Corral", "Ole Miss", "QB", 150), ("Desmond Ridder", "Cincinnati", "QB", 81), ("Breece Hall", "Iowa State", "RB", 17)],
 2020: [("DeVonta Smith", "Alabama", "WR", 1856), ("Trevor Lawrence", "Clemson", "QB", 1187), ("Mac Jones", "Alabama", "QB", 1130), ("Kyle Trask", "Florida", "QB", 737), ("Najee Harris", "Alabama", "RB", 216), ("Breece Hall", "Iowa State", "RB", 64), ("Justin Fields", "Ohio State", "QB", 48), ("Zach Wilson", "BYU", "QB", 42), ("Ian Book", "Notre Dame", "QB", 38), ("Kyle Pitts", "Florida", "TE", 24)],
 2019: [("Joe Burrow", "LSU", "QB", 2608), ("Jalen Hurts", "Oklahoma", "QB", 762), ("Justin Fields", "Ohio State", "QB", 747), ("Jonathan Taylor", "Wisconsin", "RB", 189), ("J.K. Dobbins", "Ohio State", "RB", 114), ("Trevor Lawrence", "Clemson", "QB", 88), ("Chuba Hubbard", "Oklahoma State", "RB", 68)],
 2018: [("Kyler Murray", "Oklahoma", "QB", 2167), ("Tua Tagovailoa", "Alabama", "QB", 1871), ("Dwayne Haskins", "Ohio State", "QB", 783), ("Will Grier", "West Virginia", "QB", 126), ("Gardner Minshew", "Washington State", "QB", 122), ("McKenzie Milton", "UCF", "QB", 39), ("Travis Etienne", "Clemson", "RB", 29), ("Jonathan Taylor", "Wisconsin", "RB", 26), ("Darrell Henderson", "Memphis", "RB", 21)],
 2017: [("Baker Mayfield", "Oklahoma", "QB", 2398), ("Bryce Love", "Stanford", "RB", 1300), ("Lamar Jackson", "Louisville", "QB", 793), ("Saquon Barkley", "Penn State", "RB", 304), ("Rashaad Penny", "San Diego State", "RB", 175), ("Jonathan Taylor", "Wisconsin", "RB", 58), ("Mason Rudolph", "Oklahoma State", "QB", 56), ("McKenzie Milton", "UCF", "QB", 54), ("Kerryon Johnson", "Auburn", "RB", 45)],
 2016: [("Lamar Jackson", "Louisville", "QB", 2144), ("Deshaun Watson", "Clemson", "QB", 1524), ("Baker Mayfield", "Oklahoma", "QB", 361), ("Dede Westbrook", "Oklahoma", "WR", 209), ("Jake Browning", "Washington", "QB", 182), ("D'Onta Foreman", "Texas", "RB", 131), ("Christian McCaffrey", "Stanford", "RB", 103), ("Dalvin Cook", "Florida State", "RB", 67)],
 2015: [("Derrick Henry", "Alabama", "RB", 1832), ("Christian McCaffrey", "Stanford", "RB", 1539), ("Deshaun Watson", "Clemson", "QB", 1165), ("Baker Mayfield", "Oklahoma", "QB", 334), ("Keenan Reynolds", "Navy", "QB", 180), ("Leonard Fournette", "LSU", "RB", 110), ("Dalvin Cook", "Florida State", "RB", 79), ("Ezekiel Elliott", "Ohio State", "RB", 57)],
 2014: [("Marcus Mariota", "Oregon", "QB", 2534), ("Melvin Gordon", "Wisconsin", "RB", 1250), ("Amari Cooper", "Alabama", "WR", 1023), ("Trevone Boykin", "TCU", "QB", 218), ("J.T. Barrett", "Ohio State", "QB", 78), ("Jameis Winston", "Florida State", "QB", 51), ("Tevin Coleman", "Indiana", "RB", 44), ("Dak Prescott", "Mississippi State", "QB", 21), ("Bryce Petty", "Baylor", "QB", 13)],
}
FEATS = ["ppg_z", "pos_z", "ppa_z", "wins", "top5", "top10", "log_rank", "qb", "rb", "power"]
POOL_N = {"QB": 25, "RB": 15, "WR": 12, "TE": 4}   # voters consider stars: the top of each position by points a game


def key(name):
    n = re.sub(r"[.'']", "", name.lower())
    n = re.sub(r"\b(jr|sr|ii|iii|iv)\b", "", n).split()
    return n[-1] if n else ""          # last name; matched together with the school


def pool(year, sim=None):
    raw = RAW[str(year)]
    rec = {}
    for r in raw["records"]:
        t = r.get("total") or {}
        rec[normalize_name(r["team"])] = dict(games=t.get("games") or 0, wins=t.get("wins") or 0, conf=r.get("conference"))
    ap = {}
    wk = [w for w in raw["rankings"] if w.get("seasonType") == "regular"]
    if wk:
        last = max(wk, key=lambda w: w["week"])
        for p in last["polls"]:
            if p["poll"] == "AP Top 25":
                ap = {normalize_name(x["school"]): x["rank"] for x in p["ranks"]}
    rows = []
    for pos in ("QB", "RB", "WR", "TE"):
        for c in raw[pos]:
            avg, tot = c["averagePPA"]["all"], c["totalPPA"]["all"]
            if not avg or not tot:
                continue
            team = normalize_name(c["team"]); rc = rec.get(team)
            if not rc or rc["games"] < (3 if sim is not None else 6):
                continue
            plays = tot / avg
            if plays < (40 if sim is not None else 60):
                continue
            games = rc["games"]; wins = rc["wins"]
            if sim is not None:                       # 2026: projected season instead of the finished one
                s = sim.get(c["team"])
                if not s:
                    continue
                games = games or 1; wins = s["proj"]
            rank = ap.get(team)
            rows.append(dict(year=year, name=c["name"], team=c["team"], pos=pos, ppg=tot / games, ppa=avg, plays_pg=plays / games,
                             wins=float(wins), top5=float(rank is not None and rank <= 5), top10=float(rank is not None and rank <= 10),
                             log_rank=np.log(rank if rank else 40), qb=float(pos == "QB"), rb=float(pos == "RB"), wr=float(pos == "WR"),
                             power=float(rc["conf"] in POWER or c["team"] == "Notre Dame"), share=0.0, pts=0))
    kept = []
    for pos, n in POOL_N.items():
        grp = sorted([r for r in rows if r["pos"] == pos], key=lambda r: -r["ppg"])[:n]
        v = np.array([r["ppg"] for r in grp]) if grp else np.array([0.0])
        for r in grp:
            r["pos_z"] = (r["ppg"] - v.mean()) / (v.std() + 1e-9)
        kept += grp
    rows = kept
    for f in ("ppg", "ppa"):
        v = np.array([r[f] for r in rows]); m, sd_ = v.mean(), v.std() + 1e-9
        for r in rows:
            r[f + "_z"] = (r[f] - m) / sd_
    if year in VOTES:
        tot = sum(v[3] for v in VOTES[year]); hit = 0
        for name, school, pos, pts in VOTES[year]:
            k = key(name)
            for r in rows:
                if key(r["name"]) == k and normalize_name(r["team"]) == normalize_name(school):
                    r["share"] = pts / tot; r["pts"] = pts; hit += 1; break
        rows.append(dict(_hit=hit, _n=len(VOTES[year])))
    return rows


def X(rows, mu=None, sd=None):
    A = np.array([[r[f] for f in FEATS] for r in rows], float)
    if mu is None:
        mu, sd = A.mean(0), A.std(0) + 1e-9
    return (A - mu) / sd, mu, sd


def fit(seasons, l2=0.02, iters=6000, lr=0.1):
    data = []
    for y in seasons:
        rows = [r for r in pool(y) if "_hit" not in r]
        data.append((rows, np.array([r["share"] for r in rows])))
    allrows = [r for rows, _ in data for r in rows]
    _, mu, sd = X(allrows)
    Xs = [(X(rows, mu, sd)[0], sh) for rows, sh in data]
    w = np.zeros(len(FEATS))
    for _ in range(iters):
        g = np.zeros_like(w)
        for A, sh in Xs:
            z = A @ w; z -= z.max(); p = np.exp(z); p /= p.sum()
            g += A.T @ (sh - p)
        g -= l2 * w
        w += lr * g
    return w, mu, sd


def score(rows, w, mu, sd):
    A, _, _ = X(rows, mu, sd); z = A @ w; z -= z.max(); p = np.exp(z); return p / p.sum()


def evaluate(seasons, w, mu, sd, label, out):
    lines = []
    tot_ll = 0.0; wr = []; top3 = 0; wll = []
    for y in seasons:
        rows = [r for r in pool(y) if "_hit" not in r]
        sh = np.array([r["share"] for r in rows])
        if label == "vote model":
            p = score(rows, w, mu, sd)
        elif label == "production board":
            v = np.array([r["ppg"] * (0.5 + 0.5 * min(max((r["wins"] - 6) / 6, 0), 1)) for r in rows]); p = np.exp(8 * v / v.max()); p /= p.sum()
        else:
            v = np.array([r["ppg"] for r in rows]); p = np.exp(8 * v / v.max()); p /= p.sum()
        order = np.argsort(-p); win = int(np.argmax(sh))
        rank = int(np.where(order == win)[0][0]) + 1
        wr.append(rank); wll.append(-np.log(max(p[win], 1e-9)))
        tot_ll += float(np.sum(sh * np.log(np.clip(p, 1e-9, 1))))
        actual3 = set(np.argsort(-sh)[:3]); top3 += len(actual3 & set(order[:3]))
        lines.append(f"{y}: winner {rows[win]['name']} ranked {rank}, P {100 * p[win]:.0f}% · model top 3: " + ", ".join(f"{rows[i]['name']} {100 * p[i]:.0f}%" for i in order[:3]))
    out.append(f"| {label} | {np.mean(wr):.1f} | {sum(r == 1 for r in wr)} of {len(wr)} | {top3} of {3 * len(wr)} | {np.mean(wll):.2f} | {-tot_ll / len(wr):.2f} |")
    return lines


def main():
    out = []; P = out.append
    P("# Heisman vote study (INTERNAL, Tue Oct 6 2026)\n")
    cov = []
    for y in range(2014, 2026):
        h = [r for r in pool(y) if "_hit" in r][0]; cov.append(f"{y} {h['_hit']}/{h['_n']}")
    P("Vote-getters matched to the CFBD pool (the season's top 50 QB/RB/WR/TE by points a game, 60+ plays): " + " · ".join(cov) + ". Unmatched = defensive/two-way players or name mismatches; their points leave the denominator.\n")
    w, mu, sd = fit(FIT)
    P("## Fit 2014-21, test 2022-25\n\n| ranking | winner's avg rank | winner ranked 1st | top-3 overlap | −log P(winner) | share log loss |\n|---|--:|--:|--:|--:|--:|")
    det = {}
    for lab in ("vote model", "production board", "points a game"):
        det[lab] = evaluate(TEST, w, mu, sd, lab, out)
    P("\nVote model, season by season (test):\n")
    for l in det["vote model"]:
        P("- " + l)
    P("\nProduction board, season by season (test):\n")
    for l in det["production board"]:
        P("- " + l)
    P("\n## What the ballot rewards (standardized weights, fit 2014-21)\n\n| feature | weight |\n|---|--:|")
    for f, b in sorted(zip(FEATS, w), key=lambda x: -abs(x[1])):
        P(f"| {f} | {b:+.2f} |")
    # refit on everything for 2026
    w2, mu2, sd2 = fit(list(FIT) + list(TEST))
    P("\n## Refit on 2014-25 (for the 2026 board)\n\n| feature | weight |\n|---|--:|")
    for f, b in sorted(zip(FEATS, w2), key=lambda x: -abs(x[1])):
        P(f"| {f} | {b:+.2f} |")
    # leave-one-season-out: the honest scorecard, and the temperature that calibrates P(win)
    loso = []
    for y in range(2014, 2026):
        wl, ml, sl = fit([s_ for s_ in range(2014, 2026) if s_ != y])
        rows = [r for r in pool(y) if "_hit" not in r]; sh = np.array([r["share"] for r in rows])
        A, _, _ = X(rows, ml, sl); z = A @ wl; win = int(np.argmax(sh))
        loso.append((y, rows, z, win, sh))

    def nll(tau):
        t = 0.0
        for y, rows, z, win, sh in loso:
            zz = z / tau; zz -= zz.max(); p = np.exp(zz); p /= p.sum(); t -= np.log(max(p[win], 1e-9))
        return t / len(loso)
    taus = np.arange(0.5, 6.01, 0.25); TAU = float(taus[int(np.argmin([nll(t) for t in taus]))])
    P(f"\n## Leave-one-season-out, 2014-25 (fit on the other eleven, score the held-out year); probabilities calibrated with temperature {TAU:g}\n")
    P("| year | winner | model rank | P(win) | model's favorite | its P |\n|---|---|--:|--:|---|--:|")
    ranks = []; top3 = 0
    for y, rows, z, win, sh in loso:
        zz = z / TAU; zz -= zz.max(); p = np.exp(zz); p /= p.sum(); order = np.argsort(-p)
        rank = int(np.where(order == win)[0][0]) + 1; ranks.append(rank); top3 += len(set(np.argsort(-sh)[:3]) & set(order[:3]))
        P(f"| {y} | {rows[win]['name']} | {rank} | {100 * p[win]:.0f}% | {rows[order[0]]['name']} | {100 * p[order[0]]:.0f}% |")
    P(f"\nWinner ranked 1st in {sum(r == 1 for r in ranks)} of 12 seasons, top 3 in {sum(r <= 3 for r in ranks)}; average rank {np.mean(ranks):.1f}; "
      f"top-3 overlap {top3} of 36; held-out -log P(winner) {nll(TAU):.2f} (a coin flip among the top three would be {np.log(3):.2f}).")
    # 2026
    from hot_seat_heisman import season_sim, MARKET, MARKET_DATE
    sim = season_sim()
    rows = [r for r in pool(NOW, sim) if "_hit" not in r]
    A, _, _ = X(rows, mu2, sd2); z = A @ w2 / TAU; z -= z.max(); p = np.exp(z); p /= p.sum()
    order = np.argsort(-p)
    P(f"\n## 2026 as of today — P(win the vote), projected wins from the Season Sim standing in for final wins, current AP rank\n")
    P(f"| # | player | team | pos | pts/game | proj wins | AP | P(win) | DraftKings {MARKET_DATE} |\n|--:|---|---|---|--:|--:|--:|--:|--:|")
    board = []
    for i in order[:15]:
        r = rows[i]; mk = MARKET.get(r["name"]); mp = 100 / (1 + mk / 100) if mk else None
        ap = int(round(np.exp(r["log_rank"]))) if r["log_rank"] < np.log(39) else None
        P(f"| {len(board) + 1} | {r['name']} | {r['team']} | {r['pos']} | {r['ppg']:.1f} | {r['wins']:.1f} | {ap or '-'} | {100 * p[i]:.1f}% | {('+' + str(mk) + f' ({mp:.0f}%)') if mk else '-'} |")
        board.append(dict(rank=len(board) + 1, name=r["name"], team=r["team"], pos=r["pos"], ppg=round(r["ppg"], 1), proj_wins=round(r["wins"], 1), ap=ap, p_win=round(float(p[i]), 4), market=mk))
    P("\nCaveats for the board: the backtest features are END-of-season; today's board uses to-date production and projected wins, which is a forecast, not the fitted quantity. "
      "Five games of PPA is a small sample; the AP rank moves weekly; defensive players are not in the pool.")
    text = "\n".join(out)
    (HERE / "internal" / "HEISMAN_STUDY_2026.md").write_text(text, encoding="utf-8")
    (HERE / "internal" / "heisman_vote_board_week6.json").write_text(json.dumps(dict(as_of=str(np.datetime64('today')), weights=dict(zip(FEATS, map(float, w2))), temperature=TAU, board=board), indent=1), encoding="utf-8")
    sys.stdout.reconfigure(encoding='utf-8', errors='replace'); print(text)


if __name__ == "__main__":
    main()
