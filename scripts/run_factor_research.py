"""Build monthly factor rankings, quantile returns, and IC diagnostics."""

from pathlib import Path

from marketlab.factors.research import build_monthly_factor_research


def main() -> int:
    result = build_monthly_factor_research(
        Path("data/features/technical/daily.csv.gz"),
        Path("data/features/fundamental/filing_ratios_growth.csv.gz"),
        Path("data/features/factors/monthly_panel_aligned.csv.gz"),
        Path("reports/factors/information_coefficients_aligned.csv"),
        Path("reports/factors/quantile_returns_aligned.csv"),
    )
    print(f"Monthly observations: {result['observations']}")
    print(f"IC rows: {result['ic_rows']}")
    print(f"Quantile-return rows: {result['quantile_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
