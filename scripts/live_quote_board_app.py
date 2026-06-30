"""Streamlit entrypoint for the read-only Alpaca live quote board."""

from __future__ import annotations

import argparse
import atexit
import json
from pathlib import Path
from typing import Any

import streamlit as st

from trading_lab.orderbook.alpaca_live_quote_stream import AlpacaLiveQuoteStream
from trading_lab.orderbook.live_quote_state import LiveQuoteState
from trading_lab.orderbook.streamlit_quote_board import render_quote_board


def parse_args() -> argparse.Namespace:
    """Read the launcher-generated config path after Streamlit's separator."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--config")
    args, _ = parser.parse_known_args()
    return args


def load_config(path: str | None) -> dict[str, Any]:
    """Load and validate a minimal quote-board JSON configuration."""
    if not path:
        raise ValueError("Missing --config path.")
    config_path = Path(path)
    if not config_path.exists():
        raise ValueError(f"Config file does not exist: {config_path}")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Invalid quote-board config: {error}") from error

    symbols = config.get("symbols")
    instrument_type = config.get("instrument_type")
    if not isinstance(symbols, list) or not symbols:
        raise ValueError("Config must contain a non-empty symbols list.")
    if instrument_type not in {"equity", "overnight", "crypto", "option"}:
        raise ValueError(
            "instrument_type must be equity, overnight, crypto, or option."
        )
    return config


def main() -> None:
    """Start one shared quote stream and render it across Streamlit reruns."""
    st.set_page_config(page_title="Live Quote Board", layout="wide")
    try:
        config = load_config(parse_args().config)
    except ValueError as error:
        st.error(str(error))
        return

    symbols = [str(symbol).strip().upper() for symbol in config["symbols"]]
    instrument_type = config["instrument_type"]
    config_key = (tuple(symbols), instrument_type)

    if st.session_state.get("quote_board_config_key") != config_key:
        old_stream = st.session_state.get("quote_stream")
        if old_stream is not None:
            old_stream.stop()
        quote_state = LiveQuoteState()
        stream = AlpacaLiveQuoteStream(symbols, instrument_type, quote_state)
        stream.start()
        st.session_state.quote_board_config_key = config_key
        st.session_state.quote_state = quote_state
        st.session_state.quote_stream = stream
        atexit.register(stream.stop)

    st.session_state.refresh_seconds = config.get("refresh_seconds", 1)
    st.sidebar.write(f"Group: {config.get('group_name', 'Custom')}")
    if st.sidebar.button("Stop stream"):
        st.session_state.quote_stream.stop()
        st.sidebar.success("Stream stopped.")

    render_quote_board(
        symbols=symbols,
        instrument_type=instrument_type,
        quote_state=st.session_state.quote_state,
    )


if __name__ == "__main__":
    main()
