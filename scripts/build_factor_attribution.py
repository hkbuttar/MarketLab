"""Regress net strategy returns on established U.S. risk factors."""

from pathlib import Path

from marketlab.attribution import build_factor_attribution


def main() -> int:
    report = build_factor_attribution(
        Path("data/features/backtests/daily_results.csv"),
        Path("data/raw/factors/french_daily.csv.gz"),
        Path("reports/attribution/factor_regression.json"),
    )
    for strategy, result in report.items():
        print(
            strategy,
            f"alpha={result['annualized_alpha']:.2%}",
            f"R2={result['r_squared']:.2%}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
