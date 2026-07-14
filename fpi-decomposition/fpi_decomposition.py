"""FPI decomposition: how much of ESPN's FPI is reconstructable from public inputs?

Usage:
    python fpi_decomposition.py --year 2025
    python fpi_decomposition.py --year 2025 --transfer
    python fpi_decomposition.py --year 2025 --refresh   # bypass disk cache
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from analysis import (
    FEATURE_COLS,
    build_dataset,
    fit_ols,
    top_bottom_residuals,
)
from cfbd_client import CFBDError
from name_mapping import report_coverage
from plotting import residual_chart

OUT_DIR = Path(__file__).parent / "output"


def summarize_model(model, feature_cols: list[str]) -> str:
    lines = [
        f"  N teams:      {int(model.nobs)}",
        f"  R-squared:      {model.rsquared:.3f}",
        f"  Adjusted R-sq:  {model.rsquared_adj:.3f}",
        "",
        f"  {'feature':<16}{'std. coef':>10}{'p-value':>10}",
    ]
    for name in ["const"] + feature_cols:
        lines.append(
            f"  {name:<16}{model.params[name]:>10.3f}{model.pvalues[name]:>10.4f}"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2025, help="preseason year")
    parser.add_argument(
        "--transfer",
        action="store_true",
        help="add net transfer-portal rating to the regression and compare",
    )
    parser.add_argument(
        "--refresh", action="store_true", help="bypass the disk cache"
    )
    args = parser.parse_args()

    try:
        merged, coverage, fpi_year = build_dataset(
            args.year, refresh=args.refresh, transfer=args.transfer
        )
    except CFBDError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if fpi_year != args.year:
        print(
            f"NOTE: FPI for {args.year} not on CFBD yet — fell back to {fpi_year}.\n"
        )

    print(report_coverage(coverage))
    print()

    model, fitted = fit_ols(merged, FEATURE_COLS)
    print(f"=== Baseline model: fpi ~ {' + '.join(FEATURE_COLS)} ===")
    print(summarize_model(model, FEATURE_COLS))

    residuals = top_bottom_residuals(fitted)
    OUT_DIR.mkdir(exist_ok=True)
    csv_path = OUT_DIR / f"residuals_{fpi_year}.csv"
    residuals.to_csv(csv_path, index=False)
    chart_path = residual_chart(residuals, fpi_year)
    print(f"\nResiduals CSV:   {csv_path}")
    print(f"Residual chart:  {chart_path}")

    if args.transfer:
        portal_cols = FEATURE_COLS + ["net_portal"]
        model_p, fitted_p = fit_ols(merged, portal_cols)
        print(f"\n=== Portal model: fpi ~ {' + '.join(portal_cols)} ===")
        print(summarize_model(model_p, portal_cols))

        print("\n=== Before/after comparison ===")
        print(f"  {'metric':<24}{'baseline':>12}{'+ portal':>12}")
        print(
            f"  {'Adjusted R-sq':<24}{model.rsquared_adj:>12.4f}"
            f"{model_p.rsquared_adj:>12.4f}"
        )
        print(
            f"  {'Residual std (all)':<24}{fitted['residual'].std():>12.3f}"
            f"{fitted_p['residual'].std():>12.3f}"
        )

        # Residual shrinkage for high-portal-turnover teams (top quartile by
        # gross portal activity proxied by |net_portal| among fitted teams).
        common = fitted.index.intersection(fitted_p.index)
        turnover = fitted_p.loc[common, "net_portal_raw"].abs()
        high = turnover >= turnover.quantile(0.75)
        before = fitted.loc[common][high]["residual"].abs().mean()
        after = fitted_p.loc[common][high]["residual"].abs().mean()
        print(
            f"  {'Mean |resid|, hi-portal':<24}{before:>12.3f}{after:>12.3f}"
        )

        residuals_p = top_bottom_residuals(fitted_p)
        csv_p = OUT_DIR / f"residuals_{fpi_year}_portal.csv"
        residuals_p.to_csv(csv_p, index=False)
        chart_p = residual_chart(residuals_p, fpi_year, suffix="_portal")
        print(f"\nPortal residuals CSV:   {csv_p}")
        print(f"Portal residual chart:  {chart_p}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
