"""Kenneth French Data Library factor-return downloader."""

import csv
import gzip
import io
import zipfile
from pathlib import Path

import httpx

FIVE_FACTOR_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Research_Data_5_Factors_2x3_daily_CSV.zip"
)
MOMENTUM_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Momentum_Factor_daily_CSV.zip"
)
FACTOR_COLUMNS = (
    "date",
    "market_excess",
    "size",
    "value",
    "profitability",
    "investment",
    "momentum",
    "risk_free",
)


def download_french_factors(output: Path, timeout: float = 60.0) -> int:
    """Download, align, and atomically save daily U.S. six-factor returns."""

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        five_response = client.get(FIVE_FACTOR_URL)
        five_response.raise_for_status()
        momentum_response = client.get(MOMENTUM_URL)
        momentum_response.raise_for_status()
    five = parse_factor_zip(five_response.content)
    momentum = parse_factor_zip(momentum_response.content)
    dates = sorted(set(five) & set(momentum))
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(f"{output.name}.part")
    with gzip.open(partial, "wt", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FACTOR_COLUMNS)
        writer.writeheader()
        for date in dates:
            row = five[date]
            writer.writerow(
                {
                    "date": _iso_date(date),
                    "market_excess": row["Mkt-RF"] / 100.0,
                    "size": row["SMB"] / 100.0,
                    "value": row["HML"] / 100.0,
                    "profitability": row["RMW"] / 100.0,
                    "investment": row["CMA"] / 100.0,
                    "momentum": momentum[date]["Mom"] / 100.0,
                    "risk_free": row["RF"] / 100.0,
                }
            )
    partial.replace(output)
    return len(dates)


def parse_factor_zip(content: bytes) -> dict[str, dict[str, float]]:
    """Parse the daily section of a French Data Library CSV archive."""

    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(names) != 1:
            raise ValueError("factor archive must contain exactly one CSV")
        text = archive.read(names[0]).decode("utf-8-sig")
    lines = text.splitlines()
    header_index = next(
        (index for index, line in enumerate(lines) if line.lstrip().startswith(",")),
        None,
    )
    if header_index is None:
        raise ValueError("factor CSV header is unavailable")
    reader = csv.DictReader(lines[header_index:])
    result: dict[str, dict[str, float]] = {}
    date_column = reader.fieldnames[0] if reader.fieldnames else ""
    for row in reader:
        date = row.get(date_column, "").strip()
        if len(date) != 8 or not date.isdigit():
            continue
        result[date] = {
            key.strip(): float(value.strip())
            for key, value in row.items()
            if key != date_column and key is not None and value and value.strip()
        }
    if not result:
        raise ValueError("factor archive contains no daily observations")
    return result


def _iso_date(value: str) -> str:
    return f"{value[:4]}-{value[4:6]}-{value[6:]}"
