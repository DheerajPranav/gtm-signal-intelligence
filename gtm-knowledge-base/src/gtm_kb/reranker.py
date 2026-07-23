"""Reranker: use Claude Haiku to rerank top candidates based on question relevance."""

from __future__ import annotations

import json
import time
from pathlib import Path

from anthropic import Anthropic

from .models import RankedChunk
from .query import Result


def rerank(
    question: str,
    candidates: list[Result],
    top_k: int = 5,
    model: str = "claude-3-5-haiku-20241022",
) -> tuple[list[RankedChunk], dict]:
    """Rerank candidates using Claude Haiku. Returns ranked chunks and usage stats.

    Args:
        question: The original question to rank for.
        candidates: List of Result objects from hybrid retrieval.
        top_k: Number of top results to return after reranking.
        model: Claude model to use for reranking.

    Returns:
        Tuple of (reranked chunks, usage dict with tokens and cost).
    """
    client = Anthropic()

    # Format candidates for Claude to judge
    candidate_text = "\n\n".join(
        f"[{i+1}] {c.metadata.get('doc_title')} › {c.metadata.get('section_title')}\n"
        f"Source: {c.metadata.get('source_path')}\n"
        f"Content: {c.text[:300]}..."
        for i, c in enumerate(candidates[:20])  # Rerank only top 20
    )

    prompt = f"""You are a relevance ranker. Given a question and candidate passages, rank them by how well they answer the question.

Question: {question}

Candidates:
{candidate_text}

Return a JSON array of candidate indices [1-based] in order of relevance. Only include candidates that are relevant to the question. Example format:
[2, 5, 1, 7, 3]

Respond ONLY with the JSON array, no other text."""

    start = time.time()
    response = client.messages.create(
        model=model,
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )
    latency_ms = (time.time() - start) * 1000

    # Parse the ranking
    try:
        text = response.content[0].text.strip()
        ranking = json.loads(text)
    except (json.JSONDecodeError, IndexError, AttributeError):
        # Fall back to original order if parsing fails
        ranking = list(range(1, len(candidates) + 1))

    # Build reranked results
    reranked: list[RankedChunk] = []
    for i, idx in enumerate(ranking):
        if idx < 1 or idx > len(candidates):
            continue
        candidate = candidates[idx - 1]
        # Score inversely by rerank position (1st = 1.0, 2nd = 0.8, etc.)
        rerank_score = max(0.0, 1.0 - (i * 0.2))
        reranked.append(
            RankedChunk(
                chunk_id=candidate.chunk_id,
                text=candidate.text,
                metadata=candidate.metadata,
                original_score=candidate.score,
                rerank_score=rerank_score,
            )
        )
        if len(reranked) >= top_k:
            break

    usage = {
        "reranker_model": model,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "latency_ms": latency_ms,
    }

    return reranked, usage
