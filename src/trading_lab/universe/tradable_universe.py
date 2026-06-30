"""Small, explicit universe of assets allowed by the research project."""


US_MACRO_ETFS = [
    "SPY",
    "QQQ",
    "IWM",
    "TLT",
    "GLD",
    "HYG",
    "LQD",
    "XLF",
    "XLK",
    "XLE",
]

EUROPE_PROXY_ETFS = ["VGK", "FEZ", "EWG", "EWU", "EZU"]
OVERNIGHT_US_ETFS = ["SPY", "QQQ", "EWJ", "FXI", "EWT", "AIA"]
CRYPTO = ["BTC/USD", "ETH/USD"]
OPTIONS_UNDERLYINGS_ALLOWED_LATER = ["SPY", "QQQ"]


class TradableUniverse:
    """Answer simple questions about symbols supported by the project."""

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """Normalize user-entered symbols for comparisons and requests."""
        return symbol.strip().upper()

    def is_allowed_symbol(self, symbol: str) -> bool:
        """Return whether an equity, ETF, or crypto symbol is allowed."""
        return self.normalize_symbol(symbol) in self.get_all_symbols()

    def is_crypto(self, symbol: str) -> bool:
        """Return whether the symbol belongs to the crypto universe."""
        return self.normalize_symbol(symbol) in CRYPTO

    def is_equity_or_etf(self, symbol: str) -> bool:
        """Return whether the symbol belongs to the equity/ETF universe."""
        return self.normalize_symbol(symbol) in self.get_equity_etf_symbols()

    def is_options_underlying_allowed(self, symbol: str) -> bool:
        """Return whether the underlying may support options in a later version."""
        return self.normalize_symbol(symbol) in OPTIONS_UNDERLYINGS_ALLOWED_LATER

    def is_overnight_symbol(self, symbol: str) -> bool:
        """Return whether the US-listed ETF belongs to the overnight watchlist."""
        return self.normalize_symbol(symbol) in OVERNIGHT_US_ETFS

    @staticmethod
    def get_all_symbols() -> list[str]:
        """Return every currently allowed symbol."""
        return list(
            dict.fromkeys(
                [*US_MACRO_ETFS, *EUROPE_PROXY_ETFS, *OVERNIGHT_US_ETFS, *CRYPTO]
            )
        )

    @staticmethod
    def get_equity_etf_symbols() -> list[str]:
        """Return US and Europe-proxy ETF symbols."""
        return list(
            dict.fromkeys([*US_MACRO_ETFS, *EUROPE_PROXY_ETFS, *OVERNIGHT_US_ETFS])
        )

    @staticmethod
    def get_crypto_symbols() -> list[str]:
        """Return allowed crypto pair symbols."""
        return list(CRYPTO)

    @staticmethod
    def get_overnight_symbols() -> list[str]:
        """Return US-listed ETFs monitored through Alpaca's overnight feed."""
        return list(OVERNIGHT_US_ETFS)
