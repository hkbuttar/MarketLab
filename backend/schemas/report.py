"""Research report API schemas."""

from pydantic import BaseModel, ConfigDict


class ReportItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    path: str
    category: str
    format: str
    size_bytes: int
    updated_at: str


class ReportContent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report: ReportItem
    content: str
