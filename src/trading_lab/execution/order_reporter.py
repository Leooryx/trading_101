"""Readable console output for order decisions and execution results."""

from trading_lab.execution.models import OrderDecision, OrderExecutionResult


class ConsoleOrderReporter:
    """Print proposed orders, risk decisions, and submission outcomes."""

    @staticmethod
    def print_decision(decision: OrderDecision) -> None:
        """Print an approved or rejected risk decision."""
        order = decision.proposed_order
        amount = (
            f"${order.notional}"
            if order.notional is not None
            else f"quantity {order.quantity}"
        )
        print(
            f"Proposed order: {order.side.upper()} {order.symbol} "
            f"{amount} type={order.order_type}"
        )
        print("Risk decision: APPROVED" if decision.approved else "Risk decision: REJECTED")
        for reason in decision.reasons:
            print(f"  - {reason}")

    @staticmethod
    def print_execution_result(result: OrderExecutionResult) -> None:
        """Print whether an order was simulated, blocked, or submitted."""
        print(f"Execution status: {result.status}")
        print(f"Dry run: {'yes' if result.dry_run else 'no'}")
        print(f"Submitted: {'yes' if result.submitted else 'no'}")
        if result.alpaca_order_id:
            print(f"Alpaca order id: {result.alpaca_order_id}")
        print(result.message)
