"""Console reporting for portfolio snapshots."""

from trading_lab.services.portfolio_service import PortfolioSnapshot


class ConsolePortfolioReporter:
    """Print a readable portfolio snapshot to the console."""

    @staticmethod
    def print_snapshot(snapshot: PortfolioSnapshot) -> None:
        """Print account, position, and open-order details."""
        account = snapshot.account

        print("ACCOUNT")
        print(f"Status: {account.status}")
        print(f"Currency: {account.currency}")
        print(f"Cash: {account.cash}")
        print(f"Buying power: {account.buying_power}")
        print(f"Portfolio value: {account.portfolio_value}")
        print(f"Equity: {account.equity}")

        print("\nPOSITIONS")
        if snapshot.positions.empty:
            print("No open positions.")
        else:
            for position in snapshot.positions.itertuples(index=False):
                print(f"\n{position.symbol}")
                print(f"  Asset class: {position.asset_class}")
                print(f"  Quantity: {position.quantity}")
                print(f"  Market value: {position.market_value}")
                print(f"  Weight: {position.portfolio_weight:.2%}")
                print(f"  Average entry price: {position.average_entry_price}")
                print(f"  Current price: {position.current_price}")
                print(f"  Unrealized PnL: {position.unrealized_pnl}")
                print(f"  Unrealized PnL %: {position.unrealized_pnl_pct:.2%}")
                print(f"  Side: {position.side}")

        print("\nOPEN ORDERS")
        if snapshot.open_orders.empty:
            print("No open orders.")
        else:
            for order in snapshot.open_orders.itertuples(index=False):
                print(f"\n{order.symbol}")
                print(f"  Side: {order.side}")
                print(f"  Quantity: {order.quantity}")
                print(f"  Notional: {order.notional}")
                print(f"  Order type: {order.order_type}")
                print(f"  Status: {order.status}")
                print(f"  Submitted at: {order.submitted_at}")
                print(f"  Filled quantity: {order.filled_quantity}")
                print(f"  Filled average price: {order.filled_average_price}")
