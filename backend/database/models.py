"""Relational metadata schema for MarketLab experiments."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

JSON_VALUE = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    """Base class shared by all application metadata tables."""


class Experiment(Base):
    """One immutable research configuration and its execution state."""

    __tablename__ = "experiments"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="ck_experiments_status",
        ),
    )

    experiment_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    strategy_type: Mapped[str] = mapped_column(String(100), index=True)
    dataset_version: Mapped[str] = mapped_column(String(100))
    feature_version: Mapped[str] = mapped_column(String(100))
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON_VALUE)
    date_start: Mapped[date] = mapped_column(Date)
    date_end: Mapped[date] = mapped_column(Date)
    universe: Mapped[dict[str, Any]] = mapped_column(JSON_VALUE)
    capital: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    cost_assumptions: Mapped[dict[str, Any]] = mapped_column(JSON_VALUE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    git_commit: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default="pending")

    strategy_config: Mapped["StrategyConfig | None"] = relationship(
        back_populates="experiment", cascade="all, delete-orphan"
    )
    backtest_summary: Mapped["BacktestSummary | None"] = relationship(
        back_populates="experiment", cascade="all, delete-orphan"
    )
    robustness_result: Mapped["RobustnessResult | None"] = relationship(
        back_populates="experiment", cascade="all, delete-orphan"
    )
    ml_results: Mapped[list["MLResult"]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan"
    )


class StrategyConfig(Base):
    """Normalized strategy configuration associated with an experiment."""

    __tablename__ = "strategy_configs"

    strategy_config_id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[str] = mapped_column(
        ForeignKey("experiments.experiment_id", ondelete="CASCADE"), unique=True
    )
    config: Mapped[dict[str, Any]] = mapped_column(JSON_VALUE)
    experiment: Mapped[Experiment] = relationship(back_populates="strategy_config")


class BacktestSummary(Base):
    """Compact performance and trading summary; time series stay on disk."""

    __tablename__ = "backtest_summaries"

    backtest_summary_id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[str] = mapped_column(
        ForeignKey("experiments.experiment_id", ondelete="CASCADE"), unique=True
    )
    cagr: Mapped[float] = mapped_column(Numeric(14, 10))
    sharpe: Mapped[float] = mapped_column(Numeric(14, 10))
    maximum_drawdown: Mapped[float] = mapped_column(Numeric(14, 10))
    turnover: Mapped[float] = mapped_column(Numeric(14, 10))
    costs: Mapped[Decimal] = mapped_column(Numeric(20, 2))
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON_VALUE, default=dict)
    experiment: Mapped[Experiment] = relationship(back_populates="backtest_summary")


class RobustnessResult(Base):
    """Robustness score and supporting validation diagnostics."""

    __tablename__ = "robustness_results"

    robustness_result_id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[str] = mapped_column(
        ForeignKey("experiments.experiment_id", ondelete="CASCADE"), unique=True
    )
    score: Mapped[float] = mapped_column(Numeric(8, 6))
    details: Mapped[dict[str, Any]] = mapped_column(JSON_VALUE)
    experiment: Mapped[Experiment] = relationship(back_populates="robustness_result")


class MLResult(Base):
    """Out-of-sample result for one model within an experiment."""

    __tablename__ = "ml_results"
    __table_args__ = (
        UniqueConstraint("experiment_id", "model_name", name="uq_ml_model_run"),
    )

    ml_result_id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[str] = mapped_column(
        ForeignKey("experiments.experiment_id", ondelete="CASCADE")
    )
    model_name: Mapped[str] = mapped_column(String(100))
    metrics: Mapped[dict[str, Any]] = mapped_column(JSON_VALUE)
    artifact_path: Mapped[str | None] = mapped_column(Text)
    experiment: Mapped[Experiment] = relationship(back_populates="ml_results")


class Report(Base):
    """Reference to a generated report artifact."""

    __tablename__ = "reports"

    report_id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[str] = mapped_column(
        ForeignKey("experiments.experiment_id", ondelete="CASCADE")
    )
    report_type: Mapped[str] = mapped_column(String(50))
    artifact_path: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    experiment: Mapped[Experiment] = relationship(back_populates="reports")
