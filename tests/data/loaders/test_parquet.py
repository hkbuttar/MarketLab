import csv
import gzip
import json
from pathlib import Path

import pyarrow.parquet as pq

from marketlab.data.loaders.parquet import (
    PRICE_SCHEMA,
    RISK_FREE_SCHEMA,
    convert_csv_to_parquet,
    convert_risk_free_json,
    validate_parquet,
)


def test_streams_typed_prices_and_filters_benchmark(tmp_path: Path) -> None:
    source = tmp_path / "prices.csv.gz"
    output = tmp_path / "benchmark.parquet"
    with gzip.open(source, "wt", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(PRICE_SCHEMA.names)
        writer.writerow(["2024-01-02", "SPY", 100, 102, 99, 101, 101, 1_000])
        writer.writerow(["2024-01-02", "AAA", 10, 11, 9, 10, 10, 2_000])

    result = convert_csv_to_parquet(source, output, PRICE_SCHEMA, symbol_filter="SPY")

    assert result["rows"] == 1
    assert validate_parquet(output, PRICE_SCHEMA)["rows"] == 1
    table = pq.read_table(output)
    assert table.column("symbol").to_pylist() == ["SPY"]


def test_converts_percentage_risk_free_rate_to_decimal(tmp_path: Path) -> None:
    source = tmp_path / "risk_free.json"
    output = tmp_path / "risk_free.parquet"
    source.write_text(
        json.dumps({"data": [{"date": "2024-01-02", "value": "5.25"}]}),
        encoding="utf-8",
    )

    result = convert_risk_free_json(source, output)

    assert result["rows"] == 1
    assert validate_parquet(output, RISK_FREE_SCHEMA)["rows"] == 1
    assert pq.read_table(output).column("annual_rate").to_pylist() == [0.0525]
