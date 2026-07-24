"""RAG assistant: retrieval → reranking → cited answer, with cost and latency tracking."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Optional

from .answer_gen import DEFAULT_ANSWER_MODEL, generate_answer
from .citations import parse_citations
from .models import QueryResult
from .query import query as retrieve
from .reranker import DEFAULT_RERANK_MODEL, rerank

# USD per 1M tokens. Unknown models raise rather than silently reporting $0 —
# a cost of zero must mean "no billable call", never "we didn't recognise it".
PRICING: dict[str, dict[str, float]] = {
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
}


class UnknownModelPricingError(KeyError):
    """Raised when a billed call uses a model absent from PRICING."""


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """USD cost for a call. Raises on unknown models that actually consumed tokens."""
    if input_tokens == 0 and output_tokens == 0:
        return 0.0
    if model not in PRICING:
        raise UnknownModelPricingError(
            f"No pricing for {model!r}; refusing to report $0.00 for a billed call. "
            f"Add it to gtm_kb.rag.PRICING."
        )
    rates = PRICING[model]
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000


class RAGAssistant:
    """End-to-end RAG: retrieve → rerank → answer."""

    def __init__(
        self,
        index_dir: Optional[Path] = None,
        client: Optional[Any] = None,
        rerank_model: str = DEFAULT_RERANK_MODEL,
        answer_model: str = DEFAULT_ANSWER_MODEL,
    ):
        from .config import INDEX_DIR

        self.index_dir = index_dir or INDEX_DIR
        self.client = client
        self.rerank_model = rerank_model
        self.answer_model = answer_model

    def query(
        self,
        question: str,
        retrieval_top_k: int = 20,
        reranking_top_k: int = 5,
    ) -> QueryResult:
        """Run the full pipeline and report per-stage latency plus real cost."""
        start_time = time.perf_counter()

        t0 = time.perf_counter()
        retrieved = retrieve(
            question, top_k=retrieval_top_k, mode="hybrid", index_dir=self.index_dir
        )
        retrieval_latency = (time.perf_counter() - t0) * 1000

        reranked, rerank_usage = rerank(
            question,
            retrieved,
            top_k=reranking_top_k,
            model=self.rerank_model,
            client=self.client,
        )
        rerank_cost = estimate_cost(
            rerank_usage["reranker_model"],
            rerank_usage["input_tokens"],
            rerank_usage["output_tokens"],
        )

        cited_answer, answer_usage = generate_answer(
            question, reranked, model=self.answer_model, client=self.client
        )
        answer_cost = estimate_cost(
            answer_usage["answer_model"],
            answer_usage["input_tokens"],
            answer_usage["output_tokens"],
        )

        # Single parse, shared with answer_gen — the regex lives in citations.py only.
        citations, _, unresolved = parse_citations(cited_answer.answer, reranked)

        total_tokens = (
            rerank_usage["input_tokens"]
            + rerank_usage["output_tokens"]
            + answer_usage["input_tokens"]
            + answer_usage["output_tokens"]
        )

        return QueryResult(
            question=question,
            answer_text=cited_answer.answer,
            citations=citations,
            top_chunks_for_debug=reranked,
            unresolved_citations=unresolved,
            tokens_used=total_tokens,
            cost_usd=round(rerank_cost + answer_cost, 6),
            latency_ms=round((time.perf_counter() - start_time) * 1000, 1),
            retrieval_latency_ms=round(retrieval_latency, 1),
            rerank_latency_ms=round(rerank_usage["latency_ms"], 1),
            answer_latency_ms=round(answer_usage["latency_ms"], 1),
        )
