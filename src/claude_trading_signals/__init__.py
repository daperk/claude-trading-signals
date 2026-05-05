"""claude-trading-signals: structured trading signals via the Anthropic SDK."""
from .client import SignalGenerator
from .models import OHLCV, MarketContext, Signal, SignalDirection
from .validator import SignalValidator, ValidationResult

__all__ = [
    "SignalGenerator",
    "MarketContext",
    "OHLCV",
    "Signal",
    "SignalDirection",
    "SignalValidator",
    "ValidationResult",
]
__version__ = "0.1.0"
