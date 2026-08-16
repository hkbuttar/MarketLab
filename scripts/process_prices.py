"""Build the canonical processed-price dataset from raw snapshots."""

import argparse
from pathlib import Path

from marketlab.data.loaders import write_price_dataset
from scripts.download_v1_v2_data import BENCHMARKS, listed_stock_symbols


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/prices/prices.csv.gz"),
    )
    parser.add_argument(
        "--max-symbols", type=int, help="Process a small deterministic test subset."
    )
    return parser


def latest_listing(raw_root: Path, state: str) -> Path:
    """Return the newest raw listing snapshot for an active/delisted state."""

    stem = f"listings_{state}"
    paths = sorted(
        (raw_root / "reference" / "alpha_vantage" / stem).glob(f"*/{stem}.csv")
    )
    if not paths:
        raise FileNotFoundError(f"no {state} listing snapshot found")
    return paths[-1]


def main() -> int:
    args = build_parser().parse_args()
    listing_paths = [
        latest_listing(args.raw_root, "active"),
        latest_listing(args.raw_root, "delisted"),
    ]
    symbols = listed_stock_symbols(listing_paths)
    if args.max_symbols is not None:
        symbols = symbols[: args.max_symbols]
    symbols = sorted(set(symbols).union(BENCHMARKS))

    result = write_price_dataset(
        raw_root=args.raw_root, output_path=args.output, symbols=symbols
    )
    print(f"Dataset: {args.output}")
    print(f"Rows: {result['rows']}")
    print(f"Loaded symbols: {result['loaded_symbols']}")
    print(f"Missing symbols: {len(result['missing_symbols'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
