"""Offline tests for the portfolio visibility layer."""

from __future__ import annotations

import io
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pandas as pd

from trading_lab.config import validate_alpaca_config
from trading_lab.factories import alpaca_factory
from trading_lab.loaders.account_loader import AccountLoader
from trading_lab.loaders.order_loader import ORDER_COLUMNS, OrderLoader
from trading_lab.loaders.position_loader import POSITION_COLUMNS, PositionLoader
from trading_lab.models.account import AccountSnapshot
from trading_lab.reporting.console_reporter import ConsolePortfolioReporter
from trading_lab.services.portfolio_service import PortfolioService, PortfolioSnapshot
from trading_lab.utils.money import to_decimal


class MoneyTests(unittest.TestCase):
    """Test safe Decimal conversion."""

    def test_to_decimal_handles_none_and_numeric_values(self) -> None:
        self.assertEqual(to_decimal(None), Decimal("0"))
        self.assertEqual(to_decimal("12.34"), Decimal("12.34"))
        self.assertEqual(to_decimal(1.5), Decimal("1.5"))


class FactoryTests(unittest.TestCase):
    """Test construction of the Alpaca trading client."""

    def test_factory_validates_settings_and_uses_paper_flag(self) -> None:
        with (
            patch.object(alpaca_factory.Settings, "validate_alpaca") as validate,
            patch.object(alpaca_factory.Settings, "ALPACA_API_KEY", "test-key"),
            patch.object(alpaca_factory.Settings, "ALPACA_SECRET_KEY", "test-secret"),
            patch.object(alpaca_factory.Settings, "ALPACA_PAPER", True),
            patch.object(alpaca_factory, "TradingClient") as trading_client,
        ):
            alpaca_factory.AlpacaClientFactory.create_trading_client()

        validate.assert_called_once_with()
        trading_client.assert_called_once_with(
            api_key="test-key",
            secret_key="test-secret",
            paper=True,
        )


class LoaderTests(unittest.TestCase):
    """Test normalization of Alpaca-like response objects."""

    def test_account_loader(self) -> None:
        client = Mock()
        client.get_account.return_value = SimpleNamespace(
            status="ACTIVE",
            currency="USD",
            cash="100.00",
            buying_power="200.00",
            portfolio_value="250.00",
            equity="250.00",
        )

        account = AccountLoader(client).load()

        self.assertEqual(account.cash, Decimal("100.00"))
        self.assertEqual(account.status, "ACTIVE")
        client.get_account.assert_called_once_with()

    def test_position_loader_returns_dataframe_with_explicit_columns(self) -> None:
        client = Mock()
        client.get_all_positions.return_value = [
            SimpleNamespace(
                symbol="AAPL",
                asset_class="us_equity",
                qty="2",
                market_value="400",
                avg_entry_price="180",
                current_price="200",
                unrealized_pl="40",
                unrealized_plpc="0.1111",
                side="long",
            )
        ]

        positions = PositionLoader(client).load_all()

        self.assertIsInstance(positions, pd.DataFrame)
        self.assertEqual(positions.columns.tolist(), POSITION_COLUMNS)
        self.assertEqual(positions.loc[0, "quantity"], Decimal("2"))
        self.assertEqual(positions.loc[0, "symbol"], "AAPL")
        client.get_all_positions.assert_called_once_with()

    def test_empty_position_loader_keeps_columns(self) -> None:
        client = Mock()
        client.get_all_positions.return_value = []

        positions = PositionLoader(client).load_all()

        self.assertTrue(positions.empty)
        self.assertEqual(positions.columns.tolist(), POSITION_COLUMNS)

    def test_order_loader_returns_dataframe_and_converts_dates(self) -> None:
        client = Mock()
        submitted_at = datetime(2026, 6, 30, 8, 0, tzinfo=timezone.utc)
        client.get_orders.return_value = [
            SimpleNamespace(
                symbol="MSFT",
                side="buy",
                qty="1",
                notional=None,
                type="limit",
                status="new",
                submitted_at=submitted_at,
                filled_qty="0",
                filled_avg_price=None,
            )
        ]

        orders = OrderLoader(client).load_open_orders()

        self.assertIsInstance(orders, pd.DataFrame)
        self.assertEqual(orders.columns.tolist(), ORDER_COLUMNS)
        self.assertEqual(orders.loc[0, "submitted_at"], submitted_at.isoformat())
        self.assertIsNone(orders.loc[0, "notional"])
        client.get_orders.assert_called_once_with()


class PortfolioServiceTests(unittest.TestCase):
    """Test portfolio aggregation, filters, and weight calculations."""

    @staticmethod
    def _account(portfolio_value: str) -> AccountSnapshot:
        return AccountSnapshot(
            status="ACTIVE",
            currency="USD",
            cash=Decimal("100"),
            buying_power=Decimal("200"),
            portfolio_value=Decimal(portfolio_value),
            equity=Decimal(portfolio_value),
        )

    @staticmethod
    def _positions() -> pd.DataFrame:
        records = [
            {
                "symbol": "AAPL",
                "asset_class": "us_equity",
                "quantity": Decimal("2"),
                "market_value": Decimal("250"),
                "average_entry_price": Decimal("100"),
                "current_price": Decimal("125"),
                "unrealized_pnl": Decimal("50"),
                "unrealized_pnl_pct": Decimal("0.25"),
                "side": "long",
            },
            {
                "symbol": "TSLA",
                "asset_class": "us_equity",
                "quantity": Decimal("1"),
                "market_value": Decimal("250"),
                "average_entry_price": Decimal("300"),
                "current_price": Decimal("250"),
                "unrealized_pnl": Decimal("50"),
                "unrealized_pnl_pct": Decimal("0.1667"),
                "side": "short",
            },
            {
                "symbol": "AAPL260717C00200000",
                "asset_class": "us_option",
                "quantity": Decimal("1"),
                "market_value": Decimal("100"),
                "average_entry_price": Decimal("80"),
                "current_price": Decimal("100"),
                "unrealized_pnl": Decimal("20"),
                "unrealized_pnl_pct": Decimal("0.25"),
                "side": "long",
            },
        ]
        return pd.DataFrame.from_records(records, columns=POSITION_COLUMNS)

    @staticmethod
    def _service(portfolio_value: str) -> PortfolioService:
        account_loader = Mock(
            load=Mock(return_value=PortfolioServiceTests._account(portfolio_value))
        )
        position_loader = Mock(
            load_all=Mock(return_value=PortfolioServiceTests._positions())
        )
        order_loader = Mock(
            load_open_orders=Mock(
                return_value=pd.DataFrame(columns=ORDER_COLUMNS)
            )
        )
        return PortfolioService(account_loader, position_loader, order_loader)

    def test_calculates_position_weight_column(self) -> None:
        snapshot = self._service("1000").get_snapshot()

        self.assertEqual(snapshot.positions.loc[0, "portfolio_weight"], Decimal("0.25"))

    def test_zero_portfolio_value_produces_zero_weights(self) -> None:
        snapshot = self._service("0").get_snapshot()

        self.assertTrue(
            snapshot.positions["portfolio_weight"].eq(Decimal("0")).all()
        )

    def test_snapshot_filters_return_dataframes(self) -> None:
        snapshot = self._service("1000").get_snapshot()

        self.assertEqual(snapshot.get_long_positions()["symbol"].tolist(), [
            "AAPL",
            "AAPL260717C00200000",
        ])
        self.assertEqual(snapshot.get_short_positions()["symbol"].tolist(), ["TSLA"])
        self.assertEqual(snapshot.get_option_positions()["symbol"].tolist(), [
            "AAPL260717C00200000"
        ])


class ReporterTests(unittest.TestCase):
    """Test the empty portfolio messages."""

    def test_empty_snapshot_messages(self) -> None:
        snapshot = PortfolioSnapshot(
            account=PortfolioServiceTests._account("1000"),
            positions=pd.DataFrame(columns=[*POSITION_COLUMNS, "portfolio_weight"]),
            open_orders=pd.DataFrame(columns=ORDER_COLUMNS),
        )

        output = io.StringIO()
        with patch("sys.stdout", output):
            ConsolePortfolioReporter.print_snapshot(snapshot)

        self.assertIn("No open positions.", output.getvalue())
        self.assertIn("No open orders.", output.getvalue())


class CompatibilityTests(unittest.TestCase):
    """Ensure the historical config-level validator remains importable."""

    def test_legacy_validator_is_callable(self) -> None:
        self.assertTrue(callable(validate_alpaca_config))


if __name__ == "__main__":
    unittest.main()
