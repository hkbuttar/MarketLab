"""Calculate strategy performance conditioned on market regime."""

from pathlib import Path

from marketlab.regimes import build_regime_analysis


def main() -> int:
    rows = build_regime_analysis(
        Path("data/features/backtests/daily_results.csv"),
        Path("data/features/regimes/daily_regimes.csv"),
        Path("data/features/portfolios/monthly_targets.csv.gz"),
        Path("data/raw/factors/french_daily.csv.gz"),
        Path("reports/regimes"),
    )
    for row in rows:
        print(
            row["strategy"],
            row["regime"],
            f"CAGR={row['cagr']:.2%}",
            f"Sharpe={row['sharpe']:.2f}",
            f"MaxDD={row['maximum_episode_drawdown']:.2%}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
