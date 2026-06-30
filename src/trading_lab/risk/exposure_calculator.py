"""Calculate current and simulated post-trade money exposures."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pandas as pd

from trading_lab.execution.models import ProposedOrder
from trading_lab.market_data.quote_models import MarketQuote
from trading_lab.risk.greek_exposure import (
    DEFAULT_OPTION_CONTRACT_MULTIPLIER,
    BookGreekExposure,
    GreekExposure,
)
from trading_lab.services.portfolio_service import PortfolioSnapshot
from trading_lab.utils.money import to_decimal
from trading_lab.utils.options import extract_underlying_symbol


SUMMARY_FIELDS = [
    "notional",
    "delta_notional",
    "gamma_notional",
    "vega_notional",
    "theta_notional",
    "delta_pnl_1pct_move",
    "gamma_pnl_1pct_move",
    "vega_pnl_1vol_point",
    "theta_pnl_1day",
]


class ExposureCalculator:
    """Compute provider-neutral exposures from portfolio DataFrames."""

    def __init__(
        self,
        option_multiplier: Decimal = DEFAULT_OPTION_CONTRACT_MULTIPLIER,
    ) -> None:
        self.option_multiplier = option_multiplier
        self.warnings: list[str] = []

    def compute_current_book_exposure(
        self,
        portfolio_snapshot: PortfolioSnapshot,
        quotes: dict[str, MarketQuote] | None = None,
    ) -> BookGreekExposure:
        """Compute current position exposures using quotes when supplied."""
        self.warnings.clear()
        return self._compute_positions(portfolio_snapshot.positions, quotes or {})

    def compute_post_trade_exposure(
        self,
        portfolio_snapshot: PortfolioSnapshot,
        proposed_order: ProposedOrder,
        quote: MarketQuote,
    ) -> BookGreekExposure:
        """Simulate the order in a copied positions DataFrame and recompute risk."""
        self.warnings.clear()
        positions = portfolio_snapshot.positions.copy()
        fill_price = quote.estimated_fill_price(proposed_order.side)
        if fill_price is None or fill_price <= Decimal("0"):
            self.warnings.append(
                f"No usable quote for {proposed_order.symbol}; post-trade exposure "
                "is unchanged."
            )
            return self._compute_positions(
                positions,
                {proposed_order.symbol: quote},
            )

        trade_quantity = proposed_order.quantity
        if trade_quantity is None and proposed_order.notional is not None:
            trade_quantity = proposed_order.notional / fill_price
        if trade_quantity is None:
            self.warnings.append("Order quantity could not be estimated.")
            return self._compute_positions(positions, {proposed_order.symbol: quote})

        quantity_change = (
            trade_quantity
            if proposed_order.side == "buy"
            else -trade_quantity
        )
        matching = positions.index[positions["symbol"].eq(proposed_order.symbol)]
        if len(matching):
            index = matching[0]
            current_quantity = self._signed_position_quantity(positions.loc[index])
            new_quantity = current_quantity + quantity_change
            if new_quantity == Decimal("0"):
                positions = positions.drop(index=index)
            else:
                positions.loc[index, "quantity"] = abs(new_quantity)
                positions.loc[index, "side"] = (
                    "long" if new_quantity > Decimal("0") else "short"
                )
                positions.loc[index, "current_price"] = fill_price
                positions.loc[index, "market_value"] = new_quantity * fill_price
        else:
            positions = self._append_simulated_position(
                positions,
                proposed_order,
                quantity_change,
                fill_price,
            )

        return self._compute_positions(
            positions,
            {proposed_order.symbol: quote},
        )

    def calculate_line_exposure(
        self,
        symbol: str,
        asset_class: str,
        quantity: Decimal,
        price: Decimal,
        underlying_symbol: str | None = None,
        delta: Decimal = Decimal("0"),
        gamma: Decimal = Decimal("0"),
        vega: Decimal = Decimal("0"),
        theta: Decimal = Decimal("0"),
    ) -> GreekExposure:
        """Calculate one line item using explicit, testable formulas."""
        if asset_class == "option":
            notional = quantity * self.option_multiplier * price
            delta_notional = notional * delta
            gamma_notional = notional * gamma
            vega_notional = notional * vega
            theta_notional = notional * theta
            one_percent_move = price * Decimal("0.01")
            gamma_pnl = (
                Decimal("0.5")
                * gamma
                * quantity
                * self.option_multiplier
                * one_percent_move**2
            )
            vega_pnl = quantity * self.option_multiplier * vega
            theta_pnl = quantity * self.option_multiplier * theta
        else:
            notional = quantity * price
            direction = (
                Decimal("1")
                if quantity > Decimal("0")
                else Decimal("-1") if quantity < Decimal("0") else Decimal("0")
            )
            delta = direction
            gamma = vega = theta = Decimal("0")
            delta_notional = notional
            gamma_notional = vega_notional = theta_notional = Decimal("0")
            gamma_pnl = vega_pnl = theta_pnl = Decimal("0")

        return GreekExposure(
            symbol=symbol,
            underlying_symbol=underlying_symbol,
            asset_class=asset_class,
            quantity=quantity,
            price=price,
            notional=notional,
            delta=delta,
            gamma=gamma,
            vega=vega,
            theta=theta,
            delta_notional=delta_notional,
            gamma_notional=gamma_notional,
            vega_notional=vega_notional,
            theta_notional=theta_notional,
            delta_pnl_1pct_move=delta_notional * Decimal("0.01"),
            gamma_pnl_1pct_move=gamma_pnl,
            vega_pnl_1vol_point=vega_pnl,
            theta_pnl_1day=theta_pnl,
        )

    def _compute_positions(
        self,
        positions: pd.DataFrame,
        quotes: dict[str, MarketQuote],
    ) -> BookGreekExposure:
        line_items = []
        for _, row in positions.iterrows():
            symbol = str(row["symbol"])
            asset_class = self._asset_class(row.get("asset_class"))
            quantity = self._signed_position_quantity(row)
            quote = quotes.get(symbol)

            if asset_class == "option":
                underlying = self._underlying_symbol(symbol, row)
                underlying_quote = quotes.get(underlying) if underlying else None
                price = self._first_decimal(
                    self._quote_price(underlying_quote),
                    row.get("underlying_price"),
                )
                greek_values = {
                    name: self._optional_decimal(row.get(name))
                    for name in ["delta", "gamma", "vega", "theta"]
                }
                if any(value is None for value in greek_values.values()):
                    self.warnings.append(
                        f"Option Greeks are incomplete for {symbol}; missing values "
                        "were set to zero."
                    )
                if price == Decimal("0"):
                    self.warnings.append(
                        f"Underlying price is unavailable for {symbol}; option "
                        "notionals were set to zero."
                    )
                line_items.append(
                    self.calculate_line_exposure(
                        symbol=symbol,
                        underlying_symbol=underlying,
                        asset_class="option",
                        quantity=quantity,
                        price=price,
                        delta=greek_values["delta"] or Decimal("0"),
                        gamma=greek_values["gamma"] or Decimal("0"),
                        vega=greek_values["vega"] or Decimal("0"),
                        theta=greek_values["theta"] or Decimal("0"),
                    )
                )
            else:
                price = self._first_decimal(
                    self._quote_price(quote),
                    row.get("current_price"),
                )
                line_items.append(
                    self.calculate_line_exposure(
                        symbol=symbol,
                        underlying_symbol=symbol,
                        asset_class=asset_class,
                        quantity=quantity,
                        price=price,
                    )
                )
        return self._aggregate(line_items)

    def _append_simulated_position(
        self,
        positions: pd.DataFrame,
        order: ProposedOrder,
        signed_quantity: Decimal,
        fill_price: Decimal,
    ) -> pd.DataFrame:
        record = {column: None for column in positions.columns}
        record.update(
            {
                "symbol": order.symbol,
                "asset_class": order.asset_class,
                "quantity": abs(signed_quantity),
                "market_value": signed_quantity * fill_price,
                "average_entry_price": fill_price,
                "current_price": fill_price,
                "unrealized_pnl": Decimal("0"),
                "unrealized_pnl_pct": Decimal("0"),
                "side": "long" if signed_quantity > Decimal("0") else "short",
            }
        )
        if order.metadata:
            record.update(order.metadata)
        return pd.concat([positions, pd.DataFrame([record])], ignore_index=True)

    @staticmethod
    def _signed_position_quantity(row: Any) -> Decimal:
        quantity = abs(to_decimal(row.get("quantity")))
        return -quantity if str(row.get("side", "long")).lower() == "short" else quantity

    @staticmethod
    def _asset_class(value: Any) -> str:
        normalized = str(value or "unknown").lower()
        if normalized in {"equity", "us_equity", "etf"}:
            return "equity"
        if normalized in {"crypto", "cryptocurrency"}:
            return "crypto"
        if normalized in {"option", "options", "us_option"}:
            return "option"
        return "unknown"

    @staticmethod
    def _underlying_symbol(symbol: str, row: Any) -> str | None:
        explicit = row.get("underlying_symbol")
        if explicit is not None and not pd.isna(explicit):
            return str(explicit)
        try:
            return extract_underlying_symbol(symbol)
        except ValueError:
            return None

    @staticmethod
    def _quote_price(quote: MarketQuote | None) -> Decimal | None:
        return quote.reference_price() if quote else None

    @staticmethod
    def _optional_decimal(value: Any) -> Decimal | None:
        if value is None or pd.isna(value):
            return None
        return to_decimal(value)

    @classmethod
    def _first_decimal(cls, *values: Any) -> Decimal:
        for value in values:
            converted = cls._optional_decimal(value)
            if converted is not None:
                return converted
        return Decimal("0")

    @staticmethod
    def _aggregate(line_items: list[GreekExposure]) -> BookGreekExposure:
        by_asset_class: dict[str, dict[str, Decimal]] = {}
        by_underlying: dict[str, dict[str, Decimal]] = {}

        for line in line_items:
            ExposureCalculator._add_summary(
                by_asset_class,
                line.asset_class,
                line,
            )
            ExposureCalculator._add_summary(
                by_underlying,
                line.underlying_symbol or line.symbol,
                line,
            )

        totals = {
            field: sum(
                (getattr(line, field) for line in line_items),
                Decimal("0"),
            )
            for field in SUMMARY_FIELDS
        }
        return BookGreekExposure(
            total_notional=totals["notional"],
            total_delta_notional=totals["delta_notional"],
            total_gamma_notional=totals["gamma_notional"],
            total_vega_notional=totals["vega_notional"],
            total_theta_notional=totals["theta_notional"],
            total_delta_pnl_1pct_move=totals["delta_pnl_1pct_move"],
            total_gamma_pnl_1pct_move=totals["gamma_pnl_1pct_move"],
            total_vega_pnl_1vol_point=totals["vega_pnl_1vol_point"],
            total_theta_pnl_1day=totals["theta_pnl_1day"],
            by_asset_class=by_asset_class,
            by_underlying=by_underlying,
            line_items=line_items,
        )

    @staticmethod
    def _add_summary(
        target: dict[str, dict[str, Decimal]],
        key: str,
        line: GreekExposure,
    ) -> None:
        summary = target.setdefault(
            key,
            {field: Decimal("0") for field in SUMMARY_FIELDS},
        )
        for field in SUMMARY_FIELDS:
            summary[field] += getattr(line, field)
