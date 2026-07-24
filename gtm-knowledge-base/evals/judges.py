"""LLM-judge metrics for answer quality: faithfulness and completeness.

Both judges require a real model. When no key is present they return
`available=False` and the report prints "not measured" rather than a number —
an unmeasured metric must never be rendered as a score.

`lexical_trait_coverage` is a separate, deterministic signal that runs offline.
It is NOT the completeness judge and is labelled distinctly everywhere it appears:
it only asks whether each expected trait string occurs literally in the answer,
which under-counts correct paraphrases.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Any, Optional

JUDGE_MODEL = "claude-3-5-sonnet-20241022"


@dataclass(frozen=True)
class JudgeResult:
    available: bool
    score: float = 0.0        # 0.0-1.0
    reasoning: str = ""
    input_tokens: int = 0
    output_tokens: int = 0

    def as_dict(self) -> dict:
        if not self.available:
            return {"available": False}
        return {
            "available": True,
            "score": round(self.score, 4),
            "reasoning": self.reasoning[:300],
        }


def judge_available(client: Optional[Any] = None) -> bool:
    return client is not None or bool(os.getenv("ANTHROPIC_API_KEY"))


def _get_client(client: Optional[Any]):
    if client is not None:
        return client
    if not os.getenv("ANTHROPIC_API_KEY"):
        return None
    from anthropic import Anthropic

    return Anthropic()


def _ask_judge(client, system: str, user: str) -> Optional[dict]:
    """Run a judge turn and parse its JSON verdict. None if unusable."""
    response = client.messages.create(
        model=JUDGE_MODEL,
        max_tokens=400,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    blocks = [b.text for b in response.content if getattr(b, "type", None) == "text"]
    if not blocks:
        return None

    raw = "\n".join(blocks).strip()
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
        except (json.JSONDecodeError, ValueError):
            return None

    if not isinstance(parsed, dict):
        return None
    parsed["_usage"] = (response.usage.input_tokens, response.usage.output_tokens)
    return parsed


FAITHFULNESS_SYSTEM = """You audit whether an answer is grounded in its sources.

Read the answer and the source passages it was given. Identify every factual claim
in the answer, then decide whether each is supported by the passages.

Reply with ONLY this JSON:
{"supported": <int>, "total": <int>, "unsupported_claims": ["..."], "reasoning": "<one sentence>"}

A claim is unsupported if the passages do not state it, even if it is true in general.
Hedges, restatements of the question, and refusals are not claims. Output no prose."""


COMPLETENESS_SYSTEM = """You check whether an answer covers a set of required points.

You are given an answer and a list of traits it should contain. A trait counts as
covered if the answer conveys it in any wording — an exact string match is not required.

Reply with ONLY this JSON:
{"covered": <int>, "total": <int>, "missing": ["..."], "reasoning": "<one sentence>"}

Output no prose."""


def judge_faithfulness(
    answer: str, source_texts: list[str], client: Optional[Any] = None
) -> JudgeResult:
    """Fraction of the answer's factual claims that the sources support."""
    c = _get_client(client)
    if c is None:
        return JudgeResult(available=False)

    sources = "\n\n".join(
        f"<passage {i}>\n{t}\n</passage {i}>" for i, t in enumerate(source_texts, 1)
    )
    verdict = _ask_judge(
        c, FAITHFULNESS_SYSTEM, f"<sources>\n{sources}\n</sources>\n\n<answer>\n{answer}\n</answer>"
    )
    if not verdict:
        return JudgeResult(available=False)

    total = verdict.get("total", 0)
    supported = verdict.get("supported", 0)
    if not isinstance(total, int) or not isinstance(supported, int) or total <= 0:
        # No checkable claims (e.g. an honest refusal) — scoring it would be noise.
        return JudgeResult(available=False, reasoning="no factual claims to audit")

    tokens = verdict.get("_usage", (0, 0))
    return JudgeResult(
        available=True,
        score=max(0.0, min(1.0, supported / total)),
        reasoning=str(verdict.get("reasoning", "")),
        input_tokens=tokens[0],
        output_tokens=tokens[1],
    )


def judge_completeness(
    answer: str, expected_traits: list[str], client: Optional[Any] = None
) -> JudgeResult:
    """Fraction of the expected traits the answer conveys, in any wording."""
    if not expected_traits:
        return JudgeResult(available=False, reasoning="no traits specified")

    c = _get_client(client)
    if c is None:
        return JudgeResult(available=False)

    traits = "\n".join(f"- {t}" for t in expected_traits)
    verdict = _ask_judge(
        c, COMPLETENESS_SYSTEM, f"<required_traits>\n{traits}\n</required_traits>\n\n<answer>\n{answer}\n</answer>"
    )
    if not verdict:
        return JudgeResult(available=False)

    total = verdict.get("total", 0)
    covered = verdict.get("covered", 0)
    if not isinstance(total, int) or not isinstance(covered, int) or total <= 0:
        return JudgeResult(available=False)

    tokens = verdict.get("_usage", (0, 0))
    return JudgeResult(
        available=True,
        score=max(0.0, min(1.0, covered / total)),
        reasoning=str(verdict.get("reasoning", "")),
        input_tokens=tokens[0],
        output_tokens=tokens[1],
    )


def lexical_trait_coverage(answer: str, expected_traits: list[str]) -> float:
    """Deterministic offline proxy: fraction of traits appearing literally in the answer.

    NOT the completeness judge. Case-insensitive substring matching under-counts
    valid paraphrases, so treat this as a floor on coverage, never as the metric.
    """
    if not expected_traits:
        return 0.0
    hay = " ".join(answer.split()).casefold()
    hits = sum(1 for t in expected_traits if " ".join(t.split()).casefold() in hay)
    return hits / len(expected_traits)
