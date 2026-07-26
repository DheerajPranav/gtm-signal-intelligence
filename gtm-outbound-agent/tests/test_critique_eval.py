"""Day 13 critique-eval tests: calibration arithmetic and the measurement gate."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "evals"))

from run_critique_eval import CALIBRATION, format_report, run_eval  # noqa: E402

from tests.test_research_agent import FakeToolUse, ScriptedClient


def _turn(send: bool, spam: float):
    return [FakeToolUse("record_evaluation", {
        "personalization_score": 4.0 if send else 1.0,
        "relevance_score": 4.0 if send else 1.0, "cta_score": 4.0 if send else 1.0,
        "spam_risk": spam, "would_send": send, "reasoning": "r",
    }, id="tu")]


def test_calibration_set_has_good_and_bad_emails():
    labels = [lbl for lbl, _, _ in CALIBRATION]
    assert labels.count("good") == 3 and labels.count("bad") == 3


# ── gate ──────────────────────────────────────────────────────────────────────
def test_offline_reports_readiness_without_numbers():
    r = run_eval(offline=True)
    assert r["would_send_agreement"] is None
    assert r["total"] == 6


def test_report_says_not_measured_offline():
    assert "not measured" in format_report(run_eval(offline=True))


# ── full run ──────────────────────────────────────────────────────────────────
def test_perfect_judge_agrees_and_separates_spam():
    # Score the 3 good as send/low-spam, the 3 bad as hold/high-spam (calibration order).
    turns = [_turn(True, 1.0)] * 3 + [_turn(False, 4.0)] * 3
    r = run_eval(client=ScriptedClient(*turns))
    assert r["would_send_agreement"] == pytest.approx(1.0)
    assert r["spam_gap"] == pytest.approx(3.0)  # bad(4) - good(1)
    assert r["scored"] == 6


def test_indiscriminate_judge_scores_only_half():
    # Always "send" -> matches the 3 good labels, misses the 3 bad -> 0.5 agreement.
    r = run_eval(client=ScriptedClient(_turn(True, 2.0)))
    assert r["would_send_agreement"] == pytest.approx(0.5)


def test_one_bad_row_does_not_sink_the_run():
    class Boom:
        messages = property(lambda self: self)
        def create(self, **kw):
            raise RuntimeError("model down")

    r = run_eval(client=Boom())
    assert r["errored"] == 6
    assert r["would_send_agreement"] is None
