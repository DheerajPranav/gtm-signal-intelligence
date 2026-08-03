"""The email-comparison example must actually separate great from templated emails."""

from __future__ import annotations

from examples.email_comparison import EMAILS, evaluate_all, summarize


def test_five_great_five_templated():
    labels = [e["label"] for e in EMAILS]
    assert labels.count("great") == 5
    assert labels.count("templated") == 5


def test_rubric_cleanly_separates():
    rows = evaluate_all()
    great = [r for r in rows if r.label == "great"]
    templated = [r for r in rows if r.label == "templated"]
    assert all(r.would_send for r in great)
    assert not any(r.would_send for r in templated)


def test_summary_reports_separation_and_positive_spam_gap():
    s = summarize(evaluate_all())
    assert s["separated"] is True
    assert s["great_would_send"] == "5/5"
    assert s["templated_would_send"] == "0/5"
    assert s["spam_gap"] > 0  # templated emails carry more spam risk


def test_offline_scores_are_illustrative(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    rows = evaluate_all()
    assert all(r.source == "illustrative" for r in rows)
