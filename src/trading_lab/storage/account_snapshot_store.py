"""Persist portfolio snapshots as local JSON files."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd

from trading_lab.config.settings import PROJECT_ROOT
from trading_lab.services.portfolio_service import PortfolioSnapshot


class AccountSnapshotStore:
    """Save point-in-time account state under the project's data folder."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or PROJECT_ROOT / "data" / "account_snapshots"

    def save(
        self,
        snapshot: PortfolioSnapshot,
        captured_at: datetime | None = None,
    ) -> Path:
        """Serialize a portfolio snapshot to a timestamped JSON file."""
        timestamp = self._as_utc(captured_at or datetime.now(timezone.utc))
        payload = {
            "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
            "account": {
                "status": snapshot.account.status,
                "currency": snapshot.account.currency,
                "cash": str(snapshot.account.cash),
                "buying_power": str(snapshot.account.buying_power),
                "portfolio_value": str(snapshot.account.portfolio_value),
                "equity": str(snapshot.account.equity),
            },
            "positions": self._dataframe_records(snapshot.positions),
            "open_orders": self._dataframe_records(snapshot.open_orders),
        }

        self.root.mkdir(parents=True, exist_ok=True)
        filename = f"account_snapshot_{timestamp.strftime('%Y%m%dT%H%M%SZ')}.json"
        output_path = self.root / filename
        output_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return output_path

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        """Normalize aware or naive timestamps to UTC."""
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @classmethod
    def _dataframe_records(cls, frame: pd.DataFrame) -> list[dict[str, Any]]:
        """Convert DataFrame rows to values accepted by the JSON encoder."""
        return [
            {column: cls._json_value(value) for column, value in record.items()}
            for record in frame.to_dict(orient="records")
        ]

    @staticmethod
    def _json_value(value: Any) -> Any:
        """Convert Decimal, date, and missing pandas values safely."""
        if value is None:
            return None
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, (datetime, date)):
            return value.isoformat()

        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass

        item = getattr(value, "item", None)
        return item() if callable(item) else value
