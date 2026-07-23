"""Test Day 5 RAG components: models, reranker, answer_gen."""

import pytest
from gtm_kb.models import RankedChunk, CitedAnswer, Citation, QueryResult
from gtm_kb.query import Result


def test_ranked_chunk_model():
    """Verify RankedChunk model structure."""
    chunk = RankedChunk(
        chunk_id="chunk-1",
        text="Sample text",
        metadata={"doc_title": "Product", "section_title": "Overview"},
        original_score=0.95,
        rerank_score=0.87,
    )
    assert chunk.chunk_id == "chunk-1"
    assert chunk.rerank_score == 0.87
    assert chunk.metadata["doc_title"] == "Product"


def test_ranked_chunk_model_rejects_extra_fields():
    """Verify RankedChunk rejects unexpected fields."""
    with pytest.raises(ValueError):
        RankedChunk(
            chunk_id="chunk-1",
            text="Sample text",
            metadata={"doc_title": "Product"},
            original_score=0.95,
            rerank_score=0.87,
            unknown_field="should fail",
        )


def test_citation_model():
    """Verify Citation model structure."""
    citation = Citation(
        doc_title="Product Overview",
        section_title="Features",
        source_path="product/overview.md",
        chunk_id="chunk-42",
    )
    assert citation.doc_title == "Product Overview"
    assert citation.section_title == "Features"


def test_cited_answer_model():
    """Verify CitedAnswer model structure."""
    chunk = RankedChunk(
        chunk_id="chunk-1",
        text="Sample text",
        metadata={"doc_title": "Product"},
        original_score=0.95,
        rerank_score=0.87,
    )
    answer = CitedAnswer(
        answer="This is an answer [source: Product#Overview]",
        cited_chunks=[chunk],
        usage={"input_tokens": 100, "output_tokens": 50},
    )
    assert "citation" in answer.answer.lower() or "source" in answer.answer.lower()
    assert len(answer.cited_chunks) == 1


def test_query_result_model():
    """Verify QueryResult model structure."""
    citation = Citation(
        doc_title="Product",
        section_title="Overview",
        source_path="product/overview.md",
        chunk_id="chunk-1",
    )
    chunk = RankedChunk(
        chunk_id="chunk-1",
        text="Sample text",
        metadata={"doc_title": "Product"},
        original_score=0.95,
        rerank_score=0.87,
    )
    result = QueryResult(
        question="What is Northstar?",
        answer_text="Northstar is a RevOps analytics platform.",
        citations=[citation],
        top_chunks_for_debug=[chunk],
        tokens_used=150,
        cost_usd=0.0012,
        latency_ms=234.5,
    )
    assert result.question == "What is Northstar?"
    assert result.tokens_used == 150
    assert result.cost_usd == 0.0012
    assert len(result.citations) == 1


def test_rrf_fusion_preserves_coverage():
    """Verify hybrid retrieval doesn't lose candidates during fusion."""
    from gtm_kb.query import _rrf_fuse

    # Two ranked lists from BM25 and vector search
    ranked_lists = [
        ["chunk-1", "chunk-2", "chunk-3"],  # vector results
        ["chunk-2", "chunk-4", "chunk-5"],  # BM25 results
    ]

    scores = _rrf_fuse(ranked_lists)

    # All chunks should be present
    assert "chunk-1" in scores
    assert "chunk-2" in scores
    assert "chunk-3" in scores
    assert "chunk-4" in scores
    assert "chunk-5" in scores

    # chunk-2 (appears in both) should score higher than single-appearance chunks
    assert scores["chunk-2"] > scores["chunk-1"]


def test_result_to_ranked_chunk_conversion():
    """Verify Result from query can be converted to RankedChunk."""
    result = Result(
        chunk_id="chunk-1",
        text="Sample content",
        metadata={"doc_title": "Product", "section_title": "Overview", "source_path": "product/overview.md"},
        score=0.85,
        retriever="hybrid",
    )

    # Simulate conversion to RankedChunk
    chunk = RankedChunk(
        chunk_id=result.chunk_id,
        text=result.text,
        metadata=result.metadata,
        original_score=result.score,
        rerank_score=0.92,
    )

    assert chunk.chunk_id == result.chunk_id
    assert chunk.text == result.text
    assert chunk.original_score == result.score
    assert chunk.rerank_score == 0.92
