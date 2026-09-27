"""Scheme & tendency dossier for one team (INTERNAL - internal/dossiers/, never
a slide, Corey does not see it).

  python team_dossier.py --team Miami --week 4                 # season to date (games before week 4)
  python team_dossier.py --team Miami --week 4 --split "after 1" --missing "OJ Frederique Jr.,Xavier Lucas"
  python team_dossier.py --teams "Texas,Tennessee,..." --week 4   # several

Writes internal/dossiers/<Team>_week<N>.md (Lucas's outline layout: topic ->
points -> facts) and <Team>_week<N>.json (the numbers, for the film_study
page). --split adds <Team>_week<N>_split.md: every defensive number before vs
after a week or date, the replacements from the participation proxy, and a
short read that separates what the data shows from what the card says.

SOURCES AND CONVENTIONS (the notes rules apply):
  * play-by-play = CFBD /plays, full-week files already cached by the refresh;
    formation ("Shotgun") and tempo ("No Huddle") come from the 2026 play-text
    tags; depth is the text's own "short" / "deep" tag (CFBD has NO
    intermediate tag and NO air yards - the 10-19 / 20+ bins below are yards
    GAINED on completions, which is not the same thing);
  * rushing totals = official box score (/games/teams); stuff / 10+ / explosive
    rates = play-by-play (sacks excluded); passing per attempt = completions
    only;
  * participation = the per-player game box (/games/players): a player who
    recorded nothing is invisible, so "not in the box" is not "did not play";
  * fronts and coverages: CFBD has no alignment or coverage tags. Lines marked
    CARD are the scouting card's description (scouting_top25.json, written in
    July); lines marked DATA are what the numbers imply. They are kept apart.
"""
import argparse, collections, datetime as dt, html, json, os, re, statistics, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "fpi-decomposition"))
from refresh_all import load_env_key  # noqa: E402
import cfbd_client as cfbd  # noqa: E402

YEAR = 2026
OUT = os.path.join(HERE, "internal", "dossiers")
PASS = ("Pass", "Sack", "Interception")
SKIP = ("Kickoff", "Punt", "Field Goal", "Timeout", "End", "Penalty", "Extra Point", "Two Point", "Uncategorized")
SMALL = 25          # plays: below this a rate is labelled small-sample
SPLIT_MIN = 40      # dropbacks/plays per half before the split will call a change
POS_GROUP = {"Defensive Back": "DB", "Linebacker": "LB", "Defensive Line": "DL", "Wide Receiver": "WR",
             "Tight End": "TE", "Running Back": "RB", "Quarterback": "QB", "Offensive Line": "OL",
             "Kicker": "K", "Punter": "P", "Longsnapper": "LS",
             # rosters that use abbreviations (Clemson etc.)
             "CB": "DB", "S": "DB", "SAF": "DB", "DB": "DB", "NB": "DB", "DE": "DL", "DT": "DL", "DL": "DL", "EDGE": "DL",
             "LB": "LB", "ILB": "LB", "OLB": "LB", "OL": "OL", "OT": "OL", "OG": "OL", "C": "OL", "WR": "WR", "TE": "TE", "RB": "RB", "QB": "QB",
             "PK": "K", "K": "K", "P": "P", "LS": "LS"}


# ----------------------------------------------------------------- helpers
def fix_text(s):
    """scouting_top25.json carries UTF-8 read as cp1252 (em dashes as 'â€”')."""
    if not isinstance(s, str):
        return s
    try:
        return s.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def txt(p):
    return p.get("playText") or ""


def is_drop(p):
    return any(t in p["playType"] for t in PASS)


def is_rush(p):
    # same rule as stat_package.py: a fumble on a run recovered by the defense is a run
    return (("Rush" in p["playType"]) or (p["playType"] == "Fumble Recovery (Opponent)" and "rush" in txt(p).lower())) and not is_drop(p)


def is_scrim(p):
    return (is_drop(p) or is_rush(p)) and not any(s in p["playType"] for s in SKIP)


def yd(p):
    return p.get("yardsGained") or 0


def is_comp(p):
    t = txt(p).lower()
    return ("Reception" in p["playType"] or "Passing Touchdown" in p["playType"]
            or ("complete" in t and "incomplete" not in t))


def is_sack(p):
    return "Sack" in p["playType"]


def clock_secs(p):
    c = p.get("clock") or {}
    return int(c.get("minutes") or 0) * 60 + int(c.get("seconds") or 0)


def clock_str(p):
    c = p.get("clock") or {}
    return f"Q{p.get('period', '?')} {int(c.get('minutes') or 0)}:{int(c.get('seconds') or 0):02d}"


def pct(n, d):
    return round(100.0 * n / d, 1) if d else None


def per(n, d, k=1):
    return round(n / d, k) if d else None


def fmt(v, suffix=""):
    return "n/a" if v is None else f"{v}{suffix}"


def small(n):
    return f" (small sample, n={n})" if n < SMALL else ""


NAME_RE = re.compile(r"#\d+ ([A-Z][\w'\-]*\.?\s?[A-Z][\w'\-]+(?: (?:Jr\.|Sr\.|II|III|IV))?)")
DEPTH_RE = re.compile(r"pass (?:complete|incomplete) (short|deep) (left|middle|right)", re.I)
RUSH_DIR_RE = re.compile(r"rush (left|middle|right)", re.I)


# scoring-summary rows have no tags: "Malachi Toney 47 Yd pass from Darian Mensah (Kick)" / "Joey Koch 10 Yd Run (Kick)"
SUMMARY_PASS_RE = re.compile(r"^([A-Z][\w'\.\- ]+?) \d+ Yd pass from ([A-Z][\w'\.\- ]+?) \(")
SUMMARY_RUN_RE = re.compile(r"^([A-Z][\w'\.\- ]+?) \d+ Yd Run\b")


def target_of(p):
    """(receiver, depth tag, direction) from the play text, or (None, None, None)."""
    t = txt(p)
    m = DEPTH_RE.search(t)
    depth, direction = (m.group(1).lower(), m.group(2).lower()) if m else (None, None)
    rec = None
    if m:
        tail = t[m.end():]
        mm = re.search(r"(?:to|intended for) " + NAME_RE.pattern, tail)
        if mm:
            rec = mm.group(1)
    if rec is None:
        ms = SUMMARY_PASS_RE.match(t)
        if ms:
            rec = ms.group(1)
    return rec, depth, direction


def passer_of(p):
    m = NAME_RE.search(txt(p).split(" pass ")[0]) if " pass " in txt(p) else None
    if m:
        return m.group(1)
    ms = SUMMARY_PASS_RE.match(txt(p))
    return ms.group(2) if ms else None


def rusher_of(p):
    m = NAME_RE.search(txt(p).split(" rush ")[0]) if " rush " in txt(p) else None
    if m:
        return m.group(1)
    ms = SUMMARY_RUN_RE.match(txt(p))
    return ms.group(1) if ms else None


ROSTER_ALIASES = {}   # surname -> set of first-name tokens (first name + quoted nickname), filled per team


def load_aliases(ros):
    ROSTER_ALIASES.clear()
    for r in ros:
        raw = html.unescape(str(r["name"]))
        toks = norm_name(raw)
        if not toks:
            continue
        firsts = {toks[0]}
        for nick in re.findall(r'"([^"]+)"', raw):
            firsts.add(re.sub(r"[^a-z]", "", nick.lower()))
        ROSTER_ALIASES.setdefault(toks[-1], []).append(firsts)   # one alias set PER roster entry


def norm_name(s):
    s = html.unescape(str(s))
    s = re.sub(r'"[^"]*"', " ", s)                  # drop a quoted nickname
    s = re.sub(r"\([^)]*\)", " ", s)
    s = re.sub(r"\b(Jr|Sr|II|III|IV)\b\.?", " ", s)
    s = re.sub(r"[^A-Za-z ]", "", s).lower()
    return s.split()


def same_person(a, b):
    """Loose match: same surname, and first names share an initial or a nickname."""
    ta, tb = norm_name(a), norm_name(b)
    if not ta or not tb or ta[-1] != tb[-1]:
        return False
    fa, fb = ta[0], tb[0]
    if fa == fb or fa[0] == fb[0]:
        return True
    # nickname inside quotes was dropped above; try the raw strings, then the roster's aliases
    ra, rb = html.unescape(str(a)).lower(), html.unescape(str(b)).lower()
    if (fa in rb) or (fb in ra):
        return True
    # both first names must sit in the SAME roster entry's alias set (Damari Brown is not CharMar "Marty" Brown)
    hit = lambda al, f: any(x == f or x[0] == f[0] for x in al)
    return any(hit(al, fa) and hit(al, fb) for al in ROSTER_ALIASES.get(ta[-1], []))


# ----------------------------------------------------------------- loaders
def team_games(team, through_week):
    gs = [g for g in cfbd.get("/games", {"year": YEAR, "seasonType": "regular"}, False)
          if team in (g["homeTeam"], g["awayTeam"]) and g.get("completed") and g["week"] < through_week]
    return sorted(gs, key=lambda g: g["startDate"])


def week_plays(week, refresh=False):
    return cfbd.get("/plays", {"year": YEAR, "week": week, "seasonType": "regular"}, refresh)


def box_rush(team, week, gid, refresh=False):
    own = opp = None
    for g in cfbd.get("/games/teams", {"year": YEAR, "week": week, "seasonType": "regular"}, refresh):
        if g.get("id") != gid:
            continue
        for t in g["teams"]:
            st = {x["category"]: x["stat"] for x in t["stats"]}
            if st.get("rushingAttempts") is None:
                continue
            d = dict(att=int(st["rushingAttempts"]), yds=int(st["rushingYards"]))
            d["ypc"] = round(d["yds"] / max(d["att"], 1), 1)
            if t.get("team") == team:
                own = d
            else:
                opp = d
    return own, opp


def player_box(team, week, gid, refresh=False):
    """{player: {category: {stat: value}}} for the team in game gid."""
    out = collections.defaultdict(lambda: collections.defaultdict(dict))
    for g in cfbd.get("/games/players", {"year": YEAR, "week": week}, refresh):
        if g.get("id") != gid:
            continue
        for t in g["teams"]:
            if t.get("team") != team:
                continue
            for c in t["categories"]:
                for tt in c["types"]:
                    for a in tt["athletes"]:
                        out[a["name"]][c["name"]][tt["name"]] = a["stat"]
    return out


def roster(team):
    import openpyxl
    wb = openpyxl.load_workbook(os.path.join(HERE, "rosters", "FBS_Rosters_2026.xlsx"), read_only=True)
    rows = list(wb["All Players"].iter_rows(values_only=True))
    hdr = list(rows[0])
    iT, iJ, iN, iP, iC = (hdr.index(k) for k in ("Team", "Jersey #", "Name", "Position", "Class"))
    return [dict(no=r[iJ], name=html.unescape(str(r[iN])), pos=POS_GROUP.get(r[iP], r[iP]), cls=r[iC])
            for r in rows[1:] if r and r[iT] == team]


def depth_chart(team):
    d = json.load(open(os.path.join(HERE, "ourlads_depth.json"), encoding="utf-8"))
    t = d["teams"].get(team) or {}
    rows = []
    for r in t.get("rows", []):
        players = []
        for s in r["players"]:
            if "," in s:
                last, first = s.split(",", 1)
            else:
                last, first = s, ""
            # "Vandrevius RS JR/TR" -> drop class / redshirt / transfer tokens
            ftoks = [t for t in first.split() if t.upper() not in ("RS", "FR", "SO", "JR", "SR", "GR", "TR") and "/" not in t]
            players.append((" ".join(ftoks) + " " + last.strip()).strip())
        rows.append(dict(pos=r["pos"], players=players))
    return dict(updated=t.get("updated"), off_scheme=t.get("off_scheme"), def_scheme=t.get("def_scheme"), rows=rows)


def card(team):
    d = json.load(open(os.path.join(HERE, "scouting_top25.json"), encoding="utf-8"))
    c = d["teams"].get(team) or {}
    return {k: fix_text(v) for k, v in c.items() if k in ("ob", "ot", "db", "dt", "conf")} | {"vintage": d["meta"].get("vintage")}


def team_stats(team):
    try:
        return json.load(open(os.path.join(HERE, "team_stats_2026.json"), encoding="utf-8"))["teams"].get(team) or {}
    except (OSError, KeyError):
        return {}


# ----------------------------------------------------------------- the cuts
def formation(plays):
    tagged = [p for p in plays if re.match(r"^\(\d+:\d+\)", txt(p)) or "Shotgun" in txt(p) or "No Huddle" in txt(p)]
    sg = [p for p in tagged if "Shotgun" in txt(p)]
    nh = [p for p in tagged if "No Huddle" in txt(p)]
    return dict(n=len(plays), tagged=len(tagged), shotgun=len(sg), under_center=len(tagged) - len(sg), no_huddle=len(nh),
                shotgun_pct=pct(len(sg), len(tagged)), no_huddle_pct=pct(len(nh), len(tagged)),
                run_pct_shotgun=pct(sum(1 for p in sg if is_rush(p)), len(sg)),
                run_pct_under_center=pct(sum(1 for p in tagged if "Shotgun" not in txt(p) and is_rush(p)), len(tagged) - len(sg)),
                ypp_no_huddle=per(sum(yd(p) for p in nh), len(nh)),
                ypp_huddle=per(sum(yd(p) for p in tagged if "No Huddle" not in txt(p)), len(tagged) - len(nh)))


def tempo(plays_all_types):
    """Seconds of game clock between consecutive snaps of the same drive and
    period (scrimmage plays only; gaps over 60 s are stoppages and dropped)."""
    gaps, gaps_nh, gaps_h = [], [], []
    by_drive = collections.defaultdict(list)
    for p in plays_all_types:
        if is_scrim(p):
            by_drive[p["driveId"]].append(p)
    for ps in by_drive.values():
        ps.sort(key=lambda p: (p.get("period", 0), -clock_secs(p), p.get("playNumber", 0)))
        for a, b in zip(ps, ps[1:]):
            if a.get("period") != b.get("period"):
                continue
            g = clock_secs(a) - clock_secs(b)
            if 0 < g <= 60:
                gaps.append(g)
                (gaps_nh if "No Huddle" in txt(b) else gaps_h).append(g)
    med = lambda x: round(statistics.median(x), 1) if x else None
    return dict(n=len(gaps), median=med(gaps), mean=round(statistics.mean(gaps), 1) if gaps else None,
                median_no_huddle=med(gaps_nh), median_huddle=med(gaps_h), n_no_huddle=len(gaps_nh), n_huddle=len(gaps_h),
                under_20s_pct=pct(sum(1 for g in gaps if g <= 20), len(gaps)))


def dd_bucket(p):
    d, x = p.get("down") or 0, p.get("distance") or 0
    if d == 1:
        return "1st"
    if d == 2:
        return "2nd & 1-3" if x <= 3 else ("2nd & 4-6" if x <= 6 else "2nd & 7+")
    if d == 3:
        return "3rd & 1-2" if x <= 2 else ("3rd & 3-5" if x <= 5 else "3rd & 6+")
    if d == 4:
        return "4th"
    return "other"


DD_ORDER = ["1st", "2nd & 1-3", "2nd & 4-6", "2nd & 7+", "3rd & 1-2", "3rd & 3-5", "3rd & 6+", "4th"]


def converted(p):
    return ("Touchdown" in p["playType"] and "Return" not in p["playType"]) or yd(p) >= (p.get("distance") or 99)


def cut(plays, key, order=None):
    """Group scrimmage plays by key(p) -> per-bucket line: n, run%, ypp, explosive
    (20+ pass / 10+ run) rate, sack rate, conversions where it is a 3rd/4th down."""
    g = collections.defaultdict(list)
    for p in plays:
        g[key(p)].append(p)
    out = {}
    for k in (order or sorted(g)):
        ps = g.get(k, [])
        if not ps:
            continue
        runs = [p for p in ps if is_rush(p)]
        drops = [p for p in ps if is_drop(p)]
        expl = sum(1 for p in drops if yd(p) >= 20) + sum(1 for p in runs if yd(p) >= 10)
        out[k] = dict(n=len(ps), run_pct=pct(len(runs), len(ps)), ypp=per(sum(yd(p) for p in ps), len(ps)),
                      expl_pct=pct(expl, len(ps)), sack_pct=pct(sum(1 for p in drops if is_sack(p)), len(drops)),
                      stuff_pct=pct(sum(1 for p in runs if yd(p) <= 0), len(runs)),
                      conv=(f"{sum(1 for p in ps if converted(p))}/{len(ps)}" if k and str(k)[:1] in "34" else None),
                      deep_pct=pct(sum(1 for p in drops if target_of(p)[1] == "deep"), len(drops)))
    return out


def score_state(p):
    d = (p.get("offenseScore") or 0) - (p.get("defenseScore") or 0)
    if d >= 17:
        return "leading 17+"
    if d > 0:
        return "leading 1-16"
    if d == 0:
        return "tied"
    if d >= -16:
        return "trailing 1-16"
    return "trailing 17+"


SCORE_ORDER = ["trailing 17+", "trailing 1-16", "tied", "leading 1-16", "leading 17+"]


def field_zone(p):
    y = p.get("yardsToGoal")
    if y is None:
        return "unknown"
    if y >= 80:
        return "own 1-20"
    if y > 50:
        return "own 21-49"
    if y > 20:
        return "opp 50-21"
    return "red zone (20 in)"


ZONE_ORDER = ["own 1-20", "own 21-49", "opp 50-21", "red zone (20 in)"]


def target_tree(plays, gmeta):
    drops = [p for p in plays if is_drop(p) and not is_sack(p)]
    tree = collections.defaultdict(lambda: dict(targets=0, catches=0, yds=0, short=0, deep=0, p20=0, td=0, games=set()))
    depth = collections.Counter(); direction = collections.Counter(); untagged = 0
    bins = collections.Counter()
    for p in drops:
        rec, dp, dr = target_of(p)
        if dp is None:
            untagged += 1
        else:
            depth[dp] += 1; direction[f"{dp} {dr}"] += 1
        if is_comp(p):
            bins["0-9" if yd(p) < 10 else ("10-19" if yd(p) < 20 else "20+")] += 1
        if rec:
            t = tree[rec]; t["targets"] += 1; t["games"].add(gmeta[p["gameId"]])
            if dp:
                t[dp] += 1
            if is_comp(p):
                t["catches"] += 1; t["yds"] += yd(p); t["p20"] += yd(p) >= 20
                t["td"] += "Touchdown" in p["playType"]
    rows = sorted(tree.items(), key=lambda kv: -kv[1]["targets"])
    for _, t in rows:
        t["games"] = len(t["games"])
    return dict(dropbacks=len([p for p in plays if is_drop(p)]), attempts=len(drops), untagged=untagged,
                short=depth["short"], deep=depth["deep"], deep_pct=pct(depth["deep"], depth["short"] + depth["deep"]),
                by_direction=dict(direction.most_common()), completion_bins=dict(bins), receivers=rows[:12])


def explosives(plays, gmeta, allowed=False):
    out = []
    for p in plays:
        if (is_drop(p) and yd(p) >= 20) or (is_rush(p) and yd(p) >= 15):
            who = (f"{passer_of(p) or '?'} to {target_of(p)[0] or '?'}" if is_drop(p) else rusher_of(p) or "?")
            rec, dp, dr = target_of(p)
            out.append(dict(game=gmeta[p["gameId"]], clock=clock_str(p), yards=yd(p), kind="pass" if is_drop(p) else "run",
                            who=who, tag=(f"{dp} {dr}" if dp else (RUSH_DIR_RE.search(txt(p)).group(0) if RUSH_DIR_RE.search(txt(p)) else "")),
                            ppa=p.get("ppa"), text=re.sub(r"\s+", " ", txt(p))[:160]))
    out.sort(key=lambda r: -r["yards"])
    src = collections.Counter(r["who"] for r in out)
    return dict(n=len(out), passes=sum(1 for r in out if r["kind"] == "pass"), runs=sum(1 for r in out if r["kind"] == "run"),
                sources=src.most_common(8), plays=out)


def red_zone(plays):
    inside = [p for p in plays if (p.get("yardsToGoal") or 100) <= 20]
    drives = {p["driveId"] for p in inside}
    td = {p["driveId"] for p in inside if "Touchdown" in p["playType"] and "Return" not in p["playType"] and "Interception" not in p["playType"]}
    ten = [p for p in inside if (p.get("yardsToGoal") or 100) <= 10]
    return dict(trips=len(drives), td=len(td), td_pct=pct(len(td), len(drives)), plays=len(inside),
                run_pct=pct(sum(1 for p in inside if is_rush(p)), len(inside)),
                run_pct_inside_10=pct(sum(1 for p in ten if is_rush(p)), len(ten)), plays_inside_10=len(ten),
                ypp=per(sum(yd(p) for p in inside), len(inside)))


def sacks_by_down(plays):
    out = {}
    for d in (1, 2, 3, 4):
        drops = [p for p in plays if is_drop(p) and p.get("down") == d]
        out[f"{d}"] = dict(dropbacks=len(drops), sacks=sum(1 for p in drops if is_sack(p)), sack_pct=pct(sum(1 for p in drops if is_sack(p)), len(drops)))
    return out


def side_summary(plays, box):
    drops = [p for p in plays if is_drop(p)]
    atts = [p for p in drops if not is_sack(p)]
    comps = [p for p in atts if is_comp(p)]
    runs = [p for p in plays if is_rush(p)]
    return dict(plays=len(plays), dropbacks=len(drops), att=len(atts), comp=len(comps), pass_yds=sum(yd(p) for p in comps),
                ypa=per(sum(yd(p) for p in comps), len(atts)), ypc=per(sum(yd(p) for p in comps), len(comps)),
                p20=sum(1 for p in drops if yd(p) >= 20), p20_pct=pct(sum(1 for p in drops if yd(p) >= 20), len(drops)),
                sacks=sum(1 for p in drops if is_sack(p)), sack_pct=pct(sum(1 for p in drops if is_sack(p)), len(drops)),
                ints=sum(1 for p in drops if "Interception" in p["playType"]),
                pbp_runs=len(runs), r10=sum(1 for p in runs if yd(p) >= 10), r10_pct=pct(sum(1 for p in runs if yd(p) >= 10), len(runs)),
                stuffs=sum(1 for p in runs if yd(p) <= 0), stuff_pct=pct(sum(1 for p in runs if yd(p) <= 0), len(runs)),
                box_att=box["att"] if box else None, box_yds=box["yds"] if box else None, box_ypc=box["ypc"] if box else None,
                ppa=round(statistics.mean([p["ppa"] for p in plays if p.get("ppa") is not None]), 3) if any(p.get("ppa") is not None for p in plays) else None)


# ----------------------------------------------------------------- personnel
def participation(team, games, refresh=False):
    ros = roster(team)
    load_aliases(ros)
    dc = depth_chart(team)
    appear = collections.defaultdict(dict)     # player -> game label -> short stat line
    hurries = collections.defaultdict(dict)
    for g in games:
        lab = g["_label"]
        pb = player_box(team, g["week"], g["id"], refresh)
        for nm, cats in pb.items():
            bits = []
            d = cats.get("defensive", {})
            if d:
                bits.append(f"{d.get('TOT', '0')} tkl" + (f", {d['PD']} PD" if d.get("PD", "0") != "0" else "")
                            + (f", {d['SACKS']} sk" if d.get("SACKS", "0") not in ("0", "0.0") else "")
                            + (f", {d['QB HUR']} hur" if d.get("QB HUR", "0") != "0" else ""))
                if d.get("QB HUR", "0") != "0":
                    hurries[lab][nm] = int(float(d["QB HUR"]))
            if cats.get("interceptions"):
                bits.append(f"{cats['interceptions'].get('INT', '?')} INT")
            r = cats.get("receiving", {})
            if r:
                bits.append(f"{r.get('REC', '0')} rec {r.get('YDS', '0')} yds")
            ru = cats.get("rushing", {})
            if ru:
                bits.append(f"{ru.get('CAR', '0')} car {ru.get('YDS', '0')} yds")
            pa = cats.get("passing", {})
            if pa:
                bits.append(f"{pa.get('C/ATT', '?')} pass")
            appear[nm][lab] = "; ".join(bits) or "in box"
    # roster position for every box name
    def pos_of(nm):
        for r in ros:
            if same_person(r["name"], nm):
                return r["pos"], r["no"]
        return "?", None
    rows = []
    for nm, gl in appear.items():
        pos, no = pos_of(nm)
        rows.append(dict(name=nm, pos=pos, no=no, games=len(gl), by_game=gl))
    rows.sort(key=lambda r: (r["pos"], -r["games"], r["name"]))
    # depth-chart starters: did they show up?
    starters = []
    for r in dc["rows"]:
        for i, nm in enumerate(r["players"][:2]):
            hit = next((x for x in rows if same_person(x["name"], nm)), None)
            starters.append(dict(slot=r["pos"], rank=i + 1, name=nm, games_in_box=hit["games"] if hit else 0,
                                 by_game=hit["by_game"] if hit else {}, box_name=hit["name"] if hit else None))
    return dict(roster_n=len(ros), depth_updated=dc["updated"], off_scheme=dc["off_scheme"], def_scheme=dc["def_scheme"],
                players=rows, starters=starters, hurries={k: dict(v) for k, v in hurries.items()})


# ----------------------------------------------------------------- build
def build(team, through_week, refresh=False, games=None):
    games = games if games is not None else team_games(team, through_week)
    gmeta = {}
    per_game, off_all, def_all, off_raw, def_raw = [], [], [], [], []
    for g in games:
        home = g["homeTeam"] == team
        opp = g["awayTeam"] if home else g["homeTeam"]
        us, them = (g["homePoints"], g["awayPoints"]) if home else (g["awayPoints"], g["homePoints"])
        g["_label"] = f"wk{g['week']} {'vs' if home else 'at'} {opp}"
        gmeta[g["id"]] = g["_label"]
        wk = [p for p in week_plays(g["week"], refresh) if p.get("gameId") == g["id"]]
        scrim = [p for p in wk if is_scrim(p)]
        o = [p for p in scrim if p["offense"] == team]
        d = [p for p in scrim if p["defense"] == team]
        bo, bd = box_rush(team, g["week"], g["id"], refresh)
        cls = g["awayClassification"] if home else g["homeClassification"]
        per_game.append(dict(label=g["_label"], week=g["week"], opp=opp, opp_class=cls, result=f"{'W' if us > them else 'L'} {us}-{them}",
                             date=g["startDate"][:10],
                             offense=side_summary(o, bo) | dict(formation=formation(o), tempo=tempo([p for p in wk if p["offense"] == team])),
                             defense=side_summary(d, bd) | dict(formation=formation(d))))
        off_all += o; def_all += d
        off_raw += [p for p in wk if p["offense"] == team]; def_raw += [p for p in wk if p["defense"] == team]
    box_o = dict(att=sum((g["offense"]["box_att"] or 0) for g in per_game), yds=sum((g["offense"]["box_yds"] or 0) for g in per_game))
    box_o["ypc"] = round(box_o["yds"] / max(box_o["att"], 1), 1)
    box_d = dict(att=sum((g["defense"]["box_att"] or 0) for g in per_game), yds=sum((g["defense"]["box_yds"] or 0) for g in per_game))
    box_d["ypc"] = round(box_d["yds"] / max(box_d["att"], 1), 1)

    def side(plays, raw, box, allowed):
        return dict(summary=side_summary(plays, box), formation=formation(plays), tempo=tempo(raw),
                    by_down_distance=cut(plays, dd_bucket, DD_ORDER), by_score=cut(plays, score_state, SCORE_ORDER),
                    by_zone=cut(plays, field_zone, ZONE_ORDER), targets=target_tree(plays, gmeta),
                    explosives=explosives(plays, gmeta, allowed), red_zone=red_zone(plays), sacks_by_down=sacks_by_down(plays),
                    third_long=cut([p for p in plays if p.get("down") == 3 and (p.get("distance") or 0) >= 6], lambda p: "3rd & 6+"),
                    rush_dir=dict(collections.Counter((RUSH_DIR_RE.search(txt(p)).group(1).lower() if RUSH_DIR_RE.search(txt(p)) else "untagged")
                                                      for p in plays if is_rush(p)).most_common()))
    doss = dict(team=team, through_week=through_week, generated=dt.datetime.now().isoformat(timespec="minutes"),
                games=per_game, offense=side(off_all, off_raw, box_o, False), defense=side(def_all, def_raw, box_d, True),
                card=card(team), depth=depth_chart(team), stats=team_stats(team))
    doss["personnel"] = participation(team, games, refresh)
    doss["watch"] = watch_list(doss, off_all + def_all, gmeta, team)
    return doss


def watch_list(doss, plays, gmeta, team):
    """Five plays to find on film: the three biggest offensive plays that fit
    the signature (deep shots if the deep rate is high, runs if run-heavy) and
    the two biggest defensive events (sack / INT / stuff) by |PPA|."""
    o = [p for p in plays if p["offense"] == team and p.get("ppa") is not None]
    d = [p for p in plays if p["defense"] == team and p.get("ppa") is not None]
    o.sort(key=lambda p: -p["ppa"]); d.sort(key=lambda p: p["ppa"])
    picks = []
    for p in o[:3]:
        picks.append(dict(side="offense", game=gmeta[p["gameId"]], clock=clock_str(p), ppa=round(p["ppa"], 2), yards=yd(p), text=re.sub(r"\s+", " ", txt(p))[:170]))
    for p in d[:2]:
        picks.append(dict(side="defense", game=gmeta[p["gameId"]], clock=clock_str(p), ppa=round(p["ppa"], 2), yards=yd(p), text=re.sub(r"\s+", " ", txt(p))[:170]))
    return picks


# ----------------------------------------------------------------- markdown
def rk(stats, side, key):
    r = (stats.get(side) or {}).get(key + "_rk")
    return f" (#{r} of 138)" if r else ""


def dd_table(cuts, third=True):
    rows = ["| Down & distance | plays | run % | yds/play | explosive % | sack % | deep throw % | conv |",
            "|---|---|---|---|---|---|---|---|"]
    for k, v in cuts.items():
        rows.append(f"| {k} | {v['n']} | {fmt(v['run_pct'])} | {fmt(v['ypp'])} | {fmt(v['expl_pct'])} | {fmt(v['sack_pct'])} | {fmt(v['deep_pct'])} | {v['conv'] or ''} |")
    return rows


def state_table(cuts, label):
    rows = [f"| {label} | plays | run % | yds/play | explosive % | stuff % (runs) |", "|---|---|---|---|---|---|"]
    for k, v in cuts.items():
        rows.append(f"| {k} | {v['n']} | {fmt(v['run_pct'])} | {fmt(v['ypp'])} | {fmt(v['expl_pct'])} | {fmt(v['stuff_pct'])} |")
    return rows


def md_side(D, side, stats, label_us, label_them):
    S, F, T, TT, E, RZ, SD = D["summary"], D["formation"], D["tempo"], D["targets"], D["explosives"], D["red_zone"], D["sacks_by_down"]
    off = side == "offense"
    L = []
    L.append(f"- **{'Offense' if off else 'Defense'} — what the numbers say ({S['plays']} scrimmage plays)**")
    L.append(f"  - Formation (play-text tags, {F['tagged']} of {F['n']} plays tagged): shotgun {fmt(F['shotgun_pct'], '%')} ({F['shotgun']}), under center {F['under_center']}; no-huddle {fmt(F['no_huddle_pct'], '%')} ({F['no_huddle']})")
    L.append(f"    - Run rate from shotgun {fmt(F['run_pct_shotgun'], '%')} vs under center {fmt(F['run_pct_under_center'], '%')}; yards a play no-huddle {fmt(F['ypp_no_huddle'])} vs huddle {fmt(F['ypp_huddle'])}")
    if off:
        L.append(f"  - Tempo: median {fmt(T['median'])} s of game clock between snaps in the same drive (n={T['n']}; {fmt(T['under_20s_pct'], '%')} of snaps inside 20 s); no-huddle snaps {fmt(T['median_no_huddle'])} s (n={T['n_no_huddle']}) vs huddle {fmt(T['median_huddle'])} s (n={T['n_huddle']})")
    else:
        L.append(f"  - Opponents' tempo against this defense: median {fmt(T['median'])} s between snaps (n={T['n']}); no-huddle {fmt(T['median_no_huddle'])} s vs huddle {fmt(T['median_huddle'])} s")
    L.append(f"  - Passing{' allowed' if not off else ''}: {S['comp']}-of-{S['att']} for {S['pass_yds']} — {fmt(S['ypa'])} per attempt{rk(stats, 'off' if off else 'def_', 'ypa')}, {fmt(S['ypc'])} per completion; {S['p20']} passes of 20+ in {S['dropbacks']} dropbacks ({fmt(S['p20_pct'], '%')}){rk(stats, 'off' if off else 'def_', 'p20_rate')}; sacks {S['sacks']} ({fmt(S['sack_pct'], '%')}); INT {S['ints']}")
    L.append(f"    - Depth tags (the text says only short or deep): {TT['deep']} deep of {TT['short'] + TT['deep']} tagged throws ({fmt(TT['deep_pct'], '%')} deep){'; ' + str(TT['untagged']) + ' untagged' if TT['untagged'] else ''}")
    L.append(f"    - Yards gained on completions (not air yards): 0-9: {TT['completion_bins'].get('0-9', 0)} · 10-19: {TT['completion_bins'].get('10-19', 0)} · 20+: {TT['completion_bins'].get('20+', 0)}")
    L.append(f"    - Where the throws go: " + ", ".join(f"{k} {v}" for k, v in list(TT['by_direction'].items())[:6]))
    L.append(f"  - Rushing{' allowed' if not off else ''} (box score): {S['box_att']} for {S['box_yds']}, {fmt(S['box_ypc'])} a carry{rk(stats, 'off' if off else 'def_', 'rush_ypc')}; play-by-play runs {S['pbp_runs']}: 10+ on {S['r10']} ({fmt(S['r10_pct'], '%')}), stuffed {S['stuffs']} ({fmt(S['stuff_pct'], '%')}){rk(stats, 'off' if off else 'def_', 'stuff_rate')}")
    L.append(f"    - Run direction tags: " + ", ".join(f"{k} {v}" for k, v in D['rush_dir'].items()))
    L.append(f"  - Run/pass by down and distance{' (what it faces)' if not off else ''}")
    L += ["    " + r for r in dd_table(D["by_down_distance"])]
    tl = D["third_long"].get("3rd & 6+")
    if tl:
        L.append(f"  - Third-and-long (6+){' allowed' if not off else ''}: {tl['conv']} converted, {fmt(100 - (tl['run_pct'] or 0), '%')} pass, deep throw {fmt(tl['deep_pct'], '%')}, sack {fmt(tl['sack_pct'], '%')}, explosive {fmt(tl['expl_pct'], '%')}{small(tl['n'])}")
    L.append(f"  - Red zone{' allowed' if not off else ''}: {RZ['td']} TD on {RZ['trips']} trips inside the 20 ({fmt(RZ['td_pct'], '%')}){rk(stats, 'off' if off else 'def_', 'rz_pct')}; {RZ['plays']} plays there, {fmt(RZ['run_pct'], '%')} runs; inside the 10: {fmt(RZ['run_pct_inside_10'], '%')} runs on {RZ['plays_inside_10']} plays")
    L.append(f"  - By score state{' (opponents facing this defense)' if not off else ''}")
    L += ["    " + r for r in state_table(D["by_score"], "Score state")]
    L.append(f"  - By field zone{' (opponents facing this defense)' if not off else ''}")
    L += ["    " + r for r in state_table(D["by_zone"], "Field zone")]
    if not off:
        L.append("  - Sacks by down (pbp): " + " · ".join(f"down {k}: {v['sacks']} in {v['dropbacks']} ({fmt(v['sack_pct'], '%')})" for k, v in SD.items()))
    L.append(f"  - Explosive plays{' allowed' if not off else ''} (20+ pass, 15+ run): {E['n']} — {E['passes']} passes, {E['runs']} runs")
    for who, n in E["sources"][:6]:
        L.append(f"    - {who}: {n}")
    for r in E["plays"][:8]:
        L.append(f"    - {r['game']}, {r['clock']}: {r['yards']} yds {r['kind']} ({r['tag']}) — {r['text']}")
    L.append(f"  - {'Target tree' if off else 'Who opponents throw at'} (targets · catches · yards · short/deep tags · 20+)")
    for nm, t in TT["receivers"][:10]:
        L.append(f"    - {nm}: {t['targets']} tgt, {t['catches']} rec, {t['yds']} yds, short {t['short']} / deep {t['deep']}, 20+ {t['p20']}, TD {t['td']} ({t['games']} g)")
    return L


def md_personnel(P, side_filter=None):
    L = ["- **Personnel — who is actually playing (participation proxy: the per-player game box; a player with no stat is invisible, so 'not in box' is not 'did not play')**"]
    L.append(f"  - Depth chart: OurLads {P['depth_updated']} ({P['off_scheme']} / {P['def_scheme']}); roster {P['roster_n']} players")
    L.append("  - Depth-chart starters and how many game boxes they appear in")
    for s in P["starters"]:
        if s["rank"] != 1 or s["slot"] in ("PT", "PK", "KO", "LS", "H", "PR", "KR", "P", "K"):
            continue
        flag = "" if s["games_in_box"] else " — NOT IN ANY BOX"
        L.append(f"    - {s['slot']}: {s['name']} — {s['games_in_box']} g{flag}" + (": " + "; ".join(f"{g} {v}" for g, v in s["by_game"].items()) if s["by_game"] else ""))
    L.append("  - Everyone in the box, by position group (games · per-game line)")
    for pos in ("QB", "RB", "WR", "TE", "DL", "LB", "DB", "K", "P", "?"):
        rows = [r for r in P["players"] if r["pos"] == pos]
        if not rows:
            continue
        L.append(f"    - {pos}")
        for r in rows:
            L.append(f"      - {r['name']} ({r['games']} g): " + " · ".join(f"{g}: {v}" for g, v in r["by_game"].items()))
    if P["hurries"]:
        L.append("  - QB hurries credited (player box), by game")
        for g, hv in P["hurries"].items():
            L.append(f"    - {g}: " + ", ".join(f"{k} {v}" for k, v in sorted(hv.items(), key=lambda kv: -kv[1])))
    return L


def md_card(C, depth):
    L = ["- **Front and coverage — CARD vs DATA (CFBD has no alignment or coverage tags; the card is the July description, the data is what the numbers imply)**"]
    L.append(f"  - CARD (offense, {C.get('vintage', '')}): {C.get('ob', 'no card')}")
    L.append(f"    - CARD trend: {C.get('ot', '')}")
    L.append(f"  - CARD (defense): {C.get('db', 'no card')}")
    L.append(f"    - CARD trend: {C.get('dt', '')}")
    L.append(f"  - CARD (depth chart labels): offense {depth.get('off_scheme')}, defense {depth.get('def_scheme')} (OurLads {depth.get('updated')})")
    return L


def data_reads(D):
    """DATA lines: what the numbers imply about the look, worded as inference."""
    o, d = D["offense"], D["defense"]
    L = ["  - DATA (offense): "
         + ("almost all shotgun" if (o['formation']['shotgun_pct'] or 0) >= 90 else ("shotgun-based" if (o['formation']['shotgun_pct'] or 0) >= 70 else "mixes under center in"))
         + f" ({fmt(o['formation']['shotgun_pct'], '%')}), "
         + ("tempo team" if (o['formation']['no_huddle_pct'] or 0) >= 60 else ("some tempo" if (o['formation']['no_huddle_pct'] or 0) >= 30 else "huddles"))
         + f" ({fmt(o['formation']['no_huddle_pct'], '%')} no-huddle, median {fmt(o['tempo']['median'])} s between snaps); "
         + f"deep-tag rate {fmt(o['targets']['deep_pct'], '%')}; run rate on 1st down {fmt((o['by_down_distance'].get('1st') or {}).get('run_pct'), '%')}"]
    L.append("  - DATA (defense): "
             + f"sack rate {fmt(d['summary']['sack_pct'], '%')}, stuff rate {fmt(d['summary']['stuff_pct'], '%')}, explosive passes allowed {fmt(d['summary']['p20_pct'], '%')} of dropbacks; "
             + f"deep-tag rate opponents take {fmt(d['targets']['deep_pct'], '%')} — "
             + ("a high deep rate against it is consistent with man/press looks or a front that forces quick shots" if (d['targets']['deep_pct'] or 0) >= 16 else "opponents are not taking many shots downfield")
             + ". Coverage itself cannot be read from CFBD; this is inference.")
    return L


def to_markdown(D):
    team, wk = D["team"], D["through_week"]
    L = [f"# {team} — scheme & tendency dossier through Week {wk - 1} (built {D['generated']})", "",
         "Outline notes: topic → the points → the facts. INTERNAL. Sources: CFBD play-by-play (formation, tempo, depth tags, "
         "target names), box score (rushing totals), per-player game box (participation, hurries), OurLads depth chart, "
         "scouting card (fronts/coverages = CARD lines). Per attempt = completions only; stuff / 10+ / explosive = play-by-play. "
         "Numbers in this file are one team's season to date; the national rank in brackets is from the Team Stats sheet.", ""]
    L.append("- **Results**")
    for g in D["games"]:
        o, d = g["offense"], g["defense"]
        L.append(f"  - {g['label']} ({g['opp_class']}), {g['date']}: {g['result']}")
        L.append(f"    - Offense: {o['comp']}-of-{o['att']} for {o['pass_yds']} ({fmt(o['ypa'])} / {fmt(o['ypc'])}), 20+ {o['p20']}, sacked {o['sacks']}; rush (box) {o['box_att']}-{o['box_yds']} ({fmt(o['box_ypc'])}); shotgun {fmt(o['formation']['shotgun_pct'], '%')}, no-huddle {fmt(o['formation']['no_huddle_pct'], '%')}, median {fmt(o['tempo']['median'])} s/snap")
        L.append(f"    - Defense: allowed {d['comp']}-of-{d['att']} for {d['pass_yds']} ({fmt(d['ypa'])}), 20+ {d['p20']}, sacks {d['sacks']}; rush (box) {d['box_att']}-{d['box_yds']} ({fmt(d['box_ypc'])}), stuffs {d['stuffs']}")
    L.append("")
    L += md_card(D["card"], D["depth"]) + data_reads(D)
    L.append("")
    L += md_side(D["offense"], "offense", D["stats"], team, "opponents")
    L.append("")
    L += md_side(D["defense"], "defense", D["stats"], team, "opponents")
    L.append("")
    L += md_personnel(D["personnel"])
    L.append("")
    L.append("- **What to watch for — five plays to find on film (game, quarter, clock)**")
    for w in D["watch"]:
        L.append(f"  - {w['side']}: {w['game']}, {w['clock']} — {w['yards']} yds, PPA {w['ppa']:+.2f} — {w['text']}")
    return "\n".join(L) + "\n"


# ----------------------------------------------------------------- split
def parse_split(s, games):
    """'after 1' / 'before/after week 1' / 'after 2026-09-06' -> (label, is_after(game))."""
    tok = s.strip().split()[-1]
    if re.match(r"^\d{4}-\d{2}-\d{2}$", tok):
        return f"after {tok}", lambda g: g["startDate"][:10] > tok
    w = int(re.sub(r"\D", "", tok))
    return f"after week {w}", lambda g: g["week"] > w


def split_row(name, a, b, k, suffix="", n_a=None, n_b=None):
    va, vb = a.get(k), b.get(k)
    d = (round(vb - va, 1) if isinstance(va, (int, float)) and isinstance(vb, (int, float)) else None)
    return f"| {name} | {fmt(va, suffix)} | {fmt(vb, suffix)} | {fmt(d, suffix) if d is not None else ''} |"


def md_split(team, through_week, label, before, after, missing, P_before, P_after, C):
    """before / after = dossiers built on the two game subsets."""
    bd, ad = before["defense"], after["defense"]
    bs, as_ = bd["summary"], ad["summary"]
    L = [f"# {team} — situation study: defense before vs {label} (through Week {through_week - 1})", "",
         "INTERNAL. Every defensive number split on the change; the replacements from the participation proxy; then a short read that keeps "
         "'what the data shows' apart from 'what the card / film says'. Same conventions as the dossier.", ""]
    L.append("- **The split**")
    L.append(f"  - Before: " + "; ".join(f"{g['label']} {g['result']}" for g in before["games"]) + f" — {bs['plays']} defensive plays, {bs['dropbacks']} dropbacks")
    L.append(f"  - After: " + "; ".join(f"{g['label']} {g['result']}" for g in after["games"]) + f" — {as_['plays']} defensive plays, {as_['dropbacks']} dropbacks")
    if bs["dropbacks"] < SPLIT_MIN or as_["dropbacks"] < SPLIT_MIN:
        L.append(f"  - SAMPLE WARNING: one side has fewer than {SPLIT_MIN} dropbacks. Differences below are descriptions, not conclusions.")
    if missing:
        L.append("- **The missing players — where the box last saw them**")
        for nm in missing:
            hits = [r for r in P_before["players"] + P_after["players"] if same_person(r["name"], nm)]
            seen = {}
            for h in hits:
                seen.update(h["by_game"])
            slot = next((s["slot"] for s in P_before["starters"] if same_person(s["name"], nm)), None)
            L.append(f"  - {nm}" + (f" (depth chart {slot})" if slot else "") + ": " + ("; ".join(f"{g}: {v}" for g, v in seen.items()) if seen else "no stat in any box this season"))
            for g in before["games"] + after["games"]:
                if g["label"] not in seen:
                    L.append(f"    - {g['label']}: not in the box (no tackle, PD or INT — absent, or played without a stat)")
    L.append("- **Passing allowed, before vs after**")
    L += ["  | | before | after | change |", "  |---|---|---|---|",
          "  " + split_row("Dropbacks faced", bs, as_, "dropbacks"), "  " + split_row("Per attempt (completions only)", bs, as_, "ypa"),
          "  " + split_row("Per completion", bs, as_, "ypc"), "  " + split_row("Explosive passes allowed, % of dropbacks", bs, as_, "p20_pct", "%"),
          "  " + split_row("Sack rate", bs, as_, "sack_pct", "%"), "  " + split_row("Interceptions", bs, as_, "ints"),
          "  " + split_row("Deep-tag share of throws faced", bd["targets"], ad["targets"], "deep_pct", "%")]
    L.append("  - Completions by yards gained (0-9 / 10-19 / 20+): before "
             + " / ".join(str(bd['targets']['completion_bins'].get(k, 0)) for k in ("0-9", "10-19", "20+")) + "; after "
             + " / ".join(str(ad['targets']['completion_bins'].get(k, 0)) for k in ("0-9", "10-19", "20+")))
    L.append("  - Where opponents threw (depth + direction tags): before " + ", ".join(f"{k} {v}" for k, v in list(bd['targets']['by_direction'].items())[:6])
             + "; after " + ", ".join(f"{k} {v}" for k, v in list(ad['targets']['by_direction'].items())[:6]))
    L.append("- **Explosive passes allowed (20+), each one**")
    for lab, E in (("before", bd["explosives"]), ("after", ad["explosives"])):
        rows = [r for r in E["plays"] if r["kind"] == "pass"]
        L.append(f"  - {lab}: {len(rows)}")
        for r in rows:
            L.append(f"    - {r['game']}, {r['clock']}: {r['yards']} yds ({r['tag']}) — {r['text']}")
    tb, ta = bd["third_long"].get("3rd & 6+", {}), ad["third_long"].get("3rd & 6+", {})
    L.append(f"- **Third-and-long allowed**: before {tb.get('conv', 'n/a')} converted (deep {fmt(tb.get('deep_pct'), '%')}, sack {fmt(tb.get('sack_pct'), '%')}); after {ta.get('conv', 'n/a')} (deep {fmt(ta.get('deep_pct'), '%')}, sack {fmt(ta.get('sack_pct'), '%')})")
    L.append("- **Run defense, before vs after (box score totals; stuff rate pbp)**")
    L += ["  | | before | after | change |", "  |---|---|---|---|",
          "  " + split_row("Carries allowed (box)", bs, as_, "box_att"), "  " + split_row("Per carry (box)", bs, as_, "box_ypc"),
          "  " + split_row("Stuff rate", bs, as_, "stuff_pct", "%"), "  " + split_row("10+ runs, % of pbp runs", bs, as_, "r10_pct", "%")]
    L.append("- **Sacks and hurries by down**")
    for lab, S in (("before", bd["sacks_by_down"]), ("after", ad["sacks_by_down"])):
        L.append(f"  - {lab}: " + " · ".join(f"down {k}: {v['sacks']} sacks in {v['dropbacks']} ({fmt(v['sack_pct'], '%')})" for k, v in S.items()))
    for lab, P in (("before", P_before), ("after", P_after)):
        tot = collections.Counter()
        for g, hv in P["hurries"].items():
            for k, v in hv.items():
                tot[k] += v
        L.append(f"  - hurries credited {lab} (player box): " + (", ".join(f"{k} {v}" for k, v in tot.most_common(6)) or "none credited"))
    L.append("- **Who is making the tackles in the secondary (DB rows of the player box)**")
    for lab, P in (("before", P_before), ("after", P_after)):
        L.append(f"  - {lab}")
        for r in [r for r in P["players"] if r["pos"] == "DB"]:
            L.append(f"    - {r['name']} ({r['games']} g): " + " · ".join(f"{g}: {v}" for g, v in r["by_game"].items()))
    new = [r["name"] for r in P_after["players"] if r["pos"] == "DB" and not any(same_person(r["name"], x["name"]) for x in P_before["players"])]
    gone = [r["name"] for r in P_before["players"] if r["pos"] == "DB" and not any(same_person(r["name"], x["name"]) for x in P_after["players"])]
    L.append(f"  - DBs in the box after but not before: {', '.join(new) or 'none'}; before but not after: {', '.join(gone) or 'none'}")
    # the read
    L.append("- **The read**")
    L.append("  - What the data shows")
    dy = (as_["ypa"] or 0) - (bs["ypa"] or 0)
    dp = (as_["p20_pct"] or 0) - (bs["p20_pct"] or 0)
    L.append(f"    - Per-attempt allowed moved {dy:+.1f} ({fmt(bs['ypa'])} → {fmt(as_['ypa'])}); explosive-pass rate moved {dp:+.1f} points ({fmt(bs['p20_pct'], '%')} → {fmt(as_['p20_pct'], '%')}); deep-tag share of throws faced {fmt(bd['targets']['deep_pct'], '%')} → {fmt(ad['targets']['deep_pct'], '%')}")
    L.append(f"    - Sack rate {fmt(bs['sack_pct'], '%')} → {fmt(as_['sack_pct'], '%')}; third-and-long conversions {tb.get('conv', 'n/a')} → {ta.get('conv', 'n/a')}")
    L.append(f"    - Replacements by the proxy: {', '.join(new) or 'no new DB names'}" + (f"; missing from the after games: {', '.join(gone)}" if gone else ""))
    if bs["dropbacks"] < SPLIT_MIN or as_["dropbacks"] < SPLIT_MIN:
        L.append(f"    - The sample is too small to call a scheme change: {bs['dropbacks']} vs {as_['dropbacks']} dropbacks. One game swings every rate here.")
    else:
        L.append("    - Opponent quality differs between the halves (see the results); the split does not adjust for it.")
    L.append("  - What the data cannot see")
    L.append("    - Coverage calls, alignment, press vs off, safety rotation, who was in man on the explosive plays — none of it is in CFBD. Whether a corner was beaten or a safety was late is a film question.")
    L.append("    - Snap counts: the player box only lists players who recorded a stat.")
    L.append("  - What the card says (July description, not this month's film)")
    L.append(f"    - CARD: {C.get('db', 'no card')}")
    L.append(f"    - CARD trend: {C.get('dt', '')}")
    L.append("  - Plays to watch (after the change): the explosive passes listed above, in order, plus the third-and-long conversions")
    return "\n".join(L) + "\n"


# ----------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--team")
    ap.add_argument("--teams")
    ap.add_argument("--week", type=int, required=True, help="the week being previewed (games before it)")
    ap.add_argument("--split", help='"after 1" | "before/after week 2" | "after 2026-09-06"')
    ap.add_argument("--missing", help="comma-separated player names to trace through the box")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    load_env_key()
    os.makedirs(OUT, exist_ok=True)
    teams = [t.strip() for t in (a.teams or a.team or "").split(",") if t.strip()]
    if not teams:
        ap.error("--team or --teams")
    for team in teams:
        D = build(team, a.week, a.refresh)
        slug = re.sub(r"[^A-Za-z0-9]+", "_", team).strip("_")
        md = os.path.join(OUT, f"{slug}_week{a.week}.md")
        with open(md, "w", encoding="utf-8") as f:
            f.write(to_markdown(D))
        with open(os.path.join(OUT, f"{slug}_week{a.week}.json"), "w", encoding="utf-8") as f:
            json.dump(D, f, indent=1, default=str)
        print(f"wrote {md}  ({len(D['games'])} games, {D['offense']['summary']['plays']} off / {D['defense']['summary']['plays']} def plays)")
        if a.split:
            games = team_games(team, a.week)
            label, is_after = parse_split(a.split, games)
            before = build(team, a.week, a.refresh, [g for g in games if not is_after(g)])
            after = build(team, a.week, a.refresh, [g for g in games if is_after(g)])
            missing = [m.strip() for m in (a.missing or "").split(",") if m.strip()]
            sp = os.path.join(OUT, f"{slug}_week{a.week}_split.md")
            with open(sp, "w", encoding="utf-8") as f:
                f.write(md_split(team, a.week, label, before, after, missing, before["personnel"], after["personnel"], D["card"]))
            print(f"wrote {sp}")


if __name__ == "__main__":
    main()
