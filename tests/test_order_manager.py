"""Tests for the final safety boundary before Alpaca submission."""

import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

from trading_lab.config.settings import Settings
from trading_lab.execution.order_builder import OrderBuilder
from trading_lab.execution.order_manager import OrderManager
from trading_lab.risk.limits import RiskLimits
from trading_lab.risk.risk_checker import RiskChecker
from trading_lab.universe.tradable_universe import TradableUniverse


class OrderManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        universe = TradableUniverse()
        self.order = OrderBuilder(universe).market_buy_notional(
            "SPY",
            Decimal("10"),
        )
        self.checker = RiskChecker(RiskLimits(), universe)

    def test_dry_run_never_calls_alpaca(self) -> None:
        client = Mock()
        result = OrderManager(client, self.checker).submit_order(self.order)

        self.assertEqual(result.status, "dry_run")
        self.assertFalse(result.submitted)
        client.submit_order.assert_not_called()

    def test_live_configuration_is_blocked(self) -> None:
        client = Mock()
        manager = OrderManager(client, self.checker, dry_run=False)

        with patch.object(Settings, "ALPACA_PAPER", False):
            result = manager.submit_order(self.order)

        self.assertEqual(result.status, "blocked")
        client.submit_order.assert_not_called()

    def test_paper_order_can_be_submitted_after_checks(self) -> None:
        client = Mock()
        client.submit_order.return_value = SimpleNamespace(id="order-1", status="new")
        manager = OrderManager(client, self.checker, dry_run=False)

        with patch.object(Settings, "ALPACA_PAPER", True):
            result = manager.submit_order(self.order)

        self.assertTrue(result.submitted)
        self.assertEqual(result.alpaca_order_id, "order-1")
        client.submit_order.assert_called_once()


if __name__ == "__main__":
    unittest.main()
