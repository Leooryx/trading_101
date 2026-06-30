"""Models returned by the pre-trade what-if service."""

from dataclasses import dataclass
from decimal import Decimal

from trading_lab.execution.models import ProposedOrder
from trading_lab.market_data.quote_models import MarketQuote
from trading_lab.risk.greek_exposure import BookGreekExposure


@dataclass(frozen=True)
class PreTradeImpactReport:
    """Complete account, exposure, and risk preview for one proposed order."""

    proposed_order: ProposedOrder
    quote: MarketQuote
    estimated_fill_price: Decimal | None
    estimated_quantity: Decimal | None
    estimated_notional: Decimal | None
    cash_before: Decimal | None
    cash_after: Decimal | None
    portfolio_value_before: Decimal | None
    portfolio_value_after: Decimal | None
    current_book_exposure: BookGreekExposure
    post_trade_book_exposure: BookGreekExposure
    risk_approved: bool
    risk_reasons: list[str]
    warnings: list[str]
