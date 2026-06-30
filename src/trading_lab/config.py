"""Compatibility wrapper for the configuration package."""

from trading_lab.config import (  # noqa: F401
    ALPACA_API_KEY,
    ALPACA_PAPER,
    ALPACA_SECRET_KEY,
    PROJECT_ROOT,
    Settings,
    validate_alpaca_config,
)


__all__ = [
    "ALPACA_API_KEY",
    "ALPACA_PAPER",
    "ALPACA_SECRET_KEY",
    "PROJECT_ROOT",
    "Settings",
    "validate_alpaca_config",
]
