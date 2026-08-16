"""Regime-conditioned strategy performance analysis."""

import csv
import gzip
import json
from collections import defaultdict
from pathlib import Path

from marketlab.analytics.returns import annualized_return, sharpe_ratio

REGIME_METRIC_COLUMNS = (
    "strategy",
    "regime",
    "observations",
    "cagr",
    "sharpe",
    "maximum_episode_drawdown",
    "hit_rate",
    "average_monthly_turnover",
)


def build_regime_analysis(
    results_path: Path,
    regimes_path: Path,
    targets_path: Path,
    factors_path: Path,
    output_directory: Path,
) -> list[dict[str, object]]:
    """Calculate net strategy metrics conditioned on point-in-time regimes."""

    regimes = _regime_dates(regimes_path)
    risk_free = _risk_free_rates(factors_path)
    turnover = _turnover_by_regime(targets_path, regimes)
    observations: dict[tuple[str, str], list[tuple[str, float]]] = defaultdict(list)
    with results_path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            regime = regimes.get(row["date"])
            if regime:
                observations[(row["strategy"], regime)].append(
                    (row["date"], float(row["daily_return"]))
                )
    rows: list[dict[str, object]] = []
    for (strategy, regime), values in sorted(observations.items()):
        dates = [date for date, _ in values]
        returns = [value for _, value in values]
        annual_risk_free = _annualized_average_risk_free(dates, risk_free)
        rows.append(
            {
                "strategy": strategy,
                "regime": regime,
                "observations": len(returns),
                "cagr": annualized_return(returns),
                "sharpe": sharpe_ratio(returns, annual_risk_free),
                "maximum_episode_drawdown": maximum_episode_drawdown(
                    strategy, regime, results_path, regimes
                ),
                "hit_rate": sum(value > 0 for value in returns) / len(returns),
                "average_monthly_turnover": turnover.get((strategy, regime), 0.0),
            }
        )
    output_directory.mkdir(parents=True, exist_ok=True)
    _write_csv(output_directory / "regime_performance.csv", rows)
    summary = {
        "methodology": {
            "returns": "net daily strategy returns",
            "drawdown": "worst drawdown within a contiguous regime episode",
            "turnover": "average one-way turnover on rebalance dates in regime",
            "risk_free": "daily Kenneth French RF averaged and annualized by regime",
        },
        "results": rows,
    }
    _write_json(output_directory / "regime_performance.json", summary)
    return rows


def maximum_episode_drawdown(
    strategy: str,
    target_regime: str,
    results_path: Path,
    regimes: dict[str, str],
) -> float:
    """Return the worst drawdown contained within a contiguous regime episode."""

    maximum = 0.0
    wealth = 1.0
    peak = 1.0
    active = False
    with results_path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["strategy"] != strategy:
                continue
            if regimes.get(row["date"]) != target_regime:
                wealth = 1.0
                peak = 1.0
                active = False
                continue
            if not active:
                active = True
                wealth = 1.0
                peak = 1.0
            wealth *= 1.0 + float(row["daily_return"])
            peak = max(peak, wealth)
            maximum = min(maximum, wealth / peak - 1.0)
    return maximum


def _regime_dates(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8", newline="") as file:
        return {row["date"]: row["regime"] for row in csv.DictReader(file)}


def _risk_free_rates(path: Path) -> dict[str, float]:
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        return {row["date"]: float(row["risk_free"]) for row in csv.DictReader(file)}


def _annualized_average_risk_free(
    dates: list[str], risk_free: dict[str, float]
) -> float:
    values = [risk_free[date] for date in dates if date in risk_free]
    if not values:
        return 0.0
    daily = sum(values) / len(values)
    return (1.0 + daily) ** 252 - 1.0


def _turnover_by_regime(
    path: Path, regimes: dict[str, str]
) -> dict[tuple[str, str], float]:
    values: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            regime = regimes.get(row["date"])
            if regime:
                values[(row["strategy"], regime)][row["date"]] = float(row["turnover"])
    return {key: sum(months.values()) / len(months) for key, months in values.items()}


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    partial = path.with_name(f"{path.name}.part")
    with partial.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=REGIME_METRIC_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    partial.replace(path)


def _write_json(path: Path, value: object) -> None:
    partial = path.with_name(f"{path.name}.part")
    partial.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    partial.replace(path)
