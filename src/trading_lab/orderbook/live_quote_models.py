"""Top-of-book live quote model and Decimal calculations."""

from dataclasses import dataclass
from decimal import Decimal


def compute_mid(
    bid: Decimal | None,
    ask: Decimal | None,
) -> Decimal | None:
    """Return the midpoint when both bid and ask are available."""
    if bid is None or ask is None:
        return None
    return (bid + ask) / Decimal("2")


def compute_spread(
    bid: Decimal | None,
    ask: Decimal | None,
) -> Decimal | None:
    """Return ask minus bid when both prices are available."""
    if bid is None or ask is None:
        return None
    return ask - bid


def compute_spread_bps(
    bid: Decimal | None,
    ask: Decimal | None,
) -> Decimal | None:
    """Return the quoted spread as basis points of the midpoint."""
    mid = compute_mid(bid, ask)
    spread = compute_spread(bid, ask)
    if mid is None or spread is None or mid == Decimal("0"):
        return None
    return spread / mid * Decimal("10000")


@dataclass(frozen=True)
class LiveQuote:
    """Latest top-of-book quote for one monitored symbol."""

    symbol: str
    instrument_type: str
    bid_price: Decimal | None
    bid_size: Decimal | None
    ask_price: Decimal | None
    ask_size: Decimal | None
    mid_price: Decimal | None
    spread: Decimal | None
    spread_bps: Decimal | None
    timestamp: str | None
    source: str
    status: str
