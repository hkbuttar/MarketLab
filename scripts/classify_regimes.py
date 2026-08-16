"""Classify daily SPY trend and volatility regimes."""

from pathlib import Path

from marketlab.regimes import build_regime_dataset


def main() -> int:
    output = Path("data/features/regimes/daily_regimes.csv")
    metadata = build_regime_dataset(
        Path("data/processed/prices/prices_clean.csv.gz"), output
    )
    print(f"Wrote {metadata['observations']:,} regimes to {output}")
    for regime, count in metadata["regime_counts"].items():
        print(regime, f"{count:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
