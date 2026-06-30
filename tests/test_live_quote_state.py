"""Tests for live quote calculations and thread-safe state."""

import unittest
from decimal import Decimal

from trading_lab.orderbook.live_quote_models import (
    LiveQuote,
    compute_mid,
    compute_spread,
    compute_spread_bps,
)
from trading_lab.orderbook.live_quote_state import LiveQuoteState


class LiveQuoteStateTests(unittest.TestCase):
    @staticmethod
    def _quote(bid: Decimal | None = Decimal("100")) -> LiveQuote:
        ask = Decimal("101") if bid is not None else None
        return LiveQuote(
            symbol="SPY",
            instrument_type="equity",
            bid_price=bid,
            bid_size=Decimal("10") if bid is not None else None,
            ask_price=ask,
            ask_size=Decimal("12") if ask is not None else None,
            mid_price=compute_mid(bid, ask),
            spread=compute_spread(bid, ask),
            spread_bps=compute_spread_bps(bid, ask),
            timestamp="2026-07-01T10:00:00+00:00",
            source="test",
            status="live" if bid is not None else "missing",
        )

    def test_update_and_get_latest_quote(self) -> None:
        state = LiveQuoteState()
        quote = self._quote()

        state.update_quote(quote)

        self.assertEqual(state.get_quote("spy"), quote)
        self.assertEqual(state.get_all_quotes(), [quote])
        self.assertIsNotNone(state.last_update_time)

    def test_errors_can_be_added_read_and_cleared(self) -> None:
        state = LiveQuoteState()
        state.add_error("stream unavailable")
        self.assertEqual(state.get_errors(), ["stream unavailable"])
        state.clear_errors()
        self.assertEqual(state.get_errors(), [])

    def test_missing_bid_and_ask_do_not_crash(self) -> None:
        state = LiveQuoteState()
        quote = self._quote(bid=None)
        state.update_quote(quote)

        stored = state.get_quote("SPY")
        self.assertIsNotNone(stored)
        self.assertIsNone(stored.mid_price)
        self.assertIsNone(stored.spread)
        self.assertIsNone(stored.spread_bps)

    def test_quote_math(self) -> None:
        bid = Decimal("100")
        ask = Decimal("101")
        self.assertEqual(compute_mid(bid, ask), Decimal("100.5"))
        self.assertEqual(compute_spread(bid, ask), Decimal("1"))
        self.assertEqual(
            compute_spread_bps(bid, ask),
            Decimal("1") / Decimal("100.5") * Decimal("10000"),
        )


if __name__ == "__main__":
    unittest.main()
