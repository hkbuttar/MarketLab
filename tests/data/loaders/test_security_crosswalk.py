"""Tests for the evidence-preserving ticker-to-CIK crosswalk."""

import csv
import gzip
from pathlib import Path
from zipfile import ZipFile

from marketlab.data.loaders.security_crosswalk import build_security_crosswalk


def test_combines_matching_overview_and_sec_evidence(tmp_path: Path) -> None:
    _listing(tmp_path, "active", "EXM", "Example Inc", "null", "Active")
    _listing(tmp_path, "delisted", "OLD", "Old Inc", "2020-01-01", "Delisted")
    overview = tmp_path / "fundamentals/alpha_vantage/OLD_overview/2024-01-01T000000Z"
    overview.mkdir(parents=True)
    (overview / "OLD_overview.json").write_text(
        '{"Symbol":"OLD","CIK":"1"}', encoding="utf-8"
    )
    submissions = tmp_path / "submissions.zip"
    with ZipFile(submissions, "w") as archive:
        archive.writestr(
            "registrants.csv",
            "cik,ticker,exchange,company_name\n0000000002,EXM,NYSE,Example Inc\n",
        )

    output = tmp_path / "crosswalk.csv.gz"
    result = build_security_crosswalk(
        raw_root=tmp_path, submissions_index=submissions, output=output
    )

    with gzip.open(output, "rt", encoding="utf-8", newline="") as file:
        rows = {row["symbol"]: row for row in csv.DictReader(file)}
    assert result == {"symbols": 2, "mapped_symbols": 2, "conflicts": 0, "rows": 2}
    assert rows["OLD"]["cik"] == "0000000001"
    assert rows["OLD"]["listing_end"] == "2020-01-01"
    assert rows["EXM"]["source"] == "sec_submissions"


def _listing(
    root: Path, state: str, symbol: str, name: str, end: str, status: str
) -> None:
    stem = f"listings_{state}"
    path = root / f"reference/alpha_vantage/{stem}/2024-01-01T000000Z/{stem}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "symbol,name,exchange,assetType,ipoDate,delistingDate,status\n"
        f"{symbol},{name},NYSE,Stock,2000-01-01,{end},{status}\n",
        encoding="utf-8",
    )
