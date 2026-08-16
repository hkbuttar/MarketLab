"""Run neighboring factor-window and selection-size sensitivity tests."""

from pathlib import Path

from marketlab.validation.sensitivity import run_parameter_sensitivity


def main() -> int:
    rows = run_parameter_sensitivity(
        Path("data/processed/prices/prices_clean.csv.gz"),
        Path("reports/validation/sensitivity"),
    )
    for row in rows:
        print(
            row["factor_family"],
            f"window={row['window_sessions']}",
            f"top={row['selection_fraction']:.0%}",
            f"return={row['annualized_return']:.2%}",
            f"Sharpe={row['sharpe']:.2f}",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
