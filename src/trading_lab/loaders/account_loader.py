"""Load account data from Alpaca into application models."""

from typing import Any

from alpaca.trading.client import TradingClient

from trading_lab.models.account import AccountSnapshot
from trading_lab.utils.money import to_decimal


def _as_text(value: Any) -> str:
    """Convert plain values and enum-like Alpaca values to text."""
    return str(getattr(value, "value", value))


class AccountLoader:
    """Load and normalize the current Alpaca account state."""

    def __init__(self, client: TradingClient) -> None:
        self.client = client

    def load(self) -> AccountSnapshot:
        """Return a normalized snapshot of the current account."""
        account = self.client.get_account()
        return AccountSnapshot(
            status=_as_text(account.status),
            currency=_as_text(account.currency),
            cash=to_decimal(account.cash),
            buying_power=to_decimal(account.buying_power),
            portfolio_value=to_decimal(account.portfolio_value),
            equity=to_decimal(account.equity),
        )
