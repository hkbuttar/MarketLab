"""Out-of-sample ranking-model and portfolio evaluation."""

import csv
import gzip
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

from marketlab.analytics.returns import compounded_return
from marketlab.factors.information_coefficient import spearman_ic

MONTHLY_COLUMNS = (
    "date",
    "model",
    "observations",
    "rank_ic",
    "top_quintile_return",
    "bottom_quintile_return",
    "quantile_spread",
    "turnover",
    "transaction_cost",
    "net_return",
    "benchmark_return",
    "risk_free_return",
)


def evaluate_ml_predictions(
    predictions_path: Path,
    regime_calendar_path: Path,
    factors_path: Path,
    output_directory: Path,
    *,
    cost_bps: float = 10.0,
) -> dict[str, object]:
    """Evaluate purged OOS predictions as monthly top-quintile portfolios."""

    calendar, closes = _benchmark_calendar(regime_calendar_path)
    benchmark = _forward_benchmark_returns(calendar, closes, 21)
    risk_free = _forward_risk_free_returns(calendar, factors_path, 21)
    holdings: dict[str, dict[str, float]] = defaultdict(dict)
    monthly: list[dict[str, object]] = []
    with gzip.open(predictions_path, "rt", encoding="utf-8", newline="") as file:
        current_key: tuple[str, str] | None = None
        rows: list[dict[str, str]] = []
        for row in csv.DictReader(file):
            key = (row["model"], row["date"])
            if current_key and key != current_key:
                monthly.append(
                    _monthly_observation(
                        current_key,
                        rows,
                        holdings,
                        benchmark,
                        risk_free,
                        cost_bps,
                    )
                )
                rows = []
            current_key = key
            rows.append(row)
        if current_key:
            monthly.append(
                _monthly_observation(
                    current_key,
                    rows,
                    holdings,
                    benchmark,
                    risk_free,
                    cost_bps,
                )
            )
    by_model: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in monthly:
        by_model[str(row["model"])].append(row)
    summary: dict[str, object] = {
        "method": "purged out-of-sample monthly top-quintile portfolios",
        "transaction_cost_bps_per_one_way_turnover": cost_bps,
        "models": {},
    }
    for model, rows in sorted(by_model.items()):
        summary["models"][model] = _summarize_model(rows)
    output_directory.mkdir(parents=True, exist_ok=True)
    _write_csv(output_directory / "monthly_model_performance.csv", monthly)
    _write_json(output_directory / "model_evaluation.json", summary)
    return summary


def _monthly_observation(
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
    top = ordered[:count]
    bottom = ordered[-count:]
    target = {row["symbol"]: 1.0 / count for row in top}
    previous = holdings.get(model, {})
    symbols = set(previous) | set(target)
    turnover = 0.5 * sum(
        abs(target.get(symbol, 0.0) - previous.get(symbol, 0.0)) for symbol in symbols
    )
    holdings[model] = target
    top_return = statistics.mean(float(row["forward_return_21"]) for row in top)
    bottom_return = statistics.mean(float(row["forward_return_21"]) for row in bottom)
    cost = turnover * cost_bps / 10_000.0
    predictions = [float(row["predicted_rank"]) for row in rows]
    targets = [float(row["target_return_rank"]) for row in rows]
    return {
        "date": date,
        "model": model,
        "observations": len(rows),
        "rank_ic": spearman_ic(predictions, targets) or 0.0,
        "top_quintile_return": top_return,
        "bottom_quintile_return": bottom_return,
        "quantile_spread": top_return - bottom_return,
        "turnover": turnover,
        "transaction_cost": cost,
        "net_return": top_return - cost,
        "benchmark_return": benchmark.get(date, 0.0),
        "risk_free_return": risk_free.get(date, 0.0),
    }


def _summarize_model(rows: list[dict[str, object]]) -> dict[str, float | int]:
    gross = [float(row["top_quintile_return"]) for row in rows]
    net = [float(row["net_return"]) for row in rows]
    benchmark = [float(row["benchmark_return"]) for row in rows]
    risk_free = [float(row["risk_free_return"]) for row in rows]
    ics = [float(row["rank_ic"]) for row in rows]
    spreads = [float(row["quantile_spread"]) for row in rows]
    gross_cagr = _annualized_monthly(gross)
    net_cagr = _annualized_monthly(net)
    benchmark_cagr = _annualized_monthly(benchmark)
    excess = [
        value - reference for value, reference in zip(net, risk_free, strict=True)
    ]
    volatility = _sample_std(excess) * math.sqrt(12.0)
    return {
        "months": len(rows),
        "mean_rank_ic": statistics.mean(ics),
        "rank_ic_std": _sample_std(ics),
        "positive_ic_fraction": sum(value > 0 for value in ics) / len(ics),
        "mean_quantile_spread": statistics.mean(spreads),
        "gross_cagr": gross_cagr,
        "net_cagr": net_cagr,
        "benchmark_cagr": benchmark_cagr,
        "active_cagr": net_cagr - benchmark_cagr,
        "oos_sharpe": (
            statistics.mean(excess) * 12.0 / volatility if volatility else 0.0
        ),
        "average_turnover": statistics.mean(float(row["turnover"]) for row in rows),
        "total_transaction_cost": sum(float(row["transaction_cost"]) for row in rows),
        "annualized_cost_drag": gross_cagr - net_cagr,
        "maximum_drawdown": _maximum_drawdown(net),
    }


def _benchmark_calendar(path: Path) -> tuple[list[str], dict[str, float]]:
    calendar: list[str] = []
    closes: dict[str, float] = {}
    with path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            calendar.append(row["date"])
            closes[row["date"]] = float(row["benchmark_adjusted_close"])
    return calendar, closes


def _forward_benchmark_returns(
    calendar: list[str], closes: dict[str, float], horizon: int
) -> dict[str, float]:
    return {
        date: closes[calendar[index + horizon]] / closes[date] - 1.0
        for index, date in enumerate(calendar)
        if index + horizon < len(calendar)
    }


def _forward_risk_free_returns(
    calendar: list[str], path: Path, horizon: int
) -> dict[str, float]:
    daily: dict[str, float] = {}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            daily[row["date"]] = float(row["risk_free"])
    result: dict[str, float] = {}
    for index, date in enumerate(calendar):
        if index + horizon >= len(calendar):
            continue
        wealth = 1.0
        for future in calendar[index + 1 : index + horizon + 1]:
            wealth *= 1.0 + daily.get(future, 0.0)
        result[date] = wealth - 1.0
    return result


def _annualized_monthly(returns: list[float]) -> float:
    wealth = 1.0 + compounded_return(returns)
    return wealth ** (12.0 / len(returns)) - 1.0 if wealth > 0 else -1.0


def _sample_std(values: list[float]) -> float:
    return statistics.stdev(values) if len(values) > 1 else 0.0


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
        writer = csv.DictWriter(file, fieldnames=MONTHLY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    partial.replace(path)


def _write_json(path: Path, value: object) -> None:
    partial = path.with_name(f"{path.name}.part")
    partial.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    partial.replace(path)
