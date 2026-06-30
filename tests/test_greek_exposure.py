"""Tests for money-based Greek exposure formulas."""

import unittest
from decimal import Decimal

from trading_lab.risk.exposure_calculator import ExposureCalculator


class GreekExposureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.calculator = ExposureCalculator()

    def test_long_equity_delta_exposure(self) -> None:
        exposure = self.calculator.calculate_line_exposure(
            symbol="SPY",
            underlying_symbol="SPY",
            asset_class="equity",
            quantity=Decimal("2"),
            price=Decimal("500"),
        )

        self.assertEqual(exposure.delta_notional, Decimal("1000"))
        self.assertEqual(exposure.delta_pnl_1pct_move, Decimal("10.00"))

    def test_option_greek_formulas(self) -> None:
        exposure = self.calculator.calculate_line_exposure(
            symbol="SPY260717C00600000",
            underlying_symbol="SPY",
            asset_class="option",
            quantity=Decimal("2"),
            price=Decimal("500"),
            delta=Decimal("0.5"),
            gamma=Decimal("0.02"),
            vega=Decimal("0.10"),
            theta=Decimal("-0.05"),
        )

        self.assertEqual(exposure.delta_notional, Decimal("50000.0"))
        self.assertEqual(exposure.delta_pnl_1pct_move, Decimal("500.000"))
        self.assertEqual(exposure.gamma_pnl_1pct_move, Decimal("50.0000"))
        self.assertEqual(exposure.vega_pnl_1vol_point, Decimal("20.00"))
        self.assertEqual(exposure.theta_pnl_1day, Decimal("-10.00"))


if __name__ == "__main__":
    unittest.main()
