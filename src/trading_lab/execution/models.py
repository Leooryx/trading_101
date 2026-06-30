"""Provider-neutral order, decision, and execution models."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ProposedOrder:
    """An order proposal that must pass risk checks before submission."""

    symbol: str
    side: str
    notional: Decimal | None = None
    quantity: Decimal | None = None
    order_type: str = "market"
    limit_price: Decimal | None = None
    time_in_force: str = "day"
    asset_class: str = "unknown"
    reason: str | None = None
    metadata: dict[str, Decimal] | None = None

    def validation_errors(self) -> list[str]:
        """Return simple structural validation errors without raising."""
        errors = []
        if self.side not in {"buy", "sell"}:
            errors.append("Side must be 'buy' or 'sell'.")
        if (self.notional is None) == (self.quantity is None):
            errors.append("Provide exactly one of notional or quantity.")
        if self.notional is not None and self.notional <= Decimal("0"):
            errors.append("Notional must be positive.")
        if self.quantity is not None and self.quantity <= Decimal("0"):
            errors.append("Quantity must be positive.")
        if self.order_type == "market" and self.limit_price is not None:
            errors.append("Market orders must not have a limit price.")
        if self.order_type == "limit":
            if self.limit_price is None or self.limit_price <= Decimal("0"):
                errors.append("Limit orders require a positive limit price.")
            if self.quantity is None:
                errors.append("Limit orders require a quantity.")
        return errors


@dataclass(frozen=True)
class OrderDecision:
    """Risk approval or rejection for a proposed order."""

    proposed_order: ProposedOrder
    approved: bool
    reasons: list[str]


@dataclass(frozen=True)
class OrderExecutionResult:
    """Result of a dry-run or Alpaca submission attempt."""

    proposed_order: ProposedOrder
    dry_run: bool
    submitted: bool
    alpaca_order_id: str | None
    status: str
    message: str
