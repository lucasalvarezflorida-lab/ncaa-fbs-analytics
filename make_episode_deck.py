"""Episode 1 Week 0 deck v3 — logo edition.
Motif: real school logos (ESPN 500px PNGs in decks/logos/, URLs cached in
rosters/data/teams_fbs_2026.json) on white pucks over navy. Navy score-bug
panel per game with the model/market numbers and a win-probability split
bar. Dark title + dark 'The Card' closer around light content slides."""

import os

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

NAVY = RGBColor(0x0A, 0x28, 0x51)
NAVY2 = RGBColor(0x12, 0x35, 0x68)
ORANGE = RGBColor(0xF4, 0x73, 0x21)
ICE = RGBColor(0xEA, 0xF0, 0xF8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
INK = RGBColor(0x16, 0x27, 0x3D)
MUTE = RGBColor(0x5C, 0x6B, 0x7E)
LIGHTLINE = RGBColor(0xD5, 0xDF, 0xEC)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)


def blank(bg=WHITE):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = bg
    return s


def txt(slide, x, y, w, h, text, size, color=INK, bold=False,
        align=PP_ALIGN.LEFT, italic=False, anchor=None, spacing=None):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    if anchor:
        tf.vertical_anchor = anchor
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        if spacing:
            p.space_after = Pt(spacing)
        r = p.add_run()
        r.text = line
        f = r.font
        f.name = "Arial"
        f.size = Pt(size)
        f.color.rgb = color
        f.bold = bold
        f.italic = italic
    return box


def shape(slide, kind, x, y, w, h, fill, line=None):
    sp = slide.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    sp.fill.solid()
    sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(1)
    sp.shadow.inherit = False
    return sp


def luminance(c):
    return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]


LOGO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "decks", "logos")


def logo_badge(slide, x, y, d, key, plate=False):
    """School logo at (x, y), d inches square. plate=True adds a white
    circular puck behind it — needed on navy (UVA's logo is navy)."""
    if plate:
        shape(slide, MSO_SHAPE.OVAL, x, y, d, d, WHITE)
        inset = d * 0.10
    else:
        inset = 0.0
    slide.shapes.add_picture(
        os.path.join(LOGO_DIR, TEAMS[key]["logo"]),
        Inches(x + inset), Inches(y + inset),
        Inches(d - 2 * inset), Inches(d - 2 * inset))


def wp_bar(slide, x, y, w, h, team_a, pct_a, col_a, team_b, pct_b, col_b,
           label_color=WHITE):
    """Broadcast-style split probability bar."""
    wa = w * pct_a / 100.0
    shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, RGBColor(*col_b))
    sp = shape(slide, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, max(wa, 0.6), h,
               RGBColor(*col_a))
    txt(slide, x + 0.08, y + h / 2 - 0.11, 2.4, 0.25,
        f"{team_a} {pct_a:.0f}%", 10.5, WHITE if luminance(col_a) < 150 else INK,
        bold=True)
    txt(slide, x + w - 2.48, y + h / 2 - 0.11, 2.4, 0.25,
        f"{pct_b:.0f}% {team_b}", 10.5,
        WHITE if luminance(col_b) < 150 else INK, bold=True,
        align=PP_ALIGN.RIGHT)


TEAMS = {
    "UNC": dict(code="UNC", color=(0x7B, 0xAF, 0xD4), logo="unc.png"),
    "TCU": dict(code="TCU", color=(0x4D, 0x19, 0x79), logo="tcu.png"),
    "NCSU": dict(code="NCSU", color=(0xCC, 0x00, 0x00), logo="ncsu.png"),
    "UVA": dict(code="UVA", color=(0x23, 0x2D, 0x4B), logo="uva.png"),
    "JSU": dict(code="JSU", color=(0xB5, 0x12, 0x1B), logo="jsu.png"),
    "NDSU": dict(code="NDSU", color=(0x0A, 0x56, 0x40), logo="ndsu.png"),
}

GAMES = [
    dict(
        a="UNC", b="TCU", vs="vs", title="North Carolina vs TCU",
        where="Dublin, Ireland · Aviva Stadium",
        sub="Sat Aug 29 · noon ET · ESPN · Aer Lingus Classic · Belichick year two opens abroad",
        machine="TCU –1.5", market="–6.5 / –8.5", value="5–7 pts on UNC",
        wp=("TCU", 54, "UNC", 46),
        decides=[
            "UNC rush offense #127 vs TCU rush defense #28 — June may find nothing",
            "UNC's path: Edwards at TCU's #103 pass defense",
            "TCU pass offense #29 vs UNC pass defense #49 — best-on-best",
            "Hidden yards: special teams UNC #31 vs TCU #84",
        ],
        honesty="Honesty check: UNC's −12.1 residual was 2025's biggest ACC market-overrating — the skepticism premium is earned.",
        lean="Lean: UNC ATS at −6.5 or worse · O/U no lean",
        players_a=[("Billy Edwards Jr.", "QB — Maryland grad; 2,881 yds/15 TD in 2024; Belichick's pick"),
                   ("Demon June", "RB — Corey's key, but see the run-front matchup"),
                   ("Jordan Shipp", "WR — the X"),
                   ("Trech Kekahuna", "slot")],
        players_b=[("Jaden Craig", "QB — grad transfer, first year as the guy post-Hoover"),
                   ("Jordan Dwyer", "WR"),
                   ("Ka'Morreun Pimpton", "TE"),
                   ("Markis Deal", "NT — anchors the #28 run front")],
    ),
    dict(
        a="NCSU", b="UVA", vs="at", title="NC State at Virginia",
        where="Charlottesville · Scott Stadium",
        sub="Sat Aug 29 · 3:30 ET · revenge of the 35-31 end-zone INT · UVA: 11 wins, ACC CG loss in 2025",
        machine="UVA –6.7", market="–3 / –6", value="3.7 pts on UVA at DK",
        wp=("UVA", 69, "NCSU", 31),
        decides=[
            "THE BOOKS DISAGREE BY A FULL FIELD GOAL — shop the number on air",
            "UVA's #26 pass defense vs CJ Bailey's #36 pass offense decides it",
            "NC State explosiveness bottom-third: sustain or stall",
            "Special teams: UVA #56 vs NCSU #101 — ST cost State two 2025 games",
        ],
        honesty="UVA's card weakness: turnover-luck regression + a senior-driven pass rush now gone.",
        lean="Lean: UVA — value at −3, fair at −6",
        players_a=[("CJ Bailey", "QB — yr 3; 3,105 yds, 25 TD at 68.8%; top-5 returning ACC QB"),
                   ("Duke Scott", "RB"),
                   ("JoJo Trader", "WR"),
                   ("Joseph Adedire", "DE")],
        players_b=[("Beau Pribula", "QB — Missouri transfer; named starter Jul 19; 11-9 TD-INT is the risk"),
                   ("Peyton Lewis", "RB"),
                   ("Rico Flores Jr.", "WR"),
                   ("Fisher Camac", "DE")],
    ),
    dict(
        a="JSU", b="NDSU", vs="at", title="Jacksonville State at North Dakota State",
        where="Fargo · Fargodome",
        sub="Sat Aug 29 · 5:30 ET · CBSSN · NDSU's first FBS game · 2015 FCS title rematch · ON THE UPSET BOARD",
        machine="NDSU –2.7", market="–10 → –7", value="+3 CLV banked",
        wp=("NDSU", 58, "JSU", 42),
        decides=[
            "JSU identity: #23 rush offense, back-to-back ~3,500-yard rushing seasons",
            "JSU pass game #107 — stack the box, make Creel throw",
            "JSU special teams #123 — hidden-yardage leaks compound indoors",
            "NDSU has no ratings history — ESPN's −8.3 is a guess; max uncertainty",
        ],
        honesty="July 14 YEL alert: JSU +10, edge 7.3 — the market has since moved 3+ points to the model's side.",
        lean="Model side: JSU at −7 or worse — already paid in line movement",
        players_a=[("Caden Creel", "QB — 2,600+ combined yds; dual-threat = Bison D's soft spot"),
                   ("Khristian Lando", "RB — the 'unleash' key"),
                   ("Khurtiss Perry", "DT"),
                   ("Jacob Cruz", "EDGE")],
        players_b=[("Nathan Hayes", "QB — FIRST career start; 'strongest arm since Wentz'"),
                   ("DJ Scott", "RB"),
                   ("Mekhi Collins", "WR"),
                   ("Rebuilt CB room", "the one unit with no returning proof")],
    ),
]

# ---------------- title slide ----------------
s = blank(NAVY)
txt(s, 0.9, 0.85, 11.5, 0.45, "EPISODE 1 · WEEK 0 · AUG 29, 2026", 14, ORANGE,
    bold=True)
txt(s, 0.9, 1.3, 11.5, 1.3, "Three Games, One Card", 46, WHITE, bold=True)
y = 3.0
for g in GAMES:
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, y, 11.5, 1.0, NAVY2)
    logo_badge(s, 1.15, y + 0.16, 0.68, g["a"], plate=True)
    logo_badge(s, 2.0, y + 0.16, 0.68, g["b"], plate=True)
    txt(s, 2.95, y + 0.14, 6.3, 0.45, g["title"], 17, WHITE, bold=True)
    txt(s, 2.95, y + 0.56, 6.3, 0.35, g["where"], 11,
        RGBColor(0xCA, 0xDC, 0xFC))
    txt(s, 9.3, y + 0.14, 2.9, 0.4, g["machine"], 16, ORANGE, bold=True,
        align=PP_ALIGN.RIGHT)
    txt(s, 9.3, y + 0.56, 2.9, 0.35, "machine", 10,
        RGBColor(0xCA, 0xDC, 0xFC), align=PP_ALIGN.RIGHT)
    y += 1.22
txt(s, 0.9, 6.75, 11.5, 0.5,
    "Machine = ESPN 2026 preseason FPI + 2.5 HFA, σ 13.5 · lines as of Aug 18 "
    "· model plays graded vs first-seen lines", 10.5,
    RGBColor(0x8F, 0xA5, 0xC4))

# ---------------- per-game slides ----------------
for g in GAMES:
    # -- numbers slide --
    s = blank()
    logo_badge(s, 0.9, 0.42, 0.8, g["a"])
    txt(s, 1.82, 0.52, 0.5, 0.5, g["vs"], 14, MUTE, align=PP_ALIGN.CENTER)
    logo_badge(s, 2.35, 0.42, 0.8, g["b"])
    txt(s, 3.45, 0.38, 8.9, 0.55, g["title"], 27, NAVY, bold=True)
    txt(s, 3.45, 0.94, 8.9, 0.35, g["sub"], 11, MUTE, italic=True)

    # left: what decides it
    txt(s, 0.9, 1.75, 7.2, 0.4, "WHAT DECIDES IT", 13, NAVY, bold=True)
    yy = 2.25
    for d in g["decides"]:
        shape(s, MSO_SHAPE.OVAL, 0.95, yy + 0.09, 0.14, 0.14, ORANGE)
        txt(s, 1.3, yy, 6.8, 0.8, d, 13.5)
        yy += 0.78
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, yy + 0.15, 7.2, 1.05, ICE)
    txt(s, 1.15, yy + 0.32, 6.7, 0.75, g["honesty"], 11.5, MUTE, italic=True)

    # right: navy score bug
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 8.5, 1.75, 3.9, 4.6, NAVY)
    txt(s, 8.8, 2.0, 3.3, 0.35, "THE NUMBER", 12, ORANGE, bold=True)
    txt(s, 8.8, 2.4, 3.3, 0.7, g["machine"], 30, WHITE, bold=True)
    txt(s, 8.8, 3.05, 3.3, 0.3, "machine", 10, RGBColor(0xCA, 0xDC, 0xFC))
    txt(s, 8.8, 3.45, 3.3, 0.55, g["market"], 22, WHITE, bold=True)
    txt(s, 8.8, 3.95, 3.3, 0.3, "market (DK / Bovada)", 10,
        RGBColor(0xCA, 0xDC, 0xFC))
    txt(s, 8.8, 4.35, 3.3, 0.45, g["value"], 16, ORANGE, bold=True)
    txt(s, 8.8, 4.78, 3.3, 0.3, "the gap", 10, RGBColor(0xCA, 0xDC, 0xFC))
    wa, pa, wb, pb = g["wp"]
    wp_bar(s, 8.8, 5.35, 3.3, 0.42, wa, pa, TEAMS[wa]["color"],
           wb, pb, TEAMS[wb]["color"])
    txt(s, 8.8, 5.85, 3.3, 0.3, "win probability (machine)", 9.5,
        RGBColor(0xCA, 0xDC, 0xFC))

    txt(s, 0.9, 6.85, 11.5, 0.4, g["lean"], 13, NAVY, bold=True)

    # -- players slide --
    s = blank()
    logo_badge(s, 0.9, 0.42, 0.8, g["a"])
    txt(s, 1.82, 0.52, 0.5, 0.5, g["vs"], 14, MUTE, align=PP_ALIGN.CENTER)
    logo_badge(s, 2.35, 0.42, 0.8, g["b"])
    txt(s, 3.45, 0.42, 8.9, 0.55, "Players to watch", 27, NAVY, bold=True)

    for col, (key, players) in enumerate(
            [(g["a"], g["players_a"]), (g["b"], g["players_b"])]):
        x = 0.9 + col * 6.0
        shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, 1.55, 5.65, 5.2, ICE)
        logo_badge(s, x + 0.3, 1.85, 0.62, key)
        txt(s, x + 1.1, 1.95, 4.2, 0.45, g["title"].split(" at ")[col]
            if " at " in g["title"] and col < 2 else "", 1, ICE)  # spacer
        txt(s, x + 1.1, 1.92, 4.3, 0.5,
            {"UNC": "North Carolina", "TCU": "TCU", "NCSU": "NC State",
             "UVA": "Virginia", "JSU": "Jacksonville State",
             "NDSU": "North Dakota State"}[key], 17, INK, bold=True)
        yy = 2.75
        for name, note in players:
            txt(s, x + 0.35, yy, 5.0, 0.35, name, 14.5, INK, bold=True)
            txt(s, x + 0.35, yy + 0.34, 5.0, 0.55, note, 11.5, MUTE)
            yy += 0.98
    txt(s, 0.9, 6.95, 11.5, 0.35, "EP 1 · WEEK 0 · " + g["title"], 9.5, MUTE)

# ---------------- closing card ----------------
s = blank(NAVY)
txt(s, 0.9, 0.7, 11.5, 0.45, "EPISODE 1 · THE CARD", 14, ORANGE, bold=True)
txt(s, 0.9, 1.15, 11.5, 0.9, "Where the machine stands", 38, WHITE, bold=True)
y = 2.5
for g in GAMES:
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, y, 11.5, 1.15, NAVY2)
    logo_badge(s, 1.15, y + 0.24, 0.68, g["a"], plate=True)
    logo_badge(s, 2.0, y + 0.24, 0.68, g["b"], plate=True)
    txt(s, 2.95, y + 0.16, 5.6, 0.45, g["title"], 16, WHITE, bold=True)
    txt(s, 2.95, y + 0.6, 5.6, 0.4, g["lean"].replace("Lean: ", "").replace(
        "Model side: ", ""), 12, RGBColor(0xCA, 0xDC, 0xFC))
    txt(s, 8.7, y + 0.16, 3.5, 0.4, g["machine"] + "   ·   " + g["market"],
        14, ORANGE, bold=True, align=PP_ALIGN.RIGHT)
    txt(s, 8.7, y + 0.6, 3.5, 0.35, "machine · market", 9.5,
        RGBColor(0x8F, 0xA5, 0xC4), align=PP_ALIGN.RIGHT)
    y += 1.38
txt(s, 0.9, 6.85, 11.5, 0.5,
    "Paper record starts Week 0 — graded vs first-seen lines, never moved "
    "ones. Research, not picks.", 11, RGBColor(0x8F, 0xA5, 0xC4), italic=True)

out = r"C:\Users\lucas\Fun Projects\Sports Data Analysis\ncaa-fbs-model\decks\2026_Week0_Episode1.pptx"
prs.save(out)
print("wrote", out, "- 8 slides")
