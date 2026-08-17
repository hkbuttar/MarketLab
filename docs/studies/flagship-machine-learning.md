# MarketLab Flagship Study: Machine Learning

**Experiment:** `flagship-machine-learning`

## Research hypothesis

Do nonlinear ranking models add out-of-sample value over simple factors and SPY?

## Experiment configuration

| Parameter | Value |
|---|---|
| Maximum One Way Turnover | 0.2 |
| Maximum Position | 0.05 |
| Selection Fraction | 0.2 |
| Transaction Cost Bps | 10.0 |
| Weighting | equal |

## Validation design

The shared comparison covers 2018-01-31 through 2026-06-30 using 102 monthly observations, walk-forward predictions, identical selection and turnover rules, and a 21-session forward-return horizon.

## Model results

elastic net: CAGR 8.14%, Sharpe 0.38; gradient boosting: CAGR 8.78%, Sharpe 0.40; random forest: CAGR 8.17%, Sharpe 0.37.

## Simple-strategy comparison

The best ML model was gradient boosting with net CAGR 8.78% and Sharpe 0.40. The quality-value-momentum baseline returned 11.77% with Sharpe 0.52.

## Benchmark comparison

SPY returned 14.24% with Sharpe 0.71. The best ML model's active CAGR was -5.46%.

## Evidence-based finding

The tested nonlinear models did not provide incremental out-of-sample value: gradient boosting led the ML models, but trailed both the simple multi-factor baseline and SPY.

## Limitations

- Historical backtests do not guarantee future performance.
- Daily data and modeled execution do not reproduce intraday liquidity.
- Current sector labels are not historically effective GICS classifications.
- Survivorship and source-data limitations remain documented in the data methodology.
- The comparison covers three CPU-oriented model families and is not evidence about every possible machine-learning specification.

## Conclusion

This report documents observed research results and does not constitute an investment recommendation.
