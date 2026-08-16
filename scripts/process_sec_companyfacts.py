"""Build a filing-aware index from SEC companyfacts.zip."""

import argparse
from pathlib import Path

from marketlab.data.loaders.sec_companyfacts import build_sec_companyfacts_index


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw-root", type=Path, default=Path("data/raw/fundamentals/sec_edgar")
    )
    parser.add_argument(
        "--submissions-index",
        type=Path,
        default=Path("data/processed/sec/submissions_index.zip"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/sec/companyfacts_index.zip"),
    )
    return parser


def latest_companyfacts_archive(raw_root: Path) -> Path:
    paths = sorted((raw_root / "companyfacts").glob("*/companyfacts.zip"))
    if not paths:
        raise FileNotFoundError("no SEC Company Facts archive found")
    return paths[-1]


def main() -> int:
    args = build_parser().parse_args()
    source = latest_companyfacts_archive(args.raw_root)
    result = build_sec_companyfacts_index(source, args.submissions_index, args.output)
    print(f"Source: {source}")
    print(f"Index: {args.output}")
    print(f"Entities scanned: {result['entities']}")
    print(f"Selected facts: {result['facts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
