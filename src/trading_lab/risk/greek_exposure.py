"""Money-based Greek exposure models for pre-trade analysis."""

from dataclasses import dataclass
from decimal import Decimal


DEFAULT_OPTION_CONTRACT_MULTIPLIER = Decimal("100")


@dataclass(frozen=True)
class GreekExposure:
    """One position expressed as notionals and standardized PnL sensitivities.

    ``delta_notional`` approximates directional dollar exposure.
    ``delta_pnl_1pct_move`` estimates PnL for a +1% underlying move.
    ``gamma_pnl_1pct_move`` estimates convexity PnL for the same move.
    Vega assumes the provider reports vega per one volatility point, and theta
    assumes the provider reports theta per day.
    """

    symbol: str
    underlying_symbol: str | None
    asset_class: str
    quantity: Decimal
    price: Decimal
    notional: Decimal
    delta: Decimal
    gamma: Decimal
    vega: Decimal
    theta: Decimal
    delta_notional: Decimal
    gamma_notional: Decimal
    vega_notional: Decimal
    theta_notional: Decimal
    delta_pnl_1pct_move: Decimal
    gamma_pnl_1pct_move: Decimal
    vega_pnl_1vol_point: Decimal
    theta_pnl_1day: Decimal


@dataclass(frozen=True)
class BookGreekExposure:
    """Greek exposures for the total book and useful breakdowns."""

    total_notional: Decimal
    total_delta_notional: Decimal
    total_gamma_notional: Decimal
    total_vega_notional: Decimal
    total_theta_notional: Decimal
    total_delta_pnl_1pct_move: Decimal
    total_gamma_pnl_1pct_move: Decimal
    total_vega_pnl_1vol_point: Decimal
    total_theta_pnl_1day: Decimal
    by_asset_class: dict[str, dict[str, Decimal]]
    by_underlying: dict[str, dict[str, Decimal]]
    line_items: list[GreekExposure]
