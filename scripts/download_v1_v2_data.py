"""Download the complete resumable MarketLab V1/V2 raw dataset."""

import argparse
import csv
import json
import re
import time
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path

import httpx

from marketlab.data.downloaders import (
    FUNDAMENTAL_FUNCTIONS,
    AlphaVantageFundamentalDownloader,
    AlphaVantageListingDownloader,
    AlphaVantagePriceDownloader,
    AlphaVantageTreasuryDownloader,
)
from marketlab.data.downloaders.alpha_vantage import RawHttpResponse

BENCHMARKS = ("SPY", "QQQ", "IWM")
VALID_SYMBOL = re.compile(r"^[A-Z][A-Z0-9.-]*$")
NON_COMMON_SECURITY_NAME = re.compile(
    r"\b("
    r"warrants?|wts?|rights?|rts?|units?|preferred|preference|pfd|"
    r"depositary|debentures?|bonds?|notes? due"
    r")\b",
    re.IGNORECASE,
)
PREFERRED_SYMBOL = re.compile(r"-P(?:-|$)")


class RateLimiter:
    """Sliding-window request limiter for Alpha Vantage subscriptions."""

    def __init__(self, requests_per_minute: int) -> None:
        if requests_per_minute < 1:
            raise ValueError("requests_per_minute must be positive")
        self.limit = requests_per_minute
        self._interval = 60 / requests_per_minute
        self._next_request = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        if now < self._next_request:
            time.sleep(self._next_request - now)
            now = time.monotonic()
        self._next_request = now + self._interval


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download all raw data required by MarketLab V1 and V2."
    )
    parser.add_argument(
        "--requests-per-minute",
        type=int,
        default=70,
        help="Provider request ceiling with safety margin (default: 70).",
    )
    parser.add_argument(
        "--max-symbols",
        type=int,
        help="Limit the universe for a test run; omit for every listed stock.",
    )
    parser.add_argument(
        "--skip-fundamentals",
        action="store_true",
        help="Download listings, Treasury data, and prices only.",
    )
    return parser


def listed_stock_symbols(paths: Iterable[Path]) -> list[str]:
    """Return unique U.S. stock symbols from provider listing snapshots."""

    symbols: set[str] = set()
    for path in paths:
        with path.open(newline="", encoding="utf-8-sig") as file:
            for row in csv.DictReader(file):
                symbol = row.get("symbol", "").strip().upper()
                name = row.get("name", "")
                if is_common_equity(symbol, name, row.get("assetType", "")):
                    symbols.add(symbol)
    return sorted(symbols)


def is_common_equity(symbol: str, name: str, asset_type: str) -> bool:
    """Apply a conservative common-equity screen to provider listings."""

    return bool(
        asset_type == "Stock"
        and VALID_SYMBOL.fullmatch(symbol)
        and not PREFERRED_SYMBOL.search(symbol)
        and not NON_COMMON_SECURITY_NAME.search(name)
    )


def snapshot_exists(raw_root: Path, category: str, stem: str, suffix: str) -> bool:
    """Return whether a prior immutable snapshot exists for a dataset item."""

    root = raw_root / category / "alpha_vantage" / stem
    return any(root.glob(f"*/{stem}{suffix}"))


def main() -> int:
    args = build_parser().parse_args()
    raw_root = Path("data/raw")
    limiter = RateLimiter(args.requests_per_minute)
    failures: list[dict[str, str]] = []

    with httpx.Client() as client:

        def http_get(
            url: str, params: dict[str, str], timeout: float
        ) -> RawHttpResponse:
            limiter.wait()
            response = client.get(url, params=params, timeout=timeout)
            return RawHttpResponse(
                status_code=response.status_code, body=response.content
            )

        listing = AlphaVantageListingDownloader(raw_root=raw_root, http_get=http_get)
        treasury = AlphaVantageTreasuryDownloader(raw_root=raw_root, http_get=http_get)
        prices = AlphaVantagePriceDownloader(raw_root=raw_root, http_get=http_get)
        fundamentals = AlphaVantageFundamentalDownloader(
            raw_root=raw_root, http_get=http_get
        )

        listing_paths = [
            listing.download_and_save(state="active"),
            listing.download_and_save(state="delisted"),
        ]
        treasury.download_and_save()

        symbols = listed_stock_symbols(listing_paths)
        if args.max_symbols is not None:
            symbols = symbols[: args.max_symbols]
        symbols = sorted(set(symbols).union(BENCHMARKS))
        print(f"Acquiring {len(symbols)} symbols")

        for index, symbol in enumerate(symbols, start=1):
            _run_item(
                failures,
                dataset="prices",
                symbol=symbol,
                already_done=snapshot_exists(raw_root, "prices", symbol, ".json"),
                action=lambda symbol=symbol: prices.download_and_save(symbol),
            )
            if not args.skip_fundamentals and symbol not in BENCHMARKS:
                for function in FUNDAMENTAL_FUNCTIONS:
                    stem = f"{symbol}_{function.lower()}"
                    _run_item(
                        failures,
                        dataset=function.lower(),
                        symbol=symbol,
                        already_done=snapshot_exists(
                            raw_root, "fundamentals", stem, ".json"
                        ),
                        action=lambda symbol=symbol, function=function: (
                            fundamentals.download_and_save(symbol, function=function)
                        ),
                    )
            print(f"[{index}/{len(symbols)}] {symbol}")

    manifest_path = _write_manifest(raw_root, symbols, failures)
    print(f"Manifest: {manifest_path}")
    print(f"Failures: {len(failures)}")
    return 1 if failures else 0


def _run_item(
    failures: list[dict[str, str]],
    *,
    dataset: str,
    symbol: str,
    already_done: bool,
    action: Callable[[], Path],
) -> None:
    if already_done:
        return
    try:
        action()
    except (httpx.HTTPError, OSError, RuntimeError, ValueError) as error:
        failures.append({"dataset": dataset, "symbol": symbol, "error": str(error)})


def _write_manifest(
    raw_root: Path, symbols: list[str], failures: list[dict[str, str]]
) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = raw_root / f"v1_v2_download_{timestamp}.json"
    path.write_text(
        json.dumps(
            {
                "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
                "symbols": len(symbols),
                "failures": failures,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":
    raise SystemExit(main())
