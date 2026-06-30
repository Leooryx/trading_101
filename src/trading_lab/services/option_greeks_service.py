"""Calculate and aggregate option Greek exposures."""

from dataclasses import dataclass
from decimal import Decimal

import pandas as pd

from trading_lab.loaders.option_snapshot_loader import OptionSnapshotLoader
from trading_lab.loaders.position_loader import PositionLoader
from trading_lab.utils.money import to_decimal
from trading_lab.utils.options import extract_underlying_symbol


CONTRACT_MULTIPLIER = Decimal("100")

GREEKS_POSITION_COLUMNS = [
    "option_symbol",
    "underlying_symbol",
    "asset_class",
    "side",
    "contract_quantity",
    "signed_contract_quantity",
    "contract_multiplier",
    "market_value",
    "implied_volatility",
    "delta",
    "gamma",
    "vega",
    "theta",
    "delta_exposure",
    "gamma_exposure",
    "vega_exposure",
    "theta_exposure",
    "greeks_available",
]

UNDERLYING_GREEKS_COLUMNS = [
    "underlying_symbol",
    "option_position_count",
    "net_contract_quantity",
    "delta_exposure",
    "gamma_exposure",
    "vega_exposure",
    "theta_exposure",
]


@dataclass(frozen=True)
class OptionGreeksBook:
    """Greek exposures by contract and aggregated by underlying."""

    positions: pd.DataFrame
    by_underlying: pd.DataFrame


class OptionGreeksService:
    """Build a Greek exposure book from open Alpaca option positions."""

    def __init__(
        self,
        position_loader: PositionLoader,
        snapshot_loader: OptionSnapshotLoader,
    ) -> None:
        self.position_loader = position_loader
        self.snapshot_loader = snapshot_loader

    def get_book(self) -> OptionGreeksBook:
        """Load positions and calculate contract-scaled Greek exposures."""
        positions = self.position_loader.load_all()
        is_option = positions["asset_class"].str.casefold().isin(
            {"option", "options", "us_option"}
        )
        option_positions = positions.loc[is_option].copy()

        if option_positions.empty:
            return self._empty_book()

        option_positions = option_positions.rename(
            columns={
                "symbol": "option_symbol",
                "quantity": "contract_quantity",
            }
        )
        symbols = option_positions["option_symbol"].drop_duplicates().tolist()
        snapshots = self.snapshot_loader.load(symbols)
        details = option_positions.merge(snapshots, on="option_symbol", how="left")

        details["underlying_symbol"] = details["option_symbol"].map(
            extract_underlying_symbol
        )
        details["greeks_available"] = details["greeks_available"].eq(True)

        for column in ["implied_volatility", "delta", "gamma", "vega", "theta"]:
            details[column] = details[column].map(self._decimal_or_zero)

        details["signed_contract_quantity"] = details.apply(
            self._signed_quantity,
            axis=1,
        )
        details["contract_multiplier"] = CONTRACT_MULTIPLIER

        scale = details["signed_contract_quantity"] * CONTRACT_MULTIPLIER
        for greek in ["delta", "gamma", "vega", "theta"]:
            details[f"{greek}_exposure"] = details[greek] * scale

        details = details[GREEKS_POSITION_COLUMNS]
        by_underlying = self._aggregate_by_underlying(details)
        return OptionGreeksBook(positions=details, by_underlying=by_underlying)

    @staticmethod
    def _decimal_or_zero(value: object) -> Decimal:
        """Normalize missing merged values and numeric values to Decimal."""
        if value is None or pd.isna(value):
            return Decimal("0")
        return to_decimal(value)

    @staticmethod
    def _signed_quantity(row: pd.Series) -> Decimal:
        """Normalize quantity sign from the explicit Alpaca position side."""
        quantity = abs(to_decimal(row["contract_quantity"]))
        return -quantity if str(row["side"]).casefold() == "short" else quantity

    @staticmethod
    def _aggregate_by_underlying(details: pd.DataFrame) -> pd.DataFrame:
        """Sum contract exposures for each underlying ticker."""
        aggregated = details.groupby("underlying_symbol", as_index=False).agg(
            option_position_count=("option_symbol", "count"),
            net_contract_quantity=("signed_contract_quantity", "sum"),
            delta_exposure=("delta_exposure", "sum"),
            gamma_exposure=("gamma_exposure", "sum"),
            vega_exposure=("vega_exposure", "sum"),
            theta_exposure=("theta_exposure", "sum"),
        )
        return aggregated[UNDERLYING_GREEKS_COLUMNS]

    @staticmethod
    def _empty_book() -> OptionGreeksBook:
        """Return an empty book whose DataFrames still expose their schema."""
        return OptionGreeksBook(
            positions=pd.DataFrame(columns=GREEKS_POSITION_COLUMNS),
            by_underlying=pd.DataFrame(columns=UNDERLYING_GREEKS_COLUMNS),
        )
