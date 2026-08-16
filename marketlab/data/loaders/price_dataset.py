"""Build a processed price dataset from immutable raw snapshots."""

import csv
import gzip
import json
from collections.abc import Iterable
from pathlib import Path

from marketlab.data.loaders.alpha_vantage import load_alpha_vantage_prices
from marketlab.data.schemas import PRICE_COLUMNS


def latest_price_snapshot(raw_root: Path, symbol: str) -> Path | None:
    """Return the newest raw Alpha Vantage price snapshot for a symbol."""

    snapshot_root = raw_root / "prices" / "alpha_vantage" / symbol
    paths = sorted(snapshot_root.glob(f"*/{symbol}.json"))
    return paths[-1] if paths else None


def write_price_dataset(
    *, raw_root: Path, output_path: Path, symbols: Iterable[str]
) -> dict[str, object]:
    """Write canonical prices as an atomic, gzip-compressed CSV dataset."""

    if output_path.exists():
        raise FileExistsError(f"processed dataset already exists: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    partial_path = output_path.with_name(f"{output_path.name}.part")
    if partial_path.exists():
        raise FileExistsError(f"partial dataset already exists: {partial_path}")

    requested = sorted(set(symbols))
    loaded_symbols = 0
    rows = 0
    missing: list[str] = []
    try:
        with gzip.open(partial_path, "wt", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=PRICE_COLUMNS)
            writer.writeheader()
            for symbol in requested:
                path = latest_price_snapshot(raw_root, symbol)
                if path is None:
                    missing.append(symbol)
                    continue
                records = load_alpha_vantage_prices(path)
                for record in records:
                    row = {column: getattr(record, column) for column in PRICE_COLUMNS}
                    row["date"] = record.date.date().isoformat()
                    writer.writerow(row)
                    rows += 1
                loaded_symbols += 1
        partial_path.replace(output_path)
    except BaseException:
        partial_path.unlink(missing_ok=True)
        raise

    result: dict[str, object] = {
        "requested_symbols": len(requested),
        "loaded_symbols": loaded_symbols,
        "missing_symbols": missing,
        "rows": rows,
    }
    metadata_path = output_path.with_suffix(output_path.suffix + ".metadata.json")
    metadata_path.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result
