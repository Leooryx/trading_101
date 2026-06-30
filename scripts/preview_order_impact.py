"""Preview an order's account and risk impact without sending it."""

from __future__ import annotations

import argparse
from decimal import Decimal

from trading_lab.execution.models import ProposedOrder
from trading_lab.execution.order_builder import OrderBuilder
from trading_lab.factories.alpaca_factory import AlpacaClientFactory
from trading_lab.loaders.account_loader import AccountLoader
from trading_lab.loaders.order_loader import OrderLoader
from trading_lab.loaders.position_loader import PositionLoader
from trading_lab.market_data.quote_loader import MarketQuoteLoader
from trading_lab.pretrade.pretrade_impact_service import PreTradeImpactService
from trading_lab.pretrade.pretrade_reporter import ConsolePreTradeReporter
from trading_lab.risk.exposure_calculator import ExposureCalculator
from trading_lab.risk.limits import RiskLimits
from trading_lab.risk.risk_checker import RiskChecker
from trading_lab.services.portfolio_service import PortfolioService
from trading_lab.universe.tradable_universe import TradableUniverse


def parse_args() -> argparse.Namespace:
    """Parse one provider-neutral proposed order from the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", default="SPY")
    parser.add_argument("--side", choices=["buy", "sell"], default="buy")
    parser.add_argument("--notional", type=Decimal)
    parser.add_argument("--quantity", type=Decimal)
    parser.add_argument("--order-type", choices=["market", "limit"], default="market")
    parser.add_argument("--limit-price", type=Decimal)
    parser.add_argument("--reason")
    return parser.parse_args()


def build_order(args: argparse.Namespace, builder: OrderBuilder) -> ProposedOrder:
    """Build the CLI proposal through the existing OrderBuilder."""
    if args.notional is not None and args.quantity is not None:
        raise ValueError("Provide either --notional or --quantity, not both.")
    if args.notional is None and args.quantity is None:
        args.notional = Decimal("1000")

    if args.order_type == "limit":
        if args.quantity is None:
            raise ValueError("Limit previews require --quantity.")
        if args.limit_price is None:
            raise ValueError("Limit previews require --limit-price.")
        method = (
            builder.limit_buy_quantity
            if args.side == "buy"
            else builder.limit_sell_quantity
        )
        return method(args.symbol, args.quantity, args.limit_price, args.reason)

    if args.notional is not None:
        method = (
            builder.market_buy_notional
            if args.side == "buy"
            else builder.market_sell_notional
        )
        return method(args.symbol, args.notional, args.reason)

    method = (
        builder.market_buy_quantity
        if args.side == "buy"
        else builder.market_sell_quantity
    )
    return method(args.symbol, args.quantity, args.reason)


def main() -> int:
    """Load current state and print a read-only order impact preview."""
    args = parse_args()
    universe = TradableUniverse()
    try:
        order = build_order(args, OrderBuilder(universe))
        client = AlpacaClientFactory.create_trading_client()
        portfolio_service = PortfolioService(
            account_loader=AccountLoader(client),
            position_loader=PositionLoader(client),
            order_loader=OrderLoader(client),
        )
        preview_service = PreTradeImpactService(
            portfolio_service=portfolio_service,
            quote_loader=MarketQuoteLoader(universe=universe),
            risk_checker=RiskChecker(RiskLimits(), universe),
            exposure_calculator=ExposureCalculator(),
        )
        report = preview_service.preview_order(order)
    except Exception as error:
        print(f"Preview could not start: {error}")
        return 1

    ConsolePreTradeReporter.print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
