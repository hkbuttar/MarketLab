# Factor research methodology

The factor engine evaluates cross-sectional signals before they become
strategies. Supported families include momentum, trend, reversal, volatility,
liquidity, value, quality, profitability, leverage, and growth.

At each rebalance date, continuous features are winsorized and converted to
cross-sectional percentile ranks. Diagnostics include:

- Spearman rank information coefficient against 21-session forward returns;
- IC history, dispersion, and positive-IC frequency;
- equal-weight quantile portfolio returns and top-minus-bottom spread;
- top-quantile one-way turnover;
- factor correlation and redundancy;
- descriptive sector exposure.

Missing fundamental features remain missing until an eligible filing exists.
ML preprocessing adds explicit missingness indicators rather than treating
absence as a zero economic value.

The Factor Lab API and dashboard read persisted research artifacts, ensuring the
same definitions are used by scripts, tests, and the product layer.
