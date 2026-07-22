"""Per-model token pricing.

Rates are USD per million tokens. Some models carry a promotional rate that
expires on a given date; `rates_for` picks the right one so the cost numbers in
`runs.jsonl` stay honest as promos lapse.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Rates:
    """USD per million tokens."""

    input: float
    output: float
    cache_write: float
    cache_read: float

    @classmethod
    def from_base(cls, input_: float, output: float) -> "Rates":
        # Cache writes cost 1.25x base input; cache reads cost 0.1x.
        return cls(
            input=input_,
            output=output,
            cache_write=input_ * 1.25,
            cache_read=input_ * 0.10,
        )


@dataclass(frozen=True)
class ModelPricing:
    standard: Rates
    intro: Rates | None = None
    intro_until: date | None = None


PRICING: dict[str, ModelPricing] = {
    "claude-sonnet-5": ModelPricing(
        standard=Rates.from_base(3.00, 15.00),
        intro=Rates.from_base(2.00, 10.00),
        intro_until=date(2026, 8, 31),
    ),
    "claude-haiku-4-5": ModelPricing(standard=Rates.from_base(1.00, 5.00)),
    "claude-opus-4-8": ModelPricing(standard=Rates.from_base(5.00, 25.00)),
}


def rates_for(model: str, on: date | None = None) -> Rates:
    """Return the rates in effect for `model` on `on` (default: today)."""
    try:
        pricing = PRICING[model]
    except KeyError:
        raise KeyError(
            f"No pricing for {model!r}. Add it to PRICING before using it, "
            "otherwise cost logging silently reports $0."
        ) from None

    on = on or date.today()
    if pricing.intro and pricing.intro_until and on <= pricing.intro_until:
        return pricing.intro
    return pricing.standard


def cost_usd(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_creation_tokens: int = 0,
    cache_read_tokens: int = 0,
    on: date | None = None,
) -> float:
    """Dollar cost of a single call.

    `input_tokens` is the uncached remainder only — cached tokens are billed
    separately at the write/read rates.
    """
    r = rates_for(model, on)
    per_token = 1_000_000
    return (
        input_tokens * r.input
        + output_tokens * r.output
        + cache_creation_tokens * r.cache_write
        + cache_read_tokens * r.cache_read
    ) / per_token
