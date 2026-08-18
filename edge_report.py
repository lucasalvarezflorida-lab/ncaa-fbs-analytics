"""Weekly edge table: model win prob vs market price, sorted by edge.

    python edge_report.py --week 1
    python edge_report.py --week 1 --refresh --devig shin --csv wk1.csv

Every row is stated from the MODEL'S SIDE — the team whose model win
probability exceeds its no-vig market probability. EDGE is model minus
market in percentage points. MKT% flagged * is spread-derived through the
market curve (no moneyline posted yet); those firm up as MLs land.

Uses cached CFBD data unless --refresh (which needs CFBD_API_KEY).
Requires margin_prob_curve.json — run fit_margin_curve.py once to build it.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "fpi-decomposition"))

from build_conference_book import (_spread_text, fetch_games,  # noqa: E402
                                   load_fpi_2026)
from margin_prob import load_curve  # noqa: E402
from odds import novig, overround, prob_to_american  # noqa: E402

COLUMNS = ["game", "mkt_spread", "model_spread", "side", "side_ml",
           "model_p", "mkt_p", "mkt_src", "fair_ml", "edge_pp", "flags"]

# a real two-way ML market books 2-8% of vig; Bovada ships -100000
# placeholder MLs on huge favorites, which would devig to ~50/50 and top the
# table with phantom edges — treat those pairs as no ML at all
MAX_OVERROUND = 0.15


def build_rows(week: int, refresh: bool, devig: str):
    fpi = {k: {"fpi": v} for k, v in load_fpi_2026().items()}
    if not fpi:
        sys.exit("no 2026 preseason FPI snapshot found — run refresh_all.py first")
    model_curve = load_curve("model")
    market_curve = load_curve("market")

    rows, no_market, no_model = [], 0, 0
    for g in fetch_games(refresh, fpi):
        if g["wk"] != week:
            continue
        if g["model_margin"] is None:
            no_model += 1  # FCS/unrated opponent: model has no price
            continue
        p_home = model_curve.win_prob(g["model_margin"])
        has_ml = (g["home_ml"] is not None and g["away_ml"] is not None
                  and overround(g["home_ml"], g["away_ml"]) <= MAX_OVERROUND)
        if has_ml:
            q_home, _ = novig(g["home_ml"], g["away_ml"], devig)
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
        side_ml = (g["home_ml"] if on_home else g["away_ml"]) if has_ml else None

        flags = [g["tier"]] if g["tier"] else []
        if g["ml_guard"] and side == g.get("dog"):
            flags.append("GUARD")
        if g["completed"]:
            flags.append(f"FINAL {g['home_pts']}-{g['away_pts']}")

        rows.append(dict(
            game=f"{g['away']} @ {g['home']}" + (" (N)" if g["neutral"] else ""),
            mkt_spread=g["spread_text"]
                       or _spread_text(g["home"], g["away"], g["spread"]) or "-",
            model_spread=_spread_text(g["home"], g["away"],
                                      round(-g["model_margin"], 1)),
            side=side,
            side_ml="" if side_ml is None else f"{int(side_ml):+d}",
            model_p=p, mkt_p=q, mkt_src=src,
            fair_ml=f"{prob_to_american(p):+d}",
            edge_pp=100 * (p - q),
            flags=" ".join(flags)))
    rows.sort(key=lambda r: -r["edge_pp"])
    return rows, no_market, no_model, model_curve


def print_table(rows, week, devig, no_market, no_model, curve) -> None:
    meta = curve.meta
    print(f"WEEK {week} EDGE REPORT — model curve n={meta.get('n')} games "
          f"(resid sd {meta.get('resid_sd')}), devig={devig}")
    print(f"{'GAME':41} {'MKT SPREAD':>21} {'MODEL SPREAD':>21} "
          f"{'SIDE':22} {'ML':>6} {'MODEL%':>7} {'MKT%':>7} "
          f"{'FAIR':>6} {'EDGE':>6}  FLAGS")
    for r in rows:
        mkt = f"{r['mkt_p']:.1%}" + ("*" if r["mkt_src"] == "spread" else " ")
        print(f"{r['game'][:41]:41} {r['mkt_spread'][:21]:>21} "
              f"{r['model_spread'][:21]:>21} {r['side'][:22]:22} "
              f"{r['side_ml']:>6} {r['model_p']:>7.1%} {mkt:>8} "
              f"{r['fair_ml']:>6} {r['edge_pp']:>+6.1f}  {r['flags']}")
    print(f"\n{len(rows)} games priced. "
          f"* market prob derived from the spread (no moneyline posted yet). "
          f"skipped: {no_market} without any line, {no_model} without a model "
          f"price (FCS/unrated opponent).")


def main() -> None:
    try:  # Windows consoles/pipes default to cp1252; team names are UTF-8
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(
        description="Model vs market win-probability edges for one week.")
    ap.add_argument("--week", type=int, required=True)
    ap.add_argument("--refresh", action="store_true",
                    help="re-pull games/lines from CFBD (needs CFBD_API_KEY)")
    ap.add_argument("--devig", choices=["proportional", "power", "shin"],
                    default="proportional")
    ap.add_argument("--csv", metavar="PATH", help="also write the table as CSV")
    args = ap.parse_args()

    try:
        rows, no_market, no_model, curve = build_rows(
            args.week, args.refresh, args.devig)
    except FileNotFoundError as e:
        sys.exit(str(e))

    print_table(rows, args.week, args.devig, no_market, no_model, curve)

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            w.writeheader()
            for r in rows:
                w.writerow({**r, "model_p": round(r["model_p"], 4),
                            "mkt_p": round(r["mkt_p"], 4),
                            "edge_pp": round(r["edge_pp"], 2)})
        print(f"wrote {args.csv}")


if __name__ == "__main__":
    main()
