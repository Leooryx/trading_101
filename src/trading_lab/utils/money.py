"""Helpers for numeric values returned by broker APIs."""

from decimal import Decimal
from typing import Any


def to_decimal(value: Any) -> Decimal:
    """Convert an Alpaca numeric value to Decimal without float rounding noise."""
    if value is None:
        return Decimal("0")
    return Decimal(str(value))
