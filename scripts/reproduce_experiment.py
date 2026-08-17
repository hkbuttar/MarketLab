"""Reproduce a registered MarketLab experiment."""

import argparse
from pathlib import Path

from marketlab.experiments.reproduction import (
    find_manifest,
    load_manifest,
    reproduce,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", help="Run ID or path to an experiment manifest")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify code and inputs without rerunning",
    )
    parser.add_argument(
        "--allow-code-change",
        action="store_true",
        help="Permit a non-exact rerun from a different or dirty Git revision",
    )
    arguments = parser.parse_args()
    root = Path.cwd()
    path = find_manifest(arguments.run, root / "experiments")
    manifest = load_manifest(path)
    reproduce(
        manifest,
        root,
        verify_only=arguments.verify_only,
        allow_code_change=arguments.allow_code_change,
    )
    action = "Verified" if arguments.verify_only else "Reproduced"
    print(f"{action} experiment {manifest['run_id']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
