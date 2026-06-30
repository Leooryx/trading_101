"""Grouped choices derived from the existing TradableUniverse."""

from trading_lab.universe.tradable_universe import (
    CRYPTO,
    EUROPE_PROXY_ETFS,
    OPTIONS_UNDERLYINGS_ALLOWED_LATER,
    OVERNIGHT_US_ETFS,
    US_MACRO_ETFS,
    TradableUniverse,
)


class UniverseSelector:
    """Expose stable display groups for the interactive quote-board launcher."""

    def __init__(self, universe: TradableUniverse | None = None) -> None:
        self.universe = universe or TradableUniverse()

    def get_available_groups(self) -> dict[str, list[str]]:
        """Return named universe groups in launcher display order."""
        return {
            "US macro ETFs": list(US_MACRO_ETFS),
            "Europe proxy ETFs": list(EUROPE_PROXY_ETFS),
            "Overnight / Asia proxy ETFs (24/5)": list(OVERNIGHT_US_ETFS),
            "Crypto": list(CRYPTO),
            "Options underlyings allowed later": list(
                OPTIONS_UNDERLYINGS_ALLOWED_LATER
            ),
            "All equity/ETF symbols": self.universe.get_equity_etf_symbols(),
            "All symbols": self.universe.get_all_symbols(),
        }

    def normalize_symbol(self, symbol: str) -> str:
        """Normalize a user-entered symbol through the project universe."""
        return self.universe.normalize_symbol(symbol)

    def filter_symbols_by_group(self, group_name: str) -> list[str]:
        """Return a group's symbols or raise a readable selection error."""
        groups = self.get_available_groups()
        if group_name not in groups:
            raise ValueError(f"Unknown universe group: {group_name}")
        return list(groups[group_name])

    def infer_instrument_type(self, symbol: str, requested_type: str) -> str:
        """Infer equity, crypto, or option from a symbol and requested view."""
        normalized_symbol = self.normalize_symbol(symbol)
        normalized_type = requested_type.strip().lower()
        if normalized_type in {"option", "options"}:
            return "option"
        if normalized_type in {"overnight", "24/5"}:
            return "overnight"
        if self.universe.is_crypto(normalized_symbol):
            return "crypto"
        if normalized_type == "crypto":
            return "crypto"
        return "equity"
