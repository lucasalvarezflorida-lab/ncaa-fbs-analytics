"""Film study session generator — implements FILM_STUDY_SPEC.md.

Data-driven post-game tape session for flagged games, built from CFBD
play-by-play. Produces film_study/<year>_wk<N>_<away>_at_<home>.md plus a
win-probability chart PNG.

Usage:
    python film_study.py --game "<away> at <home>" [--year YYYY] [--week N]
                         [--refresh] [--postseason]

Every section degrades gracefully: if an endpoint is missing data the report
says so instead of dying, because game-day CFBD data lands piecemeal.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "fpi-decomposition"))

import cfbd_client as cfbd
from name_mapping import normalize_name as norm

OUT_DIR = HERE / "film_study"
ALERTS_LIVE = HERE / "alerts_log.json"
ALERTS_ARCHIVE = HERE / "alerts_log_2025prior_archive.json"
SCOUTING = HERE / "scouting_top25.json"
N_SWINGS = 5
N_TURNING = 6
Z_FLAG = 1.0


def pick(d: dict, *names):
    for n in names:
        v = d.get(n)
        if v is not None:
            return v
    return None


def fnum(v):
    """CFBD ships numbers as floats OR strings depending on endpoint."""
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")


def dedup_text(text: str) -> str:
    """CFBD's play-by-play occasionally ships the play text doubled
    ("TEAM run ... TEAM run ..."). Collapse an exact repetition."""
    s = re.sub(r"\s+", " ", text or "").strip()
    half, rem = divmod(len(s), 2)
    if rem == 0 and half and s[:half] == s[half:]:
        return s[:half].strip()  # "XX" — doubled with no separator
    if rem == 1 and s[:half] == s[half + 1:]:
        return s[:half]  # "X X" — doubled around a space
    return s


def clock_str(clk) -> str:
    if isinstance(clk, dict):
        m, s = clk.get("minutes") or 0, clk.get("seconds") or 0
        return f"{int(m)}:{int(s):02d}"
    return str(clk) if clk else "?"


# ---------------------------------------------------------------- game lookup

def find_game(year: int, away: str, home: str, week, season_type: str,
              refresh: bool) -> dict:
    games = cfbd.get("/games", {"year": year, "seasonType": season_type}, refresh)
    na, nh = norm(away), norm(home)
    swapped = None
    for g in games:
        gh = pick(g, "homeTeam", "home_team")
        ga = pick(g, "awayTeam", "away_team")
        if not gh or not ga:
            continue
        if week is not None and pick(g, "week") != week:
            continue
        if norm(gh) == nh and norm(ga) == na:
            return g
        if norm(gh) == na and norm(ga) == nh and swapped is None:
            swapped = g
    if swapped is not None:
        gh = pick(swapped, "homeTeam", "home_team")
        ga = pick(swapped, "awayTeam", "away_team")
        print(f"NOTE: matched with home/away swapped — actual: {ga} at {gh}")
        return swapped
    raise SystemExit(
        f"Game not found: {away} at {home}, {year} {season_type}"
        + (f" wk{week}" if week is not None else "")
    )


def close_spread(gid, year: int, season_type: str, refresh: bool):
    """Best available spread (home perspective) from /lines, provider-ranked
    the same way build_conference_book does."""
    providers = ["DraftKings", "Bovada", "ESPN Bet"]
    try:
        records = cfbd.get("/lines", {"year": year, "seasonType": season_type},
                           refresh)
    except cfbd.CFBDError:
        return None, None
    for g in records:
        if pick(g, "id", "gameId") != gid:
            continue
        lines = g.get("lines") or []
        ranked = sorted(lines, key=lambda ln: (
            providers.index(ln.get("provider"))
            if ln.get("provider") in providers else 99))
        spread = next((fnum(ln.get("spread")) for ln in ranked
                       if ln.get("spread") is not None), None)
        total = next((fnum(pick(ln, "overUnder", "over_under")) for ln in ranked
                      if pick(ln, "overUnder", "over_under") is not None), None)
        return spread, total
    return None, None


# ------------------------------------------------------------ win probability

def wp_series(gid, refresh: bool) -> list[dict]:
    try:
        rows = cfbd.get("/metrics/wp", {"gameId": gid}, refresh)
    except cfbd.CFBDError:
        return []
    out = []
    for r in rows:
        wp = fnum(pick(r, "homeWinProb", "homeWinProbability", "home_win_prob"))
        if wp is None:
            continue
        out.append({
            "n": pick(r, "playNumber", "play_number") or len(out) + 1,
            "wp": wp,
            "text": dedup_text(pick(r, "playText", "play_text") or ""),
            "home_score": pick(r, "homeScore", "home_score"),
            "away_score": pick(r, "awayScore", "away_score"),
        })
    out.sort(key=lambda r: r["n"])
    return out


def biggest_swings(series: list[dict]) -> list[dict]:
    swings = []
    for prev, cur in zip(series, series[1:]):
        swings.append({**cur, "delta": cur["wp"] - prev["wp"]})
    swings.sort(key=lambda s: abs(s["delta"]), reverse=True)
    return swings[:N_SWINGS]


def wp_chart(series: list[dict], swings: list[dict], home: str, away: str,
             png_path: Path) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    xs = [r["n"] for r in series]
    ys = [r["wp"] * 100 for r in series]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot(xs, ys, lw=1.8)
    ax.axhline(50, ls="--", lw=0.8, color="gray")
    marked = {s["n"] for s in swings}
    for i, s in enumerate(sorted(swings, key=lambda s: s["n"]), 1):
        ax.annotate(str(i), (s["n"], s["wp"] * 100),
                    textcoords="offset points", xytext=(0, 10),
                    ha="center", fontweight="bold", color="crimson")
        ax.plot([s["n"]], [s["wp"] * 100], "o", color="crimson", ms=5)
    ax.set_ylim(0, 100)
    ax.set_xlabel("Play")
    ax.set_ylabel(f"{home} win probability (%)")
    ax.set_title(f"{away} at {home} — win probability (numbered = biggest swings)")
    fig.tight_layout()
    fig.savefig(png_path, dpi=150)
    plt.close(fig)
    return True


# ------------------------------------------------------------------ plays/EPA

def game_plays(gid, year: int, week, season_type: str, team: str,
               refresh: bool) -> list[dict]:
    params = {"year": year, "seasonType": season_type, "team": team}
    if week is not None:
        params["week"] = week
    try:
        rows = cfbd.get("/plays", params, refresh)
    except cfbd.CFBDError:
        return []
    return [r for r in rows if pick(r, "gameId", "game_id") == gid]


def turning_points(plays: list[dict]) -> list[dict]:
    scored = []
    for p in plays:
        ppa = fnum(pick(p, "ppa", "epa"))
        if ppa is None:
            continue
        scored.append({
            "ppa": ppa,
            "offense": p.get("offense") or "?",
            "period": pick(p, "period") or "?",
            "clock": clock_str(p.get("clock")),
            "down": pick(p, "down"),
            "distance": pick(p, "distance"),
            "type": pick(p, "playType", "play_type") or "?",
            "yards": pick(p, "yardsGained", "yards_gained"),
            "text": dedup_text(pick(p, "playText", "play_text") or ""),
        })
    scored.sort(key=lambda p: abs(p["ppa"]), reverse=True)
    return scored[:N_TURNING]


# --------------------------------------------------------- unit report card

def ppa_profile(team: str, year: int, gid, season_type: str, refresh: bool):
    """This game's offense/defense PPA vs the team's season distribution."""
    try:
        rows = cfbd.get("/ppa/games", {"year": year, "team": team,
                                       "seasonType": season_type}, refresh)
    except cfbd.CFBDError:
        return None
    this_game, season_off, season_def = None, [], []
    for r in rows:
        off = fnum((r.get("offense") or {}).get("overall"))
        dfn = fnum((r.get("defense") or {}).get("overall"))
        if pick(r, "gameId", "game_id") == gid:
            this_game = (off, dfn)
        else:
            if off is not None:
                season_off.append(off)
            if dfn is not None:
                season_def.append(dfn)
    if this_game is None:
        return None

    def dist(vals):
        if len(vals) < 2:
            return None
        return statistics.mean(vals), statistics.stdev(vals)

    return {"game_off": this_game[0], "game_def": this_game[1],
            "season_off": dist(season_off), "season_def": dist(season_def)}


def box_advanced(gid, refresh: bool):
    """Per-team success rate / explosiveness from the advanced box score."""
    box = None
    for key in ("id", "gameId"):
        try:
            box = cfbd.get("/game/box/advanced", {key: gid}, refresh)
            break
        except cfbd.CFBDError:
            continue
    if not isinstance(box, dict):
        return {}
    teams = box.get("teams") or {}
    out = {}
    for metric, dest in (("successRates", "success"), ("explosiveness", "explosive"),
                         ("ppa", "ppa")):
        for entry in teams.get(metric) or []:
            team = entry.get("team")
            overall = entry.get("overall") or {}
            val = fnum(overall.get("total") if isinstance(overall, dict) else overall)
            if team is not None and val is not None:
                out.setdefault(norm(team), {})[dest] = val
    return out


def season_advanced(team: str, year: int, refresh: bool):
    try:
        rows = cfbd.get("/stats/season/advanced", {"year": year, "team": team},
                        refresh)
    except cfbd.CFBDError:
        return None
    for r in rows:
        if norm(r.get("team") or "") == norm(team):
            off, dfn = r.get("offense") or {}, r.get("defense") or {}
            return {
                "off_success": fnum(pick(off, "successRate", "success_rate")),
                "off_explosive": fnum(off.get("explosiveness")),
                "def_success": fnum(pick(dfn, "successRate", "success_rate")),
                "def_explosive": fnum(dfn.get("explosiveness")),
            }
    return None


# ------------------------------------------------------------ tendency check

RUSH_RE = re.compile(r"rush|run", re.I)
PASS_RE = re.compile(r"pass|sack|interception", re.I)


def tendencies(plays: list[dict], team: str) -> dict:
    by_down = {1: [0, 0], 2: [0, 0], 3: [0, 0]}  # down -> [rush, pass]
    total = 0
    for p in plays:
        if norm(p.get("offense") or "") != norm(team):
            continue
        ptype = str(pick(p, "playType", "play_type") or "")
        down = pick(p, "down")
        is_rush, is_pass = bool(RUSH_RE.search(ptype)), bool(PASS_RE.search(ptype))
        if not (is_rush or is_pass):
            continue
        total += 1
        if down in by_down:
            by_down[down][0 if is_rush else 1] += 1
    out = {"plays": total, "by_down": {}}
    for d, (r, p) in by_down.items():
        n = r + p
        out["by_down"][d] = (100 * r / n) if n else None
    return out


def dossier_notes(team: str) -> list[str]:
    if not SCOUTING.exists():
        return []
    data = json.loads(SCOUTING.read_text(encoding="utf-8"))
    teams = data.get("teams") or {}
    entry = next((v for k, v in teams.items() if norm(k) == norm(team)), None)
    if not entry:
        return []
    notes = []
    for key, label in (("ob", "Offense base"), ("ot", "Offense tendencies"),
                       ("db", "Defense base"), ("dt", "Defense tendencies")):
        if entry.get(key):
            notes.append(f"{label}: {entry[key]}")
    return notes


# ------------------------------------------------------------- alert grading

def grade_alert(gid, home: str, hp: int, ap: int) -> dict | None:
    """Grade the Upset Board alert for this game against its FIRST-SEEN line
    (never the moved line), write the result into the live ledger, and return
    grading info. Archive entries are graded read-only."""
    for path, live in ((ALERTS_LIVE, True), (ALERTS_ARCHIVE, False)):
        if not path.exists():
            continue
        log = json.loads(path.read_text(encoding="utf-8"))
        entry = log.get(str(gid))
        if entry is None:
            continue
        spread = fnum(entry.get("spread"))
        side = entry.get("model_side")
        if spread is None or not side:
            return {"entry": entry, "ats": "?", "live": live, "record": None}
        covered = (hp - ap) + spread  # >0 home covered, first-seen line
        side_is_home = norm(side) == norm(home)
        val = covered if side_is_home else -covered
        ats = "P" if val == 0 else ("W" if val > 0 else "L")
        record = None
        if live:
            entry["final"] = f"{hp}-{ap}"
            entry["ats"] = ats
            entry["graded"] = date.today().isoformat()
            path.write_text(json.dumps(log, indent=1), encoding="utf-8")
            w = sum(1 for e in log.values() if e.get("ats") == "W")
            l = sum(1 for e in log.values() if e.get("ats") == "L")
            p = sum(1 for e in log.values() if e.get("ats") == "P")
            record = (w, l, p)
        return {"entry": entry, "ats": ats, "live": live, "record": record}
    return None


# ---------------------------------------------------------------- the report

def fmt_z(game_val, dist, invert=False):
    """'0.31 vs season 0.18±0.12 (z=+1.1) ⚠' — invert for defense where
    lower allowed is better."""
    if game_val is None:
        return "n/a"
    if not dist:
        return f"{game_val:+.3f} (no season baseline)"
    mean, sd = dist
    z = (game_val - mean) / sd if sd else 0.0
    flag = " **⚠ deviation**" if abs(z) > Z_FLAG else ""
    return f"{game_val:+.3f} vs season {mean:+.3f}±{sd:.3f} (z={z:+.1f}){flag}"


def build_report(args) -> Path:
    refresh = args.refresh
    season_type = "postseason" if args.postseason else "regular"
    g = find_game(args.year, args.away, args.home, args.week, season_type, refresh)
    gid = pick(g, "id")
    week = pick(g, "week")
    home = pick(g, "homeTeam", "home_team")
    away = pick(g, "awayTeam", "away_team")
    hp = pick(g, "homePoints", "home_points")
    ap = pick(g, "awayPoints", "away_points")
    neutral = bool(pick(g, "neutralSite", "neutral_site"))
    if hp is None or ap is None:
        raise SystemExit(f"{away} at {home} has no final score yet — film study "
                         "runs on completed games.")

    OUT_DIR.mkdir(exist_ok=True)
    stem = f"{args.year}_wk{week}_{slug(away)}_at_{slug(home)}"
    md_path = OUT_DIR / f"{stem}.md"
    png_path = OUT_DIR / f"{stem}_wp.png"

    lines = [f"# Film study — {away} at {home} "
             f"({args.year} week {week}{', neutral' if neutral else ''})", ""]

    # 1. Score vs the script
    spread, total = close_spread(gid, args.year, season_type, refresh)
    alert = grade_alert(gid, home, hp, ap)
    lines += ["## 1. The score vs the script", ""]
    lines.append(f"- **Final: {away} {ap}, {home} {hp}**"
                 f" (margin {home} {hp - ap:+d})")
    if spread is not None:
        cov = "covered" if (hp - ap) + spread > 0 else (
            "push" if (hp - ap) + spread == 0 else "did not cover")
        lines.append(f"- Close: {home} {spread:+g}"
                     + (f", total {total:g}" if total is not None else "")
                     + f" — {home} {cov}")
        if total is not None:
            ou = hp + ap
            lines.append(f"- Total: {ou} pts — "
                         + ("OVER" if ou > total else "UNDER" if ou < total else "push"))
    else:
        lines.append("- No closing line found on /lines.")
    if alert:
        e = alert["entry"]
        lines.append(f"- **Upset Board alert**: {e.get('tier')} on "
                     f"{e.get('model_side')} at first-seen {home} "
                     f"{fnum(e.get('spread')):+g} (edge {e.get('edge')})")
    else:
        lines.append("- Not on the Upset Board.")
    lines.append("")

    # 2. Win probability chart + swings
    series = wp_series(gid, refresh)
    swings = biggest_swings(series) if series else []
    lines += ["## 2. Win probability", ""]
    if series:
        if wp_chart(series, swings, home, away, png_path):
            lines.append(f"![WP chart]({png_path.name})")
            lines.append("")
        lines.append(f"Biggest swings ({home} WP):")
        lines.append("")
        for i, s in enumerate(sorted(swings, key=lambda s: s["n"]), 1):
            lines.append(f"{i}. play {s['n']}: {s['delta'] * 100:+.0f} pts "
                         f"(to {s['wp'] * 100:.0f}%) — {s['text']}")
    else:
        lines.append("No win-probability data on /metrics/wp for this game.")
    lines.append("")

    # 3. Turning points by |EPA|
    plays = game_plays(gid, args.year, week, season_type, home, refresh)
    lines += ["## 3. Turning points (top plays by |EPA|)", ""]
    tps = turning_points(plays)
    if tps:
        lines.append("| EPA | Qtr | Clock | Offense | D&D | Type | Yds | Play |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for p in tps:
            dd = (f"{p['down']} & {p['distance']}"
                  if p["down"] is not None else "—")
            text = p["text"].replace("|", "/")
            lines.append(f"| {p['ppa']:+.2f} | Q{p['period']} | {p['clock']} | "
                         f"{p['offense']} | {dd} | {p['type']} | "
                         f"{p['yards'] if p['yards'] is not None else '—'} | {text} |")
    else:
        lines.append("No play-by-play EPA on /plays for this game.")
    lines.append("")

    # 4. Unit report card
    lines += ["## 4. Unit report card (PPA/play, this game vs season)", ""]
    box = box_advanced(gid, refresh)
    for team in (away, home):
        prof = ppa_profile(team, args.year, gid, season_type, refresh)
        adv = season_advanced(team, args.year, refresh)
        b = box.get(norm(team), {})
        lines.append(f"### {team}")
        lines.append("")
        if prof:
            lines.append(f"- Offense PPA: {fmt_z(prof['game_off'], prof['season_off'])}")
            lines.append(f"- Defense PPA allowed: "
                         f"{fmt_z(prof['game_def'], prof['season_def'])}")
        else:
            lines.append("- No /ppa/games rows for this team.")
        if b.get("success") is not None:
            s = f"- Success rate: {b['success']:.3f}"
            if adv and adv.get("off_success") is not None:
                s += f" (season offense {adv['off_success']:.3f})"
            lines.append(s)
        if b.get("explosive") is not None:
            s = f"- Explosiveness: {b['explosive']:.3f}"
            if adv and adv.get("off_explosive") is not None:
                s += f" (season offense {adv['off_explosive']:.3f})"
            lines.append(s)
        lines.append("")

    # 5. Tendency check
    lines += ["## 5. Tendency check", ""]
    for team in (away, home):
        t = tendencies(plays, team)
        lines.append(f"### {team} ({t['plays']} called plays)")
        lines.append("")
        for d in (1, 2, 3):
            rate = t["by_down"].get(d)
            lines.append(f"- Down {d}: "
                         + (f"{rate:.0f}% run" if rate is not None else "no data"))
        for note in dossier_notes(team):
            lines.append(f"- Dossier — {note}")
        lines.append("")

    # 6. Alert grading
    lines += ["## 6. Alert grading", ""]
    if alert:
        e = alert["entry"]
        lines.append(f"- Model side **{e.get('model_side')}** vs first-seen "
                     f"{home} {fnum(e.get('spread')):+g} → **ATS {alert['ats']}**")
        if alert["record"]:
            w, l, p = alert["record"]
            lines.append(f"- Running ledger (live log): **{w}-{l}"
                         + (f"-{p}" if p else "") + " ATS**")
        elif not alert["live"]:
            lines.append("- Alert found in the 2025-prior archive — graded "
                         "read-only, ledger not modified.")
    else:
        lines.append("- No alert on file for this game; nothing to grade.")
    lines.append("")

    # 7. Watch list
    q = quote_plus(f"{away} vs {home} {args.year} highlights")
    lines += ["## 7. Watch list", "",
              f"- [YouTube: official highlight search]"
              f"(https://www.youtube.com/results?search_query={q})",
              "- Plays to pull up: the numbered WP swings in §2 and the top "
              "|EPA| plays in §3.", ""]

    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def main():
    ap = argparse.ArgumentParser(description="Generate a film study session "
                                             "report for one game.")
    ap.add_argument("--game", required=True,
                    help='"<away> at <home>" (also accepts "away @ home")')
    ap.add_argument("--year", type=int, default=2026)
    ap.add_argument("--week", type=int, default=None)
    ap.add_argument("--postseason", action="store_true")
    ap.add_argument("--refresh", action="store_true",
                    help="bypass the on-disk CFBD cache")
    args = ap.parse_args()

    m = re.split(r"\s+at\s+|\s*@\s*", args.game, maxsplit=1, flags=re.I)
    if len(m) != 2:
        raise SystemExit('Could not parse --game; use "<away> at <home>".')
    args.away, args.home = m[0].strip(), m[1].strip()

    path = build_report(args)
    print(f"Wrote {path}")
    png = path.with_name(path.stem + "_wp.png")
    if png.exists():
        print(f"Wrote {png}")


if __name__ == "__main__":
    main()
