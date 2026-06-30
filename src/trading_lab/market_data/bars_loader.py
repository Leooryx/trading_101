"""Download historical equity, ETF, and crypto bars from Alpaca."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
from alpaca.data.enums import DataFeed
from alpaca.data.historical.crypto import CryptoHistoricalDataClient
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from trading_lab.config.settings import Settings
from trading_lab.universe.tradable_universe import TradableUniverse


BAR_COLUMNS = ["timestamp", "open", "high", "low", "close", "volume"]


class BarsLoader:
    """Load Alpaca bars while isolating failures to individual symbols."""

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
        self.warnings: list[str] = []

    def load_equity_bars(
        self,
        symbols: list[str],
        start: str,
        end: str,
        timeframe: str = "1Day",
    ) -> dict[str, pd.DataFrame]:
        """Load equity/ETF bars using Alpaca's free IEX feed."""
        self.warnings.clear()
        return self._load_equity_bars(symbols, start, end, timeframe)

    def load_crypto_bars(
        self,
        symbols: list[str],
        start: str,
        end: str,
        timeframe: str = "1Day",
    ) -> dict[str, pd.DataFrame]:
        """Load crypto bars from Alpaca's crypto endpoint."""
        self.warnings.clear()
        return self._load_crypto_bars(symbols, start, end, timeframe)

    def load_universe_bars(
        self,
        start: str,
        end: str,
        timeframe: str = "1Day",
    ) -> dict[str, pd.DataFrame]:
        """Load bars for the complete configured universe."""
        self.warnings.clear()
        equity_bars = self._load_equity_bars(
            self.universe.get_equity_etf_symbols(),
            start,
            end,
            timeframe,
        )
        crypto_bars = self._load_crypto_bars(
            self.universe.get_crypto_symbols(),
            start,
            end,
            timeframe,
        )
        return {**equity_bars, **crypto_bars}

    def _load_equity_bars(
        self,
        symbols: list[str],
        start: str,
        end: str,
        timeframe: str,
    ) -> dict[str, pd.DataFrame]:
        results = {}
        for raw_symbol in symbols:
            symbol = self.universe.normalize_symbol(raw_symbol)
            try:
                request = StockBarsRequest(
                    symbol_or_symbols=symbol,
                    start=self._parse_datetime(start),
                    end=self._parse_datetime(end),
                    timeframe=self._parse_timeframe(timeframe),
                    feed=DataFeed.IEX,
                )
                bar_set = self.stock_client.get_stock_bars(request)
                frame = self._to_dataframe(symbol, bar_set)
                if frame.empty:
                    self._warn(symbol, "no bars returned")
                else:
                    results[symbol] = frame
            except Exception as error:  # Provider failures should not stop the batch.
                self._warn(symbol, str(error))
        return results

    def _load_crypto_bars(
        self,
        symbols: list[str],
        start: str,
        end: str,
        timeframe: str,
    ) -> dict[str, pd.DataFrame]:
        results = {}
        for raw_symbol in symbols:
            symbol = self.universe.normalize_symbol(raw_symbol)
            try:
                request = CryptoBarsRequest(
                    symbol_or_symbols=symbol,
                    start=self._parse_datetime(start),
                    end=self._parse_datetime(end),
                    timeframe=self._parse_timeframe(timeframe),
                )
                bar_set = self.crypto_client.get_crypto_bars(request)
                frame = self._to_dataframe(symbol, bar_set)
                if frame.empty:
                    self._warn(symbol, "no bars returned")
                else:
                    results[symbol] = frame
            except Exception as error:  # Provider failures should not stop the batch.
                self._warn(symbol, str(error))
        return results

    @staticmethod
    def _to_dataframe(symbol: str, bar_set: object) -> pd.DataFrame:
        """Convert one Alpaca BarSet symbol to a clean DataFrame."""
        data = getattr(bar_set, "data", {})
        bars = data.get(symbol, [])
        records = [
            {
                "timestamp": bar.timestamp,
                "open": bar.open,
                "high": bar.high,
                "low": bar.low,
                "close": bar.close,
                "volume": bar.volume,
            }
            for bar in bars
        ]
        return pd.DataFrame.from_records(records, columns=BAR_COLUMNS)

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        """Parse an ISO date or datetime and normalize it to UTC."""
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _parse_timeframe(value: str) -> TimeFrame:
        """Parse strings such as 1Day, 1Hour, or 15Min."""
        normalized = value.strip().lower()
        suffixes = {
            "min": TimeFrameUnit.Minute,
            "hour": TimeFrameUnit.Hour,
            "day": TimeFrameUnit.Day,
            "week": TimeFrameUnit.Week,
            "month": TimeFrameUnit.Month,
        }
        for suffix, unit in suffixes.items():
            if normalized.endswith(suffix):
                amount = normalized[: -len(suffix)]
                if amount.isdigit() and int(amount) > 0:
                    return TimeFrame(int(amount), unit)
        raise ValueError(f"Unsupported timeframe: {value}")

    def _warn(self, symbol: str, message: str) -> None:
        warning = f"Warning: failed to load {symbol}: {message}"
        self.warnings.append(warning)
        print(warning)
