"""Background execution service delegating to the quantitative engine."""

import json
from datetime import UTC, datetime
from pathlib import Path

from backend.schemas.backtest import BacktestRequest
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
    _write_status(
        experiment_id,
        {
            "experiment_id": experiment_id,
            "status": "running",
            "request": request.model_dump(mode="json"),
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
                "error": f"{type(error).__name__}: {error}",
            },
        )
        return
    _write_status(
        experiment_id,
        {
            "experiment_id": experiment_id,
            "status": "completed",
            "artifact_path": str(output),
            "summary": summary,
        },
    )


def read_backtest_job(experiment_id: str) -> dict[str, object]:
    """Read one persisted status record."""

    path = STATUS_ROOT / f"{experiment_id}.json"
    if not path.is_file():
        raise FileNotFoundError(experiment_id)
    return json.loads(path.read_text(encoding="utf-8"))


def _write_status(experiment_id: str, value: dict[str, object]) -> None:
    STATUS_ROOT.mkdir(parents=True, exist_ok=True)
    path = STATUS_ROOT / f"{experiment_id}.json"
    partial = path.with_suffix(".json.part")
    partial.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    partial.replace(path)
