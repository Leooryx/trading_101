"""Configuration exports, including compatibility with the old config module."""

from trading_lab.config.settings import PROJECT_ROOT, Settings


ALPACA_API_KEY = Settings.ALPACA_API_KEY
ALPACA_SECRET_KEY = Settings.ALPACA_SECRET_KEY
ALPACA_PAPER = Settings.ALPACA_PAPER


def validate_alpaca_config() -> None:
    """Validate credentials using the current settings implementation."""
    Settings.validate_alpaca()


__all__ = [
    "ALPACA_API_KEY",
    "ALPACA_PAPER",
    "ALPACA_SECRET_KEY",
    "PROJECT_ROOT",
    "Settings",
    "validate_alpaca_config",
]
