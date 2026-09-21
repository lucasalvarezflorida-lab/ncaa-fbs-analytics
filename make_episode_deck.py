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

EPISODE, WEEK = 5, 4
RENDER_UPSET_BOARD = False   # Lucas 9/9: off; flip to True to add the alerts slide before the closer
EP_DATE = "SEP 26, 2026"
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
    "FLA": dict(code="FLA", color=(0x00, 0x21, 0xA5), logo="florida.png"),
    "TTU": dict(code="TTU", color=(0xCC, 0x00, 0x00), logo="texastech.png"),
    "MSST": dict(code="MSST", color=(0x5D, 0x1A, 0x2A), logo="mississippistate.png"),
    "SCAR": dict(code="SCAR", color=(0x73, 0x00, 0x0A), logo="southcarolina.png"),
    "HOU": dict(code="HOU", color=(0xC8, 0x10, 0x2E), logo="houston.png"),
    "TENN": dict(code="TENN", color=(0xFF, 0x82, 0x00), logo="tennessee.png"),
    "ORE": dict(code="ORE", color=(0x15, 0x47, 0x33), logo="oregon.png"),
    "USC": dict(code="USC", color=(0x99, 0x00, 0x00), logo="usc.png"),
    "UGA": dict(code="UGA", color=(0xBA, 0x0C, 0x2F), logo="georgia.png"),
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
             "Alabama": "BAMA", "Kentucky": "UK", "Florida": "FLA",
             "Texas Tech": "TTU", "Mississippi State": "MSST",
             "South Carolina": "SCAR", "Houston": "HOU", "Tennessee": "TENN",
             "Oregon": "ORE", "USC": "USC", "Georgia": "UGA"}

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
        pts = [int(x + 0.5) for _, x in order]
        if pts[0] == pts[1] and m:      # never call a tie: the machine's side gets the extra point
            pts[0] += 1
        g["score"] = " – ".join(f"{disp.get(t, t)} {n}" for (t, _), n in zip(order, pts))
        g["score_note"] = f"projected score · machine margin on the {float(total):g} market total"
    else:
        g["score"], g["score_note"] = "total not posted yet", ""
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

_GAMES_EP3 = [  # Week 2 archive — the frozen Ep3 predictions (unrendered)
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

_GAMES_EP4 = [  # Week 3 archive — the frozen Ep4 predictions (unrendered)
    dict(
        a="HOU", b="TTU", vs="at", title="Houston at Texas Tech",
        cfbd=("Houston", "Texas Tech"),
        where="Lubbock · Jones AT&T Stadium",
        sub="Fri Sep 18 · 8:00 ET · the Big 12's first litmus test",
        machine="Texas Tech –13", market="–7.5", value="5.5 to Tech — small lean",
        wp=("TTU", 79, "HOU", 21),
        decides=["The prep flagged this as the Big 12's first great litmus test: Houston is the sleeper, Tech the defending champ",
                 "Fritz's year three — his career pattern says this is the monster year (.725 in year threes)",
                 "Hammond after the scare in Corvallis: 35–24 at Oregon State, 155 rushing at 3.4",
                 "Tech has won four straight in the series (38–21, 33–30, 49–28, 35–11), three by double digits; the market has moved six points toward Houston since August and the machine hasn't"],
        ctx_a=dict(coach="Fritz, year 3 — the year-three pattern (Tulane: 2 wins to 12)",
                   qb="RETURNS — Conner Weigman (2,705 pass / 795 rush / 36 TD in 2025); five-star Henderson behind him",
                   roster="81% back · 18 portal adds — the Tulane band reunited"),
        ctx_b=dict(coach="McGuire, year 5 — Shiel Wood's portal-built defense",
                   qb="Will Hammond, back from an October ACL — 20-of-27 at Oregon State",
                   roster="53% back · 23 portal adds — DL two-deep bought in the portal again"),
        honesty="Machine −13, market −7.5: 5.5 points to Tech, 5.7 points of win probability — still under the 6-point flag line because the market's moneyline (Tech −300) prices Tech at 73.5%. Tech has won four straight in the series by double digits three times. A small lean; the 53.5 total is Bovada's (DK hasn't posted one).",
        keys_a=["Weigman's legs vs the rebuilt front", "Run it 45 times — 388 on the ground last week", "Make Hammond throw from the pocket", "Win the trenches — the league's best combined line play"],
        keys_b=["Hammond's second real start", "J'Koby Williams downhill (116 at Oregon State)", "The portal defense vs a real offense", "Finish drives — 8-of-16 on third down in Corvallis"],
    ),
    dict(
        a="SMU", b="LOU", vs="at", title="SMU at Louisville",
        cfbd=("SMU", "Louisville"),
        where="Louisville · L&N Federal Credit Union Stadium",
        sub="Sat Sep 19 · 3:30 ET · the ACC's biggest non-Miami game",
        machine="Louisville –1", market="–1.5", value="machine = market · MONSTER UNDER 59.5",
        wp=("LOU", 54, "SMU", 46),
        decides=["The ACC prep called this the biggest non-Miami game on the calendar — the loser is chasing Charlotte by Week 3",
                 "Jennings in year three: 430 at FSU, then 14-of-16 for 337 and five scores",
                 "Brohm's coin-flip problem: three 2025 ACC losses by seven combined points, and a three-point loss to Ole Miss already",
                 "Both offenses score fast: three straight top-25 offenses under Lashlee, Brohm's system top-25 every year, and two defenses that bust — SMU havoc-rich and bust-prone, Louisville top-20 havoc and bottom-40 on explosives"],
        ctx_a=dict(coach="Lashlee, year 5 — both coordinators left; co-coordinator troikas",
                   qb="RETURNS — Kevin Jennings, third-year starter: SMU is 12–1 when his QBR clears 76",
                   roster="57% back · 15 portal adds — kept the line, lost the callers"),
        ctx_b=dict(coach="Brohm, year 4 — 28–12, three straight 9-win years",
                   qb="Lincoln Kienholz — 307 vs Ole Miss, 332 vs Villanova, zero picks",
                   roster="35% back · 33 portal adds — the annual re-skin"),
        honesty="Machine Louisville by 1.1, market by 1.5 — agreement, no play on the side. The number that matters is the total: 59.5 is a Monster Under, and SMU's defense is havoc-rich and bust-prone while Louisville's is top-20 havoc, bottom-40 explosives. Say the 55% and move on.",
        keys_a=["Jennings vs the bust-prone back end", "Protect Jennings — line play a tier below", "Win the takeaway ledger", "Explosives, not long drives"],
        keys_b=["Ride the Browns — the country's best RB duo", "No coverage busts", "Kienholz keeps it clean", "Win the one-score game"],
    ),
    dict(
        a="MSST", b="SCAR", vs="at", title="Mississippi State at South Carolina",
        cfbd=("Mississippi State", "South Carolina"),
        where="Columbia · Williams-Brice Stadium",
        sub="Sat Sep 19 · 4:15 ET · two hot seats, one game",
        machine="South Carolina –5", market="–4", value="0.9 to South Carolina — no play",
        wp=("SCAR", 63, "MSST", 37),
        decides=["Beamer (CBS 4.3, the SEC's hottest seat) vs Lebby (3.3, one SEC win in two years) — one of them leaves 0–1 in the league",
                 "Kamario Taylor's breakout is real: 16-of-22 for 227 and three scores plus 86 on the ground at Minnesota; State is +4.4 in our ratings",
                 "Sellers hasn't thrown yet: 10-of-23 for 96 against Towson while the team ran for 405",
                 "Arnett's defense, back in Starkville: the head coach Lebby replaced is State's DC again — his 4-2-5 held Minnesota to 13 rushing yards but allowed 279 through the air, and Sellers hasn't thrown yet"],
        ctx_a=dict(coach="Lebby, year 3 — 7–18; Arnett back as DC",
                   qb="Kamario Taylor, sophomore — the SEC's quiet breakout pick",
                   roster="34% back · 28 portal adds — six of seven OL gone"),
        ctx_b=dict(coach="Beamer, year 6 — 33–30; fourth OC in five years (Briles)",
                   qb="RETURNS — LaNorris Sellers, a top-5 draft profile who came back",
                   roster="69% back · 26 portal adds — eight new offensive linemen"),
        honesty="Machine −4.9, market −4 — 0.9 points apart, agreement. Both sides have real 2026 evidence now (State beat a rated Minnesota by 25; South Carolina's rated game was 57–0). The total, 58.5, fell just under the Monster Under line on the Tuesday pull. The story is the two seats, not the side.",
        keys_a=["Taylor's legs and arm", "Bothwell downhill (113 at Minnesota)", "Arnett's defense vs Sellers", "Win the turnover ledger"],
        keys_b=["Let Sellers throw", "Protect Sellers — the same sentence as last July", "Harbor deep", "Stewart off the edge"],
    ),
    dict(
        a="FLA", b="AUB", vs="at", title="Florida at Auburn",
        cfbd=("Florida", "Auburn"),
        where="Auburn · Jordan-Hare Stadium",
        sub="Sat Sep 19 · 7:00 ET · two first-year coaches",
        machine="Auburn –0.5", market="+2.5", value="machine takes the home dog — lean Auburn +2.5",
        wp=("AUB", 53, "FLA", 47),
        decides=["Two first-year coaches in the SEC's most underrated game: Sumrall (Tulane to the CFP) vs Golesh (USF 114th to 30th in SP+)",
                 "Auburn's rebuilt lines vs Florida's front: the top five OL gone and nine transfer linemen in, against the interior defensive line Napier stockpiled — 343 rushing at 6.7 last week was against Southern Miss; Baylor held Auburn to 103",
                 "Byrum Brown vs Aaron Philo: a 42-touchdown transfer with three picks in the opener vs a redshirt freshman who has thrown 32 passes",
                 "Jordan-Hare at night in year-one-energy mode — the prep's exact phrase for a home upset"],
        ctx_a=dict(coach="NEW — Jon Sumrall (Tulane): 20 wins and a CFP berth in two years",
                   qb="NEW — Aaron Philo, RS freshman (Georgia Tech): 16-of-21 for 242 vs Campbell",
                   roster="69% back · 27 portal adds — Baugh (1,170 yards) kept"),
        ctx_b=dict(coach="NEW — Alex Golesh (USF) · Durkin retained as DC",
                   qb="NEW — Byrum Brown (USF): 223 passing and 88 rushing vs Southern Miss",
                   roster="14% back · 39 portal adds — the most retooled roster on the card"),
        honesty="The machine has Auburn by 0.7 at home; the market has Florida by 2.5 — 3.2 points apart and 7.6 points of win probability, the widest gap on the card. Both ratings carry one rated game each. Lean Auburn +2.5 as research: the case is Jordan-Hare and Brown's legs, and the risk is Auburn's ball security (three picks in the opener).",
        keys_a=["Philo's first road start", "Baugh downhill (136 vs Campbell)", "White's front vs Brown's legs", "Fourth-down conviction — the Sumrall trait"],
        keys_b=["Brown's legs — 88 yards last week", "Ball security — three picks in the opener, zero since", "Durkin's defense at home", "Tempo without turnovers"],
    ),
    dict(
        a="LSU", b="MISS", vs="at", title="LSU at Ole Miss",
        cfbd=("LSU", "Ole Miss"),
        where="Oxford · Vaught-Hemingway Stadium",
        sub="Sat Sep 19 · 7:30 ET · Kiffin returns to Oxford",
        machine="LSU –5", market="–3", value="2.2 to LSU — quibble · MONSTER UNDER 59.5",
        wp=("LSU", 62, "MISS", 38),
        decides=["Kiffin walks back into the Vaught with the roster he built against the QB who refused to follow him — the most emotionally charged game of 2026",
                 "The home team has won five straight in this series (Ole Miss 24–19 last year)",
                 "Leavitt threw three interceptions against Louisiana Tech; Chambliss went 23-of-26 against Charlotte",
                 "55–49 or 24–19: the last three in this series were a 104-point shootout and two grinders (29–26, 24–19) — LSU has 11 sacks in two games and Golding kept the defensive spine, so the fronts decide which version shows up"],
        ctx_a=dict(coach="NEW — Lane Kiffin, off Ole Miss's 13-win CFP season",
                   qb="NEW — Sam Leavitt: 344 yards and three picks vs Louisiana Tech",
                   roster="21% back · 44 portal adds — the Portal King's magnum opus"),
        ctx_b=dict(coach="NEW — Pete Golding, promoted; kept the defensive spine",
                   qb="RETURNS — Trinidad Chambliss, via lawsuit and injunction",
                   roster="50% back · 28 portal adds — the secondary is the patch"),
        honesty="Machine LSU by 5.2, market by 3: 2.2 to LSU, inside the noise line, and the machine's LSU number still carries the 51–10 Clemson game. Five straight home wins in the series and a first-year coach on each sideline are the hedges. Quibble, not a position. The total is the play to talk about.",
        keys_a=["Leavitt's ball security", "Protect Leavitt in a hostile building", "Baker's front vs Chambliss's escapes", "Kiffin's tempo in his old house"],
        keys_b=["Let Chambliss escape", "Lacy runs it (87 vs Charlotte)", "The patched secondary vs LSU's receivers", "Special teams — No. 1 in SP+"],
    ),
]

GAMES = [  # Week 4 — kickoff order (Lucas 9/20: Oklahoma–Georgia third); Texas A&M at LSU closes
    dict(
        a="TEX", b="TENN", vs="at", title="Texas at Tennessee",
        cfbd=("Texas", "Tennessee"),
        where="Knoxville · Neyland Stadium",
        sub="Sat Sep 26 · 12:00 ET · No. 1 at No. 14 — Texas's first road game",
        machine="Texas –9", market="–5.5", value="3.5 to Texas — quibble",
        wp=("TEX", 71, "TENN", 29),
        decides=["No. 1 leaves Austin for the first time: three home games, one of them a one-point win over Ohio State",
                 "A five-star true freshman against the No. 1 team: Faizon Brandon won the job over MacIntyre and has not thrown a pick",
                 "Heupel's July goal was to steal one marquee home game — Texas and LSU both come to Neyland",
                 "Knowles' first Tennessee defense gets its first real quarterback; his year ones are historically glitchy"],
        ctx_a=dict(coach="Sarkisian, year 6 · Muschamp's defense is carrying it",
                   qb="Arch Manning, final season · 6.8 a throw through three home games",
                   roster="72% back · 22 portal adds"),
        ctx_b=dict(coach="Heupel, year 6 · new DC Jim Knowles, his fourth defensive rebuild",
                   qb="NEW — Faizon Brandon, five-star true freshman · 6 TD, 0 INT",
                   roster="35% back · 21 portal adds — 12 defensive transfers"),
        honesty="Machine Texas −9, market −5.5: 3.5 points to Texas and five points of win probability (71% vs 66%) — under the flag line. The machine's Texas number is the Ohio State win plus the preseason prior; it has not seen this offense leave Austin, and the offense is the weak half (6.8 a throw, 6 explosive passes in 110 dropbacks). The market opened −6.5 and has come toward Tennessee. Quibble, not a position.",
        keys_a=["Arch has to hit something downfield", "Stay out of third-and-long", "Stop the run — Texas State ran for 221", "Simmons vs the freshman"],
        keys_b=["Run it at Texas — 7.1 a carry", "Brandon's first ranked opponent", "Knowles' rush on passing downs", "Win the red zone"],
    ),
    dict(
        a="MISS", b="FLA", vs="at", title="Ole Miss at Florida",
        cfbd=("Ole Miss", "Florida"),
        where="Gainesville · Ben Hill Griffin Stadium",
        sub="Sat Sep 26 · 3:30 ET · No. 4 at No. 21 — two first-year coaches, both 3–0",
        machine="Florida –3", market="–2.5", value="machine = market · MONSTER UNDER 59.5",
        wp=("FLA", 59, "MISS", 41),
        decides=["Two first-year head coaches, both 3–0: Golding beat LSU, Sumrall won 44–39 at Auburn — the winner is the SEC's surprise contender",
                 "The voters have Ole Miss No. 4 and Florida No. 21; the machine has them a point apart (Florida 18.5, Ole Miss 17.9)",
                 "The home team has won the last two: Florida 24–17 in 2024 (the loss that kept Ole Miss out of the CFP), Ole Miss 34–24 last year",
                 "Aaron Philo's first ranked opponent in the Swamp: 11.3 a throw, 19% of dropbacks go for 20+"],
        ctx_a=dict(coach="NEW — Golding, promoted · 3–0 with the LSU win",
                   qb="Chambliss returns · sacked 3 times in 122 dropbacks",
                   roster="50% back · 28 portal adds"),
        ctx_b=dict(coach="NEW — Sumrall (Tulane) · 3–0",
                   qb="NEW — Aaron Philo, RS freshman · 11.3 a throw",
                   roster="69% back · 27 portal adds"),
        honesty="Machine Florida −3, market −2.5 — agreement, no side. The total is 59.5, a Monster Under number, but four of last week's five card games went over and both of these defenses have given up 38 or more once already. Say the 59% and move on.",
        keys_a=["Chambliss vs the Florida rush", "Stop the explosives — 12 allowed in 90 dropbacks", "Get Lacy going", "Finish drives — 10 of 11 in the red zone"],
        keys_b=["Feed Baugh — 458 yards, 8 TD", "Philo deep — 10 of 16", "Get Chambliss off schedule", "Tighten the red zone defense"],
    ),
    dict(
        a="OU", b="UGA", vs="at", title="Oklahoma at Georgia",
        cfbd=("Oklahoma", "Georgia"),
        where="Athens · Sanford Stadium",
        sub="Sat Sep 26 · 3:30 ET · unranked Oklahoma at No. 2 — the best pass rush on the card",
        machine="Georgia –14", market="–14", value="machine = market — no play",
        wp=("UGA", 81, "OU", 19),
        decides=["Oklahoma has scored 24 points in its last two games — 10 at Michigan, 14 against New Mexico — and dropped out of the poll",
                 "Georgia's old flaw looks fixed: Stockton is 38 of 45 with nine touchdowns and 17% of dropbacks have gone for 20+",
                 "Venables' defense is the best unit Georgia has seen: 12 sacks in 66 dropbacks, one red-zone touchdown allowed in six trips",
                 "Georgia's schedule avoids Texas, A&M and LSU — this and the trip to Oxford are the games that decide a first-round bye"],
        ctx_a=dict(coach="Venables, year 5 · the defense is elite, the offense is not",
                   qb="Mateer returns, senior · 3 picks",
                   roster="63% back · 16 portal adds"),
        ctx_b=dict(coach="Smart, year 11 · Bobo's offense",
                   qb="Stockton returns · 38 of 45, 9 TD, 0 INT",
                   roster="69% back · 9 portal adds — 169 returning starts"),
        honesty="Machine Georgia −14, market −14 — dead agreement, no play. The market opened −10 and walked four points after Oklahoma's 14–6 win over New Mexico. The total, 45.5, is the lowest on the card; the machine has no totals model, so the score call is the margin laid over it.",
        keys_a=["The pass rush is the path", "Mateer has to be the run game", "Reach the red zone", "Force a turnover — zero picks so far"],
        keys_b=["Frazier downhill — 7.9 a carry", "Get the ball out on this rush", "Make Mateer one-dimensional", "Keep hitting explosives"],
    ),
    dict(
        a="ORE", b="USC", vs="at", title="Oregon at USC",
        cfbd=("Oregon", "USC"),
        where="Los Angeles · Memorial Coliseum",
        sub="Sat Sep 26 · 7:30 ET · No. 20 at No. 12 — Oregon's season on the line in Week 4",
        machine="Oregon –0.5", market="–1.5", value="pick'em — no play · MONSTER UNDER 62.5",
        wp=("ORE", 50, "USC", 50),
        decides=["Oregon already lost as a 23.5-point favorite in Stillwater — a second loss before October makes the Big Ten title game the only road to the playoff",
                 "Riley's year five, 'no more excuses': USC is 4–0 but gave up 35 at Rutgers and 30 to Louisiana",
                 "The July prep called this trip and Ohio State the season's two proof points for Oregon; Oregon has won the last two, 36–27 and 42–27, both in Eugene",
                 "Both coordinators are new at Oregon and Gary Patterson, 66, is the new defense at USC — two offenses ahead of two defenses"],
        ctx_a=dict(coach="Lanning, year 5 · both coordinators new",
                   qb="Dante Moore returns · 9 TD, 0 INT",
                   roster="75% back · 13 portal adds — 200 returning starts"),
        ctx_b=dict(coach="Riley, year 5 · new DC Gary Patterson",
                   qb="Maiava returns · 12 TD, 10.2 a throw",
                   roster="59% back · 9 portal adds — seven of the top eight receivers gone"),
        honesty="Machine Oregon −0.5, market −1.5: a pick'em either way. The machine has taken eight points off Oregon since July, more than any team in the Top 25; the market opened Oregon −5.5 and has moved four points toward USC. No position. The total, 62.5, is the highest on the card and a Monster Under number — and neither defense has earned it.",
        keys_a=["Protect Moore — 4 sacks in Stillwater", "Stay out of third-and-long", "Attack Patterson's secondary", "Stop the run this time"],
        keys_b=["Keep Maiava clean", "Own third down — 62%", "Finish in the red zone", "Patterson's defense vs the explosives"],
    ),
    dict(
        a="TAMU", b="LSU", vs="at", title="Texas A&M at LSU",
        cfbd=("Texas A&M", "LSU"),
        where="Baton Rouge · Tiger Stadium",
        sub="Sat Sep 26 · 7:30 ET · No. 23 at No. 10 — the loser has two losses in September",
        machine="LSU –5.5", market="–8.5", value="3 to A&M — the market ran past us",
        wp=("LSU", 64, "TAMU", 36),
        decides=["Both lost last week — A&M at home to Kentucky as a 16.5-point favorite, LSU in Kiffin's return to Oxford; the loser is 2–2",
                 "A&M's schedule still has Alabama, Texas, Tennessee, Oklahoma and South Carolina — this is the first of five games it cannot give away",
                 "Leavitt has five interceptions in three games; Reed has three and is throwing for 6.1 a pop",
                 "A&M won 49–25 in this building last year; before that the home team had won four straight"],
        ctx_a=dict(coach="Elko, year 3 · two new coordinators",
                   qb="Reed returns · 6.1 a throw, 3 picks",
                   roster="73% back · 19 portal adds — both lines rebuilt"),
        ctx_b=dict(coach="NEW — Kiffin · lost his Oxford return",
                   qb="NEW — Sam Leavitt · 5 picks in three games",
                   roster="21% back · 44 portal adds"),
        honesty="Machine LSU −5.5, market −8.5: three points to A&M on the number and twelve points of win probability (LSU 64% vs the market's 77%) — the biggest gap on the card, still under the 15-point flag. The market opened LSU −3 and moved 5.5 after Kentucky; the machine counts Kentucky as one game and moved A&M 5.3. Our backtest says a stale number loses to a market move like that. No position.",
        keys_a=["Find an explosive play — 5 in 115 dropbacks", "Block Umanmielen", "Fix the back end — 14.0 a throw vs Kentucky", "Don't count on the run"],
        keys_b=["Leavitt's ball security", "Throw deep on this secondary", "Umanmielen on passing downs", "Touchdowns, not field goals"],
    ),
]

# ---- Week 3 receipts (recap slide): frozen Ep4 predictions vs finals vs the
# last pre-kick ledger pull (Fri Sep 18 5 PM MT publish pull,
# card_data_week3.json). Finals are read from the CFBD games cache; a game
# not yet played renders as a pending row and grades itself after the next
# refresh. Lines are home-perspective spreads (negative = home favored).
_RECAP_ROWS_WK2 = [
    ("OSU", "TEX", "Ohio State at Texas", ("Ohio State", "Texas"), "Texas 27–23", -3.5, -1.5),
    ("OU", "MICH", "Oklahoma at Michigan", ("Oklahoma", "Michigan"), "Oklahoma 23–21", 2.0, 5.5),
    ("ASU", "TAMU", "Arizona State at Texas A&M", ("Arizona State", "Texas A&M"), "Texas A&M 34–17", -16.5, -14.5),
    ("ARIZ", "BYU", "Arizona at BYU", ("Arizona", "BYU"), "BYU 28–20", -8.5, -7.5),
    ("BAMA", "UK", "Alabama at Kentucky", ("Alabama", "Kentucky"), "Alabama 31–18", 13.0, 10.0),
]   # Week 2: machine 40.5 vs market 48.0 (machine closer 4 of 5)
RECAP_ROWS = [
    # a, b, title, (away, home), our call, our line, closing line (home-perspective),
    # then optional: the MAN's call (Corey's score slide: each number sits under
    # that team's logo, his winner in green - read 9/21 from the 9/15 read-only
    # export) and the closing total (for the market-implied score).
    ("HOU", "TTU", "Houston at Texas Tech", ("Houston", "Texas Tech"), "Texas Tech 33–20", -13.0, -7.5, "Texas Tech 35–24", 52.5),
    ("SMU", "LOU", "SMU at Louisville", ("SMU", "Louisville"), "Louisville 30–29", -1.0, -1.5, "Louisville 35–34", 58.5),
    ("MSST", "SCAR", "Mississippi State at South Carolina", ("Mississippi State", "South Carolina"), "South Carolina 32–27", -5.0, -4.0, "South Carolina 31–27", 58.5),
    ("FLA", "AUB", "Florida at Auburn", ("Florida", "Auburn"), "Auburn 27–26", -0.5, 2.5, "Auburn 28–27", 53.5),
    ("LSU", "MISS", "LSU at Ole Miss", ("LSU", "Ole Miss"), "LSU 32–27", 5.0, 3.0, "LSU 34–28", 58.5),
]   # Week 3 margin miss: market 38.5 · man 49.0 · machine 50.5
WEEK0_MISS = (161.0, 167.0)  # machine, market through Week 2 (15 games) — running total
PRIOR_GAMES = 15
LEANS_LINE = "stated leans 4–3 · Auburn +2.5 lost by 5"


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


def _deserved():
    """(away, home) normalized -> deserved home margin (efficiency layer);
    empty if the model or the box scores are missing."""
    try:
        from inseason_ratings import deserved_margins
        return {(d["away"], d["home"]): d["deserved"] for d in deserved_margins().values()}
    except Exception as e:  # pragma: no cover - deck must build without it
        print("deserved margins unavailable:", e)
        return {}


DESERVED = _deserved()


def _call_pts(call, key):
    """'Texas Tech 33–20' -> (away_pts, home_pts) for key = (away, home)."""
    name, sc = call.rsplit(" ", 1)
    hi, lo = (int(x) for x in sc.replace("-", "–").split("–"))
    return (lo, hi) if name == key[1] else (hi, lo)


RECEIPTS_SHOW_MARKET = False   # Lucas 9/21: the market is INTERNAL - graded in the notes and
                               # MARKET_DEEP_DIVE, never on the receipts slide (man vs machine only)


def build_recap():
    """Rows + totals. Margin miss ('off by') for machine / market / man; SCORE
    miss = points off the final for both teams added up, for the two score
    calls (and the market's implied score, spread laid over the closing total)."""
    finals = _finals()
    rows = []
    T = dict(m=0.0, k=0.0, c=0.0, d=0.0, sm=0.0, sc=0.0, sk=0.0, n=0, nm=0, nk=0, nc=0, nt=0, man=False)
    for row in RECAP_ROWS:
        a, b, title, key, call, ours, close = row[:7]
        man = row[7] if len(row) > 7 else None
        ou = row[8] if len(row) > 8 else None
        lines_ = f"our line {_line_txt(a, b, ours)}"
        if RECEIPTS_SHOW_MARKET:
            lines_ += f" · closing {_line_txt(a, b, close)}"
        fin = finals.get(key)
        calls = f"Machine {NAME2CODE[call.rsplit(' ', 1)[0]]} {call.rsplit(' ', 1)[1]}"
        if man:
            calls += f" · Man {NAME2CODE[man.rsplit(' ', 1)[0]]} {man.rsplit(' ', 1)[1]}"
        if fin is None:
            rows.append((a, b, title, calls + " · FINAL pending",
                         lines_, "graded before air — see the notes", "P"))
            continue
        ap_, hp_ = fin
        win = b if hp_ >= ap_ else a
        callfin = f"{calls} · FINAL {win} {max(ap_, hp_)}–{min(ap_, hp_)}"
        margin = hp_ - ap_                       # actual home margin
        des = DESERVED.get((normalize_name(key[0]), normalize_name(key[1])))
        if des is not None:
            lines_ += f" · deserved {b if des >= 0 else a} +{abs(des):.1f}"
            T["d"] += abs(des + ours)
        off = {"M": abs(margin + ours), "K": abs(margin + close)}
        ma, mh = _call_pts(call, key)
        T["sm"] += abs(ma - ap_) + abs(mh - hp_)
        if ou is not None:
            T["sk"] += abs((ou + close) / 2 - ap_) + abs((ou - close) / 2 - hp_)
        if man:
            T["man"] = True
            ca, ch = _call_pts(man, key)
            off["C"] = abs(margin - (ch - ca))
            T["c"] += off["C"]
            T["sc"] += abs(ca - ap_) + abs(ch - hp_)
        T["m"] += off["M"]; T["k"] += off["K"]; T["n"] += 1
        shown = {k: v for k, v in off.items() if k != "K" or RECEIPTS_SHOW_MARKET}
        best = min(shown.values())
        who = [k for k, v in shown.items() if v == best]
        label = {"M": "machine", "K": "market", "C": "man"}
        if len(who) == 1:
            mark, verdict = who[0], f"{label[who[0]]} closest" if len(shown) > 2 else f"{label[who[0]]} closer"
            T[{"M": "nm", "K": "nk", "C": "nc"}[mark]] += 1
        else:
            mark, verdict = "T", ("dead tie" if len(who) == len(shown) else " / ".join(label[k] for k in who) + " tie")
            T["nt"] += 1
        miss = f"off by · machine {off['M']:g}"
        if RECEIPTS_SHOW_MARKET:
            miss += f" · market {off['K']:g}"
        if man:
            miss += f" · man {off['C']:g}"
        if len(shown) == 1:
            mark, verdict = "M", ""
        rows.append((a, b, title, callfin, lines_, miss + (f" — {verdict}" if verdict else ""), mark))
    return rows, T


RECAP, RECAP_SUM = build_recap()

# ---- Superdog boards. RULEBOOK (settled with Corey 2026-09-19): a 3.5+ point
# dog; SUPERDOG = any matchup, GIANT KILLER = an unranked dog vs an AP Top 25
# team; 5 points for a cover, 5 + the spread for an outright win, 1 for a
# push. Picks + standings live in superdog_ledger.json. Computed live from card_data so a fresh pull refreshes them.
# AP Top 25 comes from the CFBD /rankings cache via inseason_ratings (the
# Tuesday refresh and every edge_report --publish keep it current); the hand
# dict below is only a fallback if the cache is missing (last synced: week 2).
_AP_FALLBACK_WEEK = 3
_AP_FALLBACK = {"Texas": 1, "Georgia": 2, "Notre Dame": 3, "Indiana": 4,
            "Miami": 5, "Ohio State": 6, "LSU": 7, "Ole Miss": 8,
            "Texas A&M": 9, "Alabama": 10, "BYU": 11, "USC": 12,
            "Texas Tech": 13, "Penn State": 14, "Tennessee": 15, "SMU": 16,
            "Utah": 17, "Iowa": 18, "Michigan": 19, "Missouri": 20,
            "Oregon": 21, "Houston": 22, "Louisville": 23, "Oklahoma": 24,
            "Virginia": 25}  # AP week 3 (Sun Sep 13)  # AP week 2


def _load_ap():
    try:
        from inseason_ratings import latest_rankings
        r = latest_rankings(refresh=False)
        if r.get("ap") and (r.get("week") or 0) >= _AP_FALLBACK_WEEK:
            return dict(r["ap"]), r.get("week")
    except Exception as e:  # cache missing / import problem -> fallback
        print("AP poll: cache unavailable,", e)
    return {normalize_name(k): v for k, v in _AP_FALLBACK.items()}, _AP_FALLBACK_WEEK


AP_TOP25, AP_WEEK = _load_ap()


def ap_rank(team):
    return AP_TOP25.get(normalize_name(team))



_MONTHS = dict(Jan=1, Feb=2, Mar=3, Apr=4, May=5, Jun=6, Jul=7, Aug=8,
               Sep=9, Oct=10, Nov=11, Dec=12)


SUPERDOG_MIN_SPREAD = 3.5   # rulebook: a superdog is a 3.5+ point dog
SUPERDOG_COVER_PTS, SUPERDOG_PUSH_PTS = 5, 1   # rulebook: cover 5, win 5 + spread, push 1
SUPERDOG_MAX_SPREAD = 28.0  # the rating caps a game's evidence at 28: lines past it are outside what the machine can price
SUPERDOG_MAX_EDGE = 15.0    # model-vs-market gaps this big went 46.8% ATS 2023-25: stale prior, not an edge
SUPERDOG_TIE_PTS = 0.25     # expected points within a quarter point of the leader are a tie -> home dog first


def _cover_curve():
    """Margin curve at the in-season sd (ratings_current_2026.json), else as fitted."""
    from margin_prob import load_curve
    try:
        import json as _j
        sd = _j.load(open(os.path.join(HERE, "ratings_current_2026.json"),
                          encoding="utf-8"))["params"].get("sigma")
    except (FileNotFoundError, KeyError, ValueError):
        sd = None
    return load_curve("model", sd=sd)


def home_dog_tiebreak(rows):
    """rows sorted by expected points; inside the leader's tie band a home dog
    goes first (2026 through Wk 3: home dogs 30% outright, road dogs 14%)."""
    if not rows:
        return rows
    band = [r for r in rows if rows[0]["exp_pts"] - r["exp_pts"] <= SUPERDOG_TIE_PTS]
    band.sort(key=lambda r: r["at"] != "vs")   # stable: home dogs first
    return band + rows[len(band):]


def superdog_boards():
    """(any-game rows, vs-top-25 rows), each sorted by EXPECTED RULEBOOK POINTS
    = 5 x P(cover) + spread x P(win) (Lucas 9/19, once the rulebook settled;
    P(cover) = the margin curve at the dog's model margin plus the points),
    with the home-dog tiebreak. Played games (before the lines_as_of date)
    are excluded."""
    import datetime as dt
    if not CARD:
        return [], []
    curve = _cover_curve()
    asof = dt.datetime.fromisoformat(LINES_TS.replace("Z", "+00:00")).date()
    fbs = set()
    try:
        import json as _j
        for _g in _j.load(open(os.path.join(HERE, "fpi-decomposition", "data",
                                            "games_seasonType-regular_year-2026.json"), encoding="utf-8")):
            if _g.get("homeClassification") == "fbs" and _g.get("awayClassification") == "fbs":
                fbs.add(_g["id"])
    except FileNotFoundError:
        pass
    rows = []
    for g in CARD.values():
        if fbs and g.get("game_id") not in fbs:
            continue  # superdogs are FBS-vs-FBS only (Lucas 9/13)
        try:
            _, mon, day = g["date"].split(",")[0].split()
            gdate = dt.date(2026, _MONTHS[mon], int(day))
        except (KeyError, ValueError):
            continue
        if gdate < asof:
            continue
        b = g["books"].get("DraftKings") or g["books"].get("Bovada") or {}
        sp = b.get("spread")
        if sp is None or not SUPERDOG_MIN_SPREAD <= abs(sp) <= SUPERDOG_MAX_SPREAD:
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
        mm = g.get("model_margin")
        if mm is None:
            continue
        edge = abs(sp) + (-mm if dog == g["away"] else mm)   # dog's model margin + the points
        if edge >= SUPERDOG_MAX_EDGE:
            continue
        rows.append(dict(dog=dog, fav=fav, at=at, pts=abs(sp), p=p, mkt=mkt,
                         ml=ml, ev=p * abs(sp), edge=edge,
                         p_cover=float(curve.win_prob(edge)), rank=ap_rank(fav),
                         dog_rank=ap_rank(dog)))
    for r in rows:   # expected rulebook points: a cover pays 5, a win pays 5 + the spread
        r["exp_pts"] = SUPERDOG_COVER_PTS * r["p_cover"] + r["pts"] * r["p"]
    rows.sort(key=lambda r: -r["exp_pts"])
    giant = [r for r in rows if r["rank"] and not r["dog_rank"]]   # unranked dog vs Top 25
    return home_dog_tiebreak(rows), home_dog_tiebreak(giant)


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


def _luck():
    """{team: (luck per rated game, n)} = actual minus deserved margin,
    season to date, rated games (both teams in the prior) with box scores."""
    try:
        from inseason_ratings import deserved_margins
        dm = deserved_margins()
    except Exception as e:  # pragma: no cover
        print("luck column unavailable:", e)
        return {}
    rated = {t["team"] for t in _r["teams"]}
    acc = {}
    for gid, (ap_, hp_) in _finals_by_id().items():
        d = dm.get(gid)
        if not d or d["home"] not in rated or d["away"] not in rated:
            continue
        diff = (hp_ - ap_) - d["deserved"]
        for team, sgn in ((d["home"], 1), (d["away"], -1)):
            tot, n = acc.get(team, (0.0, 0))
            acc[team] = (tot + sgn * diff, n + 1)
    return {t: (tot / n, n) for t, (tot, n) in acc.items() if n}


def _finals_by_id():
    p = os.path.join(HERE, "fpi-decomposition", "data",
                     "games_seasonType-regular_year-2026.json")
    out = {}
    if os.path.exists(p):
        for g in _json.load(open(p, encoding="utf-8")):
            if g.get("homePoints") is not None and g.get("awayPoints") is not None:
                out[g["id"]] = (g["awayPoints"], g["homePoints"])
    return out


LUCK = _luck()   # internal only (Lucas 9/14): the luck column lives in the notes, not on the slide

s = blank(NAVY)
PALE = RGBColor(0xCA, 0xDC, 0xFC)
UP, DOWN = RGBColor(0x5C, 0xD6, 0x8A), RGBColor(0xFF, 0x7A, 0x7A)
txt(s, 0.9, 0.42, 11.5, 0.4,
    f"EPISODE {EPISODE} · WEEK {WEEK} · THE MACHINE'S TOP 25", 14, ORANGE,
    bold=True)
txt(s, 0.9, 0.76, 11.5, 0.8, "Our Top 25", 40, WHITE, bold=True)
txt(s, 0.9, 1.5, 11.5, 0.3,
    f"Machine rating · Δ vs preseason · AP week {AP_WEEK} poll", 13, PALE,
    bold=True)
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
_line1 = "Biggest splits: " + " · ".join(
    f"{n} #{i} vs AP #{a}" for _, _, i, a, n in _gaps[:3])
_line2 = ("Ours, not theirs: " + ", ".join(_ours_only[:4]) +
          "   ·   Theirs, not ours: " + ", ".join(n for _, n in _theirs_only[:4]))
_fy = TOP + 13 * RH + 0.08
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, _fy, 11.55, 0.62, NAVY2)
txt(s, 1.1, _fy + 0.05, 11.2, 0.28, _line1, 11, WHITE, bold=True)
txt(s, 1.1, _fy + 0.32, 11.2, 0.28, _line2, 10.5, PALE)

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
        "60% CBS rating + 40% machine odds of missing the bar", 13, PALE, bold=True)
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
        "Next three: " + " · ".join(f"{x['coach']} {x['score']:.0f}" for x in _nxt),
        11, WHITE, bold=True)
    txt(s, 1.1, _fy + 0.32, 11.2, 0.28,
        "NEEDS = wins that keep the job · P(GETS IT) = the machine's odds · "
        "MACHINE WINS = projected (10th–90th)", 10.5, PALE)

    # -- Heisman --
    s = blank(NAVY)
    txt(s, 0.9, 0.42, 11.5, 0.4,
        f"EPISODE {EPISODE} · WEEK {WEEK} · OUR HEISMAN BOARD", 14, ORANGE, bold=True)
    txt(s, 0.9, 0.76, 11.5, 0.8, "Our Heisman Favorite", 40, WHITE, bold=True)
    txt(s, 0.9, 1.5, 11.5, 0.3,
        "Team factor × QB efficiency (PPA per play) · market = DraftKings", 13, PALE,
        bold=True)
    # Row subtitles = box-score lines (Lucas 9/15: stats, not model terms).
    # Season totals from the CFBD player box scores through Week 2.
    HEISMAN_WHY = {
        "Darian Mensah": "41-of-45, 653 yards, 8 TD, 0 INT through two",
        "Josh Hoover": "19-of-27, 376 yards, 8 TD, 0 INT through two",
        "C.J. Carr": "35-of-49, 492 yards, 6 TD, 0 INT · 253 and 4 TD vs Rice",
        "Julian Sayin": "38-of-57, 598 yards, 4 TD, 1 INT · 278 in the loss at Texas",
        "Jayden Maiava": "67-of-83, 896 yards, 10 TD, 1 INT through three",
        "Arch Manning": "43-of-64, 500 yards, 5 TD, 2 INT · 195 and a pick vs Ohio State",
        "Will Hammond": "46-of-60, 487 yards, 2 TD, 1 INT through two",
        "Devon Dampier": "31-of-42, 437 yards, 5 TD · 81 rushing, 2 TD",
        "Kevin Jennings": "40-of-52, 767 yards, 8 TD, 2 INT through two",
        "Lincoln Kienholz": "34-of-50, 639 yards, 4 TD, 0 INT · 111 rushing, 3 TD",
        "Kamario Taylor": "38-of-56, 581 yards, 7 TD, 0 INT · 145 rushing",
        "Sam Leavitt": "41-of-66, 574 yards, 2 TD, 4 INT · 135 rushing, 5 TD",
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
        txt(s, 1.75, y + 0.31, 10.6, 0.3, why, 11.5, PALE)
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
        f"{fav['name']}, {fav['team']} · index {fav['index']:.1f} · market "
        f"+{fav['market']}", 18, WHITE, bold=True)
    _non = BOARDS["heisman_non_qb"]
    txt(s, 0.9, _fy + 0.85, 11.5, 0.3,
        "Non-QB watch: " +
        " · ".join(f"{x['name']}" + (f" (+{x['market']})" if x.get("market") else "")
                   for x in _non[:4]), 11, PALE)
    txt(s, 0.9, 7.13, 11.5, 0.3,
        "PPA = predicted points added per play · re-computes every rebuild", 10, PALE,
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
    f"Machine = our in-season rating + 2.5 home field · lines as of {LINES_AS_OF}",
    11.5, RGBColor(0xCA, 0xDC, 0xFC))

# ---- slide text: the headline only (Lucas 9/11). Keyed by game title. ----
SHORT = {
    "Texas at Tennessee": dict(
        sub="Sat Sep 26 · 12:00 ET · Knoxville · No. 1 at No. 14",
        ctx_a=dict(coach="Sarkisian, year 6", qb="Arch, final season", roster="72% back · 22 portal adds"),
        ctx_b=dict(coach="Heupel, year 6 · new DC Knowles", qb="NEW — Faizon Brandon, true freshman", roster="35% back · 21 portal adds"),
        decides=["No. 1 leaves Austin for the first time", "A true freshman vs No. 1", "Heupel's marquee home game", "Knowles' first real quarterback"],
        honesty="3.5 to Texas — quibble, not a position",
        keys_a=["Arch has to hit downfield", "Stay out of third-and-long", "Stop the run", "Simmons vs the freshman"],
        keys_b=["Run it at Texas", "Brandon's first ranked opponent", "Knowles' rush on passing downs", "Win the red zone"]),
    "Ole Miss at Florida": dict(
        sub="Sat Sep 26 · 3:30 ET · Gainesville · No. 4 at No. 21",
        ctx_a=dict(coach="NEW — Golding, promoted", qb="Chambliss returns", roster="50% back · 28 portal adds"),
        ctx_b=dict(coach="NEW — Sumrall (Tulane)", qb="NEW — Aaron Philo, RS freshman", roster="69% back · 27 portal adds"),
        decides=["Two first-year coaches, both 3–0", "No. 4 vs No. 21 — a point apart to the machine", "Home team has won two straight", "Philo's first ranked opponent"],
        honesty="Machine = market — no play",
        keys_a=["Chambliss vs the Florida rush", "Stop the explosives", "Get Lacy going", "Finish drives"],
        keys_b=["Feed Baugh", "Philo deep", "Get Chambliss off schedule", "Tighten the red zone"]),
    "Oregon at USC": dict(
        sub="Sat Sep 26 · 7:30 ET · Los Angeles · No. 20 at No. 12",
        ctx_a=dict(coach="Lanning, year 5 · both coordinators new", qb="Dante Moore returns", roster="75% back · 13 portal adds"),
        ctx_b=dict(coach="Riley, year 5 · new DC Gary Patterson", qb="Maiava returns", roster="59% back · 9 portal adds"),
        decides=["Oregon's season on the line in Week 4", "Riley's year five", "Oregon has won two straight in the series", "Two offenses ahead of two defenses"],
        honesty="Pick'em — no position",
        keys_a=["Protect Moore", "Stay out of third-and-long", "Attack Patterson's secondary", "Stop the run this time"],
        keys_b=["Keep Maiava clean", "Own third down", "Finish in the red zone", "Stop the explosives"]),
    "Texas A&M at LSU": dict(
        sub="Sat Sep 26 · 7:30 ET · Baton Rouge · No. 23 at No. 10",
        ctx_a=dict(coach="Elko, year 3", qb="Reed returns", roster="73% back · 19 portal adds"),
        ctx_b=dict(coach="NEW — Kiffin", qb="NEW — Sam Leavitt", roster="21% back · 44 portal adds"),
        decides=["The loser has two losses in September", "First of five A&M cannot give away", "Leavitt's five picks", "A&M won 49–25 here last year"],
        honesty="3 to A&M — the market ran past us · no position",
        keys_a=["Find an explosive play", "Block Umanmielen", "Fix the back end", "Don't count on the run"],
        keys_b=["Leavitt's ball security", "Throw deep", "Umanmielen on passing downs", "Touchdowns, not field goals"]),
    "Oklahoma at Georgia": dict(
        sub="Sat Sep 26 · 3:30 ET · Athens · unranked at No. 2",
        ctx_a=dict(coach="Venables, year 5", qb="Mateer returns, senior", roster="63% back · 16 portal adds"),
        ctx_b=dict(coach="Smart, year 11", qb="Stockton returns", roster="69% back · 9 portal adds"),
        decides=["24 points in Oklahoma's last two games", "Georgia's old flaw looks fixed", "The best defense Georgia has seen", "A first-round bye game"],
        honesty="Machine = market — no play",
        keys_a=["The pass rush is the path", "Mateer has to be the run game", "Reach the red zone", "Force a turnover"],
        keys_b=["Frazier downhill", "Get the ball out", "Make Mateer one-dimensional", "Keep hitting explosives"]),
    "Houston at Texas Tech": dict(
        sub="Fri Sep 18 · 8:00 ET · Lubbock",
        ctx_a=dict(coach="Fritz, year 3 · the year-three pattern", qb="Weigman returns", roster="81% back · 18 portal adds"),
        ctx_b=dict(coach="McGuire, year 5", qb="Hammond, back from the ACL", roster="53% back · portal-built defense"),
        decides=["The Big 12's first litmus test", "Fritz's year three", "Hammond after the scare in Corvallis", "Four straight for Tech in the series"],
        honesty="5.5 to Tech — a small lean",
        keys_a=["Weigman's legs vs the rebuilt front", "Run it 45 times", "Make Hammond throw", "Win the trenches"],
        keys_b=["Hammond's second real start", "J'Koby Williams downhill", "The portal defense vs a real offense", "Finish drives"]),
    "SMU at Louisville": dict(
        sub="Sat Sep 19 · 3:30 ET · Louisville",
        ctx_a=dict(coach="Lashlee, year 5 · coordinator troikas", qb="Jennings, year-three starter", roster="57% back · 15 portal adds"),
        ctx_b=dict(coach="Brohm, year 4", qb="Kienholz, third QB1 in three years", roster="35% back · 33 portal adds"),
        decides=["The ACC's biggest non-Miami game", "Jennings, year three", "Brohm's coin-flip problem", "Both offenses score fast"],
        honesty="Machine = market · Monster Under 59.5",
        keys_a=["Jennings vs the bust-prone back end", "Protect Jennings", "Win the takeaway ledger", "Explosives, not long drives"],
        keys_b=["Ride the Browns", "No coverage busts", "Kienholz keeps it clean", "Win the one-score game"]),
    "Mississippi State at South Carolina": dict(
        sub="Sat Sep 19 · 4:15 ET · Columbia",
        ctx_a=dict(coach="Lebby, year 3 · Arnett DC", qb="Kamario Taylor, sophomore", roster="34% back · 28 portal adds"),
        ctx_b=dict(coach="Beamer, year 6 · new OC Briles", qb="Sellers returns", roster="69% back · 26 portal adds"),
        decides=["Two hot seats, one game", "Kamario Taylor's breakout", "Sellers hasn't thrown yet", "Arnett's defense, back in Starkville"],
        honesty="0.9 to South Carolina — no play",
        keys_a=["Taylor's legs and arm", "Bothwell downhill", "Arnett's defense vs Sellers", "Win the turnover ledger"],
        keys_b=["Let Sellers throw", "Protect Sellers", "Harbor deep", "Stewart off the edge"]),
    "Florida at Auburn": dict(
        sub="Sat Sep 19 · 7:00 ET · Auburn",
        ctx_a=dict(coach="NEW — Sumrall (Tulane)", qb="NEW — Aaron Philo, RS freshman", roster="69% back · 27 portal adds"),
        ctx_b=dict(coach="NEW — Golesh · Durkin kept", qb="NEW — Byrum Brown (USF)", roster="14% back · 39 portal adds"),
        decides=["Two first-year coaches", "Auburn's rebuilt lines vs Florida's front", "Byrum Brown vs Aaron Philo", "Jordan-Hare at night"],
        honesty="Lean Auburn +2.5 — research, not a position",
        keys_a=["Philo's first road start", "Baugh downhill", "White's front vs Brown's legs", "Fourth-down conviction"],
        keys_b=["Brown's legs", "Ball security", "Durkin's defense at home", "Tempo without turnovers"]),
    "LSU at Ole Miss": dict(
        sub="Sat Sep 19 · 7:30 ET · Oxford",
        ctx_a=dict(coach="NEW — Kiffin", qb="NEW — Sam Leavitt", roster="21% back · 44 portal adds"),
        ctx_b=dict(coach="NEW — Golding, promoted", qb="Chambliss returns", roster="50% back · 28 portal adds"),
        decides=["Kiffin returns to Oxford", "Home team five straight", "Leavitt's three picks", "55–49 or 24–19"],
        honesty="2.2 to LSU — quibble · Monster Under 59.5",
        keys_a=["Leavitt's ball security", "Protect Leavitt", "Baker's front vs Chambliss", "Kiffin's tempo in his old house"],
        keys_b=["Let Chambliss escape", "Lacy runs it", "The patched secondary", "Special teams edge"]),
    "Ohio State at Texas": dict(
        sub="Sat Sep 12 · 7:30 ET · Austin · No. 1 at No. 4",
        ctx_a=dict(coach="Day, year 8 · new OC Arthur Smith", qb="Sayin returns, year two", roster="68% back · 2 of 9 D starters"),
        ctx_b=dict(coach="Sarkisian, year 6 · new DC Muschamp", qb="Arch returns, final season", roster="72% back · 22 portal adds"),
        decides=["The rematch", "One coordinator gamble each",
                 "Texas has the continuity edge", "Week 1 proved nothing yet"],
        honesty="Pick'em plus home field — no position",
        keys_a=["Make the run game real", "Sayin-to-Smith vs the back end",
                "Prove the eight-transfer defense", "Play with pace, cut the flags"],
        keys_b=["Arch on the move", "Protect the interior",
                "Explosives over efficiency", "Muschamp's first real test"]),
    "Oklahoma at Michigan": dict(
        sub="Sat Sep 12 · 12:00 ET · Ann Arbor",
        ctx_a=dict(coach="Venables, year 5", qb="Mateer returns, senior", roster="63% back · 16 portal adds"),
        ctx_b=dict(coach="NEW — Whittingham (Utah)", qb="Underwood, year two", roster="69% back · the Utah pipeline"),
        decides=["An eight-point line swing", "Whittingham's first Big House test",
                 "Underwood vs Mateer", "Payback for 24–13"],
        honesty="Lean Michigan +5.5 — research, not a position",
        keys_a=["Mateer's legs vs Hill's pressure", "The portal line has to prove it",
                "Erase Underwood's bad day", "Win the hidden yards"],
        keys_b=["Own the ball", "Run Underwood like Dampier",
                "Find receiver No. 2", "Pressure without the busts"]),
    "Arizona State at Texas A&M": dict(
        sub="Sat Sep 12 · 12:00 ET · College Station",
        ctx_a=dict(coach="Dillingham, year 4", qb="NEW — Cutter Boley", roster="16% back · 24 portal adds"),
        ctx_b=dict(coach="Elko, year 3 · two new coordinators", qb="Reed returns", roster="73% back · both lines rebuilt"),
        decides=["Dillingham's reboot vs an 11-win roster", "Boley's second start",
                 "A&M's portal-built lines", "No 2026 snaps in the number"],
        honesty="Agreement — no play",
        keys_a=["Tempo the transfer front", "Boley vs real disguise",
                "Contain before you gamble", "Fix special teams"],
        keys_b=["Reed's ball security", "Prove the portal line",
                "Havoc from the new front", "Finish drives, cut the flags"]),
    "Arizona at BYU": dict(
        sub="Sat Sep 12 · 3:30 ET · Provo · Big 12 opener",
        ctx_a=dict(coach="Brennan, year 3", qb="Fifita returns, year four", roster="65% back · 22 portal adds"),
        ctx_b=dict(coach="Sitake, year 11 · new DC Poppinga", qb="Bachmeier, year two", roster="79% back · most on the card"),
        decides=["The Big 12's continuity kings", "Provo's biggest game until Notre Dame",
                 "Poppinga replaces Hill", "BYU took four, Arizona gave three"],
        honesty="Machine = market — no play",
        keys_a=["Attack Poppinga early", "Hold the line vs Martin",
                "Ball security", "Win field position"],
        keys_b=["Run first, then punish", "Martin and Eka behind the veterans",
                "Prove the new receivers", "Win the hidden margin"]),
    "Alabama at Kentucky": dict(
        sub="Sat Sep 12 · 3:30 ET · Lexington · SEC opener",
        ctx_a=dict(coach="DeBoer, year 3 · the referendum", qb="NEW — Keelon Russell, RS freshman", roster="26% back · 17 portal adds"),
        ctx_b=dict(coach="NEW — Will Stein (Oregon OC)", qb="NEW — Kenny Minchey", roster="19% back · 31 portal adds"),
        decides=["DeBoer's referendum, on the road", "Stein's anti-Stoops",
                 "Lowest continuity on the card", "The early landmine"],
        honesty="Quibble, not a position",
        keys_a=["Russell's first road start", "Run it 49 times again",
                "Wommack's secondary vs the void", "Special teams can't leak"],
        keys_b=["The mauling line", "Minchey keeps it clean",
                "The defense is the strength", "Fix third down and the flags"]),
}


# Corey's feedback (9/15): one WHY IT MATTERS point and three keys per slide;
# the notes keep all four of each (the fourth is the reserve). Applies to the
# headline (SHORT) form only.
SLIDE_POINTS = 1
SLIDE_KEYS = 3


def slide_text(g):
    """(decides, honesty, keys_a, keys_b, is_short) — SHORT if authored,
    else the long GAMES strings."""
    sh = SHORT.get(g["title"], {})
    if sh:
        return (sh.get("decides", g["decides"])[:SLIDE_POINTS], sh.get("honesty", g["honesty"]),
                sh.get("keys_a", g["keys_a"])[:SLIDE_KEYS], sh.get("keys_b", g["keys_b"])[:SLIDE_KEYS], True)
    return (g["decides"], g["honesty"], g["keys_a"], g["keys_b"], False)


def one_fact(val, short):
    """COACH / QB / ROSTER cell: the first fact only in headline form."""
    return val.split(" · ")[0].strip() if short else val


# ---------------- week 0 receipts ----------------
s = blank()
txt(s, 0.9, 0.5, 11.5, 0.55, f"Week {WEEK - 1} — the receipts", 30, NAVY, bold=True)
txt(s, 0.9, 1.08, 11.5, 0.3,
    ("Calls frozen at recording · closing line = last pre-kick pull · " if RECEIPTS_SHOW_MARKET
     else "Calls frozen at recording · ")
    + "off by = miss vs the final margin · deserved = the efficiency margin", 12, MUTE, bold=True)
# codes, not names, on the calls line: three score lines have to fit one row
y = 1.55
VERD = {"M": ORANGE, "K": RGBColor(0xB5, 0x12, 0x1B), "C": RGBColor(0x1F, 0x7A, 0x4D), "T": MUTE, "P": MUTE}
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
if _rs["man"] and not RECEIPTS_SHOW_MARKET:
    _l1 = (f"Margin miss: man {_rs['c']:.1f} · machine {_rs['m']:.1f}"
           f" — closer: man {_rs['nc']}, machine {_rs['nm']}, {_rs['nt']} tie")
    _l2 = (f"Points off the final score: man {_rs['sc']:g} · machine {_rs['sm']:g}"
           f"   |   Machine's season: {_run_m:.1f} off across {PRIOR_GAMES + _rs['n']} games"
           + (f" · vs the deserved margins this week: {_rs['d']:.1f}" if _rs.get("d") else ""))
elif _rs["man"]:
    _l1 = (f"Margin miss: market {_rs['k']:.1f} · man {_rs['c']:.1f} · machine {_rs['m']:.1f}"
           f" — closest: market {_rs['nk']}, man {_rs['nc']}, machine {_rs['nm']}, {_rs['nt']} tie")
    _l2 = (f"Points off the final score: man {_rs['sc']:g} · machine {_rs['sm']:g}"
           + (f" · market-implied {_rs['sk']:g}" if _rs["sk"] else "")
           + f"   |   Season margin: machine {_run_m:.1f} vs market {_run_k:.1f}, "
             f"{PRIOR_GAMES + _rs['n']} games · {LEANS_LINE.split(' · ')[0]}")   # one line: the lean detail lives in the notes
elif not RECEIPTS_SHOW_MARKET:
    _l1 = f"Machine off by {_rs['m']:.1f} across {_rs['n']} games" + (f" · vs the deserved margins: {_rs['d']:.1f}" if _rs.get("d") else "")
    _l2 = f"Machine's season: {_run_m:.1f} off across {PRIOR_GAMES + _rs['n']} games"
else:
    _l1 = (f"Machine {_rs['m']:.1f} · market {_rs['k']:.1f} · machine closer in "
           f"{_rs['nm']}, market {_rs['nk']}, {_rs['nt']} tie"
           + (f" · vs the deserved margins: machine {_rs['d']:.1f}" if _rs.get("d") else ""))
    _l2 = (f"Season: machine {_run_m:.1f} vs market {_run_k:.1f} across "
           f"{PRIOR_GAMES + _rs['n']} games · {LEANS_LINE}")
txt(s, 1.15, y + 0.13, 11.0, 0.35, _l1, 14.5, WHITE, bold=True)
txt(s, 1.15, y + 0.5, 11.0, 0.3, _l2, 10.5, RGBColor(0xCA, 0xDC, 0xFC))

# ---------------- per-game slides ----------------
for g in GAMES:
    # -- numbers slide --
    s = blank()
    logo_badge(s, 0.9, 0.42, 0.8, g["a"])
    txt(s, 1.82, 0.52, 0.5, 0.5, g["vs"], 14, MUTE, align=PP_ALIGN.CENTER)
    logo_badge(s, 2.35, 0.42, 0.8, g["b"])
    txt(s, 3.45, 0.38, 8.9, 0.55, g["title"], 27, NAVY, bold=True)
    _dec, _hon, _ka, _kb, _short = slide_text(g)
    _sub = SHORT.get(g["title"], {}).get("sub", g["sub"])
    txt(s, 3.45, 0.94, 8.9, 0.35, _sub, 14 if _short else 11, MUTE,
        italic=not _short, bold=_short)

    # left: what decides it (headline form when SHORT is authored)
    txt(s, 0.9, 1.75, 7.2, 0.4, "WHY IT MATTERS", 13, NAVY, bold=True)
    yy = 2.25
    for d in _dec:
        shape(s, MSO_SHAPE.OVAL, 0.95, yy + 0.09 + (0.1 if _short else 0), 0.14, 0.14, ORANGE)
        txt(s, 1.3, yy, 6.8, 0.9, d, (24 if len(_dec) == 1 else 21) if _short else 13.5, INK, bold=_short)
        yy += 0.78
    # one point leaves room: drop the honesty box to the bottom of the bug's height
    box_y = max(yy + 0.15, 5.2) if _short else yy + 0.15
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, box_y, 7.2, 1.05, ICE)
    if _short:
        txt(s, 1.15, box_y + 0.25, 6.7, 0.55, _hon, 20, NAVY, bold=True)
    else:
        txt(s, 1.15, box_y + 0.17, 6.7, 0.75, _hon, 11.5, MUTE, italic=True)

    # right: navy score bug
    PALE = RGBColor(0xCA, 0xDC, 0xFC)
    shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 8.5, 1.75, 3.9, 4.6, NAVY)
    txt(s, 8.8, 1.98, 3.3, 0.3, "THE NUMBER", 12, ORANGE, bold=True)
    # machine line as a book would post it + fair odds from our win prob
    txt(s, 8.8, 2.3, 3.3, 0.55, g["machine"], 28 if len(g["machine"]) <= 16 else 21, WHITE, bold=True)
    txt(s, 8.8, 2.84, 3.3, 0.3, g.get("fair", ""), 12 if len(g.get("fair", "")) <= 34 else 9.5, WHITE, bold=True)
    txt(s, 8.8, 3.12, 3.3, 0.28,
        "machine line · fair odds, no vig · raw margin " + g.get("raw_margin", ""),
        8.5, PALE)
    # market
    txt(s, 8.8, 3.55, 3.3, 0.45, g["market"], 20, WHITE, bold=True)
    txt(s, 8.8, 3.98, 3.3, 0.4, "market (DK / Bovada) · " + (g.get("market_ml") or "ML not posted"),
        8.5, PALE)
    # score prediction (replaced "the gap" per Lucas's in-Slides edit 8/31;
    # the authored value/gap strings stay in GAMES as data)
    score = g.get("score", "")
    txt(s, 8.8, 4.45, 3.3, 0.4, score, 15 if len(score) <= 22 else (13 if len(score) <= 30 else 10.5),
        ORANGE if "not posted" not in score else PALE, bold=True)
    txt(s, 8.8, 4.82, 3.3, 0.25, "score prediction", 8.5, PALE)
    wa, pa, wb, pb = g["wp"]
    wp_bar(s, 8.8, 5.2, 3.3, 0.4, wa, pa, TEAMS[wa]["color"],
           wb, pb, TEAMS[wb]["color"])
    txt(s, 8.8, 5.66, 3.3, 0.25, "win probability (machine)", 8.5, PALE)
    # Line movement (g["move"], LEDGER[title]) is INTERNAL (Lucas 9/15): it stays
    # in the ledger and the notes, not on the slide.

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
            txt(s, x, 2.34, 3.55, 0.6, one_fact(val, _short), 15 if _short else 10.5, INK,
                bold=_short)
        yy = 3.5
        step = 1.1 if (_short and len(keys) <= 3) else 0.92
        for k in keys:
            shape(s, MSO_SHAPE.OVAL, 1.0, yy + (0.2 if _short else 0.12), 0.15, 0.15, ORANGE)
            txt(s, 1.45, yy, 10.5, 0.8, k, 24 if _short else 15.5, INK,
                bold=_short)
            yy += step
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
    txt(s, 2.5, y + 0.17, 5.4, 0.4, g["title"], 16, WHITE, bold=True)
    txt(s, 7.0, y + 0.06, 5.2, 0.45, g.get("score", ""), 19, ORANGE,
        bold=True, align=PP_ALIGN.RIGHT)
    txt(s, 7.0, y + 0.47, 5.2, 0.25, "market " + g["market"].split(" / ")[0], 9.5,
        RGBColor(0xCA, 0xDC, 0xFC), align=PP_ALIGN.RIGHT)
    y += 0.8
# superdog band
shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, 0.9, y + 0.08, 11.5, 1.02, ORANGE)
for i, (label, board) in enumerate(
        [("SUPERDOG", [r for r in SUPERDOG_ANY   # any matchup, but not the Giant Killer pick again
                       if not (SUPERDOG_T25 and r is SUPERDOG_T25[0])]),
         ("GIANT KILLER", SUPERDOG_T25)]):
    if not board:
        continue
    r = board[0]
    fav = (f"#{r['rank']} " if r["rank"] else "") + r["fav"]
    ml = f" · ML {int(r['ml']):+d}" if r.get("ml") is not None else ""
    txt(s, 1.2, y + 0.15 + i * 0.44, 3.0, 0.38, "★ " + label, 14, NAVY,
        bold=True)
    txt(s, 3.6, y + 0.15 + i * 0.44, 8.6, 0.38,
        f"{r['dog']} +{r['pts']:g} {r['at']} {fav}{ml}", 16, WHITE,
        bold=True)
txt(s, 0.9, 7.15, 11.5, 0.3,
    "Superdogs: 5 for a cover · 5 + the spread for a win · 1 for a push · research, not picks", 11,
    RGBColor(0xCA, 0xDC, 0xFC), italic=True)

out = os.path.join(HERE, "decks", f"2026_Week{WEEK}_Episode{EPISODE}.pptx")
prs.save(out)
print("wrote", out, f"- {len(prs.slides)} slides")
