"""Full playoff simulator (Phase 5, built 2026-09-22) - replaces playoff_sim_rough.py.

    python playoff_sim.py --fit                  # fit + validate the committee model on 2014-2025 (internal)
    python playoff_sim.py --week 4               # Monte Carlo from the on-air rating -> internal/playoff_sim_week4.json
    python playoff_sim.py --week 4 --sims 20000 --team Miami     # one team's paths in detail

WHAT IT DOES
  1. Season: every remaining regular-season game is drawn from the on-air
     machine (rating gap + 2.5 home field, residual sd 15.9), each team's true
     rating redrawn per sim (TEAM_SD) so early-season uncertainty is honest.
     Completed games are fixed. FCS games are wins for the FBS side with
     probability FCS_WIN.
  2. Conference championships: the top two by conference record play at a
     neutral site (tiebreaks: head-to-head, then the machine rating - a stand-in
     for each league's full tiebreaker text). Every FBS conference holds one;
     independents cannot win a title.
  3. Committee: a pairwise model fit to the 2014-2025 selection-Sunday
     committee rankings (CFBD /rankings, "Playoff Committee Rankings"): the
     probability the committee ranks i above j is a logistic in the
     differences of rating, losses, strength of record, quality wins and the
     conference-champion flag, plus head-to-head. It is fit ONCE by --fit and
     frozen in playoff_committee_model.json; the sim ranks every simulated
     season with it and applies head-to-head as an adjacent-swap in the top
     16. --fit prints how well it reproduces each season's top 12 and how it
     treats two- and three-loss teams.
  4. Field: FORMAT (12 teams, the 5 highest-ranked conference champions
     auto-qualify, 7 at-large, straight seeding, byes to seeds 1-4). Bracket:
     first round at the higher seed, then neutral, from the same margin model.
  Per team: playoff odds, first-round bye odds, conference title odds,
  national title odds, expected wins, and the most likely path into the field
  (modal record + champion / at-large among its playoff seasons).

INTERNAL until Lucas says otherwise (the show's Top 25 playoff column is a
separate switch). The rating is the ON-AIR machine; shadow ratings are not
used here because none beat it (internal/EFFICIENCY_2026.md).
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name as norm  # noqa: E402
import inseason_ratings as ir  # noqa: E402

DATA = HERE / "fpi-decomposition" / "data"
MODEL_JSON = HERE / "playoff_committee_model.json"
SD, HFA, TEAM_SD, FCS_WIN, BASE = ir.SIGMA_INSEASON, ir.HFA, 3.5, 0.97, 20.0
FORMAT = dict(teams=12, auto_champs=5, byes=4)
FEATURES = ["rating", "losses", "sor", "qwins", "champ"]
TOP_RATED = 25      # "quality win" = a win over a team rated in the machine's top 25 at that point


def _pick(g, *names):
    for k in names:
        if g.get(k) is not None:
            return g[k]
    return None


# ---------------- season data ----------------

def load_season(season: int):
    """(prior, games) - games: all regular-season games with an FBS side, normalized
    names, conference fields, completed results; CCGs flagged from the notes."""
    from backtest import load_prior
    prior = load_prior(season)
    raw = json.loads((DATA / f"games_seasonType-regular_year-{season}.json").read_text(encoding="utf-8"))
    games = []
    for g in raw:
        home, away = _pick(g, "homeTeam", "home_team"), _pick(g, "awayTeam", "away_team")
        if not home or not away:
            continue
        h, a = norm(home), norm(away)
        hc, ac = _pick(g, "homeClassification", "home_classification"), _pick(g, "awayClassification", "away_classification")
        if hc != "fbs" and ac != "fbs":
            continue
        hp, ap = _pick(g, "homePoints", "home_points"), _pick(g, "awayPoints", "away_points")
        notes = (g.get("notes") or "")
        games.append(dict(id=g.get("id"), week=int(_pick(g, "week") or 0), home=h, away=a, home_raw=home, away_raw=away,
                          neutral=bool(_pick(g, "neutralSite", "neutral_site")), conf_game=bool(_pick(g, "conferenceGame", "conference_game")),
                          home_conf=_pick(g, "homeConference", "home_conference"), away_conf=_pick(g, "awayConference", "away_conference"),
                          home_fbs=(hc == "fbs"), away_fbs=(ac == "fbs"),
                          completed=bool(_pick(g, "completed")) and hp is not None and ap is not None,
                          margin=(float(hp - ap) if hp is not None and ap is not None else None),
                          ccg=False))
    games.sort(key=lambda g: (g["week"], g["id"] or 0))
    # CFBD does not label FBS title games: a conference's CCG is the ONE game
    # between two of its members in the last week that conference played
    # (leagues without a title game have several games that week). Only for a
    # finished season - the current season's CCGs are not scheduled yet and
    # the sim creates them.
    if games and all(g["completed"] for g in games if g["home_fbs"] and g["away_fbs"]):
        last = collections.defaultdict(int)
        for g in games:
            if g["conf_game"] and g["home_conf"] == g["away_conf"] and g["home_conf"]:
                last[g["home_conf"]] = max(last[g["home_conf"]], g["week"])
        cand = collections.defaultdict(list)
        for g in games:
            if g["conf_game"] and g["home_conf"] == g["away_conf"] and g["home_conf"] and g["week"] == last[g["home_conf"]]:
                cand[g["home_conf"]].append(g)
        for c, gs in cand.items():
            if len(gs) == 1:
                gs[0]["ccg"] = True
    return prior, games


def machine_rating(prior, games, through_week=None, cap_mode="residual"):
    rows = [dict(home=g["home"], away=g["away"], neutral=g["neutral"], margin=g["margin"])
            for g in games if g["completed"] and g["home"] in prior and g["away"] in prior
            and (through_week is None or g["week"] <= through_week)]
    return ir.ridge_update(prior, rows, cap_mode=cap_mode)


def phi(x):
    return 0.5 * (1 + math.erf(x / (SD * math.sqrt(2))))


def team_features(teams, rating, games, champions: set, through_week=None):
    """Deterministic (played-games) features per team: wins, losses, sor, qwins, champ, h2h dict."""
    R = rating
    top = set(sorted(R, key=lambda t: -R[t])[:TOP_RATED])
    f = {t: dict(rating=R[t], wins=0, losses=0, sor=0.0, qwins=0, champ=float(t in champions)) for t in teams}
    h2h = collections.defaultdict(dict)
    for g in games:
        if not g["completed"] or (through_week is not None and g["week"] > through_week):
            continue
        h, a = g["home"], g["away"]
        hw = g["margin"] > 0
        hf = 0.0 if g["neutral"] else HFA
        ra = R.get(a, R.get(h, BASE) - 29 if not g["away_fbs"] else BASE)
        rh = R.get(h, R.get(a, BASE) - 29 if not g["home_fbs"] else BASE)
        if h in f:
            f[h]["wins" if hw else "losses"] += 1
            f[h]["sor"] += (1 if hw else 0) - phi(BASE - ra + hf)
            f[h]["qwins"] += int(hw and a in top)
            h2h[h][a] = 1 if hw else -1
        if a in f:
            f[a]["wins" if not hw else "losses"] += 1
            f[a]["sor"] += (0 if hw else 1) - phi(BASE - rh - hf)
            f[a]["qwins"] += int((not hw) and h in top)
            h2h[a][h] = -1 if hw else 1
    return f, h2h


# ---------------- committee model ----------------

def committee_poll(season: int):
    """{team: rank} from the LAST regular-season 'Playoff Committee Rankings' poll (selection Sunday)."""
    path = DATA / f"rankings_year-{season}.json"
    if not path.exists():
        return {}, None
    weeks = [w for w in json.loads(path.read_text(encoding="utf-8")) if w.get("seasonType") == "regular"]
    best, bw = {}, None
    for w in sorted(weeks, key=lambda w: w.get("week") or 0):
        for p in w.get("polls", []):
            if "committee" in (p.get("poll") or "").lower() or "playoff" in (p.get("poll") or "").lower():
                best = {norm(r.get("school") or r.get("team")): int(r["rank"]) for r in p.get("ranks", []) if r.get("rank")}
                bw = w.get("week")
    return best, bw


def season_champions(games, prior):
    """Conference champions from the played season: the CCG winner, else the best
    conference record (rating tiebreak)."""
    champs, by_conf = set(), collections.defaultdict(list)
    ccg_conf = set()
    for g in games:
        if g["ccg"] and g["completed"] and g["home_conf"] == g["away_conf"] and g["home_conf"]:
            champs.add(g["home"] if g["margin"] > 0 else g["away"]); ccg_conf.add(g["home_conf"])
    rec = collections.defaultdict(lambda: [0, 0])
    conf_of = {}
    for g in games:
        if g["home_fbs"]:
            conf_of[g["home"]] = g["home_conf"]
        if g["away_fbs"]:
            conf_of[g["away"]] = g["away_conf"]
        if g["completed"] and g["conf_game"] and not g["ccg"]:
            hw = g["margin"] > 0
            rec[g["home"]][0 if hw else 1] += 1; rec[g["away"]][1 if hw else 0] += 1
    for t, c in conf_of.items():
        if c and "independent" not in c.lower():
            by_conf[c].append(t)
    for c, ts in by_conf.items():
        if c in ccg_conf:
            continue
        best = max(ts, key=lambda t: (rec[t][0] / max(sum(rec[t]), 1), prior.get(t, -99)))
        champs.add(best)
    return champs


def fit_committee(seasons=range(2014, 2026)):
    """Pairwise logistic fit on selection-Sunday rankings. Returns weights + validation."""
    pairs, val = [], []
    for s in seasons:
        poll, wk = committee_poll(s)
        if not poll:
            print(f"{s}: no committee poll cached"); continue
        prior, games = load_season(s)
        R = machine_rating(prior, games)
        teams = [t for t in prior]
        champs = season_champions(games, prior)
        f, h2h = team_features(teams, R, games, champs)
        ranked = [t for t in sorted(poll, key=poll.get) if t in f]
        # pairs: every ranked pair, plus each ranked team vs unranked FBS teams with <= 3 losses (they were below)
        unr = [t for t in teams if t not in poll and f[t]["losses"] <= 3 and f[t]["wins"] >= 7]
        for i, a in enumerate(ranked):
            for b in ranked[i + 1:] + unr:
                d = [f[a][k] - f[b][k] for k in FEATURES] + [h2h[a].get(b, 0)]
                pairs.append((d, 1.0))
                pairs.append(([-x for x in d], 0.0))
        val.append(dict(season=s, poll=poll, feats=f, h2h=h2h, week=wk))
    X = np.array([p[0] for p in pairs]); y = np.array([p[1] for p in pairs])
    # standardize, logistic regression by Newton's method, small ridge
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Z = (X - mu) / sd
    w = np.zeros(Z.shape[1])
    for _ in range(50):
        p = 1 / (1 + np.exp(-(Z @ w)))
        g = Z.T @ (p - y) + 1e-3 * w
        H = (Z * (p * (1 - p))[:, None]).T @ Z + 1e-3 * np.eye(len(w))
        w -= np.linalg.solve(H, g)
    coef = w / sd            # weights on raw differences (mu cancels in differences)
    model = dict(features=FEATURES + ["h2h"], coef=[float(c) for c in coef], seasons=[v["season"] for v in val],
                 n_pairs=int(len(pairs) // 2), fit=dt.date.today().isoformat())
    # validation per season
    rep = []
    for v in val:
        f, poll = v["feats"], v["poll"]
        score = {t: sum(c * f[t][k] for c, k in zip(coef, FEATURES)) for t in f}
        order = rank_with_h2h(score, v["h2h"])
        top12 = order[:12]
        actual12 = [t for t in sorted(poll, key=poll.get)[:12]]
        two = [(t, poll[t], order.index(t) + 1) for t in actual12 if f[t]["losses"] == 2]
        three = [(t, poll[t], order.index(t) + 1) for t in actual12 if f[t]["losses"] >= 3]
        rep.append(dict(season=v["season"], top12_overlap=len(set(top12) & set(actual12)),
                        top4_overlap=len(set(order[:4]) & set(actual12[:4])),
                        mean_abs_rank_err_top12=float(np.mean([abs(order.index(t) + 1 - poll[t]) for t in actual12])),
                        two_loss=[dict(team=t, committee=r, model=m) for t, r, m in two],
                        three_loss=[dict(team=t, committee=r, model=m) for t, r, m in three],
                        model_top12=top12, committee_top12=actual12))
    model["validation"] = rep
    return model


def rank_with_h2h(score: dict, h2h, window=16):
    order = sorted(score, key=lambda t: -score[t])
    # adjacent swap: a team directly below one it beat head-to-head with no worse a record moves up
    changed = True
    while changed:
        changed = False
        for i in range(min(window, len(order)) - 1):
            a, b = order[i], order[i + 1]
            if h2h.get(b, {}).get(a, 0) == 1 and score[a] - score[b] < abs(score[a]) * 0.02 + 0.3:
                order[i], order[i + 1] = b, a; changed = True
    return order


def load_model():
    return json.loads(MODEL_JSON.read_text(encoding="utf-8")) if MODEL_JSON.exists() else None


# ---------------- Monte Carlo ----------------

def simulate(week: int, sims: int = 10000, seed: int = 2026, season: int = 2026, focus: str | None = None):
    rng = np.random.default_rng(seed)
    model = load_model()
    if not model:
        sys.exit("run --fit first (playoff_committee_model.json)")
    coef = dict(zip(model["features"], model["coef"]))
    prior, games = load_season(season)
    if season == 2026:
        R = {t["team"]: t["cur"] for t in json.loads((HERE / "ratings_current_2026.json").read_text(encoding="utf-8"))["teams"]}
    else:
        R = machine_rating(prior, games, through_week=week - 1)
    teams = sorted(R); ix = {t: i for i, t in enumerate(teams)}; T = len(teams); S = sims
    conf_of = {}
    for g in games:
        if g["home_fbs"] and g["home"] in ix:
            conf_of[g["home"]] = g["home_conf"]
        if g["away_fbs"] and g["away"] in ix:
            conf_of[g["away"]] = g["away_conf"]
    top = set(sorted(R, key=lambda t: -R[t])[:TOP_RATED])
    Rv = np.array([R[t] for t in teams])
    true = Rv[None, :] + rng.normal(0, TEAM_SD, (S, T))
    wins = np.zeros((S, T)); losses = np.zeros((S, T)); sor = np.zeros((S, T)); qw = np.zeros((S, T))
    cw = np.zeros((S, T)); cl = np.zeros((S, T))
    h2h = np.zeros((S, T, T), dtype=np.int8) if T <= 160 else None
    for g in games:
        if g["ccg"] and not g["completed"]:
            continue
        h, a = g["home"], g["away"]
        hi, ai = ix.get(h), ix.get(a)
        if hi is None and ai is None:
            continue
        hf = 0.0 if g["neutral"] else HFA
        ra = Rv[ai] if ai is not None else Rv[hi] - 29
        rh = Rv[hi] if hi is not None else Rv[ai] - 29
        if g["completed"] and (g["week"] < week or season != 2026):
            hw = np.full(S, g["margin"] > 0)
        elif hi is None or ai is None:       # FCS game still to play
            hw = rng.random(S) < (FCS_WIN if hi is not None else 1 - FCS_WIN)
        else:
            hw = (true[:, hi] - true[:, ai] + hf + rng.normal(0, SD, S)) > 0
        if hi is not None:
            wins[:, hi] += hw; losses[:, hi] += ~hw; sor[:, hi] += hw - phi(BASE - ra + hf); qw[:, hi] += hw * (a in top)
            if g["conf_game"]:
                cw[:, hi] += hw; cl[:, hi] += ~hw
        if ai is not None:
            wins[:, ai] += ~hw; losses[:, ai] += hw; sor[:, ai] += (~hw) - phi(BASE - rh - hf); qw[:, ai] += (~hw) * (h in top)
            if g["conf_game"]:
                cw[:, ai] += ~hw; cl[:, ai] += hw
        if h2h is not None and hi is not None and ai is not None:
            h2h[:, hi, ai] = np.where(hw, 1, -1); h2h[:, ai, hi] = -h2h[:, hi, ai]
    # conference championships
    confs = collections.defaultdict(list)
    for t, c in conf_of.items():
        if c and "independent" not in c.lower():
            confs[c].append(ix[t])
    champ = np.zeros((S, T), bool)
    for c, members in confs.items():
        m = np.array(members)
        pct = cw[:, m] / np.maximum(cw[:, m] + cl[:, m], 1)
        key = pct + 1e-4 * true[:, m] / 100.0              # rating as the tiebreak stand-in
        order = np.argsort(-key, axis=1)
        one, two = m[order[:, 0]], m[order[:, 1]]
        if h2h is not None:   # head-to-head between the top two flips the seeding when records tie
            tie = np.isclose(pct[np.arange(S), order[:, 0]], pct[np.arange(S), order[:, 1]])
            beat = h2h[np.arange(S), two, one] == 1
            flip = tie & beat
            one, two = np.where(flip, two, one), np.where(flip, one, two)
        hw = (true[np.arange(S), one] - true[np.arange(S), two] + rng.normal(0, SD, S)) > 0
        winner = np.where(hw, one, two); loser = np.where(hw, two, one)
        champ[np.arange(S), winner] = True
        for arr, idx in ((wins, winner), (losses, loser)):
            arr[np.arange(S), idx] += 1
        ra_ = true[np.arange(S), two]; rh_ = true[np.arange(S), one]
        sor[np.arange(S), one] += hw - np.array([phi(BASE - x) for x in Rv[two]])
        sor[np.arange(S), two] += (~hw) - np.array([phi(BASE - x) for x in Rv[one]])
    # committee score and ranking
    score = (coef["rating"] * true + coef["losses"] * losses + coef["sor"] * sor + coef["qwins"] * qw + coef["champ"] * champ)
    order = np.argsort(-score, axis=1)
    F, N_AUTO, BYES = FORMAT["teams"], FORMAT["auto_champs"], FORMAT["byes"]
    field = np.zeros((S, T), bool); seed_of = np.full((S, T), 99)
    titles = np.zeros(T)
    for s in range(S):
        o = list(order[s])
        if h2h is not None:   # adjacent head-to-head swap in the top 16
            for _ in range(2):
                for i in range(min(16, T) - 1):
                    a, b = o[i], o[i + 1]
                    if h2h[s, b, a] == 1 and losses[s, b] <= losses[s, a] and score[s, a] - score[s, b] < 0.3:
                        o[i], o[i + 1] = b, a
        champs_ranked = [t for t in o if champ[s, t]][:N_AUTO]
        chosen = set(champs_ranked)
        for t in o:
            if len(chosen) >= F:
                break
            chosen.add(t)
        seeds = [t for t in o if t in chosen][:F]
        for k, t in enumerate(seeds):
            field[s, t] = True; seed_of[s, t] = k + 1
        # bracket: 5-12 first round at the higher seed, then neutral
        def game(x, y, home):
            return x if (true[s, x] - true[s, y] + (HFA if home else 0) + rng.normal(0, SD)) > 0 else y
        w = {i: seeds[i - 1] for i in range(1, F + 1)}
        r1 = {5: game(w[5], w[12], True), 6: game(w[6], w[11], True), 7: game(w[7], w[10], True), 8: game(w[8], w[9], True)}
        q = [game(w[1], r1[8], False), game(w[2], r1[7], False), game(w[3], r1[6], False), game(w[4], r1[5], False)]
        semi = [game(q[0], q[3], False), game(q[1], q[2], False)]
        titles[game(semi[0], semi[1], False)] += 1
    out = []
    for t in teams:
        i = ix[t]
        inf = field[:, i]
        path = None
        if inf.any():
            combos = collections.Counter((int(wins[s, i]), int(losses[s, i]), bool(champ[s, i])) for s in np.flatnonzero(inf))
            (w_, l_, c_), n = combos.most_common(1)[0]
            path = dict(record=f"{w_}-{l_}", via=("wins the " + str(conf_of.get(t)) if c_ else "at-large"), share=round(n / inf.sum(), 3))
        out.append(dict(team=t, rating=round(R[t], 1), conf=conf_of.get(t), playoff=round(float(inf.mean()), 4),
                        bye=round(float((seed_of[:, i] <= BYES).mean()), 4), conf_title=round(float(champ[:, i].mean()), 4),
                        national_title=round(float(titles[i] / S), 4), exp_wins=round(float(wins[:, i].mean()), 2),
                        exp_losses=round(float(losses[:, i].mean()), 2),
                        avg_seed=(round(float(seed_of[inf, i].mean()), 2) if inf.any() else None), path=path))
    out.sort(key=lambda r: (-r["playoff"], -r["rating"]))
    res = dict(week=week, season=season, sims=S, as_of=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
               status="INTERNAL - not on the show until Lucas switches the Top 25 playoff column on",
               params=dict(sd=SD, hfa=HFA, team_sd=TEAM_SD, fcs_win=FCS_WIN, format=FORMAT, committee=model["coef"],
                           committee_features=model["features"]), teams=out)
    if focus:
        i = ix[norm(focus)]
        inf = field[:, i]
        combos = collections.Counter((int(wins[s, i]), int(losses[s, i]), bool(champ[s, i])) for s in range(S))
        res["focus"] = dict(team=focus, by_record=[dict(record=f"{w}-{l}", champ=c, n=n,
                                                        playoff=round(float(field[[s for s in range(S) if (int(wins[s, i]), int(losses[s, i]), bool(champ[s, i])) == (w, l, c)], i].mean()), 3))
                                                   for (w, l, c), n in combos.most_common(12)])
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fit", action="store_true")
    ap.add_argument("--week", type=int)
    ap.add_argument("--sims", type=int, default=10000)
    ap.add_argument("--team")
    ap.add_argument("--season", type=int, default=2026)
    a = ap.parse_args()
    if a.fit:
        m = fit_committee()
        MODEL_JSON.write_text(json.dumps(m, indent=1), encoding="utf-8")
        print("committee model:", {k: round(v, 4) for k, v in zip(m["features"], m["coef"])}, f"({m['n_pairs']} pairs, seasons {m['seasons'][0]}-{m['seasons'][-1]})")
        print(f"{'season':>6} {'top12 hit':>9} {'top4 hit':>8} {'rank err':>8}  two-loss teams (committee -> model) | three-loss")
        for v in m["validation"]:
            two = ", ".join(f"{x['team']} {x['committee']}->{x['model']}" for x in v["two_loss"]) or "-"
            three = ", ".join(f"{x['team']} {x['committee']}->{x['model']}" for x in v["three_loss"]) or "-"
            print(f"{v['season']:>6} {v['top12_overlap']:>6}/12 {v['top4_overlap']:>5}/4 {v['mean_abs_rank_err_top12']:8.2f}  {two} | {three}")
        print(f"wrote {MODEL_JSON.name}")
    if a.week:
        res = simulate(a.week, a.sims, focus=a.team, season=a.season)
        (HERE / "internal").mkdir(exist_ok=True)
        out = HERE / "internal" / f"playoff_sim_week{a.week}.json"
        out.write_text(json.dumps(res, indent=1), encoding="utf-8")
        print(f"playoff sim before week {a.week}: {a.sims} sims - INTERNAL")
        print(f"{'':3} {'team':22} {'rating':>6} {'playoff':>8} {'bye':>6} {'conf':>6} {'title':>6} {'exp W-L':>8}  most likely path")
        for k, r in enumerate(res["teams"][:30], 1):
            p = r["path"]
            print(f"{k:2d}. {r['team']:22} {r['rating']:6.1f} {100 * r['playoff']:7.1f}% {100 * r['bye']:5.1f}% {100 * r['conf_title']:5.1f}% {100 * r['national_title']:5.1f}% {r['exp_wins']:4.1f}-{r['exp_losses']:<3.1f}  "
                  + (f"{p['record']} {p['via']} ({100 * p['share']:.0f}% of its playoff seasons)" if p else "-"))
        if "focus" in res:
            print(f"\n{res['focus']['team']} by record:")
            for x in res["focus"]["by_record"]:
                print(f"  {x['record']:6s} {'champ' if x['champ'] else '     '}  {x['n']:5d} sims  playoff {100 * x['playoff']:.0f}%")
        print(f"wrote {out.relative_to(HERE)}")


if __name__ == "__main__":
    main()


def write_playoff_sheet(book: Path, week: int | None = None) -> None:
    """'Playoff Sim' sheet in the workbook from the latest internal/playoff_sim_week*.json."""
    from openpyxl import load_workbook
    from openpyxl.styles import Font, PatternFill
    files = sorted((HERE / "internal").glob("playoff_sim_week*.json"), key=lambda p: int(p.stem.rsplit("week", 1)[1]))
    if week is not None:
        files = [f for f in files if f.stem.endswith(f"week{week}")]
    if not files:
        print("playoff sheet: no playoff_sim_week*.json yet"); return
    d = json.loads(files[-1].read_text(encoding="utf-8"))
    wb = load_workbook(book, keep_vba=True)
    if "Playoff Sim" in wb.sheetnames:
        del wb["Playoff Sim"]
    ws = wb.create_sheet("Playoff Sim")
    ws["A1"] = f"PLAYOFF SIM - before week {d['week']} - {d['sims']:,} seasons from the on-air rating"
    ws["A1"].font = Font(bold=True, size=13)
    ws["A2"] = ("12-team field: 5 highest-ranked conference champions + 7 at-large, straight seeding, byes 1-4. Committee = "
                "a model fit to the 2014-2025 selection-Sunday rankings (rating, losses, strength of record, quality wins, "
                "champion, head-to-head). Internal until the show's playoff column is switched on.")
    hdr = ["Team", "Conf", "Rating", "Playoff %", "Bye %", "Conf title %", "National title %", "Exp W", "Exp L", "Avg seed",
           "Most likely path", "Path share"]
    for j, h in enumerate(hdr, 1):
        c = ws.cell(row=4, column=j, value=h); c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F3864")
    for i, t in enumerate(d["teams"], 5):
        p = t.get("path") or {}
        vals = [t["team"].title(), t.get("conf"), t["rating"], round(100 * t["playoff"], 1), round(100 * t["bye"], 1),
                round(100 * t["conf_title"], 1), round(100 * t["national_title"], 1), t["exp_wins"], t["exp_losses"], t.get("avg_seed"),
                (f"{p.get('record')} {p.get('via')}" if p else ""), (round(100 * p["share"]) if p else None)]
        for j, v in enumerate(vals, 1):
            ws.cell(row=i, column=j, value=v)
    ws.freeze_panes = "B5"
    ws.auto_filter.ref = f"A4:L{4 + len(d['teams'])}"
    for col, w in zip("ABCDEFGHIJKL", (22, 18, 9, 10, 8, 12, 15, 8, 8, 9, 34, 10)):
        ws.column_dimensions[col].width = w
    wb.save(book)
    print(f"playoff sheet written: {len(d['teams'])} teams, before week {d['week']}")
