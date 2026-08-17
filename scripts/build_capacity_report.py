"""Build persisted strategy-capacity diagnostics."""

from pathlib import Path

from marketlab.validation.capacity_report import build_capacity_report


def main() -> int:
    report = build_capacity_report(
        Path("data/features/portfolios/monthly_targets.csv.gz"),
        Path("data/features/factors/monthly_panel_investable.csv.gz"),
        Path("reports/validation/capacity.json"),
    )
    print(f"Strategies: {len(report['strategies'])}")
    print("Report: reports/validation/capacity.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
