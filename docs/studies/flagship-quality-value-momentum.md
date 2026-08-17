# MarketLab Flagship Study: Multi-Factor

**Experiment:** `flagship-quality-value-momentum`

## Research hypothesis

Does combining quality, value, and momentum improve strategy stability?

## Experiment configuration

| Parameter | Value |
|---|---|
| Asset Class | daily U.S. equities |
| Execution | next-session execution |
| Portfolio | long-only monthly rebalance |
| Transaction Costs | commission, spread, and market impact |

## Data and universe

The net backtest contains 4,283 daily observations from 2009-08-03 through 2026-08-12. SPY is the benchmark.

## Portfolio construction and execution

Signals are ranked cross-sectionally in the point-in-time investable universe. Targets are long-only and executed on the next session with modeled trading costs.

## Performance and risk

Net CAGR was 13.39%, annualized volatility was 18.65%, Sharpe was 0.77, and maximum drawdown was -42.36%. Modeled transaction costs totaled $227,118.

## Regime analysis

bear high vol: CAGR -16.98%, Sharpe -0.44; bear low vol: CAGR -57.45%, Sharpe -4.75; bull high vol: CAGR 34.11%, Sharpe 1.69; bull low vol: CAGR 14.11%, Sharpe 0.94.

## Capacity

At the latest rebalance, the 10% ADV limit implied maximum AUM of $62,690,121; the binding security was NATH. The historical minimum capacity estimate was $8,063,675.

## Robustness

The MarketLab diagnostic score was 69.9/100 (moderate). This is a project-specific diagnostic, not an industry-standard rating.

## Evidence-based finding

The combined factor strategy had the highest full-sample CAGR and robustness score of the three rule-based strategies, while still suffering negative returns in both tested bear regimes.

## Limitations

- Historical backtests do not guarantee future performance.
- Daily data and modeled execution do not reproduce intraday liquidity.
- Current sector labels are not historically effective GICS classifications.
- Survivorship and source-data limitations remain documented in the data methodology.

## Conclusion

This report documents observed research results and does not constitute an investment recommendation.
