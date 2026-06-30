"""Internal order data models."""

from dataclasses import dataclass


@dataclass(frozen=True)
class OrderSummary:
    """A normalized summary of an Alpaca order."""

    symbol: str
    side: str
    quantity: str | None
    notional: str | None
    order_type: str
    status: str
    submitted_at: str | None
    filled_quantity: str | None
    filled_average_price: str | None
