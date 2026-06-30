"""Tests for conservative order risk decisions."""

import unittest
from decimal import Decimal

from trading_lab.execution.models import ProposedOrder
from trading_lab.execution.order_builder import OrderBuilder
from trading_lab.risk.limits import RiskLimits
from trading_lab.risk.risk_checker import RiskChecker
from trading_lab.universe.tradable_universe import TradableUniverse


class RiskCheckerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.universe = TradableUniverse()
        self.builder = OrderBuilder(self.universe)
        self.checker = RiskChecker(RiskLimits(), self.universe)

    def test_rejects_symbol_outside_universe(self) -> None:
        order = self.builder.market_buy_notional("RANDOM", Decimal("10"))
        decision = self.checker.check_order(order)
        self.assertFalse(decision.approved)
        self.assertIn("outside the tradable universe", " ".join(decision.reasons))

    def test_rejects_notional_above_maximum(self) -> None:
        order = self.builder.market_buy_notional("SPY", Decimal("1001"))
        decision = self.checker.check_order(order)
        self.assertFalse(decision.approved)
        self.assertIn("maximum single-order", " ".join(decision.reasons))

    def test_rejects_option_when_options_are_disabled(self) -> None:
        order = self.builder.market_buy_quantity(
            "SPY260717C00600000",
            Decimal("1"),
        )
        decision = self.checker.check_order(order)
        self.assertFalse(decision.approved)
        self.assertIn("Options execution is disabled.", decision.reasons)

    def test_approves_small_spy_buy(self) -> None:
        order = self.builder.market_buy_notional("SPY", Decimal("10"))
        decision = self.checker.check_order(order)
        self.assertTrue(decision.approved)
        self.assertEqual(decision.reasons, ["Approved"])

    def test_rejects_invalid_side(self) -> None:
        order = ProposedOrder(
            symbol="SPY",
            side="hold",
            notional=Decimal("10"),
            asset_class="equity",
        )
        decision = self.checker.check_order(order)
        self.assertFalse(decision.approved)
        self.assertIn("Side must be 'buy' or 'sell'.", decision.reasons)

    def test_rejects_sell_when_shorting_is_disabled(self) -> None:
        order = self.builder.market_sell_quantity("SPY", Decimal("1"))
        decision = self.checker.check_order(order)
        self.assertFalse(decision.approved)
        self.assertIn("shorting is disabled", " ".join(decision.reasons))


if __name__ == "__main__":
    unittest.main()
