"""Provider-neutral current market quote model."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class MarketQuote:
    """Best-effort current prices used by pre-trade simulations."""

    symbol: str
    bid_price: Decimal | None
    ask_price: Decimal | None
    mid_price: Decimal | None
    last_price: Decimal | None
    timestamp: str | None
    source: str

    def estimated_fill_price(self, side: str) -> Decimal | None:
        """Estimate a market fill using the executable side of the quote."""
        normalized_side = side.strip().lower()
        if normalized_side == "buy" and self.ask_price is not None:
            return self.ask_price
        if normalized_side == "sell" and self.bid_price is not None:
            return self.bid_price
        return self.mid_price or self.last_price

    def reference_price(self) -> Decimal | None:
        """Return a neutral valuation price for current positions."""
        return (
            self.mid_price
            or self.last_price
            or self.bid_price
            or self.ask_price
        )
