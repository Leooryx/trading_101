"""Manually save the current Alpaca account state as JSON."""

from trading_lab.factories.alpaca_factory import AlpacaClientFactory
from trading_lab.loaders.account_loader import AccountLoader
from trading_lab.loaders.order_loader import OrderLoader
from trading_lab.loaders.position_loader import PositionLoader
from trading_lab.services.portfolio_service import PortfolioService
from trading_lab.storage.account_snapshot_store import AccountSnapshotStore


def main() -> None:
    """Load the current account state and save it under data/."""
    client = AlpacaClientFactory.create_trading_client()
    service = PortfolioService(
        account_loader=AccountLoader(client),
        position_loader=PositionLoader(client),
        order_loader=OrderLoader(client),
    )
    output_path = AccountSnapshotStore().save(service.get_snapshot())
    print(f"Account snapshot saved to: {output_path}")


if __name__ == "__main__":
    main()
