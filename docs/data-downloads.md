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
