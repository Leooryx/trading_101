"""Tests for the explicit tradable universe."""

import unittest

from trading_lab.universe.tradable_universe import TradableUniverse


class TradableUniverseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.universe = TradableUniverse()

    def test_expected_symbols_are_allowed(self) -> None:
        self.assertTrue(self.universe.is_allowed_symbol("SPY"))
        self.assertTrue(self.universe.is_allowed_symbol("QQQ"))
        self.assertTrue(self.universe.is_allowed_symbol("BTC/USD"))
        self.assertTrue(self.universe.is_allowed_symbol("EWJ"))

    def test_overnight_group_contains_asia_proxies(self) -> None:
        self.assertTrue(self.universe.is_overnight_symbol("EWJ"))
        self.assertIn("FXI", self.universe.get_overnight_symbols())

    def test_unknown_symbol_is_rejected(self) -> None:
        self.assertFalse(self.universe.is_allowed_symbol("RANDOM"))

    def test_crypto_detection_and_normalization(self) -> None:
        self.assertTrue(self.universe.is_crypto("  btc/usd "))
        self.assertFalse(self.universe.is_crypto("SPY"))


if __name__ == "__main__":
    unittest.main()
