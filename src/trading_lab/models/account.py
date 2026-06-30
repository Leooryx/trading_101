"""Internal account data models."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class AccountSnapshot:
    """A point-in-time view of an Alpaca account."""

    status: str
    currency: str
    cash: Decimal
    buying_power: Decimal
    portfolio_value: Decimal
    equity: Decimal
