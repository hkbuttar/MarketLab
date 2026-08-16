"""Audited cleaning of invalid provider price observations."""

import csv
import gzip
import json
from collections import Counter
from pathlib import Path

from marketlab.data.schemas import PRICE_COLUMNS
from marketlab.data.validation.processed import price_row_issues

QUARANTINE_COLUMNS = (*PRICE_COLUMNS, "issues")


def clean_price_dataset(
    source: Path, output: Path, quarantine: Path
) -> dict[str, object]:
    """Copy valid prices and preserve invalid rows with reason codes."""

    for path in (output, quarantine):
        if path.exists():
            raise FileExistsError(f"cleaning output already exists: {path}")
        path.parent.mkdir(parents=True, exist_ok=True)
    output_partial = output.with_name(f"{output.name}.part")
    quarantine_partial = quarantine.with_name(f"{quarantine.name}.part")
    if output_partial.exists() or quarantine_partial.exists():
        raise FileExistsError("partial cleaning output already exists")

    total = 0
    accepted = 0
    rejected = 0
    reasons: Counter[str] = Counter()
    try:
        with (
            gzip.open(source, "rt", encoding="utf-8", newline="") as source_file,
            gzip.open(
                output_partial, "wt", encoding="utf-8", newline=""
            ) as output_file,
            gzip.open(
                quarantine_partial, "wt", encoding="utf-8", newline=""
            ) as quarantine_file,
        ):
            reader = csv.DictReader(source_file)
            if reader.fieldnames != list(PRICE_COLUMNS):
                raise ValueError("price columns do not match the canonical schema")
            writer = csv.DictWriter(output_file, fieldnames=PRICE_COLUMNS)
            rejected_writer = csv.DictWriter(
                quarantine_file, fieldnames=QUARANTINE_COLUMNS
            )
            writer.writeheader()
            rejected_writer.writeheader()
            for row in reader:
                total += 1
                issues = price_row_issues(row)
                if issues:
                    rejected += 1
                    reasons.update(issues)
                    rejected_writer.writerow({**row, "issues": ";".join(issues)})
                else:
                    accepted += 1
                    writer.writerow(row)
        output_partial.replace(output)
        quarantine_partial.replace(quarantine)
    except BaseException:
        output_partial.unlink(missing_ok=True)
        quarantine_partial.unlink(missing_ok=True)
        raise

    result: dict[str, object] = {
        "source_rows": total,
        "accepted_rows": accepted,
        "quarantined_rows": rejected,
        "reasons": dict(reasons),
    }
    metadata = output.with_suffix(output.suffix + ".metadata.json")
    metadata.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result
