"""Pydantic models for Day 5: reranking, answer generation, and citation tracking."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True)
class Citation:
    """A reference to a source chunk."""
    doc_title: str
    section_title: str
    source_path: str
    chunk_id: str


class RankedChunk(BaseModel):
    """A chunk with a rerank score."""
    chunk_id: str
    text: str
    metadata: dict
    original_score: float
    rerank_score: float = Field(description="Score from reranker (0.0 to 1.0)")

    model_config = ConfigDict(extra="forbid")


class CitedAnswer(BaseModel):
    """An answer with inline citations and source attribution."""
    answer: str = Field(
        description="The answer text with inline citations like [source: doc_title#section]"
    )
    cited_chunks: list[RankedChunk] = Field(
        default_factory=list,
        description="Ranked source chunks the answer cited"
    )
    usage: dict = Field(
        default_factory=dict,
        description="Token usage from the answer generation call"
    )

    model_config = ConfigDict(extra="forbid")


class QueryResult(BaseModel):
    """Complete result of a retrieval + reranking + answer generation query."""
    question: str
    answer_text: str
    citations: list[Citation]
    top_chunks_for_debug: list[RankedChunk]
    tokens_used: int = 0
    cost_usd: float = 0.0
    latency_ms: float = 0.0

    model_config = ConfigDict(extra="forbid")
