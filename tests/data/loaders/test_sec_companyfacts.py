"""Tests for filing-aware SEC Company Facts indexing."""

import csv
import io
import json
from pathlib import Path
from zipfile import ZipFile

from marketlab.data.loaders.sec_companyfacts import build_sec_companyfacts_index


def test_indexes_selected_facts_with_acceptance_time(tmp_path: Path) -> None:
    submissions = tmp_path / "submissions_index.zip"
    with ZipFile(submissions, "w") as archive:
        archive.writestr(
            "filings.csv",
            "accession_number,accepted_at\n0001,20240201120000\n",
        )

    source = tmp_path / "companyfacts.zip"
    payload = {
        "facts": {
            "us-gaap": {
                "Assets": {
                    "units": {
                        "USD": [
                            {
                                "end": "2023-12-31",
                                "val": 100,
                                "accn": "0001",
                                "fy": 2023,
                                "fp": "FY",
                                "form": "10-K",
                                "filed": "2024-02-01",
                            }
                        ]
                    }
                },
                "UnneededConcept": {"units": {"USD": []}},
            }
        }
    }
    with ZipFile(source, "w") as archive:
        archive.writestr("CIK0000000001.json", json.dumps(payload))

    output = tmp_path / "companyfacts_index.zip"
    result = build_sec_companyfacts_index(source, submissions, output)

    assert result == {"entities": 1, "facts": 1}
    with ZipFile(output) as archive:
        rows = list(csv.DictReader(io.TextIOWrapper(archive.open("facts.csv"))))
    assert rows[0]["concept"] == "Assets"
    assert rows[0]["available_at"] == "20240201120000"
    assert rows[0]["value"] == "100"
    assert not output.with_name("companyfacts_index.zip.part").exists()
