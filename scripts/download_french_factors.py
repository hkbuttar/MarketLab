"""Download daily U.S. Fama-French five factors plus momentum."""

from pathlib import Path

from marketlab.data.downloaders.french import download_french_factors


def main() -> int:
    output = Path("data/raw/factors/french_daily.csv.gz")
    observations = download_french_factors(output)
    print(f"Wrote {observations:,} aligned factor observations to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
