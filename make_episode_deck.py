"""Episode 1 Week 0 deck — logo edition + 2025 stat lines.
Player notes carry 2025 season stats (CFBD /stats/player/season, incl.
Harvard and NDSU FCS rows; transfers credited to their 2025 team).
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
    "HAW": dict(code="HAW", color=(0x00, 0x34, 0x20), logo="hawaii.png"),
    "STAN": dict(code="STAN", color=(0x8C, 0x15, 0x15), logo="stanford.png"),
    "MEM": dict(code="MEM", color=(0x00, 0x49, 0x91), logo="memphis.png"),
    "UNLV": dict(code="UNLV", color=(0xB1, 0x02, 0x02), logo="unlv.png"),
}

NAME2CODE = {"North Carolina": "UNC", "TCU": "TCU", "NC State": "NCSU",
             "Virginia": "UVA", "Jacksonville State": "JSU",
             "North Dakota State": "NDSU", "Hawai'i": "HAW",
             "Stanford": "STAN", "Memphis": "MEM", "UNLV": "UNLV"}

# ---- card_data contract (review item A): market + model numbers come from
# edge_report.py --publish, never from hand-typed literals. Narrative fields
# (decides / honesty / lean / players) stay authored here.
CARD_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "card_data_week1.json")


def load_card_data():
    if not os.path.exists(CARD_DATA):
        return {}, None
    import json
    d = json.load(open(CARD_DATA, encoding="utf-8"))
    return {(g["away"], g["home"]): g for g in d["games"]}, d.get("lines_as_of")


def _dash(x):
    """-7.5 -> '–7.5', 3 -> '+3' (home-perspective spread for display)."""
    return f"–{abs(x):g}" if x < 0 else (f"+{x:g}" if x > 0 else "PK")


def _fmt_ts(ts):
    import datetime as dt
    if not ts:
        return "?"
    t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    t = t.astimezone(dt.timezone(dt.timedelta(hours=-4)))  # ET in August
    return f"{t:%b %d}".replace(" 0", " ")


CARD, LINES_TS = load_card_data()
LINES_AS_OF = _fmt_ts(LINES_TS) if LINES_TS else "Aug 23"
CODE2NAME = {v: k for k, v in NAME2CODE.items()}


def load_qual_flags():
    """cards/week1_flags.json — the qualitative overlay (review item D):
    {team: [{type, text, source, date, confidence}]}. Missing file = none."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "cards", "week1_flags.json")
    if not os.path.exists(path):
        return {}
    import json
    return json.load(open(path, encoding="utf-8"))


QUAL_FLAGS = load_qual_flags()


def _american(p):
    """Fair (no-vig) American odds for win prob p."""
    if p >= 0.5:
        return f"–{round(100 * p / (1 - p))}"
    return f"+{round(100 * (1 - p) / p)}"


def _book_line(margin):
    """Model margin -> the half-point line a book would post (home persp.)."""
    x = round(margin * 2) / 2
    return x


def apply_card(g):
    """Overlay pipeline numbers onto a GAMES entry; returns the ledger strip
    text and flags (empty if the game isn't in card_data)."""
    c = CARD.get(g["cfbd"])
    if not c:
        return "", []
    ha, hb = NAME2CODE[c["home"]], NAME2CODE[c["away"]]
    disp = {"STAN": "Stanford"}
    m = c["model_margin"]
    ph_raw = c["model_p_home"]
    # 1) the machine's line the way a book posts it (half points)
    line = _book_line(m)
    fav, num = (ha, line) if line >= 0 else (hb, -line)
    g["machine"] = (f"{disp.get(fav, fav)} –{num:g}" if num else "PK")
    g["raw_margin"] = f"{disp.get(ha, ha)} {m:+.1f}" if m >= 0 else f"{disp.get(hb, hb)} {-m:+.1f}"
    # 2) fair moneylines, both sides, from the model's win prob (no vig)
    g["fair"] = (f"{disp.get(ha, ha)} {_american(ph_raw)} · "
                 f"{disp.get(hb, hb)} {_american(1 - ph_raw)}")
    # 3) projected score = model margin laid over the MARKET total (the
    #    pipeline has no totals model; say so on the card)
    total = c.get("ou")
    if total is not None:
        hp, ap = (float(total) + m) / 2, (float(total) - m) / 2
        order = [(ha, hp), (hb, ap)] if hp >= ap else [(hb, ap), (ha, hp)]
        g["score"] = " – ".join(f"{disp.get(t, t)} {round(p)}" for t, p in order)
        g["score_note"] = f"projected score · machine margin on the {float(total):g} market total"
    else:
        g["score"], g["score_note"] = "", ""
    books = c.get("books") or {}
    dk, bov = books.get("DraftKings", {}).get("spread"), books.get("Bovada", {}).get("spread")
    parts = [_dash(x) for x in (dk, bov) if x is not None]
    g["market"] = " / ".join(parts) if parts else c["mkt_spread"]
    mls = []
    for bname, short in (("DraftKings", "DK"), ("Bovada", "Bov")):
        b = books.get(bname) or {}
        if b.get("home_ml") is not None and b.get("away_ml") is not None:
            mls.append(f"{short} {disp.get(ha, ha)} {int(b['home_ml']):+d} / "
                       f"{disp.get(hb, hb)} {int(b['away_ml']):+d}")
    g["market_ml"] = " · ".join(mls)
    ph = round(ph_raw * 100)
    g["wp"] = (ha, ph, hb, 100 - ph)
    strip = ""
    if c.get("first_spread") is not None:
        strip = (f"first-seen {_dash(c['first_spread'])} ({_fmt_ts(c['first_ts'])}) "
                 f"→ now {_dash(c['now_spread'])}")
        if c.get("opener") is not None:
            strip += f" · opened {_dash(c['opener'])}"
        if c.get("clv") is not None:
            strip += f" · CLV {c['clv']:+g}"
    flags = [f for f in (c.get("flags") or "").split() if f]
    if c.get("mkt_src") == "ml":
        strip += f" · market ML {c['mkt_p_home']*100:.0f}% {ha}"
    return strip, flags

GAMES = [
    dict(
        a="UNC", b="TCU", vs="vs", title="North Carolina vs TCU",
        cfbd=("North Carolina", "TCU"),
        where="Dublin, Ireland · Aviva Stadium",
        sub="Sat Aug 29 · noon ET · ESPN · Aer Lingus Classic · Belichick year two opens abroad",
        machine="TCU –1.5", market="–7.5 / –8", value="6–6.5 pts on UNC",
        wp=("TCU", 54, "UNC", 46),
        decides=[
            "UNC rush offense #127 vs TCU rush defense #28 — June may find nothing",
            "UNC's path: Edwards at TCU's #103 pass defense",
            "TCU pass offense #29 vs UNC pass defense #49 — best-on-best",
            "STRUCTURAL DISAGREEMENT: moneyline says TCU ~73%, machine says 54% — an 18-pt gap, not a spread quibble",
        ],
        honesty="Honesty check: UNC's −12.1 residual was 2025's biggest ACC market-overrating — the skepticism premium is earned. Line moved from −6.5 to −7.5 since Aug 18: the market is leaning further into TCU, not toward us.",
        lean="Lean: UNC ATS at −7.5 — research, not a play, while the win-prob gap is this wide · O/U no lean",
        players_a=[("Billy Edwards Jr.", "QB — Maryland grad; 2,881 yds/15 TD in '24; '25 at Wisconsin lost to injury (7/16, 113 yds); Belichick's pick"),
                   ("Demon June", "RB — 2025: 464 yds at 5.5/carry, 3 total TD — Corey's key, but see the run-front matchup"),
                   ("Jordan Shipp", "WR — the X; 2025: 60 rec, 671 yds, 6 TD"),
                   ("Trech Kekahuna", "slot — 2025 at Wisconsin: 26 rec, 211 yds; 129 rush yds, 1 TD")],
        players_b=[("Jaden Craig", "QB — Harvard grad transfer; 2025: 61.6%, 2,829 yds, 25-7; first year as the guy post-Hoover"),
                   ("Jordan Dwyer", "WR — 2025: 54 rec, 730 yds, 7 TD (13.5 avg)"),
                   ("Ka'Morreun Pimpton", "TE — 2025: just 1 catch (a TD)"),
                   ("Markis Deal", "NT — anchors the #28 run front; 2025: 26 tkl, 2 TFL, 1 sack")],
    ),
    dict(
        a="NCSU", b="UVA", vs="at", title="NC State at Virginia",
        cfbd=("NC State", "Virginia"),
        where="Charlottesville · Scott Stadium",
        sub="Sat Aug 29 · 3:30 ET · revenge of the 35-31 end-zone INT · UVA: 11 wins, ACC CG loss in 2025",
        machine="UVA –6.7", market="–5.5 / –5.5", value="EDGE GONE — market converged",
        wp=("UVA", 65, "NCSU", 35),
        decides=[
            "The books converged: −3 / −6 on Aug 18 → −5.5 everywhere by Aug 22 — the edge we stated is gone",
            "UVA's #26 pass defense vs CJ Bailey's #36 pass offense decides it",
            "NC State explosiveness bottom-third: sustain or stall",
            "Special teams: UVA #56 vs NCSU #101 — ST cost State two 2025 games",
        ],
        honesty="UVA's +11.7 residual (11th-highest in FBS) says ESPN rates them well above what public inputs explain — and the roster lost 6 of its top 7 receivers and its senior pass rush. The machine's −6.7 is the stalest number on this card.",
        lean="No play: value was at −3, fair is −6, the market sits at −5.5 · machine still leans UVA",
        players_a=[("CJ Bailey", "QB — yr 3; 2025: 3,105 yds, 25-9 at 68.8%; top-5 returning ACC QB"),
                   ("Duke Scott", "RB — 2025: 595 yds at 5.6/carry, 4 TD, plus 15 catches (Jayden on the stat sheet)"),
                   ("JoJo Trader", "WR — Miami transfer; 2025: 13 rec, 178 yds, 1 TD"),
                   ("Joseph Adedire", "DE — 2025: 6 tkl, 2 TFL, 1 sack")],
        players_b=[("Beau Pribula", "QB — Missouri transfer; 2025: 67.4%, 1,946 yds, 11-9 TD-INT (+6 rush TD); named starter Jul 15 at ACC Kickoff"),
                   ("Peyton Lewis", "RB — Tennessee transfer; 2025: 290 yds, 7 TD on 70 carries"),
                   ("Rico Flores Jr.", "WR — UCLA transfer; 2025: 26 rec, 274 yds"),
                   ("Fisher Camac", "DE — 2025: 44 tkl, 5.5 TFL, 3.5 sacks")],
    ),
    dict(
        a="JSU", b="NDSU", vs="at", title="Jacksonville State at North Dakota State",
        cfbd=("Jacksonville State", "North Dakota State"),
        where="Fargo · Fargodome",
        sub="Sat Aug 29 · 5:30 ET · CBSSN · NDSU's first FBS game · 2015 FCS title rematch · ON THE UPSET BOARD",
        machine="NDSU –2.7", market="–10 → –7", value="+3 CLV banked",
        wp=("NDSU", 57, "JSU", 43),
        decides=[
            "JSU identity: #23 rush offense, back-to-back ~3,500-yard rushing seasons",
            "JSU pass game #107 — stack the box, make Creel throw",
            "JSU special teams #123 — hidden-yardage leaks compound indoors",
            "NDSU has no ratings history — ESPN's −8.3 is a guess; max uncertainty",
        ],
        honesty="July 14 YEL alert: JSU +10, edge 7.3 — the market has since moved 3 points to the model's side (−7 at both books Aug 23). MAX UNCERTAINTY: NDSU has zero FBS ratings history, so the 57% deserves a range, not a point.",
        lean="Model side: JSU at −7 or worse — already paid in line movement",
        players_a=[("Caden Creel", "QB — 2025: 1,514 pass + 1,075 rush (5.9/carry), 16 total TD; dual-threat = Bison D's soft spot"),
                   ("Khristian Lando", "RB — the 'unleash' key; 2025: 201 yds on 51 carries behind Creel"),
                   ("Khurtiss Perry", "DT — 2025: 20 tkl, 4.5 TFL, 2 sacks"),
                   ("Jacob Cruz", "EDGE — 2025: 14 tkl, 1.5 TFL, 1 INT")],
        players_b=[("Nathan Hayes", "QB — FIRST career start; 2025 in relief: 25/44, 381 yds, 4-1, plus 88 rush yds; 'strongest arm since Wentz'"),
                   ("DJ Scott", "RB — 2025: 502 yds at 5.3/carry, 6 TD"),
                   ("Mekhi Collins", "WR — 2025: 6 catches, 159 yds, 2 TD — 26.5 per grab"),
                   ("Rebuilt CB room", "the one unit with no returning proof")],
    ),
    dict(
        a="HAW", b="STAN", vs="at", title="Hawai'i at Stanford",
        cfbd=("Hawai'i", "Stanford"),
        where="Palo Alto · Stanford Stadium",
        sub="Sat Aug 29 · 7:00 ET · ACC Network · Pritchard's first game · the machine rates Hawai'i the better team",
        machine="Stanford –1.6", market="–5.5 / –5.5", value="3.9 pts on Hawai'i",
        wp=("STAN", 54, "HAW", 46),
        decides=[
            "Neither side can run: Stanford rush offense #128 vs Hawai'i rush D #70; Hawai'i rush O #117 vs Stanford's #15 front",
            "So it's Alejado (#52 pass offense) at Stanford's #115 pass defense — the run-and-shoot's whole path",
            "Stanford QB Davis Warren: zero 2025 snaps at Michigan, career 7 TD–10 INT — unmodeled QB-tier risk",
            "Hawai'i's #8 special teams was Matsuzawa (27/29) + Barfield's return TD — the kicker is gone; unit rank overstates",
        ],
        honesty="Hawai'i's +5.8 residual: ESPN's 2025 rating ran ahead of its inputs, and the two sack leaders left. The line moved −3 → −5.5 toward Stanford since it opened — the market is not buying the machine's Hawai'i lean.",
        lean="Lean: Hawai'i +5.5 — a 4-pt gap, not a conviction; the opener at +3 was the worse number",
        players_a=[("Micah Alejado", "QB — MWC Preseason POY; 2025: 66.3%, 3,106 yds, 24-9"),
                   ("Pofele Ashlock", "WR — 2025: 76 rec, 827 yds, 8 TD; the top target left (Jackson Harris, 963 yds)"),
                   ("Cam Barfield", "RB/KR — 2025: 371 rush yds, 4 TD; 28.7 per kick return with an 86-yd TD"),
                   ("Lesterlaisene Lagafuaina", "DL — 2025: 7.5 TFL, 3.5 sacks; the returning piece of a front that lost both sack leaders")],
        players_b=[("Davis Warren", "QB — Michigan transfer; 2025: no stat line (backup); career 5.4 yds/dropback, 7 TD–10 INT"),
                   ("Micah Ford", "RB — 2025: 643 yds at 4.4/carry, 4 TD, plus 11 catches"),
                   ("Nico Brown", "WR — Yale transfer; 2025: 71 rec, 1,085 yds, 11 TD in the Ivy"),
                   ("Matt Rose", "ILB — 2025: team-high 106 tkl, 8 TFL, 3 sacks")],
    ),
    dict(
        a="MEM", b="UNLV", vs="at", title="Memphis at UNLV",
        cfbd=("Memphis", "UNLV"),
        where="Las Vegas · Allegiant Stadium",
        sub="Sat Aug 29 · 10:00 ET · FOX · G5 heavyweight opener · Huff's 53-transfer debut · first film_study game",
        machine="UNLV –6.2", market="–5.5 / –5.5", value="market came to us: –3 → –5.5",
        wp=("UNLV", 64, "MEM", 36),
        decides=[
            "Memphis rush offense #5 vs UNLV rush defense #130 — but that #5 was Silverfield's roster; Huff flipped 53 players (111th returning production)",
            "UNLV rush offense #9 (Thomas, 7.0 a carry) vs Memphis rush D #20 — now led by transfers",
            "Arnold (#32 pass O context) at Memphis's #118 pass defense; Memphis's QB derby is a zero-FBS-snap tier",
            "Memphis's #16 special teams was Sutton Smith's 99-yd return TD — he's gone; UNLV #65",
        ],
        honesty="The machine's −6.2 is built on 2025 unit ranks for a Memphis roster that is 53 transfers new — both sides' numbers are stale in opposite directions. Residuals are flat (MEM −1.8, UNLV +0.7); the line already moved to our side.",
        lean="Model side UNLV — the edge was at −3 and it's gone; at −5.5 this is a watch and the first film_study run, not a play",
        players_a=[("Air Noland / Marcus Stokes", "QB derby — Noland threw 3 passes at South Carolina in 2025; Stokes: 3,297 yds, 30 TD at D-II West Florida"),
                   ("Dallan Hayden", "RB — Colorado transfer; 2025: 326 yds at 4.7/carry, 1 TD"),
                   ("Tychaun Chapman", "WR — Southern Miss transfer; 2025: 24 rec, 444 yds, 3 TD"),
                   ("J'Mond Tapp", "DL — Southern Miss transfer; 2025: 69 tkl, 12 TFL, 7.5 sacks, 10 hurries")],
        players_b=[("Jackson Arnold", "QB — Auburn transfer; 2025: 63.3%, 1,309 yds, 6-2, +311 rush/8 TD in 8 starts (4-4); Orji still pushing"),
                   ("Jai'Den Thomas", "RB — MW POY candidate; 2025: 1,034 yds at 7.0/carry, 12 TD, +38 catches"),
                   ("Rebuilt WR room", "every 2025 target gone (Bradley 931, Omeire, Reynolds); Reddicks, Stellato, Walker via portal"),
                   ("Dee Crayton", "LB — Clemson transfer; 2025: 5 tkl as a reserve — the defense's 'patch' is unproven")],
    ),
]

# overlay pipeline numbers (card_data) before any slide is built
LEDGER = {g["title"]: apply_card(g) for g in GAMES}
print("card_data:", "loaded, lines as of " + LINES_AS_OF if CARD else
      "NOT FOUND — using hand-typed numbers")

# ---------------- title slide ----------------
s = blank(NAVY)
txt(s, 0.9, 0.85, 11.5, 0.45, "EPISODE 1 · WEEK 0 · AUG 29, 2026", 14, ORANGE,
    bold=True)
txt(s, 0.9, 1.2, 11.5, 1.1, "Five Games, One Card", 44, WHITE, bold=True)
y = 2.4
for g in GAMES:
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, y, 11.5, 0.8, NAVY2)
    logo_badge(s, 1.1, y + 0.1, 0.6, g["a"], plate=True)
    logo_badge(s, 1.85, y + 0.1, 0.6, g["b"], plate=True)
    txt(s, 2.7, y + 0.1, 6.5, 0.4, g["title"], 15, WHITE, bold=True)
    txt(s, 2.7, y + 0.46, 6.5, 0.3, g["where"], 10,
        RGBColor(0xCA, 0xDC, 0xFC))
    txt(s, 9.3, y + 0.1, 2.9, 0.4, g["machine"], 15, ORANGE, bold=True,
        align=PP_ALIGN.RIGHT)
    txt(s, 9.3, y + 0.47, 2.9, 0.3, "machine", 9.5,
        RGBColor(0xCA, 0xDC, 0xFC), align=PP_ALIGN.RIGHT)
    y += 0.88
txt(s, 0.9, 6.85, 11.5, 0.5,
    "Machine = ESPN 2026 preseason FPI + 2.5 HFA, empirical margin curve "
    f"(σ 17.9, 2021–25 fit) · lines as of {LINES_AS_OF} · model plays graded vs "
    "first-seen lines", 10.5,
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
    PALE = RGBColor(0xCA, 0xDC, 0xFC)
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 8.5, 1.7, 3.9, 4.78, NAVY)
    txt(s, 8.8, 1.9, 3.3, 0.3, "THE NUMBER", 12, ORANGE, bold=True)
    # machine line as a book would post it + fair odds from our win prob
    txt(s, 8.8, 2.2, 3.3, 0.5, g["machine"], 26, WHITE, bold=True)
    txt(s, 8.8, 2.68, 3.3, 0.3, g.get("fair", ""), 11.5, WHITE, bold=True)
    txt(s, 8.8, 2.94, 3.3, 0.28,
        "machine line · fair odds, no vig · raw margin " + g.get("raw_margin", ""),
        8.5, PALE)
    # projected score (model margin over the market total)
    txt(s, 8.8, 3.3, 3.3, 0.4, g.get("score", ""), 17, WHITE, bold=True)
    txt(s, 8.8, 3.64, 3.3, 0.28, g.get("score_note", ""), 8.5, PALE)
    # market
    txt(s, 8.8, 3.98, 3.3, 0.4, g["market"], 17, WHITE, bold=True)
    txt(s, 8.8, 4.32, 3.3, 0.4, "market (DK / Bovada) · " + g.get("market_ml", ""),
        8.5, PALE)
    # the gap (authored)
    txt(s, 8.8, 4.72, 3.3, 0.35, g["value"], 14 if len(g["value"]) <= 20 else 11.5,
        ORANGE, bold=True)
    txt(s, 8.8, 5.02, 3.3, 0.25, "the gap", 8.5, PALE)
    wa, pa, wb, pb = g["wp"]
    wp_bar(s, 8.8, 5.34, 3.3, 0.4, wa, pa, TEAMS[wa]["color"],
           wb, pb, TEAMS[wb]["color"])
    txt(s, 8.8, 5.8, 3.3, 0.25, "win probability (machine)", 8.5, PALE)
    strip, flags = LEDGER[g["title"]]
    if flags:
        txt(s, 8.8, 6.07, 3.3, 0.3, "FLAGS  " + " · ".join(flags), 9.5,
            ORANGE, bold=True)
    if strip:
        txt(s, 0.9, 6.62, 11.5, 0.25, "Line ledger: " + strip, 9, MUTE)

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
        has_flags = bool(QUAL_FLAGS.get(CODE2NAME[key]))
        shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, 1.55, 5.65,
              5.5 if has_flags else 5.2, ICE)
        logo_badge(s, x + 0.3, 1.85, 0.62, key)
        txt(s, x + 1.1, 1.95, 4.2, 0.45, g["title"].split(" at ")[col]
            if " at " in g["title"] and col < 2 else "", 1, ICE)  # spacer
        txt(s, x + 1.1, 1.92, 4.3, 0.5,
            {"UNC": "North Carolina", "TCU": "TCU", "NCSU": "NC State",
             "UVA": "Virginia", "JSU": "Jacksonville State",
             "NDSU": "North Dakota State", "HAW": "Hawai'i",
             "STAN": "Stanford", "MEM": "Memphis", "UNLV": "UNLV"}[key],
            17, INK, bold=True)
        team_flags = QUAL_FLAGS.get(CODE2NAME[key], [])
        pitch = 0.84 if team_flags else 0.98
        yy = 2.75
        for name, note in players:
            txt(s, x + 0.35, yy, 5.0, 0.35, name, 14.5, INK, bold=True)
            txt(s, x + 0.35, yy + 0.34, 5.0, 0.55, note, 11.5, MUTE)
            yy += pitch
        if team_flags:
            # qualitative overlay (review item D): cards/week1_flags.json —
            # displayed, not priced
            shape(s, MSO_SHAPE.RECTANGLE, x + 0.35, yy + 0.02, 5.0, 0.012,
                  RGBColor(0xF4, 0x73, 0x21))
            txt(s, x + 0.35, yy + 0.07, 5.0, 0.7,
                "FLAGS  " + " · ".join(f["text"] for f in team_flags[:3]),
                9.5, RGBColor(0xB6, 0x4F, 0x0F), bold=True)
    txt(s, 0.9, 7.13, 11.5, 0.3, "EP 1 · WEEK 0 · " + g["title"], 9, MUTE)

# ---------------- closing card ----------------
s = blank(NAVY)
txt(s, 0.9, 0.7, 11.5, 0.45, "EPISODE 1 · THE CARD", 14, ORANGE, bold=True)
txt(s, 0.9, 1.1, 11.5, 0.9, "Where the machine stands", 36, WHITE, bold=True)
y = 2.15
for g in GAMES:
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, y, 11.5, 0.84, NAVY2)
    logo_badge(s, 1.1, y + 0.12, 0.6, g["a"], plate=True)
    logo_badge(s, 1.85, y + 0.12, 0.6, g["b"], plate=True)
    txt(s, 2.7, y + 0.08, 5.9, 0.4, g["title"], 14.5, WHITE, bold=True)
    txt(s, 2.7, y + 0.44, 6.3, 0.38, g["lean"].replace("Lean: ", "").replace(
        "Model side: ", "").replace("Model side ", ""), 10, RGBColor(0xCA, 0xDC, 0xFC))
    txt(s, 9.0, y + 0.08, 3.2, 0.4, g["machine"] + "   ·   " + g["market"],
        12.5, ORANGE, bold=True, align=PP_ALIGN.RIGHT)
    txt(s, 9.0, y + 0.46, 3.2, 0.3, "machine · market", 9,
        RGBColor(0x8F, 0xA5, 0xC4), align=PP_ALIGN.RIGHT)
    y += 0.92
txt(s, 0.9, 6.85, 11.5, 0.5,
    "Paper record starts Week 0 — graded vs first-seen lines, never moved "
    "ones. Research, not picks.", 11, RGBColor(0x8F, 0xA5, 0xC4), italic=True)

out = r"C:\Users\lucas\Fun Projects\Sports Data Analysis\ncaa-fbs-model\decks\2026_Week0_Episode1.pptx"
prs.save(out)
print("wrote", out, f"- {len(prs.slides)} slides")
