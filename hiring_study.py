"""Hiring-history study (INTERNAL, Lucas 10/4/2026) - prep for the "who replaces him" segment.

Every FBS head-coach hire 2010-2023 from CFBD /coaches (head coaches only - coordinators are not in the data).
SOURCE of the hire  sitting FBS head coach (HC of another FBS school the year before) / former FBS head coach /
                    first-time FBS head coach (coordinator, FCS or NFL - cannot be told apart here).
OUTCOME             lift = the program's SRS in the coach's years 2-3 minus its SRS in the two years before he
                    arrived (year 1 is skipped: it is the old roster); also "still there in year 4".
QUESTION 1          which source wins, at power-conference jobs and elsewhere.
QUESTION 2          for sitting head coaches: does what he did at the old job predict the lift? Features: his
                    last two seasons' SRS there minus that school's SRS in the two years before HIM (the lift he
                    produced), his last-season win pct, years there, and how big the step up is (new program's
                    ten-year SRS minus the old one's). Fit hires 2010-2018, test 2019-2023.
THEN                the 2026 candidate board: every sitting FBS head coach outside the power conferences, ranked by
                    the fitted profile -> internal/candidate_board_2026.json.

    python hiring_study.py
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / "fpi-decomposition"))
from refresh_all import load_env_key  # noqa: E402
load_env_key()
import cfbd_client as cfbd  # noqa: E402

NOW = 2026
POWER = {"SEC", "Big Ten", "Big 12", "ACC", "Pac-12", "Pac-10", "Big East"}


def is_power(conf, school, year):
    if school == "Notre Dame":
        return True
    if conf in ("Pac-12", "Pac-10"):
        return year <= 2023
    if conf == "Big East":
        return year <= 2012
    return conf in POWER


def table():
    """T[(school, year)] = dict(coach, wins, losses, srs, conf); H[coach] = sorted [(year, school)]"""
    by = defaultdict(list)
    for c in cfbd.get("/coaches", {"minYear": 1990, "maxYear": NOW}, True):
        name = f"{c['firstName']} {c['lastName']}"
        for s in c["seasons"]:
            by[(s["school"], s["year"])].append((s.get("games") or 0, name, s))
    T, H = {}, defaultdict(list)
    for (school, y), v in by.items():
        g, name, s = max(v, key=lambda x: x[0])
        T[(school, y)] = dict(coach=name, wins=s.get("wins") or 0, losses=s.get("losses") or 0, srs=s.get("srs"), conf=s.get("conference"))
        H[name].append((y, school))
    for n in H:
        H[n].sort()
    return T, H


def srs_avg(T, school, years):
    v = [T[(school, y)]["srs"] for y in years if (school, y) in T and T[(school, y)]["srs"] is not None]
    return float(np.mean(v)) if v else None


def hires(T, H, first=2010, last=NOW):
    out = []
    for (school, y), v in T.items():
        if not first <= y <= last or (school, y - 1) not in T or T[(school, y - 1)]["coach"] == v["coach"]:
            continue
        c = v["coach"]
        prior = [(yy, s) for yy, s in H[c] if yy < y and s != school]
        back = any(s == school for yy, s in H[c] if yy < y - 1)             # a returning coach / interim made permanent
        if any(yy == y - 1 for yy, s in prior):
            src, old = "sitting FBS head coach", [s for yy, s in prior if yy == y - 1][0]
        elif prior:
            src, old = "former FBS head coach", prior[-1][1]
        else:
            src, old = "first-time FBS head coach", None
        yrs = 0
        while T.get((school, y + yrs), {}).get("coach") == c:
            yrs += 1
        before = srs_avg(T, school, (y - 1, y - 2)); after = srs_avg(T, school, (y + 1, y + 2)) if yrs >= 3 else None
        row = dict(year=y, school=school, coach=c, src=src, old=old, power=is_power(v["conf"], school, y), back=back,
                   years=yrs, before=before, lift=(after - before) if after is not None and before is not None else None,
                   y4=(yrs >= 4) if y + 3 <= NOW else None)
        if src == "sitting FBS head coach":
            t0 = y - 1
            while T.get((old, t0 - 1), {}).get("coach") == c:
                t0 -= 1
            o_last = srs_avg(T, old, (y - 1, y - 2) if t0 <= y - 2 else (y - 1,))
            o_before = srs_avg(T, old, (t0 - 1, t0 - 2))
            ten_new = srs_avg(T, school, range(y - 10, y)); ten_old = srs_avg(T, old, range(y - 10, y))
            lw = T[(old, y - 1)]
            row.update(old_years=y - t0, old_power=is_power(T[(old, y - 1)]["conf"], old, y - 1),
                       built=(o_last - o_before) if o_last is not None and o_before is not None else None,
                       old_srs=o_last, last_wp=lw["wins"] / max(lw["wins"] + lw["losses"], 1),
                       step=(ten_new - ten_old) if ten_new is not None and ten_old is not None else None)
        out.append(row)
    return out


def ols(X, y):
    Xb = np.column_stack([np.ones(len(X)), X]); b, *_ = np.linalg.lstsq(Xb, y, rcond=None)
    r = y - Xb @ b; s2 = r @ r / max(len(y) - Xb.shape[1], 1)
    return b, np.sqrt(np.diag(s2 * np.linalg.inv(Xb.T @ Xb)))


def main():
    T, H = table()
    hs = [h for h in hires(T, H) if not h["back"]]
    out = []; P = out.append
    done = [h for h in hs if h["year"] <= 2023]
    P("# Hiring-history study (INTERNAL, Sun Oct 4 2026)\n")
    P(f"{len(done)} FBS head-coach hires 2010-2023 (returning coaches and promoted interims with an earlier stint dropped). "
      "Lift = program SRS in the coach's years 2-3 minus the two years before he arrived (points per game vs an average team). "
      "Head coaches only: a 'first-time FBS head coach' is a coordinator, an FCS coach or an NFL coach - this data cannot say which.\n")
    P("## Where hires come from, and how they did\n\n| job | source | hires | share | lift (mean) | se | lift > 0 | reached year 4 |\n|---|---|--:|--:|--:|--:|--:|--:|")
    for pw, lab in ((True, "power conference"), (False, "everyone else")):
        grp = [h for h in done if h["power"] == pw]
        for src in ("sitting FBS head coach", "former FBS head coach", "first-time FBS head coach"):
            g = [h for h in grp if h["src"] == src]; lf = np.array([h["lift"] for h in g if h["lift"] is not None])
            y4 = [h["y4"] for h in g if h["y4"] is not None]
            P(f"| {lab} | {src} | {len(g)} | {100 * len(g) / max(len(grp), 1):.0f}% | {lf.mean():+.1f} | {lf.std() / np.sqrt(len(lf)):.1f} | "
              f"{100 * np.mean(lf > 0):.0f}% of {len(lf)} | {100 * np.mean(y4):.0f}% |")
    sit = [h for h in done if h["src"] == "sitting FBS head coach"]
    P("\n## Sitting head coaches hired to power jobs: where from\n")
    pj = [h for h in sit if h["power"]]
    P(f"{len(pj)} hires: {sum(not h['old_power'] for h in pj)} came from outside the power conferences, {sum(h['old_power'] for h in pj)} from another power job. "
      f"Median years at the old job {np.median([h['old_years'] for h in pj]):.0f}; median last-season win pct {100 * np.median([h['last_wp'] for h in pj]):.0f}%; "
      f"median SRS at the old job {np.median([h['old_srs'] for h in pj if h['old_srs'] is not None]):+.1f}.\n")
    P("## Does the old job predict the new one? (sitting head coaches, all jobs)\n")
    F = ["built", "old_srs", "last_wp", "old_years", "step", "before"]
    ok = [h for h in sit if h["lift"] is not None and all(h.get(f) is not None for f in F)]
    tr = [h for h in ok if h["year"] <= 2018]; te = [h for h in ok if h["year"] > 2018]
    X = lambda rs: np.array([[h[f] for f in F] for h in rs], float)
    b, se = ols(X(tr), np.array([h["lift"] for h in tr]))
    P(f"Fit on {len(tr)} hires 2010-2018, test on {len(te)} hires 2019-2023.\n\n| term | coef | se | meaning |\n|---|--:|--:|---|")
    mean = {"built": "SRS lift he produced at the old job", "old_srs": "how good his last two teams were", "last_wp": "last season's win pct",
            "old_years": "years at the old job", "step": "new program's ten-year level minus the old one's", "before": "how good the new program was before him"}
    P(f"| const | {b[0]:+.2f} | {se[0]:.2f} | |")
    for f, c, s in zip(F, b[1:], se[1:]):
        P(f"| {f} | {c:+.2f} | {s:.2f} | {mean[f]} |")
    yte = np.array([h["lift"] for h in te]); pred = np.column_stack([np.ones(len(te)), X(te)]) @ b
    naive = np.mean([h["lift"] for h in tr])
    b2, _ = ols(X(tr)[:, [5]], np.array([h["lift"] for h in tr])); pred2 = b2[0] + b2[1] * X(te)[:, 5]
    P(f"\nTest (2019-2023 hires), mean absolute error of the predicted lift: every hire gets the average lift {np.mean(np.abs(yte - naive)):.2f} · "
      f"only 'how good the program was before' {np.mean(np.abs(yte - pred2)):.2f} · full profile {np.mean(np.abs(yte - pred)):.2f}. "
      f"Correlation of the full profile with the real lift on the test hires: {np.corrcoef(pred, yte)[0, 1]:+.2f}.\n")
    # ---- 2026 candidate board: sitting HCs outside the power conferences ----
    P("## 2026 candidate board - sitting head coaches outside the power conferences\n")
    P("Ranked by the coach's own part of the fitted profile above (how good his last two teams are, what he built, last season's win pct, years there); "
      "the terms that belong to the new program are left out, so this is 'who travels best', not a fit to any one job. "
      "Built = his program's SRS now minus the two years before he arrived.\n")
    ratings = {t["team"]: t for t in json.loads((HERE / "ratings_current_2026.json").read_text(encoding="utf-8"))["teams"]}
    from name_mapping import normalize_name
    cands = []
    for (school, y), v in T.items():
        if y != NOW or is_power(v["conf"], school, NOW):
            continue
        c = v["coach"]; t0 = NOW
        while T.get((school, t0 - 1), {}).get("coach") == c:
            t0 -= 1
        if NOW - t0 < 1:
            continue                                                    # first-year coaches have built nothing yet
        now_srs = srs_avg(T, school, (NOW, NOW - 1) if t0 <= NOW - 1 else (NOW,)); before = srs_avg(T, school, (t0 - 1, t0 - 2))
        if now_srs is None or before is None:
            continue
        last = T.get((school, NOW - 1)); r = ratings.get(normalize_name(school), {})
        lwp = last["wins"] / max(last["wins"] + last["losses"], 1) if last else 0.5
        travel = b[1] * (now_srs - before) + b[2] * now_srs + b[3] * lwp + b[4] * (NOW - t0 + 1)
        cands.append(dict(travel=round(float(travel), 1), coach=c, school=school, conf=v["conf"], years=NOW - t0 + 1, built=round(now_srs - before, 1), srs=round(now_srs, 1),
                          last=f"{last['wins']}-{last['losses']}" if last else "", rating=r.get("cur"), delta=r.get("delta")))
    cands.sort(key=lambda x: -x["travel"])
    P("| # | coach | school | yr | travel score | built (SRS lift) | SRS now | 2025 | machine rating (vs July) |\n|--:|---|---|--:|--:|--:|--:|---|--:|")
    for k, c in enumerate(cands[:20], 1):
        P(f"| {k} | {c['coach']} | {c['school']} | {c['years']} | {c['travel']:+.1f} | {c['built']:+.1f} | {c['srs']:+.1f} | {c['last']} | {c['rating']} ({c['delta']:+}) |" if c["rating"] is not None
          else f"| {k} | {c['coach']} | {c['school']} | {c['years']} | {c['travel']:+.1f} | {c['built']:+.1f} | {c['srs']:+.1f} | {c['last']} | - |")
    P("\nLimits: coordinators, FCS and NFL coaches are not in the data (they are most first-time hires); no contracts, buyouts, age, ties to a school or who wants the job. "
      "SRS for 2026 is the season to date. 'Built' flatters a coach who inherited a crater and punishes one who inherited a good team.")
    text = "\n".join(out)
    (HERE / "internal" / "HIRING_STUDY_2026.md").write_text(text, encoding="utf-8")
    (HERE / "internal" / "candidate_board_2026.json").write_text(json.dumps(cands, indent=1), encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
