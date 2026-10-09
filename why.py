"""why.py - ONE source for the machine's "why" sentences (Lucas 10/9: notes, slide and the page kept
drifting because each wrote its own).

Everything comes from tape_data_2026.json (tape_data.py - the on-air rating, the efficiency shadow's
unit split, team stats with ranks, graded game logs, the margin curve). Same rules as the JavaScript in
tape_template.html; when one changes, change the other (there is no Node on this PC to share code).

    python why.py "Texas A&M" "Missouri" --site B        # A at B (B hosts); --site A / N
    from why import matchup; w = matchup("Texas A&M", "Missouri", "B"); w["honesty"]

Returns a dict: margin (A minus B), p_a, call, read, number, plays, tape, resume, honesty (number + plays,
the notes' honesty draft). No market numbers anywhere.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

DATA = HERE / "tape_data_2026.json"
_D = None


def data() -> dict:
    global _D
    if _D is None:
        _D = json.loads(DATA.read_text(encoding="utf-8"))
    return _D


def team(name: str) -> dict:
    d = data()
    k = normalize_name(name)
    if k in d["teams"]:
        return d["teams"][k]
    hit = next((t for t in d["teams"].values() if t["name"].lower() == name.lower()), None)
    if hit is None:
        raise KeyError(f"no rated team named {name!r}")
    return hit


def win_prob(m: float) -> float:
    c = data()["curve"]
    if m <= c[0][0]:
        return c[0][1]
    if m >= c[-1][0]:
        return c[-1][1]
    lo, hi = 0, len(c) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if c[mid][0] <= m:
            lo = mid
        else:
            hi = mid
    t = (m - c[lo][0]) / (c[hi][0] - c[lo][0])
    return c[lo][1] + t * (c[hi][1] - c[lo][1])


def f1(x: float) -> str:
    return f"{x:.1f}"


def sg(x: float) -> str:
    return f"{x:+.1f}"


def matchup(a_name: str, b_name: str, site: str = "B") -> dict:
    """site: 'A' (A hosts), 'N' (neutral), 'B' (B hosts). Margin is A minus B."""
    d = data(); rule = d["rule"]; hfa = rule["hfa"]; lam = rule["lam"]
    A, B = team(a_name), team(b_name)
    site = site.upper()[0]
    h = hfa if site == "A" else (-hfa if site == "B" else 0.0)
    m = A["now"] - B["now"] + h
    p_a = 1 - win_prob(-m) if site == "B" else win_prob(m)
    fav, dog = (A, B) if m >= 0 else (B, A)
    am, gap = abs(m), abs(A["now"] - B["now"])
    out = dict(a=A["name"], b=B["name"], site=site, margin=round(m, 1), p_a=round(p_a, 3),
               call=f"{fav['name']} by {f1(am)}")

    # the read (verdict line)
    if am < 1:
        read = f"A coin flip: the ratings are {f1(gap)} apart and " + ("there is no home field to break it." if site == "N" else "home field all but cancels the gap.")
    elif gap < hfa and site != "N":
        read = f"{fav['name']} by {f1(am)}: the two are {f1(gap)} apart on the ratings, so home field ({hfa:g}) is most of the call."
    else:
        tail = "" if site == "N" else (f" plus {hfa:g} for the home field" if (h > 0) == (fav is A) else f" less {hfa:g} for playing on the road")
        read = f"{fav['name']} by {f1(am)}: a {f1(gap)}-point gap in the ratings{tail}."
    out["read"] = read

    # the number
    jg = A["july"] - B["july"]; jfav = A if jg >= 0 else B
    number = (f"In July the machine had {jfav['name']} ahead by {f1(abs(jg))}; since then {A['name']} {sg(A['delta'])}, {B['name']} {sg(B['delta'])}"
              f" (the July number is worth {lam:g} games of evidence, so after {A['rated_gp']} and {B['rated_gp']} rated games it still carries a share).")
    if A.get("qb_out") or B.get("qb_out"):
        t = A if A.get("qb_out") else B
        number += f" {t['name']} is carrying a QB-out adjustment of {f1(t['qb_out'])} points."
    out["number"] = number

    # the plays
    plays = ""
    if A.get("eff") and B.get("eff"):
        ea, eb = A["eff"], B["eff"]
        aoff, boff = ea["off"] - eb["def_"], eb["off"] - ea["def_"]
        em = aoff - boff + (ea["st"] - eb["st"]) + h
        dis = em - m
        efav = A if em >= 0 else B
        out.update(plays_margin=round(em, 1), blend=round(0.5 * (m + em), 1))
        plays = "Play by play (PPA and success rate, garbage time out) "
        if abs(dis) < 1.5:
            plays += f"agrees with the machine within a point: {efav['name']} by {f1(abs(em))}."
        elif (em >= 0) == (m >= 0):
            plays += f"sides with {efav['name']} {'harder' if abs(em) > am else 'less'} than the scoreboard does: {f1(abs(em))} against the machine's {f1(am)}."
        else:
            plays += f"leans the other way: {efav['name']} by {f1(abs(em))} against the machine's {fav['name']} by {f1(am)}."
        if abs(aoff) >= abs(boff):
            o, dd, v = (A, B, aoff) if aoff >= 0 else (B, A, aoff)
            unit = f"{A['name']}'s offense against {B['name']}'s defense" if aoff >= 0 else f"{B['name']}'s defense against {A['name']}'s offense"
            big = abs(aoff)
        else:
            unit = f"{B['name']}'s offense against {A['name']}'s defense" if boff >= 0 else f"{A['name']}'s defense against {B['name']}'s offense"
            big = abs(boff)
        plays += f" The biggest unit edge is {unit} ({f1(big)} a game)."
        bl = out["blend"]; bfav = A if bl >= 0 else B
        plays += f" The 50/50 blend of the machine and the plays is {bfav['name']} by {f1(abs(bl))}."
        if abs(dis) >= 3 and A["rank"] <= 40 and B["rank"] <= 40 and am <= 14:
            plays += " This is an A&M-type gap: on close games between top-40 teams the final has landed about halfway from the machine toward the plays' number (2022-26), so the blend is the number to argue about."
    out["plays"] = plays

    # the tape
    tape = ""
    if A.get("stats") and B.get("stats"):
        def edges(O, Dd):
            eO = eD = 0
            for k, _lab, _hi in d["stat_keys"]:
                orK, drK = O["stats"]["off"].get(k + "_rk"), Dd["stats"]["def_"].get(k + "_rk")
                if orK is None or drK is None or orK == drK:
                    continue
                if orK < drK:
                    eO += 1
                else:
                    eD += 1
            return eO, eD
        e1, e2 = edges(A, B), edges(B, A)
        a_e, b_e = e1[0] + e2[1], e1[1] + e2[0]
        tape = f"On the season rates with FBS ranks, the better-ranked unit takes the row: {A['name']} {a_e}, {B['name']} {b_e}. "
        if a_e == b_e or ((a_e > b_e) == (m >= 0)):
            tape += "The tape and the number point the same way."
        else:
            tape += f"The tape leans {A['name'] if a_e > b_e else B['name']} while the number says {fav['name']}; the number weighs who the stats came against, the tape does not."
    out["tape"] = tape

    # the resume
    ra = [g for g in A["games"] if g["rated"]]; rb = [g for g in B["games"] if g["rated"]]
    sa, sb = sum(g["resid"] for g in ra), sum(g["resid"] for g in rb)
    resume = (f"{A['name']} has {'beaten' if sa >= 0 else 'fallen short of'} expectation by {f1(abs(sa))} points over {len(ra)} rated games; "
              f"{B['name']} by {f1(abs(sb))} ({'ahead' if sb >= 0 else 'short'}).")
    for T, rows in ((A, ra), (B, rb)):
        if rows:
            best = max(rows, key=lambda g: g["resid"]); worst = min(rows, key=lambda g: g["resid"])
            luck = sum(g["to"] for g in rows) * rule["to_pts"]
            resume += f" {T['name']}: best grade {best['opp']} ({sg(best['resid'])}), worst {worst['opp']} ({sg(worst['resid'])}), turnover luck {sg(luck)}."
    out["resume"] = resume
    out["honesty"] = (number + (" " + plays if plays else "")).strip()
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("a"); ap.add_argument("b")
    ap.add_argument("--site", default="B", help="A = first team hosts, B = second team hosts, N = neutral")
    ap.add_argument("--json", action="store_true")
    x = ap.parse_args()
    w = matchup(x.a, x.b, x.site)
    if x.json:
        print(json.dumps(w, indent=1))
    else:
        print(f"{w['call']} ({100 * (w['p_a'] if w['margin'] >= 0 else 1 - w['p_a']):.0f}%)  margin A-B {w['margin']:+.1f}")
        for k in ("read", "number", "plays", "tape", "resume"):
            if w[k]:
                print(f"\n{k.upper()}: {w[k]}")
