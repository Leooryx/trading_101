"""Simple models used by the market-data layer."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Bar:
    """One normalized OHLCV market-data bar."""

    symbol: str
    timestamp: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


@dataclass(frozen=True)
class MarketDataRequest:
    """A provider-neutral request for historical bars."""

    symbols: list[str]
    start: str
    end: str
    timeframe: str
