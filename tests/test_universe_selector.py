"""Tests for quote-board universe grouping and instrument inference."""

import unittest

from trading_lab.orderbook.universe_selector import UniverseSelector


class UniverseSelectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.selector = UniverseSelector()

    def test_returns_non_empty_groups(self) -> None:
        groups = self.selector.get_available_groups()
        self.assertTrue(groups)
        self.assertTrue(all(groups.values()))

    def test_expected_symbols_appear_in_groups(self) -> None:
        groups = self.selector.get_available_groups()
        self.assertIn("SPY", groups["All equity/ETF symbols"])
        self.assertIn("BTC/USD", groups["Crypto"])
        self.assertIn("EWJ", groups["Overnight / Asia proxy ETFs (24/5)"])

    def test_infers_equity_and_crypto(self) -> None:
        self.assertEqual(
            self.selector.infer_instrument_type("SPY", "equity / ETF"),
            "equity",
        )
        self.assertEqual(
            self.selector.infer_instrument_type("BTC/USD", "equity"),
            "crypto",
        )

    def test_options_request_uses_option_type(self) -> None:
        self.assertEqual(
            self.selector.infer_instrument_type("SPY", "options"),
            "option",
        )

    def test_overnight_request_uses_overnight_type(self) -> None:
        self.assertEqual(
            self.selector.infer_instrument_type("EWJ", "24/5"),
            "overnight",
        )


if __name__ == "__main__":
    unittest.main()
