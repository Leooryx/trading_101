"""Offline tests for historical bars and local price storage."""

import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pandas as pd

from trading_lab.market_data.bars_loader import BAR_COLUMNS, BarsLoader
from trading_lab.market_data.price_store import PriceStore


class BarsLoaderTests(unittest.TestCase):
    def test_one_failed_symbol_does_not_stop_the_batch(self) -> None:
        stock_client = Mock()

        def get_bars(request: object) -> object:
            symbol = request.symbol_or_symbols
            if symbol == "QQQ":
                raise RuntimeError("temporary provider error")
            bar = SimpleNamespace(
                timestamp=datetime(2026, 1, 2, tzinfo=timezone.utc),
                open=100.0,
                high=102.0,
                low=99.0,
                close=101.0,
                volume=1000.0,
            )
            return SimpleNamespace(data={symbol: [bar]})

        stock_client.get_stock_bars.side_effect = get_bars
        loader = BarsLoader(stock_client=stock_client, crypto_client=Mock())

        with patch("builtins.print"):
            result = loader.load_equity_bars(
                ["SPY", "QQQ"],
                "2026-01-01",
                "2026-01-03",
            )

        self.assertEqual(list(result), ["SPY"])
        self.assertEqual(result["SPY"].columns.tolist(), BAR_COLUMNS)
        self.assertEqual(len(loader.warnings), 1)
        self.assertIn("QQQ", loader.warnings[0])


class PriceStoreTests(unittest.TestCase):
    def test_saves_and_loads_files_with_clean_crypto_name(self) -> None:
        frame = pd.DataFrame(
            [{"timestamp": "2026-01-02", "close": 100.0}]
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            store = PriceStore(Path(temporary_directory))

            output_path = store.save("BTC/USD", frame)
            loaded = store.load("BTC/USD")

            self.assertEqual(output_path.stem, "BTCUSD")
            self.assertTrue(store.exists("BTC/USD"))
            self.assertEqual(loaded.loc[0, "close"], 100.0)


if __name__ == "__main__":
    unittest.main()
