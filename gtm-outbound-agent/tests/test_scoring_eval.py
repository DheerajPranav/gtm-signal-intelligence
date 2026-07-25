"""Day 10 scoring-eval tests: Spearman/confusion arithmetic and the measurement gate."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "evals"))

from run_scoring_eval import (  # noqa: E402
    band_for_score,
    confusion,
    format_report,
    run_eval,
    spearman,
)
from scoring_gold import GOLD, band_counts  # noqa: E402

from tests.test_research_agent import FakeToolUse, ScriptedClient
from gtm_outbound.icp import StaticICPProvider

ICP = StaticICPProvider("B2B SaaS ICP text")


# ── Spearman ──────────────────────────────────────────────────────────────────
def test_perfect_agreement_is_one():
    assert spearman([2, 1, 0], [2, 1, 0]) == pytest.approx(1.0)


def test_perfect_disagreement_is_minus_one():
    assert spearman([0.1, 0.5, 0.9], [2, 1, 0]) == pytest.approx(-1.0)


def test_ties_use_average_ranks():
    # Two strongs tie at score, one none below. Monotonic -> rho 1.0 despite the tie.
    assert spearman([0.9, 0.9, 0.1], [2, 2, 0]) == pytest.approx(1.0)


def test_constant_series_has_no_correlation():
    assert spearman([0.5, 0.5, 0.5], [2, 1, 0]) is None


def test_empty_series_is_none_not_zero():
    assert spearman([], []) is None


# ── band thresholds + confusion ───────────────────────────────────────────────
def test_band_thresholds():
    assert band_for_score(0.9) == "strong"
    assert band_for_score(0.65) == "strong"
    assert band_for_score(0.5) == "weak"
    assert band_for_score(0.4) == "weak"
    assert band_for_score(0.39) == "none"


def test_confusion_counts_land_on_the_right_cell():
    m = confusion(["strong", "weak", "none"], ["strong", "strong", "none"])
    assert m["strong"]["strong"] == 1
    assert m["strong"]["weak"] == 1  # gold strong, predicted weak
    assert m["none"]["none"] == 1


# ── gold set shape ────────────────────────────────────────────────────────────
def test_gold_set_has_the_promised_15_labeled_companies():
    assert len(GOLD) == 15
    assert band_counts() == {"strong": 7, "weak": 4, "none": 4}


# ── offline gate ──────────────────────────────────────────────────────────────
def test_offline_reports_readiness_without_a_number():
    r = run_eval(offline=True)
    assert r["spearman"] is None
    assert r["confusion"] is None
    assert r["total_rows"] == 15
    assert r["band_counts"]["strong"] == 7


def test_report_says_not_measured_when_offline():
    assert "not measured" in format_report(run_eval(offline=True))


# ── full run with a scripted model ────────────────────────────────────────────
def _turn_for_band(band: str):
    v = {"strong": 0.9, "weak": 0.5, "none": 0.1}[band]
    return [FakeToolUse("record_fit_score", {
        "firmographic_score": v, "technographic_score": v,
        "behavioral_score": v, "timing_score": v,
        "dimension_reasoning": {k: "r" for k in
                                ("firmographic", "technographic", "behavioral", "timing")},
        "cited_signals": ["s"], "reasoning": "r",
    }, id=f"tu-{band}")]


def test_full_run_with_a_perfect_scorer_passes_the_gate():
    # One scripted turn per gold company, each landing in its own band.
    turns = [_turn_for_band(band) for band, _ in GOLD]
    client = ScriptedClient(*turns)

    r = run_eval(client=client, icp_provider=ICP)

    assert r["mode"] == "full"
    assert r["scored_rows"] == 15
    assert r["spearman"] == pytest.approx(1.0)
    assert r["accuracy"] == pytest.approx(1.0)
    # Confusion is purely diagonal.
    assert r["confusion"]["strong"]["strong"] == 7
    assert r["confusion"]["weak"]["weak"] == 4
    assert r["confusion"]["none"]["none"] == 4


def test_full_run_report_shows_the_gate_passing():
    turns = [_turn_for_band(band) for band, _ in GOLD]
    report = format_report(run_eval(client=ScriptedClient(*turns), icp_provider=ICP))
    assert "✅" in report


def test_one_bad_row_does_not_sink_the_run():
    class Boom:
        messages = property(lambda self: self)
        def create(self, **kw):
            raise RuntimeError("model down")

    r = run_eval(client=Boom(), icp_provider=ICP)
    assert r["errored_rows"] == 15
    assert r["scored_rows"] == 0
    assert r["spearman"] is None  # nothing scored -> no fabricated correlation
