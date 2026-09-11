"""Episode 3 Week 2 deck — the frozen Ep2 template with Week 2 data.
Slide 2 is the Week 1 receipts board (frozen Ep2 predictions graded vs
finals and the last pre-kick ledger pull; finals are looked up from the
CFBD games cache so a pending game fills itself in after the refresh).
Per-game flow unchanged: why it matters -> one slide per team -> closing
card with score predictions + superdogs. Ep1/Ep2 GAMES blocks are archived
below as _GAMES_EP1/_GAMES_EP2 (frozen predictions live in git + ledger).
Rule (Lucas 9/7): slides stay lean; all depth lives in week{N}_ep{M}_podcast.md.
Rule (Lucas 9/11): slide text is the HEADLINE only — keys are 2-6 words
("Attack Poppinga early"), WHY IT MATTERS is one line each, the honesty
box is one sentence. The sentence behind every headline lives in the notes.
SHORT below carries the slide text; long-form strings stay in GAMES as the
archive of the reasoning.
Motif: real school logos (ESPN 500px PNGs in decks/logos/, URLs cached in
rosters/data/teams_fbs_2026.json) on white pucks over navy. Navy score-bug
panel per game with the model/market numbers and a win-probability split
bar. Dark title + dark 'The Card' closer around light content slides."""

import os
import sys

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

EPISODE, WEEK = 3, 2
RENDER_UPSET_BOARD = False   # Lucas 9/9: off; flip to True to add the alerts slide before the closer
EP_DATE = "SEP 12, 2026"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "fpi-decomposition"))
from name_mapping import normalize_name  # noqa: E402

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
    "BAY": dict(code="BAY", color=(0x15, 0x45, 0x35), logo="baylor.png"),
    "AUB": dict(code="AUB", color=(0x0C, 0x24, 0x40), logo="auburn.png"),
    "CLEM": dict(code="CLEM", color=(0xF6, 0x67, 0x33), logo="clemson.png"),
    "LSU": dict(code="LSU", color=(0x46, 0x1D, 0x7C), logo="lsu.png"),
    "LOU": dict(code="LOU", color=(0xAD, 0x00, 0x00), logo="louisville.png"),
    "MISS": dict(code="MISS", color=(0x14, 0x21, 0x3D), logo="olemiss.png"),
    "WIS": dict(code="WIS", color=(0xC5, 0x05, 0x0C), logo="wisconsin.png"),
    "ND": dict(code="ND", color=(0x0C, 0x23, 0x40), logo="notredame.png"),
    "SMU": dict(code="SMU", color=(0x00, 0x33, 0xA0), logo="smu.png"),
    "FSU": dict(code="FSU", color=(0x78, 0x2F, 0x40), logo="fsu.png"),
    "OSU": dict(code="OSU", color=(0xBB, 0x00, 0x00), logo="ohiostate.png"),
    "TEX": dict(code="TEX", color=(0xBF, 0x57, 0x00), logo="texas.png"),
    "OU": dict(code="OU", color=(0x84, 0x16, 0x17), logo="oklahoma.png"),
    "MICH": dict(code="MICH", color=(0x00, 0x27, 0x4C), logo="michigan.png"),
    "ASU": dict(code="ASU", color=(0x8C, 0x1D, 0x40), logo="arizonastate.png"),
    "TAMU": dict(code="TAMU", color=(0x50, 0x00, 0x00), logo="texasam.png"),
    "ARIZ": dict(code="ARIZ", color=(0x0C, 0x23, 0x4B), logo="arizona.png"),
    "BYU": dict(code="BYU", color=(0x00, 0x22, 0xE0), logo="byu.png"),
    "BAMA": dict(code="BAMA", color=(0x9E, 0x16, 0x32), logo="alabama.png"),
    "UK": dict(code="UK", color=(0x00, 0x33, 0xA0), logo="kentucky.png"),
}

NAME2CODE = {"North Carolina": "UNC", "TCU": "TCU", "NC State": "NCSU",
             "Virginia": "UVA", "Jacksonville State": "JSU",
             "North Dakota State": "NDSU", "Hawai'i": "HAW",
             "Stanford": "STAN", "Memphis": "MEM", "UNLV": "UNLV",
             "Baylor": "BAY", "Auburn": "AUB", "Clemson": "CLEM",
             "LSU": "LSU", "Louisville": "LOU", "Ole Miss": "MISS",
             "Wisconsin": "WIS", "Notre Dame": "ND", "SMU": "SMU",
             "Florida State": "FSU", "Ohio State": "OSU", "Texas": "TEX",
             "Oklahoma": "OU", "Michigan": "MICH", "Arizona State": "ASU",
             "Texas A&M": "TAMU", "Arizona": "ARIZ", "BYU": "BYU",
             "Alabama": "BAMA", "Kentucky": "UK"}

# ---- card_data contract (review item A): market + model numbers come from
# edge_report.py --publish, never from hand-typed literals. Narrative fields
# (decides / honesty / keys) stay authored here; lean + players are kept as
# data but no longer rendered.
CARD_DATA = os.path.join(HERE, f"card_data_week{WEEK}.json")


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
    t = t.astimezone(dt.timezone(dt.timedelta(hours=-4)))  # EDT
    return f"{t:%b %d}".replace(" 0", " ")


CARD, LINES_TS = load_card_data()
LINES_AS_OF = _fmt_ts(LINES_TS) if LINES_TS else "?"
CODE2NAME = {v: k for k, v in NAME2CODE.items()}


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
    """Overlay pipeline numbers onto a GAMES entry; returns the line-movement
    strip text (empty if the game isn't in card_data). Also sets g["move"],
    the compact first-seen → now form for the score bug."""
    c = CARD.get(g["cfbd"])
    if not c:
        return "", []
    ha, hb = NAME2CODE[c["home"]], NAME2CODE[c["away"]]
    disp = CODE2NAME
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
        g["score"] = " – ".join(f"{disp.get(t, t)} {int(p + 0.5)}" for t, p in order)
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
    first, now, clv = c.get("first_spread"), c.get("now_spread"), c.get("clv")
    # sides-flip guard: a first-seen with the opposite sign and an absurd CLV
    # is a known CFBD data error (e.g. Wisconsin-ND Jul 14) — fall back to the
    # book opener as the honest starting point and drop the corrupt CLV.
    flipped = (first is not None and now is not None and first * now < 0
               and clv is not None and abs(clv) > 20)
    if flipped:
        first, clv = c.get("opener"), None
    if first is not None:
        if flipped:
            strip = (f"opened {_dash(first)} → now {_dash(now)} "
                     "(first-seen excluded: sides-flip data error)")
        else:
            strip = (f"first-seen {_dash(first)} ({_fmt_ts(c['first_ts'])}) "
                     f"→ now {_dash(now)}")
            if c.get("opener") is not None and c["opener"] != first:
                strip += f" · opened {_dash(c['opener'])}"
            if clv is not None:
                strip += f" · CLV {clv + 0:+g}"
        g["move"] = f"{_dash(first)} → {_dash(now)}"
        if clv:
            g["move"] += f" · CLV {clv:+g}"
    return strip

_GAMES_EP1 = [  # Week 0 archive — the frozen Ep1 predictions (unrendered)
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
                keys_a=["Throw it — TCU's pass defense is the soft spot; the run game is closed", 'Win the hidden yards — the special-teams edge is real', "Bend-don't-break without Steve Belichick: keep the defense simple", 'Keep the circus outside: a clean, scripted first quarter'],
        keys_b=['Craig efficient, not heroic — distribute to a loaded receiver room', 'Make UNC one-dimensional with the run front, then rush the passer', 'Hold up in the back end with a new starting safety', 'Dwyer in the return game: the weapon inside a mediocre unit'],
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
                keys_a=['Bailey has to beat an elite pass defense with a rebuilt receiver room', 'Establish Duke Scott to stay out of obvious passing downs', 'Stop losing games on special teams', 'Make Pribula the story — pressure with the new edges'],
        keys_b=['Pribula ball security: no giveaways, no hero throws', 'Ride the veteran O-line and the run game', 'Replace the pass rush, not just the pass rushers', 'Let the pass defense win the rebuilt-receiver matchup'],
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
        honesty="July 14 YEL alert: JSU +10, edge 7.3 — the market has since moved 3 points to our side (−7 at both books). MAX UNCERTAINTY: zero FBS ratings history, so the 57% deserves a range, not a point. And NDSU is FULLY ELIGIBLE — the NCAA repealed the transition ban Jun 24: MWC title game, bowls and the CFP are all open in year one.",
        lean="Model side: JSU at −7 or worse — already paid in line movement",
                keys_a=['Run into a front with no FBS tape — the identity must survive the RB change', "Stay ahead of the chains; don't make Creel throw 30 times", 'No hidden-yardage leaks indoors', 'Make Hayes beat you in his first start — disguise, third-and-long'],
        keys_b=['Protect Hayes early: scripted, short, on schedule', 'Lean on the run game and the O-line', "Tackle Creel in space — the rebuilt CB room's test", "Take the free points JSU's special teams give"],
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
                keys_a=['Volume through the air at a bottom-20 pass defense', "Find the targets if Ashlock can't go", "Keep Alejado upright against Stanford's one good unit — the run front", "Three stops, not ten — and don't lose the kicking game with a new kicker"],
        keys_b=['Warren efficient, not expansive — first game back from the ACL', 'Make the run game exist', 'Tackle in space against four wide', 'Hold serve on special teams'],
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
                keys_a=["Don't ask the (unannounced) quarterback to win it — run first", 'Run at the worst run defense in the league', 'Tapp has to get home on Arnold', 'Survive the hidden-yardage swing without Sutton Smith'],
        keys_b=["Feed Jai'Den Thomas", 'No turnovers from the quarterback, whoever it is', 'Make the new receivers real', "The run defense cannot be last year's unit against Huff-ball"],
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

_GAMES_EP2 = [  # Week 1 archive — the frozen Ep2 predictions (unrendered)
    dict(
        a="BAY", b="AUB", vs="vs", title="Baylor vs Auburn",
        cfbd=("Baylor", "Auburn"),
        where="Atlanta · Mercedes-Benz Stadium",
        sub="Sat Sep 5 · 3:30 ET · neutral site · Golesh's Auburn debut · Lagway's Baylor debut",
        machine="Auburn –5.5", market="–7 / –7", value="1.5 on Baylor · MONSTER UNDER under 59.5",
        wp=("AUB", 63, "BAY", 37),
        decides=[
            "Two rebooted programs, one neutral floor: Golesh's Auburn debut (USF's No. 2 total offense travels with him) vs Lagway's Baylor debut",
            "The starkest contrast on the card: Auburn returns 14% of its offense and rebuilt with 39 transfers — Baylor returns 60%, the most continuity here",
            "Lagway's health (shoulder and leg in 2025) is the Big 12 season's biggest single variable — Auburn's top-10 DL is the first test",
            "The 59.5 total is top-decile — five years of closing lines say that class goes UNDER 55% of the time, and two year-one offenses in a dome only helps",
        ],
        ctx_a=dict(coach="Aranda, year 6 — seat survived; new DC Klanderman (K-State)",
                   qb="NEW — DJ Lagway (Florida), biggest transfer get in program history",
                   roster="60% of offensive production back — most on this card · 31 portal adds"),
        ctx_b=dict(coach="NEW — Alex Golesh (USF) · Durkin RETAINED as DC",
                   qb="NEW and unsettled — open room after the Knight exit",
                   roster="14% back — most retooled roster on the card · 39 portal adds"),
        honesty="Both sidelines are running year-one installs the preseason numbers can't see — the machine's prior hasn't ingested a single 2026 snap. Auburn's edge is a talent prior; Baylor's counter is cohesion. Machine −5.5 vs market −7.5: a quibble, not a position.",
        keys_a=["Keep Lagway upright — his 2025 injury file is the season's whole risk profile; everything else is decoration",
                "Attack the rebuilt secondary: four transfer corners arrived — Auburn's front returned, the back end didn't",
                "Steal a possession with tempo — a halftime double-up covers the whole spread by itself",
                "Make the install-week offense chase: an early lead forces a unit that's never played together to hurry"],
        keys_b=["Lean on the defense that didn't change — 27 of the 39 transfers went to offense; Durkin's side kept its spine",
                "Tempo without turnovers: speed multiplies mistakes in week one of an install — take the give, live with punts",
                "Feed the tight ends where Golesh's 12-personnel system lives",
                "Win the line with top-10 DL talent — Lagway under duress is the whole ballgame"],
    ),
    dict(
        a="CLEM", b="LSU", vs="at", title="Clemson at LSU",
        cfbd=("Clemson", "LSU"),
        where="Baton Rouge · Tiger Stadium",
        sub="Sat Sep 5 · 7:30 ET · Kiffin's first game at LSU · Death Valley at night",
        machine="LSU –9", market="–10.5 / –10.5", value="1.5 to Clemson — quibble, not a play",
        wp=("LSU", 70, "CLEM", 30),
        decides=[
            "The biggest coaching debut of the season: Kiffin left a 13-win CFP team for this — first drive at night in Death Valley",
            "Dabo answers his worst season in 15 years with a throwback: Morris back as OC, first-year QB Vizzina — and Clemson opens UNRANKED vs No. 11",
            "Opposite repair jobs: LSU rebuilt with 44 transfers (21% back), Clemson added just 11 (41% back) — Saturday tells us which was right",
            "The market opened −11.5 and has walked to −10, toward the machine's −9 all week — and the loser burns a playoff mulligan",
        ],
        honesty="The machine's −9.1 is a preseason guess about a program running its second system and second staff inside one calendar year — and Clemson's offense is just as new. Install-week variance says treat every number here gently; 30–21 is a margin on a market total, not a script.",
        ctx_a=dict(coach="Dabo, year 18 — Chad Morris returns as OC",
                   qb="NEW — Vizzina, first-year starter post-Klubnik",
                   roster="41% back · just 11 portal adds — still portal-light by choice"),
        ctx_b=dict(coach="NEW — Lane Kiffin, off Ole Miss's 13-win CFP season",
                   qb="NEW — Sam Leavitt (Arizona State), the spring's biggest QB move",
                   roster="21% back · 44 portal adds — the biggest retool here"),
        keys_a=["Let Allen's defense set the terms — the only unit on this field that never stopped being itself",
                "Give Vizzina his pressure answers BEFORE the snap: quick game and screens, no improvising against Baker",
                "Win explosives — don't trade field goals with LSU's skill talent; the top-5 blue-chip roster has to cash as big plays",
                "Silence the crowd on third down — remove Death Valley's 2.5 and the machine has this at only 6.6"],
        keys_b=["Protect Leavitt — the portal-built OL on a short runway is the bet of the entire season",
                "Tempo early: force Allen's 4-2-5 to line up plain before the disguises load",
                "Let Baker hunt — SP+'s projected No. 2 defense against a first-career-start QB",
                "Finish in the red zone: settling for field goals keeps an unranked underdog alive all night"],
    ),
    dict(
        a="LOU", b="MISS", vs="vs", title="Louisville vs Ole Miss",
        cfbd=("Louisville", "Ole Miss"),
        where="Nashville · Nissan Stadium",
        sub="Sun Sep 6 · 7:30 ET · neutral site · Golding's debut as the head man · Chambliss back after the eligibility win",
        machine="Ole Miss –6.5", market="–7 / –6.5", value="machine = market — no gap",
        wp=("MISS", 65, "LOU", 35),
        decides=[
            "Golding's first game as the head man — can a promoted DC keep a 13-win CFP program's identity after Kiffin took its brain to Baton Rouge?",
            "Chambliss chose Oxford over following Kiffin — the rarest continuity win (50% back); Brohm counters with his third new QB1 in three years",
            "Ranked vs ranked, Sunday night in Nashville: #24 Louisville, #9 Ole Miss — neutral on paper, an Ole Miss crowd in practice",
            "SP+ projects Louisville favored in every game AFTER this one — win here and the huge ACC script is live; Ole Miss defends the CFP label",
        ],
        ctx_a=dict(coach="Brohm, year 4",
                   qb="NEW — Kienholz: third QB1 in three years, least-proven yet",
                   roster="35% back · 33 portal adds — the annual Brohm re-skin"),
        ctx_b=dict(coach="NEW — Pete Golding, promoted; kept the defensive spine",
                   qb="RETURNS — Chambliss, SEC Newcomer of the Year; won his eligibility appeal",
                   roster="50% back · 28 portal adds — the spine stayed"),
        honesty="The market opened −8.5 and walked to −7 — it has come to the machine's −6.5. That's agreement, not edge. And nothing in a preseason prior prices a first-year head coach's clock-and-timeout management on a Sunday neutral floor.",
        keys_a=["Ride the run game — the RB room is the roster's sneaky strength, and every carry keeps Chambliss on the sideline",
                "No coverage busts: top-20 havoc with bottom-40 explosives allowed is the Brohm tradeoff — one bust loses this game",
                "Pressure with the edges vs a rebuilt Ole Miss pass-pro — the one matchup the underdog clearly wins",
                "Keep Kienholz's menu short — Brohm's system has made a top-25 offense of every QB; let it work before asking for heroes"],
        keys_b=["Let Chambliss escape — statistically the nation's best at turning dead plays into first downs",
                "The interior line ends Louisville's run game early — force the least-proven Brohm QB to win it himself",
                "Tempo the Brohm defense into simple, static looks — no disguise time, no gambling looks",
                "Win field position all night — on a neutral floor against a new QB, the long field is a weapon"],
    ),
    dict(
        a="WIS", b="ND", vs="vs", title="Wisconsin vs Notre Dame",
        cfbd=("Wisconsin", "Notre Dame"),
        where="Green Bay · Lambeau Field",
        sub="Sun Sep 6 · 7:30 ET · neutral site · the 'Leave No Doubt' tour opens · Fickell's survival season",
        machine="ND –21", market="–20.5 / –20", value="no gap — watch, don't touch",
        wp=("ND", 87, "WIS", 13),
        decides=[
            "The revenge tour begins: 'Leave No Doubt' was born from the selection-show snub — Freeman rewatches the pain on purpose",
            "ND is the card's continuity outlier — Carr in year two, 51% of production back, just 7 portal adds — in a week full of reboots",
            "Fickell's survival season: a public vote of confidence, the Air Raid detour dead, and a G5 dual-threat QB making the B1G jump as a 20-point dog",
            "No. 4 ND plays for a top-seed résumé; Wisconsin's 3-3-5 — top-25 two straight years with zero offensive help — plays for a moral cover",
        ],
        ctx_a=dict(coach="Fickell, year 4 — survival season; the Air Raid detour is dead",
                   qb="NEW — Colton Joseph (Old Dominion), a real dual threat",
                   roster="31% back · 33 portal adds — retooled around a veteran OL"),
        ctx_b=dict(coach="Freeman — full staff and identity continuity",
                   qb="RETURNS — CJ Carr, year two: the top-10's likeliest QB leap",
                   roster="51% back · just 7 portal adds — the continuity program"),
        honesty="Housekeeping: our ledger's July first-seen here is a known CFBD sides-flip error — the honest movement read is the opener, −16.5 walked to −20.5, four points toward the Irish. Machine −21.1, market −20.5: agreement, and spreads this size sit in the favorite-longshot zone anyway. Watch, don't touch.",
        keys_a=["Shorten the game: long drives, clock runs, zero gifts — fewer possessions is the underdog's only math",
                "Find counters vs the tite front built to erase the run-first pivot — the league's most veteran OL has to earn it",
                "Joseph's legs on third-and-medium — the one chain-mover that travels up from the G5",
                "Force Carr to beat the 3-3-5 from the pocket — this defense is genuinely good enough to keep it inside 20"],
        keys_b=["Prove the post-Love duo/counter identity early — the gap-scheme run game sets up everything else",
                "Carr in rhythm: play-action on schedule, nothing forced — his year-two leap is the top 10's likeliest QB jump",
                "Erase explosives and make Wisconsin drive 12 plays — bend-don't-break with elite tackling wins by attrition",
                "'Leave No Doubt' means no scoreboard mercy — style points are seed points in a week-one résumé game"],
    ),
    dict(
        a="SMU", b="FSU", vs="at", title="SMU at Florida State",
        cfbd=("SMU", "Florida State"),
        where="Tallahassee · Doak Campbell Stadium",
        sub="Mon Sep 7 · 7:30 ET · Labor Day nightcap · ON THE UPSET BOARD — RED",
        machine="FSU –0.5", market="+3 / +3", value="RED: home dog outright",
        wp=("FSU", 52, "SMU", 48),
        decides=[
            "Monday night, alone on the calendar — the whole sport watches the week's last word",
            "No program swung harder in 36 months than FSU (CFP → 2–10 → rebound) — now it hosts SMU's post-CFP expectations and a No. 19 ranking",
            "SMU kept the roster AND Jennings (57% back) but lost BOTH coordinators to troikas; FSU kept Norvell but rents portal QBs a third time",
            "RED ALERT: machine takes the home dog outright — FSU 52% vs market 42%; strip home field and it actually favors SMU by 1.8",
        ],
        ctx_a=dict(coach="Lashlee, year 5 — both coordinators left; co-coordinator troikas",
                   qb="RETURNS — Kevin Jennings; the system's made 3 straight top-25 offenses",
                   roster="57% back · 15 portal adds — kept the roster, lost the callers"),
        ctx_b=dict(coach="Norvell, year 7 — Harris promoted to OC (Malzahn retired)",
                   qb="NEW — veteran portal room again",
                   roster="40% back · 22 portal adds — another portal reload"),
        honesty="Respect the backtest: RED alerts hit 49.7% ATS across 2023–25 — the flag is a research shortlist, not a pick. The entire machine case is the 2.5-point Monday-night home bump — neutralize the Doak and it likes SMU. And FSU's whiplash makes its prior the least trustworthy number on this card.",
        keys_a=["Prove the troika can call it — tempo and spacing from drive one, no committee hesitation on fourth downs",
                "Protect Jennings from FSU's top-10 portal front — line play is the one place SMU is a tier below",
                "Explosives, not field goals: White's 3-3-5 bends on purpose — long drives are the trap, chunk plays are the answer",
                "Win the takeaway ledger — the gambling back seven has to cash on the road, Monday night"],
        keys_b=["Run it with the portal front — make the game physical exactly where the trench classes graded top-10",
                "Quarterback run is the cheat code in Norvell's heavier-hand offense — the extra hat SMU's smaller front must answer",
                "No boom-bust: field position over hero ball — the whiplash program cannot beat itself Monday",
                "Start fast and make the Doak matter — the machine's whole case for FSU is worth 2.5 points of Monday night"],
    ),
]

GAMES = [
    dict(
        a="OU", b="MICH", vs="at", title="Oklahoma at Michigan",
        cfbd=("Oklahoma", "Michigan"),
        where="Ann Arbor · Michigan Stadium",
        sub="Sat Sep 12 · 12:00 ET · rematch of OU's 24–13 win in Norman · Whittingham's first Big House test · the card's biggest machine-market gap",
        machine="Oklahoma –2", market="–5.5 / –5.5", value="3.5 to Michigan — the card's widest gap (11.6 pp of win prob) · lean, not a position",
        wp=("OU", 54, "MICH", 46),
        decides=[
            "The line swung eight points in a week: Michigan opened –1.5, survived Western Michigan 13–12 (three turnovers, 19:52 of possession) and is now +5.5 — the market re-priced a program; the machine moved 4.3",
            "Two rebuilds at opposite speeds: Whittingham's Utah operating system (OC Beck, DC Hill, three Utah starters) is one game old; Venables' defense is in year five and was the SEC's best in 2025",
            "The QB question is the whole show: Underwood's year-two leap (12-of-22 last week) vs Mateer's rebuilt throwing motion (11-of-17, three TDs) — both offenses are built around their QB's legs",
            "Payback with stakes: OU won 24–13 in Norman last September; a Michigan loss at home to open Whittingham's era puts an 8–4 program's floor in play by mid-September",
        ],
        ctx_a=dict(coach="Venables, year 5 — calls the defense himself; OC Arbuckle year two",
                   qb="RETURNS — John Mateer, senior; new throwing motion after the 2025 thumb injury",
                   roster="63% back · 16 portal adds — five OL transfers, WR room rebuilt around Sategna"),
        ctx_b=dict(coach="NEW — Kyle Whittingham (Utah, 177 wins) after Moore's December firing; Beck OC, Hill DC",
                   qb="RETURNS — Bryce Underwood, year two: the No. 1 recruit's Heisman-track season",
                   roster="69% back · 17 portal adds — the Utah pipeline (Daley, Snowden, Lea'ea, Buchanan)"),
        honesty="The market moved seven points on one MAC game; the pre-registered machine moved 4.3 — that gap is the entire 'edge'. It is a bet that 13–12 was noise, made about a first-year head coach and a year-two QB the July prior can't see. Lean Michigan +5.5 as research; the backtest never rewarded us for chasing chaos.",
        keys_a=["Mateer's legs vs Jay Hill's sim pressures — the designed QB run (8 TDs in 2025) is the answer to a blitz-heavy front that punishes hesitation",
                "The five-transfer OL vs Michigan's DL two-deep — 2025's run game ranked 124th in yards per carry; 170 at 4.4 against UTEP proved nothing",
                "Erase the bad-QB day: Underwood went 12-of-22 with a pick — Venables' back seven (Guillory, the Bowens) has to cash on the road at noon",
                "Hidden yards travel: 115 punt-return yards and a defensive score last week — special teams is how a 2-point machine number becomes a cover"],
        keys_b=["Own the ball — 19:52 of possession and three turnovers against a MAC team; Beck's system is built on 30-minute halves and zero gifts",
                "Run Underwood like Dampier: 47 yards on nine carries was the first look — the QB-run leverage is the identity Whittingham imported from Utah",
                "Find receiver No. 2: Buchanan's 126 yards was the whole passing game — Marsh has to be a real target or Venables squeezes one side",
                "Hill's defense allowed 221 yards and 4.2 per pass to WMU — bring that to Mateer's Air Raid without the explosive concessions the pressure invites"],
    ),
    dict(
        a="ASU", b="TAMU", vs="at", title="Arizona State at Texas A&M",
        cfbd=("Arizona State", "Texas A&M"),
        where="College Station · Kyle Field",
        sub="Sat Sep 12 · 12:00 ET · Boley's second start vs an SEC secondary · Elko's portal-built trenches get a tempo test",
        machine="Texas A&M –16.5", market="–14.5 / –14", value="machine 2 past the market — agreement, no play",
        wp=("TAMU", 85, "ASU", 15),
        decides=[
            "Dillingham's post-Leavitt reboot (16% of production back — the least on the card, 24 transfers) meets an 11-win Aggie roster that kept its skill talent and rebuilt both trenches through the portal",
            "Cutter Boley's debut was 21-of-27 for 387 and six touchdowns — against Morgan State; Kyle Field at noon with Elko's disguises is the real audition",
            "A&M's story is its lines: six of the top seven OL and five of seven DL are gone, replaced by transfers with 42 combined SEC starts — a tempo offense is the stress test they'd choose least",
            "Neither rating has a 2026 snap in it: both teams beat FCS opponents the machine doesn't rate, so this number is July's prior plus home field — and the market agrees within two points",
        ],
        ctx_a=dict(coach="Dillingham, year 4 — a full reset after the injury-shredded 2025",
                   qb="NEW — Cutter Boley (Kentucky), won a four-way derby; 387 yards, 6 TDs in the debut",
                   roster="16% back — least on the card · 24 portal adds · 11 of 34 regulars return"),
        ctx_b=dict(coach="Elko, year 3 — two NEW coordinators (Wiggins OC, Hemphill DC)",
                   qb="RETURNS — Marcel Reed: 3,000 pass / 550 rush in 2025, and 12 interceptions",
                   roster="73% back · 19 portal adds — skill talent kept, both trenches rebuilt"),
        honesty="Machine –16.7, market –14.5: two points apart on a 14-point spread is agreement. The 70–7 and 50–0 scores are zero evidence — FCS opponents aren't rated, so neither team's number moved. The scouting risk the prior can't price is Reed's turnover habit (four picks in last year's two losses) against a 3-3-5 that gambles for exactly that.",
        keys_a=["Tempo the transfer defensive line — five new starters up front are the one A&M unit that hasn't played together; 4-of-5 on fourth down says Dillingham will push it",
                "Boley's second start against real disguise: Ricks, Ratcliffe, Brooks and portal corner Gibson rotate late — the six-touchdown debut came against Morgan State",
                "Contain before you gamble: the 3-3-5 is undersized by design, and Reed's designed run in the red zone is exactly what it concedes",
                "Fix special teams (No. 125 last year) — at Kyle Field a +14.5 cover lives or dies in field position"],
        keys_b=["Reed's ball security — 12 picks last year, four in the two losses; a gambling defense wants the hero throw, take the checkdown",
                "Prove the portal OL: 236 rushing yards at 5.0 and 43 minutes of possession last week — run it 45 times again against a light front",
                "Havoc from the new front — Saka (12.5% pressure rate) and Henderson vs a QB making his second start",
                "Finish drives and cut the flags (8 for 75 last week) — style points are the whole game when the spread is 14.5"],
    ),
    dict(
        a="ARIZ", b="BYU", vs="at", title="Arizona at BYU",
        cfbd=("Arizona", "BYU"),
        where="Provo · LaVell Edwards Stadium",
        sub="Sat Sep 12 · 3:30 ET · Big 12 opener · BYU has won three straight in the series (33–27 in Tucson last year) · Fifita's final tour",
        machine="BYU –8.5", market="–7.5 / –7.5", value="machine = market — no gap",
        wp=("BYU", 70, "ARIZ", 30),
        decides=[
            "The Big 12's continuity kings: BYU returns 79% of its production and 177 starts — most in the league — with Bachmeier in year two; Arizona returns the QB (Fifita, 9,183 career yards) and eleven defensive starters",
            "Provo's biggest home game in program memory until Notre Dame arrives: a 12-win team that lost twice, both to Texas Tech, opens the league with the one opponent that 'plays everybody'",
            "The coordinator change is BYU's: Jay Hill took the 3-3-5 to Michigan and Poppinga inherits ten rotation defenders — Fifita is the first quarterback who can make that matter",
            "Week 1 receipts: BYU ran for 308 at 6.7 and forced four turnovers; Arizona put up 520 yards but coughed it up three times — the exact ledger this spread is built on",
        ],
        ctx_a=dict(coach="Brennan, year 3 — DC Danny Gonzales returns eleven 2025 starters",
                   qb="RETURNS — Noah Fifita, year four as the starter: 9,183 yards, 73 TDs",
                   roster="65% back · 22 portal adds — leading rusher and top two receivers gone"),
        ctx_b=dict(coach="Sitake, year 11 — NEW DC Kelly Poppinga (Hill left for Michigan)",
                   qb="RETURNS — Bear Bachmeier, year two: the Big 12's safest QB bet",
                   roster="79% back — most on the card · 9 portal adds · 177 returning starts"),
        honesty="Machine –8.4, market –7.5: agreement. Both ratings are still the July prior — Utah Tech and Northern Arizona aren't rated, so 63–7 and 35–7 moved nothing. BYU has won three straight in the series and the honest lean is that its 79% continuity is the most reliable number on this card; the caveat is a first-time coordinator on the side of the ball that made BYU's last two years.",
        keys_a=["Attack Poppinga's first game plan — hit the corners early with Fifita's quick game before the disguises settle in",
                "Front-six physicality: BYU ran for 308 last week and LJ Martin is a 1,300-yard back — the rebuilt front has to hold the line or the play-action never gets tested",
                "Ball security — three giveaways against Northern Arizona; BYU's defense manufactured four takeaways and a touchdown last week",
                "Play the field-position game Brennan wins — a top-tier secondary, fourth-down aggression, and the hidden yards decide a 7.5-point spread in Provo"],
        keys_b=["Run first, then punish: Bachmeier's QB-run and deep play-action beat single-high all last year — Arizona's secondary is the first one that will make him earn it",
                "Martin and Eka behind four returning linemen — 6.7 a carry last week; this is where the continuity edge shows up on the field",
                "Prove the new receivers: Glasker (65 yards, two scores) and Kasper stepped in for the departed top three — a real secondary is the first real test",
                "Win the hidden margin — 183 return yards and a defensive score last week; against a team that turned it over three times, takeaways are the cover"],
    ),
    dict(
        a="BAMA", b="UK", vs="at", title="Alabama at Kentucky",
        cfbd=("Alabama", "Kentucky"),
        where="Lexington · Kroger Field",
        sub="Sat Sep 12 · 3:30 ET · SEC opener · Keelon Russell's first road start · Will Stein's first SEC game · Kentucky hasn't beaten Alabama since 1997",
        machine="Alabama –13", market="–10.5 / –10.5", value="2.7 to Alabama — quibble, not a play",
        wp=("BAMA", 79, "UK", 21),
        decides=[
            "DeBoer's referendum year opens on the road with a redshirt-freshman quarterback: Russell went 18-of-30 for 256 with zero touchdowns in the opener — the offense scored five rushing TDs instead",
            "Will Stein's Kentucky is the anti-Stoops: motion, pace, a Notre Dame transfer QB (Minchey: 301 yards, four TDs in the debut) behind six transfer linemen averaging 6-5, 323",
            "Continuity is the card's lowest on both sides: Alabama returns 26% of its offensive production, Kentucky 19% — 31 transfers in Lexington, the most of anyone we cover this week",
            "The market's early landmine: the deep dive called Kentucky Week 2 one of three early traps — Alabama lost its opener a year ago and DeBoer has lost as many games in two years as Saban did in five",
        ],
        ctx_a=dict(coach="DeBoer, year 3 — the referendum season; Wommack year 3 on defense",
                   qb="NEW — Keelon Russell, RS freshman, the No. 2 recruit in the 2025 class",
                   roster="26% back · 17 portal adds — six of the top seven OL gone, QB gone"),
        ctx_b=dict(coach="NEW — Will Stein (Oregon OC) after the Stoops era ended at 5–7",
                   qb="NEW — Kenny Minchey (Notre Dame): accurate, mobile, one start of proof",
                   roster="19% back · 31 portal adds — most on the card; six transfer OL, ten defensive starters back"),
        honesty="Machine –13.2, market –10.5: 2.7 to Alabama sits right at the noise line, and it comes with the two hedges a prior can't price — a teenager's first road start and a year-one head coach whose rating has zero 2026 snaps in it (Youngstown State isn't rated). Treat it as a quibble; the real information arrives at 3:30.",
        keys_a=["Russell's first road start — zero passing touchdowns against ECU; DeBoer's rhythm game needs him to attack the intermediate middle, not just survive",
                "Run it 49 times again: 227 yards and five rushing scores last week — the rebuilt OL vs Kentucky's returning front is where an SEC road game is decided",
                "Wommack's secondary (Brown, Lee, Sabb) vs the receiver room the deep dive called a void — make Minchey hold the ball",
                "Special teams: 107th last year and projected 109th — a 10.5-point spread at Kroger dies in hidden yards"],
        keys_b=["The mauling line: six transfers, 49 FBS starts, three all-conference — vs an Alabama interior that lost four of its top five tackles; Baxter and Patterson downhill",
                "Minchey's profile: four touchdowns, no picks, 11.1 a throw — keep it clean against the best secondary in America and the spread is in play all afternoon",
                "The defense is the strength — ten of nineteen starters back plus Castell; make Russell win from the pocket on third-and-long",
                "Clean up the two Week 1 leaks: 3-of-8 on third down and six penalties for 70 — those are the stats that lose to Alabama"],
    ),
    dict(
        a="OSU", b="TEX", vs="at", title="Ohio State at Texas",
        cfbd=("Ohio State", "Texas"),
        where="Austin · DKR–Texas Memorial Stadium",
        sub="Sat Sep 12 · 7:30 ET · No. 1 at No. 4 · the 2025 opener rematch (OSU 14–7) · Arch's last tour vs Sayin-to-Smith",
        machine="Texas –3.5", market="–1.5 / –2", value="machine 2 points past the market — mostly bookkeeping, see honesty box",
        wp=("TEX", 60, "OSU", 40),
        decides=[
            "The rematch of the year: Ohio State won last year's opener 14–7 in Columbus and the 2024 CFP semifinal — Texas gets it at home, at night, with Arch Manning in what is almost certainly his last season",
            "Two title-or-bust rosters and one coordinator gamble each: Arthur Smith installing an NFL run game around Sayin–Smith, Will Muschamp replacing the coordinator whose defense outranked Sark's offense two years running",
            "Continuity edge is Texas: 72% of its offensive production back plus the sport's most talked-about portal class (Coleman, Smothers, Biles); Ohio State returns 68% on offense but only two of nine defensive starters",
            "Week 1 said nothing and everything: 56–3 and 59–7 — Sayin 21-of-25, Arch 4 touchdowns — but Texas allowed 349 yards to Texas State and Ohio State took nine flags",
        ],
        ctx_a=dict(coach="Day, year 8 — NEW OC Arthur Smith (ex-Falcons HC); Patricia year two on defense",
                   qb="RETURNS — Julian Sayin, year two: No. 1 in success rate as a freshman",
                   roster="68% of offensive production back · 17 portal adds — but 2 of 9 defensive starters return"),
        ctx_b=dict(coach="Sarkisian, year 6 — NEW DC Will Muschamp (the league's riskiest coordinator swap)",
                   qb="RETURNS — Arch Manning, year two as the starter; final season, Heisman favorite",
                   roster="72% back · 22 portal adds — the headline portal class (Coleman, Smothers, Biles, Siani)"),
        honesty="The machine says Texas by 3.7; the market says 1.5; ESPN's own live FPI says 0.7. Three points of our number are bookkeeping — the ±28 margin cap turned 56–3 into an 'underperformance' and docked Ohio State 4.1 rating points for winning by 53. Strip the artifact and this is a pick'em plus home field, which is exactly what everyone else says. No position.",
        keys_a=["Make Arthur Smith's run game real — 237 yards at 6.8 a carry last week; if wide zone travels, Sayin plays on schedule instead of in a phone booth",
                "Sayin-to-Smith vs the back end Kwiatkowski built and Muschamp inherited: McDonald, Littleton and portal corner Mascoe held this offense to 14 last year",
                "Prove the eight-transfer defense — Russaw, Smith, Moore, Little — against the deepest skill corps in the sport; two of nine starters back is the season's real question",
                "Urgency: last year's slow-tempo offense died in the two games that mattered — play with pace, and cut the nine penalties from Week 1"],
        keys_b=["Arch on the move: designed movement is Sark's 2026 wrinkle and accuracy on the run is Arch's last flaw — Patricia's disguises will test exactly that",
                "Protect the interior — the 2025 OL regression was the whole story of a preseason No. 1 that missed the CFP; Ohio State's transfer front arrives Saturday",
                "Explosives over efficiency: Coleman, Wingo, Smothers (4.4 yards after contact) vs a rally-tackle defense that squeezes chunk plays — win the big-play count",
                "Muschamp's first real test: 349 yards allowed to Texas State is a flag; Simmons off the edge and Biles inside have to make Sayin uncomfortable early"],
    ),
]

# ---- Week 1 receipts (recap slide): frozen Ep2 predictions vs finals vs the
# last pre-kick ledger pull (Fri Sep 4 5 PM ET; Mon Sep 7 9:25 AM ET for
# SMU–FSU). Finals are read from the CFBD games cache; a game not yet
# played renders as a pending row and grades itself after the next refresh.
# Lines are home-perspective spreads (negative = home favored).
RECAP_ROWS = [
    # a, b, title, (away, home), our call, our line, closing line
    ("BAY", "AUB", "Baylor vs Auburn", ("Baylor", "Auburn"), "Auburn 33–27", -5.5, -7.5),
    ("CLEM", "LSU", "Clemson at LSU", ("Clemson", "LSU"), "LSU 30–21", -9.0, -10.0),
    ("LOU", "MISS", "Louisville vs Ole Miss", ("Louisville", "Ole Miss"), "Ole Miss 31–25", -6.5, -6.5),
    ("WIS", "ND", "Wisconsin vs Notre Dame", ("Wisconsin", "Notre Dame"), "ND 34–13", -21.0, -20.5),
    ("SMU", "FSU", "SMU at Florida State", ("SMU", "Florida State"), "FSU 27–26", -0.5, 2.5),
]
WEEK0_MISS = (70.0, 70.0)  # machine, market — carried forward for the running total


def _finals():
    """(away, home) -> (away_pts, home_pts) from the CFBD 2026 games cache."""
    import json
    p = os.path.join(HERE, "fpi-decomposition", "data",
                     "games_seasonType-regular_year-2026.json")
    out = {}
    if os.path.exists(p):
        for g in json.load(open(p, encoding="utf-8")):
            if g.get("homePoints") is not None and g.get("awayPoints") is not None:
                out[(g["awayTeam"], g["homeTeam"])] = (g["awayPoints"], g["homePoints"])
    return out


def _line_txt(a, b, sp):
    """home-perspective spread -> 'Fav –x' with the short team name."""
    if sp < 0:
        return f"{CODE2NAME[b]} –{-sp:g}"
    if sp > 0:
        return f"{CODE2NAME[a]} –{sp:g}"
    return "PK"


def build_recap():
    finals = _finals()
    rows, tot_m, tot_k, n_m, n_k, n_t = [], 0.0, 0.0, 0, 0, 0
    for a, b, title, key, call, ours, close in RECAP_ROWS:
        lines_ = f"our line {_line_txt(a, b, ours)} · closing {_line_txt(a, b, close)}"
        fin = finals.get(key)
        if fin is None:
            rows.append((a, b, title, f"we called {call} · FINAL pending",
                         lines_, "graded before air — see the notes", "P"))
            continue
        ap_, hp_ = fin
        win, lose = (CODE2NAME[b], CODE2NAME[a]) if hp_ >= ap_ else (CODE2NAME[a], CODE2NAME[b])
        callfin = f"we called {call} · FINAL {win} {max(ap_, hp_)}–{min(ap_, hp_)}"
        margin = hp_ - ap_                       # actual home margin
        off_m, off_k = abs(margin + ours), abs(margin + close)
        tot_m, tot_k = tot_m + off_m, tot_k + off_k
        if off_m < off_k:
            verdict, mark = "machine closer", "M"
            n_m += 1
        elif off_k < off_m:
            verdict, mark = "market closer", "K"
            n_k += 1
        else:
            verdict, mark = "dead tie", "T"
            n_t += 1
        rows.append((a, b, title, callfin, lines_,
                     f"machine off by {off_m:g} · market off by {off_k:g} — {verdict}", mark))
    graded = n_m + n_k + n_t
    return rows, dict(m=tot_m, k=tot_k, n=graded, nm=n_m, nk=n_k, nt=n_t)


RECAP, RECAP_SUM = build_recap()

# ---- Superdog boards (segment: pick a dog to win outright; points = the
# spread). Computed live from card_data so a fresh pull refreshes them.
# AP Top 25 comes from the CFBD /rankings cache via inseason_ratings (the
# Tuesday refresh and every edge_report --publish keep it current); the hand
# dict below is only a fallback if the cache is missing (last synced: week 2).
_AP_FALLBACK = {"Ohio State": 1, "Georgia": 2, "Notre Dame": 3, "Texas": 4,
            "Indiana": 5, "Oregon": 6, "Miami": 7, "LSU": 8, "Ole Miss": 9,
            "Texas A&M": 10, "Oklahoma": 11, "Alabama": 12, "Texas Tech": 13,
            "USC": 14, "BYU": 15, "Penn State": 16, "SMU": 17, "Tennessee": 18,
            "Washington": 19, "Utah": 20, "Iowa": 21, "Houston": 22,
            "Missouri": 23, "Louisville": 24, "Virginia": 25}  # AP week 2


def _load_ap():
    try:
        from inseason_ratings import latest_rankings
        r = latest_rankings(refresh=False)
        if r.get("ap"):
            return dict(r["ap"]), r.get("week")
    except Exception as e:  # cache missing / import problem -> fallback
        print("AP poll: cache unavailable,", e)
    return {normalize_name(k): v for k, v in _AP_FALLBACK.items()}, None


AP_TOP25, AP_WEEK = _load_ap()


def ap_rank(team):
    return AP_TOP25.get(normalize_name(team))



_MONTHS = dict(Jan=1, Feb=2, Mar=3, Apr=4, May=5, Jun=6, Jul=7, Aug=8,
               Sep=9, Oct=10, Nov=11, Dec=12)


def superdog_boards():
    """(any-game rows, vs-top-25 rows), each sorted by EV; played games
    (before the lines_as_of date) are excluded."""
    import datetime as dt
    if not CARD:
        return [], []
    asof = dt.datetime.fromisoformat(LINES_TS.replace("Z", "+00:00")).date()
    rows = []
    for g in CARD.values():
        try:
            _, mon, day = g["date"].split(",")[0].split()
            gdate = dt.date(2026, _MONTHS[mon], int(day))
        except (KeyError, ValueError):
            continue
        if gdate < asof:
            continue
        b = g["books"].get("DraftKings") or g["books"].get("Bovada") or {}
        sp = b.get("spread")
        if sp is None or abs(sp) < 0.5:
            continue
        ph = g["model_p_home"]
        if sp < 0:
            dog, fav, p = g["away"], g["home"], 1 - ph
        else:
            dog, fav, p = g["home"], g["away"], ph
        at = "at" if dog == g["away"] else "vs"
        mkt_ph = g.get("mkt_p_home")
        mkt = (1 - mkt_ph if sp < 0 else mkt_ph) if mkt_ph is not None else None
        ml = b.get("away_ml") if dog == g["away"] else b.get("home_ml")
        rows.append(dict(dog=dog, fav=fav, at=at, pts=abs(sp), p=p, mkt=mkt,
                         ml=ml, ev=p * abs(sp), rank=ap_rank(fav)))
    rows.sort(key=lambda r: -r["ev"])
    return rows, [r for r in rows if r["rank"]]


SUPERDOG_ANY, SUPERDOG_T25 = superdog_boards()

# overlay pipeline numbers (card_data) before any slide is built
LEDGER = {g["title"]: apply_card(g) for g in GAMES}
print("card_data:", "loaded, lines as of " + LINES_AS_OF if CARD else
      "NOT FOUND — using hand-typed numbers")
print(f"AP poll: week {AP_WEEK} ({len(AP_TOP25)} ranked) · receipts graded "
      f"{RECAP_SUM['n']}/{len(RECAP_ROWS)}")

# ---------------- slide 1: the machine's top 25 ----------------
# Data: ratings_current_2026.json (our in-season rating, sorted) joined to
# rosters/data/teams_fbs_2026.json for display names + ESPN logo URLs (logos
# are fetched into decks/logos on first use). AP column = the cached poll.
import json as _json
import re as _re
import urllib.request as _urlreq

_TEAMS_FBS = {}
try:
    for _t in _json.load(open(os.path.join(HERE, "rosters", "data",
                                           "teams_fbs_2026.json"),
                              encoding="utf-8")):
        _TEAMS_FBS[normalize_name(_t["school"])] = _t
except FileNotFoundError:
    pass


def logo_for(norm):
    """decks/logos/<slug>.png for a normalized team name; fetched from the
    cached ESPN URL on first use. None if unavailable."""
    t = _TEAMS_FBS.get(norm)
    if not t or not t.get("logos"):
        return None
    path = os.path.join(LOGO_DIR, _re.sub(r"[^a-z0-9]", "", norm) + ".png")
    if not os.path.exists(path):
        url = t["logos"][0].replace("http://", "https://")
        try:
            req = _urlreq.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with open(path, "wb") as f:
                f.write(_urlreq.urlopen(req, timeout=20).read())
        except Exception as e:  # keep building; the row just has no logo
            print("logo fetch failed:", norm, e)
            return None
    return path


def school(norm):
    return _TEAMS_FBS.get(norm, {}).get("school", norm.title())


_r = _json.load(open(os.path.join(HERE, "ratings_current_2026.json"),
                     encoding="utf-8"))
_top = _r["teams"][:25]
_top_set = {t["team"] for t in _top}

s = blank(NAVY)
PALE = RGBColor(0xCA, 0xDC, 0xFC)
UP, DOWN = RGBColor(0x5C, 0xD6, 0x8A), RGBColor(0xFF, 0x7A, 0x7A)
txt(s, 0.9, 0.42, 11.5, 0.4,
    f"EPISODE {EPISODE} · WEEK {WEEK} · THE MACHINE'S TOP 25", 14, ORANGE,
    bold=True)
txt(s, 0.9, 0.76, 11.5, 0.8, "Our Top 25", 40, WHITE, bold=True)
txt(s, 0.9, 1.5, 11.5, 0.3,
    f"our in-season rating after {_r.get('games_used')} rated games · "
    "Δ = move vs ESPN's preseason FPI (0.0 = no rated game yet) · "
    f"AP = week {AP_WEEK} poll · NR = not ranked", 11, PALE, italic=True)
TOP, RH, CW = 1.98, 0.36, 5.5
for x0 in (0.9, 6.95):
    txt(s, x0 + 3.3, TOP - 0.24, 0.75, 0.22, "RATING", 8, PALE,
        bold=True, align=PP_ALIGN.RIGHT)
    txt(s, x0 + 4.05, TOP - 0.24, 0.75, 0.22, "Δ PRE", 8, PALE,
        bold=True, align=PP_ALIGN.RIGHT)
    txt(s, x0 + 4.8, TOP - 0.24, 0.65, 0.22, "VOTERS", 8, PALE,
        bold=True, align=PP_ALIGN.RIGHT)
for col, (x0, rows) in enumerate(((0.9, _top[:13]), (6.95, _top[13:]))):
    for i, t in enumerate(rows):
        rank, y = i + 1 + col * 13, TOP + i * RH
        if i % 2 == 0:
            shape(s, MSO_SHAPE.RECTANGLE, x0, y, CW, RH, NAVY2)
        txt(s, x0 + 0.02, y + 0.035, 0.45, 0.3, str(rank), 13, ORANGE,
            bold=True, align=PP_ALIGN.RIGHT)
        lp = logo_for(t["team"])
        if lp:
            shape(s, MSO_SHAPE.OVAL, x0 + 0.6, y + 0.04, 0.28, 0.28, WHITE)
            s.shapes.add_picture(lp, Inches(x0 + 0.63), Inches(y + 0.07),
                                 Inches(0.22), Inches(0.22))
        txt(s, x0 + 1.0, y + 0.035, 2.3, 0.3, school(t["team"]), 12.5, WHITE,
            bold=True)
        txt(s, x0 + 3.3, y + 0.035, 0.75, 0.3, f"{t['cur']:.1f}", 12.5,
            WHITE, align=PP_ALIGN.RIGHT)
        d = t["delta"]
        txt(s, x0 + 4.05, y + 0.05, 0.75, 0.3, f"{d:+.1f}" if d else "0.0",
            11, UP if d > 0 else (DOWN if d < 0 else PALE), bold=bool(d),
            align=PP_ALIGN.RIGHT)
        ap = AP_TOP25.get(t["team"])
        txt(s, x0 + 4.8, y + 0.05, 0.65, 0.3, f"AP {ap}" if ap else "NR", 10,
            PALE, align=PP_ALIGN.RIGHT)
# man-vs-machine footer: biggest rank disagreements, computed from the data
_gaps = sorted(((abs(AP_TOP25[t["team"]] - i), -i, i, AP_TOP25[t["team"]],
                 school(t["team"])) for i, t in enumerate(_top, 1)
                if t["team"] in AP_TOP25), reverse=True)  # ties -> higher-ranked team first
_ours_only = [school(t["team"]) for t in _top if t["team"] not in AP_TOP25]
_theirs_only = sorted(((v, school(k)) for k, v in AP_TOP25.items()
                       if k not in _top_set))
_line1 = "Biggest splits with the voters: " + " · ".join(
    f"{n} (machine #{i}, AP #{a})" for _, _, i, a, n in _gaps[:4])
_line2 = ("In our 25, not theirs: " + ", ".join(_ours_only[:4]) +
          "   |   In theirs, not ours: " +
          ", ".join(f"{n} (AP {v})" for v, n in _theirs_only[:4]))
_fy = TOP + 13 * RH + 0.08
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, _fy, 11.55, 0.62, NAVY2)
txt(s, 1.1, _fy + 0.06, 11.2, 0.28, _line1, 9.5, WHITE, bold=True)
txt(s, 1.1, _fy + 0.32, 11.2, 0.28, _line2, 9.5, PALE)

# ---------------- slides 2-3: hot seat + Heisman boards ----------------
# Data: boards_week{N}.json from hot_seat_heisman.py (CBS rating x season-sim
# odds of hitting the job-saving win total; QB PPA blend x team P(10+)).
_BP = os.path.join(HERE, f"boards_week{WEEK}.json")
BOARDS = _json.load(open(_BP, encoding="utf-8")) if os.path.exists(_BP) else None
if BOARDS:
    PALE = RGBColor(0xCA, 0xDC, 0xFC)
    UP, DOWN = RGBColor(0x5C, 0xD6, 0x8A), RGBColor(0xFF, 0x7A, 0x7A)

    def _row_logo(s, x, y, team):
        lp = logo_for(normalize_name(team))
        if lp:
            shape(s, MSO_SHAPE.OVAL, x, y + 0.05, 0.3, 0.3, WHITE)
            s.shapes.add_picture(lp, Inches(x + 0.035), Inches(y + 0.085),
                                 Inches(0.23), Inches(0.23))

    def _hdr(s, x, w, y, label, align=PP_ALIGN.LEFT):
        txt(s, x, y, w, 0.22, label, 8, PALE, bold=True, align=align)

    # -- hot seat --
    s = blank(NAVY)
    txt(s, 0.9, 0.42, 11.5, 0.4,
        f"EPISODE {EPISODE} · WEEK {WEEK} · THE SEAT BOARD", 14, ORANGE, bold=True)
    txt(s, 0.9, 0.76, 11.5, 0.8, "Hot Seat Top 10", 40, WHITE, bold=True)
    txt(s, 0.9, 1.5, 11.5, 0.3,
        "seat score = 60% the man (CBS hot-seat rating 0–5, Aug 29) + 40% the machine "
        "(odds of missing the job-saving win total, from our season sim) · * = estimated",
        10.5, PALE, italic=True)
    TOP, RH = 2.08, 0.4
    R = PP_ALIGN.RIGHT
    _hdr(s, 1.75, 2.8, TOP - 0.25, "COACH · SCHOOL")
    _hdr(s, 4.6, 1.5, TOP - 0.25, "TENURE")
    _hdr(s, 6.15, 0.55, TOP - 0.25, "CBS", R)
    _hdr(s, 6.75, 0.55, TOP - 0.25, "NEEDS", R)
    _hdr(s, 7.35, 0.7, TOP - 0.25, "P(GETS IT)", R)
    _hdr(s, 8.1, 0.95, TOP - 0.25, "MACHINE WINS", R)
    _hdr(s, 9.1, 0.5, TOP - 0.25, "Δ", R)
    _hdr(s, 9.65, 0.55, TOP - 0.25, "SCORE", R)
    _hdr(s, 10.3, 2.1, TOP - 0.25, "LAST RESULT")
    for i, r in enumerate(BOARDS["hot_seat"][:10]):
        y = TOP + i * RH
        if i % 2 == 0:
            shape(s, MSO_SHAPE.RECTANGLE, 0.9, y, 11.5, RH, NAVY2)
        txt(s, 0.9, y + 0.06, 0.4, 0.3, str(i + 1), 13, ORANGE, bold=True, align=R)
        _row_logo(s, 1.35, y, r["team"])
        txt(s, 1.75, y + 0.06, 2.8, 0.3, f"{r['coach']} · {r['team']}", 12, WHITE, bold=True)
        txt(s, 4.6, y + 0.09, 1.5, 0.3, r["tenure"], 8.5, PALE)
        txt(s, 6.15, y + 0.07, 0.55, 0.3, f"{r['cbs']:.1f}{'*' if r['cbs_est'] else ''}",
            11, WHITE, bold=True, align=R)
        txt(s, 6.75, y + 0.07, 0.55, 0.3, f"{r['bar']} W", 11, WHITE, align=R)
        txt(s, 7.35, y + 0.07, 0.7, 0.3, f"{round(100 * r['p_bar'])}%", 11,
            DOWN if r["p_bar"] < 0.4 else (UP if r["p_bar"] > 0.6 else WHITE),
            bold=True, align=R)
        txt(s, 8.1, y + 0.07, 0.95, 0.3, f"{r['proj']:.1f} ({r['p10']:g}–{r['p90']:g})",
            10.5, WHITE, align=R)
        d = r["delta"] or 0.0
        txt(s, 9.1, y + 0.09, 0.5, 0.3, f"{d:+.1f}" if d else "0.0", 10,
            UP if d > 0 else (DOWN if d < 0 else PALE), bold=bool(d), align=R)
        txt(s, 9.65, y + 0.06, 0.55, 0.3, f"{r['score']:.0f}", 12.5, ORANGE, bold=True, align=R)
        last = (r["results"] or ["—"])[-1].replace("vs ", "vs ").replace("at ", "at ")
        txt(s, 10.3, y + 0.09, 2.1, 0.3, last, 8.5, PALE)
    _fy = TOP + 10 * RH + 0.12
    _nxt = BOARDS["hot_seat"][10:13]
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, _fy, 11.5, 0.62, NAVY2)
    txt(s, 1.1, _fy + 0.06, 11.2, 0.28,
        "Next three: " + " · ".join(f"{x['coach']} ({x['team']}, {x['score']:.0f})" for x in _nxt),
        9.5, WHITE, bold=True)
    txt(s, 1.1, _fy + 0.32, 11.2, 0.28,
        "NEEDS = the win total that keeps the job (from the deep-dive write-ups — a "
        "judgment call) · P(GETS IT) = the machine's odds of reaching it · MACHINE WINS = "
        f"projected wins (10th–90th pct), {BOARDS['games_used']} rated games in",
        8.5, PALE)

    # -- Heisman --
    s = blank(NAVY)
    txt(s, 0.9, 0.42, 11.5, 0.4,
        f"EPISODE {EPISODE} · WEEK {WEEK} · OUR HEISMAN BOARD", 14, ORANGE, bold=True)
    txt(s, 0.9, 0.76, 11.5, 0.8, "Our Heisman Favorite", 40, WHITE, bold=True)
    txt(s, 0.9, 1.5, 11.5, 0.3,
        "index = team factor (0.5 + half the odds of 10+ wins) × blended PPA per play "
        "(2026 + 150 plays of the 2025 line as prior) · market = DraftKings, Sep 8",
        10.5, PALE, italic=True)
    HEISMAN_WHY = {
        "Julian Sayin": "Best returning efficiency in the sport (0.545 in 2025, No. 1 in success rate) on a title favorite — the market has him 8th at +1400",
        "Darian Mensah": "401 yards, 5 TD, 90% at Stanford — but the prior is a Duke season (0.371); Miami's 74% P(10+) is the best team factor on the board",
        "C.J. Carr": "Carried by the team: Notre Dame's 91% P(10+) is the board's highest; the efficiency line is average so far (0.398 on 31 plays, 0.433 prior)",
        "Josh Hoover": "1.639 per play on 15 plays — a tiny sample — plus Indiana's 73% P(10+) and the offense that made a Heisman winner of a transfer last year",
        "Will Hammond": "Situation, not tape: Texas Tech's 80% P(10+) is 2nd on the board while his efficiency is 8th of 9 (0.384) — Houston in Lubbock is the first real test",
        "Arch Manning": "The market's No. 2 at +950, our 8th: a mediocre 2025 prior (0.338) and the same 47% team factor as Ohio State — Saturday is the referendum",
    }
    _mkt = {x["name"]: x["market"] for x in BOARDS["heisman"] + BOARDS["heisman_non_qb"]
            if x.get("market")}
    _order = sorted(_mkt, key=lambda n: _mkt[n])
    _mrank = {n: i + 1 for i, n in enumerate(_order)}
    TOP, RH = 2.08, 0.62
    _hdr(s, 1.75, 2.7, TOP - 0.25, "QUARTERBACK · TEAM")
    _hdr(s, 4.5, 1.2, TOP - 0.25, "2026 PPA (PLAYS)", R)
    _hdr(s, 5.75, 0.8, TOP - 0.25, "2025 PRIOR", R)
    _hdr(s, 6.6, 0.7, TOP - 0.25, "BLEND", R)
    _hdr(s, 7.35, 0.9, TOP - 0.25, "TEAM P(10+)", R)
    _hdr(s, 8.3, 0.7, TOP - 0.25, "INDEX", R)
    _hdr(s, 9.05, 0.9, TOP - 0.25, "MARKET", R)
    _hdr(s, 10.0, 0.9, TOP - 0.25, "MKT RANK", R)
    _hdr(s, 10.95, 1.45, TOP - 0.25, "MAN VS MACHINE", R)
    for i, r in enumerate(BOARDS["heisman"][:5]):
        y = TOP + i * RH
        if i % 2 == 0:
            shape(s, MSO_SHAPE.RECTANGLE, 0.9, y, 11.5, RH, NAVY2)
        txt(s, 0.9, y + 0.04, 0.4, 0.3, str(i + 1), 13, ORANGE, bold=True, align=R)
        _row_logo(s, 1.35, y - 0.02, r["team"])
        why = HEISMAN_WHY.get(r["name"]) or (
            f"team factor {r['team_factor']:.2f} × blended efficiency {r['blend']:.3f} "
            f"(2026 {r['ppa26']:.3f} on {r['plays26']} plays, prior {r['ppa25']})")
        txt(s, 1.75, y + 0.33, 10.6, 0.28, why, 9.5, PALE)
        txt(s, 1.75, y + 0.04, 2.7, 0.3, f"{r['name']} · {r['team']}", 12, WHITE, bold=True)
        txt(s, 4.5, y + 0.05, 1.2, 0.3, f"{r['ppa26']:.3f} ({r['plays26']})", 10.5, WHITE, align=R)
        txt(s, 5.75, y + 0.05, 0.8, 0.3, f"{r['ppa25']:.3f}" if r["ppa25"] is not None else "new", 10.5, PALE, align=R)
        txt(s, 6.6, y + 0.05, 0.7, 0.3, f"{r['blend']:.3f}", 10.5, WHITE, align=R)
        txt(s, 7.35, y + 0.05, 0.9, 0.3, f"{round(100 * r['p10w'])}%", 10.5, WHITE, align=R)
        txt(s, 8.3, y + 0.04, 0.7, 0.3, f"{r['index']:.1f}", 12.5, ORANGE, bold=True, align=R)
        txt(s, 9.05, y + 0.05, 0.9, 0.3, f"+{r['market']}" if r["market"] else "off board",
            10.5, WHITE if r["market"] else PALE, align=R)
        mr = _mrank.get(r["name"])
        txt(s, 10.0, y + 0.05, 0.9, 0.3, f"#{mr}" if mr else "—", 10.5, PALE, align=R)
        gap = (mr - (i + 1)) if mr else None
        lab = ("market too low" if gap and gap >= 3 else "market too high" if gap is not None and gap <= -3
               else "agree" if gap is not None else "unpriced")
        txt(s, 10.95, y + 0.05, 1.45, 0.3, lab, 9.5,
            UP if lab == "market too low" else (DOWN if lab == "market too high" else PALE),
            bold=lab != "agree", align=R)
    _nx = BOARDS["heisman"][5:9]
    txt(s, 0.9, TOP + 5 * RH + 0.04, 11.5, 0.28,
        "Next up: " + " · ".join(f"{x['name']} {x['index']:.1f}" +
                                (f" (market #{_mrank[x['name']]})" if x['name'] in _mrank else "")
                                for x in _nx), 9.5, PALE, italic=True)
    fav = BOARDS["heisman"][0]
    _fy = TOP + 5 * RH + 0.4
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, _fy, 11.5, 0.72, ORANGE)
    txt(s, 1.2, _fy + 0.1, 3.0, 0.5, "★ OUR FAVORITE", 15, NAVY, bold=True)
    txt(s, 4.0, _fy + 0.08, 8.2, 0.55,
        f"{fav['name']}, {fav['team']} — index {fav['index']:.1f} · market "
        f"+{fav['market']} (#{_mrank.get(fav['name'], '—')} on the board)", 17, WHITE, bold=True)
    _non = BOARDS["heisman_non_qb"]
    txt(s, 0.9, _fy + 0.85, 11.5, 0.3,
        "Non-QB watch (own scale — PPA per target, not comparable to the QB column): " +
        " · ".join(f"{x['name']} {x['ppa26']:.2f}" + (f" (+{x['market']})" if x.get("market") else "")
                   for x in _non[:4]), 9.5, PALE)
    txt(s, 0.9, 7.13, 11.5, 0.3,
        "PPA = CFBD predicted points added per play · a great QB on a 9-win team stays "
        "alive (team factor floor 0.5) · the board re-computes every rebuild", 8.5, PALE,
        italic=True)

# ---------------- title slide ----------------
s = blank(NAVY)
txt(s, 0.9, 0.85, 11.5, 0.45, f"EPISODE {EPISODE} · WEEK {WEEK} · {EP_DATE}", 14, ORANGE,
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
    txt(s, 8.4, y + 0.1, 3.8, 0.4, g["machine"] + "   ·   " + g["market"],
        13.5, ORANGE, bold=True, align=PP_ALIGN.RIGHT)
    txt(s, 8.4, y + 0.47, 3.8, 0.3, "machine · market", 9.5,
        RGBColor(0xCA, 0xDC, 0xFC), align=PP_ALIGN.RIGHT)
    y += 0.88
txt(s, 0.9, 6.85, 11.5, 0.5,
    "Machine = our in-season rating (ESPN preseason FPI prior + 2026 results, "
    f"λ 3, cap ±28) + 2.5 HFA · empirical margin curve (σ 15.9) · lines as of "
    f"{LINES_AS_OF} · model plays graded vs first-seen lines", 10.5,
    RGBColor(0x8F, 0xA5, 0xC4))

# ---- slide text: the headline only (Lucas 9/11). Keyed by game title. ----
SHORT = {
    "Ohio State at Texas": dict(
        ctx_a=dict(coach="Day, year 8 · new OC Arthur Smith", qb="Sayin returns, year two", roster="68% back · 2 of 9 D starters"),
        ctx_b=dict(coach="Sarkisian, year 6 · new DC Muschamp", qb="Arch returns, final season", roster="72% back · 22 portal adds"),
        decides=["The rematch", "One coordinator gamble each",
                 "Texas has the continuity edge", "Week 1 proved nothing yet"],
        honesty="Machine 3.7, market 1.5, ESPN 0.7 — three points of ours is the cap artifact. No position.",
        keys_a=["Make the run game real", "Sayin-to-Smith vs the back end",
                "Prove the eight-transfer defense", "Play with pace, cut the flags"],
        keys_b=["Arch on the move", "Protect the interior",
                "Explosives over efficiency", "Muschamp's first real test"]),
    "Oklahoma at Michigan": dict(
        ctx_a=dict(coach="Venables, year 5", qb="Mateer returns, senior", roster="63% back · 16 portal adds"),
        ctx_b=dict(coach="NEW — Whittingham (Utah)", qb="Underwood, year two", roster="69% back · the Utah pipeline"),
        decides=["An eight-point line swing", "Whittingham's first Big House test",
                 "Underwood vs Mateer", "Payback for 24–13"],
        honesty="The market moved 7, the machine moved 4.3 — lean Michigan +5.5 as research, not a position.",
        keys_a=["Mateer's legs vs Hill's pressure", "The portal line has to prove it",
                "Erase Underwood's bad day", "Win the hidden yards"],
        keys_b=["Own the ball", "Run Underwood like Dampier",
                "Find receiver No. 2", "Pressure without the busts"]),
    "Arizona State at Texas A&M": dict(
        ctx_a=dict(coach="Dillingham, year 4", qb="NEW — Cutter Boley", roster="16% back · 24 portal adds"),
        ctx_b=dict(coach="Elko, year 3 · two new coordinators", qb="Reed returns", roster="73% back · both lines rebuilt"),
        decides=["Dillingham's reboot vs an 11-win roster", "Boley's second start",
                 "A&M's portal-built lines", "No 2026 snaps in the number"],
        honesty="Two points apart on a 14-point spread is agreement — no play.",
        keys_a=["Tempo the transfer front", "Boley vs real disguise",
                "Contain before you gamble", "Fix special teams"],
        keys_b=["Reed's ball security", "Prove the portal line",
                "Havoc from the new front", "Finish drives, cut the flags"]),
    "Arizona at BYU": dict(
        ctx_a=dict(coach="Brennan, year 3", qb="Fifita returns, year four", roster="65% back · 22 portal adds"),
        ctx_b=dict(coach="Sitake, year 11 · new DC Poppinga", qb="Bachmeier, year two", roster="79% back · most on the card"),
        decides=["The Big 12's continuity kings", "Provo's biggest game until Notre Dame",
                 "Poppinga replaces Hill", "BYU took four, Arizona gave three"],
        honesty="Machine 8.4, market 7.5, both still the July prior — no play.",
        keys_a=["Attack Poppinga early", "Hold the line vs Martin",
                "Ball security", "Win field position"],
        keys_b=["Run first, then punish", "Martin and Eka behind the veterans",
                "Prove the new receivers", "Win the hidden margin"]),
    "Alabama at Kentucky": dict(
        ctx_a=dict(coach="DeBoer, year 3 · the referendum", qb="NEW — Keelon Russell, RS freshman", roster="26% back · 17 portal adds"),
        ctx_b=dict(coach="NEW — Will Stein (Oregon OC)", qb="NEW — Kenny Minchey", roster="19% back · 31 portal adds"),
        decides=["DeBoer's referendum, on the road", "Stein's anti-Stoops",
                 "Lowest continuity on the card", "The early landmine"],
        honesty="2.7 to Alabama sits right at the noise line — quibble, not a position.",
        keys_a=["Russell's first road start", "Run it 49 times again",
                "Wommack's secondary vs the void", "Special teams can't leak"],
        keys_b=["The mauling line", "Minchey keeps it clean",
                "The defense is the strength", "Fix third down and the flags"]),
}


def slide_text(g):
    """(decides, honesty, keys_a, keys_b, is_short) — SHORT if authored,
    else the long GAMES strings."""
    sh = SHORT.get(g["title"], {})
    return (sh.get("decides", g["decides"]), sh.get("honesty", g["honesty"]),
            sh.get("keys_a", g["keys_a"]), sh.get("keys_b", g["keys_b"]), bool(sh))


# ---------------- week 0 receipts ----------------
s = blank()
txt(s, 0.9, 0.5, 11.5, 0.55, f"Week {WEEK - 1} — the receipts", 30, NAVY, bold=True)
txt(s, 0.9, 1.08, 11.5, 0.3,
    "Our call frozen at the Ep2 recording · closing line = last pre-kick pull "
    "(Fri 5 PM ET · Mon 9:25 AM ET) · “off by” = miss vs the final margin",
    11, MUTE, italic=True)
y = 1.55
VERD = {"M": ORANGE, "K": RGBColor(0xB5, 0x12, 0x1B), "T": MUTE, "P": MUTE}
for a, b, tit, callfin, lines_, miss, mark in RECAP:
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, y, 11.5, 0.86, ICE)
    logo_badge(s, 1.1, y + 0.13, 0.6, a)
    logo_badge(s, 1.8, y + 0.13, 0.6, b)
    txt(s, 2.6, y + 0.09, 4.8, 0.35, tit, 13.5, INK, bold=True)
    txt(s, 2.6, y + 0.46, 4.9, 0.3, callfin, 10.5, INK)
    txt(s, 7.35, y + 0.11, 4.8, 0.3, lines_, 9.5, MUTE)
    txt(s, 7.35, y + 0.44, 4.8, 0.3, miss, 10, VERD[mark], bold=True)
    y += 0.94
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, y + 0.05, 11.5, 0.85, NAVY)
_rs = RECAP_SUM
_run_m, _run_k = WEEK0_MISS[0] + _rs["m"], WEEK0_MISS[1] + _rs["k"]
txt(s, 1.15, y + 0.17, 11.0, 0.65,
    f"Total miss across {_rs['n']} graded games: machine {_rs['m']:.1f} points, "
    f"closing market {_rs['k']:.1f} — machine closer in {_rs['nm']}, market in "
    f"{_rs['nk']}, {_rs['nt']} tie. Stated positions 2–0: Baylor +7.5 covered "
    "and the MONSTER UNDER on 59.5 cashed (33 total). Two weeks in: machine "
    f"{_run_m:.1f} vs market {_run_k:.1f} across {5 + _rs['n']} games — still a "
    "coin flip with Vegas. Stated leans 3–2 on the season.",
    10.5, WHITE)

# ---------------- per-game slides ----------------
for g in GAMES:
    # -- numbers slide --
    s = blank()
    logo_badge(s, 0.9, 0.42, 0.8, g["a"])
    txt(s, 1.82, 0.52, 0.5, 0.5, g["vs"], 14, MUTE, align=PP_ALIGN.CENTER)
    logo_badge(s, 2.35, 0.42, 0.8, g["b"])
    txt(s, 3.45, 0.38, 8.9, 0.55, g["title"], 27, NAVY, bold=True)
    txt(s, 3.45, 0.94, 8.9, 0.35, g["sub"], 11, MUTE, italic=True)

    # left: what decides it (headline form when SHORT is authored)
    _dec, _hon, _ka, _kb, _short = slide_text(g)
    txt(s, 0.9, 1.75, 7.2, 0.4, "WHY IT MATTERS", 13, NAVY, bold=True)
    yy = 2.25
    for d in _dec:
        shape(s, MSO_SHAPE.OVAL, 0.95, yy + 0.09 + (0.08 if _short else 0), 0.14, 0.14, ORANGE)
        txt(s, 1.3, yy, 6.8, 0.8, d, 21 if _short else 13.5, INK, bold=_short)
        yy += 0.78
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, yy + 0.15, 7.2, 1.05, ICE)
    txt(s, 1.15, yy + 0.32, 6.7, 0.75, _hon, 13 if _short else 11.5, MUTE,
        italic=True)

    # right: navy score bug
    PALE = RGBColor(0xCA, 0xDC, 0xFC)
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 8.5, 1.75, 3.9, 4.6, NAVY)
    txt(s, 8.8, 1.98, 3.3, 0.3, "THE NUMBER", 12, ORANGE, bold=True)
    # machine line as a book would post it + fair odds from our win prob
    txt(s, 8.8, 2.3, 3.3, 0.55, g["machine"], 28, WHITE, bold=True)
    txt(s, 8.8, 2.84, 3.3, 0.3, g.get("fair", ""), 12, WHITE, bold=True)
    txt(s, 8.8, 3.12, 3.3, 0.28,
        "machine line · fair odds, no vig · raw margin " + g.get("raw_margin", ""),
        8.5, PALE)
    # market
    txt(s, 8.8, 3.55, 3.3, 0.45, g["market"], 20, WHITE, bold=True)
    txt(s, 8.8, 3.98, 3.3, 0.4, "market (DK / Bovada) · " + g.get("market_ml", ""),
        8.5, PALE)
    # score prediction (replaced "the gap" per Lucas's in-Slides edit 8/31;
    # the authored value/gap strings stay in GAMES as data)
    score = g.get("score", "")
    txt(s, 8.8, 4.45, 3.3, 0.4, score, 15 if len(score) <= 22 else 13,
        ORANGE, bold=True)
    txt(s, 8.8, 4.82, 3.3, 0.25, "score prediction", 8.5, PALE)
    wa, pa, wb, pb = g["wp"]
    wp_bar(s, 8.8, 5.2, 3.3, 0.4, wa, pa, TEAMS[wa]["color"],
           wb, pb, TEAMS[wb]["color"])
    txt(s, 8.8, 5.66, 3.3, 0.25, "win probability (machine)", 8.5, PALE)
    if g.get("move"):
        txt(s, 8.8, 5.95, 3.3, 0.3, "LINE MOVE  " + g["move"], 9.5,
            ORANGE, bold=True)
    strip = LEDGER[g["title"]]
    if strip:
        txt(s, 0.9, 6.82, 11.5, 0.3, "Line movement: " + strip, 10.5, MUTE)

    # -- team slides (Corey's format: one full slide per team; the score
    #    predictions live only on the closing card, truly LAST). Context band
    #    = the significance frame: coach status, QB situation, roster
    #    continuity (CFBD returning offensive PPA + portal-add counts). --
    _sh = SHORT.get(g["title"], {})
    for key, keys, ctx in ((g["a"], _ka, _sh.get("ctx_a", g["ctx_a"])),
                           (g["b"], _kb, _sh.get("ctx_b", g["ctx_b"]))):
        s = blank()
        logo_badge(s, 0.9, 0.55, 1.15, key)
        txt(s, 2.35, 0.66, 9.9, 0.62, CODE2NAME[key], 32, NAVY, bold=True)
        txt(s, 2.35, 1.34, 9.9, 0.35, "What it takes to win · " + g["title"],
            13, MUTE, italic=True)
        shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, 1.95, 11.5, 1.05, ICE)
        for i, (label, val) in enumerate((("COACH", ctx["coach"]),
                                          ("QB", ctx["qb"]),
                                          ("ROSTER", ctx["roster"]))):
            x = 1.15 + i * 3.85
            txt(s, x, 2.08, 3.55, 0.25, label, 9.5, ORANGE, bold=True)
            txt(s, x, 2.34, 3.55, 0.6, val, 15 if _short else 10.5, INK,
                bold=_short)
        yy = 3.4
        for k in keys:
            shape(s, MSO_SHAPE.OVAL, 1.0, yy + (0.2 if _short else 0.12), 0.15, 0.15, ORANGE)
            txt(s, 1.45, yy, 10.5, 0.8, k, 24 if _short else 15.5, INK,
                bold=_short)
            yy += 0.92
        txt(s, 0.9, 7.13, 11.5, 0.3, f"EP {EPISODE} · WEEK {WEEK} · " + g["title"], 9, MUTE)

# ---------------- upset board (this week's alerts + the scorecard) ----------------
if RENDER_UPSET_BOARD and BOARDS and BOARDS.get("upset_board"):
    UB = BOARDS["upset_board"]
    PALE = RGBColor(0xCA, 0xDC, 0xFC)
    UP, DOWN = RGBColor(0x5C, 0xD6, 0x8A), RGBColor(0xFF, 0x7A, 0x7A)
    s = blank(NAVY)
    txt(s, 0.9, 0.42, 11.5, 0.4,
        f"EPISODE {EPISODE} · WEEK {WEEK} · THE MACHINE'S ALERTS", 14, ORANGE, bold=True)
    txt(s, 0.9, 0.76, 11.5, 0.8, "The Upset Board", 40, WHITE, bold=True)
    txt(s, 0.9, 1.5, 11.5, 0.3,
        "RED = machine takes the dog outright (spread ≥ 3) · YEL = same side, 6+ points "
        "of disagreement · ⚑ = Monster Under total · graded vs the line first seen",
        10.5, PALE, italic=True)
    TOP, RH = 2.08, 0.38
    R = PP_ALIGN.RIGHT
    for x, w, lab, al in ((0.9, 0.5, "TIER", PP_ALIGN.LEFT), (1.45, 3.0, "MATCHUP", PP_ALIGN.LEFT),
                          (4.5, 2.2, "ALERT LINE → NOW", PP_ALIGN.LEFT), (6.75, 0.55, "CLV", R),
                          (7.35, 1.3, "MACHINE (HOME)", R), (8.7, 0.6, "EDGE", R),
                          (9.45, 1.65, "MACHINE SIDE", PP_ALIGN.LEFT), (11.15, 1.25, "DOG ML / O/U", R)):
        txt(s, x, TOP - 0.25, w, 0.22, lab, 8, PALE, bold=True, align=al)
    rows = UB["rows"][:11]
    for i, r in enumerate(rows):
        y = TOP + i * RH
        if i % 2 == 0:
            shape(s, MSO_SHAPE.RECTANGLE, 0.9, y, 11.5, RH, NAVY2)
        red = r["tier"] == "🔴"
        txt(s, 0.95, y + 0.05, 0.5, 0.3, "RED" if red else "YEL", 10,
            DOWN if red else ORANGE, bold=True)
        txt(s, 1.45, y + 0.05, 3.0, 0.3, r["matchup"], 11.5, WHITE, bold=True)
        _short = lambda t: str(t).replace("Florida International", "FIU").replace("Kansas State", "K-State").replace("Sacramento State", "Sac State").replace("Washington State", "Wazzu")
        mv = (f"{_short(r['alert_line'])} → {_short(r['now'])}" if r["now"] and r["now"] != r["alert_line"]
              else f"{_short(r['alert_line'])} (unch.)")
        txt(s, 4.5, y + 0.07, 2.2, 0.3, mv, 9, PALE)
        clv = r["clv"] or 0
        txt(s, 6.75, y + 0.06, 0.55, 0.3, f"{clv:+g}" if clv else "0", 10,
            UP if clv > 0 else (DOWN if clv < 0 else PALE), bold=bool(clv), align=R)
        m = r["margin_home"]
        txt(s, 7.35, y + 0.06, 1.3, 0.3, f"{m:+.1f}" if m is not None else "—", 10, WHITE, align=R)
        txt(s, 8.7, y + 0.06, 0.6, 0.3, f"{abs(r['edge']):.1f}" if r["edge"] is not None else "—",
            10.5, ORANGE, bold=True, align=R)
        txt(s, 9.45, y + 0.06, 1.65, 0.3, r["side"] or "", 10, WHITE)
        tail = f"{r['dog_ml']}" if r["dog_ml"] else ""
        ou = r["ou"].replace(" ⚑MONSTER UNDER", " ⚑")
        txt(s, 11.15, y + 0.07, 1.25, 0.3, (tail + " · " if tail else "") + ou, 9,
            ORANGE if "⚑" in ou or tail else PALE, bold="⚑" in ou or bool(tail), align=R)
    _fy = TOP + len(rows) * RH + 0.12
    sc = {k: v for k, v in UB["scorecard"]}
    line1 = (f"Scorecard 2026 (vs first-seen lines): {sc.get('Alerts logged')} alerts · model side "
             f"{sc.get('Model side ATS')} ATS · RED dogs outright {sc.get('Red dogs outright*')} · "
             f"avg CLV {sc.get('Avg CLV, graded (pts)')} · beat/tie/lost the close "
             f"{sc.get('CLV beat-tie-lost close')} · {sc.get('Pending')} pending")
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, _fy, 11.5, 0.62, NAVY2)
    txt(s, 1.1, _fy + 0.06, 11.2, 0.28, line1, 9.5, WHITE, bold=True)
    txt(s, 1.1, _fy + 0.32, 11.2, 0.28,
        "Backtest 2023–25: these rules ran 49.7% ATS — a research shortlist and a "
        "narrative engine, not a bet slip · RED dogs at +401 or longer on the road are "
        "ATS-only (longshot moneylines bled −22.9% ROI 2021–25)", 8.5, PALE)

# ---------------- closing card: predictions + superdogs ----------------
s = blank(NAVY)
PALE = RGBColor(0xCA, 0xDC, 0xFC)
txt(s, 0.9, 0.55, 11.5, 0.45, f"EPISODE {EPISODE} · THE CARD", 14, ORANGE, bold=True)
txt(s, 0.9, 0.95, 11.5, 0.8, "Our predictions", 36, WHITE, bold=True)
y = 1.95
for g in GAMES:
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, y, 11.5, 0.72, NAVY2)
    logo_badge(s, 1.1, y + 0.1, 0.52, g["a"], plate=True)
    logo_badge(s, 1.75, y + 0.1, 0.52, g["b"], plate=True)
    txt(s, 2.5, y + 0.19, 5.4, 0.4, g["title"], 14, WHITE, bold=True)
    txt(s, 7.0, y + 0.09, 5.2, 0.42, g.get("score", ""), 15.5, ORANGE,
        bold=True, align=PP_ALIGN.RIGHT)
    txt(s, 7.0, y + 0.47, 5.2, 0.25, "market " + g["market"], 8.5,
        RGBColor(0x8F, 0xA5, 0xC4), align=PP_ALIGN.RIGHT)
    y += 0.8
# superdog band
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, y + 0.08, 11.5, 1.02, ORANGE)
for i, (label, board) in enumerate(
        [("SUPERDOG", [r for r in SUPERDOG_ANY if not r["rank"]]),
         ("GIANT KILLER", SUPERDOG_T25)]):
    if not board:
        continue
    r = board[0]
    fav = (f"#{r['rank']} " if r["rank"] else "") + r["fav"]
    ml = f" · ML {int(r['ml']):+d}" if r.get("ml") is not None else ""
    txt(s, 1.2, y + 0.17 + i * 0.44, 3.0, 0.35, "★ " + label, 13, NAVY,
        bold=True)
    txt(s, 3.6, y + 0.17 + i * 0.44, 8.6, 0.35,
        f"{r['dog']} +{r['pts']:g} {r['at']} {fav}{ml}", 13.5, WHITE,
        bold=True)
txt(s, 0.9, 7.18, 11.5, 0.3,
    "projected scores = machine margin on the market total · superdogs = "
    "dog to win outright, points = the spread · graded vs first-seen lines "
    "· research, not picks", 9, RGBColor(0x8F, 0xA5, 0xC4), italic=True)

out = os.path.join(HERE, "decks", f"2026_Week{WEEK}_Episode{EPISODE}.pptx")
prs.save(out)
print("wrote", out, f"- {len(prs.slides)} slides")
