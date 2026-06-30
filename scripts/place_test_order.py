"""Safely simulate or manually send a $10 SPY paper order."""

from __future__ import annotations

import argparse
from decimal import Decimal

from trading_lab.config.settings import Settings
from trading_lab.execution.order_builder import OrderBuilder
from trading_lab.execution.order_manager import OrderManager
from trading_lab.execution.order_reporter import ConsoleOrderReporter
from trading_lab.factories.alpaca_factory import AlpacaClientFactory
from trading_lab.risk.limits import RiskLimits
from trading_lab.risk.risk_checker import RiskChecker
from trading_lab.universe.tradable_universe import TradableUniverse


def parse_args() -> argparse.Namespace:
    """Parse the explicit paper-order submission flag."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--send",
        action="store_true",
        help="Submit after risk checks and an exact SEND confirmation.",
    )
    return parser.parse_args()


def main() -> int:
    """Build, assess, and optionally submit the controlled test order."""
    args = parse_args()
    universe = TradableUniverse()
    limits = RiskLimits()
    risk_checker = RiskChecker(limits=limits, universe=universe)
    order = OrderBuilder(universe).market_buy_notional(
        "SPY",
        Decimal("10"),
        reason="Controlled manual paper-trading test",
    )
    decision = risk_checker.check_order(order)
    ConsoleOrderReporter.print_decision(decision)
    if not decision.approved:
        return 1

    if args.send:
        if not Settings.ALPACA_PAPER:
            print("Blocked: ALPACA_PAPER is false. Live trading is disabled.")
            return 1
        confirmation = input("Type SEND to confirm: ")
        if confirmation != "SEND":
            print("Order cancelled. Nothing was sent.")
            return 0

    try:
        client = AlpacaClientFactory.create_trading_client()
    except ValueError as error:
        print(f"Alpaca client configuration failed: {error}")
        return 1

    manager = OrderManager(
        trading_client=client,
        risk_checker=risk_checker,
        dry_run=not args.send,
    )
    result = manager.submit_order(order)
    ConsoleOrderReporter.print_execution_result(result)
    return 0 if result.dry_run or result.submitted else 1


if __name__ == "__main__":
    raise SystemExit(main())
