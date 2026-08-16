"""Point-in-time fundamental ratio features."""

import csv
import gzip
import json
from pathlib import Path

from marketlab.data.schemas import FUNDAMENTAL_COLUMNS

FUNDAMENTAL_FEATURE_COLUMNS = (
    "symbol",
    "fiscal_period",
    "report_date",
    "available_date",
    "book_to_market",
    "earnings_yield",
    "sales_to_price",
    "gross_profitability",
    "return_on_assets",
    "leverage",
    "free_cash_flow_yield",
    "revenue_growth_yoy",
    "net_income_growth_yoy",
    "asset_growth_yoy",
    "free_cash_flow_growth_yoy",
)


def build_fundamental_features(source: Path, output: Path) -> dict[str, int]:
    """Calculate ratios using only values known at each availability time."""

    if output.exists():
        raise FileExistsError(f"fundamental features already exist: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(f"{output.name}.part")
    rows = 0
    try:
        with (
            gzip.open(source, "rt", encoding="utf-8", newline="") as input_file,
            gzip.open(partial, "wt", encoding="utf-8", newline="") as output_file,
        ):
            reader = csv.DictReader(input_file)
            if reader.fieldnames != list(FUNDAMENTAL_COLUMNS):
                raise ValueError("fundamental columns do not match canonical schema")
            writer = csv.DictWriter(output_file, fieldnames=FUNDAMENTAL_FEATURE_COLUMNS)
            writer.writeheader()
            rows_to_process = list(reader)
            rows_to_process.sort(
                key=lambda row: (
                    row["symbol"],
                    row["report_date"],
                    row["available_date"],
                )
            )
            history: dict[tuple[str, int, str], dict[str, str]] = {}
            for row in rows_to_process:
                market_cap = _value(row["market_cap"])
                assets = _value(row["assets"])
                fiscal_year, period = _fiscal_period(row["fiscal_period"])
                prior = (
                    history.get((row["symbol"], fiscal_year - 1, period), {})
                    if fiscal_year is not None
                    else {}
                )
                writer.writerow(
                    {
                        "symbol": row["symbol"],
                        "fiscal_period": row["fiscal_period"],
                        "report_date": row["report_date"],
                        "available_date": row["available_date"],
                        "book_to_market": _ratio(row["book_value"], market_cap),
                        "earnings_yield": _ratio(row["net_income"], market_cap),
                        "sales_to_price": _ratio(row["revenue"], market_cap),
                        "gross_profitability": _ratio(row["gross_profit"], assets),
                        "return_on_assets": _ratio(row["net_income"], assets),
                        "leverage": _ratio(row["debt"], assets),
                        "free_cash_flow_yield": _ratio(
                            row["free_cash_flow"], market_cap
                        ),
                        "revenue_growth_yoy": _growth(
                            row["revenue"], prior.get("revenue", "")
                        ),
                        "net_income_growth_yoy": _growth(
                            row["net_income"], prior.get("net_income", "")
                        ),
                        "asset_growth_yoy": _growth(
                            row["assets"], prior.get("assets", "")
                        ),
                        "free_cash_flow_growth_yoy": _growth(
                            row["free_cash_flow"], prior.get("free_cash_flow", "")
                        ),
                    }
                )
                if fiscal_year is not None:
                    history[(row["symbol"], fiscal_year, period)] = row
                rows += 1
        partial.replace(output)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    result = {"rows": rows}
    output.with_suffix(output.suffix + ".metadata.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def _value(value: str) -> float | None:
    return float(value) if value else None


def _ratio(numerator: str, denominator: float | None) -> str:
    if not numerator or denominator in {None, 0}:
        return ""
    return format(float(numerator) / denominator, ".15g")


def _fiscal_period(value: str) -> tuple[int | None, str]:
    year, period = value.split("-", 1)
    return (int(year), period) if year.isdigit() else (None, period)


def _growth(current: str, prior: str) -> str:
    if not current or not prior:
        return ""
    previous = float(prior)
    if previous == 0:
        return ""
    return format((float(current) - previous) / abs(previous), ".15g")
