"""Best-effort current quotes from Alpaca stock and crypto endpoints."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from alpaca.data.enums import DataFeed
from alpaca.data.historical.crypto import CryptoHistoricalDataClient
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import (
    CryptoLatestQuoteRequest,
    CryptoLatestTradeRequest,
    StockLatestQuoteRequest,
    StockLatestTradeRequest,
)

from trading_lab.config.settings import Settings
from trading_lab.market_data.quote_models import MarketQuote
from trading_lab.universe.tradable_universe import TradableUniverse
from trading_lab.utils.money import to_decimal


class MarketQuoteLoader:
    """Load current executable quotes without propagating provider failures."""

    def __init__(
        self,
        stock_client: StockHistoricalDataClient | None = None,
        crypto_client: CryptoHistoricalDataClient | None = None,
        universe: TradableUniverse | None = None,
    ) -> None:
        if stock_client is None or crypto_client is None:
            Settings.validate_alpaca()
        self.stock_client = stock_client or StockHistoricalDataClient(
            api_key=Settings.ALPACA_API_KEY,
            secret_key=Settings.ALPACA_SECRET_KEY,
        )
        self.crypto_client = crypto_client or CryptoHistoricalDataClient(
            api_key=Settings.ALPACA_API_KEY,
            secret_key=Settings.ALPACA_SECRET_KEY,
        )
        self.universe = universe or TradableUniverse()

    def get_quote(self, symbol: str) -> MarketQuote:
        """Return a stock or crypto quote, including failure details in source."""
        normalized = self.universe.normalize_symbol(symbol)
        if self.universe.is_crypto(normalized):
            return self._get_crypto_quote(normalized)
        return self._get_stock_quote(normalized, DataFeed.IEX)

    def get_overnight_quote(self, symbol: str) -> MarketQuote:
        """Return Alpaca's indicative overnight quote for a US-listed symbol."""
        normalized = self.universe.normalize_symbol(symbol)
        return self._get_stock_quote(normalized, DataFeed.OVERNIGHT)

    def _get_stock_quote(self, symbol: str, feed: DataFeed) -> MarketQuote:
        errors = []
        quote = None
        trade = None
        try:
            quotes = self.stock_client.get_stock_latest_quote(
                StockLatestQuoteRequest(
                    symbol_or_symbols=symbol,
                    feed=feed,
                )
            )
            quote = quotes.get(symbol)
        except Exception as error:
            errors.append(f"quote: {error}")
        try:
            trades = self.stock_client.get_stock_latest_trade(
                StockLatestTradeRequest(
                    symbol_or_symbols=symbol,
                    feed=feed,
                )
            )
            trade = trades.get(symbol)
        except Exception as error:
            errors.append(f"trade: {error}")
        return self._build_quote(
            symbol,
            quote,
            trade,
            f"alpaca_stock_{feed.value}",
            errors,
        )

    def _get_crypto_quote(self, symbol: str) -> MarketQuote:
        errors = []
        quote = None
        trade = None
        try:
            quotes = self.crypto_client.get_crypto_latest_quote(
                CryptoLatestQuoteRequest(symbol_or_symbols=symbol)
            )
            quote = quotes.get(symbol)
        except Exception as error:
            errors.append(f"quote: {error}")
        try:
            trades = self.crypto_client.get_crypto_latest_trade(
                CryptoLatestTradeRequest(symbol_or_symbols=symbol)
            )
            trade = trades.get(symbol)
        except Exception as error:
            errors.append(f"trade: {error}")
        return self._build_quote(symbol, quote, trade, "alpaca_crypto", errors)

    @classmethod
    def _build_quote(
        cls,
        symbol: str,
        quote: Any,
        trade: Any,
        source: str,
        errors: list[str],
    ) -> MarketQuote:
        bid = cls._price(getattr(quote, "bid_price", None))
        ask = cls._price(getattr(quote, "ask_price", None))
        mid = (bid + ask) / Decimal("2") if bid and ask else None
        last = cls._price(getattr(trade, "price", None))
        timestamp = getattr(quote, "timestamp", None) or getattr(
            trade, "timestamp", None
        )
        source_detail = source
        if errors:
            source_detail += " | " + " | ".join(errors)
        if quote is None and trade is None and not errors:
            source_detail += " | no data returned"
        return MarketQuote(
            symbol=symbol,
            bid_price=bid,
            ask_price=ask,
            mid_price=mid,
            last_price=last,
            timestamp=cls._timestamp(timestamp),
            source=source_detail,
        )

    @staticmethod
    def _price(value: Any) -> Decimal | None:
        if value is None:
            return None
        price = to_decimal(value)
        return price if price > Decimal("0") else None

    @staticmethod
    def _timestamp(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)
