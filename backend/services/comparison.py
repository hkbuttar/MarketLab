"""Consistent comparison of persisted backtest experiments."""

from backend.schemas.comparison import BacktestComparison, ComparedBacktest
from backend.services.backtests import read_backtest_job, read_backtest_result


def compare_backtests(experiment_ids: list[str]) -> BacktestComparison:
    """Compare two to five completed runs and disclose configuration differences."""

    if not 2 <= len(experiment_ids) <= 5:
        raise ValueError("select between 2 and 5 experiments")
    if len(set(experiment_ids)) != len(experiment_ids):
        raise ValueError("experiments must be unique")
    experiments = []
    for experiment_id in experiment_ids:
        result = read_backtest_result(experiment_id)
        job = read_backtest_job(experiment_id)
        experiments.append(
            ComparedBacktest(
                experiment_id=experiment_id,
                strategy=str(result["strategy"]),
                start_date=str(result["start_date"]),
                end_date=str(result["end_date"]),
                configuration=dict(job.get("request") or {}),
                metrics=result["metrics"],
            )
        )
    return BacktestComparison(
        experiments=experiments,
        configuration_warnings=_configuration_warnings(experiments),
    )


def _configuration_warnings(experiments: list[ComparedBacktest]) -> list[str]:
    warnings = []
    for field, label in (
        ("start_date", "start dates"),
        ("end_date", "end dates"),
        ("capital", "starting capital"),
        ("cost_bps", "transaction-cost assumptions"),
        ("rebalance", "rebalance frequencies"),
        ("weighting", "weighting methods"),
    ):
        if field in {"start_date", "end_date"}:
            values = {getattr(item, field) for item in experiments}
        else:
            values = {
                str(item.configuration.get(field, "unavailable"))
                for item in experiments
            }
        if len(values) > 1 or "unavailable" in values:
            warnings.append(f"Experiments use different or unavailable {label}.")
    return warnings
