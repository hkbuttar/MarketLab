"""Tests for the performance benchmark harness."""

import sys
from pathlib import Path

import pytest

from marketlab.performance import benchmark


def test_peak_rss_normalizes_platform_units(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")
    assert benchmark.peak_rss_mb(8 * 1024 * 1024) == 8
    monkeypatch.setattr(sys, "platform", "linux")
    assert benchmark.peak_rss_mb(8 * 1024) == 8


def test_unknown_workload_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown benchmark workload"):
        benchmark.run_workload("missing", Path("."))


def test_default_suite_excludes_expensive_workloads() -> None:
    assert not set(benchmark.DEFAULT_WORKLOADS) & set(benchmark.EXPENSIVE_WORKLOADS)
