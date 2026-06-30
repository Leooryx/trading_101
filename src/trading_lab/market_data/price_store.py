"""Local parquet/CSV storage for downloaded price data."""

import re
from pathlib import Path

import pandas as pd

from trading_lab.config.settings import PROJECT_ROOT


class PriceStore:
    """Save and load one local market-data file per symbol."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or PROJECT_ROOT / "data" / "market_data"

    def save(self, symbol: str, data: pd.DataFrame) -> Path:
        """Prefer parquet and fall back to CSV if parquet cannot be written."""
        self.root.mkdir(parents=True, exist_ok=True)
        parquet_path = self.root / f"{self._filename(symbol)}.parquet"
        try:
            data.to_parquet(parquet_path, index=False)
            return parquet_path
        except Exception:
            if parquet_path.exists():
                parquet_path.unlink()
            csv_path = self.root / f"{self._filename(symbol)}.csv"
            data.to_csv(csv_path, index=False)
            return csv_path

    def load(self, symbol: str) -> pd.DataFrame:
        """Load a previously saved parquet or CSV file."""
        parquet_path = self.root / f"{self._filename(symbol)}.parquet"
        if parquet_path.exists():
            return pd.read_parquet(parquet_path)

        csv_path = self.root / f"{self._filename(symbol)}.csv"
        if csv_path.exists():
            return pd.read_csv(csv_path)

        raise FileNotFoundError(f"No market data stored for {symbol}")

    def exists(self, symbol: str) -> bool:
        """Return whether either supported file format exists."""
        stem = self._filename(symbol)
        return (self.root / f"{stem}.parquet").exists() or (
            self.root / f"{stem}.csv"
        ).exists()

    @staticmethod
    def _filename(symbol: str) -> str:
        """Convert symbols such as BTC/USD to filesystem-safe names."""
        return re.sub(r"[^A-Z0-9]", "", symbol.strip().upper())
