"""Build an evidence-preserving ticker-to-CIK crosswalk."""

import csv
import gzip
import io
import json
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

from scripts.download_v1_v2_data import is_common_equity

CROSSWALK_COLUMNS = (
    "symbol",
    "cik",
    "company_name",
    "exchange",
    "listing_start",
    "listing_end",
    "status",
    "source",
    "conflict",
)


def build_security_crosswalk(
    *, raw_root: Path, submissions_index: Path, output: Path
) -> dict[str, int]:
    """Combine listing, overview, and SEC registrant evidence atomically."""

    if output.exists():
        raise FileExistsError(f"security crosswalk already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(f"{output.name}.part")
    if partial.exists():
        raise FileExistsError(f"partial security crosswalk exists: {partial}")

    listings = _load_listings(raw_root)
    overview = _load_overview_mappings(raw_root)
    sec = _load_sec_mappings(submissions_index)
    rows = 0
    mapped_symbols = 0
    conflicts = 0
    try:
        with gzip.open(partial, "wt", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=CROSSWALK_COLUMNS)
            writer.writeheader()
            for symbol, listing in sorted(listings.items()):
                evidence: dict[str, set[str]] = defaultdict(set)
                if symbol in overview:
                    evidence[overview[symbol]].add("alpha_vantage_overview")
                for cik in sec.get(symbol, set()):
                    evidence[cik].add("sec_submissions")
                conflict = len(evidence) > 1
                conflicts += int(conflict)
                mapped_symbols += int(bool(evidence))
                if not evidence:
                    evidence[""].add("alpha_vantage_listing")
                for cik, sources in sorted(evidence.items()):
                    writer.writerow(
                        {
                            "symbol": symbol,
                            "cik": cik,
                            "company_name": listing["name"],
                            "exchange": listing["exchange"],
                            "listing_start": _null_to_empty(listing["ipoDate"]),
                            "listing_end": _null_to_empty(listing["delistingDate"]),
                            "status": listing["status"],
                            "source": "+".join(sorted(sources)),
                            "conflict": str(conflict).lower(),
                        }
                    )
                    rows += 1
        partial.replace(output)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise

    result = {
        "symbols": len(listings),
        "mapped_symbols": mapped_symbols,
        "conflicts": conflicts,
        "rows": rows,
    }
    metadata = output.with_suffix(output.suffix + ".metadata.json")
    metadata.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def _load_listings(raw_root: Path) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for state in ("delisted", "active"):
        stem = f"listings_{state}"
        paths = sorted(
            (raw_root / "reference" / "alpha_vantage" / stem).glob(f"*/{stem}.csv")
        )
        if not paths:
            raise FileNotFoundError(f"no {state} listing snapshot found")
        with paths[-1].open(encoding="utf-8-sig", newline="") as file:
            for row in csv.DictReader(file):
                symbol = row["symbol"].strip().upper()
                if is_common_equity(symbol, row["name"], row["assetType"]):
                    result[symbol] = row
    return result


def _load_overview_mappings(raw_root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    root = raw_root / "fundamentals" / "alpha_vantage"
    for directory in root.glob("*_overview"):
        paths = sorted(directory.glob(f"*/{directory.name}.json"))
        if not paths:
            continue
        try:
            payload = json.loads(paths[-1].read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        symbol = str(payload.get("Symbol", "")).strip().upper()
        cik = _normalize_cik(payload.get("CIK"))
        if symbol and cik:
            result[symbol] = cik
    return result


def _load_sec_mappings(path: Path) -> dict[str, set[str]]:
    result: dict[str, set[str]] = defaultdict(set)
    with ZipFile(path) as archive:
        with (
            archive.open("registrants.csv") as binary_file,
            io.TextIOWrapper(binary_file, encoding="utf-8", newline="") as file,
        ):
            for row in csv.DictReader(file):
                result[row["ticker"].strip().upper()].add(row["cik"])
    return dict(result)


def _normalize_cik(value: object) -> str:
    text = str(value or "").strip()
    return text.zfill(10) if text.isdigit() else ""


def _null_to_empty(value: str) -> str:
    return "" if value in {"", "null"} else value
