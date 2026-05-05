"""Sanity checks on generated signals."""
from __future__ import annotations

from dataclasses import dataclass, field

from .models import MarketContext, Signal, SignalDirection


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    errors: tuple[str, ...] = field(default_factory=tuple)


class SignalValidator:
    """Default validator. Subclass and override `validate` for custom rules."""

    def validate(self, signal: Signal, context: MarketContext) -> ValidationResult:
        errors: list[str] = []

        if signal.symbol != context.symbol:
            errors.append(
                f"signal.symbol ({signal.symbol}) does not match context.symbol ({context.symbol})"
            )

        if signal.direction == SignalDirection.NEUTRAL:
            if any(x is not None for x in (signal.entry_price, signal.stop_loss, signal.take_profit)):
                errors.append("neutral signals must have null entry_price, stop_loss, and take_profit")
        else:
            errors.extend(self._check_price_levels(signal))

        if not signal.reasoning.strip():
            errors.append("reasoning is empty")

        return ValidationResult(is_valid=not errors, errors=tuple(errors))

    @staticmethod
    def _check_price_levels(signal: Signal) -> list[str]:
        errors: list[str] = []
        entry, sl, tp = signal.entry_price, signal.stop_loss, signal.take_profit

        if signal.direction == SignalDirection.LONG:
            if entry is not None and sl is not None and not sl < entry:
                errors.append(f"long: stop_loss ({sl}) must be < entry_price ({entry})")
            if entry is not None and tp is not None and not tp > entry:
                errors.append(f"long: take_profit ({tp}) must be > entry_price ({entry})")
        elif signal.direction == SignalDirection.SHORT:
            if entry is not None and sl is not None and not sl > entry:
                errors.append(f"short: stop_loss ({sl}) must be > entry_price ({entry})")
            if entry is not None and tp is not None and not tp < entry:
                errors.append(f"short: take_profit ({tp}) must be < entry_price ({entry})")
        return errors
