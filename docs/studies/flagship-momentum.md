# MarketLab Flagship Study: Momentum

**Experiment:** `flagship-momentum`

## Research hypothesis

Does cross-sectional momentum survive costs and capacity constraints?

## Experiment configuration

| Parameter | Value |
|---|---|
| Asset Class | daily U.S. equities |
| Execution | next-session execution |
| Portfolio | long-only monthly rebalance |
| Transaction Costs | commission, spread, and market impact |

## Data and universe

The net backtest contains 6,481 daily observations from 2000-11-01 through 2026-08-12. SPY is the benchmark.

## Portfolio construction and execution

Signals are ranked cross-sectionally in the point-in-time investable universe. Targets are long-only and executed on the next session with modeled trading costs.

## Performance and risk

Net CAGR was 4.32%, annualized volatility was 30.95%, Sharpe was 0.27, and maximum drawdown was -63.18%. Modeled transaction costs totaled $5,445,953.

## Regime analysis

bear high vol: CAGR -34.44%, Sharpe -0.98; bear low vol: CAGR -27.66%, Sharpe -2.00; bull high vol: CAGR 30.25%, Sharpe 1.22; bull low vol: CAGR 15.03%, Sharpe 0.49.

## Capacity

At the latest rebalance, the 10% ADV limit implied maximum AUM of $73,918,660; the binding security was BODI. The historical minimum capacity estimate was $21,066,969.

## Robustness

The MarketLab diagnostic score was 34.4/100 (weak). This is a project-specific diagnostic, not an industry-standard rating.

## Evidence-based finding

Momentum remained profitable after modeled costs, but its -63.18% drawdown and weak robustness label do not support a strong result.

## Limitations

- Historical backtests do not guarantee future performance.
- Daily data and modeled execution do not reproduce intraday liquidity.
- Current sector labels are not historically effective GICS classifications.
- Survivorship and source-data limitations remain documented in the data methodology.

## Conclusion

This report documents observed research results and does not constitute an investment recommendation.
