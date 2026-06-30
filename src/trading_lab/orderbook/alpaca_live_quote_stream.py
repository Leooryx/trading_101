"""Background Alpaca top-of-book quote streaming.

V1 intentionally streams only the best bid and ask. A future crypto-specific
component may reconstruct multiple depth levels and compute liquidity metrics.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from threading import Event, Thread, current_thread
from typing import Any

from alpaca.data.enums import DataFeed
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.live.crypto import CryptoDataStream
from alpaca.data.live.stock import StockDataStream
from alpaca.data.requests import StockLatestQuoteRequest

from trading_lab.config.settings import Settings
from trading_lab.orderbook.live_quote_models import (
    LiveQuote,
    compute_mid,
    compute_spread,
    compute_spread_bps,
)
from trading_lab.orderbook.live_quote_state import LiveQuoteState
from trading_lab.universe.tradable_universe import TradableUniverse
from trading_lab.utils.money import to_decimal
from trading_lab.utils.options import extract_underlying_symbol


class AlpacaLiveQuoteStream:
    """Subscribe to Alpaca quotes and update shared state in a daemon thread."""

    def __init__(
        self,
        symbols: list[str],
        instrument_type: str,
        quote_state: LiveQuoteState,
    ) -> None:
        universe = TradableUniverse()
        self.symbols = list(
            dict.fromkeys(universe.normalize_symbol(symbol) for symbol in symbols)
        )
        self.instrument_type = self._normalize_instrument_type(instrument_type)
        self.quote_state = quote_state
        self._stream: Any = None
        self._thread: Thread | None = None
        self._running = Event()

    def start(self) -> None:
        """Create the appropriate stream and start it in the background."""
        if self.is_running():
            return
        if not self.symbols:
            self.quote_state.add_error("No symbols were selected for streaming.")
            return

        self._initialize_missing_quotes()
        if self.instrument_type == "option" and not self._options_are_contracts():
            self.quote_state.add_error(
                "Options streaming requires full OCC contract symbols. The selected "
                "SPY/QQQ rows are underlyings only; contract discovery is not part of V1."
            )
            return

        try:
            Settings.validate_alpaca()
            if self.instrument_type == "overnight":
                self._bootstrap_overnight_quotes()
            self._stream = self._create_stream()
            self._stream.subscribe_quotes(self._handle_quote, *self.symbols)
            self._running.set()
            self._thread = Thread(
                target=self._run_stream,
                name=f"alpaca-{self.instrument_type}-quotes",
                daemon=True,
            )
            self._thread.start()
        except Exception as error:
            self._running.clear()
            self.quote_state.add_error(f"Could not start Alpaca quote stream: {error}")

    def stop(self) -> None:
        """Ask Alpaca to stop and briefly join the background thread."""
        self._running.clear()
        if self._stream is not None:
            try:
                self._stream.stop()
            except Exception as error:
                self.quote_state.add_error(f"Could not stop quote stream cleanly: {error}")
        if (
            self._thread is not None
            and self._thread.is_alive()
            and self._thread is not current_thread()
        ):
            self._thread.join(timeout=3)

    def is_running(self) -> bool:
        """Return whether the background stream is expected to be active."""
        return self._running.is_set()

    async def _handle_quote(self, quote: Any) -> None:
        """Normalize one Alpaca quote callback into LiveQuote state."""
        self.quote_state.update_quote(
            self._to_live_quote(
                quote,
                source=f"alpaca_{self.instrument_type}_stream",
            )
        )

    def _to_live_quote(self, quote: Any, source: str) -> LiveQuote:
        """Convert an Alpaca REST or WebSocket quote to the shared model."""
        symbol = str(self._field(quote, "symbol", "")).upper()
        bid = self._positive_decimal(self._field(quote, "bid_price"))
        ask = self._positive_decimal(self._field(quote, "ask_price"))
        bid_size = self._decimal_or_none(self._field(quote, "bid_size"))
        ask_size = self._decimal_or_none(self._field(quote, "ask_size"))
        timestamp = self._timestamp(self._field(quote, "timestamp"))
        status = "live" if bid is not None or ask is not None else "missing"
        return LiveQuote(
            symbol=symbol,
            instrument_type=self.instrument_type,
            bid_price=bid,
            bid_size=bid_size,
            ask_price=ask,
            ask_size=ask_size,
            mid_price=compute_mid(bid, ask),
            spread=compute_spread(bid, ask),
            spread_bps=compute_spread_bps(bid, ask),
            timestamp=timestamp,
            source=source,
            status=status,
        )

    def _bootstrap_overnight_quotes(self) -> None:
        """Load latest overnight quotes once before WebSocket updates arrive."""
        try:
            client = StockHistoricalDataClient(
                api_key=Settings.ALPACA_API_KEY,
                secret_key=Settings.ALPACA_SECRET_KEY,
            )
            quotes = client.get_stock_latest_quote(
                StockLatestQuoteRequest(
                    symbol_or_symbols=self.symbols,
                    feed=DataFeed.OVERNIGHT,
                )
            )
            for quote in quotes.values():
                self.quote_state.update_quote(
                    self._to_live_quote(quote, source="alpaca_overnight_rest")
                )
        except Exception as error:
            self.quote_state.add_error(
                f"Overnight REST quote bootstrap unavailable: {error}"
            )

    def _run_stream(self) -> None:
        try:
            self._stream.run()
        except Exception as error:
            self.quote_state.add_error(f"Alpaca quote stream stopped: {error}")
        finally:
            self._running.clear()

    def _create_stream(self) -> Any:
        common = {
            "api_key": Settings.ALPACA_API_KEY,
            "secret_key": Settings.ALPACA_SECRET_KEY,
        }
        if self.instrument_type == "equity":
            return StockDataStream(feed=DataFeed.IEX, **common)
        if self.instrument_type == "overnight":
            return StockDataStream(feed=DataFeed.OVERNIGHT, **common)
        if self.instrument_type == "crypto":
            return CryptoDataStream(**common)
        if self.instrument_type == "option":
            try:
                from alpaca.data.live.option import OptionDataStream
            except ImportError as error:
                raise RuntimeError(
                    "Option quote streaming is unavailable in this alpaca-py version."
                ) from error
            return OptionDataStream(**common)
        raise ValueError(f"Unsupported instrument type: {self.instrument_type}")

    def _initialize_missing_quotes(self) -> None:
        for symbol in self.symbols:
            self.quote_state.update_quote(
                LiveQuote(
                    symbol=symbol,
                    instrument_type=self.instrument_type,
                    bid_price=None,
                    bid_size=None,
                    ask_price=None,
                    ask_size=None,
                    mid_price=None,
                    spread=None,
                    spread_bps=None,
                    timestamp=None,
                    source="waiting_for_alpaca",
                    status="missing",
                )
            )

    def _options_are_contracts(self) -> bool:
        for symbol in self.symbols:
            try:
                extract_underlying_symbol(symbol)
            except ValueError:
                return False
        return True

    @staticmethod
    def _normalize_instrument_type(value: str) -> str:
        normalized = value.strip().lower()
        aliases = {
            "equity / etf": "equity",
            "equity/etf": "equity",
            "etf": "equity",
            "24/5": "overnight",
            "options": "option",
        }
        return aliases.get(normalized, normalized)

    @staticmethod
    def _field(value: Any, name: str, default: Any = None) -> Any:
        if isinstance(value, dict):
            return value.get(name, default)
        return getattr(value, name, default)

    @staticmethod
    def _decimal_or_none(value: Any) -> Decimal | None:
        return None if value is None else to_decimal(value)

    @classmethod
    def _positive_decimal(cls, value: Any) -> Decimal | None:
        converted = cls._decimal_or_none(value)
        if converted is None or converted <= Decimal("0"):
            return None
        return converted

    @staticmethod
    def _timestamp(value: Any) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)
