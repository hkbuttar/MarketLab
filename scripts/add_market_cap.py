"""Add point-in-time market capitalization to canonical fundamentals."""

import argparse
from pathlib import Path

from marketlab.data.loaders.market_cap import add_point_in_time_market_cap


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fundamentals",
        type=Path,
        default=Path("data/processed/fundamentals/fundamentals_point_in_time.csv.gz"),
    )
    parser.add_argument(
        "--prices",
        type=Path,
        default=Path("data/processed/prices/prices_clean.csv.gz"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/fundamentals/fundamentals_valued.csv.gz"),
    )
    args = parser.parse_args()
    result = add_point_in_time_market_cap(args.fundamentals, args.prices, args.output)
    print(f"Dataset: {args.output}")
    print(f"Valued rows: {result['valued_rows']}")
    print(f"Rows missing shares: {result['missing_shares']}")
    print(f"Rows missing a prior price: {result['missing_prior_price']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
