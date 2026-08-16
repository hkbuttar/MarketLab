"""Tests for seeded moving-block bootstrap robustness analysis."""

import math
import random

from marketlab.validation.bootstrap import _summarize, bootstrap_series


def test_bootstrap_is_reproducible_and_preserves_paired_outperformance() -> None:
    benchmark = [0.001 * math.sin(index / 3) for index in range(100)]
    strategy = [value + 0.0005 for value in benchmark]
    risk_free = [0.0] * len(strategy)

    first = bootstrap_series(
        strategy,
        benchmark,
        risk_free,
        iterations=25,
        block_size=5,
        rng=random.Random(7),
    )
    second = bootstrap_series(
        strategy,
        benchmark,
        risk_free,
        iterations=25,
        block_size=5,
        rng=random.Random(7),
    )

    assert first == second
    summary = _summarize(first)
    assert summary["probability_sharpe_positive"] == 1.0
    assert summary["probability_cagr_above_benchmark"] == 1.0
    assert (
        summary["cagr"]["lower_95"]
        <= summary["cagr"]["median"]
        <= summary["cagr"]["upper_95"]
    )
