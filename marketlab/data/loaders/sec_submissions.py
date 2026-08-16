"""Index SEC submissions directly from the official bulk ZIP archive."""

import csv
import json
import re
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

ANNUAL_AND_QUARTERLY_FORMS = {"10-K", "10-K/A", "10-Q", "10-Q/A"}
CIK_FILE = re.compile(r"^CIK(?P<cik>\d{10})(?:-submissions-\d+)?\.json$")
REGISTRANT_COLUMNS = ("cik", "ticker", "exchange", "company_name")
FILING_COLUMNS = (
    "cik",
    "accession_number",
    "form",
    "filing_date",
    "report_date",
    "accepted_at",
    "primary_document",
)


class InvalidSecSubmissionError(ValueError):
    """Raised when an SEC submissions member has inconsistent data."""


def build_sec_submissions_index(source: Path, output: Path) -> dict[str, int]:
    """Write ticker/CIK and 10-K/10-Q indexes without extracting the source."""

    if output.exists():
        raise FileExistsError(f"SEC submissions index already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(f"{output.name}.part")
    if partial.exists():
        raise FileExistsError(f"partial SEC submissions index exists: {partial}")

    registrants = 0
    filings = 0
    try:
        with (
            ZipFile(source) as source_zip,
            ZipFile(
                partial, "x", compression=ZIP_DEFLATED, compresslevel=6
            ) as output_zip,
        ):
            with output_zip.open("registrants.csv", "w") as binary_file:
                text_file = _TextWriter(binary_file)
                writer = csv.DictWriter(text_file, fieldnames=REGISTRANT_COLUMNS)
                writer.writeheader()
                for name in source_zip.namelist():
                    match = CIK_FILE.fullmatch(name)
                    if match is None or "-submissions-" in name:
                        continue
                    payload = _read_json(source_zip, name)
                    registrants += _write_registrants(
                        writer, match.group("cik"), payload
                    )
                text_file.flush()

            with output_zip.open("filings.csv", "w") as binary_file:
                text_file = _TextWriter(binary_file)
                writer = csv.DictWriter(text_file, fieldnames=FILING_COLUMNS)
                writer.writeheader()
                for name in source_zip.namelist():
                    match = CIK_FILE.fullmatch(name)
                    if match is None:
                        continue
                    payload = _read_json(source_zip, name)
                    recent = (
                        payload.get("filings", {}).get("recent", {})
                        if "-submissions-" not in name
                        else payload
                    )
                    filings += _write_filings(writer, match.group("cik"), recent)
                text_file.flush()
        partial.replace(output)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise

    return {"registrants": registrants, "filings": filings}


class _TextWriter:
    """Minimal text adapter that does not close its ZipFile member."""

    def __init__(self, binary_file: Any) -> None:
        self.binary_file = binary_file

    def write(self, value: str) -> int:
        content = value.encode("utf-8")
        self.binary_file.write(content)
        return len(value)

    def flush(self) -> None:
        pass


def _read_json(archive: ZipFile, name: str) -> dict[str, Any]:
    try:
        with archive.open(name) as file:
            payload = json.load(file)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InvalidSecSubmissionError(f"cannot read SEC member {name}") from error
    if not isinstance(payload, dict):
        raise InvalidSecSubmissionError(f"SEC member {name} is not an object")
    return payload


def _write_registrants(
    writer: csv.DictWriter, cik: str, payload: dict[str, Any]
) -> int:
    tickers = payload.get("tickers", [])
    exchanges = payload.get("exchanges", [])
    if not isinstance(tickers, list) or not isinstance(exchanges, list):
        raise InvalidSecSubmissionError(f"invalid registrant arrays for CIK {cik}")
    if len(tickers) != len(exchanges):
        raise InvalidSecSubmissionError(f"ticker/exchange mismatch for CIK {cik}")
    for ticker, exchange in zip(tickers, exchanges, strict=True):
        writer.writerow(
            {
                "cik": cik,
                "ticker": ticker,
                "exchange": exchange,
                "company_name": payload.get("name", ""),
            }
        )
    return len(tickers)


def _write_filings(writer: csv.DictWriter, cik: str, filings: object) -> int:
    if not isinstance(filings, dict):
        raise InvalidSecSubmissionError(f"invalid filing arrays for CIK {cik}")
    forms = filings.get("form", [])
    if not isinstance(forms, list):
        raise InvalidSecSubmissionError(f"invalid filing forms for CIK {cik}")
    source_fields = {
        "accession_number": "accessionNumber",
        "filing_date": "filingDate",
        "report_date": "reportDate",
        "accepted_at": "acceptanceDateTime",
        "primary_document": "primaryDocument",
    }
    arrays: dict[str, list[Any]] = {}
    for destination, source in source_fields.items():
        values = filings.get(source, [])
        if not isinstance(values, list) or len(values) != len(forms):
            raise InvalidSecSubmissionError(
                f"inconsistent {source} array for CIK {cik}"
            )
        arrays[destination] = values

    written = 0
    for index, form in enumerate(forms):
        if form not in ANNUAL_AND_QUARTERLY_FORMS:
            continue
        row = {"cik": cik, "form": form}
        row.update({name: values[index] for name, values in arrays.items()})
        writer.writerow(row)
        written += 1
    return written
