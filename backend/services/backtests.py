"""Background execution service delegating to the quantitative engine."""

import csv
import json
import math
from datetime import UTC, datetime
from pathlib import Path

from backend.schemas.backtest import BacktestRequest
from marketlab.analytics.drawdown import drawdown_statistics
from marketlab.analytics.returns import annualized_return, sharpe_ratio
from marketlab.analytics.risk import annualized_volatility
from marketlab.backtest import run_daily_backtest

STATUS_ROOT = Path("experiments/api_backtests")
OUTPUT_ROOT = Path("data/features/backtests/api")


def create_backtest_job(experiment_id: str, request: BacktestRequest) -> None:
    """Persist queued state before returning an accepted API response."""

    _write_status(
        experiment_id,
        {
            "experiment_id": experiment_id,
            "status": "queued",
            "request": request.model_dump(mode="json"),
            "created_at": datetime.now(UTC).isoformat(),
        },
    )


def run_backtest_job(experiment_id: str, request: BacktestRequest) -> None:
    """Run one filtered backtest and atomically update its job status."""

    output = OUTPUT_ROOT / f"{experiment_id}.csv"
    try:
        created_at = read_backtest_job(experiment_id).get("created_at")
    except FileNotFoundError:
        created_at = datetime.now(UTC).isoformat()
    _write_status(
        experiment_id,
        {
            "experiment_id": experiment_id,
            "status": "running",
            "request": request.model_dump(mode="json"),
            "created_at": created_at,
        },
    )
    try:
        summary = run_daily_backtest(
            Path("data/features/portfolios/monthly_targets.csv.gz"),
            Path("data/processed/prices/prices_clean.csv.gz"),
            Path("data/features/portfolios/rebalance_trades_split_adjusted.csv.gz"),
            Path("data/processed/reference/security_crosswalk.csv.gz"),
            output,
            initial_capital=request.capital,
            strategies={request.strategy},
            start_date=request.start_date.isoformat(),
            end_date=request.end_date.isoformat(),
            cost_bps=request.cost_bps,
        )
    except Exception as error:
        _write_status(
            experiment_id,
            {
                "experiment_id": experiment_id,
                "status": "failed",
                "request": request.model_dump(mode="json"),
                "created_at": created_at,
                "error": f"{type(error).__name__}: {error}",
            },
        )
        return
    _write_status(
        experiment_id,
        {
            "experiment_id": experiment_id,
            "status": "completed",
            "request": request.model_dump(mode="json"),
            "created_at": created_at,
            "artifact_path": str(output),
            "summary": summary,
        },
    )


def read_backtest_job(experiment_id: str) -> dict[str, object]:
    """Read one persisted status record."""

    if not experiment_id or Path(experiment_id).name != experiment_id:
        raise FileNotFoundError(experiment_id)
    path = STATUS_ROOT / f"{experiment_id}.json"
    if not path.is_file():
        raise FileNotFoundError(experiment_id)
    return json.loads(path.read_text(encoding="utf-8"))


def list_backtest_jobs() -> list[dict[str, object]]:
    """List persisted jobs newest first without reading result artifacts."""

    if not STATUS_ROOT.is_dir():
        return []
    jobs = []
    for path in STATUS_ROOT.glob("*.json"):
        if path.name.startswith("."):
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, OSError):
            continue
        request = value.get("request") or {}
        jobs.append(
            {
                "experiment_id": value.get("experiment_id", path.stem),
                "status": value.get("status", "failed"),
                "strategy": request.get("strategy") or _summary_strategy(value),
                "created_at": value.get("created_at"),
            }
        )
    return sorted(
        jobs,
        key=lambda item: (
            str(item.get("created_at") or ""),
            str(item["experiment_id"]),
        ),
        reverse=True,
    )


def read_backtest_result(experiment_id: str) -> dict[str, object]:
    """Derive display metrics from a completed job's persisted daily results."""

    job = read_backtest_job(experiment_id)
    if job.get("status") != "completed" or not job.get("artifact_path"):
        raise ValueError("backtest result is not complete")
    path = Path(str(job["artifact_path"]))
    if not path.is_file():
        raise FileNotFoundError(path)
    rows = list(csv.DictReader(path.open(encoding="utf-8", newline="")))
    if not rows:
        raise ValueError("backtest result artifact is empty")
    returns = [float(row["daily_return"]) for row in rows]
    nav = [float(row["net_nav"]) for row in rows]
    initial_net = float(rows[0]["net_nav"]) / (1 + returns[0]) if returns[0] > -1 else 0
    ending_net = float(rows[-1]["net_nav"])
    ending_gross = float(rows[-1]["gross_nav"])
    initial_benchmark = float(rows[0]["benchmark_nav"])
    ending_benchmark = float(rows[-1]["benchmark_nav"])
    curve = _sample_curve(rows, maximum_points=260)
    return {
        "experiment_id": experiment_id,
        "strategy": rows[0]["strategy"],
        "start_date": rows[0]["date"],
        "end_date": rows[-1]["date"],
        "metrics": {
            "total_return": ending_net / initial_net - 1 if initial_net else -1.0,
            "benchmark_return": ending_benchmark / initial_benchmark - 1,
            "cagr": annualized_return(returns),
            "annualized_volatility": annualized_volatility(returns),
            "sharpe": sharpe_ratio(returns),
            "maximum_drawdown": float(
                drawdown_statistics(nav, [row["date"] for row in rows])[
                    "maximum_drawdown"
                ]
            ),
            "total_costs": float(rows[-1]["cumulative_costs"]),
            "cost_drag": (
                (ending_gross - ending_net) / initial_net if initial_net else 0
            ),
            "observations": len(rows),
        },
        "equity_curve": curve,
    }


def _summary_strategy(value: dict[str, object]) -> str | None:
    summary = value.get("summary")
    if isinstance(summary, dict) and summary:
        return str(next(iter(summary)))
    return None


def _sample_curve(
    rows: list[dict[str, str]], maximum_points: int
) -> list[dict[str, object]]:
    step = max(1, math.ceil(len(rows) / maximum_points))
    sampled = rows[::step]
    if sampled[-1] is not rows[-1]:
        sampled.append(rows[-1])
    return [
        {
            "date": row["date"],
            "net_nav": float(row["net_nav"]),
            "gross_nav": float(row["gross_nav"]),
            "benchmark_nav": float(row["benchmark_nav"]),
        }
        for row in sampled
    ]


def _write_status(experiment_id: str, value: dict[str, object]) -> None:
    STATUS_ROOT.mkdir(parents=True, exist_ok=True)
    path = STATUS_ROOT / f"{experiment_id}.json"
    partial = path.with_suffix(".json.part")
    partial.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    partial.replace(path)
