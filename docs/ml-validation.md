# Machine-learning validation

ML models rank the same monthly cross-section used by simple strategies. The
current comparison includes Elastic Net, Random Forest, and Gradient Boosting.
Features contain technical, fundamental, and missingness columns; the target is
the forward 21-session return rank.

Training uses expanding annual walk-forward folds. A test year is never used to
fit its model. Observations whose forward label overlaps the test boundary are
purged, followed by a five-session embargo. Evaluation is entirely out of sample.

Model diagnostics include rank IC, positive-IC frequency, quantile spread,
top-quintile net return, turnover, costs, drawdown, and Sharpe. Model-versus-simple
strategy comparisons share selection, weighting, maximum-position, turnover,
and transaction-cost rules.

Explainability is calculated per test year with permutation importance and SHAP.
The report emphasizes feature-importance stability across folds instead of one
global importance chart. These tools explain model behavior; they do not prove a
causal relationship.
