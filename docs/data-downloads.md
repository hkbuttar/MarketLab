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

## Performance analytics

Build return, risk, drawdown, benchmark-relative, calendar-period, and realized
trading statistics from the daily backtest:

```bash
python scripts/build_performance_analytics.py
```

The command writes `reports/performance/performance_summary.json` and
`reports/performance/period_returns.csv`. Sharpe and Sortino default to a zero
risk-free rate; pass `--risk-free-rate 0.04`, for example, to use a constant 4%
annual assumption until the daily Treasury series is integrated.

## Factor attribution

Download the daily U.S. Fama-French five factors and momentum factor from the
Kenneth French Data Library, then regress net strategy returns on them:

```bash
python scripts/download_french_factors.py
python scripts/build_factor_attribution.py
```

The canonical factor file is stored under `data/raw/factors/`. The attribution
report at `reports/attribution/factor_regression.json` contains annualized alpha,
market, size, value, profitability, investment and momentum betas, classical
OLS standard errors, observation counts, and R-squared.

Build monthly sector weights, active weights against an ADV-weighted investable
universe proxy, rank-factor exposures, market beta, and concentration metrics:

```bash
python scripts/build_exposure_analysis.py
```

Outputs are written under `reports/attribution/`. Every summary records that
Alpha Vantage classifications are current labels without historical effective
dates; they are not represented as point-in-time GICS classifications.

## Market regimes

Classify SPY sessions into bull/bear and high/low-volatility states:

```bash
python scripts/classify_regimes.py
```

The classifier compares adjusted SPY price with its trailing 200-session mean
and 21-session realized volatility with the median of the preceding 252
volatility observations. The volatility threshold is lagged one session, so no
future observation affects an existing label. Results and methodology metadata
are written under `data/features/regimes/`.

Condition strategy results on those regimes:

```bash
python scripts/analyze_regimes.py
```

The report includes conditional CAGR, Sharpe ratio using the aligned daily
French risk-free series, hit rate, rebalance turnover, and the worst drawdown
inside a contiguous episode of each regime. CSV and JSON outputs are written to
`reports/regimes/`.

## Parameter sensitivity

Evaluate gross month-end factor portfolios across 6/9/12-month momentum,
20/40/60-session volatility, and top 10%/20%/30% selection sizes:

```bash
python scripts/run_parameter_sensitivity.py
```

The analysis recreates each neighboring factor directly from clean adjusted
prices, applies the standard price/liquidity screen and cross-sectional 1%/99%
winsorization, and reports every grid point without selecting a winner. Summary
and Sharpe heatmap CSVs are written under `reports/validation/sensitivity/`.

Replay realized gross strategy paths under 0, 5, 10, 25, and 50 bps all-in
cost assumptions:

```bash
python scripts/run_cost_sensitivity.py
```

Each scenario applies its fixed cost to realized traded notional instead of
stacking it on the baseline commission/spread/impact model. A strategy is
explicitly labeled economically attractive when its net CAGR is positive and
its net Sharpe is at least 0.5. Detailed and threshold summaries are written to
the sensitivity report directory.

## Bootstrap robustness

Estimate sampling uncertainty with a seeded 21-session moving-block bootstrap:

```bash
python scripts/run_bootstrap_analysis.py
```

The default 1,000 paired resamples preserve short-run return dependence and the
contemporaneous relationship between each strategy, SPY, and the daily
risk-free rate. The report includes 95% percentile intervals for CAGR, Sharpe,
Sortino, and maximum drawdown, plus `P(Sharpe > 0)` and
`P(CAGR > benchmark)`. Summary JSON and compressed samples are written under
`reports/validation/bootstrap/`.

## Multiple-testing adjustment

Adjust primary-strategy Sharpe evidence for every recorded parameter trial:

```bash
python scripts/run_deflated_sharpe.py
```

The Deflated Sharpe calculation records the 18 neighboring parameter variants
and three primary strategies as 21 trials. It estimates the expected maximum
Sharpe under repeated testing and adjusts each strategy using its observation
count, skewness, and kurtosis. The JSON report preserves raw Sharpe, adjusted
probability, evidence label, and number of trials at
`reports/validation/deflated_sharpe.json`.

## MarketLab robustness diagnostic

Combine five separately reported validation components into the internal score:

```bash
python scripts/build_robustness_scores.py
```

The weights are 30% chronological final-20% holdout performance, 20% cost
resilience, 20% parameter stability, 15% regime stability, and 15% bootstrap
confidence. This is explicitly a MarketLab diagnostic, not an industry-standard
statistic. The JSON methodology preserves every transformation and component;
CSV and JSON results are written under `reports/validation/`.

## Machine-learning ranking dataset

Build the point-in-time monthly cross-sectional dataset:

```bash
python scripts/build_ml_dataset.py
```

The eight feature families are momentum, volatility, three-month trend,
one-month reversal, liquidity, value, quality, and profitability. Features and
the winsorized forward 21-session return target are converted to cross-sectional
ranks for an investment-ranking objective. Dates and symbols remain explicit
for chronological splitting, every feature has a missingness indicator, and the
raw forward return is retained only for evaluation—not as a model feature.

## Ranking models

MarketLab intentionally supports exactly three ranking regressors: Elastic Net,
Random Forest, and histogram gradient-boosted trees. All use deterministic
seeds and fold-local median imputation; Elastic Net additionally standardizes
features within its training fold. The boosted model disables internal random
early-stopping splits so chronological validation remains controlled by the
walk-forward engine. Neural networks and unregistered model families are
outside the project scope.

## Standard walk-forward ML

Run strict expanding-window yearly training:

```bash
python scripts/run_walk_forward_ml.py
```

The first fold trains on 2013–2017 and predicts 2018. Each subsequent fold adds
the completed test year to training and predicts the next calendar year through
2026. Models, imputers, and scalers are refit only on each training window, and
the compressed output contains only out-of-sample predictions. This dataset is
explicitly marked as standard, unpurged walk-forward; overlapping-label purging
and embargo are implemented in the following validation step.

Run the 21-session-purged, five-session-embargoed comparison:

```bash
python scripts/run_purged_walk_forward_ml.py
```

Before every yearly fit, the engine removes training observations whose forward
label interval reaches the embargo boundary preceding the test year. It refits
the same three models, writes a separate compressed prediction artifact, and
compares standard versus purged mean monthly rank IC and top-quintile realized
return at `reports/ml/walk_forward_purging_comparison.json`.

## ML model evaluation

Evaluate the purged out-of-sample predictions as monthly top-quintile
portfolios:

```bash
python scripts/evaluate_ml_models.py
```

The report includes mean and stability of rank IC, top-minus-bottom quantile
spread, gross and net CAGR, risk-free-adjusted Sharpe, turnover, a transparent
10-bps one-way transaction-cost assumption, maximum drawdown, and comparison
with matching 21-session SPY returns. Monthly diagnostics and the model summary
are written under `reports/ml/`.

## ML explainability

Refit every purged fold and calculate out-of-sample permutation and SHAP
importance:

```bash
python scripts/explain_ml_models.py
```

Permutation importance uses rank IC as its scorer. Actual SHAP values are
calculated with linear and tree explainers on deterministic OOS subsamples. The
time-by-feature matrix and stability summary report mean importance, dispersion,
and the fraction of test years in which each predictor ranked among the top
three. Outputs are written under `reports/ml/explainability/`.

## ML versus simple strategies

Run the shared-period portfolio comparison:

```bash
python scripts/compare_ml_strategies.py
```

The comparison rebuilds the three purged ML portfolios and evaluates them
alongside momentum, low-volatility, quality-value-momentum, and SPY from
February 2018 through June 2026. Every active approach uses the same winsorized
21-session forward returns, top-20% selection, equal weighting, 5% position cap,
20% monthly one-way turnover limit, and 10-bps transaction-cost assumption.
Outputs are written under `reports/ml/comparison/`.

Each run also writes an immutable JSON manifest under
`experiments/ml_strategy_comparison/`. The manifest records the command,
parameters, Git revision and dirty state, reported metrics, and SHA-256 digest
and byte size of every input and output artifact. This makes changes in either
code or local research data visible when two runs are compared.

## Data still requiring a licensed source

Alpha Vantage `OVERVIEW` provides current sector and industry labels, not a
point-in-time classification history. Research that requires historically exact
GICS membership needs a licensed classification dataset such as S&P Capital IQ,
Compustat, or another vendor with effective dates. Until then, MarketLab must
label sector-neutral historical results with that limitation.
