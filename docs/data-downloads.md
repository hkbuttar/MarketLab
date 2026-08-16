# Raw data downloads

MarketLab stores immutable provider responses under `data/raw/`. Each snapshot
includes the exact response bytes and a JSON sidecar containing its source,
download time, row count, and date range. Canonical renaming and type conversion
happen later in loaders, never in downloaders.

## Provider configuration

The initial deployment-safe adapter uses Alpha Vantage's documented HTTPS API.
Copy `.env.example` to `.env`, obtain an API key from Alpha Vantage, and export
the key before running a download:

```bash
export ALPHA_VANTAGE_API_KEY="your-key"
```

The canonical schema needs both as-traded OHLCV and adjusted close. Alpha
Vantage supplies those fields through `TIME_SERIES_DAILY_ADJUSTED`, which is a
premium endpoint. Provider access and data licensing remain deployment
configuration concerns rather than assumptions embedded in research code.

## Daily prices

Download equities and benchmark ETFs with:

```bash
python scripts/download_prices.py AAPL MSFT SPY QQQ IWM
```

A run creates one immutable timestamped snapshot per symbol:

```text
data/raw/prices/alpha_vantage/SPY/<downloaded-at>/SPY.json
data/raw/prices/alpha_vantage/SPY/<downloaded-at>/SPY.metadata.json
```

Downloaded data is ignored by Git. The `.gitkeep` files preserve the expected
directory layout without committing datasets.

Fundamental and reference adapters remain separate because historical
fundamentals require trustworthy publication or availability dates. They must
not be inferred from a current company snapshot.

## Complete V1/V2 acquisition

After loading `.env`, run a small end-to-end provider test:

```bash
python scripts/download_v1_v2_data.py --max-symbols 5
```

The complete active-and-delisted U.S. common-equity run is resumable:

```bash
python scripts/download_v1_v2_data.py
```

It stays below a 75-request/minute subscription by defaulting to 70 requests per
minute. Rerunning skips existing symbol/endpoint snapshots and records failures
in a manifest under `data/raw/`. Alpha Vantage categorizes preferred shares,
warrants, rights, and units as `Stock`; MarketLab excludes those instruments by
security name and symbol pattern while retaining legitimate common share classes.

## Filing-aware fundamentals

Alpha Vantage statements are useful normalized source data, but SEC filing dates
are the authoritative availability timestamps for U.S. issuers. Configure the
identifying user agent required by SEC fair-access policy:

```text
SEC_USER_AGENT=MarketLab your-email@example.com
```

Then download the nightly Company Facts and Submissions bulk archives:

```bash
python scripts/download_sec_bulk.py
```

These archives come directly from SEC EDGAR and require no API key. They are
large; the downloader streams them to `.part` files, verifies the ZIP signature,
checks advertised size against available disk space, and atomically finalizes
successful snapshots. Keep them out of Git and retain their raw ZIP snapshots.

## Processed prices

Test the canonical price pipeline on a small symbol subset first:

```bash
python scripts/process_prices.py --max-symbols 5 \
  --output data/processed/prices/prices_sample.csv.gz
```

Then build the complete gzip-compressed CSV dataset:

```bash
python scripts/process_prices.py
```

The processor selects the latest immutable snapshot for each intended common
equity and benchmark, normalizes it to the canonical price schema, and records
missing symbols in an adjacent metadata file. Output is streamed through a
`.part` file and finalized atomically so an interruption cannot masquerade as a
complete dataset.

## Data still requiring a licensed source

Alpha Vantage `OVERVIEW` provides current sector and industry labels, not a
point-in-time classification history. Research that requires historically exact
GICS membership needs a licensed classification dataset such as S&P Capital IQ,
Compustat, or another vendor with effective dates. Until then, MarketLab must
label sector-neutral historical results with that limitation.
