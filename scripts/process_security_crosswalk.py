"""Build the historical ticker-to-CIK evidence crosswalk."""

import argparse
from pathlib import Path

from marketlab.data.loaders.security_crosswalk import build_security_crosswalk


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-root", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--submissions-index",
        type=Path,
        default=Path("data/processed/sec/submissions_index.zip"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/reference/security_crosswalk.csv.gz"),
    )
    args = parser.parse_args()
    result = build_security_crosswalk(
        raw_root=args.raw_root,
        submissions_index=args.submissions_index,
        output=args.output,
    )
    print(f"Crosswalk: {args.output}")
    print(f"Universe symbols: {result['symbols']}")
    print(f"Mapped symbols: {result['mapped_symbols']}")
    print(f"Conflicting symbols: {result['conflicts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
