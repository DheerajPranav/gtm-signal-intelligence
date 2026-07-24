"""Reranker: Claude Haiku reorders retrieval candidates by relevance to the question.

The model sees a truncated pool (RERANK_POOL) and returns 1-based indices into it.
Every assumption about that response is checked — the model can return duplicates,
out-of-range indices, non-integers, or prose instead of JSON, and none of those may
corrupt the ranking or crash the pipeline.
"""

from __future__ import annotations

import json
import re
import time
from typing import Any, Optional

from .models import RankedChunk
from .query import Result

DEFAULT_RERANK_MODEL = "claude-3-5-haiku-20241022"
RERANK_POOL = 20  # candidates shown to the model
SNIPPET_CHARS = 400

SYSTEM_PROMPT = """You rank passages by how well they answer a question.

Reply with ONLY a JSON array of 1-based candidate indices, most relevant first, e.g. [3,1,7].
Omit candidates that do not help answer the question. Never invent an index. Output no prose."""


def _snippet(text: str) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= SNIPPET_CHARS else flat[:SNIPPET_CHARS] + "…"


def _parse_ranking(raw: str, pool_size: int) -> list[int]:
    """Extract a clean, deduplicated, in-range list of 1-based indices.

    Tolerates the model wrapping JSON in prose or code fences. Returns [] when
    nothing usable is found, letting the caller fall back to retrieval order.
    """
    candidates: list[Any] = []

    try:
        candidates = json.loads(raw.strip())
    except (json.JSONDecodeError, ValueError):
        # Salvage the first bracketed run of digits, e.g. "Here you go: [2, 5, 1]".
        match = re.search(r"\[[\s\d,]*\]", raw)
        if match:
            try:
                candidates = json.loads(match.group(0))
            except (json.JSONDecodeError, ValueError):
                candidates = []

    if not isinstance(candidates, list):
        return []

    cleaned: list[int] = []
    seen: set[int] = set()
    for item in candidates:
        # Reject bools explicitly: bool is a subclass of int in Python.
        if isinstance(item, bool) or not isinstance(item, int):
            continue
        if not (1 <= item <= pool_size) or item in seen:
            continue
        seen.add(item)
        cleaned.append(item)

    return cleaned


def rerank(
    question: str,
    candidates: list[Result],
    top_k: int = 5,
    model: str = DEFAULT_RERANK_MODEL,
    client: Optional[Any] = None,
) -> tuple[list[RankedChunk], dict]:
    """Rerank retrieval candidates with a cheap model.

    Args:
        question: The question to rank against.
        candidates: Hybrid-retrieval results.
        top_k: How many chunks to return.
        model: Claude model to use.
        client: Injected Anthropic client. Defaults to a real one — tests pass a fake.

    Returns:
        (reranked chunks, usage dict). Usage carries `fell_back=True` when the
        model's response was unusable and retrieval order was kept instead.
    """
    if not candidates:
        return [], {
            "reranker_model": model,
            "input_tokens": 0,
            "output_tokens": 0,
            "latency_ms": 0.0,
            "fell_back": False,
        }

    # The model only ever sees this slice, so indices must be validated against it —
    # not against the full candidate list, or we'd accept an index for a chunk the
    # model never saw and silently promote an unranked result.
    pool = candidates[:RERANK_POOL]

    if client is None:
        from anthropic import Anthropic

        client = Anthropic()

    candidate_text = "\n\n".join(
        f"[{i}] {c.metadata.get('doc_title')} › {c.metadata.get('section_title')}\n"
        f"{_snippet(c.text)}"
        for i, c in enumerate(pool, 1)
    )
    user_content = f"Question: {question}\n\nCandidates:\n{candidate_text}"

    start = time.time()
    response = client.messages.create(
        model=model,
        max_tokens=200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    latency_ms = (time.time() - start) * 1000

    text_blocks = [b.text for b in response.content if getattr(b, "type", None) == "text"]
    ranking = _parse_ranking("\n".join(text_blocks), len(pool)) if text_blocks else []

    fell_back = not ranking
    if fell_back:
        # Keep retrieval order rather than dropping results entirely.
        ranking = list(range(1, len(pool) + 1))

    selected = ranking[:top_k]
    denominator = max(len(selected), 1)

    reranked = [
        RankedChunk(
            chunk_id=pool[idx - 1].chunk_id,
            text=pool[idx - 1].text,
            metadata=pool[idx - 1].metadata,
            original_score=pool[idx - 1].score,
            # Linear decay across however many were selected, so scores stay
            # distinct for any top_k instead of saturating at 0 past rank 5.
            rerank_score=round(1.0 - (position / denominator), 6),
        )
        for position, idx in enumerate(selected)
    ]

    return reranked, {
        "reranker_model": model,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "latency_ms": latency_ms,
        "fell_back": fell_back,
    }
