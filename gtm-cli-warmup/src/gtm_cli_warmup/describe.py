"""Company description via Anthropic tool use.

The model returns structured data by calling a tool whose input schema is
derived from the Pydantic model — no string parsing, no JSON-in-prose.
"""

from __future__ import annotations

from typing import Any

import anthropic

from .cost import CallRecord, CostTracker, timed
from .models import CompanyDescription

MODEL = "claude-sonnet-5"
MAX_TOKENS = 1024

SYSTEM = (
    "You are a GTM research assistant. Given a company name, return a concise, "
    "factual structured description. The one_liner must be exactly three "
    "sentences. If you are unsure of a value, give your best estimate rather "
    "than refusing — size_guess is explicitly a guess."
)


def _tool_schema() -> dict[str, Any]:
    """Anthropic tool definition derived from the Pydantic model."""
    schema = CompanyDescription.model_json_schema()
    schema["additionalProperties"] = False
    return {
        "name": "record_company_description",
        "description": (
            "Record a structured description of the company. Call this exactly "
            "once with your final answer."
        ),
        "strict": True,
        "input_schema": schema,
    }


class DescribeError(RuntimeError):
    """The model did not return a usable tool call."""


def describe_company(
    company: str,
    tracker: CostTracker,
    client: anthropic.Anthropic | None = None,
) -> tuple[CompanyDescription, CallRecord]:
    """Describe `company`, recording tokens/cost/latency on `tracker`."""
    client = client or anthropic.Anthropic()
    tool = _tool_schema()

    with timed() as t:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            # This is a cheap, well-specified extraction — thinking would add
            # latency and tokens without improving the answer.
            thinking={"type": "disabled"},
            system=SYSTEM,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"]},
            messages=[{"role": "user", "content": f"Describe: {company}"}],
        )

    record = tracker.record(response, model=MODEL, latency_ms=t["ms"], company=company)

    if response.stop_reason == "refusal":
        raise DescribeError(f"Model refused the request for {company!r}.")

    for block in response.content:
        if block.type == "tool_use" and block.name == tool["name"]:
            return CompanyDescription.model_validate(block.input), record

    raise DescribeError(
        f"No tool call in response (stop_reason={response.stop_reason!r}). "
        "If this is 'max_tokens', raise MAX_TOKENS."
    )
