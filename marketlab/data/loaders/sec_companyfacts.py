"""Index selected SEC Company Facts with point-in-time availability."""

import csv
import io
import json
import re
from pathlib import Path
from typing import Any
from zipfile import ZIP_DEFLATED, ZipFile

from marketlab.data.loaders.sec_submissions import ANNUAL_AND_QUARTERLY_FORMS

CIK_FILE = re.compile(r"^CIK(?P<cik>\d{10})\.json$")
SELECTED_CONCEPTS = {
    "Assets",
    "CashAndCashEquivalentsAtCarryingValue",
    "CommonStockSharesOutstanding",
    "DebtCurrent",
    "EarningsPerShareDiluted",
    "EntityCommonStockSharesOutstanding",
    "GrossProfit",
    "Liabilities",
    "LongTermDebtCurrent",
    "LongTermDebtNoncurrent",
    "NetCashProvidedByUsedInOperatingActivities",
    "NetIncomeLoss",
    "OperatingIncomeLoss",
    "PaymentsOfDividends",
    "PaymentsToAcquirePropertyPlantAndEquipment",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
    "StockholdersEquity",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
    "WeightedAverageNumberOfDilutedSharesOutstanding",
}
FACT_COLUMNS = (
    "cik",
    "taxonomy",
    "concept",
    "unit",
    "value",
    "period_start",
    "period_end",
    "fiscal_year",
    "fiscal_period",
    "form",
    "filed_date",
    "accepted_at",
    "available_at",
    "accession_number",
    "frame",
)


class InvalidCompanyFactsError(ValueError):
    """Raised when a selected SEC Company Facts member is malformed."""


def load_acceptance_times(submissions_index: Path) -> dict[str, str]:
    """Load accession-to-acceptance mappings from the submissions index."""

    result: dict[str, str] = {}
    with ZipFile(submissions_index) as archive:
        with (
            archive.open("filings.csv") as binary_file,
            io.TextIOWrapper(binary_file, encoding="utf-8", newline="") as file,
        ):
            for row in csv.DictReader(file):
                accession = row["accession_number"]
                accepted_at = row["accepted_at"]
                if accession and accepted_at:
                    result[accession] = accepted_at
    return result


def build_sec_companyfacts_index(
    source: Path, submissions_index: Path, output: Path
) -> dict[str, int]:
    """Write selected filing-aware facts without extracting the source ZIP."""

    if output.exists():
        raise FileExistsError(f"SEC Company Facts index already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(f"{output.name}.part")
    if partial.exists():
        raise FileExistsError(f"partial SEC Company Facts index exists: {partial}")

    acceptance_times = load_acceptance_times(submissions_index)
    entities = 0
    facts = 0
    try:
        with (
            ZipFile(source) as source_zip,
            ZipFile(
                partial, "x", compression=ZIP_DEFLATED, compresslevel=6
            ) as output_zip,
            output_zip.open("facts.csv", "w", force_zip64=True) as binary_file,
            io.TextIOWrapper(binary_file, encoding="utf-8", newline="") as file,
        ):
            writer = csv.DictWriter(file, fieldnames=FACT_COLUMNS)
            writer.writeheader()
            for name in source_zip.namelist():
                match = CIK_FILE.fullmatch(name)
                if match is None:
                    continue
                payload = _read_json(source_zip, name)
                facts += _write_selected_facts(
                    writer,
                    match.group("cik"),
                    payload,
                    acceptance_times,
                )
                entities += 1
        partial.replace(output)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise

    return {"entities": entities, "facts": facts}


def _read_json(archive: ZipFile, name: str) -> dict[str, Any]:
    try:
        with archive.open(name) as file:
            payload = json.load(file)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InvalidCompanyFactsError(f"cannot read SEC member {name}") from error
    if not isinstance(payload, dict):
        raise InvalidCompanyFactsError(f"SEC member {name} is not an object")
    return payload


def _write_selected_facts(
    writer: csv.DictWriter,
    cik: str,
    payload: dict[str, Any],
    acceptance_times: dict[str, str],
) -> int:
    taxonomies = payload.get("facts", {})
    if not isinstance(taxonomies, dict):
        raise InvalidCompanyFactsError(f"invalid facts object for CIK {cik}")
    written = 0
    for taxonomy, concepts in taxonomies.items():
        if not isinstance(concepts, dict):
            continue
        for concept, definition in concepts.items():
            if concept not in SELECTED_CONCEPTS or not isinstance(definition, dict):
                continue
            units = definition.get("units", {})
            if not isinstance(units, dict):
                raise InvalidCompanyFactsError(
                    f"invalid units for CIK {cik} concept {concept}"
                )
            for unit, observations in units.items():
                if not isinstance(observations, list):
                    raise InvalidCompanyFactsError(
                        f"invalid observations for CIK {cik} concept {concept}"
                    )
                for observation in observations:
                    if not isinstance(observation, dict):
                        continue
                    form = observation.get("form", "")
                    if form not in ANNUAL_AND_QUARTERLY_FORMS:
                        continue
                    accession = str(observation.get("accn", ""))
                    filed_date = str(observation.get("filed", ""))
                    accepted_at = acceptance_times.get(accession, "")
                    writer.writerow(
                        {
                            "cik": cik,
                            "taxonomy": taxonomy,
                            "concept": concept,
                            "unit": unit,
                            "value": observation.get("val", ""),
                            "period_start": observation.get("start", ""),
                            "period_end": observation.get("end", ""),
                            "fiscal_year": observation.get("fy", ""),
                            "fiscal_period": observation.get("fp", ""),
                            "form": form,
                            "filed_date": filed_date,
                            "accepted_at": accepted_at,
                            "available_at": accepted_at or filed_date,
                            "accession_number": accession,
                            "frame": observation.get("frame", ""),
                        }
                    )
                    written += 1
    return written
