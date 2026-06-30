"""Internal position data models."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Position:
    """A normalized open trading position."""

    symbol: str
    asset_class: str
    quantity: Decimal
    market_value: Decimal
    average_entry_price: Decimal
    current_price: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal
    side: str

    def is_long(self) -> bool:
        """Return True when this is a long position."""
        return self.side.casefold() == "long"

    def is_short(self) -> bool:
        """Return True when this is a short position."""
        return self.side.casefold() == "short"

    def is_option(self) -> bool:
        """Return True when this position contains an option contract."""
        return self.asset_class.casefold() in {"option", "options", "us_option"}
