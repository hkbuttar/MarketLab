"""Measure representative MarketLab runtime and peak-memory workloads."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from marketlab.performance.benchmark import (
    DEFAULT_WORKLOADS,
    EXPENSIVE_WORKLOADS,
    result_dict,
    run_workload,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/performance/pipeline_benchmark.json"),
    )
    parser.add_argument(
        "--workload",
        choices=(*DEFAULT_WORKLOADS, *EXPENSIVE_WORKLOADS),
        action="append",
    )
    parser.add_argument("--include-expensive", action="store_true")
    parser.add_argument(
        "--worker",
        choices=(*DEFAULT_WORKLOADS, *EXPENSIVE_WORKLOADS),
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()
    root = args.root.resolve()
    if args.worker:
        print(json.dumps(result_dict(run_workload(args.worker, root)), sort_keys=True))
        return 0

    workloads = args.workload or list(DEFAULT_WORKLOADS)
    if args.include_expensive and not args.workload:
        workloads.extend(EXPENSIVE_WORKLOADS)
    results = []
    for name in workloads:
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--root",
            str(root),
            "--worker",
            name,
        ]
        completed = subprocess.run(command, capture_output=True, text=True)
        if completed.returncode:
            message = completed.stderr.strip() or (
                "worker exited without an error message"
            )
            raise RuntimeError(f"benchmark workload {name!r} failed:\n{message}")
        result = json.loads(completed.stdout)
        results.append(result)
        duration = result["elapsed_seconds"]
        memory = result["peak_rss_mb"]
        print(f"{name}: {duration:.2f}s, {memory:.1f} MiB peak RSS")

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "machine": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "logical_cpus": os.cpu_count(),
        },
        "scope": "Measured locally; results are not scalability guarantees.",
        "results": results,
    }
    output = root / args.output if not args.output.is_absolute() else args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(f"{output.name}.part")
    partial.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    partial.replace(output)
    print(f"Benchmark report: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
