"""Build factor stability, turnover, and correlation diagnostics."""

from pathlib import Path

from marketlab.factors.tear_sheet import build_factor_tear_sheet


def main() -> int:
    summary = build_factor_tear_sheet(
        Path("data/features/factors/monthly_panel_investable.csv.gz"),
        Path("reports/factors/information_coefficients_investable.csv"),
        Path("reports/factors/quantile_returns_investable.csv"),
        Path("reports/factors/tear_sheet_summary.json"),
        Path("reports/factors/rolling_information_coefficients.csv"),
        Path("reports/factors/top_quantile_turnover.csv"),
        Path("reports/factors/factor_correlations.csv"),
    )
    print(f"Factors summarized: {len(summary['information_coefficient'])}")
    print("Summary: reports/factors/tear_sheet_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
