"""Conservative default limits for manual paper trading."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RiskLimits:
    """Risk limits applied to every proposed order."""

    max_single_order_notional: Decimal = Decimal("1000")
    max_single_asset_weight: Decimal = Decimal("0.20")
    max_crypto_weight: Decimal = Decimal("0.30")
    allow_short: bool = False
    allow_options: bool = False
    allow_live_trading: bool = False
    paper_only: bool = True
    allowed_order_types: tuple[str, ...] = ("market", "limit")
