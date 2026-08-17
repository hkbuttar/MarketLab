"""Tests for experiment registry discovery."""

import json

import pytest

from backend.services.experiments import experiment_catalog, experiment_detail


def _manifest(root) -> None:
    path = root / "experiments/comparison/run-1.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_id": "run-1",
                "experiment": "comparison",
                "created_at": "2026-08-17T00:00:00Z",
                "command": "python scripts/compare.py",
                "git": {"revision": "abc", "dirty": False},
                "parameters": {"cost_bps": 10},
                "metrics": {"sharpe": 0.5},
                "inputs": [{"path": "input.csv", "size_bytes": 1, "sha256": "a"}],
                "outputs": [{"path": "output.json", "size_bytes": 2, "sha256": "b"}],
            }
        ),
        encoding="utf-8",
    )


def test_experiment_catalog_and_detail(tmp_path) -> None:
    _manifest(tmp_path)

    catalog = experiment_catalog(tmp_path)
    detail = experiment_detail("run-1", tmp_path)

    assert catalog[0].name == "comparison"
    assert catalog[0].input_count == 1
    assert detail.parameters == {"cost_bps": 10}
    assert detail.outputs[0].sha256 == "b"


def test_experiment_detail_is_root_bounded(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        experiment_detail("../secret", tmp_path)
