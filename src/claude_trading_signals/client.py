"""Signal generator backed by the Anthropic SDK."""
from __future__ import annotations

import os
from decimal import Decimal
from typing import Any

from anthropic import Anthropic

from .models import OHLCV, MarketContext, Signal, SignalDirection
from .prompts import SYSTEM_PROMPT, build_user_message
from .validator import SignalValidator, ValidationResult

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_MAX_TOKENS = 1024


SUBMIT_SIGNAL_TOOL: dict[str, Any] = {
    "name": "submit_signal",
    "description": "Submit a structured trading signal for the given instrument.",
    "input_schema": {
        "type": "object",
        "properties": {
            "direction": {
                "type": "string",
                "enum": ["long", "short", "neutral"],
                "description": "Trade direction.",
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Conviction in [0, 1].",
            },
            "entry_price": {
                "type": ["number", "null"],
                "description": "Suggested entry price. Null for neutral signals.",
            },
            "stop_loss": {
                "type": ["number", "null"],
                "description": "Stop loss price. Null for neutral signals.",
            },
            "take_profit": {
                "type": ["number", "null"],
                "description": "Take profit price. Null for neutral signals.",
            },
            "reasoning": {
                "type": "string",
                "description": "Concise reasoning citing specific evidence from candles or news.",
            },
        },
        "required": ["direction", "confidence", "reasoning"],
    },
}


class SignalGenerator:
    """Generate structured trading signals from market context using Claude.

    The system prompt is sent with `cache_control` enabled, so repeated calls
    within the cache TTL pay a fraction of the input cost on the cached portion.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_MODEL,
        validator: SignalValidator | None = None,
    ) -> None:
        self.client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = model
        self.validator = validator or SignalValidator()

    def generate(
        self,
        context: MarketContext,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> tuple[Signal, ValidationResult]:
        """Generate a structured signal for the given market context.

        Returns a `(Signal, ValidationResult)` tuple. Validation never raises
        — the caller decides whether to act on signals that fail consistency
        checks.
        """
        user_text = build_user_message(
            symbol=context.symbol,
            timeframe=context.timeframe,
            candles_summary=_format_candles(context.candles),
            news_context=context.news_context,
            additional_context=str(context.additional_context) if context.additional_context else None,
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            tools=[SUBMIT_SIGNAL_TOOL],
            tool_choice={"type": "tool", "name": "submit_signal"},
            messages=[{"role": "user", "content": user_text}],
        )

        signal = _parse_tool_response(response, context.symbol, self.model)
        validation = self.validator.validate(signal, context)
        return signal, validation


def _format_candles(candles: list[OHLCV]) -> str:
    rows = ["timestamp,open,high,low,close,volume"]
    for c in candles:
        rows.append(f"{c.timestamp.isoformat()},{c.open},{c.high},{c.low},{c.close},{c.volume}")
    return "\n".join(rows)


def _parse_tool_response(response: Any, symbol: str, model: str) -> Signal:
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "submit_signal":
            args = block.input
            return Signal(
                symbol=symbol,
                direction=SignalDirection(args["direction"]),
                confidence=float(args["confidence"]),
                entry_price=_to_decimal(args.get("entry_price")),
                stop_loss=_to_decimal(args.get("stop_loss")),
                take_profit=_to_decimal(args.get("take_profit")),
                reasoning=args["reasoning"],
                model=model,
            )
    raise RuntimeError("Model response did not contain a submit_signal tool call")


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))
