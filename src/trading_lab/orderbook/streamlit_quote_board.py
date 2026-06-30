"""Streamlit rendering for the read-only live quote board."""

from __future__ import annotations

import html
import time
from datetime import datetime, timezone
from decimal import Decimal

from trading_lab.orderbook.live_quote_models import LiveQuote
from trading_lab.orderbook.live_quote_state import LiveQuoteState


def render_quote_board(
    symbols: list[str],
    instrument_type: str,
    quote_state: LiveQuoteState,
) -> None:
    """Render one top-of-book row per symbol and refresh every second."""
    import streamlit as st

    st.title("Live Quote Board")
    st.caption(
        f"Instrument type: {instrument_type} | "
        f"Selected universe: {', '.join(symbols)}"
    )
    st.markdown(_CSS, unsafe_allow_html=True)

    quotes_by_symbol = {quote.symbol: quote for quote in quote_state.get_all_quotes()}
    rows = []
    for symbol in symbols:
        quote = quotes_by_symbol.get(symbol)
        if quote is None:
            quote = _missing_quote(symbol, instrument_type)
        rows.append(_quote_row(quote))

    if not rows or all(quote.status == "missing" for quote in quotes_by_symbol.values()):
        st.info("Waiting for quote...")

    st.markdown(
        "<div class='quote-table'><table>"
        "<thead><tr>"
        "<th>Symbol</th><th class='bid'>BID</th><th class='bid'>BID Size</th>"
        "<th class='ask'>ASK</th><th class='ask'>ASK Size</th>"
        "<th>Spread</th><th>Spread bps</th><th>Mid</th>"
        "<th>Time</th><th>Status</th>"
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>",
        unsafe_allow_html=True,
    )

    errors = quote_state.get_errors()
    with st.expander(f"Warnings / errors ({len(errors)})", expanded=bool(errors)):
        if errors:
            for error in errors:
                st.warning(error)
        else:
            st.write("No stream errors.")

    refresh_seconds = float(st.session_state.get("refresh_seconds", 1))
    time.sleep(max(refresh_seconds, 0.2))
    st.rerun()


def _quote_row(quote: LiveQuote) -> str:
    status = _display_status(quote)
    values = [
        html.escape(quote.symbol),
        _format_decimal(quote.bid_price),
        _format_decimal(quote.bid_size),
        _format_decimal(quote.ask_price),
        _format_decimal(quote.ask_size),
        _format_decimal(quote.spread),
        _format_decimal(quote.spread_bps),
        _format_decimal(quote.mid_price),
        html.escape(quote.timestamp or "—"),
        html.escape(status),
    ]
    classes = ["", "bid", "bid", "ask", "ask", "", "", "", "", status]
    cells = "".join(
        f"<td class='{css_class}'>{value}</td>"
        for value, css_class in zip(values, classes)
    )
    return f"<tr>{cells}</tr>"


def _display_status(quote: LiveQuote) -> str:
    if quote.status != "live" or not quote.timestamp:
        return quote.status
    try:
        quoted_at = datetime.fromisoformat(quote.timestamp.replace("Z", "+00:00"))
        if quoted_at.tzinfo is None:
            quoted_at = quoted_at.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - quoted_at.astimezone(timezone.utc)
        return "stale" if age.total_seconds() > 15 else "live"
    except ValueError:
        return "stale"


def _format_decimal(value: Decimal | None) -> str:
    if value is None:
        return "—"
    return html.escape(f"{value:.8f}".rstrip("0").rstrip("."))


def _missing_quote(symbol: str, instrument_type: str) -> LiveQuote:
    return LiveQuote(
        symbol=symbol,
        instrument_type=instrument_type,
        bid_price=None,
        bid_size=None,
        ask_price=None,
        ask_size=None,
        mid_price=None,
        spread=None,
        spread_bps=None,
        timestamp=None,
        source="waiting",
        status="missing",
    )


_CSS = """
<style>
.quote-table { overflow-x: auto; }
.quote-table table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
.quote-table th, .quote-table td {
  padding: 0.65rem 0.75rem; border-bottom: 1px solid #374151; text-align: right;
}
.quote-table th:first-child, .quote-table td:first-child { text-align: left; font-weight: 700; }
.quote-table .bid { background: rgba(250, 204, 21, 0.20); color: #facc15; }
.quote-table .ask { background: rgba(59, 130, 246, 0.20); color: #60a5fa; }
.quote-table .live { color: #22c55e; font-weight: 700; }
.quote-table .stale { color: #f59e0b; font-weight: 700; }
.quote-table .missing, .quote-table .error { color: #ef4444; font-weight: 700; }
</style>
"""
