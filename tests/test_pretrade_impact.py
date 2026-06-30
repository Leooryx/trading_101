"""Offline tests for read-only pre-trade what-if simulations."""

import unittest
from decimal import Decimal
from unittest.mock import Mock

import pandas as pd

from trading_lab.execution.order_builder import OrderBuilder
from trading_lab.loaders.order_loader import ORDER_COLUMNS
from trading_lab.loaders.position_loader import POSITION_COLUMNS
from trading_lab.market_data.quote_models import MarketQuote
from trading_lab.models.account import AccountSnapshot
from trading_lab.pretrade.pretrade_impact_service import PreTradeImpactService
from trading_lab.risk.exposure_calculator import ExposureCalculator
from trading_lab.risk.limits import RiskLimits
from trading_lab.risk.risk_checker import RiskChecker
from trading_lab.services.portfolio_service import PortfolioSnapshot
from trading_lab.universe.tradable_universe import TradableUniverse


class PreTradeImpactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.universe = TradableUniverse()
        self.builder = OrderBuilder(self.universe)
        self.quote = MarketQuote(
            symbol="SPY",
            bid_price=Decimal("99"),
            ask_price=Decimal("100"),
            mid_price=Decimal("99.5"),
            last_price=Decimal("99.75"),
            timestamp="2026-07-01T10:00:00+00:00",
            source="test",
        )

    @staticmethod
    def _snapshot(positions: pd.DataFrame | None = None) -> PortfolioSnapshot:
        return PortfolioSnapshot(
            account=AccountSnapshot(
                status="ACTIVE",
                currency="USD",
                cash=Decimal("100000"),
                buying_power=Decimal("200000"),
                portfolio_value=Decimal("100000"),
                equity=Decimal("100000"),
            ),
            positions=(
                positions
                if positions is not None
                else pd.DataFrame(columns=[*POSITION_COLUMNS, "portfolio_weight"])
            ),
            open_orders=pd.DataFrame(columns=ORDER_COLUMNS),
        )

    def _service(
        self,
        snapshot: PortfolioSnapshot,
        quote: MarketQuote,
    ) -> PreTradeImpactService:
        portfolio_service = Mock(get_snapshot=Mock(return_value=snapshot))
        quote_loader = Mock(get_quote=Mock(return_value=quote))
        risk_checker = RiskChecker(RiskLimits(), self.universe)
        return PreTradeImpactService(
            portfolio_service,
            quote_loader,
            risk_checker,
            ExposureCalculator(),
        )

    def test_buy_notional_increases_delta_and_reduces_cash(self) -> None:
        order = self.builder.market_buy_notional("SPY", Decimal("1000"))

        report = self._service(self._snapshot(), self.quote).preview_order(order)

        self.assertEqual(report.estimated_quantity, Decimal("10"))
        self.assertEqual(report.cash_after, Decimal("99000"))
        delta_change = (
            report.post_trade_book_exposure.total_delta_notional
            - report.current_book_exposure.total_delta_notional
        )
        self.assertLess(abs(delta_change - Decimal("1000")), Decimal("10"))

    def test_sell_quantity_decreases_exposure(self) -> None:
        position = {
            "symbol": "SPY",
            "asset_class": "us_equity",
            "quantity": Decimal("10"),
            "market_value": Decimal("1000"),
            "average_entry_price": Decimal("100"),
            "current_price": Decimal("100"),
            "unrealized_pnl": Decimal("0"),
            "unrealized_pnl_pct": Decimal("0"),
            "side": "long",
            "portfolio_weight": Decimal("0.01"),
        }
        positions = pd.DataFrame([position])
        order = self.builder.market_sell_quantity("SPY", Decimal("1"))

        report = self._service(
            self._snapshot(positions),
            self.quote,
        ).preview_order(order)

        self.assertEqual(
            report.current_book_exposure.total_delta_notional,
            Decimal("995.0"),
        )
        self.assertEqual(
            report.post_trade_book_exposure.total_delta_notional,
            Decimal("895.5"),
        )

    def test_missing_quote_adds_warning_without_crashing(self) -> None:
        missing_quote = MarketQuote(
            symbol="SPY",
            bid_price=None,
            ask_price=None,
            mid_price=None,
            last_price=None,
            timestamp=None,
            source="test unavailable",
        )
        order = self.builder.market_buy_notional("SPY", Decimal("1000"))

        report = self._service(
            self._snapshot(),
            missing_quote,
        ).preview_order(order)

        self.assertIsNone(report.estimated_fill_price)
        self.assertTrue(any("No market price" in warning for warning in report.warnings))
        self.assertTrue(any("timestamp" in warning for warning in report.warnings))

    def test_quote_fill_prefers_ask_for_buy_and_bid_for_sell(self) -> None:
        self.assertEqual(self.quote.estimated_fill_price("buy"), Decimal("100"))
        self.assertEqual(self.quote.estimated_fill_price("sell"), Decimal("99"))


if __name__ == "__main__":
    unittest.main()
