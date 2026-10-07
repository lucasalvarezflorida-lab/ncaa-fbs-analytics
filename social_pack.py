"""Sunday social pack (Lucas 10/6/2026): the week's numbers as post-ready cards + captions, for the social session.

    python social_pack.py --week 5          # 5 = the week just graded -> social/week5/

Writes social/week{N}/: receipts.png, standings.png, top25.png, hotseat.png, heisman.png (1080x1080), captions.md and
pack.json (every number on the cards). Nothing here is posted; the social session reads this folder. Sources: score_tracker.json,
superdog_ledger.json, ratings_current_2026.json + weekly change, boards_week{N+1}.json. NO market numbers on any card
(the show's rule) - the Heisman card carries the machine's index only. Logos from decks/logos (fetched on first use).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

NAVY, NAVY2, ORANGE, ICE, WHITE, INK, MUTE, PALE = "#0A2851", "#123568", "#F47321", "#EAF0F8", "#FFFFFF", "#16273D", "#5C6B7E", "#CADCFC"
UP, DOWN = "#5CD68A", "#FF7A7A"
W = H = 1080
FONTS = Path("C:/Windows/Fonts")


def font(size, bold=False):
    try:
        return ImageFont.truetype(str(FONTS / ("segoeuib.ttf" if bold else "segoeui.ttf")), size)
    except OSError:
        return ImageFont.load_default()


def card(title, kicker):
    im = Image.new("RGB", (W, H), NAVY); d = ImageDraw.Draw(im)
    d.text((60, 48), kicker.upper(), font=font(26, True), fill=ORANGE)
    d.text((60, 86), title, font=font(60, True), fill=WHITE)
    d.rectangle([60, 168, W - 60, 171], fill=ORANGE)
    d.text((60, H - 70), "Man vs Machine · College Football Podcast", font=font(26, True), fill=PALE)
    return im, d


_TEAMS = {}
try:
    for _t in json.loads((HERE / "rosters" / "data" / "teams_fbs_2026.json").read_text(encoding="utf-8")):
        _TEAMS[normalize_name(_t["school"])] = _t
except FileNotFoundError:
    pass


def logo(d_im, norm, x, y, size):
    """decks/logos/<slug>.png (the deck's cache); fetched from the cached ESPN URL on first use, like the deck does."""
    import re, urllib.request
    p = HERE / "decks" / "logos" / (re.sub(r"[^a-z0-9]", "", norm) + ".png")
    if not p.exists():
        t = _TEAMS.get(norm)
        if not t or not t.get("logos"):
            return
        try:
            req = urllib.request.Request(t["logos"][0].replace("http://", "https://"), headers={"User-Agent": "Mozilla/5.0"})
            p.write_bytes(urllib.request.urlopen(req, timeout=20).read())
        except Exception:
            return
    try:
        lg = Image.open(p).convert("RGBA").resize((size, size)); d_im.paste(lg, (x, y), lg)
    except Exception:
        pass


def tname(norm):
    return _TEAMS.get(norm, {}).get("school", norm.title())


def receipts_card(week, rows, out):
    im, d = card(f"Week {week} receipts", "the machine vs the man")
    y = 200
    mm = cm = 0; mw = cw = 0
    for r in rows:
        a, h = r["final"]; ma, mh = r["machine"]; act = h - a; mach = mh - ma
        mm += abs(act - mach); mw += (act > 0) == (mach > 0)
        man = r.get("man"); line2 = f"Machine {r['home'] if mach > 0 else r['away']} {max(ma, mh)}–{min(ma, mh)} · off by {abs(act - mach):g}"
        if man:
            ca, ch = man; mn = ch - ca; cm += abs(act - mn); cw += (act > 0) == (mn > 0)
            line2 += f"     Man {r['home'] if mn > 0 else r['away']} {max(ca, ch)}–{min(ca, ch)} · off by {abs(act - mn):g}"
        d.rounded_rectangle([60, y, W - 60, y + 118], radius=14, fill=NAVY2)
        logo(im, normalize_name(r["away"]), 76, y + 14, 56); logo(im, normalize_name(r["home"]), 140, y + 14, 56)
        d.text((212, y + 14), f"{r['away']} {a} at {r['home']} {h}", font=font(34, True), fill=WHITE)
        d.text((212, y + 66), line2, font=font(26), fill=PALE)
        y += 132
    d.rounded_rectangle([60, y + 10, W - 60, y + 130], radius=14, fill=ORANGE)
    d.text((84, y + 24), f"Winners: machine {mw}–{len(rows) - mw} · man {cw}–{len(rows) - cw}", font=font(34, True), fill=WHITE)
    d.text((84, y + 72), f"Margin miss (lower is better): machine {mm:g} · man {cm:g}", font=font(30), fill=WHITE)
    im.save(out / "receipts.png")
    return dict(machine_wins=mw, man_wins=cw, machine_miss=mm, man_miss=cm)


def standings_card(week, led, out):
    im, d = card("Superdog standings", f"through week {week}")
    st = led["standings"]
    for i, (lab, v) in enumerate((("MAN", st["man"]), ("MACHINE", st["machine"]))):
        x = 60 + i * 490
        d.rounded_rectangle([x, 220, x + 470, 470], radius=18, fill=NAVY2)
        d.text((x + 30, 240), lab, font=font(34, True), fill=ORANGE)
        d.text((x + 30, 300), f"{v:g}", font=font(120, True), fill=WHITE)
    y = 510
    for key, lab in ((f"man_picks_week{week}", "Man"), ("machine_picks", "Machine")):
        picks = [p for p in led.get(key, []) if p.get("week", week) == week]
        d.text((60, y), f"{lab}'s picks this week", font=font(30, True), fill=ORANGE); y += 44
        for p in picks:
            res = p.get("result") or "pending"; col = UP if res in ("win", "cover") else (DOWN if res == "loss" else PALE)
            d.text((60, y), f"{p['pick']}  ·  {res}{(' +' + format(p['points'], 'g')) if p.get('points') else ''}", font=font(28), fill=col); y += 40
        y += 16
    d.text((60, y + 10), "Rules: 3.5+ point dogs · 5 for a cover · 5 + the spread for the win · 1 for a push", font=font(24), fill=PALE)
    im.save(out / "standings.png")
    return dict(man=st["man"], machine=st["machine"])


def top25_card(rows, wc, ap, out):
    im, d = card("The machine's Top 25", "rating · move this week · AP")
    for i, t in enumerate(rows[:25]):
        col = i // 13; rr = i % 13
        x = 60 + col * 490; y = 200 + rr * 60
        w = wc.get(t["team"], {}); dw = w.get("d_week", 0.0)
        logo(im, t["team"], x, y + 4, 44)
        d.text((x + 56, y + 6), f"{i + 1}. {tname(t['team'])}", font=font(30, True), fill=WHITE)
        d.text((x + 330, y + 8), f"{t['cur']:.1f}", font=font(28, True), fill=ORANGE)
        d.text((x + 400, y + 10), f"{dw:+.1f}", font=font(24), fill=UP if dw > 0 else (DOWN if dw < 0 else PALE))
        a = ap.get(t["team"]); d.text((x + 452, y + 12), f"AP {a}" if a else "NR", font=font(20), fill=PALE)
    im.save(out / "top25.png")
    return [dict(rank=i + 1, team=tname(t["team"]), rating=t["cur"], d_week=wc.get(t["team"], {}).get("d_week"), ap=ap.get(t["team"])) for i, t in enumerate(rows[:25])]


def hotseat_card(rows, out):
    im, d = card("Hot seat top five", "40% what six lists say · 60% the machine's odds he's gone")
    y = 210
    for i, r in enumerate(rows[:5]):
        d.rounded_rectangle([60, y, W - 60, y + 128], radius=14, fill=NAVY2)
        logo(im, normalize_name(r["team"]), 80, y + 24, 80)
        d.text((180, y + 18), f"{i + 1}. {r['coach']} · {r['team']}", font=font(36, True), fill=WHITE)
        d.text((180, y + 70), f"{r['record']} · {round(100 * r['p_gone'])}% to be gone · buyout {r.get('buyout') or '—'}{'*' if r.get('buyout_est') else ''}", font=font(27), fill=PALE)
        d.text((W - 200, y + 34), f"{r['score']:.0f}", font=font(60, True), fill=ORANGE)
        y += 142
    d.text((60, y + 6), "P(gone) = odds he is not the coach next season, fit on 2014–25 · * buyout estimated", font=font(22), fill=PALE)
    im.save(out / "hotseat.png")
    return [dict(rank=i + 1, coach=r["coach"], team=r["team"], record=r["record"], p_gone=r["p_gone"], buyout=r.get("buyout"), score=r["score"]) for i, r in enumerate(rows[:5])]


def heisman_card(rows, out):
    im, d = card("The machine's best-player board", "best so far, not a prediction")
    y = 210
    for i, r in enumerate(rows[:5]):
        d.rounded_rectangle([60, y, W - 60, y + 128], radius=14, fill=NAVY2)
        logo(im, normalize_name(r["team"]), 80, y + 24, 80)
        d.text((180, y + 18), f"{i + 1}. {r['name']} · {r['pos']} · {r['team']}", font=font(36, True), fill=WHITE)
        d.text((180, y + 70), f"{r['ppg']} points added a game · team {round(100 * r['p10w'])}% to ten wins", font=font(27), fill=PALE)
        d.text((W - 200, y + 34), f"{r['index']:.1f}", font=font(60, True), fill=ORANGE)
        y += 142
    d.text((60, y + 6), "Points added per game (CFBD PPA, shrunk toward 2025) × team factor", font=font(22), fill=PALE)
    im.save(out / "heisman.png")
    return [dict(rank=i + 1, name=r["name"], pos=r["pos"], team=r["team"], ppg=r["ppg"], index=r["index"]) for i, r in enumerate(rows[:5])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--week", type=int, required=True, help="the week just graded")
    a = ap.parse_args(); n = a.week
    from refresh_all import load_env_key, load_fpi_2026
    load_env_key()
    import inseason_ratings as ir
    out = HERE / "social" / f"week{n}"; out.mkdir(parents=True, exist_ok=True)
    st = [r for r in json.loads((HERE / "score_tracker.json").read_text(encoding="utf-8")) if r["week"] == n and r.get("final")]
    led = json.loads((HERE / "superdog_ledger.json").read_text(encoding="utf-8"))
    rt = json.loads((HERE / "ratings_current_2026.json").read_text(encoding="utf-8"))["teams"]
    wc = ir.weekly_change(load_fpi_2026())["teams"]; apr = ir.latest_rankings(False)["ap"]
    bf = HERE / f"boards_week{n + 1}.json"
    boards = json.loads(bf.read_text(encoding="utf-8")) if bf.exists() else {}
    pack = dict(week=n, generated=dt.datetime.now().isoformat(timespec="minutes"))
    pack["receipts"] = receipts_card(n, st, out)
    pack["standings"] = standings_card(n, led, out)
    pack["top25"] = top25_card(rt, wc, apr, out)
    if boards:
        pack["hotseat"] = hotseat_card(boards["hot_seat"], out)
        pack["heisman"] = heisman_card(boards["heisman_all"], out)
    r = pack["receipts"]; s = pack["standings"]
    cap = [f"# Captions — Week {n} (drafts; the social session rewrites for each platform)\n",
           f"## receipts.png\nWeek {n} receipts. Winners: machine {r['machine_wins']}–{len(st) - r['machine_wins']}, man {r['man_wins']}–{len(st) - r['man_wins']}. "
           f"Margin miss: machine {r['machine_miss']:g}, man {r['man_miss']:g}. Every call was frozen at recording. #ManVsMachine #CFB\n",
           f"## standings.png\nSuperdog standings through Week {n}: Man {s['man']:g}, Machine {s['machine']:g}. 3.5+ point dogs only, 5 for a cover, 5 plus the spread for the win.\n",
           "## top25.png\nThe machine's Top 25: points better than an average FBS team, built from every game played, de-lucked. The move column is this week's games alone.\n"]
    if boards:
        h = pack["hotseat"][0]; k = pack["heisman"][0]
        cap += [f"## hotseat.png\nHot seat top five. No. 1 is {h['coach']} ({h['team']}, {h['record']}): {round(100 * h['p_gone'])}% to be gone by next season on the machine's model. Six hot-seat lists plus a model of every departure since 2014.\n",
                f"## heisman.png\nThe machine's best-player board, best so far and not a prediction: {k['name']} ({k['team']}) on top at {k['ppg']} points added a game.\n"]
    (out / "captions.md").write_text("\n".join(cap), encoding="utf-8")
    (out / "pack.json").write_text(json.dumps(pack, indent=1), encoding="utf-8")
    print(f"social pack -> {out.relative_to(HERE)}: " + ", ".join(p.name for p in sorted(out.iterdir())))


if __name__ == "__main__":
    main()
