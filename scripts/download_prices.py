"""Download raw daily equity and benchmark price snapshots."""

import argparse

from marketlab.data.downloaders import AlphaVantagePriceDownloader


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download raw Alpha Vantage daily adjusted-price snapshots."
    )
    parser.add_argument(
        "symbols",
        nargs="+",
        help="Equity or ETF symbols, for example AAPL MSFT SPY.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    downloader = AlphaVantagePriceDownloader()
    for symbol in args.symbols:
        path = downloader.download_and_save(symbol)
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
