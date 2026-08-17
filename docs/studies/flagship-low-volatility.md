# MarketLab Flagship Study: Low Volatility

**Experiment:** `flagship-low-volatility`

## Research hypothesis

Does low-volatility investing reduce risk consistently across regimes?

## Experiment configuration

| Parameter | Value |
|---|---|
| Asset Class | daily U.S. equities |
| Execution | next-session execution |
| Portfolio | long-only monthly rebalance |
| Transaction Costs | commission, spread, and market impact |

## Data and universe

The net backtest contains 6,652 daily observations from 2000-03-01 through 2026-08-12. SPY is the benchmark.

## Portfolio construction and execution

Signals are ranked cross-sectionally in the point-in-time investable universe. Targets are long-only and executed on the next session with modeled trading costs.

## Performance and risk

Net CAGR was 9.85%, annualized volatility was 13.73%, Sharpe was 0.75, and maximum drawdown was -43.26%. Modeled transaction costs totaled $277,577.

## Regime analysis

bear high vol: CAGR -16.16%, Sharpe -0.64; bear low vol: CAGR -16.90%, Sharpe -1.95; bull high vol: CAGR 27.75%, Sharpe 2.05; bull low vol: CAGR 13.00%, Sharpe 1.36.

## Capacity

At the latest rebalance, the 10% ADV limit implied maximum AUM of $69,262,466; the binding security was HEFT. The historical minimum capacity estimate was $22,237,275.

## Robustness

The MarketLab diagnostic score was 66.2/100 (moderate). This is a project-specific diagnostic, not an industry-standard rating.

## Evidence-based finding

Low volatility produced positive full-sample risk-adjusted returns and shallower losses than momentum, but returns were negative in both tested bear regimes.

## Limitations

- Historical backtests do not guarantee future performance.
- Daily data and modeled execution do not reproduce intraday liquidity.
- Current sector labels are not historically effective GICS classifications.
- Survivorship and source-data limitations remain documented in the data methodology.

## Conclusion

This report documents observed research results and does not constitute an investment recommendation.
