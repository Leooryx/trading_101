"""Load Alpaca option snapshots and Greeks into a DataFrame."""

from collections.abc import Sequence

import pandas as pd
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.requests import OptionSnapshotRequest

from trading_lab.utils.money import to_decimal


OPTION_SNAPSHOT_COLUMNS = [
    "option_symbol",
    "implied_volatility",
    "delta",
    "gamma",
    "vega",
    "theta",
    "greeks_available",
]


class OptionSnapshotLoader:
    """Load current market snapshots for option contract symbols."""

    def __init__(self, client: OptionHistoricalDataClient) -> None:
        self.client = client

    def load(self, symbols: Sequence[str]) -> pd.DataFrame:
        """Return current implied volatility and Greeks for each symbol."""
        unique_symbols = list(dict.fromkeys(symbols))
        if not unique_symbols:
            return pd.DataFrame(columns=OPTION_SNAPSHOT_COLUMNS)

        request = OptionSnapshotRequest(symbol_or_symbols=unique_symbols)
        snapshots = self.client.get_option_snapshot(request)
        records = []

        for symbol, snapshot in snapshots.items():
            greeks = snapshot.greeks
            records.append(
                {
                    "option_symbol": symbol,
                    "implied_volatility": to_decimal(snapshot.implied_volatility),
                    "delta": to_decimal(greeks.delta if greeks else None),
                    "gamma": to_decimal(greeks.gamma if greeks else None),
                    "vega": to_decimal(greeks.vega if greeks else None),
                    "theta": to_decimal(greeks.theta if greeks else None),
                    "greeks_available": greeks is not None,
                }
            )

        return pd.DataFrame.from_records(records, columns=OPTION_SNAPSHOT_COLUMNS)
