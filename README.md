# claude-trading-signals

Generate **structured trading signals** from market data using **Claude** via the Anthropic SDK. Built on tool use for type-safe outputs, prompt caching for cost efficiency, and an explicit validation layer that rejects impossible signals before they reach your strategy.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Disclaimer:** Educational and research use only. Not financial advice. LLM-generated signals are not a substitute for thorough backtesting and risk management.

---

## Why this exists

Asking an LLM "should I buy or sell EURUSD?" returns prose that's hard to parse and easy to act on incorrectly. This library:

- **Forces structured outputs** via Anthropic [tool use](https://docs.claude.com/en/docs/build-with-claude/tool-use) (`submit_signal`) — no JSON parsing of free text, no markdown-fenced surprises
- **Validates direction / price-level consistency** before you trust the signal (e.g. catches a `LONG` with `stop_loss > entry_price`)
- **Caches the system prompt** with `cache_control` for ~10% input cost on repeated calls within the cache TTL
- **Returns typed Pydantic models** — `Signal`, `MarketContext`, `OHLCV` — not dicts and not strings

---

## Install

```bash
pip install git+https://github.com/daperk/claude-trading-signals.git
```

Set your key:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Usage

```python
from datetime import datetime, timezone
from decimal import Decimal
from claude_trading_signals import MarketContext, OHLCV, SignalGenerator

ctx = MarketContext(
    symbol="EURUSD",
    timeframe="1h",
    candles=[
        OHLCV(
            timestamp=datetime(2026, 5, 5, 14, tzinfo=timezone.utc),
            open=Decimal("1.0850"), high=Decimal("1.0870"),
            low=Decimal("1.0845"), close=Decimal("1.0865"),
            volume=Decimal("12500"),
        ),
        # ... more recent candles
    ],
    news_context="ECB held rates; mild risk-on tone in equities.",
)

gen = SignalGenerator()  # picks up ANTHROPIC_API_KEY from env
signal, validation = gen.generate(ctx)

print(signal.direction)     # SignalDirection.LONG
print(signal.confidence)    # 0.72
print(signal.entry_price)   # Decimal('1.0865')
print(signal.reasoning)     # "Higher highs over last 5 candles..."
print(validation.is_valid)  # True
```

`generate()` returns a `(Signal, ValidationResult)` tuple. Validation never raises — the caller decides whether to act on signals that fail consistency checks.

A runnable demo with synthetic candles is in [`examples/basic.py`](examples/basic.py).

---

## What's in a Signal

```python
class Signal(BaseModel):
    symbol: str
    direction: SignalDirection      # "long" | "short" | "neutral"
    confidence: float               # 0.0 to 1.0
    entry_price: Decimal | None
    stop_loss: Decimal | None
    take_profit: Decimal | None
    reasoning: str
    generated_at: datetime
    model: str
```

`Decimal` everywhere on prices — no float drift.

---

## Validation rules

The default `SignalValidator` rejects signals where:

- Direction is `LONG` but `stop_loss >= entry_price` or `take_profit <= entry_price`
- Direction is `SHORT` but `stop_loss <= entry_price` or `take_profit >= entry_price`
- Direction is `NEUTRAL` but any price level is set
- The signal's symbol does not match the context's symbol
- Reasoning is empty or whitespace

Override `SignalValidator.validate` for custom rules — minimum risk:reward, max confidence given recent volatility, etc.:

```python
from claude_trading_signals import SignalValidator, ValidationResult

class StrictValidator(SignalValidator):
    def validate(self, signal, context):
        result = super().validate(signal, context)
        if signal.confidence > 0.9:
            return ValidationResult(
                False,
                result.errors + ("confidence > 0.9 likely overconfident",),
            )
        return result

gen = SignalGenerator(validator=StrictValidator())
```

---

## How structured output works

Under the hood, `generate()` defines a `submit_signal` tool with a JSON schema and forces Claude to invoke it via `tool_choice={"type": "tool", "name": "submit_signal"}`. Claude returns a `tool_use` block whose `input` field already conforms to the schema — no regex parsing, no "did the model wrap JSON in markdown" headaches.

The system prompt is sent with `cache_control: {"type": "ephemeral"}`, so repeated calls within the 5-minute cache TTL pay ~10% of the input cost on the cached portion.

---

## Model selection

Defaults to `claude-sonnet-4-6` for a balance of cost and reasoning quality:

```python
gen = SignalGenerator(model="claude-opus-4-7")              # best reasoning
gen = SignalGenerator(model="claude-haiku-4-5-20251001")    # fastest, cheapest
```

---

## Development

```bash
git clone https://github.com/daperk/claude-trading-signals.git
cd claude-trading-signals
pip install -e ".[dev]"
pytest
```

---

## License

MIT — see [LICENSE](LICENSE).
