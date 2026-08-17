"""Flagship studies assembled from completed MarketLab research artifacts."""

from __future__ import annotations

import json
from pathlib import Path

from marketlab.reporting.report import ResearchReport, write_research_report

STRATEGY_LABELS = {
    "momentum": "Momentum",
    "low_volatility": "Low Volatility",
    "quality_value_momentum": "Multi-Factor",
}


def generate_flagship_studies(
    project_root: Path = Path("."),
) -> list[tuple[Path, Path]]:
    """Generate the four documented studies from persisted result artifacts."""

    reports = project_root / "reports"
    performance = _read_json(reports / "performance/performance_summary.json")
    capacity = _read_json(reports / "validation/capacity.json")["strategies"]
    robustness = _read_json(reports / "validation/robustness_scores.json")["strategies"]
    regimes = _read_json(reports / "regimes/regime_performance.json")["results"]
    comparison = _read_json(reports / "ml/comparison/model_strategy_comparison.json")
    studies = [
        _strategy_study("momentum", performance, capacity, robustness, regimes),
        _strategy_study("low_volatility", performance, capacity, robustness, regimes),
        _strategy_study(
            "quality_value_momentum",
            performance,
            capacity,
            robustness,
            regimes,
        ),
        _ml_study(comparison),
    ]
    output = project_root / "docs/studies"
    return [
        write_research_report(study, output / study.experiment_id) for study in studies
    ]


def _strategy_study(
    strategy: str,
    performance: dict[str, object],
    capacity: dict[str, object],
    robustness: dict[str, object],
    regimes: list[dict[str, object]],
) -> ResearchReport:
    metrics = performance[strategy]
    capacity_metrics = capacity[strategy]
    score = robustness[strategy]
    regime_rows = [row for row in regimes if row["strategy"] == strategy]
    regime_summary = "; ".join(
        f"{str(row['regime']).replace('_', ' ')}: CAGR {_pct(row['cagr'])}, "
        f"Sharpe {float(row['sharpe']):.2f}"
        for row in regime_rows
    )
    label = STRATEGY_LABELS[strategy]
    questions = {
        "momentum": (
            "Does cross-sectional momentum survive costs and capacity constraints?"
        ),
        "low_volatility": (
            "Does low-volatility investing reduce risk consistently across regimes?"
        ),
        "quality_value_momentum": (
            "Does combining quality, value, and momentum improve strategy stability?"
        ),
    }
    latest_capacity = capacity_metrics["latest"]
    conclusion = _strategy_conclusion(strategy, metrics, score)
    return ResearchReport(
        title=f"MarketLab Flagship Study: {label}",
        hypothesis=questions[strategy],
        experiment_id=f"flagship-{strategy.replace('_', '-')}",
        configuration={
            "asset_class": "daily U.S. equities",
            "portfolio": "long-only monthly rebalance",
            "execution": "next-session execution",
            "transaction_costs": "commission, spread, and market impact",
        },
        sections={
            "Data and universe": (
                f"The net backtest contains {int(metrics['observations']):,} daily "
                f"observations from {metrics['start_date']} through "
                f"{metrics['end_date']}. SPY is the benchmark."
            ),
            "Portfolio construction and execution": (
                "Signals are ranked cross-sectionally in the point-in-time "
                "investable universe. Targets are long-only and executed on the "
                "next session with modeled trading costs."
            ),
            "Performance and risk": (
                f"Net CAGR was {_pct(metrics['cagr'])}, annualized volatility was "
                f"{_pct(metrics['annualized_volatility'])}, Sharpe was "
                f"{float(metrics['sharpe']):.2f}, and maximum drawdown was "
                f"{_pct(metrics['maximum_drawdown'])}. Modeled transaction costs "
                f"totaled ${float(metrics['transaction_costs']):,.0f}."
            ),
            "Regime analysis": regime_summary + ".",
            "Capacity": (
                f"At the latest rebalance, the 10% ADV limit implied maximum AUM "
                f"of ${float(latest_capacity['maximum_aum']):,.0f}; the binding "
                f"security was {latest_capacity['binding_symbol']}. The historical "
                f"minimum capacity estimate was "
                f"${float(capacity_metrics['historical_minimum_aum']):,.0f}."
            ),
            "Robustness": (
                f"The MarketLab diagnostic score was "
                f"{float(score['overall_score']):.1f}/100 ({score['label']}). "
                "This is a project-specific diagnostic, not an industry-standard "
                "rating."
            ),
            "Evidence-based finding": conclusion,
        },
        limitations=_limitations(),
    )


def _ml_study(comparison: dict[str, object]) -> ResearchReport:
    results = comparison["results"]
    models = {
        name: values
        for name, values in results.items()
        if values["category"] == "ml_model"
    }
    best_name, best = max(models.items(), key=lambda item: item[1]["net_cagr"])
    baseline = results["quality_value_momentum"]
    benchmark = results["SPY"]
    table = "; ".join(
        f"{name.replace('_', ' ')}: CAGR {_pct(values['net_cagr'])}, "
        f"Sharpe {float(values['sharpe']):.2f}"
        for name, values in sorted(models.items())
    )
    return ResearchReport(
        title="MarketLab Flagship Study: Machine Learning",
        hypothesis=(
            "Do nonlinear ranking models add out-of-sample value over simple "
            "factors and SPY?"
        ),
        experiment_id="flagship-machine-learning",
        configuration=dict(comparison["constraints"]),
        sections={
            "Validation design": (
                f"The shared comparison covers {best['start_date']} through "
                f"{best['end_date']} using {int(best['months'])} monthly "
                "observations, walk-forward predictions, identical selection and "
                "turnover rules, and a 21-session forward-return horizon."
            ),
            "Model results": table + ".",
            "Simple-strategy comparison": (
                f"The best ML model was {best_name.replace('_', ' ')} with net CAGR "
                f"{_pct(best['net_cagr'])} and Sharpe "
                f"{float(best['sharpe']):.2f}. The quality-value-momentum baseline "
                f"returned {_pct(baseline['net_cagr'])} with Sharpe "
                f"{float(baseline['sharpe']):.2f}."
            ),
            "Benchmark comparison": (
                f"SPY returned {_pct(benchmark['net_cagr'])} with Sharpe "
                f"{float(benchmark['sharpe']):.2f}. The best ML model's active "
                f"CAGR was {_pct(best['active_cagr'])}."
            ),
            "Evidence-based finding": (
                "The tested nonlinear models did not provide incremental "
                "out-of-sample value: gradient boosting led the ML models, but "
                "trailed both the simple multi-factor baseline and SPY."
            ),
        },
        limitations=(
            *_limitations(),
            "The comparison covers three CPU-oriented model families and is not "
            "evidence about every possible machine-learning specification.",
        ),
    )


def _strategy_conclusion(
    strategy: str, metrics: dict[str, object], score: dict[str, object]
) -> str:
    if strategy == "momentum":
        return (
            f"Momentum remained profitable after modeled costs, but its "
            f"{_pct(metrics['maximum_drawdown'])} drawdown and "
            f"{score['label']} robustness label do not support a strong result."
        )
    if strategy == "low_volatility":
        return (
            "Low volatility produced positive full-sample risk-adjusted returns "
            "and shallower losses than momentum, but returns were negative in "
            "both tested bear regimes."
        )
    return (
        "The combined factor strategy had the highest full-sample CAGR and "
        "robustness score of the three rule-based strategies, while still "
        "suffering negative returns in both tested bear regimes."
    )


def _limitations() -> tuple[str, ...]:
    return (
        "Historical backtests do not guarantee future performance.",
        "Daily data and modeled execution do not reproduce intraday liquidity.",
        "Current sector labels are not historically effective GICS classifications.",
        "Survivorship and source-data limitations remain documented in the data "
        "methodology.",
    )


def _pct(value: object) -> str:
    return f"{float(value):.2%}"


def _read_json(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(f"required study artifact is unavailable: {path}")
    return json.loads(path.read_text(encoding="utf-8"))
