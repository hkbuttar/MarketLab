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
            for row in reader:
                market_cap = _value(row["market_cap"])
                assets = _value(row["assets"])
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
                    }
                )
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
