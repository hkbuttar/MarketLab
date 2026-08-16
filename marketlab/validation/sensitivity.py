"""Gross factor-portfolio parameter sensitivity analysis."""

import csv
import gzip
import math
import tempfile
from contextlib import ExitStack
from pathlib import Path

from marketlab.analytics.drawdown import drawdown_statistics
from marketlab.analytics.returns import (
    annualized_return,
    compounded_return,
    sharpe_ratio,
)
from marketlab.factors.ranking import percentile_ranks
from marketlab.features.preprocessing.investable import winsorize

MOMENTUM_WINDOWS = (126, 189, 252)
VOLATILITY_WINDOWS = (20, 40, 60)
SELECTION_FRACTIONS = (0.10, 0.20, 0.30)
STAGING_COLUMNS = (
    "date",
    "symbol",
    "forward_return_21",
    *(f"momentum_{window}" for window in MOMENTUM_WINDOWS),
    *(f"volatility_{window}" for window in VOLATILITY_WINDOWS),
)
RESULT_COLUMNS = (
    "factor_family",
    "window_sessions",
    "selection_fraction",
    "monthly_observations",
    "annualized_return",
    "annualized_volatility",
    "sharpe",
    "worst_month",
)
COST_SCENARIOS_BPS = (0, 5, 10, 25, 50)
COST_RESULT_COLUMNS = (
    "strategy",
    "cost_bps",
    "observations",
    "ending_nav",
    "cagr",
    "sharpe",
    "maximum_drawdown",
    "total_scenario_costs",
    "cost_drag",
    "economically_attractive",
)


def run_cost_sensitivity(
    results_path: Path,
    trades_path: Path,
    factors_path: Path,
    output_directory: Path,
    *,
    initial_capital: float = 1_000_000.0,
) -> list[dict[str, object]]:
    """Replay gross returns under fixed all-in costs per traded dollar."""

    notionals: dict[tuple[str, str], float] = {}
    with gzip.open(trades_path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            key = (row["strategy"], row["execution_date"])
            notionals[key] = notionals.get(key, 0.0) + float(row["notional"])
    risk_free: dict[str, float] = {}
    with gzip.open(factors_path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            risk_free[row["date"]] = float(row["risk_free"])
    series: dict[str, list[dict[str, str]]] = {}
    with results_path.open(encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            series.setdefault(row["strategy"], []).append(row)
    output: list[dict[str, object]] = []
    for strategy, rows in sorted(series.items()):
        gross_returns: list[float] = []
        previous = initial_capital
        for row in rows:
            current = float(row["gross_nav"])
            gross_returns.append(current / previous - 1.0)
            previous = current
        dates = [row["date"] for row in rows]
        annual_risk_free = _annualized_risk_free(dates, risk_free)
        gross_ending = float(rows[-1]["gross_nav"])
        for bps in COST_SCENARIOS_BPS:
            nav = initial_capital
            path: list[float] = []
            daily_returns: list[float] = []
            total_costs = 0.0
            for date, gross_return in zip(dates, gross_returns, strict=True):
                cost = notionals.get((strategy, date), 0.0) * bps / 10_000.0
                previous_nav = nav
                nav = max(0.0, nav * (1.0 + gross_return) - cost)
                total_costs += cost
                daily_returns.append(nav / previous_nav - 1.0 if previous_nav else 0.0)
                path.append(nav)
            cagr = annualized_return(daily_returns)
            sharpe = sharpe_ratio(daily_returns, annual_risk_free)
            drawdown = drawdown_statistics(path, dates)["maximum_drawdown"]
            output.append(
                {
                    "strategy": strategy,
                    "cost_bps": bps,
                    "observations": len(rows),
                    "ending_nav": nav,
                    "cagr": cagr,
                    "sharpe": sharpe,
                    "maximum_drawdown": drawdown,
                    "total_scenario_costs": total_costs,
                    "cost_drag": max(0.0, (gross_ending - nav) / gross_ending),
                    "economically_attractive": cagr > 0 and sharpe >= 0.5,
                }
            )
    output_directory.mkdir(parents=True, exist_ok=True)
    _write_cost_results(output_directory / "cost_sensitivity.csv", output)
    _write_cost_summary(output_directory / "cost_sensitivity_summary.csv", output)
    return output


def run_parameter_sensitivity(
    prices_path: Path, output_directory: Path
) -> list[dict[str, object]]:
    """Evaluate neighboring factor windows and selection sizes at month-end."""

    month_ends = _benchmark_month_ends(prices_path)
    monthly: dict[tuple[str, int, float], list[float]] = {}
    with tempfile.TemporaryDirectory(prefix="marketlab-sensitivity-") as directory:
        paths = _stage_observations(prices_path, month_ends, Path(directory))
        for path in paths.values():
            with path.open(encoding="utf-8", newline="") as file:
                by_date: dict[str, list[dict[str, str]]] = {}
                for row in csv.DictReader(file):
                    by_date.setdefault(row["date"], []).append(row)
            for rows in by_date.values():
                _evaluate_cross_section(rows, monthly)
    results: list[dict[str, object]] = []
    for (family, window, fraction), returns in sorted(monthly.items()):
        annual_return = (1.0 + compounded_return(returns)) ** (12 / len(returns)) - 1.0
        volatility = _sample_std(returns) * math.sqrt(12.0)
        results.append(
            {
                "factor_family": family,
                "window_sessions": window,
                "selection_fraction": fraction,
                "monthly_observations": len(returns),
                "annualized_return": annual_return,
                "annualized_volatility": volatility,
                "sharpe": (
                    (sum(returns) / len(returns) * 12 / volatility)
                    if volatility
                    else 0.0
                ),
                "worst_month": min(returns),
            }
        )
    output_directory.mkdir(parents=True, exist_ok=True)
    _write_results(output_directory / "parameter_sensitivity.csv", results)
    for family in ("momentum", "volatility"):
        _write_heatmap(
            output_directory / f"{family}_sharpe_heatmap.csv", results, family
        )
    return results


def _benchmark_month_ends(path: Path) -> set[str]:
    values: dict[str, str] = {}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row["symbol"] == "SPY":
                values[row["date"][:7]] = row["date"]
    if not values:
        raise ValueError("SPY is unavailable for the month-end calendar")
    return set(values.values())


def _stage_observations(
    path: Path, month_ends: set[str], directory: Path
) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    with ExitStack() as stack:
        writers: dict[str, csv.DictWriter] = {}
        with gzip.open(path, "rt", encoding="utf-8", newline="") as file:
            current_symbol = ""
            rows: list[dict[str, str]] = []
            for row in csv.DictReader(file):
                if current_symbol and row["symbol"] != current_symbol:
                    _stage_symbol(rows, month_ends, directory, paths, writers, stack)
                    rows = []
                current_symbol = row["symbol"]
                rows.append(row)
            if rows:
                _stage_symbol(rows, month_ends, directory, paths, writers, stack)
    return paths


def _stage_symbol(
    rows: list[dict[str, str]],
    month_ends: set[str],
    directory: Path,
    paths: dict[str, Path],
    writers: dict[str, csv.DictWriter],
    stack: ExitStack,
) -> None:
    adjusted = [float(row["adjusted_close"]) for row in rows]
    returns = [0.0] + [
        current / previous - 1.0
        for previous, current in zip(adjusted, adjusted[1:], strict=False)
    ]
    dollars = [float(row["close"]) * float(row["volume"]) for row in rows]
    for index, row in enumerate(rows):
        if (
            row["date"] not in month_ends
            or index < max(MOMENTUM_WINDOWS)
            or index + 21 >= len(rows)
            or float(row["close"]) < 5.0
        ):
            continue
        average_dollar_volume = sum(dollars[index - 20 : index + 1]) / 21.0
        if average_dollar_volume < 1_000_000:
            continue
        staged: dict[str, object] = {
            "date": row["date"],
            "symbol": row["symbol"],
            "forward_return_21": adjusted[index + 21] / adjusted[index] - 1.0,
        }
        for window in MOMENTUM_WINDOWS:
            staged[f"momentum_{window}"] = (
                adjusted[index] / adjusted[index - window] - 1.0
            )
        for window in VOLATILITY_WINDOWS:
            staged[f"volatility_{window}"] = _sample_std(
                returns[index - window + 1 : index + 1]
            ) * math.sqrt(252.0)
        year = row["date"][:4]
        if year not in writers:
            output = directory / f"{year}.csv"
            paths[year] = output
            handle = stack.enter_context(output.open("w", encoding="utf-8", newline=""))
            writers[year] = csv.DictWriter(handle, fieldnames=STAGING_COLUMNS)
            writers[year].writeheader()
        writers[year].writerow(staged)


def _evaluate_cross_section(
    rows: list[dict[str, str]],
    monthly: dict[tuple[str, int, float], list[float]],
) -> None:
    forward = winsorize([float(row["forward_return_21"]) for row in rows])
    for family, windows, higher in (
        ("momentum", MOMENTUM_WINDOWS, True),
        ("volatility", VOLATILITY_WINDOWS, False),
    ):
        for window in windows:
            values = winsorize([float(row[f"{family}_{window}"]) for row in rows])
            ranks = percentile_ranks(values)
            ordered = sorted(
                range(len(rows)),
                key=lambda index: ranks[index],
                reverse=higher,
            )
            for fraction in SELECTION_FRACTIONS:
                count = max(1, math.ceil(len(ordered) * fraction))
                selected = [forward[index] for index in ordered[:count]]
                result = sum(selected) / count
                monthly.setdefault((family, window, fraction), []).append(result)


def _sample_std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / (len(values) - 1))


def _write_results(path: Path, rows: list[dict[str, object]]) -> None:
    partial = path.with_name(f"{path.name}.part")
    with partial.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=RESULT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    partial.replace(path)


def _write_heatmap(path: Path, rows: list[dict[str, object]], family: str) -> None:
    columns = (
        "window_sessions",
        *(f"top_{int(value * 100)}pct" for value in SELECTION_FRACTIONS),
    )
    partial = path.with_name(f"{path.name}.part")
    with partial.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for window in (
            MOMENTUM_WINDOWS if family == "momentum" else VOLATILITY_WINDOWS
        ):
            values: dict[str, object] = {"window_sessions": window}
            for row in rows:
                if row["factor_family"] == family and row["window_sessions"] == window:
                    values[f"top_{int(float(row['selection_fraction']) * 100)}pct"] = (
                        row["sharpe"]
                    )
            writer.writerow(values)
    partial.replace(path)


def _annualized_risk_free(dates: list[str], values: dict[str, float]) -> float:
    observations = [values[date] for date in dates if date in values]
    if not observations:
        return 0.0
    daily = sum(observations) / len(observations)
    return (1.0 + daily) ** 252 - 1.0


def _write_cost_results(path: Path, rows: list[dict[str, object]]) -> None:
    partial = path.with_name(f"{path.name}.part")
    with partial.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=COST_RESULT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    partial.replace(path)


def _write_cost_summary(path: Path, rows: list[dict[str, object]]) -> None:
    columns = (
        "strategy",
        "first_unattractive_bps",
        "highest_tested_attractive_bps",
    )
    strategies = sorted({str(row["strategy"]) for row in rows})
    partial = path.with_name(f"{path.name}.part")
    with partial.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for strategy in strategies:
            strategy_rows = [row for row in rows if row["strategy"] == strategy]
            attractive = [
                int(row["cost_bps"])
                for row in strategy_rows
                if row["economically_attractive"]
            ]
            unattractive = [
                int(row["cost_bps"])
                for row in strategy_rows
                if not row["economically_attractive"]
            ]
            writer.writerow(
                {
                    "strategy": strategy,
                    "first_unattractive_bps": min(unattractive) if unattractive else "",
                    "highest_tested_attractive_bps": (
                        max(attractive) if attractive else ""
                    ),
                }
            )
    partial.replace(path)
