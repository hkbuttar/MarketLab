"""Generate next-open executable trades from monthly portfolio targets."""

from pathlib import Path

from marketlab.backtest.trade_generation import generate_rebalance_trades


def main() -> int:
    result = generate_rebalance_trades(
        Path("data/features/portfolios/monthly_targets.csv.gz"),
        Path("data/processed/prices/prices_clean.csv.gz"),
        Path("data/features/portfolios/rebalance_trades_split_adjusted.csv.gz"),
    )
    print(f"Trades: {result['trades']}")
    print(f"Total costs: {result['total_costs']}")
    print(f"Ending positions: {result['ending_positions']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
