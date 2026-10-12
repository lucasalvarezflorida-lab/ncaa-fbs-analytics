"""board_data.py - the data file behind "The Board" (board/index.html): the machine's Top 25 and the
whole FBS table, this week's movers, the playoff picture and each team's week-by-week rank.

Built from what the Sunday run already produces (Lucas 10/11: "replace what you read out of a
terminal log every week"):
  * tape_data_2026.json          every rated team: rating, July prior, delta, rank, record, QB-out, the
                                 efficiency shadow's total and rank, colours and an embedded logo
  * inseason_ratings.weekly_change  this week's move (results only, never a rule change)
  * internal/playoff_sim_weekN.json (latest)  playoff / conference title / national title odds
  * CFBD /rankings (cache)       the AP poll, when it is posted
  * rank history                 the on-air rule re-solved after each completed week (no QB-out layer,
                                 so the line shows results; the current week's point is the live number)

NO MARKET NUMBERS - the page is a presentable thing. Nothing here changes the on-air number.

    python board_data.py           # -> board_data_2026.json
    python board.py                # -> board/index.html (template + data)
"""
from __future__ import annotations

import datetime as dt
import glob
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))
import inseason_ratings as ir  # noqa: E402

OUT = HERE / "board_data_2026.json"
TAPE = HERE / "tape_data_2026.json"


def latest_playoff() -> dict:
    files = sorted(glob.glob(str(HERE / "internal" / "playoff_sim_week*.json")), key=lambda p: int(p.rsplit("week", 1)[1].split(".")[0]))
    if not files:
        return {}
    d = json.loads(Path(files[-1]).read_text(encoding="utf-8"))
    rows = d["teams"] if isinstance(d["teams"], list) else [dict(team=k, **v) for k, v in d["teams"].items()]
    return dict(week=d.get("week"), sims=d.get("sims"), teams={r["team"]: r for r in rows})


def rank_history(prior: dict, games: list[dict]) -> dict[str, list[int | None]]:
    """{team: [rank after week 1, after week 2, ...]} under the on-air rule, results only."""
    weeks = sorted({g["week"] or 0 for g in games})
    last = ir.latest_full_week(games)
    weeks = [w for w in weeks if w <= last]
    hist: dict[str, list] = {t: [] for t in prior}
    for w in weeks:
        r = ir.solve_2026(prior, [g for g in games if (g["week"] or 0) <= w])
        order = sorted(r, key=lambda t: -r[t])
        rk = {t: i + 1 for i, t in enumerate(order)}
        for t in prior:
            hist[t].append(rk[t])
    return dict(weeks=weeks, ranks=hist)


def build() -> dict:
    from refresh_all import load_fpi_2026
    prior = load_fpi_2026()
    tape = json.loads(TAPE.read_text(encoding="utf-8"))
    games = [g for g in ir.completed_games_2026() if g["home"] in prior and g["away"] in prior]
    wc = ir.weekly_change(prior)
    po = latest_playoff()
    try:
        rk = ir.latest_rankings(refresh=False)
    except Exception:  # noqa: BLE001
        rk = dict(week=None, ap={})
    hist = rank_history(prior, games)
    through = ir.latest_full_week(games)

    teams = []
    for key, t in tape["teams"].items():
        w = wc["teams"].get(key, {})
        p = po.get("teams", {}).get(key, {})
        # record from the tape's game log (FCS games count in the record, not in the machine)
        wins = sum(1 for g in t["games"] if g["result"].startswith("W"))
        losses = sum(1 for g in t["games"] if g["result"].startswith("L"))
        last = [g for g in t["games"] if g["wk"] == through]
        teams.append(dict(
            key=key, name=t["name"], abbr=t["abbr"], conf=t["conf"], color=t["color"], alt=t["alt"], logo=t["logo"],
            record=f"{wins}-{losses}", rated_gp=t["rated_gp"],
            july=t["july"], now=t["now"], delta=t["delta"], rank=t["rank"], qb_out=t.get("qb_out"),
            d_week=w.get("d_week"), prev_rank=w.get("prev_rank"), d_rank=w.get("d_rank"),
            eff=t["eff"]["total"], eff_rank=t["eff"]["rank"],
            playoff=p.get("playoff"), conf_title=p.get("conf_title"), natl=p.get("national_title"),
            exp_w=p.get("exp_wins"), exp_l=p.get("exp_losses"),
            ap=rk["ap"].get(key),
            last=(f"{last[0]['result']} {'vs' if last[0]['site'] == 'home' else ('at' if last[0]['site'] == 'away' else 'n')} {last[0]['opp']}" if last else "bye"),
            ranks=hist["ranks"].get(key, []),
        ))
    teams.sort(key=lambda x: x["rank"])
    movers = sorted([x for x in teams if x["d_week"] is not None], key=lambda x: -x["d_week"])
    out = dict(
        as_of=dt.datetime.now().isoformat(timespec="minutes"), season=2026, through_week=through,
        rule=tape.get("rule"), games_used=len(games), ap_week=rk.get("week"), playoff_week=po.get("week"), sims=po.get("sims"),
        hist_weeks=hist["weeks"],
        risers=[dict(key=x["key"], name=x["name"], d=x["d_week"], frm=x["prev_rank"], to=x["rank"], last=x["last"]) for x in movers[:8]],
        fallers=[dict(key=x["key"], name=x["name"], d=x["d_week"], frm=x["prev_rank"], to=x["rank"], last=x["last"]) for x in movers[::-1][:8]],
        into=[dict(key=x["key"], name=x["name"], frm=x["prev_rank"], to=x["rank"]) for x in teams if x["rank"] <= 25 and (x["prev_rank"] or 0) > 25],
        out=[dict(key=x["key"], name=x["name"], frm=x["prev_rank"], to=x["rank"]) for x in teams if x["rank"] > 25 and x["prev_rank"] and x["prev_rank"] <= 25],
        confs=sorted({x["conf"] for x in teams if x["conf"]}),
        teams=teams,
    )
    OUT.write_text(json.dumps(out, separators=(",", ":"), ensure_ascii=False), encoding="utf-8")
    return out


if __name__ == "__main__":
    d = build()
    print(f"wrote {OUT.name}: {len(d['teams'])} teams through week {d['through_week']}, playoff sim week {d['playoff_week']}, AP week {d['ap_week']}")
    for t in d["teams"][:10]:
        print(f"  {t['rank']:2d} {t['name']:18s} {t['now']:5.1f} ({t['d_week']:+.1f}, #{t['prev_rank']} -> #{t['rank']}) playoff {t['playoff']}")
