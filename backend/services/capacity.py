"""Read persisted strategy-capacity diagnostics."""

import json
from pathlib import Path

from backend.schemas.capacity import CapacityResponse, StrategyCapacity


def capacity_report(
    project_root: Path = Path("."),
) -> CapacityResponse:
    path = project_root.resolve() / "reports/validation/capacity.json"
    if not path.is_file():
        raise FileNotFoundError(path)
    document = json.loads(path.read_text(encoding="utf-8"))
    assumptions = document["assumptions"]
    return CapacityResponse(
        generated_at=document["generated_at"],
        maximum_adv_participation=assumptions["maximum_adv_participation"],
        liquidation_days=assumptions["liquidation_days"],
        strategies=[
            StrategyCapacity(name=name, **values)
            for name, values in sorted(document["strategies"].items())
        ],
    )
