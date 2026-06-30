"""Download and store historical bars for the configured universe."""

from __future__ import annotations

import argparse
from datetime import date, timedelta

from trading_lab.market_data.bars_loader import BarsLoader
from trading_lab.market_data.price_store import PriceStore
from trading_lab.universe.tradable_universe import TradableUniverse


def parse_args() -> argparse.Namespace:
    """Parse the optional date range and timeframe."""
    today = date.today()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default=str(today - timedelta(days=365)))
    parser.add_argument("--end", default=str(today))
    parser.add_argument("--timeframe", default="1Day")
    return parser.parse_args()


def main() -> int:
    """Download the universe and print a clear persistence summary."""
    args = parse_args()
    universe = TradableUniverse()
    attempted = universe.get_all_symbols()

    try:
        loader = BarsLoader(universe=universe)
        store = PriceStore()
        bars_by_symbol = loader.load_universe_bars(
            start=args.start,
            end=args.end,
            timeframe=args.timeframe,
        )
    except (ValueError, TypeError) as error:
        print(f"Market data download could not start: {error}")
        return 1

    output_paths = {}
    for symbol, frame in bars_by_symbol.items():
        try:
            output_paths[symbol] = store.save(symbol, frame)
        except Exception as error:
            print(f"Warning: failed to save {symbol}: {error}")

    succeeded = list(output_paths)
    failed = [symbol for symbol in attempted if symbol not in output_paths]
    print("\nMARKET DATA SUMMARY")
    print(f"Symbols attempted: {len(attempted)}")
    print(f"Symbols succeeded: {len(succeeded)}")
    print(f"Symbols failed: {len(failed)}")
    if failed:
        print(f"Failed symbols: {', '.join(failed)}")
    for symbol, path in output_paths.items():
        print(f"  {symbol}: {path}")
    return 0 if succeeded else 1


if __name__ == "__main__":
    raise SystemExit(main())
