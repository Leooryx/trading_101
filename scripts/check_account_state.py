"""Print the current Alpaca account, positions, and open orders."""

from trading_lab.factories.alpaca_factory import AlpacaClientFactory
from trading_lab.loaders.account_loader import AccountLoader
from trading_lab.loaders.order_loader import OrderLoader
from trading_lab.loaders.position_loader import PositionLoader
from trading_lab.reporting.console_reporter import ConsolePortfolioReporter
from trading_lab.services.portfolio_service import PortfolioService


def main() -> None:
    """Build and print the current portfolio snapshot."""
    client = AlpacaClientFactory.create_trading_client()
    service = PortfolioService(
        account_loader=AccountLoader(client),
        position_loader=PositionLoader(client),
        order_loader=OrderLoader(client),
    )
    ConsolePortfolioReporter.print_snapshot(service.get_snapshot())


if __name__ == "__main__":
    main()
