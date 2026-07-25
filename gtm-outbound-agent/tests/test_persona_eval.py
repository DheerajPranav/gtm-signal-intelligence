"""Day 11 persona-eval tests: metric arithmetic, grounding proxy, and the gate."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "evals"))

from run_persona_eval import (  # noqa: E402
    distinctness,
    eval_profiles,
    format_report,
    is_grounded,
    run_eval,
)

from gtm_outbound.models import BuyingInfluence, Department, Persona, Seniority
from gtm_outbound.positioning import StaticPositioningProvider

from tests.test_research_agent import FakeToolUse, ScriptedClient

POS = StaticPositioningProvider("positioning")


def _persona(pains, prios=("forecast accuracy",)) -> Persona:
    return Persona(
        id="p1__operations", title="VP RevOps", department=Department.OPERATIONS,
        seniority=Seniority.VP, pain_points=list(pains), priorities=list(prios),
        objections=["o"], buying_influence=BuyingInfluence.ECONOMIC_BUYER,
    )


# ── grounding proxy ───────────────────────────────────────────────────────────
def test_card_using_northstar_language_is_grounded():
    assert is_grounded(_persona(["pipeline hygiene is a mess"])) is True


def test_generic_card_is_not_grounded():
    assert is_grounded(_persona(["they want more revenue"], prios=["grow fast"])) is False


# ── distinctness ──────────────────────────────────────────────────────────────
def test_identical_pain_vocab_is_zero_distance():
    assert distinctness([{"a", "b"}, {"a", "b"}]) == pytest.approx(0.0)


def test_disjoint_pain_vocab_is_max_distance():
    assert distinctness([{"a", "b"}, {"c", "d"}]) == pytest.approx(1.0)


def test_distinctness_needs_two_companies():
    assert distinctness([{"a"}]) is None


# ── fixtures ──────────────────────────────────────────────────────────────────
def test_eval_uses_contrasting_industries():
    profiles = eval_profiles()
    assert len(profiles) >= 3
    industries = {p.industry.value for p in profiles if p.industry}
    subs = {p.sub_industry.value for p in profiles if p.sub_industry}
    assert len(subs) >= 3  # genuinely different companies, not near-duplicates


# ── offline gate ──────────────────────────────────────────────────────────────
def test_offline_reports_readiness_without_numbers():
    r = run_eval(offline=True)
    assert r["count_ok"] is None
    assert r["kb_grounding"] is None
    assert r["companies"] >= 3


def test_report_says_not_measured_offline():
    assert "not measured" in format_report(run_eval(offline=True))


# ── full scripted run ─────────────────────────────────────────────────────────
def _turn(pain_word: str):
    # 3 complete cards; each priority carries a positioning term -> grounded.
    cards = [{
        "title": f"Role {i}", "department": "operations", "seniority": "vp",
        "buying_influence": "economic_buyer",
        "pain_points": [f"{pain_word} pain {i}"],
        "priorities": ["forecast accuracy"], "objections": ["o"],
    } for i in range(3)]
    return [FakeToolUse("record_personas", {"personas": cards}, id=f"tu-{pain_word}")]


def test_full_run_scores_all_dimensions():
    n_companies = len(eval_profiles())
    # Distinct pain vocab per company so distinctness > 0.
    turns = [_turn(f"word{i}") for i in range(n_companies)]
    r = run_eval(client=ScriptedClient(*turns), positioning_provider=POS)

    assert r["mode"] == "full"
    assert r["scored_companies"] == n_companies
    assert r["count_ok"] == pytest.approx(1.0)     # every company returned 3 complete cards
    assert r["kb_grounding"] == pytest.approx(1.0)  # all grounded via "forecast accuracy"
    assert r["distinctness"] > 0.0                  # cards differ across companies


def test_one_bad_company_does_not_sink_the_run():
    class Boom:
        messages = property(lambda self: self)
        def create(self, **kw):
            raise RuntimeError("model down")

    r = run_eval(client=Boom(), positioning_provider=POS)
    assert r["errored_companies"] == len(eval_profiles())
    assert r["count_ok"] is None  # nothing scored -> no fabricated number
