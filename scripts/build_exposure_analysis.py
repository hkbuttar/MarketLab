"""Build portfolio sector, factor, beta, and concentration diagnostics."""

from pathlib import Path

from marketlab.attribution.exposures import build_exposure_report


def main() -> int:
    report = build_exposure_report(
        Path("data/features/portfolios/monthly_targets.csv.gz"),
        Path("data/features/factors/monthly_panel_investable.csv.gz"),
        Path("data/raw/fundamentals/alpha_vantage"),
        Path("reports/attribution/factor_regression.json"),
        Path("reports/attribution"),
    )
    print(f"Classified symbols: {report['classified_symbols']:,}")
    for strategy, values in report["strategies"].items():
        print(
            strategy,
            f"beta={values['market_beta']:.2f}",
            f"effective holdings={values['average_effective_holdings']:.1f}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
