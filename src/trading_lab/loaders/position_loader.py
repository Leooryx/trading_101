"""Load Alpaca positions into a pandas DataFrame."""

from typing import Any

import pandas as pd
from alpaca.trading.client import TradingClient

from trading_lab.utils.money import to_decimal


POSITION_COLUMNS = [
    "symbol",
    "asset_class",
    "quantity",
    "market_value",
    "average_entry_price",
    "current_price",
    "unrealized_pnl",
    "unrealized_pnl_pct",
    "side",
]


def _as_text(value: Any) -> str:
    """Convert plain values and enum-like Alpaca values to text."""
    return str(getattr(value, "value", value))


class PositionLoader:
    """Load and normalize all open Alpaca positions."""

    def __init__(self, client: TradingClient) -> None:
        self.client = client

    def load_all(self) -> pd.DataFrame:
        """Return all open positions with explicit, stable column names."""
        positions = self.client.get_all_positions()
        records = [
            {
                "symbol": position.symbol,
                "asset_class": _as_text(position.asset_class),
                "quantity": to_decimal(position.qty),
                "market_value": to_decimal(position.market_value),
                "average_entry_price": to_decimal(position.avg_entry_price),
                "current_price": to_decimal(position.current_price),
                "unrealized_pnl": to_decimal(position.unrealized_pl),
                "unrealized_pnl_pct": to_decimal(position.unrealized_plpc),
                "side": _as_text(position.side),
            }
            for position in positions
        ]
        return pd.DataFrame.from_records(records, columns=POSITION_COLUMNS)
