"""Build canonical filing-aware fundamental records."""

import argparse
from pathlib import Path

from marketlab.data.loaders.canonical_fundamentals import (
    build_canonical_fundamentals,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--companyfacts-index",
        type=Path,
        default=Path("data/processed/sec/companyfacts_index.zip"),
    )
    parser.add_argument(
        "--submissions-index",
        type=Path,
        default=Path("data/processed/sec/submissions_index.zip"),
    )
    parser.add_argument(
        "--crosswalk",
        type=Path,
        default=Path("data/processed/reference/security_crosswalk.csv.gz"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/fundamentals/fundamentals_normalized.csv.gz"),
    )
    args = parser.parse_args()
    result = build_canonical_fundamentals(
        args.companyfacts_index,
        args.submissions_index,
        args.output,
        args.crosswalk,
    )
    print(f"Dataset: {args.output}")
    print(f"Rows: {result['rows']}")
    print(f"SEC entities: {result['entities']}")
    print(f"Entities without dated ticker mappings: {result['unmapped_entities']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
