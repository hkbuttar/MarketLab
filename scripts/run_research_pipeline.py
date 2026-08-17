"""Run or inspect the resumable end-to-end MarketLab research pipeline."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from marketlab.pipeline import STAGES, run_tasks, select_tasks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-at", choices=STAGES, default=STAGES[0])
    parser.add_argument("--through", choices=STAGES, default=STAGES[-1])
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()
    root = Path.cwd()
    records = run_tasks(
        select_tasks(start_at=arguments.start_at, through=arguments.through),
        root,
        dry_run=arguments.dry_run,
    )
    for record in records:
        print(f"[{record['status']:^9}] {record['stage']}: {record['task']}")
    if arguments.dry_run:
        return 0
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    destination = root / "experiments/pipeline_runs" / f"{timestamp}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_at": datetime.now(UTC).isoformat(),
        "start_at": arguments.start_at,
        "through": arguments.through,
        "tasks": records,
    }
    partial = destination.with_name(f"{destination.name}.part")
    partial.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    partial.replace(destination)
    print(f"Pipeline manifest: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
