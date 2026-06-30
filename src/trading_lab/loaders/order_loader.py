"""Load Alpaca orders into a pandas DataFrame."""

from typing import Any

import pandas as pd
from alpaca.trading.client import TradingClient


ORDER_COLUMNS = [
    "symbol",
    "side",
    "quantity",
    "notional",
    "order_type",
    "status",
    "submitted_at",
    "filled_quantity",
    "filled_average_price",
]


def _as_optional_text(value: Any) -> str | None:
    """Convert Alpaca values, including dates and enums, to safe text."""
    if value is None:
        return None

    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        return str(isoformat())

    return str(getattr(value, "value", value))


def _as_text(value: Any) -> str:
    """Convert an expected Alpaca value to text."""
    return _as_optional_text(value) or ""


class OrderLoader:
    """Load and normalize all open Alpaca orders."""

    def __init__(self, client: TradingClient) -> None:
        self.client = client

    def load_open_orders(self) -> pd.DataFrame:
        """Return open orders with explicit, stable column names."""
        orders = self.client.get_orders()
        records = [
            {
                "symbol": order.symbol,
                "side": _as_text(order.side),
                "quantity": _as_optional_text(order.qty),
                "notional": _as_optional_text(order.notional),
                "order_type": _as_text(order.type),
                "status": _as_text(order.status),
                "submitted_at": _as_optional_text(order.submitted_at),
                "filled_quantity": _as_optional_text(order.filled_qty),
                "filled_average_price": _as_optional_text(order.filled_avg_price),
            }
            for order in orders
        ]
        return pd.DataFrame.from_records(records, columns=ORDER_COLUMNS)
