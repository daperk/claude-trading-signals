"""Minimal example: generate a signal for EURUSD using synthetic candles.

Set ANTHROPIC_API_KEY in your environment, then run:
    python examples/basic.py
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from claude_trading_signals import OHLCV, MarketContext, SignalGenerator


def make_demo_candles() -> list[OHLCV]:
    now = datetime.now(timezone.utc)
    base = Decimal("1.0850")
    candles: list[OHLCV] = []
    for i in range(10):
        drift = Decimal(str(0.0005 * i))
        candles.append(
            OHLCV(
                timestamp=now - timedelta(hours=10 - i),
                open=base + drift,
                high=base + drift + Decimal("0.0010"),
                low=base + drift - Decimal("0.0008"),
                close=base + drift + Decimal("0.0003"),
                volume=Decimal("1000"),
            )
        )
    return candles


def main() -> None:
    context = MarketContext(
        symbol="EURUSD",
        timeframe="1h",
        candles=make_demo_candles(),
        news_context="ECB held rates; mild risk-on tone in equities.",
    )

    gen = SignalGenerator()
    signal, validation = gen.generate(context)

    print(f"Direction:    {signal.direction.value}")
    print(f"Confidence:   {signal.confidence:.2f}")
    print(f"Entry:        {signal.entry_price}")
    print(f"Stop loss:    {signal.stop_loss}")
    print(f"Take profit:  {signal.take_profit}")
    print(f"Reasoning:    {signal.reasoning}")
    print(f"Model:        {signal.model}")
    print(f"\nValidation:   {'PASSED' if validation.is_valid else 'FAILED'}")
    for err in validation.errors:
        print(f"  - {err}")


if __name__ == "__main__":
    main()
