"""Feature registration and discovery."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FeatureDefinition:
    """Stable metadata for one research feature."""

    name: str
    family: str
    description: str


FEATURES = {
    item.name: item
    for item in (
        FeatureDefinition("return_1d", "technical", "One-day adjusted return."),
        FeatureDefinition("momentum_21", "technical", "21-session return."),
        FeatureDefinition("momentum_63", "technical", "63-session return."),
        FeatureDefinition("momentum_126", "technical", "126-session return."),
        FeatureDefinition("momentum_252", "technical", "252-session return."),
        FeatureDefinition(
            "momentum_12_1", "technical", "252-to-21-session adjusted return."
        ),
        FeatureDefinition(
            "volatility_21", "technical", "Annualized 21-session volatility."
        ),
        FeatureDefinition(
            "volatility_63", "technical", "Annualized 63-session volatility."
        ),
        FeatureDefinition(
            "average_dollar_volume_21",
            "technical",
            "Mean 21-session close times volume.",
        ),
        FeatureDefinition("book_to_market", "fundamental", "Book equity / market cap."),
        FeatureDefinition("earnings_yield", "fundamental", "Net income / market cap."),
        FeatureDefinition("sales_to_price", "fundamental", "Revenue / market cap."),
        FeatureDefinition(
            "gross_profitability", "fundamental", "Gross profit / assets."
        ),
        FeatureDefinition("return_on_assets", "fundamental", "Net income / assets."),
        FeatureDefinition("leverage", "fundamental", "Debt / assets."),
        FeatureDefinition("free_cash_flow_yield", "fundamental", "FCF / market cap."),
        FeatureDefinition(
            "revenue_growth_yoy", "fundamental", "Same-period revenue growth."
        ),
        FeatureDefinition(
            "net_income_growth_yoy", "fundamental", "Same-period income growth."
        ),
        FeatureDefinition(
            "asset_growth_yoy", "fundamental", "Same-period asset growth."
        ),
        FeatureDefinition(
            "free_cash_flow_growth_yoy",
            "fundamental",
            "Same-period free-cash-flow growth.",
        ),
    )
}


def get_feature(name: str) -> FeatureDefinition:
    """Return registered feature metadata or raise for an unknown name."""

    return FEATURES[name]
