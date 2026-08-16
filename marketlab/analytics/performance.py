"""Performance report orchestration for daily backtest results."""

import csv
import json
from collections import defaultdict
from pathlib import Path

from marketlab.analytics.benchmark import benchmark_statistics
from marketlab.analytics.drawdown import drawdown_statistics
from marketlab.analytics.returns import (
    annualized_return,
    compounded_return,
    period_returns,
    sharpe_ratio,
    sortino_ratio,
)
from marketlab.analytics.risk import (
    annualized_volatility,
    downside_deviation,
    historical_cvar,
    historical_var,
)
from marketlab.analytics.turnover import portfolio_statistics, trading_statistics


def build_performance_report(
    results_path: Path,
    trades_path: Path,
    targets_path: Path,
    output_directory: Path,
    *,
    risk_free_rate: float = 0.0,
) -> dict[str, dict[str, object]]:
    """Calculate and atomically save strategy and calendar-period analytics."""

    series: dict[str, list[dict[str, str]]] = defaultdict(list)
    with results_path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            series[row["strategy"]].append(row)
    trading = trading_statistics(trades_path)
    portfolio = portfolio_statistics(targets_path)
    report: dict[str, dict[str, object]] = {}
    calendar_rows: list[dict[str, object]] = []
    for strategy, rows in sorted(series.items()):
        dates = [row["date"] for row in rows]
        returns = [float(row["daily_return"]) for row in rows]
        nav = [float(row["net_nav"]) for row in rows]
        benchmark_nav = [float(row["benchmark_nav"]) for row in rows]
        benchmark_returns = [0.0]
        benchmark_returns.extend(
            current / previous - 1.0
            for previous, current in zip(benchmark_nav, benchmark_nav[1:], strict=False)
        )
        drawdown = drawdown_statistics(nav, dates)
        annual_return = annualized_return(returns)
        strategy_trading = trading.get(strategy, {})
        gross_ending = float(rows[-1]["gross_nav"])
        net_ending = nav[-1]
        periods = period_returns(dates, returns)
        for frequency, values in periods.items():
            for period, value in values.items():
                calendar_rows.append(
                    {
                        "strategy": strategy,
                        "frequency": frequency,
                        "period": period,
                        "return": value,
                    }
                )
        report[strategy] = {
            "start_date": dates[0],
            "end_date": dates[-1],
            "observations": len(rows),
            "cumulative_return": compounded_return(returns),
            "cagr": annual_return,
            "annualized_return": annual_return,
            "annualized_volatility": annualized_volatility(returns),
            "downside_deviation": downside_deviation(returns),
            "historical_var_95": historical_var(returns),
            "historical_cvar_95": historical_cvar(returns),
            "sharpe": sharpe_ratio(returns, risk_free_rate),
            "sortino": sortino_ratio(returns, risk_free_rate),
            "calmar": (
                annual_return / abs(float(drawdown["maximum_drawdown"]))
                if drawdown["maximum_drawdown"]
                else 0.0
            ),
            **drawdown,
            **benchmark_statistics(returns, benchmark_returns),
            **strategy_trading,
            **portfolio.get(strategy, {}),
            "cost_drag": (
                (gross_ending - net_ending) / gross_ending if gross_ending else 0.0
            ),
            "ending_net_nav": net_ending,
            "ending_gross_nav": gross_ending,
        }
    output_directory.mkdir(parents=True, exist_ok=True)
    _write_json(output_directory / "performance_summary.json", report)
    _write_periods(output_directory / "period_returns.csv", calendar_rows)
    return report


def _write_json(path: Path, value: object) -> None:
    partial = path.with_name(f"{path.name}.part")
    partial.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    partial.replace(path)


def _write_periods(path: Path, rows: list[dict[str, object]]) -> None:
    partial = path.with_name(f"{path.name}.part")
    with partial.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(
            file, fieldnames=("strategy", "frequency", "period", "return")
        )
        writer.writeheader()
        writer.writerows(rows)
    partial.replace(path)
