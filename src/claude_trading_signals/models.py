"""Pydantic models for trading signals and market context."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class SignalDirection(str, Enum):
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


class OHLCV(BaseModel):
    """A single OHLCV candle."""

    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    @model_validator(mode="after")
    def _check_high_low(self) -> OHLCV:
        if self.high < self.low:
            raise ValueError(f"high ({self.high}) must be >= low ({self.low})")
        return self


class MarketContext(BaseModel):
    """Inputs to the signal generator."""

    symbol: str = Field(..., description="Trading symbol, e.g. 'EURUSD' or 'BTC/USD'.")
    timeframe: str = Field(..., description="Candle timeframe, e.g. '1h', '4h', '1d'.")
    candles: list[OHLCV] = Field(..., min_length=1, description="Recent OHLCV candles, oldest first.")
    news_context: str | None = Field(None, description="Optional recent news / events summary.")
    additional_context: dict | None = Field(None, description="Free-form extra context.")


class Signal(BaseModel):
    """A structured trading signal returned by the model."""

    symbol: str
    direction: SignalDirection
    confidence: float = Field(..., ge=0.0, le=1.0)
    entry_price: Decimal | None = None
    stop_loss: Decimal | None = None
    take_profit: Decimal | None = None
    reasoning: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model: str
