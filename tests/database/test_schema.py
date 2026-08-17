from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database.models import Base, Experiment, MLResult
from backend.database.session import database_url


def _experiment() -> Experiment:
    now = datetime.now(UTC)
    return Experiment(
        experiment_id="experiment-1",
        name="ML comparison",
        strategy_type="ranking",
        dataset_version="v1-v2-20260815",
        feature_version="1",
        parameters={"top_fraction": 0.2},
        date_start=date(2018, 1, 31),
        date_end=date(2026, 6, 30),
        universe={"asset_class": "US equities"},
        capital=Decimal("1000000.00"),
        cost_assumptions={"transaction_cost_bps": 10.0},
        created_at=now,
        updated_at=now,
        git_commit="a" * 40,
        status="completed",
    )


def test_schema_creates_only_compact_metadata_tables() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    assert set(inspect(engine).get_table_names()) == {
        "backtest_summaries",
        "experiments",
        "ml_results",
        "reports",
        "robustness_results",
        "strategy_configs",
    }


def test_ml_model_name_is_unique_within_experiment() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    experiment = _experiment()
    experiment.ml_results.extend(
        [
            MLResult(model_name="elastic_net", metrics={}, artifact_path=None),
            MLResult(model_name="elastic_net", metrics={}, artifact_path=None),
        ]
    )

    with Session(engine) as session, pytest.raises(IntegrityError):
        session.add(experiment)
        session.commit()


def test_database_url_must_be_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MARKETLAB_DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="MARKETLAB_DATABASE_URL"):
        database_url()
