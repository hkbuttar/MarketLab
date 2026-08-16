"""Create research-safe prices and quarantine invalid provider rows."""

import argparse
from pathlib import Path

from marketlab.data.validation import clean_price_dataset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data/processed/prices/prices.csv.gz"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/prices/prices_clean.csv.gz"),
    )
    parser.add_argument(
        "--quarantine",
        type=Path,
        default=Path("reports/price_quarantine.csv.gz"),
    )
    args = parser.parse_args()
    result = clean_price_dataset(args.source, args.output, args.quarantine)
    print(f"Clean dataset: {args.output}")
    print(f"Quarantine: {args.quarantine}")
    print(f"Accepted rows: {result['accepted_rows']}")
    print(f"Quarantined rows: {result['quarantined_rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
