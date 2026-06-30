"""Tests for provider-neutral proposed order construction."""

import unittest
from decimal import Decimal

from trading_lab.execution.order_builder import OrderBuilder


class OrderBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.builder = OrderBuilder()

    def test_market_buy_notional(self) -> None:
        order = self.builder.market_buy_notional("SPY", Decimal("10"))

        self.assertEqual(order.symbol, "SPY")
        self.assertEqual(order.side, "buy")
        self.assertEqual(order.notional, Decimal("10"))
        self.assertIsNone(order.quantity)
        self.assertEqual(order.order_type, "market")
        self.assertEqual(order.asset_class, "equity")

    def test_limit_order_requires_limit_price(self) -> None:
        with self.assertRaisesRegex(ValueError, "limit_price must be positive"):
            self.builder.limit_buy_quantity(
                "SPY",
                Decimal("1"),
                None,  # type: ignore[arg-type]
            )

    def test_symbol_normalization(self) -> None:
        order = self.builder.market_buy_notional("  spy ", Decimal("10"))
        self.assertEqual(order.symbol, "SPY")


if __name__ == "__main__":
    unittest.main()
