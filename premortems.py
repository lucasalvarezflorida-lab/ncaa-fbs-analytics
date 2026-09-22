"""Pre-mortems the machine grades itself on (Phase 3, 2026-09-22).

For every pick on the card the machine writes ONE pre-mortem:
    "This pick is wrong if ___"
where the blank is a condition checkable from the box score or the
play-by-play after the game, plus one short narrative reason.

HOW THE MACHINE PICKS THE CONDITION
  The card's stat package (stat_package_week{N}.json) gives each team's
  season rates on offense and defense. For the picked team P and the other
  team O, every unit-vs-unit matchup is a candidate:
      O's run game vs P's run defense, O's passing vs P's pass defense
      (yards per attempt, explosive passes), O's third downs vs P's,
      P's passing / rushing vs O's defense, P's pass protection vs O's
      rush, P's ball security vs O's takeaways.
  Each candidate's threshold is the MIDPOINT between what one unit does and
  what the other allows; the condition fires when the game lands on O's side
  of it. The pre-mortem is the candidate with the widest gap between the two
  units (in units of a typical game-to-game spread) - the matchup the two
  track records disagree on most, i.e. the one the pick leans on hardest.
  The next two candidates are stored as alternatives for a hand swap.

STORAGE  premortems.json  {"week": {"Away at Home": {...}}}, condition in
machine-readable form:
    {"team": "Tennessee", "unit": "offense", "stat": "rush_ypc", "op": ">",
     "value": 5.0, "source": "box"}
  team / unit = whose numbers are read (unit "defense" = what that team's
  defense allowed); source "box" = official box score (rushing follows the
  NCAA convention: sacks count), "pbp" = play-by-play (completions-only
  yards per attempt, 20+ completions, sacks, stuffs, third downs).

    python premortems.py --week 4              # write the week's pre-mortems (keeps existing ones)
    python premortems.py --week 4 --force      # regenerate, overwriting hand edits
    python premortems.py --week 4 --show       # print the week

grade_premortems.py checks them after the games. Public material: no market
numbers anywhere in here (the pick is the machine's own line)."""
import argparse, json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)

PM_FILE = os.path.join(HERE, "premortems.json")

# stat -> (label, per-game scale of a typical difference, rounding, higher-is-better-for-the-offense)
STATS = dict(
    rush_ypc=dict(label="yards a carry", scale=1.0, rnd=1, source="box"),
    pass_ypa=dict(label="yards an attempt", scale=1.5, rnd=1, source="pbp"),
    p20=dict(label="completions of 20+", scale=1.2, rnd=0, source="pbp"),
    t3_pct=dict(label="third-down conversion rate", scale=12.0, rnd=0, source="box"),
    sacks_taken=dict(label="sacks taken", scale=1.3, rnd=0, source="box"),
    stuff_rate=dict(label="runs stuffed", scale=7.0, rnd=0, source="pbp"),
    ints_thrown=dict(label="interceptions thrown", scale=0.8, rnd=0, source="box"),
)


def load():
    return json.load(open(PM_FILE, encoding="utf-8")) if os.path.exists(PM_FILE) else {}


def save(d):
    json.dump(d, open(PM_FILE, "w", encoding="utf-8"), indent=1)


def _pct(frac):
    n, d = frac.split("/")
    return 100.0 * int(n) / max(int(d), 1)


def rates(side, gp):
    """Per-game and rate view of one unit's season block from the stat package."""
    return dict(rush_ypc=side["box_ypc"], pass_ypa=side["ypa"], p20_rate=side["p20_rate"],
                dropbacks=side["dropbacks"] / gp, t3_pct=_pct(side["t3"]),
                sack_rate=side["sack_rate"], stuff_rate=side["stuff_rate"],
                ints=side["ints"] / gp, sacks=side["sacks"] / gp)


def blocks(pk):
    """(offense, defense, games, basis): FBS-only numbers when the team has
    played 2+ FBS games (an FCS blowout is not evidence), else the season."""
    n = sum(1 for g in pk["games"] if g["opp_class"] == "fbs")
    if n >= 2:
        return pk["offense_vs_fbs"], pk["defense_vs_fbs"], n, "vs FBS opponents"
    return pk["offense"], pk["defense"], len(pk["games"]), "season"


def candidates(P, O, pkP, pkO):
    """All unit-vs-unit conditions for pick P vs opponent O. Each: the team
    whose game stat is read, the unit, the stat, the operator, the threshold,
    the gap in scale units, and the narrative."""
    Po_, Pd_, gp_P, _ = blocks(pkP)
    Oo_, Od_, gp_O, _ = blocks(pkO)
    Po, Pd = rates(Po_, gp_P), rates(Pd_, gp_P)
    Oo, Od = rates(Oo_, gp_O), rates(Od_, gp_O)
    C = []

    def add(team, unit, stat, op, value, gap, does, allows, text):
        C.append(dict(team=team, unit=unit, stat=stat, op=op, value=value, source=STATS[stat]["source"],
                      gap=round(gap, 2), does=does, allows=allows, text=text))

    # O's offense against P's defense: fires when O beats the midpoint
    mid = (Oo["rush_ypc"] + Pd["rush_ypc"]) / 2
    add(O, "offense", "rush_ypc", ">", round(mid, 1), (Oo["rush_ypc"] - Pd["rush_ypc"]) / STATS["rush_ypc"]["scale"],
        Oo["rush_ypc"], Pd["rush_ypc"],
        f"{O} runs for {Oo['rush_ypc']} a carry against FBS teams and {P} allows {Pd['rush_ypc']}. The pick leans on {P}'s run defense holding; past {mid:.1f} a carry, {O} has won the matchup the machine trusts.")
    mid = (Oo["pass_ypa"] + Pd["pass_ypa"]) / 2
    add(O, "offense", "pass_ypa", ">", round(mid, 1), (Oo["pass_ypa"] - Pd["pass_ypa"]) / STATS["pass_ypa"]["scale"],
        Oo["pass_ypa"], Pd["pass_ypa"],
        f"{O} throws for {Oo['pass_ypa']} an attempt and {P}'s defense allows {Pd['pass_ypa']}. If {O} gets past {mid:.1f} a throw, the passing matchup the machine counts on has flipped.")
    mid_rate = (Oo["p20_rate"] + Pd["p20_rate"]) / 2
    cnt = max(1, math.ceil(mid_rate / 100 * Oo["dropbacks"] - 0.25))
    add(O, "offense", "p20", ">=", cnt, (Oo["p20_rate"] - Pd["p20_rate"]) / 4.0, Oo["p20_rate"], Pd["p20_rate"],
        f"{O} hits a 20+ yard completion on {Oo['p20_rate']:.1f}% of dropbacks; {P} allows one on {Pd['p20_rate']:.1f}%. {cnt} or more explosive passes and {O}'s offense has done what {P}'s defense has not let anyone do.")
    mid = (Oo["t3_pct"] + Pd["t3_pct"]) / 2
    add(O, "offense", "t3_pct", ">", round(mid), (Oo["t3_pct"] - Pd["t3_pct"]) / STATS["t3_pct"]["scale"], round(Oo["t3_pct"]), round(Pd["t3_pct"]),
        f"{O} converts {Oo['t3_pct']:.0f}% of third downs; {P} allows {Pd['t3_pct']:.0f}%. Over {mid:.0f}% and {O} kept the drives alive that the machine expects to end.")
    # P's offense against O's defense: fires when P falls to the midpoint
    mid = (Po["pass_ypa"] + Od["pass_ypa"]) / 2
    add(P, "offense", "pass_ypa", "<", round(mid, 1), (Po["pass_ypa"] - Od["pass_ypa"]) / STATS["pass_ypa"]["scale"], Po["pass_ypa"], Od["pass_ypa"],
        f"{P} throws for {Po['pass_ypa']} an attempt; {O}'s defense allows {Od['pass_ypa']}. Under {mid:.1f} a throw and {P}'s passing game has been held to what {O} usually allows, not what {P} usually does.")
    mid = (Po["rush_ypc"] + Od["rush_ypc"]) / 2
    add(P, "offense", "rush_ypc", "<", round(mid, 1), (Po["rush_ypc"] - Od["rush_ypc"]) / STATS["rush_ypc"]["scale"], Po["rush_ypc"], Od["rush_ypc"],
        f"{P} runs for {Po['rush_ypc']} a carry; {O} allows {Od['rush_ypc']}. Under {mid:.1f} a carry and {O}'s front has taken the run game away from the pick.")
    mid_rate = (Po["sack_rate"] + Od["sack_rate"]) / 2
    cnt = max(1, math.ceil(mid_rate / 100 * Po["dropbacks"] - 0.25))
    add(P, "offense", "sacks_taken", ">=", cnt, (Od["sack_rate"] - Po["sack_rate"]) / 4.0, Od["sack_rate"], Po["sack_rate"],
        f"{O} sacks the quarterback on {Od['sack_rate']:.1f}% of dropbacks; {P} has given one up on {Po['sack_rate']:.1f}%. {cnt} or more sacks and {O}'s rush has beaten the protection the machine assumes.")
    mid = (Po["stuff_rate"] + Od["stuff_rate"]) / 2
    add(P, "offense", "stuff_rate", ">=", round(mid), (Od["stuff_rate"] - Po["stuff_rate"]) / STATS["stuff_rate"]["scale"], round(Od["stuff_rate"]), round(Po["stuff_rate"]),
        f"{O} stuffs {Od['stuff_rate']:.0f}% of runs; {P} gets stuffed on {Po['stuff_rate']:.0f}%. At {mid:.0f}% or more, {P}'s runs are going nowhere and its offense is off schedule.")
    mid = (Po["ints"] + Od["ints"]) / 2
    cnt = max(1, math.ceil(mid - 0.25))
    add(P, "offense", "ints_thrown", ">=", cnt, (Od["ints"] - Po["ints"]) / STATS["ints_thrown"]["scale"], round(Od["ints"], 1), round(Po["ints"], 1),
        f"{O} takes away {Od['ints']:.1f} interceptions a game; {P} throws {Po['ints']:.1f}. {cnt} or more picks and the turnover margin the rating does not model has decided it.")
    return sorted(C, key=lambda c: -abs(c["gap"]))


def condition_text(c):
    lab = STATS[c["stat"]]["label"]
    v = c["value"]
    if c["stat"] in ("rush_ypc", "pass_ypa"):
        word = "more than" if c["op"] == ">" else "under"
        return f"{c['team']} averages {word} {v:.1f} {lab}"
    if c["stat"] == "p20":
        return f"{c['team']} has {int(v)}+ completions of 20 yards or more"
    if c["stat"] == "sacks_taken":
        return f"{c['team']} is sacked {int(v)}+ times"
    if c["stat"] == "ints_thrown":
        return f"{c['team']} throws {'an interception' if int(v) == 1 else str(int(v)) + '+ interceptions'}"
    if c["stat"] == "t3_pct":
        return f"{c['team']} converts more than {int(v)}% on third down"
    if c["stat"] == "stuff_rate":
        return f"{c['team']} is stuffed on {int(v)}% or more of its runs"
    return f"{c['team']} {c['unit']} {c['stat']} {c['op']} {v}"


def card(week):
    """The week's card from score_tracker.json + card_data (frozen if it exists)."""
    rows = [r for r in json.load(open("score_tracker.json", encoding="utf-8")) if r["week"] == week]
    src = f"card_data_week{week}_frozen.json"
    if not os.path.exists(src):
        src = f"card_data_week{week}.json"
    cd = {(g["away"], g["home"]): g for g in json.load(open(src, encoding="utf-8"))["games"]}
    out = []
    for r in rows:
        g = cd.get((r["away"], r["home"]))
        if not g:
            print("no card data for", r["game"]); continue
        m = g["model_margin"]
        pick = r["home"] if m > 0 else r["away"]
        out.append(dict(game=r["game"], away=r["away"], home=r["home"], game_id=g["game_id"], model_margin=m,
                        pick=pick, p_pick=(g["model_p_home"] if m > 0 else 1 - g["model_p_home"]),
                        machine_call=r.get("machine")))
    return out


def build(week, force=False):
    pk = {p["team"]: p for p in json.load(open(f"stat_package_week{week}.json", encoding="utf-8"))}
    pms = load()
    wk = pms.setdefault(str(week), {})
    for g in card(week):
        if g["game"] in wk and not force:
            print("kept:", g["game"]); continue
        P, O = g["pick"], (g["away"] if g["pick"] == g["home"] else g["home"])
        if P not in pk or O not in pk:
            print("no stat package for", g["game"]); continue
        C = candidates(P, O, pk[P], pk[O])
        top = C[0]
        wk[g["game"]] = dict(
            game_id=g["game_id"], away=g["away"], home=g["home"], pick=P, machine_margin=g["model_margin"],
            basis=blocks(pk[P])[3],
            p_pick=round(g["p_pick"], 3), machine_call=g["machine_call"],
            condition={k: top[k] for k in ("team", "unit", "stat", "op", "value", "source")},
            text=condition_text(top), why=top["text"], evidence=dict(does=top["does"], allows=top["allows"], gap=top["gap"]),
            alternatives=[dict(condition={k: c[k] for k in ("team", "unit", "stat", "op", "value", "source")},
                               text=condition_text(c), gap=c["gap"]) for c in C[1:3]],
            result=None)
        print(f"{g['game']:26s} pick {P:14s} wrong if {wk[g['game']]['text']}  (gap {top['gap']:+.2f})")
    save(pms)
    return wk


def show(week):
    wk = load().get(str(week), {})
    for game, p in wk.items():
        r = p.get("result")
        print(f"\n{game} - pick {p['pick']} ({100 * p['p_pick']:.0f}%)")
        print(f"  Wrong if: {p['text']}")
        print(f"  Why: {p['why']}")
        if r:
            print(f"  RESULT: fired={r['fired']} ({r['observed']}) pick lost={r['pick_lost']} -> {r['verdict']}")
        for a in p.get("alternatives", []):
            print(f"  alt: {a['text']} (gap {a['gap']:+.2f})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    if a.show:
        show(a.week)
    else:
        build(a.week, a.force)
        print(f"\nwrote {os.path.basename(PM_FILE)} (week {a.week})")
