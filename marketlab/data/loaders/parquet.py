"""Streaming conversion of canonical CSV datasets to typed Parquet storage."""

import gzip
import json
from datetime import date
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

PRICE_SCHEMA = pa.schema(
    [
        ("date", pa.date32()),
        ("symbol", pa.string()),
        ("open", pa.float64()),
        ("high", pa.float64()),
        ("low", pa.float64()),
        ("close", pa.float64()),
        ("adjusted_close", pa.float64()),
        ("volume", pa.int64()),
    ]
)
FUNDAMENTAL_SCHEMA = pa.schema(
    [
        ("symbol", pa.string()),
        ("fiscal_period", pa.string()),
        ("report_date", pa.date32()),
        ("available_date", pa.timestamp("ms", tz="UTC")),
        ("market_cap", pa.float64()),
        ("book_value", pa.float64()),
        ("net_income", pa.float64()),
        ("revenue", pa.float64()),
        ("gross_profit", pa.float64()),
        ("assets", pa.float64()),
        ("debt", pa.float64()),
        ("free_cash_flow", pa.float64()),
        ("shares_outstanding", pa.float64()),
    ]
)
SECURITY_SCHEMA = pa.schema(
    [
        ("symbol", pa.string()),
        ("cik", pa.string()),
        ("company_name", pa.string()),
        ("exchange", pa.string()),
        ("listing_start", pa.date32()),
        ("listing_end", pa.date32()),
        ("status", pa.string()),
        ("source", pa.string()),
        ("conflict", pa.bool_()),
    ]
)
RISK_FREE_SCHEMA = pa.schema([("date", pa.date32()), ("annual_rate", pa.float64())])


def convert_csv_to_parquet(
    source: Path,
    destination: Path,
    schema: pa.Schema,
    *,
    symbol_filter: str | None = None,
    batch_size: int = 64 * 1024 * 1024,
) -> dict[str, int]:
    """Stream a canonical Gzip CSV into an atomic Zstandard Parquet file."""

    if destination.exists():
        raise FileExistsError(f"Parquet output already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    rows = 0
    try:
        with gzip.open(source, "rb") as file:
            reader = pacsv.open_csv(
                file,
                read_options=pacsv.ReadOptions(block_size=batch_size),
                convert_options=pacsv.ConvertOptions(column_types=schema),
            )
            with pq.ParquetWriter(partial, schema, compression="zstd") as writer:
                for batch in reader:
                    if symbol_filter is not None:
                        batch = batch.filter(
                            pc.equal(batch.column("symbol"), symbol_filter)
                        )
                    if batch.num_rows:
                        writer.write_batch(batch)
                        rows += batch.num_rows
        partial.replace(destination)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    return {"rows": rows, "size_bytes": destination.stat().st_size}


def convert_risk_free_json(source: Path, destination: Path) -> dict[str, int]:
    """Convert Alpha Vantage percentage yields to decimal annual rates."""

    if destination.exists():
        raise FileExistsError(f"Parquet output already exists: {destination}")
    payload = json.loads(source.read_text(encoding="utf-8"))
    rows = sorted(
        (
            {
                "date": date.fromisoformat(value["date"]),
                "annual_rate": float(value["value"]) / 100.0,
            }
            for value in payload["data"]
            if value.get("value") not in {None, ".", ""}
        ),
        key=lambda value: value["date"],
    )
    table = pa.Table.from_pylist(rows, schema=RISK_FREE_SCHEMA)
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    try:
        pq.write_table(table, partial, compression="zstd")
        partial.replace(destination)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    return {"rows": table.num_rows, "size_bytes": destination.stat().st_size}


def validate_parquet(path: Path, schema: pa.Schema) -> dict[str, int]:
    """Validate physical schema and return lightweight file metadata."""

    file = pq.ParquetFile(path)
    if not file.schema_arrow.equals(schema):
        raise ValueError(f"Parquet schema mismatch: {path}")
    return {"rows": file.metadata.num_rows, "row_groups": file.metadata.num_row_groups}
