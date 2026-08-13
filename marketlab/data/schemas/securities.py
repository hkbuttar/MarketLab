"""Canonical security reference-data record."""

from dataclasses import dataclass

from marketlab.data.schemas._types import column_names, require_string


@dataclass(frozen=True, slots=True)
class SecurityRecord:
    """Reference metadata for one listed security."""

    symbol: str
    company_name: str
    sector: str
    industry: str
    exchange: str

    def __post_init__(self) -> None:
        for field_name in (
            "symbol",
            "company_name",
            "sector",
            "industry",
            "exchange",
        ):
            require_string(getattr(self, field_name), field_name)


SECURITY_COLUMNS = column_names(SecurityRecord)
SECURITY_PRIMARY_KEY = ("symbol",)
