"""Build canonical typed Parquet datasets from validated processed sources."""

import argparse
import json
from pathlib import Path

from marketlab.data.loaders.parquet import (
    FUNDAMENTAL_SCHEMA,
    PRICE_SCHEMA,
    RISK_FREE_SCHEMA,
    SECURITY_SCHEMA,
    convert_csv_to_parquet,
    convert_risk_free_json,
    validate_parquet,
)


def _latest_risk_free() -> Path:
    paths = sorted(
        Path("data/raw/reference/alpha_vantage/treasury_3month_daily").glob(
            "*/*_daily.json"
        )
    )
    if not paths:
        raise FileNotFoundError("Alpha Vantage risk-free dataset is unavailable")
    return paths[-1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prices-source",
        type=Path,
        default=Path("data/processed/prices/prices_clean.csv.gz"),
    )
    parser.add_argument(
        "--output-directory", type=Path, default=Path("data/processed/parquet")
    )
    arguments = parser.parse_args()
    output = arguments.output_directory
    jobs = (
        (
            "prices",
            lambda: convert_csv_to_parquet(
                arguments.prices_source, output / "prices.parquet", PRICE_SCHEMA
            ),
            PRICE_SCHEMA,
        ),
        (
            "benchmark",
            lambda: convert_csv_to_parquet(
                arguments.prices_source,
                output / "benchmark.parquet",
                PRICE_SCHEMA,
                symbol_filter="SPY",
            ),
            PRICE_SCHEMA,
        ),
        (
            "securities",
            lambda: convert_csv_to_parquet(
                Path("data/processed/reference/security_crosswalk.csv.gz"),
                output / "securities.parquet",
                SECURITY_SCHEMA,
            ),
            SECURITY_SCHEMA,
        ),
        (
            "fundamentals",
            lambda: convert_csv_to_parquet(
                Path(
                    "data/processed/fundamentals/fundamentals_normalized_valued.csv.gz"
                ),
                output / "fundamentals.parquet",
                FUNDAMENTAL_SCHEMA,
            ),
            FUNDAMENTAL_SCHEMA,
        ),
        (
            "risk_free",
            lambda: convert_risk_free_json(
                _latest_risk_free(), output / "risk_free.parquet"
            ),
            RISK_FREE_SCHEMA,
        ),
    )
    manifest: dict[str, object] = {}
    for name, convert, schema in jobs:
        destination = output / f"{name}.parquet"
        if destination.exists():
            result = {
                "size_bytes": destination.stat().st_size,
                **validate_parquet(destination, schema),
            }
        else:
            result = convert()
            result.update(validate_parquet(destination, schema))
        manifest[name] = result
        print(name, result)
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
