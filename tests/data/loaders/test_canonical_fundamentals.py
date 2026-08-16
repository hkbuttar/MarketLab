"""Tests for canonical filing-aware fundamental records."""

import csv
import gzip
import io
from pathlib import Path
from zipfile import ZipFile

from marketlab.data.loaders.canonical_fundamentals import (
    build_canonical_fundamentals,
)
from marketlab.data.loaders.sec_companyfacts import FACT_COLUMNS


def test_builds_canonical_fundamental_record(tmp_path: Path) -> None:
    submissions = tmp_path / "submissions.zip"
    with ZipFile(submissions, "w") as archive:
        archive.writestr(
            "registrants.csv",
            "cik,ticker,exchange,company_name\n0000000001,EXM,NYSE,Example\n",
        )
        archive.writestr(
            "filings.csv",
            "cik,accession_number,form,filing_date,report_date,accepted_at,primary_document\n"
            "0000000001,0001,10-K,2024-02-01,2023-12-31,20240201120000,annual.htm\n",
        )

    facts = tmp_path / "facts.zip"
    fact_rows = [
        _fact("Assets", 100),
        _fact("StockholdersEquity", 60),
        _fact("NetCashProvidedByUsedInOperatingActivities", 20, "2023-01-01"),
        _fact("PaymentsToAcquirePropertyPlantAndEquipment", 5, "2023-01-01"),
    ]
    text = io.StringIO()
    writer = csv.DictWriter(text, fieldnames=FACT_COLUMNS)
    writer.writeheader()
    writer.writerows(fact_rows)
    with ZipFile(facts, "w") as archive:
        archive.writestr("facts.csv", text.getvalue())

    output = tmp_path / "fundamentals.csv.gz"
    result = build_canonical_fundamentals(facts, submissions, output)

    with gzip.open(output, "rt", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    assert result == {"entities": 1, "unmapped_entities": 0, "rows": 1}
    assert rows[0]["symbol"] == "EXM"
    assert rows[0]["fiscal_period"] == "2023-FY"
    assert rows[0]["available_date"] == "2024-02-01T12:00:00Z"
    assert rows[0]["assets"] == "100.0"
    assert rows[0]["free_cash_flow"] == "15.0"


def _fact(concept: str, value: int, start: str = "") -> dict[str, object]:
    return {
        "cik": "0000000001",
        "taxonomy": "us-gaap",
        "concept": concept,
        "unit": "USD",
        "value": value,
        "period_start": start,
        "period_end": "2023-12-31",
        "fiscal_year": "2023",
        "fiscal_period": "FY",
        "form": "10-K",
        "filed_date": "2024-02-01",
        "accepted_at": "20240201120000",
        "available_at": "20240201120000",
        "accession_number": "0001",
        "frame": "",
    }
