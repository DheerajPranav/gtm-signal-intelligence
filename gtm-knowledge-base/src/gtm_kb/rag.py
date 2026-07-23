"""RAG assistant: orchestrates retrieval → reranking → answer generation with cost tracking."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from .query import query as retrieve
from .reranker import rerank
from .answer_gen import generate_answer
from .models import QueryResult, Citation


# Pricing per 1M tokens (May 2024 rates)
PRICING = {
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
}


def _estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost for a model call."""
    if model not in PRICING:
        return 0.0
    rates = PRICING[model]
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000


class RAGAssistant:
    """End-to-end RAG: retrieve → rerank → answer with cost and latency tracking."""

    def __init__(self, index_dir: Optional[Path] = None):
        from .config import INDEX_DIR
        self.index_dir = index_dir or INDEX_DIR

    def query(
        self,
        question: str,
        retrieval_top_k: int = 20,
        reranking_top_k: int = 5,
    ) -> QueryResult:
        """Execute a full RAG query.

        Args:
            question: The user's question.
            retrieval_top_k: Number of candidates from hybrid retrieval.
            reranking_top_k: Number of top results after reranking.

        Returns:
            QueryResult with answer, citations, and cost/latency.
        """
        start_time = time.time()
        total_tokens = 0
        total_cost = 0.0

        # Step 1: Hybrid retrieval
        retrieval_start = time.time()
        retrieved = retrieve(question, top_k=retrieval_top_k, mode="hybrid", index_dir=self.index_dir)
        retrieval_latency = (time.time() - retrieval_start) * 1000

        # Step 2: Rerank
        reranked, rerank_usage = rerank(question, retrieved, top_k=reranking_top_k)
        total_tokens += rerank_usage.get("input_tokens", 0) + rerank_usage.get("output_tokens", 0)
        total_cost += _estimate_cost(
            rerank_usage.get("reranker_model", ""),
            rerank_usage.get("input_tokens", 0),
            rerank_usage.get("output_tokens", 0),
        )

        # Step 3: Answer generation with citations
        cited_answer, answer_usage = generate_answer(question, reranked)
        total_tokens += answer_usage.get("input_tokens", 0) + answer_usage.get("output_tokens", 0)
        total_cost += _estimate_cost(
            answer_usage.get("answer_model", ""),
            answer_usage.get("input_tokens", 0),
            answer_usage.get("output_tokens", 0),
        )

        # Extract citations from the answer text
        import re
        citation_pattern = r"\[source:\s*([^#]+)#([^\]]+)\]"
        citation_matches = re.finditer(citation_pattern, cited_answer.answer, re.IGNORECASE)

        citations: list[Citation] = []
        seen_keys = set()

        for match in citation_matches:
            doc_title = match.group(1).strip()
            section_title = match.group(2).strip()

            for chunk in reranked:
                chunk_doc = chunk.metadata.get("doc_title", "").strip()
                chunk_sec = chunk.metadata.get("section_title", "").strip()

                if (
                    chunk_doc.lower() == doc_title.lower()
                    and chunk_sec.lower() == section_title.lower()
                ):
                    key = (chunk_doc, section_title, chunk.chunk_id)
                    if key not in seen_keys:
                        citations.append(
                            Citation(
                                doc_title=chunk_doc,
                                section_title=section_title,
                                source_path=chunk.metadata.get("source_path", ""),
                                chunk_id=chunk.chunk_id,
                            )
                        )
                        seen_keys.add(key)
                    break

        total_latency = (time.time() - start_time) * 1000

        return QueryResult(
            question=question,
            answer_text=cited_answer.answer,
            citations=citations,
            top_chunks_for_debug=reranked,
            tokens_used=total_tokens,
            cost_usd=round(total_cost, 4),
            latency_ms=round(total_latency, 1),
        )
