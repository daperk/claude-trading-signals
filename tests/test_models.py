from datetime import datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from claude_trading_signals.models import OHLCV, MarketContext, Signal, SignalDirection


def _candle(close: str = "100") -> OHLCV:
    return OHLCV(
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        open=Decimal("99"),
        high=Decimal("101"),
        low=Decimal("98"),
        close=Decimal(close),
        volume=Decimal("1000"),
    )


class TestOHLCV:
    def test_valid_candle(self):
        c = _candle()
        assert c.high >= c.low

    def test_high_below_low_rejected(self):
        with pytest.raises(ValidationError):
            OHLCV(
                timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
                open=Decimal("99"),
                high=Decimal("90"),
                low=Decimal("98"),
                close=Decimal("100"),
                volume=Decimal("1000"),
            )


class TestMarketContext:
    def test_requires_at_least_one_candle(self):
        with pytest.raises(ValidationError):
            MarketContext(symbol="EURUSD", timeframe="1h", candles=[])

    def test_basic_construction(self):
        ctx = MarketContext(symbol="EURUSD", timeframe="1h", candles=[_candle()])
        assert ctx.symbol == "EURUSD"
        assert ctx.news_context is None


class TestSignal:
    def test_confidence_above_one_rejected(self):
        with pytest.raises(ValidationError):
            Signal(
                symbol="X",
                direction=SignalDirection.LONG,
                confidence=1.5,
                reasoning="r",
                model="m",
            )

    def test_confidence_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            Signal(
                symbol="X",
                direction=SignalDirection.LONG,
                confidence=-0.1,
                reasoning="r",
                model="m",
            )

    def test_minimal_neutral_signal(self):
        s = Signal(
            symbol="X",
            direction=SignalDirection.NEUTRAL,
            confidence=0.0,
            reasoning="mixed signals",
            model="m",
        )
        assert s.entry_price is None
        assert s.stop_loss is None
        assert s.take_profit is None
        assert s.generated_at.tzinfo is timezone.utc
