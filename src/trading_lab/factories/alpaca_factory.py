"""Factory for authenticated Alpaca clients."""

from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.trading.client import TradingClient

from trading_lab.config.settings import Settings


class AlpacaClientFactory:
    """Create Alpaca API clients from validated application settings."""

    @staticmethod
    def create_trading_client() -> TradingClient:
        """Create a trading client for the configured paper or live account."""
        Settings.validate_alpaca()
        return TradingClient(
            api_key=Settings.ALPACA_API_KEY,
            secret_key=Settings.ALPACA_SECRET_KEY,
            paper=Settings.ALPACA_PAPER,
        )

    @staticmethod
    def create_option_data_client() -> OptionHistoricalDataClient:
        """Create a client for Alpaca option market-data snapshots."""
        Settings.validate_alpaca()
        return OptionHistoricalDataClient(
            api_key=Settings.ALPACA_API_KEY,
            secret_key=Settings.ALPACA_SECRET_KEY,
        )
