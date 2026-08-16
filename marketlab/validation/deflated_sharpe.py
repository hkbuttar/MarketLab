"""Multiple-testing-adjusted Sharpe evidence analysis."""

import csv
import gzip
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from marketlab.analytics.returns import sharpe_ratio

EULER_MASCHERONI = 0.5772156649015329


def run_deflated_sharpe_analysis(
    results_path: Path,
    factors_path: Path,
    sensitivity_path: Path,
    output_path: Path,
) -> dict[str, object]:
    """Adjust primary strategy Sharpe evidence for all evaluated variants."""

    risk_free: dict[str, float] = {}
    with gzip.open(factors_path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            risk_free[row["date"]] = float(row["risk_free"])
    series: dict[str, list[tuple[str, float]]] = defaultdict(list)
    with results_path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            series[row["strategy"]].append((row["date"], float(row["daily_return"])))
    primary: dict[str, dict[str, float | int]] = {}
    primary_sharpes: list[float] = []
    for strategy, observations in sorted(series.items()):
        dates = [date for date, _ in observations]
        returns = [value for _, value in observations]
        annual_risk_free = _annualized_risk_free(dates, risk_free)
        raw_sharpe = sharpe_ratio(returns, annual_risk_free)
        primary_sharpes.append(raw_sharpe)
        primary[strategy] = {
            "raw_sharpe": raw_sharpe,
            "observations": len(returns),
            "skewness": _skewness(returns),
            "kurtosis": _kurtosis(returns),
        }
    sensitivity_sharpes: list[float] = []
    with sensitivity_path.open(encoding="utf-8", newline="") as file:
        sensitivity_sharpes.extend(float(row["sharpe"]) for row in csv.DictReader(file))
    trials = [*sensitivity_sharpes, *primary_sharpes]
    expected_maximum = expected_maximum_sharpe(trials)
    for values in primary.values():
        probability = deflated_sharpe_probability(
            float(values["raw_sharpe"]),
            expected_maximum,
            int(values["observations"]),
            float(values["skewness"]),
            float(values["kurtosis"]),
        )
        values["deflated_sharpe_probability"] = probability
        values["adjusted_evidence"] = (
            "strong"
            if probability >= 0.95
            else "moderate" if probability >= 0.80 else "weak"
        )
    report: dict[str, object] = {
        "method": "Deflated Sharpe probability",
        "number_of_trials": len(trials),
        "sensitivity_variants": len(sensitivity_sharpes),
        "primary_strategies": len(primary_sharpes),
        "expected_maximum_sharpe_under_multiple_testing": expected_maximum,
        "evidence_thresholds": {"strong": 0.95, "moderate": 0.80},
        "strategies": primary,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    partial = output_path.with_name(f"{output_path.name}.part")
    partial.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    partial.replace(output_path)
    return report


def expected_maximum_sharpe(trial_sharpes: list[float]) -> float:
    """Estimate the null maximum Sharpe across the recorded number of trials."""

    if len(trial_sharpes) < 2:
        return 0.0
    trials = len(trial_sharpes)
    deviation = statistics.stdev(trial_sharpes)
    normal = statistics.NormalDist()
    first = normal.inv_cdf(1.0 - 1.0 / trials)
    second = normal.inv_cdf(1.0 - 1.0 / (trials * math.e))
    return deviation * ((1.0 - EULER_MASCHERONI) * first + EULER_MASCHERONI * second)


def deflated_sharpe_probability(
    annual_sharpe: float,
    expected_maximum_annual_sharpe: float,
    observations: int,
    skewness: float,
    kurtosis: float,
) -> float:
    """Return the probability Sharpe exceeds its multiple-testing benchmark."""

    if observations < 2:
        return 0.0
    sharpe = annual_sharpe / math.sqrt(252.0)
    benchmark = expected_maximum_annual_sharpe / math.sqrt(252.0)
    denominator = math.sqrt(
        max(1e-15, 1.0 - skewness * sharpe + (kurtosis - 1.0) * sharpe**2 / 4.0)
    )
    statistic = (sharpe - benchmark) * math.sqrt(observations - 1) / denominator
    return statistics.NormalDist().cdf(statistic)


def _annualized_risk_free(dates: list[str], values: dict[str, float]) -> float:
    observations = [values[date] for date in dates if date in values]
    daily = sum(observations) / len(observations) if observations else 0.0
    return (1.0 + daily) ** 252 - 1.0


def _skewness(values: list[float]) -> float:
    mean = sum(values) / len(values)
    deviation = math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))
    return (
        sum((value - mean) ** 3 for value in values) / len(values) / deviation**3
        if deviation
        else 0.0
    )


def _kurtosis(values: list[float]) -> float:
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return (
        sum((value - mean) ** 4 for value in values) / len(values) / variance**2
        if variance
        else 3.0
    )
