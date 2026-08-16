"""Apples-to-apples ML and simple-strategy portfolio comparison."""

import csv
import gzip
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from marketlab.analytics.returns import compounded_return
from marketlab.portfolio.turnover import limit_turnover
from marketlab.portfolio.weighting import construct_weights

COMPARISON_COLUMNS = (
    "date",
    "strategy_or_model",
    "category",
    "gross_return",
    "turnover",
    "transaction_cost",
    "net_return",
    "benchmark_return",
    "risk_free_return",
)


def compare_models_with_strategies(
    predictions_path: Path,
    targets_path: Path,
    panel_path: Path,
    ml_monthly_path: Path,
    output_directory: Path,
    *,
    cost_bps: float = 10.0,
) -> dict[str, object]:
    """Evaluate every approach on identical dates, returns, and constraints."""

    benchmark, risk_free = _benchmark_controls(ml_monthly_path)
    dates = set(benchmark)
    rows = _ml_portfolios(predictions_path, benchmark, risk_free, cost_bps)
    rows.extend(
        _simple_portfolios(
            targets_path,
            panel_path,
            dates,
            benchmark,
            risk_free,
            cost_bps,
        )
    )
    rows.extend(
        {
            "date": date,
            "strategy_or_model": "SPY",
            "category": "benchmark",
            "gross_return": value,
            "turnover": 0.0,
            "transaction_cost": 0.0,
            "net_return": value,
            "benchmark_return": value,
            "risk_free_return": risk_free[date],
        }
        for date, value in sorted(benchmark.items())
    )
    by_name: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_name[str(row["strategy_or_model"])].append(row)
    summary = {
        name: _summarize(sorted(values, key=lambda row: str(row["date"])))
        for name, values in sorted(by_name.items())
    }
    ranking = sorted(summary, key=lambda name: summary[name]["net_cagr"], reverse=True)
    report: dict[str, object] = {
        "method": "shared 21-session forward-return portfolio comparison",
        "constraints": {
            "selection_fraction": 0.20,
            "weighting": "equal",
            "maximum_position": 0.05,
            "maximum_one_way_turnover": 0.20,
            "transaction_cost_bps": cost_bps,
        },
        "ranking_by_net_cagr": ranking,
        "results": summary,
    }
    output_directory.mkdir(parents=True, exist_ok=True)
    _write_csv(output_directory / "model_strategy_monthly_comparison.csv", rows)
    _write_json(output_directory / "model_strategy_comparison.json", report)
    return report


def _ml_portfolios(
    path: Path,
    benchmark: dict[str, float],
    risk_free: dict[str, float],
    cost_bps: float,
) -> list[dict[str, object]]:
    holdings: dict[str, dict[str, float]] = defaultdict(dict)
    output: list[dict[str, object]] = []
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        current: tuple[str, str] | None = None
        rows: list[dict[str, str]] = []
        for row in csv.DictReader(file):
            key = (row["model"], row["date"])
            if current and key != current:
                output.append(
                    _ml_month(current, rows, holdings, benchmark, risk_free, cost_bps)
                )
                rows = []
            current = key
            rows.append(row)
        if current:
            output.append(
                _ml_month(current, rows, holdings, benchmark, risk_free, cost_bps)
            )
    return output


def _ml_month(
    key: tuple[str, str],
    rows: list[dict[str, str]],
    holdings: dict[str, dict[str, float]],
    benchmark: dict[str, float],
    risk_free: dict[str, float],
    cost_bps: float,
) -> dict[str, object]:
    model, date = key
    ordered = sorted(rows, key=lambda row: float(row["predicted_rank"]), reverse=True)
    count = max(1, math.ceil(len(ordered) * 0.20))
    selected = ordered[:count]
    target = construct_weights(
        {row["symbol"]: float(row["predicted_rank"]) for row in selected},
        method="equal",
        maximum_weight=0.05,
    )
    weights, turnover = limit_turnover(holdings[model], target, 0.20)
    holdings[model] = weights
    returns = {row["symbol"]: float(row["forward_return_21"]) for row in rows}
    gross = sum(weight * returns.get(symbol, 0.0) for symbol, weight in weights.items())
    return _comparison_row(
        date, model, "ml_model", gross, turnover, benchmark, risk_free, cost_bps
    )


def _simple_portfolios(
    targets_path: Path,
    panel_path: Path,
    dates: set[str],
    benchmark: dict[str, float],
    risk_free: dict[str, float],
    cost_bps: float,
) -> list[dict[str, object]]:
    weights: dict[tuple[str, str, str], float] = {}
    turnovers: dict[tuple[str, str], float] = {}
    with gzip.open(targets_path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["date"] not in dates:
                continue
            weights[(row["date"], row["strategy"], row["symbol"])] = float(
                row["weight"]
            )
            turnovers[(row["date"], row["strategy"])] = float(row["turnover"])
    returns: dict[tuple[str, str], float] = defaultdict(float)
    with gzip.open(panel_path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["date"] not in dates:
                continue
            for strategy in ("momentum", "low_volatility", "quality_value_momentum"):
                weight = weights.get((row["date"], strategy, row["symbol"]))
                if weight is not None:
                    returns[(row["date"], strategy)] += weight * float(
                        row["forward_return_21"]
                    )
    output: list[dict[str, object]] = []
    initialized: set[str] = set()
    for (date, strategy), turnover in sorted(turnovers.items()):
        # Start every approach from cash on the shared comparison window. A
        # fully invested portfolio has 50% one-way turnover under our
        # half-L1 convention; subsequent months retain the stored constraint.
        if strategy not in initialized:
            turnover = 0.5
            initialized.add(strategy)
        output.append(
            _comparison_row(
                date,
                strategy,
                "simple_strategy",
                returns.get((date, strategy), 0.0),
                turnover,
                benchmark,
                risk_free,
                cost_bps,
            )
        )
    return output


def _comparison_row(
    date: str,
    name: str,
    category: str,
    gross: float,
    turnover: float,
    benchmark: dict[str, float],
    risk_free: dict[str, float],
    cost_bps: float,
) -> dict[str, object]:
    cost = turnover * cost_bps / 10_000.0
    return {
        "date": date,
        "strategy_or_model": name,
        "category": category,
        "gross_return": gross,
        "turnover": turnover,
        "transaction_cost": cost,
        "net_return": gross - cost,
        "benchmark_return": benchmark[date],
        "risk_free_return": risk_free[date],
    }


def _benchmark_controls(path: Path) -> tuple[dict[str, float], dict[str, float]]:
    benchmark: dict[str, float] = {}
    risk_free: dict[str, float] = {}
    with path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            benchmark[row["date"]] = float(row["benchmark_return"])
            risk_free[row["date"]] = float(row["risk_free_return"])
    return benchmark, risk_free


def _summarize(rows: list[dict[str, object]]) -> dict[str, float | int | str]:
    net = [float(row["net_return"]) for row in rows]
    benchmark = [float(row["benchmark_return"]) for row in rows]
    risk_free = [float(row["risk_free_return"]) for row in rows]
    cagr = _annualized(net)
    benchmark_cagr = _annualized(benchmark)
    excess = [
        value - reference for value, reference in zip(net, risk_free, strict=True)
    ]
    volatility = statistics.stdev(excess) * math.sqrt(12.0)
    return {
        "category": str(rows[0]["category"]),
        "months": len(rows),
        "start_date": str(rows[0]["date"]),
        "end_date": str(rows[-1]["date"]),
        "net_cagr": cagr,
        "benchmark_cagr": benchmark_cagr,
        "active_cagr": cagr - benchmark_cagr,
        "sharpe": statistics.mean(excess) * 12.0 / volatility if volatility else 0.0,
        "maximum_drawdown": _maximum_drawdown(net),
        "average_turnover": statistics.mean(float(row["turnover"]) for row in rows),
        "ending_wealth": 1.0 + compounded_return(net),
    }


def _annualized(returns: list[float]) -> float:
    wealth = 1.0 + compounded_return(returns)
    return wealth ** (12.0 / len(returns)) - 1.0 if wealth > 0 else -1.0


def _maximum_drawdown(returns: list[float]) -> float:
    wealth = 1.0
    peak = 1.0
    maximum = 0.0
    for value in returns:
        wealth *= 1.0 + value
        peak = max(peak, wealth)
        maximum = min(maximum, wealth / peak - 1.0)
    return maximum


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    partial = path.with_name(f"{path.name}.part")
    with partial.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COMPARISON_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    partial.replace(path)


def _write_json(path: Path, value: object) -> None:
    partial = path.with_name(f"{path.name}.part")
    partial.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    partial.replace(path)
