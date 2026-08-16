"""Tests for streaming SEC submissions indexing."""

import csv
import io
import json
from pathlib import Path
from zipfile import ZipFile

from marketlab.data.loaders.sec_submissions import build_sec_submissions_index


def test_builds_registrant_and_point_in_time_filing_indexes(tmp_path: Path) -> None:
    source = tmp_path / "submissions.zip"
    payload = {
        "name": "Example Inc.",
        "tickers": ["EXM"],
        "exchanges": ["NYSE"],
        "filings": {
            "recent": {
                "accessionNumber": ["0001", "0002"],
                "form": ["10-K", "8-K"],
                "filingDate": ["2024-02-01", "2024-02-02"],
                "reportDate": ["2023-12-31", "2024-02-02"],
                "acceptanceDateTime": ["20240201120000", "20240202120000"],
                "primaryDocument": ["annual.htm", "event.htm"],
            }
        },
    }
    with ZipFile(source, "w") as archive:
        archive.writestr("CIK0000000001.json", json.dumps(payload))

    output = tmp_path / "index.zip"
    result = build_sec_submissions_index(source, output)

    assert result == {"registrants": 1, "filings": 1}
    with ZipFile(output) as archive:
        registrants = list(
            csv.DictReader(io.TextIOWrapper(archive.open("registrants.csv")))
        )
        filings = list(csv.DictReader(io.TextIOWrapper(archive.open("filings.csv"))))
    assert registrants[0] == {
        "cik": "0000000001",
        "ticker": "EXM",
        "exchange": "NYSE",
        "company_name": "Example Inc.",
    }
    assert filings[0]["accession_number"] == "0001"
    assert filings[0]["form"] == "10-K"
    assert filings[0]["accepted_at"] == "20240201120000"
