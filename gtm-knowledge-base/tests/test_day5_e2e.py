"""Day 5 Definition-of-Done gate: the full retrieve → rerank → cited-answer pipeline
over the real 30-doc corpus, with the LLM faked so the run is deterministic and free.

This is the computed gate for "every answer includes at least one citation" and
"cost per query is reported" — asserted, not narrated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from gtm_kb.ingest import ingest
from gtm_kb.rag import RAGAssistant


@dataclass
class FakeUsage:
    input_tokens: int = 2000
    output_tokens: int = 150


@dataclass
class FakeTextBlock:
    text: str
    type: str = "text"


@dataclass
class FakeMessage:
    content: list[Any]
    stop_reason: str = "end_turn"
    usage: FakeUsage = field(default_factory=FakeUsage)


class ScriptedClient:
    """Returns a rerank ranking on the first call, then a cited answer.

    The answer text is built from the chunks the pipeline actually retrieved, so
    the citation must genuinely resolve — it can't pass by hardcoding a string.
    """

    def __init__(self) -> None:
        self.messages = self
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> FakeMessage:
        self.calls.append(kwargs)
        content = kwargs["messages"][0]["content"]

        if len(self.calls) == 1:  # rerank turn
            return FakeMessage(content=[FakeTextBlock("[2, 1, 3]")])

        # answer turn — cite the first source the pipeline actually passed in
        import re

        m = re.search(r'doc_title="([^"]*)" section_title="([^"]*)"', content)
        assert m, "answer prompt should carry structured source attributes"
        marker = f"[source: {m.group(1)}#{m.group(2)}]"
        return FakeMessage(content=[FakeTextBlock(f"Northstar competes with Clari {marker}.")])


@pytest.fixture(scope="module")
def index_dir(tmp_path_factory):
    d = tmp_path_factory.mktemp("kb_index_day5")
    ingest(index_dir=d)
    return d


@pytest.fixture
def assistant(index_dir):
    return RAGAssistant(index_dir=index_dir, client=ScriptedClient())


def test_dod_answer_carries_at_least_one_resolved_citation(assistant):
    result = assistant.query("Who does Northstar compete with?")

    assert result.citations, "Day 5 DoD: every answer must include >=1 citation"
    assert not result.unresolved_citations, (
        f"answer cited sources not in context: {result.unresolved_citations}"
    )
    # every citation must point at a chunk that was actually retrieved
    retrieved_ids = {c.chunk_id for c in result.top_chunks_for_debug}
    assert all(c.chunk_id in retrieved_ids for c in result.citations)


def test_dod_cost_and_per_stage_latency_are_reported(assistant):
    result = assistant.query("What is Northstar's pricing?")

    assert result.cost_usd > 0, "a billed call must report non-zero cost"
    assert result.tokens_used > 0
    # per-stage latencies are recorded, and the total covers them
    assert result.retrieval_latency_ms >= 0
    assert result.answer_latency_ms >= 0
    assert result.latency_ms >= result.retrieval_latency_ms


def test_reranking_limits_chunks_to_requested_top_k(assistant):
    result = assistant.query("What integrations exist?", reranking_top_k=2)
    assert len(result.top_chunks_for_debug) <= 2


def test_pipeline_passes_retrieved_chunks_through_to_answer_prompt(assistant):
    """Guards the wiring: the answer turn must see the reranked chunks, not raw text."""
    result = assistant.query("What is the ICP?")

    client = assistant.client
    answer_prompt = client.calls[-1]["messages"][0]["content"]
    for chunk in result.top_chunks_for_debug:
        assert chunk.metadata["doc_title"] in answer_prompt
