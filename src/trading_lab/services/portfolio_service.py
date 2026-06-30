"""Build a complete portfolio view from normalized broker data."""

from dataclasses import dataclass
from decimal import Decimal

import pandas as pd

from trading_lab.loaders.account_loader import AccountLoader
from trading_lab.loaders.order_loader import OrderLoader
from trading_lab.loaders.position_loader import PositionLoader
from trading_lab.models.account import AccountSnapshot


@dataclass(frozen=True)
class PortfolioSnapshot:
    """A complete point-in-time view of the trading portfolio."""

    account: AccountSnapshot
    positions: pd.DataFrame
    open_orders: pd.DataFrame

    def get_long_positions(self) -> pd.DataFrame:
        """Return only long positions."""
        return self.positions.loc[
            self.positions["side"].str.casefold().eq("long")
        ].copy()

    def get_short_positions(self) -> pd.DataFrame:
        """Return only short positions."""
        return self.positions.loc[
            self.positions["side"].str.casefold().eq("short")
        ].copy()

    def get_option_positions(self) -> pd.DataFrame:
        """Return only option positions, whether long or short."""
        option_classes = {"option", "options", "us_option"}
        return self.positions.loc[
            self.positions["asset_class"].str.casefold().isin(option_classes)
        ].copy()


class PortfolioService:
    """Coordinate account, position, and order loaders."""

    def __init__(
        self,
        account_loader: AccountLoader,
        position_loader: PositionLoader,
        order_loader: OrderLoader,
    ) -> None:
        self.account_loader = account_loader
        self.position_loader = position_loader
        self.order_loader = order_loader

    def get_snapshot(self) -> PortfolioSnapshot:
        """Load broker data and return one consolidated portfolio snapshot."""
        account = self.account_loader.load()
        positions = self.position_loader.load_all()
        open_orders = self.order_loader.load_open_orders()

        positions = positions.copy()
        if account.portfolio_value != Decimal("0"):
            positions["portfolio_weight"] = positions["market_value"].map(
                lambda value: value / account.portfolio_value
            )
        else:
            positions["portfolio_weight"] = Decimal("0")

        return PortfolioSnapshot(
            account=account,
            positions=positions,
            open_orders=open_orders,
        )
