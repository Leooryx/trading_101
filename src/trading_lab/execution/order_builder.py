"""Convenient construction of normalized proposed orders."""

from decimal import Decimal

from trading_lab.execution.models import ProposedOrder
from trading_lab.universe.tradable_universe import TradableUniverse
from trading_lab.utils.money import to_decimal
from trading_lab.utils.options import extract_underlying_symbol


class OrderBuilder:
    """Build consistent proposed orders without contacting Alpaca."""

    def __init__(self, universe: TradableUniverse | None = None) -> None:
        self.universe = universe or TradableUniverse()

    def market_buy_notional(
        self,
        symbol: str,
        notional: Decimal,
        reason: str | None = None,
    ) -> ProposedOrder:
        """Build a market buy expressed as a cash notional."""
        return self._build(
            symbol=symbol,
            side="buy",
            notional=self._positive(notional, "notional"),
            order_type="market",
            reason=reason,
        )

    def market_sell_quantity(
        self,
        symbol: str,
        quantity: Decimal,
        reason: str | None = None,
    ) -> ProposedOrder:
        """Build a market sell expressed as a quantity."""
        return self._build(
            symbol=symbol,
            side="sell",
            quantity=self._positive(quantity, "quantity"),
            order_type="market",
            reason=reason,
        )

    def market_sell_notional(
        self,
        symbol: str,
        notional: Decimal,
        reason: str | None = None,
    ) -> ProposedOrder:
        """Build a market sell expressed as a cash notional."""
        return self._build(
            symbol=symbol,
            side="sell",
            notional=self._positive(notional, "notional"),
            order_type="market",
            reason=reason,
        )

    def market_buy_quantity(
        self,
        symbol: str,
        quantity: Decimal,
        reason: str | None = None,
    ) -> ProposedOrder:
        """Build a market buy expressed as a quantity."""
        return self._build(
            symbol=symbol,
            side="buy",
            quantity=self._positive(quantity, "quantity"),
            order_type="market",
            reason=reason,
        )

    def limit_buy_quantity(
        self,
        symbol: str,
        quantity: Decimal,
        limit_price: Decimal,
        reason: str | None = None,
    ) -> ProposedOrder:
        """Build a limit buy with quantity and price."""
        return self._build(
            symbol=symbol,
            side="buy",
            quantity=self._positive(quantity, "quantity"),
            order_type="limit",
            limit_price=self._positive(limit_price, "limit_price"),
            reason=reason,
        )

    def limit_sell_quantity(
        self,
        symbol: str,
        quantity: Decimal,
        limit_price: Decimal,
        reason: str | None = None,
    ) -> ProposedOrder:
        """Build a limit sell with quantity and price."""
        return self._build(
            symbol=symbol,
            side="sell",
            quantity=self._positive(quantity, "quantity"),
            order_type="limit",
            limit_price=self._positive(limit_price, "limit_price"),
            reason=reason,
        )

    def _build(
        self,
        symbol: str,
        side: str,
        order_type: str,
        notional: Decimal | None = None,
        quantity: Decimal | None = None,
        limit_price: Decimal | None = None,
        reason: str | None = None,
    ) -> ProposedOrder:
        normalized_symbol = self.universe.normalize_symbol(symbol)
        asset_class = self._asset_class(normalized_symbol)
        time_in_force = "gtc" if asset_class == "crypto" else "day"
        return ProposedOrder(
            symbol=normalized_symbol,
            side=side,
            notional=notional,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            time_in_force=time_in_force,
            asset_class=asset_class,
            reason=reason,
        )

    def _asset_class(self, symbol: str) -> str:
        if self.universe.is_crypto(symbol):
            return "crypto"
        if self.universe.is_equity_or_etf(symbol):
            return "equity"
        try:
            underlying = extract_underlying_symbol(symbol)
        except ValueError:
            return "unknown"
        return (
            "option"
            if self.universe.is_options_underlying_allowed(underlying)
            else "unknown"
        )

    @staticmethod
    def _positive(value: Decimal, name: str) -> Decimal:
        converted = to_decimal(value)
        if converted <= Decimal("0"):
            raise ValueError(f"{name} must be positive")
        return converted
