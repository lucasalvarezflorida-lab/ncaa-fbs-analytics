"""bracket_proto.py - PROTOTYPE of "The Bracket" slide (Lucas 10/13): the season sim's twelve-team field.

Field = the twelve teams most likely to make the playoff in internal/playoff_sim_weekN.json (latest).
Champions = the sim's most likely champion in each of the four power leagues plus the best Group of Five
champion (the fifth automatic bid). Seeds = straight seeding by the sim's average seed, byes to 1-4.
Committee column = the first CFP rankings (Nov 3); until then the AP rank stands in, labelled as such.
Standalone: writes decks/proto_bracket_weekN.pptx (one slide) - not in the episode deck. NO MARKET.

    python bracket_proto.py
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

NAVY, NAVY2, ORANGE, WHITE = RGBColor(0x0A, 0x28, 0x51), RGBColor(0x12, 0x35, 0x68), RGBColor(0xF4, 0x73, 0x21), RGBColor(0xFF, 0xFF, 0xFF)
PALE, UP, DOWN = RGBColor(0xCA, 0xDC, 0xFC), RGBColor(0x5C, 0xD6, 0x8A), RGBColor(0xFF, 0x7A, 0x7A)
LOGO_DIR = os.path.join(HERE, "decks", "logos")
POWER = {"SEC", "Big Ten", "ACC", "Big 12"}


def txt(slide, x, y, w, h, text, size, color=WHITE, bold=False, align=PP_ALIGN.LEFT, italic=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = text
    f = r.font; f.name = "Arial"; f.size = Pt(size); f.color.rgb = color; f.bold = bold; f.italic = italic
    return box


def shape(slide, kind, x, y, w, h, fill):
    s = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = fill; s.line.fill.background(); s.shadow.inherit = False
    return s


def school(norm):
    try:
        for t in json.load(open(os.path.join(HERE, "rosters", "data", "teams_fbs_2026.json"), encoding="utf-8")):
            if normalize_name(t["school"]) == norm:
                return t["school"]
    except FileNotFoundError:
        pass
    return norm.title()


def logo(norm):
    p = os.path.join(LOGO_DIR, re.sub(r"[^a-z0-9]", "", norm) + ".png")
    return p if os.path.exists(p) else None


def field():
    files = sorted(glob.glob(os.path.join(HERE, "internal", "playoff_sim_week*.json")), key=lambda f: int(f.rsplit("week", 1)[1].split(".")[0]))
    d = json.load(open(files[-1], encoding="utf-8"))
    rows = d["teams"] if isinstance(d["teams"], list) else [dict(team=k, **v) for k, v in d["teams"].items()]
    by_conf: dict[str, list] = {}
    for r in rows:
        by_conf.setdefault(r["conf"], []).append(r)
    champs = {}
    for conf, rs in by_conf.items():
        best = max(rs, key=lambda r: r["conf_title"])
        if best["conf_title"] > 0:
            champs[conf] = best["team"]
    power_champs = {champs[c] for c in POWER if c in champs}
    g5 = max((r for c, rs in by_conf.items() if c not in POWER and c != "FBS Independents" for r in rs), key=lambda r: r["playoff"])
    pool = sorted(rows, key=lambda r: -r["playoff"])
    inside = [r for r in pool if r["team"] in power_champs or r["team"] == g5["team"]]
    at_large = [r for r in pool if r not in inside][: 12 - len(inside)]
    team_field = sorted(inside + at_large, key=lambda r: r["avg_seed"])
    for r in team_field:
        r["how"] = ("champion" if r["team"] in power_champs else ("Group of Five champion" if r["team"] == g5["team"] else "at-large"))
    out = [r for r in pool if r not in team_field][:4]
    return d.get("week"), d.get("sims"), team_field, out


def build():
    week, sims, F, nxt = field()
    try:
        import inseason_ratings as ir
        ap = ir.latest_rankings(refresh=False)["ap"]
    except Exception:  # noqa: BLE001
        ap = {}
    prs = Presentation(); prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    s = prs.slides.add_slide(prs.slide_layouts[6])
    shape(s, MSO_SHAPE.RECTANGLE, 0, 0, 13.333, 7.5, NAVY)
    txt(s, 0.9, 0.42, 11.5, 0.4, f"PROTOTYPE · WEEK {week} · THE MACHINE'S BRACKET", 14, ORANGE, True)
    txt(s, 0.9, 0.76, 11.5, 0.8, "The Bracket", 40, WHITE, True)
    txt(s, 0.9, 1.5, 11.5, 0.3, f"The season simulated {sims:,} times from today's ratings · five champions, seven at large · byes to the top four seeds", 13, PALE, True)
    TOP, RH = 2.12, 0.37
    hdr = [(0.9, 0.45, "SEED", PP_ALIGN.RIGHT), (1.95, 2.6, "TEAM", PP_ALIGN.LEFT), (4.55, 1.3, "LEAGUE", PP_ALIGN.LEFT), (5.85, 1.75, "HOW THEY GET IN", PP_ALIGN.LEFT),
           (7.7, 0.8, "IN", PP_ALIGN.RIGHT), (8.55, 0.7, "BYE", PP_ALIGN.RIGHT), (9.3, 0.8, "AVG SEED", PP_ALIGN.RIGHT), (10.2, 1.0, "TITLE", PP_ALIGN.RIGHT), (11.3, 1.1, "AP (COMMITTEE NOV 3)", PP_ALIGN.RIGHT)]
    for x, w, lab, al in hdr:
        txt(s, x, TOP - 0.25, w, 0.22, lab, 8, PALE, True, al)
    for i, r in enumerate(F):
        y = TOP + i * RH
        if i % 2 == 0:
            shape(s, MSO_SHAPE.RECTANGLE, 0.9, y, 11.5, RH, NAVY2)
        if i == 4:
            shape(s, MSO_SHAPE.RECTANGLE, 0.9, y - 0.015, 11.5, 0.03, ORANGE)   # the bye line
        txt(s, 0.9, y + 0.05, 0.45, 0.3, str(i + 1), 13, ORANGE, True, PP_ALIGN.RIGHT)
        lp = logo(r["team"])
        if lp:
            shape(s, MSO_SHAPE.OVAL, 1.5, y + 0.04, 0.29, 0.29, WHITE)
            s.shapes.add_picture(lp, Inches(1.53), Inches(y + 0.07), Inches(0.23), Inches(0.23))
        txt(s, 1.95, y + 0.05, 2.6, 0.3, school(r["team"]), 12.5, WHITE, True)
        txt(s, 4.55, y + 0.08, 1.3, 0.3, r["conf"].replace("FBS Independents", "Independent"), 9.5, PALE)
        how = r["how"]
        txt(s, 5.85, y + 0.07, 1.75, 0.3, how, 10, ORANGE if how != "at-large" else PALE, how != "at-large")
        p = r["playoff"]
        txt(s, 7.7, y + 0.06, 0.8, 0.3, f"{round(100 * p)}%", 11.5, UP if p >= 0.5 else (DOWN if p < 0.2 else WHITE), True, PP_ALIGN.RIGHT)
        txt(s, 8.55, y + 0.07, 0.7, 0.3, f"{round(100 * r['bye'])}%", 10.5, WHITE, False, PP_ALIGN.RIGHT)
        txt(s, 9.3, y + 0.07, 0.8, 0.3, f"{r['avg_seed']:.1f}", 10.5, PALE, False, PP_ALIGN.RIGHT)
        txt(s, 10.2, y + 0.07, 1.0, 0.3, f"{100 * r['national_title']:.1f}%", 10.5, PALE, False, PP_ALIGN.RIGHT)
        a = ap.get(r["team"])
        txt(s, 11.3, y + 0.07, 1.1, 0.3, f"AP {a}" if a else "NR", 10.5, PALE, False, PP_ALIGN.RIGHT)
    fy = TOP + 12 * RH + 0.1
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, fy, 11.5, 0.7, NAVY2)
    txt(s, 1.1, fy + 0.05, 11.2, 0.28, "First four out: " + " · ".join(f"{school(r['team'])} {round(100 * r['playoff'])}%" for r in nxt), 11, WHITE, True)
    txt(s, 1.1, fy + 0.34, 11.2, 0.34, "IN = chance of a playoff spot · BYE = chance of a top-four seed · champions = the sim's most likely winner of each power league; the fifth bid is the best Group of Five champion · "
        "the committee column shows the AP poll until the first CFP rankings on Nov 3 · prototype, not on air", 9.5, PALE)
    out = os.path.join(HERE, "decks", f"proto_bracket_week{week}.pptx")
    prs.save(out)
    return out, F


if __name__ == "__main__":
    out, F = build()
    print("wrote", out)
    for i, r in enumerate(F, 1):
        print(f"  {i:2d} {r['team']:18s} {r['conf']:14s} {r['how']:22s} in {r['playoff']:.2f} bye {r['bye']:.2f} seed {r['avg_seed']}")
