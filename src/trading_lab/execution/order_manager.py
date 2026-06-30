"""The only application component allowed to submit orders to Alpaca."""

from decimal import Decimal
from typing import Any

from alpaca.trading.enums import OrderSide, OrderType, TimeInForce
from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

from trading_lab.config.settings import Settings
from trading_lab.execution.models import OrderExecutionResult, ProposedOrder
from trading_lab.risk.risk_checker import RiskChecker


class OrderManager:
    """Risk-check proposed orders and optionally submit them to Alpaca."""

    def __init__(
        self,
        trading_client: Any,
        risk_checker: RiskChecker,
        dry_run: bool = True,
    ) -> None:
        self.trading_client = trading_client
        self.risk_checker = risk_checker
        self.dry_run = dry_run

    def submit_order(
        self,
        order: ProposedOrder,
        current_portfolio_value: Decimal | None = None,
    ) -> OrderExecutionResult:
        """Reject, simulate, or submit one proposed order safely."""
        decision = self.risk_checker.check_order(order, current_portfolio_value)
        if not decision.approved:
            return OrderExecutionResult(
                proposed_order=order,
                dry_run=self.dry_run,
                submitted=False,
                alpaca_order_id=None,
                status="rejected",
                message="; ".join(decision.reasons),
            )

        if self.dry_run:
            return OrderExecutionResult(
                proposed_order=order,
                dry_run=True,
                submitted=False,
                alpaca_order_id=None,
                status="dry_run",
                message="Dry run: risk approved, no order sent.",
            )

        limits = self.risk_checker.limits
        if not Settings.ALPACA_PAPER and (
            limits.paper_only or not limits.allow_live_trading
        ):
            return OrderExecutionResult(
                proposed_order=order,
                dry_run=False,
                submitted=False,
                alpaca_order_id=None,
                status="blocked",
                message="Live trading is blocked by the current risk limits.",
            )

        try:
            request = self._build_request(order)
            print("WARNING: sending an order to the Alpaca paper account.")
            response = self.trading_client.submit_order(order_data=request)
            return OrderExecutionResult(
                proposed_order=order,
                dry_run=False,
                submitted=True,
                alpaca_order_id=self._optional_text(getattr(response, "id", None)),
                status=self._text(getattr(response, "status", "submitted")),
                message="Order submitted to Alpaca.",
            )
        except Exception as error:
            return OrderExecutionResult(
                proposed_order=order,
                dry_run=False,
                submitted=False,
                alpaca_order_id=None,
                status="failed",
                message=f"Order submission failed: {error}",
            )

    @staticmethod
    def _build_request(
        order: ProposedOrder,
    ) -> MarketOrderRequest | LimitOrderRequest:
        """Translate a provider-neutral proposal into an Alpaca request."""
        common = {
            "symbol": order.symbol,
            "side": OrderSide(order.side),
            "time_in_force": TimeInForce(order.time_in_force),
            "qty": OrderManager._float_or_none(order.quantity),
            "notional": OrderManager._float_or_none(order.notional),
        }
        if order.order_type == "market":
            return MarketOrderRequest(type=OrderType.MARKET, **common)
        if order.order_type == "limit":
            return LimitOrderRequest(
                type=OrderType.LIMIT,
                limit_price=OrderManager._float_or_none(order.limit_price),
                **common,
            )
        raise ValueError(f"Unsupported order type: {order.order_type}")

    @staticmethod
    def _float_or_none(value: Decimal | None) -> float | None:
        return float(value) if value is not None else None

    @staticmethod
    def _optional_text(value: Any) -> str | None:
        return None if value is None else OrderManager._text(value)

    @staticmethod
    def _text(value: Any) -> str:
        return str(getattr(value, "value", value))
