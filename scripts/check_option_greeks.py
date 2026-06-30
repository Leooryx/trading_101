"""Print Greek exposures for the current Alpaca option positions."""

from trading_lab.factories.alpaca_factory import AlpacaClientFactory
from trading_lab.loaders.option_snapshot_loader import OptionSnapshotLoader
from trading_lab.loaders.position_loader import PositionLoader
from trading_lab.reporting.console_greeks_reporter import ConsoleGreeksReporter
from trading_lab.services.option_greeks_service import OptionGreeksService


def main() -> None:
    """Build and print the current option Greek exposure book."""
    service = OptionGreeksService(
        position_loader=PositionLoader(
            AlpacaClientFactory.create_trading_client()
        ),
        snapshot_loader=OptionSnapshotLoader(
            AlpacaClientFactory.create_option_data_client()
        ),
    )
    ConsoleGreeksReporter.print_book(service.get_book())


if __name__ == "__main__":
    main()
