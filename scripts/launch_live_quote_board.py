"""Interactive launcher for the read-only Streamlit live quote board."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

from trading_lab.config.settings import PROJECT_ROOT
from trading_lab.orderbook.universe_selector import UniverseSelector


def choose_number(prompt: str, maximum: int) -> int:
    """Prompt until the user enters a valid numbered choice."""
    while True:
        answer = input(prompt).strip()
        if answer.isdigit() and 1 <= int(answer) <= maximum:
            return int(answer)
        print(f"Please enter a number between 1 and {maximum}.")


def choose_symbols(available: list[str]) -> list[str]:
    """Select all symbols or validate a comma-separated subset."""
    load_all = input("Load all symbols? [Y/n] ").strip().lower()
    if load_all in {"", "y", "yes"}:
        return list(available)

    while True:
        raw = input("Enter comma-separated symbols: ")
        selected = list(
            dict.fromkeys(symbol.strip().upper() for symbol in raw.split(",") if symbol.strip())
        )
        invalid = [symbol for symbol in selected if symbol not in available]
        if selected and not invalid:
            return selected
        if invalid:
            print(f"Symbols outside this group: {', '.join(invalid)}")
        else:
            print("Select at least one symbol.")


def compatible_symbols(
    symbols: list[str],
    instrument_type: str,
    selector: UniverseSelector,
) -> list[str]:
    """Keep only symbols compatible with the chosen stream endpoint."""
    if instrument_type == "crypto":
        return [symbol for symbol in symbols if selector.universe.is_crypto(symbol)]
    if instrument_type == "overnight":
        return [
            symbol for symbol in symbols if selector.universe.is_overnight_symbol(symbol)
        ]
    if instrument_type == "equity":
        return [symbol for symbol in symbols if selector.universe.is_equity_or_etf(symbol)]
    return [
        symbol
        for symbol in symbols
        if selector.universe.is_options_underlying_allowed(symbol)
    ]


def main() -> int:
    """Collect choices, write local config, and launch Streamlit."""
    if importlib.util.find_spec("streamlit") is None:
        print("Streamlit is not installed. Run: python -m pip install streamlit")
        return 1

    selector = UniverseSelector()
    groups = selector.get_available_groups()
    group_names = list(groups)

    print("Available universe groups:\n")
    for index, group_name in enumerate(group_names, start=1):
        print(f"{index}. {group_name}")
    group_index = choose_number("\nSelect group: ", len(group_names)) - 1
    group_name = group_names[group_index]
    available = selector.filter_symbols_by_group(group_name)
    print(f"\nSymbols:\n{', '.join(available)}\n")
    selected = choose_symbols(available)

    instrument_choices = [
        ("equity / ETF", "equity"),
        ("overnight US ETF (24/5)", "overnight"),
        ("crypto", "crypto"),
        ("options", "option"),
    ]
    print("\nInstrument type:\n")
    for index, (label, _) in enumerate(instrument_choices, start=1):
        print(f"{index}. {label}")
    instrument_index = choose_number(
        "\nSelect instrument type: ", len(instrument_choices)
    ) - 1
    instrument_type = instrument_choices[instrument_index][1]
    compatible = compatible_symbols(selected, instrument_type, selector)
    skipped = [symbol for symbol in selected if symbol not in compatible]
    if skipped:
        print(
            "Skipping symbols incompatible with this stream: "
            + ", ".join(skipped)
        )
    selected = compatible
    if not selected:
        print("No selected symbols are compatible with this instrument type.")
        return 1

    config_root = PROJECT_ROOT / "data" / "live_quote_board" / "configs"
    config_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    config_path = config_root / f"quote_board_{timestamp}.json"
    config = {
        "symbols": selected,
        "instrument_type": instrument_type,
        "group_name": group_name,
        "refresh_seconds": 1,
    }
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    print("\nLaunching Streamlit quote board for:")
    print(f"Group: {group_name}")
    print(f"Instrument type: {instrument_type}")
    print(f"Symbols: {', '.join(selected)}")

    app_path = PROJECT_ROOT / "scripts" / "live_quote_board_app.py"
    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--",
        "--config",
        str(config_path),
    ]
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    try:
        return subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            env=environment,
            check=False,
        ).returncode
    except KeyboardInterrupt:
        print("\nQuote board closed.")
        return 0
    except OSError as error:
        print(f"Could not launch Streamlit: {error}")
        return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (EOFError, KeyboardInterrupt):
        print("\nLauncher cancelled.")
        raise SystemExit(0)
