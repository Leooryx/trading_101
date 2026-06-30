"""Tests for local JSON account snapshots."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd

from trading_lab.loaders.order_loader import ORDER_COLUMNS
from trading_lab.models.account import AccountSnapshot
from trading_lab.services.portfolio_service import PortfolioSnapshot
from trading_lab.storage.account_snapshot_store import AccountSnapshotStore


class AccountSnapshotStoreTests(unittest.TestCase):
    """Test JSON serialization without calling Alpaca."""

    def test_saves_timestamped_json_with_string_decimals(self) -> None:
        snapshot = PortfolioSnapshot(
            account=AccountSnapshot(
                status="ACTIVE",
                currency="USD",
                cash=Decimal("100000"),
                buying_power=Decimal("200000"),
                portfolio_value=Decimal("100000"),
                equity=Decimal("100000"),
            ),
            positions=pd.DataFrame(
                [
                    {
                        "symbol": "SPY",
                        "quantity": Decimal("2"),
                        "market_value": Decimal("1000.50"),
                    }
                ]
            ),
            open_orders=pd.DataFrame(columns=ORDER_COLUMNS),
        )
        captured_at = datetime(2026, 6, 30, 18, 30, tzinfo=timezone.utc)

        with tempfile.TemporaryDirectory() as temporary_directory:
            store = AccountSnapshotStore(Path(temporary_directory))
            output_path = store.save(snapshot, captured_at=captured_at)
            payload = json.loads(output_path.read_text(encoding="utf-8"))

            self.assertEqual(
                output_path.name,
                "account_snapshot_20260630T183000Z.json",
            )
            self.assertEqual(payload["timestamp"], "2026-06-30T18:30:00Z")
            self.assertEqual(payload["account"]["cash"], "100000")
            self.assertEqual(payload["positions"][0]["quantity"], "2")
            self.assertEqual(
                payload["positions"][0]["market_value"],
                "1000.50",
            )
            self.assertEqual(payload["open_orders"], [])


if __name__ == "__main__":
    unittest.main()
