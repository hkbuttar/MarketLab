"""Build constrained monthly single-factor and multi-factor portfolios."""

from pathlib import Path

from marketlab.portfolio import build_monthly_portfolios


def main() -> int:
    result = build_monthly_portfolios(
        Path("data/features/factors/monthly_panel_investable.csv.gz"),
        Path("data/features/portfolios/monthly_targets.csv.gz"),
    )
    print(f"Rebalances: {result['rebalances']}")
    print(f"Portfolio rows: {result['portfolio_rows']}")
    print(f"Average turnover: {result['average_turnover']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
