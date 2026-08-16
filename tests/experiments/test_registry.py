import hashlib
import json
from pathlib import Path

import pytest

from marketlab.experiments.registry import record_experiment


def test_records_reproducible_artifact_manifest(tmp_path: Path) -> None:
    source = tmp_path / "input.csv"
    result = tmp_path / "result.json"
    source.write_text("date,value\n2024-01-01,1\n", encoding="utf-8")
    result.write_text('{"cagr": 0.1}\n', encoding="utf-8")

    manifest_path = record_experiment(
        "sample_run",
        command="python scripts/sample.py",
        parameters={"cost_bps": 10.0},
        inputs=[source],
        outputs=[result],
        metrics={"cagr": 0.1},
        project_root=tmp_path,
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["experiment"] == "sample_run"
    assert manifest["parameters"] == {"cost_bps": 10.0}
    assert manifest["metrics"] == {"cagr": 0.1}
    assert manifest["inputs"][0] == {
        "path": "input.csv",
        "size_bytes": source.stat().st_size,
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }
    assert manifest["outputs"][0]["path"] == "result.json"


def test_rejects_artifact_outside_project_root(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-marketlab-test.txt"
    outside.write_text("outside", encoding="utf-8")

    with pytest.raises(ValueError, match="outside project root"):
        record_experiment(
            "sample_run",
            command="sample",
            parameters={},
            inputs=[outside],
            outputs=[],
            metrics={},
            project_root=tmp_path,
        )

    outside.unlink()
