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

## SEC submissions index

Build the ticker-to-CIK mapping and point-in-time 10-K/10-Q filing index without
extracting the large submissions archive:

```bash
python scripts/process_sec_submissions.py
```

The resulting `data/processed/sec/submissions_index.zip` contains compressed
`registrants.csv` and `filings.csv` members. Filing acceptance timestamps are
retained so later fundamental joins can enforce historical availability.

## SEC Company Facts index

After building the submissions index, process the selected accounting concepts:

```bash
python scripts/process_sec_companyfacts.py
```

This reads `companyfacts.zip` directly and writes
`data/processed/sec/companyfacts_index.zip`. Each selected fact retains its
period, form, accession number, filing date, and exact acceptance timestamp when
available. The filing date is used as a conservative fallback for older records
without an acceptance timestamp.

## Canonical fundamentals

Create the canonical filing-aware fundamental table from both SEC indexes:

```bash
python scripts/process_fundamentals.py
```

The output is streamed to
`data/processed/fundamentals/fundamentals_point_in_time.csv.gz`. It maps SEC
registrants through the dated security crosswalk, excludes unresolved mapping
conflicts, selects consistent accounting concepts, aggregates debt, and
calculates free cash flow as operating cash flow less capital expenditure.
Market capitalization remains empty until prices and shares are joined.

## Security crosswalk

Build a ticker-to-CIK crosswalk from the latest Alpha Vantage listings, overview
CIKs, and SEC registrant mappings:

```bash
python scripts/process_security_crosswalk.py
```

The output at `data/processed/reference/security_crosswalk.csv.gz` retains IPO
and delisting dates from the listing source. Conflicting provider mappings are
written as separate evidence rows with `conflict=true`; they are never resolved
silently.

## Processed-data validation

Run the complete streaming validation after generating prices and point-in-time
fundamentals:

```bash
python scripts/validate_processed_data.py
```

The command checks canonical columns, price ordering and OHLC relationships,
duplicate fundamental keys, filing chronology, numeric validity, missingness,
and cross-dataset symbol coverage. It writes the complete result atomically to
`reports/data_validation.json` and exits nonzero when critical errors exist.

Quarantine invalid provider observations without modifying the original dataset:

```bash
python scripts/clean_prices.py
```

This writes research-safe observations to
`data/processed/prices/prices_clean.csv.gz` and preserves every rejected row,
with deterministic reason codes, in `reports/price_quarantine.csv.gz`.

## Point-in-time market capitalization

Join historically reported shares to the latest clean, unadjusted closing price
available on or before each filing timestamp:

```bash
python scripts/add_market_cap.py
```

The result is written to
`data/processed/fundamentals/fundamentals_valued.csv.gz`. Using the unadjusted
close with the historically reported share count preserves the economic market
capitalization at that time; no future trading date is used.

## Research features

Build daily technical features and filing-date fundamental ratios:

```bash
python scripts/build_features.py
```

Technical features include adjusted returns, 21/63/126/252-session momentum,
12-to-1 momentum, annualized 21/63-session volatility, and 21-session average
dollar volume. Fundamental features include valuation, profitability, leverage,
free-cash-flow ratios, and same-period year-over-year growth keyed to the
original availability timestamp. After quarterly normalization, rebuild only
the smaller fundamental feature file with:

```bash
python scripts/build_features.py --skip-technical
```

## Monthly factor research

Build month-end cross-sectional ranks, quintiles, forward 21-session returns,
and Spearman information coefficients:

```bash
python scripts/run_factor_research.py
```

Every cross-section is anchored to SPY's shared month-end trading calendar.
Fundamental features are joined only when their acceptance date precedes the
rebalance date. Yearly temporary staging keeps memory bounded and is removed
after the atomic panel and diagnostic outputs are finalized.

## Investable factor preprocessing

Apply a $5 minimum price, $1 million trailing 21-session average dollar-volume
screen, and cross-sectional 1st/99th percentile winsorization:

```bash
python scripts/preprocess_factor_research.py
```

The original factor panel remains unchanged. The investable panel and its IC and
quintile diagnostics use only exact shared month-end prices and winsorized
forward returns, while missing factor values remain missing rather than imputed.

## Factor tear sheet

Summarize IC consistency, rolling 12-month IC, quintile monotonicity and spreads,
top-quintile turnover, and average cross-sectional factor correlations:

```bash
python scripts/build_factor_tear_sheet.py
```

The resulting JSON and CSV diagnostics are written under `reports/factors/` and
are derived exclusively from the screened, winsorized investable panel.

## Monthly target portfolios

Construct momentum, low-volatility, and quality/value/momentum long-only target
portfolios:

```bash
python scripts/build_portfolios.py
```

Each strategy selects its top score quintile, remains fully invested, caps each
position at 5%, and limits one-way monthly turnover to 20%. Equal and
score-proportional weighting are both supported by the reusable constructor.

## Executable rebalance trades

Translate monthly target weights into next-session-open whole-share fills:

```bash
python scripts/generate_trades.py
```

The simulator sells before buying, enforces available cash, suppresses trades
below $1,000, exits residual targets below one basis point, caps each order at
10% of trailing dollar volume, and records commission, half-spread, and nonlinear
market-impact costs without using the signal-day close as an execution price.
Large discontinuities in the adjusted-to-unadjusted price factor are applied as
split multipliers before holdings are valued; small dividend-related adjustment
changes are deliberately ignored.

## Daily backtest valuation

Chain monthly targets into daily gross and net NAV using adjusted-price total
returns and realized execution costs:

```bash
python scripts/run_backtest.py
```

Targets activate on the next SPY session. Missing execution histories remain
cash; a security that delists during a holding period receives a one-time 70%
recovery of its last marked value. The engine records gross NAV, net NAV, daily
return, SPY benchmark NAV, and cumulative costs for each strategy. Exchange test
instruments identified by the security reference data are excluded from
valuation.

## Data still requiring a licensed source

Alpha Vantage `OVERVIEW` provides current sector and industry labels, not a
point-in-time classification history. Research that requires historically exact
GICS membership needs a licensed classification dataset such as S&P Capital IQ,
Compustat, or another vendor with effective dates. Until then, MarketLab must
label sector-neutral historical results with that limitation.
