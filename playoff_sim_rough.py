"""Rough 12-team playoff Monte Carlo from the current machine ratings. INTERNAL.
Season: every remaining game ~ Normal(rating gap + HFA, 15.9), with each team's
true rating redrawn per sim (sd 4: three weeks of data). Conference title game =
top two by league record. Committee proxy = strength of record (wins above what
a rating-20 team would expect vs the same schedule) + a small 'eye test' term.
Field = 5 best champions + 7 at-large; straight seeding, top 4 byes."""
import sys, os, io, json, contextlib, collections, math
import numpy as np
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd()); sys.path.insert(0, "fpi-decomposition")
from refresh_all import load_env_key
import build_conference_book as b
from name_mapping import normalize_name as norm
load_env_key()
rng = np.random.default_rng(2026)
S, SD, HFA, TEAM_SD, BASE, FCS_MARGIN = int(os.environ.get("SIMS", 10000)), 15.9, 2.5, 4.0, 20.0, 29.0
EYE = 0.05   # wins per rating point in the committee score

R = {t["team"]: t["cur"] for t in json.load(open("ratings_current_2026.json"))["teams"]}
teams = sorted(R); ix = {t: i for i, t in enumerate(teams)}; T = len(teams)
with contextlib.redirect_stdout(io.StringIO()):
    games = b.fetch_games(False, {})
disp, conf = {}, {}
for g in games:
    for side in ("home", "away"):
        n = norm(g[side])
        if n in ix:
            disp[n] = g[side]; conf[n] = g[f"{side}_conf"]
Phi = lambda x: 0.5 * (1 + math.erf(x / (SD * math.sqrt(2))))

rating = np.array([R[t] for t in teams])[None, :] + rng.normal(0, TEAM_SD, (S, T))
wins = np.zeros((S, T)); losses = np.zeros((S, T)); cw = np.zeros((S, T)); cl = np.zeros((S, T)); sor = np.zeros((S, T))
for g in games:
    h, a = norm(g["home"]), norm(g["away"])
    hi, ai = ix.get(h), ix.get(a)
    if hi is None and ai is None:
        continue
    hf = 0.0 if g["neutral"] else HFA
    # what a BASE-rated team would expect in each seat (point ratings)
    exp_h = Phi(BASE - (R[a] if ai is not None else BASE - FCS_MARGIN) + hf)
    exp_a = Phi(BASE - (R[h] if hi is not None else BASE - FCS_MARGIN) - hf)
    if g["completed"] and g["home_pts"] is not None:
        hw = np.full(S, g["home_pts"] > g["away_pts"])
    else:
        rh = rating[:, hi] if hi is not None else rating[:, ai] - FCS_MARGIN
        ra = rating[:, ai] if ai is not None else rating[:, hi] - FCS_MARGIN
        hw = (rh - ra + hf + rng.normal(0, SD, S)) > 0
    for i, won, e in ((hi, hw, exp_h), (ai, ~hw, exp_a)):
        if i is None:
            continue
        wins[:, i] += won; losses[:, i] += ~won; sor[:, i] += won - e
        if g["conf_game"]:
            cw[:, i] += won; cl[:, i] += ~won

confs = collections.defaultdict(list)
for t in teams:
    c = conf.get(t)
    if c and "Independent" not in c:
        confs[c].append(ix[t])
champ = np.zeros((S, T), bool)
for c, members in confs.items():
    m = np.array(members)
    pct = cw[:, m] / np.maximum(cw[:, m] + cl[:, m], 1) + 0.01 * sor[:, m] + rng.normal(0, 1e-3, (S, len(m)))
    top2 = np.argsort(-pct, axis=1)[:, :2]
    a_, b_ = m[top2[:, 0]], m[top2[:, 1]]
    rows = np.arange(S)
    aw = (rating[rows, a_] - rating[rows, b_] + rng.normal(0, SD, S)) > 0
    w_, l_ = np.where(aw, a_, b_), np.where(aw, b_, a_)
    champ[rows, w_] = True
    wins[rows, w_] += 1; losses[rows, l_] += 1
    sor[rows, w_] += 0.5; sor[rows, l_] -= 0.25   # title games: a win helps, a loss costs little

LOSS_PEN = float(os.environ.get("LOSS_PEN", 0.0))   # committee loss-aversion beyond strength of record
score = sor + EYE * rating - LOSS_PEN * losses
made = np.zeros(T); bye = np.zeros(T); title = np.zeros(T); final = np.zeros(T)
order_all = np.argsort(-score, axis=1)
for s in range(S):
    order = order_all[s]
    champs = [i for i in order if champ[s, i]][:5]
    field = list(champs)
    for i in order:
        if len(field) == 12: break
        if i not in field: field.append(i)
    seeds = sorted(field, key=lambda i: -score[s, i])
    made[seeds] += 1; bye[seeds[:4]] += 1
    def play(x, y, home=None):
        edge = rating[s, x] - rating[s, y] + (HFA if home == x else 0)
        return x if edge + rng.normal(0, SD) > 0 else y
    r1 = [play(seeds[4], seeds[11], seeds[4]), play(seeds[5], seeds[10], seeds[5]),
          play(seeds[6], seeds[9], seeds[6]), play(seeds[7], seeds[8], seeds[7])]
    qf = [play(seeds[3], r1[0]), play(seeds[2], r1[1]), play(seeds[1], r1[2]), play(seeds[0], r1[3])]
    f1, f2 = play(qf[3], qf[0]), play(qf[2], qf[1])
    final[[f1, f2]] += 1
    title[play(f1, f2)] += 1

top25 = sorted(teams, key=lambda t: -R[t])[:25]
print(f"{S} sims | {'':2} {'team':18s} {'rating':>6} {'rec':>5} {'proj W':>6} {'playoff':>8} {'bye':>6} {'conf':>6} {'final':>6} {'title':>6}")
for k, t in enumerate(top25, 1):
    i = ix[t]; g_w = int(sum(1 for g in games if g['completed'] and g['home_pts'] is not None and ((norm(g['home']) == t and g['home_pts'] > g['away_pts']) or (norm(g['away']) == t and g['away_pts'] > g['home_pts']))))
    g_l = int(sum(1 for g in games if g['completed'] and g['home_pts'] is not None and ((norm(g['home']) == t and g['home_pts'] < g['away_pts']) or (norm(g['away']) == t and g['away_pts'] < g['home_pts']))))
    print(f"{k:>2} {disp.get(t, t):18s} {R[t]:6.1f} {g_w}-{g_l:<3} {wins[:, i].mean():6.1f} {made[i]/S:8.1%} {bye[i]/S:6.1%} {champ[:, i].mean():6.1%} {final[i]/S:6.1%} {title[i]/S:6.1%}")
others = sorted(((made[ix[t]] / S, disp.get(t, t), conf.get(t)) for t in teams if t not in top25), reverse=True)[:10]
print("\noutside our top 25 with the best playoff odds:", [(n, c, f"{p:.0%}") for p, n, c in others])
print("sum of playoff probs (should be 12):", round(made.sum() / S, 2), "| title sum:", round(title.sum() / S, 2))

# ---- diagnostic: P(in | regular-season + title-game losses) for a few teams
in_field = np.zeros((S, T), bool)
for s in range(S):
    order = order_all[s]
    champs = [i for i in order if champ[s, i]][:5]
    field = list(champs)
    for i in order:
        if len(field) == 12: break
        if i not in field: field.append(i)
    in_field[s, field] = True
for t in ("texas am", "lsu", "miami", "ole miss", "penn state", "texas tech"):
    i = ix[t]; out = []
    for L in range(0, 5):
        m = losses[:, i] == L
        if m.sum() >= 50: out.append(f"{L} losses: {in_field[m, i].mean():.0%} (n={m.sum()})")
    print(f"{disp[t]:12s}", " | ".join(out))
al = [(losses[s][[i for i in np.where(in_field[s])[0] if not champ[s, i]]]).max() for s in range(0, S, 10)]
print("most losses by an at-large team, share of sims:", {int(k): f"{v/len(al):.0%}" for k, v in sorted(collections.Counter(al).items())})
