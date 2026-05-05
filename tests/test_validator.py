from datetime import datetime, timezone
from decimal import Decimal

from claude_trading_signals.models import OHLCV, MarketContext, Signal, SignalDirection
from claude_trading_signals.validator import SignalValidator


def _ctx(symbol: str = "EURUSD") -> MarketContext:
    return MarketContext(
        symbol=symbol,
        timeframe="1h",
        candles=[
            OHLCV(
                timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
                open=Decimal("1.10"),
                high=Decimal("1.12"),
                low=Decimal("1.09"),
                close=Decimal("1.11"),
                volume=Decimal("100"),
            )
        ],
    )


class TestSignalValidator:
    def setup_method(self):
        self.v = SignalValidator()

    def test_valid_long(self):
        s = Signal(
            symbol="EURUSD",
            direction=SignalDirection.LONG,
            confidence=0.7,
            entry_price=Decimal("1.10"),
            stop_loss=Decimal("1.08"),
            take_profit=Decimal("1.15"),
            reasoning="bullish breakout above prior high",
            model="claude",
        )
        assert self.v.validate(s, _ctx()).is_valid

    def test_valid_short(self):
        s = Signal(
            symbol="EURUSD",
            direction=SignalDirection.SHORT,
            confidence=0.6,
            entry_price=Decimal("1.10"),
            stop_loss=Decimal("1.12"),
            take_profit=Decimal("1.05"),
            reasoning="rejection at resistance",
            model="claude",
        )
        assert self.v.validate(s, _ctx()).is_valid

    def test_long_with_inverted_stop_loss(self):
        s = Signal(
            symbol="EURUSD",
            direction=SignalDirection.LONG,
            confidence=0.7,
            entry_price=Decimal("1.10"),
            stop_loss=Decimal("1.12"),
            take_profit=Decimal("1.15"),
            reasoning="bullish",
            model="claude",
        )
        result = self.v.validate(s, _ctx())
        assert not result.is_valid
        assert any("stop_loss" in e for e in result.errors)

    def test_long_with_inverted_take_profit(self):
        s = Signal(
            symbol="EURUSD",
            direction=SignalDirection.LONG,
            confidence=0.7,
            entry_price=Decimal("1.10"),
            stop_loss=Decimal("1.08"),
            take_profit=Decimal("1.05"),
            reasoning="bullish",
            model="claude",
        )
        result = self.v.validate(s, _ctx())
        assert not result.is_valid
        assert any("take_profit" in e for e in result.errors)

    def test_neutral_with_levels_set_is_invalid(self):
        s = Signal(
            symbol="EURUSD",
            direction=SignalDirection.NEUTRAL,
            confidence=0.2,
            entry_price=Decimal("1.10"),
            reasoning="mixed",
            model="claude",
        )
        assert not self.v.validate(s, _ctx()).is_valid

    def test_symbol_mismatch(self):
        s = Signal(
            symbol="GBPUSD",
            direction=SignalDirection.NEUTRAL,
            confidence=0.0,
            reasoning="mixed",
            model="claude",
        )
        assert not self.v.validate(s, _ctx("EURUSD")).is_valid

    def test_empty_reasoning(self):
        s = Signal(
            symbol="EURUSD",
            direction=SignalDirection.NEUTRAL,
            confidence=0.0,
            reasoning="   ",
            model="claude",
        )
        assert not self.v.validate(s, _ctx()).is_valid
