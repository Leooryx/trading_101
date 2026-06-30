"""Console reporting for option Greek exposure books."""

from trading_lab.services.option_greeks_service import OptionGreeksBook


class ConsoleGreeksReporter:
    """Print contract-level and underlying-level Greek exposures."""

    @staticmethod
    def print_book(book: OptionGreeksBook) -> None:
        """Print the current option Greek exposure book."""
        print("OPTION GREEKS BOOK")

        if book.positions.empty:
            print("No open option positions.")
            return

        print("\nBY CONTRACT")
        for position in book.positions.itertuples(index=False):
            print(f"\n{position.option_symbol} ({position.side})")
            print(f"  Underlying: {position.underlying_symbol}")
            print(f"  Contracts: {position.signed_contract_quantity}")
            print(f"  Delta: {position.delta}")
            print(f"  Gamma: {position.gamma}")
            print(f"  Vega: {position.vega}")
            print(f"  Theta: {position.theta}")
            print(f"  Delta exposure: {position.delta_exposure}")
            print(f"  Gamma exposure: {position.gamma_exposure}")
            print(f"  Vega exposure: {position.vega_exposure}")
            print(f"  Theta exposure: {position.theta_exposure}")
            if not position.greeks_available:
                print("  Warning: Greeks unavailable; exposures shown as zero.")

        print("\nBY UNDERLYING")
        for underlying in book.by_underlying.itertuples(index=False):
            print(f"\n{underlying.underlying_symbol}")
            print(f"  Option positions: {underlying.option_position_count}")
            print(f"  Net contracts: {underlying.net_contract_quantity}")
            print(f"  Delta exposure: {underlying.delta_exposure}")
            print(f"  Gamma exposure: {underlying.gamma_exposure}")
            print(f"  Vega exposure: {underlying.vega_exposure}")
            print(f"  Theta exposure: {underlying.theta_exposure}")
