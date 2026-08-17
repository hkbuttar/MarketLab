# Backtesting methodology

MarketLab simulates daily valuation of monthly, long-only target portfolios.
Signals are formed at a rebalance close and become executable on the next market
session. Adjusted closes drive holding-period returns, while as-traded opens and
whole shares drive execution.

## Portfolio controls

The engine supports equal, score, and inverse-volatility weights; maximum
position and holding counts; liquidity filters; cash buffers; turnover limits;
and risk targeting. Sector-cap logic requires explicit classifications and is
not silently enabled with current labels.

## Execution and costs

Orders are capped by average-dollar-volume participation. Simulated fills include
a minimum/per-share commission, half-spread proxy, and square-root market impact.
Delistings use the recorded security crosswalk and an explicit recovery
assumption. No intraday order book or fill timing is inferred.

## Analytics

Results include gross and net NAV, benchmark NAV, cumulative costs, CAGR,
volatility, Sharpe, Sortino, drawdown, historical VaR/CVaR, turnover, attribution,
regime results, and capacity. The API derives display metrics from persisted daily
results rather than rerunning a strategy.

Backtest comparisons warn when date ranges, capital, costs, rebalance frequency,
or weighting definitions differ.
