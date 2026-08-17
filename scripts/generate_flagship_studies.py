"""Publish the four flagship MarketLab studies from completed artifacts."""

from pathlib import Path

from marketlab.reporting.studies import generate_flagship_studies


def main() -> int:
    for markdown, html in generate_flagship_studies(Path(".")):
        print(f"Study: {markdown}")
        print(f"Study: {html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
