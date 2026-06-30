"""Console reporting for pre-trade what-if impact reports."""

from decimal import Decimal

from trading_lab.pretrade.models import PreTradeImpactReport
from trading_lab.risk.greek_exposure import BookGreekExposure


class ConsolePreTradeReporter:
    """Print a readable before/after account and risk comparison."""

    @classmethod
    def print_report(cls, report: PreTradeImpactReport) -> None:
        """Print the complete pre-trade impact report."""
        order = report.proposed_order
        quote = report.quote
        print("=== PRE-TRADE IMPACT ===")

        print("\nA. Proposed order")
        print(f"Symbol: {order.symbol}")
        print(f"Side: {order.side.upper()}")
        print(f"Notional: {cls._value(order.notional)}")
        print(f"Quantity: {cls._value(order.quantity)}")
        print(f"Order type: {order.order_type}")
        print(f"Reason: {order.reason or '-'}")

        print("\nB. Market quote")
        print(f"Source: {quote.source}")
        print(f"Bid: {cls._value(quote.bid_price)}")
        print(f"Ask: {cls._value(quote.ask_price)}")
        print(f"Mid: {cls._value(quote.mid_price)}")
        print(f"Last: {cls._value(quote.last_price)}")
        print(f"Timestamp: {quote.timestamp or '-'}")
        print(f"Estimated fill price: {cls._value(report.estimated_fill_price)}")

        print("\nC. Estimated execution")
        print(f"Estimated quantity: {cls._value(report.estimated_quantity)}")
        print(f"Estimated notional: {cls._value(report.estimated_notional)}")

        print("\nD. Account impact")
        cls._before_after("Cash", report.cash_before, report.cash_after)
        cls._before_after(
            "Portfolio value",
            report.portfolio_value_before,
            report.portfolio_value_after,
        )

        print("\nE. Book exposure before -> after")
        cls._book_comparison(
            report.current_book_exposure,
            report.post_trade_book_exposure,
        )

        print("\nF. Exposure by asset class")
        cls._breakdown(
            report.current_book_exposure.by_asset_class,
            report.post_trade_book_exposure.by_asset_class,
        )

        print("\nG. Exposure by underlying")
        cls._breakdown(
            report.current_book_exposure.by_underlying,
            report.post_trade_book_exposure.by_underlying,
        )

        print("\nH. Risk decision")
        print("APPROVED" if report.risk_approved else "REJECTED")
        for reason in report.risk_reasons:
            print(f"  - {reason}")

        print("\nI. Warnings")
        if report.warnings:
            for warning in report.warnings:
                print(f"  - {warning}")
        else:
            print("None.")

    @classmethod
    def _book_comparison(
        cls,
        before: BookGreekExposure,
        after: BookGreekExposure,
    ) -> None:
        fields = [
            ("Total notional", "total_notional"),
            ("Delta notional", "total_delta_notional"),
            ("Gamma notional", "total_gamma_notional"),
            ("Vega notional", "total_vega_notional"),
            ("Theta notional", "total_theta_notional"),
            ("Delta PnL for +1% move", "total_delta_pnl_1pct_move"),
            ("Gamma PnL for +1% move", "total_gamma_pnl_1pct_move"),
            ("Vega PnL for +1 vol point", "total_vega_pnl_1vol_point"),
            ("Theta PnL for 1 day", "total_theta_pnl_1day"),
        ]
        for label, field in fields:
            cls._before_after(label, getattr(before, field), getattr(after, field))

    @classmethod
    def _breakdown(
        cls,
        before: dict[str, dict[str, Decimal]],
        after: dict[str, dict[str, Decimal]],
    ) -> None:
        keys = sorted(set(before) | set(after))
        if not keys:
            print("None.")
            return
        metrics = [
            "notional",
            "delta_notional",
            "gamma_notional",
            "vega_notional",
            "theta_notional",
        ]
        for key in keys:
            print(f"  {key}:")
            for metric in metrics:
                old = before.get(key, {}).get(metric, Decimal("0"))
                new = after.get(key, {}).get(metric, Decimal("0"))
                print(
                    f"    {metric}: {cls._value(old)} -> {cls._value(new)}"
                )

    @staticmethod
    def _before_after(
        label: str,
        before: Decimal | None,
        after: Decimal | None,
    ) -> None:
        print(
            f"{label}: {ConsolePreTradeReporter._value(before)} -> "
            f"{ConsolePreTradeReporter._value(after)}"
        )

    @staticmethod
    def _value(value: Decimal | None) -> str:
        if value is None:
            return "-"
        return f"{value:.8f}".rstrip("0").rstrip(".")
