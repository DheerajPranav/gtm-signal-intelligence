"""Day 9 eval-harness tests: grounding arithmetic and the verification gate."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "evals"))

from run_enrichment_eval import (  # noqa: E402
    format_report,
    load_gold,
    run_eval,
    score_fields,
    score_url_grounding,
)

from gtm_outbound.models import CompanyProfile, Sourced, TargetCompany

NOW = datetime(2026, 7, 24)


def _s(value: str, url: str) -> Sourced[str]:
    return Sourced[str](value=value, source_url=url, confidence=0.9)


def _profile(**kw) -> CompanyProfile:
    return CompanyProfile(
        target=TargetCompany(domain="acme.com", name="Acme"), last_updated=NOW, **kw
    )


# ── URL grounding ─────────────────────────────────────────────────────────────
def test_all_cited_urls_retrieved_scores_one():
    p = _profile(industry=_s("SaaS", "https://a.test"))
    score, bad = score_url_grounding(p, {"https://a.test"})
    assert score == 1.0 and bad == []


def test_fabricated_url_is_caught_without_a_model():
    """The damaging failure: a citation that looks sourced but points nowhere real."""
    p = _profile(
        industry=_s("SaaS", "https://a.test"),
        funding_stage=_s("Series C", "https://invented.test/page"),
    )
    score, bad = score_url_grounding(p, {"https://a.test"})

    assert score == pytest.approx(0.5)
    assert bad == ["https://invented.test/page"]


def test_empty_profile_is_not_penalised_for_grounding():
    """Sourcing nothing is a coverage problem, not a hallucination."""
    score, bad = score_url_grounding(_profile(), set())
    assert score == 1.0 and bad == []


def test_grounding_counts_list_field_citations_too():
    p = _profile(tech_stack=[_s("Salesforce", "https://real.test"),
                             _s("Snowflake", "https://fake.test")])
    score, bad = score_url_grounding(p, {"https://real.test"})
    assert score == pytest.approx(0.5)
    assert bad == ["https://fake.test"]


# ── field accuracy ────────────────────────────────────────────────────────────
def test_exact_match_counts_as_a_hit():
    p = _profile(industry=_s("B2B SaaS", "https://a.test"))
    assert score_fields(p, {"industry": "B2B SaaS"}) == (1, 1)


def test_comparison_ignores_case_and_padding():
    p = _profile(industry=_s("  b2b saas ", "https://a.test"))
    assert score_fields(p, {"industry": "B2B SaaS"}) == (1, 1)


def test_null_expectations_are_skipped_not_counted_as_misses():
    """An unverifiable field must not drag accuracy down."""
    p = _profile(industry=_s("B2B SaaS", "https://a.test"))
    assert score_fields(p, {"industry": "B2B SaaS", "funding_stage": None}) == (1, 1)


def test_missing_field_counts_as_comparable_but_not_a_hit():
    assert score_fields(_profile(), {"industry": "B2B SaaS"}) == (0, 1)


def test_wrong_value_counts_as_comparable_but_not_a_hit():
    p = _profile(industry=_s("fintech", "https://a.test"))
    assert score_fields(p, {"industry": "B2B SaaS"}) == (0, 1)


# ── coverage ──────────────────────────────────────────────────────────────────
def test_coverage_distinguishes_absent_from_wrong():
    partial = _profile(industry=_s("SaaS", "https://a.test"))
    assert partial.coverage() == pytest.approx(0.25)
    assert set(partial.unsourced_fields()) == {"sub_industry", "size_band", "funding_stage"}


# ── verification gate ─────────────────────────────────────────────────────────
def test_shipped_gold_set_has_ten_rows():
    assert len(load_gold()) == 10


def test_shipped_gold_set_is_unverified_by_design():
    """Ground truth about real companies must be checked by a human before it scores."""
    gold = load_gold()
    assert all(g["verified"] is False for g in gold)
    assert all(v is None for g in gold for v in g["expected"].values())


def test_offline_run_reports_readiness_without_inventing_metrics():
    r = run_eval(offline=True)
    assert r["field_accuracy"] is None
    assert r["url_grounding"] is None
    assert r["verified_rows"] == 0
    assert r["total_rows"] == 10


def test_unverified_rows_are_excluded_from_accuracy(tmp_path):
    gold = tmp_path / "g.jsonl"
    gold.write_text(json.dumps({
        "domain": "acme.com", "name": "Acme", "verified": False,
        "expected": {"industry": "B2B SaaS"},
    }) + "\n", encoding="utf-8")

    class P:
        served_urls = {"https://a.test"}
        def web_search(self, q): return []
        def news_search(self, q): return []
        def fetch_page(self, u): raise RuntimeError("unused")

    from tests.test_research_agent import ScriptedClient, FakeToolUse
    client = ScriptedClient([FakeToolUse(
        "record_profile",
        {"industry": {"value": "B2B SaaS", "source_url": "https://a.test", "confidence": 0.9}},
        id="tu-r",
    )])

    r = run_eval(provider=P(), client=client, gold_path=gold)

    # The value matches, but the row is unverified — so it must not produce a score.
    assert r["field_accuracy"] is None
    assert r["field_accuracy_n"] == 0
    assert r["url_grounding"] == 1.0  # grounding needs no ground truth


def test_verified_rows_do_produce_accuracy(tmp_path):
    gold = tmp_path / "g.jsonl"
    gold.write_text(json.dumps({
        "domain": "acme.com", "name": "Acme", "verified": True,
        "expected": {"industry": "B2B SaaS", "funding_stage": "Series C"},
    }) + "\n", encoding="utf-8")

    class P:
        served_urls = {"https://a.test"}
        def web_search(self, q): return []
        def news_search(self, q): return []
        def fetch_page(self, u): raise RuntimeError("unused")

    from tests.test_research_agent import ScriptedClient, FakeToolUse
    client = ScriptedClient([FakeToolUse(
        "record_profile",
        {"industry": {"value": "B2B SaaS", "source_url": "https://a.test", "confidence": 0.9}},
        id="tu-r",
    )])

    r = run_eval(provider=P(), client=client, gold_path=gold)

    assert r["field_accuracy"] == pytest.approx(0.5)  # 1 of 2 comparable
    assert r["field_accuracy_n"] == 2


def test_report_says_not_measured_when_nothing_is_verified():
    report = format_report(run_eval(offline=True))
    assert "not measured" in report
    assert "no gold row has `verified: true`" in report.lower()


def test_one_failing_domain_does_not_sink_the_run(tmp_path):
    gold = tmp_path / "g.jsonl"
    gold.write_text(json.dumps({
        "domain": "bad.com", "name": "Bad", "verified": False, "expected": {},
    }) + "\n", encoding="utf-8")

    class P:
        def web_search(self, q): return []
        def news_search(self, q): return []
        def fetch_page(self, u): raise RuntimeError("unused")

    class Boom:
        messages = property(lambda self: self)
        def create(self, **kw): raise RuntimeError("model down")

    r = run_eval(provider=P(), client=Boom(), gold_path=gold)

    assert r["errored_rows"] == 1
    assert r["rows"][0]["error"].startswith("RuntimeError")
