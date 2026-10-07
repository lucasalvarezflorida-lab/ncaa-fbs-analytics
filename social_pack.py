"""Sunday social pack (Lucas 10/6/2026) - DATA ONLY. The podcast owns the numbers; the social session (mvm-social) owns
how they look and reads this folder.

    python social_pack.py --week 5          # 5 = the week just graded -> social/week5/

Writes social/week{N}/pack.json (schema below), captions.md (draft captions) and logos/<slug>.png for every team on the
pack. No cards are drawn here any more (10/6 split): mvm-social\\render_cards.py draws them from pack.json.
SCHEMA PROMISE: keys are added, never renamed or removed; a metric that changes on the show keeps its old key for a week
and says so in "notes". schema_version bumps only when that promise is broken. NO market numbers in the pack.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

SCHEMA = 1
_TEAMS = {}
try:
    for _t in json.loads((HERE / "rosters" / "data" / "teams_fbs_2026.json").read_text(encoding="utf-8")):
        _TEAMS[normalize_name(_t["school"])] = _t
except FileNotFoundError:
    pass


def slug(norm):
    return re.sub(r"[^a-z0-9]", "", norm)


def tname(norm):
    return _TEAMS.get(norm, {}).get("school", norm.title())


def logo_file(norm):
    """decks/logos/<slug>.png - fetched from the cached ESPN URL on first use (same cache the deck uses)."""
    import urllib.request
    p = HERE / "decks" / "logos" / (slug(norm) + ".png")
    if not p.exists():
        t = _TEAMS.get(norm)
        if not t or not t.get("logos"):
            return None
        try:
            req = urllib.request.Request(t["logos"][0].replace("http://", "https://"), headers={"User-Agent": "Mozilla/5.0"})
            p.write_bytes(urllib.request.urlopen(req, timeout=20).read())
        except Exception:
            return None
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True, help="the week just graded")
    a = ap.parse_args(); n = a.week
    from refresh_all import load_env_key, load_fpi_2026
    load_env_key()
    import inseason_ratings as ir
    out = HERE / "social" / f"week{n}"; (out / "logos").mkdir(parents=True, exist_ok=True)
    teams_used = set()

    def team(name_or_norm):
        norm = normalize_name(name_or_norm); teams_used.add(norm)
        return dict(name=tname(norm), norm=norm, logo=f"logos/{slug(norm)}.png")

    # receipts: the week's card, graded on the score calls (the show's convention since 10/6)
    st = [r for r in json.loads((HERE / "score_tracker.json").read_text(encoding="utf-8")) if r["week"] == n and r.get("final")]
    games = []; mm = cm = 0.0; mw = cw = 0
    for r in st:
        a_, h = r["final"]; ma, mh = r["machine"]; act = h - a_; mach = mh - ma
        mm += abs(act - mach); mw += (act > 0) == (mach > 0)
        g = dict(away=team(r["away"]), home=team(r["home"]), final=dict(away=a_, home=h),
                 machine=dict(call=f"{r['home'] if mach > 0 else r['away']} {max(ma, mh)}–{min(ma, mh)}", away=ma, home=mh, off_by=abs(act - mach), winner_right=(act > 0) == (mach > 0)))
        if r.get("man"):
            ca, ch = r["man"]; mn = ch - ca; cm += abs(act - mn); cw += (act > 0) == (mn > 0)
            g["man"] = dict(call=f"{r['home'] if mn > 0 else r['away']} {max(ca, ch)}–{min(ca, ch)}", away=ca, home=ch, off_by=abs(act - mn), winner_right=(act > 0) == (mn > 0))
        games.append(g)
    receipts = dict(games=games, machine=dict(wins=mw, losses=len(st) - mw, margin_miss=mm), man=dict(wins=cw, losses=len(st) - cw, margin_miss=cm),
                    off_by_means="the score call's margin vs the final margin, both sides")

    # superdogs
    led = json.loads((HERE / "superdog_ledger.json").read_text(encoding="utf-8"))

    def picks(key):
        return [dict(pick=p["pick"], result=p.get("result") or "pending", points=p.get("points"), final=p.get("final")) for p in led.get(key, []) if p.get("week", n) == n]
    standings = dict(man=led["standings"]["man"], machine=led["standings"]["machine"], through_week=n,
                     man_picks=picks(f"man_picks_week{n}"), machine_picks=picks("machine_picks"),
                     rules="3.5+ point dogs · 5 for a cover · 5 + the spread for an outright win · 1 for a push")

    # top 25 + movers
    rt = json.loads((HERE / "ratings_current_2026.json").read_text(encoding="utf-8"))
    wc = ir.weekly_change(load_fpi_2026())["teams"]; apr = ir.latest_rankings(False)["ap"]
    top25 = [dict(rank=i + 1, team=team(t["team"]), rating=t["cur"], d_week=wc.get(t["team"], {}).get("d_week"),
                  prev_rank=wc.get(t["team"], {}).get("prev_rank"), ap=apr.get(t["team"]), games=t["gp"]) for i, t in enumerate(rt["teams"][:25])]
    movers = sorted(wc.items(), key=lambda kv: -kv[1]["d_week"])
    risers = [dict(team=team(t), d_week=v["d_week"], prev_rank=v["prev_rank"], rank=v["rank"]) for t, v in movers[:5]]
    fallers = [dict(team=team(t), d_week=v["d_week"], prev_rank=v["prev_rank"], rank=v["rank"]) for t, v in movers[-5:][::-1]]

    # boards (next week's file, built on Sunday)
    bf = HERE / f"boards_week{n + 1}.json"; boards = json.loads(bf.read_text(encoding="utf-8")) if bf.exists() else {}
    hot = [dict(rank=i + 1, coach=r["coach"], team=team(r["team"]), record=r.get("record"), p_gone=r["p_gone"], lists=r.get("lists"),
                human_prior=r["cbs"], buyout=(r.get("buyout") or "").replace("—", "") or None, buyout_estimated=bool(r.get("buyout_est")),
                score=r["score"], last_result=(r.get("results") or [None])[-1], tenure=r.get("tenure")) for i, r in enumerate(boards.get("hot_seat", [])[:10])]
    heis = [dict(rank=i + 1, name=r["name"], pos=r["pos"], team=team(r["team"]), points_per_game=r["ppg"], index=r["index"],
                 team_p10w=r["p10w"], plays=r["plays26"], games=r["games"]) for i, r in enumerate(boards.get("heisman_all", [])[:8])]

    for norm in teams_used:
        p = logo_file(norm)
        if p:
            shutil.copyfile(p, out / "logos" / p.name)

    pack = dict(schema_version=SCHEMA, week=n, generated=dt.datetime.now().isoformat(timespec="minutes"),
                notes=["Receipts: 'off by' is the score call's margin vs the final, both sides (since 10/6; before that the machine was graded on its line).",
                       "Hot seat: score = 40% six-list human prior + 60% model P(gone); the human half changed from CBS-only on 10/6.",
                       "Heisman: 'best so far, not a prediction' - index = points added per game x team factor; keep that phrase on anything public.",
                       "No market numbers anywhere in this pack, by the show's rule."],
                receipts=receipts, standings=standings, top25=top25, risers=risers, fallers=fallers, hot_seat=hot, heisman=heis,
                rating_rule=rt.get("params"))
    (out / "pack.json").write_text(json.dumps(pack, indent=1, ensure_ascii=False), encoding="utf-8")
    cap = [f"# Captions — Week {n} (drafts; the social session rewrites per platform)\n",
           f"## receipts\nWeek {n} receipts. Winners: machine {mw}–{len(st) - mw}, man {cw}–{len(st) - cw}. Margin miss: machine {mm:g}, man {cm:g}. Every call was frozen at recording. #ManVsMachine #CFB\n",
           f"## standings\nSuperdog standings through Week {n}: Man {standings['man']:g}, Machine {standings['machine']:g}. 3.5+ point dogs only, 5 for a cover, 5 plus the spread for the win.\n",
           "## top25\nThe machine's Top 25: points better than an average FBS team, built from every game played, de-lucked. The move column is this week's games alone.\n"]
    if hot:
        cap.append(f"## hot_seat\nHot seat top five. No. 1 is {hot[0]['coach']} ({hot[0]['team']['name']}, {hot[0]['record']}): {round(100 * hot[0]['p_gone'])}% to be gone by next season on the machine's model. Six hot-seat lists plus a model of every departure since 2014.\n")
    if heis:
        cap.append(f"## heisman\nThe machine's best-player board, best so far and not a prediction: {heis[0]['name']} ({heis[0]['team']['name']}) on top at {heis[0]['points_per_game']} points added a game.\n")
    (out / "captions.md").write_text("\n".join(cap), encoding="utf-8")
    for old in ("receipts.png", "standings.png", "top25.png", "hotseat.png", "heisman.png"):   # the drawn cards are not ours any more
        (out / old).unlink(missing_ok=True)
    print(f"social pack -> {out.relative_to(HERE)}: pack.json, captions.md, {len(list((out / 'logos').iterdir()))} logos")


if __name__ == "__main__":
    main()
