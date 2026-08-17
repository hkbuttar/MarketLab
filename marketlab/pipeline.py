"""Resumable orchestration for the complete MarketLab research workflow."""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineTask:
    """One idempotent command and the artifacts that prove its completion."""

    stage: str
    name: str
    script: str
    outputs: tuple[str, ...]
    arguments: tuple[str, ...] = ()

    def command(self, python: str = sys.executable) -> list[str]:
        return [python, f"scripts/{self.script}", *self.arguments]

    def complete(self, root: Path) -> bool:
        return bool(self.outputs) and all(
            (root / path).is_file() for path in self.outputs
        )


STAGES = ("data", "features", "research", "validation", "ml", "reporting")

TASKS = (
    PipelineTask(
        "data",
        "SEC submissions index",
        "process_sec_submissions.py",
        ("data/processed/sec/submissions_index.zip",),
    ),
    PipelineTask(
        "data",
        "SEC company facts index",
        "process_sec_companyfacts.py",
        ("data/processed/sec/companyfacts_index.zip",),
    ),
    PipelineTask(
        "data",
        "security crosswalk",
        "process_security_crosswalk.py",
        ("data/processed/reference/security_crosswalk.csv.gz",),
    ),
    PipelineTask(
        "data",
        "canonical prices",
        "process_prices.py",
        ("data/processed/prices/prices.csv.gz",),
    ),
    PipelineTask(
        "data",
        "clean prices",
        "clean_prices.py",
        ("data/processed/prices/prices_clean.csv.gz",),
    ),
    PipelineTask(
        "data",
        "canonical fundamentals",
        "process_fundamentals.py",
        ("data/processed/fundamentals/fundamentals_normalized.csv.gz",),
    ),
    PipelineTask(
        "data",
        "point-in-time market capitalization",
        "add_market_cap.py",
        ("data/processed/fundamentals/fundamentals_normalized_valued.csv.gz",),
    ),
    PipelineTask(
        "data",
        "processed-data validation",
        "validate_processed_data.py",
        ("reports/data_validation_valued.json",),
        (
            "--prices",
            "data/processed/prices/prices_clean.csv.gz",
            "--fundamentals",
            "data/processed/fundamentals/fundamentals_normalized_valued.csv.gz",
            "--report",
            "reports/data_validation_valued.json",
        ),
    ),
    PipelineTask(
        "data",
        "Parquet storage",
        "build_parquet_storage.py",
        ("data/processed/parquet/manifest.json",),
    ),
    PipelineTask(
        "features",
        "technical and fundamental features",
        "build_features.py",
        (
            "data/features/technical/daily.csv.gz",
            "data/features/fundamental/filing_ratios_growth.csv.gz",
        ),
    ),
    PipelineTask(
        "features",
        "aligned factor panel",
        "run_factor_research.py",
        ("data/features/factors/monthly_panel_aligned.csv.gz",),
    ),
    PipelineTask(
        "features",
        "investable factor panel",
        "preprocess_factor_research.py",
        ("data/features/factors/monthly_panel_investable.csv.gz",),
    ),
    PipelineTask(
        "research",
        "factor tear sheet",
        "build_factor_tear_sheet.py",
        ("reports/factors/tear_sheet_summary.json",),
    ),
    PipelineTask(
        "research",
        "portfolio targets",
        "build_portfolios.py",
        ("data/features/portfolios/monthly_targets.csv.gz",),
    ),
    PipelineTask(
        "research",
        "rebalance trades",
        "generate_trades.py",
        ("data/features/portfolios/rebalance_trades_split_adjusted.csv.gz",),
    ),
    PipelineTask(
        "research",
        "daily backtests",
        "run_backtest.py",
        ("data/features/backtests/daily_results.csv",),
    ),
    PipelineTask(
        "research",
        "performance analytics",
        "build_performance_analytics.py",
        ("reports/performance/performance_summary.json",),
    ),
    PipelineTask(
        "research",
        "factor attribution",
        "build_factor_attribution.py",
        ("reports/attribution/factor_regression.json",),
    ),
    PipelineTask(
        "research",
        "exposure analysis",
        "build_exposure_analysis.py",
        ("reports/attribution/exposure_summary.json",),
    ),
    PipelineTask(
        "research",
        "regime classification",
        "classify_regimes.py",
        ("data/features/regimes/daily_regimes.csv",),
    ),
    PipelineTask(
        "research",
        "regime analysis",
        "analyze_regimes.py",
        ("reports/regimes/regime_performance.json",),
    ),
    PipelineTask(
        "validation",
        "capacity",
        "build_capacity_report.py",
        ("reports/validation/capacity.json",),
    ),
    PipelineTask(
        "validation",
        "parameter sensitivity",
        "run_parameter_sensitivity.py",
        ("reports/validation/sensitivity/parameter_sensitivity.csv",),
    ),
    PipelineTask(
        "validation",
        "cost sensitivity",
        "run_cost_sensitivity.py",
        ("reports/validation/sensitivity/cost_sensitivity.csv",),
    ),
    PipelineTask(
        "validation",
        "bootstrap",
        "run_bootstrap_analysis.py",
        ("reports/validation/bootstrap/bootstrap_summary.json",),
    ),
    PipelineTask(
        "validation",
        "deflated Sharpe",
        "run_deflated_sharpe.py",
        ("reports/validation/deflated_sharpe.json",),
    ),
    PipelineTask(
        "validation",
        "robustness scores",
        "build_robustness_scores.py",
        ("reports/validation/robustness_scores.json",),
    ),
    PipelineTask(
        "ml",
        "ML research dataset",
        "build_ml_dataset.py",
        ("data/features/ml/cross_sectional_ranking.csv.gz",),
    ),
    PipelineTask(
        "ml",
        "walk-forward models",
        "run_walk_forward_ml.py",
        ("data/features/ml/walk_forward_predictions.csv.gz",),
    ),
    PipelineTask(
        "ml",
        "purged walk-forward models",
        "run_purged_walk_forward_ml.py",
        ("data/features/ml/walk_forward_predictions_purged.csv.gz",),
    ),
    PipelineTask(
        "ml",
        "ML evaluation",
        "evaluate_ml_models.py",
        ("reports/ml/model_evaluation.json",),
    ),
    PipelineTask(
        "ml",
        "ML explainability",
        "explain_ml_models.py",
        ("reports/ml/explainability/feature_importance_stability.json",),
    ),
    PipelineTask(
        "ml",
        "ML strategy comparison",
        "compare_ml_strategies.py",
        ("reports/ml/comparison/model_strategy_comparison.json",),
    ),
    PipelineTask(
        "reporting",
        "flagship studies",
        "generate_flagship_studies.py",
        (
            "docs/studies/flagship-momentum.md",
            "docs/studies/flagship-low-volatility.md",
            "docs/studies/flagship-quality-value-momentum.md",
            "docs/studies/flagship-machine-learning.md",
        ),
    ),
)


def select_tasks(
    *, start_at: str = STAGES[0], through: str = STAGES[-1]
) -> tuple[PipelineTask, ...]:
    """Select an inclusive, ordered stage range."""

    start = STAGES.index(start_at)
    end = STAGES.index(through)
    if start > end:
        raise ValueError("start stage must not follow the final stage")
    selected = set(STAGES[start : end + 1])
    return tuple(task for task in TASKS if task.stage in selected)


def run_tasks(
    tasks: Sequence[PipelineTask],
    root: Path,
    *,
    dry_run: bool = False,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> list[dict[str, object]]:
    """Run missing tasks sequentially and return manifest-ready records."""

    records: list[dict[str, object]] = []
    for task in tasks:
        command = task.command()
        if task.complete(root):
            status = "skipped"
        elif dry_run:
            status = "planned"
        else:
            runner(command, cwd=root, check=True, text=True)
            if not task.complete(root):
                raise RuntimeError(
                    f"{task.name} completed without producing expected artifacts"
                )
            status = "completed"
        records.append(
            {
                "stage": task.stage,
                "task": task.name,
                "status": status,
                "command": command,
                "outputs": list(task.outputs),
            }
        )
    return records
