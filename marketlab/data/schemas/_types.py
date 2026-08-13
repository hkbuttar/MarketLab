"""Shared runtime type checks for canonical records."""

from dataclasses import fields
from datetime import datetime
from numbers import Real
from typing import Protocol

type Numeric = int | float


class DataRecord(Protocol):
    """Structural type implemented by canonical data records."""

    __dataclass_fields__: dict[str, object]


def column_names(record_type: type[DataRecord]) -> tuple[str, ...]:
    """Return a record's fields in canonical storage order."""

    return tuple(field.name for field in fields(record_type))


def require_datetime(value: object, field_name: str) -> None:
    """Require a timezone-naive or timezone-aware datetime value."""

    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")


def require_string(value: object, field_name: str) -> None:
    """Require a string value."""

    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")


def require_float(value: object, field_name: str) -> None:
    """Require a floating-point value."""

    if not isinstance(value, float):
        raise TypeError(f"{field_name} must be a float")


def require_numeric(value: object, field_name: str, *, optional: bool = False) -> None:
    """Require a real numeric value, excluding booleans."""

    if optional and value is None:
        return
    if isinstance(value, bool) or not isinstance(value, Real):
        qualifier = "numeric or None" if optional else "numeric"
        raise TypeError(f"{field_name} must be {qualifier}")
