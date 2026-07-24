"""Day 5 LLM-path tests. No API calls — the Anthropic client is faked so the
rerank / answer / citation wiring is verified deterministically.

Mirrors the fake-client pattern established in gtm-cli-warmup/tests/test_lead.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from gtm_kb.answer_gen import AnswerError, generate_answer
from gtm_kb.citations import parse_citations
from gtm_kb.models import RankedChunk
from gtm_kb.query import Result
from gtm_kb.rag import UnknownModelPricingError, estimate_cost
from gtm_kb.reranker import _parse_ranking, rerank


# ── fakes standing in for the Anthropic SDK ───────────────────────────────────
@dataclass
class FakeUsage:
    input_tokens: int = 1000
    output_tokens: int = 200


@dataclass
class FakeTextBlock:
    text: str
    type: str = "text"


@dataclass
class FakeMessage:
    content: list[Any]
    stop_reason: str = "end_turn"
    usage: FakeUsage = field(default_factory=FakeUsage)


class RecordingClient:
    """Captures create() kwargs and returns canned messages in sequence."""

    def __init__(self, *texts: str) -> None:
        self._messages = [FakeMessage(content=[FakeTextBlock(t)]) for t in texts]
        self._i = 0
        self.calls: list[dict[str, Any]] = []
        self.messages = self

    def create(self, **kwargs: Any) -> FakeMessage:
        self.calls.append(kwargs)
        msg = self._messages[min(self._i, len(self._messages) - 1)]
        self._i += 1
        return msg


class EmptyContentClient:
    def __init__(self) -> None:
        self.messages = self

    def create(self, **kwargs: Any) -> FakeMessage:
        return FakeMessage(content=[], stop_reason="max_tokens")


# ── fixtures ──────────────────────────────────────────────────────────────────
def _result(i: int, doc: str = "Pricing", section: str = "Tiers") -> Result:
    return Result(
        chunk_id=f"chunk-{i}",
        text=f"Body text for chunk {i}.",
        metadata={
            "doc_title": doc,
            "section_title": section,
            "source_path": f"product/{doc.lower()}.md",
        },
        score=1.0 / i,
        retriever="hybrid",
    )


def _chunk(i: int, doc: str = "Pricing", section: str = "Tiers") -> RankedChunk:
    return RankedChunk(
        chunk_id=f"chunk-{i}",
        text=f"Body text for chunk {i}.",
        metadata={
            "doc_title": doc,
            "section_title": section,
            "source_path": f"product/{doc.lower()}.md",
        },
        original_score=0.5,
        rerank_score=1.0,
    )


# ── _parse_ranking: every way a model can misbehave ───────────────────────────
def test_parse_ranking_happy_path():
    assert _parse_ranking("[3, 1, 2]", pool_size=5) == [3, 1, 2]


def test_parse_ranking_drops_out_of_range_indices():
    """An index past the pool would map to a chunk the model never saw."""
    assert _parse_ranking("[1, 99, 2, 0, -4]", pool_size=3) == [1, 2]


def test_parse_ranking_deduplicates():
    assert _parse_ranking("[2, 2, 1, 2]", pool_size=5) == [2, 1]


def test_parse_ranking_salvages_json_wrapped_in_prose():
    assert _parse_ranking("Sure! Here you go: [2, 1]. Hope that helps.", pool_size=5) == [2, 1]


def test_parse_ranking_rejects_non_integers_and_bools():
    # bool is an int subclass in Python — True must not become index 1.
    assert _parse_ranking('[true, "2", 3.7, 3]', pool_size=5) == [3]


def test_parse_ranking_returns_empty_on_garbage():
    assert _parse_ranking("I cannot rank these.", pool_size=5) == []


def test_parse_ranking_handles_non_list_json():
    assert _parse_ranking('{"best": 1}', pool_size=5) == []


# ── rerank ────────────────────────────────────────────────────────────────────
def test_rerank_reorders_by_model_ranking():
    candidates = [_result(i) for i in range(1, 6)]
    client = RecordingClient("[3, 1]")

    reranked, usage = rerank("q", candidates, top_k=2, client=client)

    assert [c.chunk_id for c in reranked] == ["chunk-3", "chunk-1"]
    assert usage["fell_back"] is False


def test_rerank_scores_stay_distinct_beyond_rank_five():
    """Regression: a fixed 0.2 decay saturated every rank past the 5th at 0.0."""
    candidates = [_result(i) for i in range(1, 11)]
    client = RecordingClient("[1,2,3,4,5,6,7,8]")

    reranked, _ = rerank("q", candidates, top_k=8, client=client)

    scores = [c.rerank_score for c in reranked]
    assert len(set(scores)) == len(scores), f"duplicate scores: {scores}"
    assert all(s >= 0.0 for s in scores)
    assert scores == sorted(scores, reverse=True)


def test_rerank_never_selects_beyond_the_pool_it_showed():
    """Regression: indices were validated against all candidates, not the shown pool."""
    candidates = [_result(i) for i in range(1, 31)]  # 30 > RERANK_POOL of 20
    client = RecordingClient("[25, 1]")  # 25 was never shown to the model

    reranked, _ = rerank("q", candidates, top_k=5, client=client)

    assert [c.chunk_id for c in reranked] == ["chunk-1"]


def test_rerank_falls_back_to_retrieval_order_on_unparseable_response():
    candidates = [_result(i) for i in range(1, 4)]
    client = RecordingClient("sorry, I can't do that")

    reranked, usage = rerank("q", candidates, top_k=3, client=client)

    assert [c.chunk_id for c in reranked] == ["chunk-1", "chunk-2", "chunk-3"]
    assert usage["fell_back"] is True


def test_rerank_on_empty_candidates_makes_no_call():
    client = RecordingClient("[1]")
    reranked, usage = rerank("q", [], top_k=5, client=client)

    assert reranked == []
    assert client.calls == []
    assert usage["input_tokens"] == 0


# ── citation parsing ──────────────────────────────────────────────────────────
def test_parse_citations_resolves_and_dedupes():
    chunks = [_chunk(1, "Pricing", "Tiers"), _chunk(2, "Security", "SOC2")]
    answer = (
        "Costs $2,500 [source: Pricing#Tiers] and is certified "
        "[source: Security#SOC2]. Again [source: Pricing#Tiers]."
    )

    citations, cited, unresolved = parse_citations(answer, chunks)

    assert [c.chunk_id for c in citations] == ["chunk-1", "chunk-2"]
    assert [c.chunk_id for c in cited] == ["chunk-1", "chunk-2"]
    assert unresolved == []


def test_parse_citations_surfaces_hallucinated_sources():
    """A citation matching no supplied chunk is a grounding failure, not a no-op."""
    chunks = [_chunk(1, "Pricing", "Tiers")]
    answer = "Northstar has 500 staff [source: Company#Headcount]."

    citations, cited, unresolved = parse_citations(answer, chunks)

    assert citations == []
    assert cited == []
    assert unresolved == ["Company#Headcount"]


def test_parse_citations_is_case_and_whitespace_insensitive():
    chunks = [_chunk(1, "Pricing", "Tiers")]
    answer = "See [source:   pricing  #  TIERS ]."

    citations, _, unresolved = parse_citations(answer, chunks)

    assert len(citations) == 1
    assert unresolved == []


def test_parse_citations_keeps_adjacent_citations_separate():
    chunks = [_chunk(1, "Pricing", "Tiers"), _chunk(2, "Security", "SOC2")]
    answer = "Both [source: Pricing#Tiers][source: Security#SOC2] apply."

    citations, _, _ = parse_citations(answer, chunks)

    assert len(citations) == 2


# ── generate_answer ───────────────────────────────────────────────────────────
def test_generate_answer_returns_only_cited_chunks():
    """Regression: cited_chunks used to be every chunk shown, not the cited subset."""
    chunks = [_chunk(1, "Pricing", "Tiers"), _chunk(2, "Security", "SOC2")]
    client = RecordingClient("It is $2,500 [source: Pricing#Tiers].")

    answer, _ = generate_answer("how much?", chunks, client=client)

    assert [c.chunk_id for c in answer.cited_chunks] == ["chunk-1"]


def test_generate_answer_fences_sources_and_sets_system_prompt():
    chunks = [_chunk(1)]
    client = RecordingClient("ok [source: Pricing#Tiers]")

    generate_answer("q", chunks, client=client)

    kwargs = client.calls[0]
    assert "system" in kwargs, "grounding rules must live in the system prompt"
    assert "<sources>" in kwargs["messages"][0]["content"]
    assert kwargs["messages"][0]["role"] == "user"


def test_generate_answer_short_circuits_with_no_chunks():
    """No grounding available: refuse honestly without burning an API call."""
    client = RecordingClient("should not be called")

    answer, usage = generate_answer("q", [], client=client)

    assert client.calls == []
    assert answer.cited_chunks == []
    assert usage["input_tokens"] == 0
    assert "cannot be answered" in answer.answer.lower()


def test_generate_answer_raises_when_model_returns_no_text():
    with pytest.raises(AnswerError, match="no text block"):
        generate_answer("q", [_chunk(1)], client=EmptyContentClient())


def test_generate_answer_records_unresolved_citations():
    chunks = [_chunk(1, "Pricing", "Tiers")]
    client = RecordingClient("Claim [source: Invented#Section].")

    answer, _ = generate_answer("q", chunks, client=client)

    assert answer.unresolved_citations == ["Invented#Section"]
    assert answer.cited_chunks == []


# ── cost accounting ───────────────────────────────────────────────────────────
def test_estimate_cost_computes_known_model():
    # 1M in + 1M out on Sonnet = $3.00 + $15.00
    assert estimate_cost("claude-3-5-sonnet-20241022", 1_000_000, 1_000_000) == pytest.approx(18.00)


def test_estimate_cost_raises_on_unknown_model_with_tokens():
    """A billed call must never silently report $0.00."""
    with pytest.raises(UnknownModelPricingError):
        estimate_cost("claude-9-imaginary", 100, 50)


def test_estimate_cost_is_zero_when_no_tokens_consumed():
    assert estimate_cost("claude-9-imaginary", 0, 0) == 0.0
