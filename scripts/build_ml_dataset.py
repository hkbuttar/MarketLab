"""Build the point-in-time cross-sectional ML ranking dataset."""

from pathlib import Path

from marketlab.ml.dataset import build_ml_dataset


def main() -> int:
    output = Path("data/features/ml/cross_sectional_ranking.csv.gz")
    metadata = build_ml_dataset(
        Path("data/features/factors/monthly_panel_investable.csv.gz"), output
    )
    print(
        f"Wrote {metadata['rows']:,} rows across {metadata['dates']} dates to {output}"
    )
    print(f"Date range: {metadata['start_date']} to {metadata['end_date']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
