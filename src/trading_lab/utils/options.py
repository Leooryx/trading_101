"""Helpers for OCC-style option symbols."""

import re


OPTION_SYMBOL_PATTERN = re.compile(
    r"^(?P<underlying>[A-Z0-9.]{1,6})\d{6}[CP]\d{8}$",
    re.IGNORECASE,
)


def extract_underlying_symbol(option_symbol: str) -> str:
    """Extract the underlying ticker from an Alpaca/OCC option symbol."""
    match = OPTION_SYMBOL_PATTERN.fullmatch(option_symbol.strip())
    if not match:
        raise ValueError(f"Invalid OCC option symbol: {option_symbol}")
    return match.group("underlying").upper()
