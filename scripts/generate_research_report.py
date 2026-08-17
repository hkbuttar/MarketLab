"""Generate Markdown and HTML research reports for a completed backtest."""

import argparse

from backend.services.reports import generate_backtest_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_id")
    args = parser.parse_args()
    for report in generate_backtest_report(args.experiment_id):
        print(f"Report: reports/{report.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
