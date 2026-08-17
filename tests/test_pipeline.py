"""Tests for resumable end-to-end pipeline orchestration."""

from pathlib import Path
from subprocess import CompletedProcess

import pytest

from marketlab.pipeline import PipelineTask, run_tasks, select_tasks


def test_stage_selection_is_inclusive_and_ordered() -> None:
    tasks = select_tasks(start_at="validation", through="ml")
    assert tasks
    assert {task.stage for task in tasks} == {"validation", "ml"}
    assert tasks[0].stage == "validation"
    assert tasks[-1].stage == "ml"


def test_reverse_stage_range_is_rejected() -> None:
    with pytest.raises(ValueError, match="start stage"):
        select_tasks(start_at="reporting", through="data")


def test_completed_task_is_skipped(tmp_path: Path) -> None:
    output = tmp_path / "artifact.json"
    output.write_text("{}", encoding="utf-8")
    task = PipelineTask("data", "example", "example.py", ("artifact.json",))

    records = run_tasks((task,), tmp_path, runner=_unexpected_runner)

    assert records[0]["status"] == "skipped"


def test_dry_run_does_not_execute_missing_task(tmp_path: Path) -> None:
    task = PipelineTask("data", "example", "example.py", ("artifact.json",))
    records = run_tasks((task,), tmp_path, dry_run=True, runner=_unexpected_runner)
    assert records[0]["status"] == "planned"


def test_task_must_create_declared_output(tmp_path: Path) -> None:
    task = PipelineTask("data", "example", "example.py", ("artifact.json",))

    def runner(*args: object, **kwargs: object) -> CompletedProcess[str]:
        return CompletedProcess(args, 0)

    with pytest.raises(RuntimeError, match="expected artifacts"):
        run_tasks((task,), tmp_path, runner=runner)


def _unexpected_runner(*args: object, **kwargs: object) -> CompletedProcess[str]:
    raise AssertionError("runner should not have been called")
