"""Point-in-time cross-sectional machine-learning datasets."""

import csv
import gzip
import json
from collections import defaultdict, deque
from pathlib import Path

from marketlab.factors.ranking import percentile_ranks
from marketlab.features.preprocessing.investable import INVESTABLE_COLUMNS

FEATURE_COLUMNS = (
    "momentum",
    "volatility",
    "trend",
    "reversal",
    "liquidity",
    "value",
    "quality",
    "profitability",
)
ML_DATASET_COLUMNS = (
    "date",
    "symbol",
    *FEATURE_COLUMNS,
    *(f"{feature}_missing" for feature in FEATURE_COLUMNS),
    "target_return_rank",
    "forward_return_21",
)


def build_ml_dataset(source: Path, output: Path) -> dict[str, object]:
    """Build ranked features and forward-return target without temporal leakage."""

    if output.exists():
        raise FileExistsError(f"ML dataset already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(f"{output.name}.part")
    histories: dict[str, deque[float]] = defaultdict(lambda: deque(maxlen=3))
    missing = {feature: 0 for feature in FEATURE_COLUMNS}
    row_count = 0
    dates: list[str] = []
    try:
        with (
            gzip.open(source, "rt", encoding="utf-8", newline="") as input_file,
            gzip.open(partial, "wt", encoding="utf-8", newline="") as output_file,
        ):
            reader = csv.DictReader(input_file)
            if reader.fieldnames != list(INVESTABLE_COLUMNS):
                raise ValueError("investable panel columns are not canonical")
            writer = csv.DictWriter(output_file, fieldnames=ML_DATASET_COLUMNS)
            writer.writeheader()
            current_date = ""
            rows: list[dict[str, str]] = []
            for row in reader:
                if current_date and row["date"] != current_date:
                    written = _process_date(rows, histories, writer, missing)
                    if written:
                        dates.append(current_date)
                    row_count += written
                    rows = []
                current_date = row["date"]
                rows.append(row)
            if rows:
                written = _process_date(rows, histories, writer, missing)
                if written:
                    dates.append(current_date)
                row_count += written
        partial.replace(output)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    metadata: dict[str, object] = {
        "rows": row_count,
        "dates": len(dates),
        "start_date": dates[0] if dates else "",
        "end_date": dates[-1] if dates else "",
        "features": list(FEATURE_COLUMNS),
        "target": (
            "cross-sectional percentile rank of winsorized forward " "21-session return"
        ),
        "missing_rates": {
            feature: count / row_count if row_count else 0.0
            for feature, count in missing.items()
        },
    }
    metadata_path = output.with_suffix(output.suffix + ".metadata.json")
    metadata_partial = metadata_path.with_name(f"{metadata_path.name}.part")
    metadata_partial.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    metadata_partial.replace(metadata_path)
    return metadata


def _process_date(
    rows: list[dict[str, str]],
    histories: dict[str, deque[float]],
    writer: csv.DictWriter,
    missing: dict[str, int],
) -> int:
    eligible = [row for row in rows if row["forward_return_21"]]
    if not eligible:
        for row in rows:
            histories[row["symbol"]].append(float(row["close"]))
        return 0
    raw: dict[str, list[float | None]] = {feature: [] for feature in FEATURE_COLUMNS}
    targets = [float(row["forward_return_21"]) for row in eligible]
    for row in eligible:
        history = histories[row["symbol"]]
        close = float(row["close"])
        momentum = _float(row["momentum_12_1_rank"])
        volatility = _float(row["volatility_63_rank"])
        trend = close / history[0] - 1.0 if len(history) == 3 else None
        reversal = -(close / history[-1] - 1.0) if history else None
        liquidity = float(row["average_dollar_volume_21"])
        book = _float(row["book_to_market_rank"])
        earnings = _float(row["earnings_yield_rank"])
        value = (
            (book + earnings) / 2.0
            if book is not None and earnings is not None
            else None
        )
        asset_growth = _float(row["asset_growth_yoy_rank"])
        profitability = _float(row["gross_profitability_rank"])
        values = {
            "momentum": momentum,
            "volatility": volatility,
            "trend": trend,
            "reversal": reversal,
            "liquidity": liquidity,
            "value": value,
            "quality": 1.0 - asset_growth if asset_growth is not None else None,
            "profitability": profitability,
        }
        for feature, value in values.items():
            raw[feature].append(value)
    ranked = {
        feature: (
            values
            if feature
            in {"momentum", "volatility", "value", "quality", "profitability"}
            else percentile_ranks(values)
        )
        for feature, values in raw.items()
    }
    target_ranks = percentile_ranks(targets)
    for index, row in enumerate(eligible):
        output: dict[str, object] = {
            "date": row["date"],
            "symbol": row["symbol"],
            "target_return_rank": target_ranks[index],
            "forward_return_21": row["forward_return_21"],
        }
        for feature in FEATURE_COLUMNS:
            value = ranked[feature][index]
            output[feature] = "" if value is None else value
            output[f"{feature}_missing"] = int(value is None)
            missing[feature] += int(value is None)
        writer.writerow(output)
    for row in rows:
        histories[row["symbol"]].append(float(row["close"]))
    return len(eligible)


def _float(value: str) -> float | None:
    return float(value) if value else None
