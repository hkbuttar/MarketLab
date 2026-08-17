"""Strategy definition endpoints."""

from fastapi import APIRouter

from marketlab.strategies import STRATEGIES

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.get("")
def list_strategies() -> dict[str, list[dict[str, object]]]:
    """Expose engine-owned strategy definitions without duplicating them."""

    return {
        "items": [
            {
                "name": config.name,
                "factors": [
                    {
                        "name": factor.name,
                        "weight": factor.weight,
                        "higher_is_better": factor.higher_is_better,
                    }
                    for factor in config.factors
                ],
                "selection_fraction": config.selection_fraction,
                "weighting": config.weighting,
                "maximum_position": config.maximum_position,
                "maximum_turnover": config.maximum_turnover,
                "rebalance_frequency": config.rebalance_frequency,
                "signal_delay_sessions": config.signal_delay_sessions,
            }
            for config in STRATEGIES.values()
        ]
    }
