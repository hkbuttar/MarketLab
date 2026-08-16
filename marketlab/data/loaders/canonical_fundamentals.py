"""Create canonical filing-aware fundamentals from processed SEC indexes."""

import csv
import gzip
import io
import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from zipfile import ZipFile

from marketlab.data.schemas import FUNDAMENTAL_COLUMNS

CONCEPT_METRICS = {
    "Assets": "assets",
    "EntityCommonStockSharesOutstanding": "shares_outstanding",
    "CommonStockSharesOutstanding": "shares_outstanding",
    "WeightedAverageNumberOfDilutedSharesOutstanding": "shares_outstanding",
    "StockholdersEquity": "book_value",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": (
        "book_value"
    ),
    "NetIncomeLoss": "net_income",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "revenue",
    "Revenues": "revenue",
    "SalesRevenueNet": "revenue",
    "GrossProfit": "gross_profit",
    "NetCashProvidedByUsedInOperatingActivities": "operating_cash_flow",
    "PaymentsToAcquirePropertyPlantAndEquipment": "capital_expenditure",
}
CONCEPT_PRIORITY = {
    "RevenueFromContractWithCustomerExcludingAssessedTax": 0,
    "Revenues": 1,
    "SalesRevenueNet": 2,
    "EntityCommonStockSharesOutstanding": 0,
    "CommonStockSharesOutstanding": 1,
    "WeightedAverageNumberOfDilutedSharesOutstanding": 2,
    "StockholdersEquity": 0,
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": 1,
}
DEBT_CONCEPTS = {"DebtCurrent", "LongTermDebtCurrent", "LongTermDebtNoncurrent"}


def build_canonical_fundamentals(
    companyfacts_index: Path,
    submissions_index: Path,
    output: Path,
    crosswalk: Path | None = None,
) -> dict[str, int]:
    """Stream one canonical row per mapped ticker and SEC filing period."""

    if output.exists():
        raise FileExistsError(f"canonical fundamentals already exist: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(f"{output.name}.part")
    if partial.exists():
        raise FileExistsError(f"partial canonical fundamentals exist: {partial}")

    tickers, filings = _load_submission_context(submissions_index)
    securities = _load_crosswalk(crosswalk) if crosswalk else _undated(tickers)
    rows = 0
    entities = 0
    unmapped_entities = 0
    try:
        with (
            gzip.open(partial, "wt", encoding="utf-8", newline="") as output_file,
            ZipFile(companyfacts_index) as archive,
            archive.open("facts.csv") as binary_file,
            io.TextIOWrapper(binary_file, encoding="utf-8", newline="") as input_file,
        ):
            writer = csv.DictWriter(output_file, fieldnames=FUNDAMENTAL_COLUMNS)
            writer.writeheader()
            current_cik = ""
            entity_rows: list[dict[str, str]] = []
            for fact in csv.DictReader(input_file):
                cik = fact["cik"]
                if current_cik and cik != current_cik:
                    written = _write_entity(
                        writer, current_cik, entity_rows, securities, filings
                    )
                    rows += written
                    entities += 1
                    unmapped_entities += int(current_cik not in securities)
                    entity_rows = []
                current_cik = cik
                entity_rows.append(fact)
            if current_cik:
                written = _write_entity(
                    writer, current_cik, entity_rows, securities, filings
                )
                rows += written
                entities += 1
                unmapped_entities += int(current_cik not in securities)
        partial.replace(output)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise

    result = {
        "entities": entities,
        "unmapped_entities": unmapped_entities,
        "rows": rows,
    }
    metadata = output.with_suffix(output.suffix + ".metadata.json")
    metadata.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def _load_submission_context(
    path: Path,
) -> tuple[dict[str, list[str]], dict[str, tuple[str, str]]]:
    tickers: dict[str, list[str]] = defaultdict(list)
    filings: dict[str, tuple[str, str]] = {}
    with ZipFile(path) as archive:
        with (
            archive.open("registrants.csv") as binary_file,
            io.TextIOWrapper(binary_file, encoding="utf-8", newline="") as file,
        ):
            for row in csv.DictReader(file):
                tickers[row["cik"]].append(row["ticker"])
        with (
            archive.open("filings.csv") as binary_file,
            io.TextIOWrapper(binary_file, encoding="utf-8", newline="") as file,
        ):
            for row in csv.DictReader(file):
                filings[row["accession_number"]] = (
                    row["report_date"],
                    row["accepted_at"] or row["filing_date"],
                )
    return dict(tickers), filings


def _load_crosswalk(path: Path) -> dict[str, list[tuple[str, str, str]]]:
    securities: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if not row["cik"] or row["conflict"] == "true":
                continue
            securities[row["cik"]].add(
                (row["symbol"], row["listing_start"], row["listing_end"])
            )
    return {cik: sorted(intervals) for cik, intervals in securities.items()}


def _undated(tickers: dict[str, list[str]]) -> dict[str, list[tuple[str, str, str]]]:
    return {
        cik: [(symbol, "", "") for symbol in symbols]
        for cik, symbols in tickers.items()
    }


def _write_entity(
    writer: csv.DictWriter,
    cik: str,
    facts: list[dict[str, str]],
    securities: dict[str, list[tuple[str, str, str]]],
    filings: dict[str, tuple[str, str]],
) -> int:
    intervals = securities.get(cik, [])
    if not intervals:
        return 0
    groups: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)
    for fact in facts:
        accession = fact["accession_number"]
        filing = filings.get(accession)
        if filing is None or fact["period_end"] != filing[0]:
            continue
        key = (
            accession,
            fact["fiscal_year"],
            fact["fiscal_period"],
            fact["form"],
        )
        groups[key].append(fact)

    written = 0
    for (accession, fiscal_year, fiscal_period, _form), group in groups.items():
        report_date, available_at = filings[accession]
        values = _canonical_values(group)
        for symbol in _symbols_on_date(intervals, report_date):
            writer.writerow(
                {
                    "symbol": symbol,
                    "fiscal_period": f"{fiscal_year}-{fiscal_period}",
                    "report_date": report_date,
                    "available_date": _iso_datetime(available_at),
                    "market_cap": "",
                    "book_value": values.get("book_value", ""),
                    "net_income": values.get("net_income", ""),
                    "revenue": values.get("revenue", ""),
                    "gross_profit": values.get("gross_profit", ""),
                    "assets": values.get("assets", ""),
                    "debt": values.get("debt", ""),
                    "free_cash_flow": values.get("free_cash_flow", ""),
                    "shares_outstanding": values.get("shares_outstanding", ""),
                }
            )
            written += 1
    return written


def _symbols_on_date(
    intervals: list[tuple[str, str, str]], report_date: str
) -> list[str]:
    return sorted(
        {
            symbol
            for symbol, start, end in intervals
            if (not start or start <= report_date) and (not end or report_date <= end)
        }
    )


def _canonical_values(facts: list[dict[str, str]]) -> dict[str, float]:
    candidates: dict[str, list[tuple[int, int, float]]] = defaultdict(list)
    debt: dict[str, float] = {}
    for fact in facts:
        concept = fact["concept"]
        try:
            value = float(fact["value"])
        except ValueError:
            continue
        if concept in DEBT_CONCEPTS:
            debt[concept] = value
            continue
        metric = CONCEPT_METRICS.get(concept)
        if metric is None:
            continue
        duration = _duration_days(fact["period_start"], fact["period_end"])
        priority = CONCEPT_PRIORITY.get(concept, 0)
        candidates[metric].append((priority, duration, value))

    result = {
        metric: sorted(options, key=lambda option: (option[0], option[1]))[0][2]
        for metric, options in candidates.items()
    }
    if "DebtCurrent" in debt:
        result["debt"] = debt["DebtCurrent"] + debt.get("LongTermDebtNoncurrent", 0)
    elif debt:
        result["debt"] = debt.get("LongTermDebtCurrent", 0) + debt.get(
            "LongTermDebtNoncurrent", 0
        )
    if "operating_cash_flow" in result and "capital_expenditure" in result:
        result["free_cash_flow"] = (
            result["operating_cash_flow"] - result["capital_expenditure"]
        )
    return result


def _duration_days(start: str, end: str) -> int:
    if not start:
        return 0
    try:
        return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).days
    except ValueError:
        return 999_999


def _iso_datetime(value: str) -> str:
    if len(value) == 14 and value.isdigit():
        parsed = datetime.strptime(value, "%Y%m%d%H%M%S").replace(tzinfo=UTC)
        return parsed.isoformat().replace("+00:00", "Z")
    if len(value) == 10:
        return f"{value}T23:59:59Z"
    return value
