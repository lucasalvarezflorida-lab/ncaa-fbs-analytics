"""Weekly edge board, two views.

VIEW: contest (default) — spread picks + totals for a spreads/O-U points
contest (e.g. favordog). P(cover) = the fitted margin curve evaluated at the
point edge (model margin minus market margin), sorted by cover prob; totals
via the U-TAIL rule. --payout sets what a winning pick pays (even money vs
-110), which moves break-even (50% vs 52.38%).

    python edge_report.py --week 1 --bank 1500
    python edge_report.py --week 1 --payout 110 --csv wk1.csv

VIEW: ml — model win probability vs no-vig moneyline market, the
model-vs-market research table (podcast work). Stated from the model's side;
EDGE is model minus no-vig market in percentage points.

    python edge_report.py --week 1 --view ml --devig shin

Both views: cached CFBD data unless --refresh (needs CFBD_API_KEY);
margin_prob_curve.json required (run fit_margin_curve.py once); --kelly /
--bank size stakes (bank is never assumed — pass it explicitly).

PUBLISH (review item A): `--publish` implies --refresh, appends the pull to
lines_history.jsonl (line_ledger), and writes card_data_week{N}.json — the
contract the episode deck reads (model margin/win prob, per-book lines,
ML-implied market prob, first-seen -> current spread, CLV, flags). The ML
view's FIRST>NOW and CLV columns come from the same ledger. `--week auto`
picks the first week with an unplayed game.

    python edge_report.py --week auto --view ml --publish

Flags: EDGE_GONE (a >=3-pt first-seen edge decayed below 1.5), EDGE_FLIP,
CLV+x / CLV-x (line moved >=2 toward / against the model side), STRUCT
(model and no-vig moneyline win probs differ by >=15pp — the market disagrees
about the matchup, not the number; narrative treatment differs from a
spread-gap play).

Notes. Spread pushes: integer lines carry push mass the continuous curve
splits between the sides — treat cover probs within ~1pp of break-even as no
edge, especially at 3 and 7. Totals: no totals model exists; U-TAIL is the
lone FDR survivor of the market post-mortem (unders 55.1% on top-decile
totals, 2021-25 pooled — a base rate, not a per-game estimate; the Kelly
number is a ceiling). ML view: Bovada ships -100000 placeholder MLs on huge
favorites; pairs booking >15% overround fall back to spread-derived market
prob (marked *).
"""

from __future__ import annotations

import argparse
import csv
import datetime
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))

import line_ledger  # noqa: E402
from build_conference_book import (_spread_text, fetch_games,  # noqa: E402
                                   load_fpi_2026)
from margin_prob import load_curve  # noqa: E402
from odds import kelly, novig, overround, prob_to_american  # noqa: E402

# model vs no-vig market win-prob gap that counts as a structural
# disagreement (unsigned; only when a real moneyline exists)
STRUCT_PP = 15.0

# unders on top-decile totals, 2021-25 pooled (the lone FDR survivor);
# a base rate, not a per-game estimate
U_TAIL_P = 0.551

# a real two-way ML market books 2-8% of vig; Bovada ships -100000
# placeholder MLs on huge favorites, which would devig to ~50/50 and top the
# table with phantom edges — treat those pairs as no ML at all
MAX_OVERROUND = 0.15

CONTEST_COLUMNS = ["market", "game", "mkt_line", "model_line", "pick", "p",
                   "kelly_frac", "stake_pts", "flags"]
ML_COLUMNS = ["game", "mkt_spread", "model_spread", "side", "side_ml",
              "model_p", "mkt_p", "mkt_src", "fair_ml", "edge_pp",
              "first_spread", "now_spread", "clv", "kelly_frac", "stake_pts",
              "flags"]


def _signed(x: float) -> str:
    return f"{x:+g}"


def _load_inputs(refresh: bool):
    fpi = {k: {"fpi": v} for k, v in load_fpi_2026().items()}
    if not fpi:
        sys.exit("no 2026 preseason FPI snapshot found — run refresh_all.py first")
    return fetch_games(refresh, fpi), load_curve("model")


def resolve_week(week: str, games: list[dict]) -> int:
    """'auto' -> the first week that still has an unplayed game with a line."""
    if week != "auto":
        return int(week)
    open_weeks = sorted({g["wk"] for g in games
                         if not g["completed"] and g["spread"] is not None})
    if not open_weeks:
        sys.exit("--week auto: no unplayed games with lines found")
    return open_weeks[0]


def _same_book_mls(g: dict):
    """Prefer the moneyline pair from the book that supplied the spread, so a
    DraftKings spread is not devigged against a Bovada price (provenance)."""
    books = g.get("books") or {}
    b = books.get(g.get("spread_book"))
    if b and b.get("home_ml") is not None and b.get("away_ml") is not None:
        return b["home_ml"], b["away_ml"], g["spread_book"]
    return g["home_ml"], g["away_ml"], g.get("ml_book")


# ---------------- contest view: spreads + totals ----------------

def build_contest_rows(week: int, refresh: bool, payout_ml: int,
                       kelly_frac: float, bank: float | None):
    games, curve = _load_inputs(refresh)
    spreads, totals = [], []
    no_line = no_model = 0
    for g in games:
        if g["wk"] != week:
            continue

        if g["ou_tail"]:
            kf = kelly(U_TAIL_P, payout_ml, kelly_frac)
            totals.append(dict(
                market="total",
                game=f"{g['away']} @ {g['home']}" + (" (N)" if g["neutral"] else ""),
                mkt_line=f"O/U {g['ou']:g}", model_line="",
                pick=f"UNDER {g['ou']:g}", p=U_TAIL_P, kelly_frac=kf,
                stake_pts=round(bank * kf) if bank else None,
                flags="U-TAIL"))

        if g["model_margin"] is None:
            no_model += 1
            continue
        if g["spread"] is None or g["edge"] is None:
            no_line += 1
            continue
        side = g["model_side"]
        side_line = float(g["spread"]) if side == g["home"] else -float(g["spread"])
        p_cover = curve.win_prob(abs(g["edge"]))
        kf = kelly(p_cover, payout_ml, kelly_frac)
        flags = [g["tier"]] if g["tier"] else []
        if float(g["spread"]) == int(float(g["spread"])):
            flags.append("INT")  # integer line: push possible, prob approximate
        if g["completed"]:
            flags.append(f"FINAL {g['home_pts']}-{g['away_pts']}")
        spreads.append(dict(
            market="spread",
            game=f"{g['away']} @ {g['home']}" + (" (N)" if g["neutral"] else ""),
            mkt_line=g["spread_text"]
                     or _spread_text(g["home"], g["away"], g["spread"]),
            model_line=_spread_text(g["home"], g["away"],
                                    round(-g["model_margin"], 1)),
            pick=f"{side} {_signed(side_line)}",
            p=p_cover, kelly_frac=kf,
            stake_pts=round(bank * kf) if bank else None,
            flags=" ".join(flags)))

    spreads.sort(key=lambda r: -r["p"])
    totals.sort(key=lambda r: -float(r["mkt_line"].split()[-1]))
    return spreads, totals, no_line, no_model, curve


def print_contest(spreads, totals, week, payout_ml, kelly_frac, bank,
                  no_line, no_model, curve) -> None:
    meta = curve.meta
    payout_s = "even money" if payout_ml == 100 else str(payout_ml)
    be = 0.5 if payout_ml == 100 else 110 / 210
    print(f"WEEK {week} CONTEST BOARD — spread picks + U-TAIL totals")
    print(f"cover probs: margin curve n={meta.get('n')} (resid sd "
          f"{meta.get('resid_sd')}) at the point edge · payout ASSUMED "
          f"{payout_s} (break-even {be:.1%}) — CONFIRM IN THE PICK UI · "
          f"kelly={kelly_frac:g}x" + (f" · bank={bank:g}" if bank else ""))

    stake_h = f" {'STAKE':>6}" if bank else ""
    print("\n=== SPREAD PICKS ===")
    print(f"{'GAME':41} {'MKT LINE':>25} {'MODEL LINE':>25} "
          f"{'PICK':>26} {'P(COVER)':>9} {'KELLY':>6}{stake_h}  FLAGS")
    for r in spreads:
        stake = f" {r['stake_pts']:>6}" if bank else ""
        print(f"{r['game'][:41]:41} {r['mkt_line'][:25]:>25} "
              f"{r['model_line'][:25]:>25} {r['pick'][:26]:>26} "
              f"{r['p']:>9.1%} {r['kelly_frac']:>6.1%}{stake}  {r['flags']}")

    print(f"\n=== TOTALS (U-TAIL unders: {U_TAIL_P:.1%} on top-decile "
          f"totals, pooled 2021-25 — base rate, not a model) ===")
    if totals:
        for r in totals:
            stake = f" {r['stake_pts']:>6}" if bank else ""
            print(f"{r['game'][:41]:41} {r['mkt_line']:>10} "
                  f"{r['pick']:>12} {r['p']:>9.1%} "
                  f"{r['kelly_frac']:>6.1%}{stake}")
    else:
        print("no games in the top total decile this week")

    print(f"\n{len(spreads)} spread picks priced, {len(totals)} U-TAIL "
          f"unders. skipped: {no_line} without a posted spread, {no_model} "
          f"without a model price (FCS/unrated opponent).\n"
          f"INT = integer line, push possible — treat cover probs within "
          f"~1pp of break-even as no edge, especially at 3 and 7.")


# ---------------- ml view: model win prob vs no-vig market ----------------

def build_ml_rows(week: int, refresh: bool, devig: str,
                  kelly_frac: float, bank: float | None):
    games, model_curve = _load_inputs(refresh)
    market_curve = load_curve("market")
    rows, no_market, no_model = [], 0, 0
    for g in games:
        if g["wk"] != week:
            continue
        if g["model_margin"] is None:
            no_model += 1
            continue
        p_home = model_curve.win_prob(g["model_margin"])
        home_ml, away_ml, ml_book = _same_book_mls(g)
        has_ml = (home_ml is not None and away_ml is not None
                  and overround(home_ml, away_ml) <= MAX_OVERROUND)
        if has_ml:
            q_home, _ = novig(home_ml, away_ml, devig)
            src = "ml"
        elif g["spread"] is not None:
            q_home = market_curve.win_prob(-float(g["spread"]))
            src = "spread"
        else:
            no_market += 1
            continue

        on_home = p_home > q_home
        side = g["home"] if on_home else g["away"]
        p = p_home if on_home else 1 - p_home
        q = q_home if on_home else 1 - q_home
        side_ml = (home_ml if on_home else away_ml) if has_ml else None
        kf = kelly(p, side_ml, kelly_frac) if side_ml is not None else None

        # ledger: first-seen vs now, CLV signed to the model side, decay flags
        led = line_ledger.assess(g["id"], g["model_margin"], g["home"], g["away"])

        flags = [g["tier"]] if g["tier"] else []
        if g["ml_guard"] and side == g.get("dog"):
            flags.append("GUARD")
        wp_gap = abs(p_home - q_home) * 100
        if src == "ml" and wp_gap >= STRUCT_PP:
            flags.append("STRUCT")
        flags += led["flags"]
        if g["completed"]:
            flags.append(f"FINAL {g['home_pts']}-{g['away_pts']}")

        rows.append(dict(
            game=f"{g['away']} @ {g['home']}" + (" (N)" if g["neutral"] else ""),
            game_id=g["id"], wk=g["wk"], home=g["home"], away=g["away"],
            neutral=g["neutral"], date=g["date"], venue=g["venue"],
            mkt_spread=g["spread_text"]
                       or _spread_text(g["home"], g["away"], g["spread"]) or "-",
            model_spread=_spread_text(g["home"], g["away"],
                                      round(-g["model_margin"], 1)),
            model_margin=round(g["model_margin"], 2),
            model_p_home=round(p_home, 4), mkt_p_home=round(q_home, 4),
            wp_gap_pp=round(wp_gap, 1),
            side=side,
            side_ml="" if side_ml is None else f"{int(side_ml):+d}",
            model_p=p, mkt_p=q, mkt_src=src, ml_book=ml_book,
            spread_book=g.get("spread_book"), books=g.get("books") or {},
            ou=g["ou"], ou_tail=g["ou_tail"],
            fair_ml=f"{prob_to_american(p):+d}",
            edge_pp=100 * (p - q),
            first_spread=led["first_spread"], first_ts=led["first_ts"],
            now_spread=led["now_spread"], now_ts=led["now_ts"],
            opener=led["opener"], clv=led["clv"],
            first_edge=led["first_edge"], now_edge=led["now_edge"],
            tier=g["tier"],
            kelly_frac=kf,
            stake_pts=round(bank * kf) if (bank and kf is not None) else None,
            flags=" ".join(flags)))
    rows.sort(key=lambda r: -r["edge_pp"])
    return rows, no_market, no_model, model_curve


def print_ml(rows, week, devig, no_market, no_model, curve,
             kelly_frac, bank) -> None:
    meta = curve.meta
    print(f"WEEK {week} MODEL vs MARKET (moneyline view) — curve "
          f"n={meta.get('n')} (resid sd {meta.get('resid_sd')}), "
          f"devig={devig}, kelly={kelly_frac:g}x"
          + (f", bank={bank:g}" if bank else ""))
    stake_h = f" {'STAKE':>6}" if bank else ""
    print(f"{'GAME':41} {'MKT SPREAD':>25} {'MODEL SPREAD':>25} "
          f"{'SIDE':22} {'ML':>6} {'MODEL%':>7} {'MKT%':>7} "
          f"{'FAIR':>6} {'EDGE':>6} {'FIRST>NOW':>11} {'CLV':>5} "
          f"{'KELLY':>6}{stake_h}  FLAGS")
    for r in rows:
        mkt = f"{r['mkt_p']:.1%}" + ("*" if r["mkt_src"] == "spread" else " ")
        kel = f"{r['kelly_frac']:.1%}" if r["kelly_frac"] is not None else "-"
        stake = ""
        if bank:
            stake = f" {r['stake_pts'] if r['stake_pts'] is not None else '-':>6}"
        if r["first_spread"] is not None:
            move = f"{r['first_spread']:+g}>{r['now_spread']:+g}"
            clv = f"{r['clv']:+g}" if r["clv"] is not None else "-"
        else:
            move, clv = "-", "-"
        print(f"{r['game'][:41]:41} {r['mkt_spread'][:25]:>25} "
              f"{r['model_spread'][:25]:>25} {r['side'][:22]:22} "
              f"{r['side_ml']:>6} {r['model_p']:>7.1%} {mkt:>8} "
              f"{r['fair_ml']:>6} {r['edge_pp']:>+6.1f} {move:>11} {clv:>5} "
              f"{kel:>6}{stake}  {r['flags']}")
    pulls = line_ledger.pulls()
    as_of = pulls[-1]["ts"] if pulls else "no ledger yet"
    print(f"\n{len(rows)} games priced. "
          f"* market prob derived from the spread (no usable moneyline). "
          f"skipped: {no_market} without any line, {no_model} without a "
          f"model price (FCS/unrated opponent).\n"
          f"FIRST>NOW = home-perspective spread at first sight -> latest pull "
          f"({as_of}); CLV signed to the model's side. "
          f"STRUCT = model/market win probs differ by >= {STRUCT_PP:g}pp.\n"
          f"KELLY = {kelly_frac:g}x Kelly at the posted ML (0.0% = no +EV "
          f"at that price even if the no-vig edge is positive; - = no ML).")


def write_card_data(rows: list[dict], week: int, curve, devig: str) -> Path:
    """The deck's contract: everything the card shows about the market and
    the model, per game, plus the ledger's as-of stamp."""
    pulls = line_ledger.pulls()
    out = dict(
        week=week, generated=datetime.datetime.now().isoformat(timespec="seconds"),
        lines_as_of=pulls[-1]["ts"] if pulls else None,
        curve=dict(n=curve.meta.get("n"), resid_sd=curve.meta.get("resid_sd")),
        devig=devig, struct_pp=STRUCT_PP,
        thresholds=dict(edge_min=line_ledger.EDGE_MIN,
                        edge_decay=line_ledger.EDGE_DECAY,
                        clv_move=line_ledger.CLV_MOVE),
        games=[{k: r[k] for k in (
            "game_id", "wk", "home", "away", "neutral", "date", "venue",
            "model_margin", "model_spread", "model_p_home", "mkt_p_home",
            "mkt_src", "ml_book", "spread_book", "books", "mkt_spread", "ou",
            "ou_tail", "side", "model_p", "mkt_p", "edge_pp", "wp_gap_pp",
            "first_spread", "first_ts", "now_spread", "now_ts", "opener",
            "clv", "first_edge", "now_edge", "tier", "flags")}
               for r in rows])
    path = HERE / f"card_data_week{week}.json"
    json.dump(out, open(path, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    return path


def main() -> None:
    try:  # Windows consoles/pipes default to cp1252; team names are UTF-8
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(
        description="Weekly edge board: contest view (spreads + totals) or "
                    "ml view (model vs no-vig moneyline market).")
    ap.add_argument("--week", required=True,
                    help="CFBD week number, or 'auto' (first unplayed week)")
    ap.add_argument("--view", choices=["contest", "ml"], default="contest")
    ap.add_argument("--refresh", action="store_true",
                    help="re-pull games/lines from CFBD (needs CFBD_API_KEY)")
    ap.add_argument("--publish", action="store_true",
                    help="publish-time pull: implies --refresh, records the "
                         "line ledger, writes card_data_week{N}.json")
    ap.add_argument("--payout", choices=["even", "110"], default="even",
                    help="contest view: what a winning pick pays (default "
                         "'even', UNCONFIRMED; '110' for -110 juice)")
    ap.add_argument("--devig", choices=["proportional", "power", "shin"],
                    default="proportional", help="ml view: devig method")
    ap.add_argument("--kelly", type=float, default=0.25, metavar="FRAC",
                    help="Kelly fraction for stake sizing (default 0.25)")
    ap.add_argument("--bank", type=float, metavar="POINTS",
                    help="bankroll in points; adds a STAKE column")
    ap.add_argument("--csv", metavar="PATH", help="also write the board as CSV")
    args = ap.parse_args()
    refresh = args.refresh or args.publish

    try:
        # one load resolves 'auto'; the pull (if any) happens here, so the
        # ledger is appended before any view reads it; later loads hit cache
        games, _ = _load_inputs(refresh)
        week = resolve_week(args.week, games)
        if args.view == "contest":
            payout_ml = 100 if args.payout == "even" else -110
            spreads, totals, no_line, no_model, curve = build_contest_rows(
                week, False, payout_ml, args.kelly, args.bank)
            print_contest(spreads, totals, week, payout_ml, args.kelly,
                          args.bank, no_line, no_model, curve)
            csv_rows, fields = spreads + totals, CONTEST_COLUMNS
        else:
            rows, no_market, no_model, curve = build_ml_rows(
                week, False, args.devig, args.kelly, args.bank)
            print_ml(rows, week, args.devig, no_market, no_model, curve,
                     args.kelly, args.bank)
            csv_rows, fields = rows, ML_COLUMNS
        if args.publish:
            if args.view != "ml":
                rows, *_ = build_ml_rows(week, False, args.devig, args.kelly,
                                         args.bank)
                curve = load_curve("model")
            path = write_card_data(rows, week, curve, args.devig)
            print(f"published {path.name} ({len(rows)} games)")
    except FileNotFoundError as e:
        sys.exit(str(e))

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            for r in csv_rows:
                out = dict(r)
                for k in ("p", "model_p", "mkt_p", "kelly_frac"):
                    if out.get(k) is not None:
                        out[k] = round(out[k], 4)
                if out.get("edge_pp") is not None:
                    out["edge_pp"] = round(out["edge_pp"], 2)
                w.writerow(out)
        print(f"wrote {args.csv}")


if __name__ == "__main__":
    main()
