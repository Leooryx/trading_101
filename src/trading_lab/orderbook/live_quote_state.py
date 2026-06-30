"""Thread-safe state shared by Alpaca streams and Streamlit."""

from datetime import datetime, timezone
from threading import Lock

from trading_lab.orderbook.live_quote_models import LiveQuote


class LiveQuoteState:
    """Store the latest quote per symbol and recoverable stream errors."""

    def __init__(self) -> None:
        self.latest_quotes: dict[str, LiveQuote] = {}
        self.last_update_time: datetime | None = None
        self.errors: list[str] = []
        self._lock = Lock()

    def update_quote(self, quote: LiveQuote) -> None:
        """Atomically store the newest quote for its normalized symbol."""
        with self._lock:
            self.latest_quotes[quote.symbol.strip().upper()] = quote
            self.last_update_time = datetime.now(timezone.utc)

    def get_quote(self, symbol: str) -> LiveQuote | None:
        """Return the latest quote for a symbol, if one exists."""
        with self._lock:
            return self.latest_quotes.get(symbol.strip().upper())

    def get_all_quotes(self) -> list[LiveQuote]:
        """Return a stable copy of all latest quotes sorted by symbol."""
        with self._lock:
            return sorted(self.latest_quotes.values(), key=lambda quote: quote.symbol)

    def add_error(self, message: str) -> None:
        """Record a readable, non-fatal stream error."""
        with self._lock:
            self.errors.append(message)

    def get_errors(self) -> list[str]:
        """Return a copy of all current errors."""
        with self._lock:
            return list(self.errors)

    def clear_errors(self) -> None:
        """Remove all recorded errors."""
        with self._lock:
            self.errors.clear()
