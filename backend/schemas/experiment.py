"""Experiment registry API schemas."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class ExperimentArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    size_bytes: int
    sha256: str


class ExperimentListItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    name: str
    created_at: str
    git_revision: str | None
    git_dirty: bool | None
    input_count: int
    output_count: int


class ExperimentDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int
    run_id: str
    name: str
    created_at: str
    command: str
    git_revision: str | None
    git_dirty: bool | None
    parameters: dict[str, Any]
    metrics: dict[str, Any]
    inputs: list[ExperimentArtifact]
    outputs: list[ExperimentArtifact]
