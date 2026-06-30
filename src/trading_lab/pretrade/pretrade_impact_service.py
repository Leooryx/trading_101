"""Orchestrate a read-only pre-trade order impact simulation."""

from datetime import datetime, timezone
from decimal import Decimal

from trading_lab.execution.models import ProposedOrder
from trading_lab.market_data.quote_loader import MarketQuoteLoader
from trading_lab.pretrade.models import PreTradeImpactReport
from trading_lab.risk.exposure_calculator import ExposureCalculator
from trading_lab.risk.risk_checker import RiskChecker
from trading_lab.services.portfolio_service import PortfolioService


class PreTradeImpactService:
    """Preview an order without importing or calling the OrderManager."""

    def __init__(
        self,
        portfolio_service: PortfolioService,
        quote_loader: MarketQuoteLoader,
        risk_checker: RiskChecker,
        exposure_calculator: ExposureCalculator,
    ) -> None:
        self.portfolio_service = portfolio_service
        self.quote_loader = quote_loader
        self.risk_checker = risk_checker
        self.exposure_calculator = exposure_calculator

    def preview_order(self, order: ProposedOrder) -> PreTradeImpactReport:
        """Return estimated account and exposure changes for a proposed order."""
        snapshot = self.portfolio_service.get_snapshot()
        quote = self.quote_loader.get_quote(order.symbol)
        fill_price = quote.estimated_fill_price(order.side)
        warnings = []

        if fill_price is None:
            warnings.append(
                f"No market price is available for {order.symbol}; execution "
                "and post-trade estimates may be incomplete."
            )
        if quote.timestamp is None:
            warnings.append("Quote timestamp is unavailable; quote freshness is unknown.")
        else:
            stale_warning = self._stale_quote_warning(quote.timestamp)
            if stale_warning:
                warnings.append(stale_warning)
        if order.side == "buy" and quote.ask_price is None and fill_price is not None:
            warnings.append("Ask price is unavailable; estimated fill uses a fallback price.")
        if order.side == "sell" and quote.bid_price is None and fill_price is not None:
            warnings.append("Bid price is unavailable; estimated fill uses a fallback price.")

        estimated_quantity = order.quantity
        estimated_notional = order.notional
        if order.notional is not None and fill_price is not None:
            estimated_quantity = order.notional / fill_price
        if order.quantity is not None and fill_price is not None:
            estimated_notional = order.quantity * fill_price

        current_exposure = self.exposure_calculator.compute_current_book_exposure(
            snapshot,
            quotes={order.symbol: quote},
        )
        warnings.extend(self.exposure_calculator.warnings)
        post_trade_exposure = self.exposure_calculator.compute_post_trade_exposure(
            snapshot,
            order,
            quote,
        )
        warnings.extend(self.exposure_calculator.warnings)

        if order.asset_class == "option" or any(
            line.asset_class == "option"
            for line in post_trade_exposure.line_items
        ):
            warnings.append(
                "Option vega and theta conventions depend on the data provider; "
                "vega is treated as per volatility point and theta as per day."
            )

        cash_before = snapshot.account.cash
        cash_after = self._cash_after(
            cash_before,
            order.side,
            estimated_notional,
        )
        portfolio_value_before = snapshot.account.portfolio_value
        risk_decision = self.risk_checker.check_order(
            order,
            current_portfolio_value=portfolio_value_before,
        )

        return PreTradeImpactReport(
            proposed_order=order,
            quote=quote,
            estimated_fill_price=fill_price,
            estimated_quantity=estimated_quantity,
            estimated_notional=estimated_notional,
            cash_before=cash_before,
            cash_after=cash_after,
            portfolio_value_before=portfolio_value_before,
            portfolio_value_after=portfolio_value_before,
            current_book_exposure=current_exposure,
            post_trade_book_exposure=post_trade_exposure,
            risk_approved=risk_decision.approved,
            risk_reasons=risk_decision.reasons,
            warnings=list(dict.fromkeys(warnings)),
        )

    @staticmethod
    def _cash_after(
        cash_before: Decimal | None,
        side: str,
        estimated_notional: Decimal | None,
    ) -> Decimal | None:
        if cash_before is None or estimated_notional is None:
            return None
        if side == "buy":
            return cash_before - estimated_notional
        if side == "sell":
            return cash_before + estimated_notional
        return cash_before

    @staticmethod
    def _stale_quote_warning(timestamp: str) -> str | None:
        """Warn when a parseable quote is older than fifteen minutes."""
        try:
            quoted_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if quoted_at.tzinfo is None:
                quoted_at = quoted_at.replace(tzinfo=timezone.utc)
            age = datetime.now(timezone.utc) - quoted_at.astimezone(timezone.utc)
        except ValueError:
            return "Quote timestamp could not be parsed; freshness is unknown."
        if age.total_seconds() > 15 * 60:
            return "Quote may be stale (older than 15 minutes)."
        return None
