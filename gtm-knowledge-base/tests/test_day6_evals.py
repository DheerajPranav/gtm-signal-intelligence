"""Day 6 eval-harness tests: metric definitions and judge honesty.

The harness grades every other capability, so its own arithmetic is gated here.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "evals"))

from judges import (  # noqa: E402
    JudgeResult,
    judge_completeness,
    judge_faithfulness,
    lexical_trait_coverage,
)
from metrics import compute_retrieval_metrics  # noqa: E402
from run_eval import format_report, load_golden_qa, percentile  # noqa: E402


# ── retrieval metrics ─────────────────────────────────────────────────────────
def test_perfect_retrieval_scores_one_across_the_board():
    m = compute_retrieval_metrics(["a.md"] * 5, ["a.md"], k=5)
    assert (m.hit_rate, m.recall, m.chunk_precision, m.mrr) == (1.0, 1.0, 1.0, 1.0)


def test_chunk_precision_is_denominated_by_k_not_unique_docs():
    """Regression: the old harness divided by unique-doc count, so 1 gold doc
    retrieved among 1 unique doc scored 1.0 while the window was 80% noise."""
    m = compute_retrieval_metrics(["a.md", "b.md", "b.md", "b.md", "b.md"], ["a.md"], k=5)
    assert m.chunk_precision == pytest.approx(0.2)  # 1 of 5 chunks on-target


def test_hit_rate_is_binary_regardless_of_how_many_chunks_hit():
    one = compute_retrieval_metrics(["a.md", "x.md", "y.md", "z.md", "w.md"], ["a.md"], k=5)
    many = compute_retrieval_metrics(["a.md"] * 5, ["a.md"], k=5)
    assert one.hit_rate == many.hit_rate == 1.0


def test_recall_counts_distinct_gold_docs_not_chunk_repeats():
    m = compute_retrieval_metrics(["a.md", "a.md", "a.md"], ["a.md", "b.md"], k=5)
    assert m.recall == pytest.approx(0.5)


def test_mrr_rewards_ranking_the_gold_chunk_higher():
    top = compute_retrieval_metrics(["a.md", "x.md", "y.md"], ["a.md"], k=5)
    third = compute_retrieval_metrics(["x.md", "y.md", "a.md"], ["a.md"], k=5)
    assert top.mrr == 1.0
    assert third.mrr == pytest.approx(1 / 3)
    assert top.mrr > third.mrr


def test_complete_miss_scores_zero():
    m = compute_retrieval_metrics(["x.md", "y.md"], ["a.md"], k=5)
    assert (m.hit_rate, m.recall, m.chunk_precision, m.mrr) == (0.0, 0.0, 0.0, 0.0)


def test_metrics_respect_the_k_cutoff():
    """A gold doc sitting at rank 6 must not count toward an @5 metric."""
    m = compute_retrieval_metrics(["x.md"] * 5 + ["a.md"], ["a.md"], k=5)
    assert m.hit_rate == 0.0


def test_no_expected_sources_does_not_divide_by_zero():
    m = compute_retrieval_metrics(["a.md"], [], k=5)
    assert m.recall == 0.0


# ── percentiles ───────────────────────────────────────────────────────────────
def test_percentile_of_empty_series_is_none_not_a_placeholder():
    """Regression: the old harness substituted a hardcoded 50ms and printed it
    as a measured p50."""
    assert percentile([], 50) is None


def test_percentile_picks_expected_ranks():
    assert percentile([10.0], 95) == 10.0
    assert percentile([1.0, 2.0, 3.0, 4.0], 50) == pytest.approx(2.0)


# ── judges: availability honesty ──────────────────────────────────────────────
@dataclass
class FakeUsage:
    input_tokens: int = 500
    output_tokens: int = 80


@dataclass
class FakeTextBlock:
    text: str
    type: str = "text"


@dataclass
class FakeMessage:
    content: list[Any]
    usage: FakeUsage = field(default_factory=FakeUsage)


class JudgeClient:
    def __init__(self, payload: str) -> None:
        self._payload = payload
        self.messages = self
        self.calls: list[dict] = []

    def create(self, **kwargs: Any) -> FakeMessage:
        self.calls.append(kwargs)
        return FakeMessage(content=[FakeTextBlock(self._payload)])


def test_faithfulness_without_a_key_reports_unavailable_not_a_score(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = judge_faithfulness("some answer", ["a passage"])
    assert result.available is False
    assert result.as_dict() == {"available": False}


def test_completeness_without_a_key_reports_unavailable(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert judge_completeness("answer", ["trait"]).available is False


def test_faithfulness_scores_supported_over_total():
    client = JudgeClient('{"supported": 3, "total": 4, "unsupported_claims": ["x"], "reasoning": "one claim unsupported"}')
    result = judge_faithfulness("answer", ["passage"], client=client)
    assert result.available is True
    assert result.score == pytest.approx(0.75)


def test_completeness_scores_covered_over_total():
    client = JudgeClient('{"covered": 1, "total": 2, "missing": ["b"], "reasoning": "missed one"}')
    result = judge_completeness("answer", ["a", "b"], client=client)
    assert result.score == pytest.approx(0.5)


def test_judge_salvages_json_wrapped_in_prose():
    client = JudgeClient('Here is my verdict:\n{"supported": 2, "total": 2, "reasoning": "ok"}')
    assert judge_faithfulness("a", ["p"], client=client).score == 1.0


def test_judge_returns_unavailable_on_unparseable_verdict():
    client = JudgeClient("I am unable to comply.")
    assert judge_faithfulness("a", ["p"], client=client).available is False


def test_faithfulness_with_zero_claims_is_unavailable_not_zero():
    """An honest refusal has no claims to audit; scoring it 0.0 would punish
    correct behaviour."""
    client = JudgeClient('{"supported": 0, "total": 0, "reasoning": "no claims"}')
    assert judge_faithfulness("I cannot answer that.", ["p"], client=client).available is False


def test_completeness_with_no_traits_is_unavailable():
    assert judge_completeness("answer", []).available is False


# ── lexical proxy ─────────────────────────────────────────────────────────────
def test_lexical_coverage_counts_literal_trait_hits():
    assert lexical_trait_coverage("Costs $2,500 per month", ["$2,500", "per month"]) == 1.0
    assert lexical_trait_coverage("Costs $2,500", ["$2,500", "per month"]) == pytest.approx(0.5)


def test_lexical_coverage_is_case_insensitive():
    assert lexical_trait_coverage("REVOPS ANALYTICS", ["revops analytics"]) == 1.0


# ── report rendering ──────────────────────────────────────────────────────────
def test_report_prints_not_measured_instead_of_fabricating_numbers():
    stub = {
        "timestamp": "2026-07-24 00:00:00",
        "mode": "retrieval-only",
        "k": 5,
        "total_questions": 1,
        "retrieval": {
            "hit_rate_at_5": 0.5, "recall_at_5": 0.5,
            "chunk_precision_at_5": 0.2, "mrr_at_5": 0.5,
        },
        "answer_quality": {
            "measured": False, "faithfulness": None, "completeness": None,
            "lexical_trait_coverage": None, "ungrounded_citations": None,
        },
        "performance": {
            "measured": False, "latency_p50_ms": None, "latency_p95_ms": None,
            "avg_cost_per_query": None, "total_cost_usd": None,
        },
        "by_category": {"factoid": {"count": 1, "hit_rate": 0.5, "recall": 0.5}},
        "questions": [{
            "question": "q", "category": "factoid",
            "retrieval": {"hit_rate": 0.5, "recall": 0.5, "mrr": 0.5},
        }],
    }
    report = format_report(stub)

    assert "not measured" in report
    assert "Faithfulness" in report
    # the retrieval numbers that WERE computed still render
    assert "0.5" in report


# ── golden set integrity ──────────────────────────────────────────────────────
def test_golden_set_has_35_questions_across_five_categories():
    qa = load_golden_qa()
    assert len(qa) == 35
    assert {q["category"] for q in qa} == {
        "factoid", "comparison", "synthesis", "icp", "edge_case",
    }


def test_every_golden_question_declares_sources_and_traits():
    for q in load_golden_qa():
        assert q["expected_sources"], f"{q['question']!r} has no expected_sources"
        assert q["expected_answer_traits"], f"{q['question']!r} has no expected_answer_traits"
