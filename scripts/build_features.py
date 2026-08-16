"""Build technical and point-in-time fundamental feature datasets."""

import argparse
from pathlib import Path

from marketlab.features.fundamental import build_fundamental_features
from marketlab.features.technical import build_daily_technical_features


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prices",
        type=Path,
        default=Path("data/processed/prices/prices_clean.csv.gz"),
    )
    parser.add_argument(
        "--fundamentals",
        type=Path,
        default=Path("data/processed/fundamentals/fundamentals_valued.csv.gz"),
    )
    parser.add_argument(
        "--technical-output",
        type=Path,
        default=Path("data/features/technical/daily.csv.gz"),
    )
    parser.add_argument(
        "--fundamental-output",
        type=Path,
        default=Path("data/features/fundamental/filing_ratios.csv.gz"),
    )
    args = parser.parse_args()
    technical = build_daily_technical_features(args.prices, args.technical_output)
    fundamental = build_fundamental_features(args.fundamentals, args.fundamental_output)
    print(f"Technical rows: {technical['rows']}")
    print(f"Technical symbols: {technical['symbols']}")
    print(f"Fundamental rows: {fundamental['rows']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
