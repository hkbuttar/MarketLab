"""Build point-in-time filing indexes from SEC submissions.zip."""

import argparse
from pathlib import Path

from marketlab.data.loaders.sec_submissions import build_sec_submissions_index


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw-root", type=Path, default=Path("data/raw/fundamentals/sec_edgar")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/sec/submissions_index.zip"),
    )
    return parser


def latest_submissions_archive(raw_root: Path) -> Path:
    paths = sorted((raw_root / "submissions").glob("*/submissions.zip"))
    if not paths:
        raise FileNotFoundError("no SEC submissions archive found")
    return paths[-1]


def main() -> int:
    args = build_parser().parse_args()
    source = latest_submissions_archive(args.raw_root)
    result = build_sec_submissions_index(source, args.output)
    print(f"Source: {source}")
    print(f"Index: {args.output}")
    print(f"Ticker mappings: {result['registrants']}")
    print(f"10-K/10-Q filings: {result['filings']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
