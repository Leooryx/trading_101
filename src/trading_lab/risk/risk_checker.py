"""Pure risk checks for proposed orders."""

from decimal import Decimal

from trading_lab.execution.models import OrderDecision, ProposedOrder
from trading_lab.risk.limits import RiskLimits
from trading_lab.universe.tradable_universe import TradableUniverse
from trading_lab.utils.options import extract_underlying_symbol


class RiskChecker:
    """Approve or reject proposed orders without submitting anything."""

    def __init__(self, limits: RiskLimits, universe: TradableUniverse) -> None:
        self.limits = limits
        self.universe = universe

    def check_order(
        self,
        order: ProposedOrder,
        current_portfolio_value: Decimal | None = None,
    ) -> OrderDecision:
        """Apply the configured limits and return all rejection reasons."""
        reasons = list(order.validation_errors())

        if not self._symbol_is_allowed(order):
            reasons.append(f"Symbol {order.symbol} is outside the tradable universe.")
        if order.order_type not in self.limits.allowed_order_types:
            reasons.append(f"Order type {order.order_type} is not allowed.")
        if order.asset_class == "option" and not self.limits.allow_options:
            reasons.append("Options execution is disabled.")
        if order.side == "sell" and not self.limits.allow_short:
            reasons.append("Sell orders are blocked because shorting is disabled.")

        if order.notional is not None:
            if order.notional > self.limits.max_single_order_notional:
                reasons.append(
                    "Order notional exceeds the maximum single-order notional."
                )
            reasons.extend(
                self._weight_reasons(order, current_portfolio_value)
            )

        if reasons:
            return OrderDecision(order, approved=False, reasons=reasons)
        return OrderDecision(order, approved=True, reasons=["Approved"])

    def _symbol_is_allowed(self, order: ProposedOrder) -> bool:
        if order.asset_class != "option":
            return self.universe.is_allowed_symbol(order.symbol)
        try:
            underlying = extract_underlying_symbol(order.symbol)
        except ValueError:
            return False
        return self.universe.is_options_underlying_allowed(underlying)

    def _weight_reasons(
        self,
        order: ProposedOrder,
        current_portfolio_value: Decimal | None,
    ) -> list[str]:
        if current_portfolio_value is None:
            return []
        if current_portfolio_value <= Decimal("0"):
            return ["Current portfolio value must be positive for weight checks."]

        weight = order.notional / current_portfolio_value
        reasons = []
        if weight > self.limits.max_single_asset_weight:
            reasons.append("Order weight exceeds the maximum single-asset weight.")
        if (
            order.asset_class == "crypto"
            and weight > self.limits.max_crypto_weight
        ):
            reasons.append("Crypto order weight exceeds the configured crypto cap.")
        return reasons
