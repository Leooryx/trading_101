"""Offline tests for the option Greeks pipeline."""

from __future__ import annotations

import io
import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pandas as pd

from trading_lab.factories import alpaca_factory
from trading_lab.loaders.option_snapshot_loader import (
    OPTION_SNAPSHOT_COLUMNS,
    OptionSnapshotLoader,
)
from trading_lab.loaders.position_loader import POSITION_COLUMNS
from trading_lab.reporting.console_greeks_reporter import ConsoleGreeksReporter
from trading_lab.services.option_greeks_service import OptionGreeksService
from trading_lab.utils.options import extract_underlying_symbol


class OptionSymbolTests(unittest.TestCase):
    """Test extraction of the underlying from OCC symbols."""

    def test_extracts_underlying(self) -> None:
        self.assertEqual(
            extract_underlying_symbol("AAPL260717C00200000"),
            "AAPL",
        )

    def test_rejects_invalid_symbol(self) -> None:
        with self.assertRaisesRegex(ValueError, "Invalid OCC option symbol"):
            extract_underlying_symbol("AAPL")


class OptionSnapshotLoaderTests(unittest.TestCase):
    """Test conversion of Alpaca snapshots to a stable DataFrame."""

    def test_loads_greeks(self) -> None:
        client = Mock()
        client.get_option_snapshot.return_value = {
            "AAPL260717C00200000": SimpleNamespace(
                implied_volatility=0.25,
                greeks=SimpleNamespace(
                    delta=0.5,
                    gamma=0.03,
                    vega=0.12,
                    theta=-0.04,
                ),
            )
        }

        snapshots = OptionSnapshotLoader(client).load(
            ["AAPL260717C00200000"]
        )

        self.assertEqual(snapshots.columns.tolist(), OPTION_SNAPSHOT_COLUMNS)
        self.assertEqual(snapshots.loc[0, "delta"], Decimal("0.5"))
        request = client.get_option_snapshot.call_args.args[0]
        self.assertEqual(request.symbol_or_symbols, ["AAPL260717C00200000"])

    def test_empty_symbols_skip_api_call(self) -> None:
        client = Mock()

        snapshots = OptionSnapshotLoader(client).load([])

        self.assertTrue(snapshots.empty)
        self.assertEqual(snapshots.columns.tolist(), OPTION_SNAPSHOT_COLUMNS)
        client.get_option_snapshot.assert_not_called()


class OptionGreeksServiceTests(unittest.TestCase):
    """Test filtering, exposure calculations, and aggregation."""

    @staticmethod
    def _positions() -> pd.DataFrame:
        records = [
            {
                "symbol": "AAPL260717C00200000",
                "asset_class": "us_option",
                "quantity": Decimal("2"),
                "market_value": Decimal("1000"),
                "average_entry_price": Decimal("4"),
                "current_price": Decimal("5"),
                "unrealized_pnl": Decimal("200"),
                "unrealized_pnl_pct": Decimal("0.25"),
                "side": "long",
            },
            {
                "symbol": "AAPL260717P00180000",
                "asset_class": "us_option",
                "quantity": Decimal("1"),
                "market_value": Decimal("300"),
                "average_entry_price": Decimal("4"),
                "current_price": Decimal("3"),
                "unrealized_pnl": Decimal("100"),
                "unrealized_pnl_pct": Decimal("0.25"),
                "side": "short",
            },
            {
                "symbol": "MSFT",
                "asset_class": "us_equity",
                "quantity": Decimal("3"),
                "market_value": Decimal("1200"),
                "average_entry_price": Decimal("350"),
                "current_price": Decimal("400"),
                "unrealized_pnl": Decimal("150"),
                "unrealized_pnl_pct": Decimal("0.14"),
                "side": "long",
            },
        ]
        return pd.DataFrame.from_records(records, columns=POSITION_COLUMNS)

    @staticmethod
    def _snapshots() -> pd.DataFrame:
        records = [
            {
                "option_symbol": "AAPL260717C00200000",
                "implied_volatility": Decimal("0.25"),
                "delta": Decimal("0.5"),
                "gamma": Decimal("0.1"),
                "vega": Decimal("0.2"),
                "theta": Decimal("-0.1"),
                "greeks_available": True,
            },
            {
                "option_symbol": "AAPL260717P00180000",
                "implied_volatility": Decimal("0.3"),
                "delta": Decimal("-0.4"),
                "gamma": Decimal("0.05"),
                "vega": Decimal("0.1"),
                "theta": Decimal("-0.05"),
                "greeks_available": True,
            },
        ]
        return pd.DataFrame.from_records(records, columns=OPTION_SNAPSHOT_COLUMNS)

    def test_calculates_and_aggregates_exposures(self) -> None:
        position_loader = Mock(load_all=Mock(return_value=self._positions()))
        snapshot_loader = Mock(load=Mock(return_value=self._snapshots()))

        book = OptionGreeksService(position_loader, snapshot_loader).get_book()

        snapshot_loader.load.assert_called_once_with(
            ["AAPL260717C00200000", "AAPL260717P00180000"]
        )
        self.assertEqual(book.positions["option_symbol"].tolist(), [
            "AAPL260717C00200000",
            "AAPL260717P00180000",
        ])
        aapl = book.by_underlying.iloc[0]
        self.assertEqual(aapl["delta_exposure"], Decimal("140.0"))
        self.assertEqual(aapl["gamma_exposure"], Decimal("15.00"))
        self.assertEqual(aapl["vega_exposure"], Decimal("30.0"))
        self.assertEqual(aapl["theta_exposure"], Decimal("-15.00"))

    def test_empty_option_book_skips_snapshot_call(self) -> None:
        stocks = self._positions().loc[
            lambda frame: frame["asset_class"].eq("us_equity")
        ]
        position_loader = Mock(load_all=Mock(return_value=stocks))
        snapshot_loader = Mock()

        book = OptionGreeksService(position_loader, snapshot_loader).get_book()

        self.assertTrue(book.positions.empty)
        self.assertTrue(book.by_underlying.empty)
        snapshot_loader.load.assert_not_called()


class OptionGreeksReporterTests(unittest.TestCase):
    """Test the empty book message."""

    def test_empty_book_message(self) -> None:
        position_loader = Mock(
            load_all=Mock(return_value=pd.DataFrame(columns=POSITION_COLUMNS))
        )
        book = OptionGreeksService(position_loader, Mock()).get_book()
        output = io.StringIO()

        with patch("sys.stdout", output):
            ConsoleGreeksReporter.print_book(book)

        self.assertIn("No open option positions.", output.getvalue())


class OptionDataFactoryTests(unittest.TestCase):
    """Test construction of the option market-data client."""

    def test_factory_uses_validated_credentials(self) -> None:
        with (
            patch.object(alpaca_factory.Settings, "validate_alpaca") as validate,
            patch.object(alpaca_factory.Settings, "ALPACA_API_KEY", "test-key"),
            patch.object(alpaca_factory.Settings, "ALPACA_SECRET_KEY", "test-secret"),
            patch.object(alpaca_factory, "OptionHistoricalDataClient") as data_client,
        ):
            alpaca_factory.AlpacaClientFactory.create_option_data_client()

        validate.assert_called_once_with()
        data_client.assert_called_once_with(
            api_key="test-key",
            secret_key="test-secret",
        )


if __name__ == "__main__":
    unittest.main()
