"""New-QB road split: 2026 QB1 (attempts leader) classed vs 2025 -
RETURNING (100+ att, same team) / TRANSFER_VET (100+ att elsewhere) /
NEW_GREEN (first-time starter) - then SU / ATS / points vs the line by site.
Non-neutral FBS-vs-FBS lined games from the cached CFBD pulls. Internal
research (notes only). Run: python qb_road_split.py"""
import sys, os, io, contextlib, collections, statistics as st
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.getcwd()); sys.path.insert(0, "fpi-decomposition")
from refresh_all import load_env_key
import cfbd_client as cfbd
import build_conference_book as b
load_env_key()

def att_table(yr, refresh=False):
    """{team: {playerId: (name, att)}}"""
    out = collections.defaultdict(dict)
    for r in cfbd.get("/stats/player/season", {"year": yr, "category": "passing"}, refresh):
        if r.get("statType") == "ATT":
            out[r["team"]][str(r["playerId"])] = (r["player"], float(r["stat"]))
    return out

a25, a26 = att_table(2025), att_table(2026, refresh=True)   # QB1 = attempts leader to date
where25 = {}  # playerId -> (team, att) of his biggest 2025 stop
for team, ps in a25.items():
    for pid, (nm, att) in ps.items():
        if att > where25.get(pid, ("", 0))[1]:
            where25[pid] = (team, att)

with contextlib.redirect_stdout(io.StringIO()):
    games = b.fetch_games(False, {})
fbs_teams = {g["home"] for g in games if g["home_class"] == "fbs"} | {g["away"] for g in games if g["away_class"] == "fbs"}

EXP = 100  # 2025 attempts that make a QB "experienced"
cls, qb1 = {}, {}
for t in sorted(fbs_teams):
    ps = a26.get(t)
    if not ps:
        continue
    pid, (nm, att) = max(ps.items(), key=lambda kv: kv[1][1])
    t25, att25 = where25.get(pid, (None, 0))
    same_team_att = a25.get(t, {}).get(pid, (None, 0))[1]
    if same_team_att >= EXP:
        c = "RETURNING"
    elif t25 and t25 != t and att25 >= EXP:
        c = "TRANSFER_VET"      # new to the team, started elsewhere
    else:
        c = "NEW_GREEN"         # first-time starter (in-house or low-snap transfer)
    cls[t] = c
    qb1[t] = (nm, int(att), t25, int(att25))
cnt = collections.Counter(cls.values())
print("QB1 classes (2026 attempts leader vs 2025):", dict(cnt), "| unclassified FBS teams:", sorted(fbs_teams - set(cls)))
for chk in ("LSU", "Oregon", "Texas Tech", "Houston", "Ohio State", "Florida", "Auburn", "Miami", "Louisville"):
    print("  ", chk, cls.get(chk), qb1.get(chk))

done = [g for g in games if g["completed"] and g["home_pts"] is not None and g["away_pts"] is not None
        and g["home_class"] == "fbs" and g["away_class"] == "fbs" and g["spread"] is not None and not g["neutral"]]
print("\nnon-neutral FBS-vs-FBS lined games:", len(done))

def rows(filter_cls, site):
    """team-game rows: (cover_margin, won, spread_for_team)"""
    out = []
    for g in done:
        t = g["home"] if site == "home" else g["away"]
        if cls.get(t) not in filter_cls:
            continue
        m = g["home_pts"] - g["away_pts"]; s = float(g["spread"])
        if site == "away":
            m, s = -m, -s
        out.append(dict(g=g, team=t, margin=m, line=s, cover=m + s))
    return out

def show(label, R):
    if not R:
        print(f"{label:34s} n=0"); return
    w = sum(r["margin"] > 0 for r in R); cw = sum(r["cover"] > 0 for r in R); cl = sum(r["cover"] < 0 for r in R)
    print(f"{label:34s} n={len(R):3d} SU {w}-{len(R)-w} ({100*w/len(R):.0f}%) | ATS {cw}-{cl}-{len(R)-cw-cl} ({100*cw/max(cw+cl,1):.0f}%) | vs line {st.mean(r['cover'] for r in R):+.1f} | avg line {st.mean(r['line'] for r in R):+.1f}")

NEW = {"TRANSFER_VET", "NEW_GREEN"}
print("\n== by QB class and site ==")
for label, c in (("RETURNING starter", {"RETURNING"}), ("ANY new QB", NEW), ("  transfer w/ 100+ att elsewhere", {"TRANSFER_VET"}), ("  first-time starter", {"NEW_GREEN"})):
    show(label + " - ROAD", rows(c, "away"))
    show(label + " - HOME", rows(c, "home"))

print("\n== new QB on the road, by role ==")
R = rows(NEW, "away")
show("road FAVORITE", [r for r in R if r["line"] < 0])
show("road DOG", [r for r in R if r["line"] > 0])
show("road, line within 7", [r for r in R if abs(r["line"]) <= 7])
R2 = rows({"RETURNING"}, "away")
show("(returning) road FAVORITE", [r for r in R2 if r["line"] < 0])
show("(returning) road DOG", [r for r in R2 if r["line"] > 0])
show("(returning) road, line within 7", [r for r in R2 if abs(r["line"]) <= 7])

print("\n== matchup: road QB class vs home QB class ==")
for rc_l, rc in (("new", NEW), ("ret", {"RETURNING"})):
    for hc_l, hc in (("new", NEW), ("ret", {"RETURNING"})):
        show(f"road {rc_l} at home {hc_l}", [r for r in rows(rc, "away") if cls.get(r["g"]["home"]) in hc])

print("\n== first road start of the year for a new QB ==")
seen = set(); first = []
for r in sorted(R, key=lambda r: (r["g"]["wk"], r["g"]["id"])):
    if r["team"] not in seen:
        seen.add(r["team"]); first.append(r)
show("first road game, new QB", first)
print("\nworst / best new-QB road games vs the line:")
for r in sorted(R, key=lambda r: r["cover"])[:6] + sorted(R, key=lambda r: r["cover"])[-4:]:
    g = r["g"]
    print(f"  wk{g['wk']} {g['away']} {g['away_pts']} at {g['home']} {g['home_pts']} | {r['team']} line {r['line']:+.1f} -> vs line {r['cover']:+.1f} | QB {qb1[r['team']][0]} ({cls[r['team']]})")
