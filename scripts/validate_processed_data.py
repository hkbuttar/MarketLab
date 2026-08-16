"""Validate canonical prices, fundamentals, chronology, and coverage."""

import argparse
from pathlib import Path

from marketlab.data.validation import validate_processed_data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prices",
        type=Path,
        default=Path("data/processed/prices/prices.csv.gz"),
    )
    parser.add_argument(
        "--fundamentals",
        type=Path,
        default=Path("data/processed/fundamentals/fundamentals_point_in_time.csv.gz"),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=Path("reports/data_validation.json"),
    )
    args = parser.parse_args()
    result = validate_processed_data(args.prices, args.fundamentals, args.report)
    print(f"Status: {result['status']}")
    print(f"Report: {args.report}")
    print(f"Price rows: {result['prices']['rows']}")
    print(f"Fundamental rows: {result['fundamentals']['rows']}")
    print(f"Symbols with both: {result['coverage']['symbols_with_both']}")
    return int(result["status"] != "passed")


if __name__ == "__main__":
    raise SystemExit(main())
