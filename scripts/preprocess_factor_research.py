"""Screen and robustly preprocess the aligned monthly factor panel."""

from pathlib import Path

from marketlab.features.preprocessing import build_investable_factor_research


def main() -> int:
    result = build_investable_factor_research(
        Path("data/features/factors/monthly_panel_aligned.csv.gz"),
        Path("data/processed/prices/prices_clean.csv.gz"),
        Path("data/features/factors/monthly_panel_investable.csv.gz"),
        Path("reports/factors/information_coefficients_investable.csv"),
        Path("reports/factors/quantile_returns_investable.csv"),
    )
    print(f"Eligible observations: {result['eligible_rows']}")
    print(f"Excluded observations: {result['excluded_rows']}")
    print(f"IC rows: {result['ic_rows']}")
    print(f"Quantile-return rows: {result['quantile_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
