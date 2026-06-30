"""Application settings loaded from the project-level .env file."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    """Environment-based settings for the Alpaca trading client."""

    ALPACA_API_KEY: str = os.getenv("ALPACA_API_KEY", "")
    ALPACA_SECRET_KEY: str = os.getenv("ALPACA_SECRET_KEY", "")
    ALPACA_PAPER: bool = os.getenv("ALPACA_PAPER", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    @classmethod
    def validate_alpaca(cls) -> None:
        """Raise a clear error when required Alpaca credentials are missing."""
        missing = []

        if not cls.ALPACA_API_KEY:
            missing.append("ALPACA_API_KEY")
        if not cls.ALPACA_SECRET_KEY:
            missing.append("ALPACA_SECRET_KEY")

        if missing:
            names = ", ".join(missing)
            raise ValueError(
                f"Missing required environment variables: {names}. "
                "Run scripts/setup_credentials.py first."
            )
