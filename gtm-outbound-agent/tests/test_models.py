"""Day 8 model tests: schema strictness, score bounds, and the memory-write policy."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from gtm_outbound.models import (
    EPISODIC_MAX_SPAM_RISK,
    EPISODIC_MIN_PERSONALIZATION,
    AccountBrief,
    BuyingInfluence,
    CompanyProfile,
    Department,
    EmailDraft,
    EmailEval,
    FitScore,
    Persona,
    PlaybookRule,
    SemanticFact,
    FactType,
    Seniority,
    Sourced,
    TargetCompany,
    VariantAngle,
    decide_memory_write,
)

NOW = datetime(2026, 7, 24, 12, 0, 0)


def _s(value: str, url: str = "https://acme.com/about", conf: float = 0.9) -> Sourced[str]:
    return Sourced[str](value=value, source_url=url, confidence=conf)


def _profile() -> CompanyProfile:
    return CompanyProfile(
        target=TargetCompany(domain="acme.com", name="Acme"),
        industry=_s("fintech"),
        sub_industry=_s("payments"),
        size_band=_s("200-500"),
        funding_stage=_s("Series C"),
        tech_stack=[_s("Salesforce"), _s("Snowflake")],
        recent_news=[_s("raised $40M")],
        key_people=[_s("Jane Doe")],
        buying_signals=[_s("hired VP RevOps")],
        last_updated=NOW,
    )


def _persona(pid: str = "p1") -> Persona:
    return Persona(
        id=pid,
        title="VP RevOps",
        department=Department.OPERATIONS,
        seniority=Seniority.VP,
        pain_points=["forecast accuracy"],
        priorities=["pipeline hygiene"],
        objections=["price"],
        buying_influence=BuyingInfluence.ECONOMIC_BUYER,
    )


def _draft(variant_id: str, persona_id: str = "p1") -> EmailDraft:
    return EmailDraft(
        persona_id=persona_id,
        variant_id=variant_id,
        subject="Quick question",
        body="Body text.",
        personalization_hooks=["recent raise"],
        variant_angle=VariantAngle.TRIGGER_EVENT_LED,
    )


def _eval(pers=4.5, rel=4.5, cta=4.0, spam=1.0, send=True) -> EmailEval:
    return EmailEval(
        personalization_score=pers,
        relevance_score=rel,
        cta_score=cta,
        spam_risk=spam,
        would_send=send,
        reasoning="test",
    )


# ── schema strictness ─────────────────────────────────────────────────────────
def test_models_reject_unknown_fields():
    with pytest.raises(ValidationError):
        TargetCompany(domain="acme.com", name="Acme", unexpected="nope")


def test_fit_score_bounds_are_enforced():
    with pytest.raises(ValidationError):
        FitScore(
            score=1.5, firmographic_score=0.5, technographic_score=0.5,
            behavioral_score=0.5, timing_score=0.5, reasoning="r",
        )


def test_email_eval_rejects_scores_above_five():
    with pytest.raises(ValidationError):
        _eval(pers=6.0)


def test_playbook_rule_rejects_negative_support():
    with pytest.raises(ValidationError):
        PlaybookRule(
            rule_id="r1", segment_key="fintech_vp", rule_text="t",
            variant_angle=VariantAngle.PAIN_LED, support_n=-1,
            effect_size=0.3, confidence=0.7, created_at=NOW, last_verified_at=NOW,
        )


def test_enums_reject_unknown_members():
    payload = _persona().model_dump()
    payload["seniority"] = "emperor"
    with pytest.raises(ValidationError):
        Persona.model_validate(payload)


# ── AccountBrief keying ───────────────────────────────────────────────────────
def test_multiple_variants_per_persona_all_survive():
    """Regression: keying emails by persona_id dropped every variant but the last."""
    drafts = {v: _draft(v) for v in ("p1__pain", "p1__trigger", "p1__peer")}
    brief = AccountBrief(
        target=TargetCompany(domain="acme.com", name="Acme"),
        profile=_profile(),
        fit=FitScore(
            score=0.8, firmographic_score=0.9, technographic_score=0.8,
            behavioral_score=0.7, timing_score=0.8, reasoning="strong fit",
        ),
        personas=[_persona()],
        emails=drafts,
        evals={v: _eval() for v in drafts},
        cost_usd=0.12,
        latency_ms=4200.0,
        timestamp=NOW,
    )

    assert len(brief.emails_for_persona("p1")) == 3


def test_every_email_can_be_joined_to_its_eval():
    drafts = {v: _draft(v) for v in ("p1__pain", "p1__trigger")}
    brief = AccountBrief(
        target=TargetCompany(domain="acme.com", name="Acme"),
        profile=_profile(),
        fit=FitScore(
            score=0.8, firmographic_score=0.9, technographic_score=0.8,
            behavioral_score=0.7, timing_score=0.8, reasoning="r",
        ),
        personas=[_persona()],
        emails=drafts,
        evals={"p1__pain": _eval(), "p1__trigger": _eval(pers=2.0)},
        cost_usd=0.1, latency_ms=100.0, timestamp=NOW,
    )

    for variant_id in brief.emails:
        assert brief.eval_for(variant_id) is not None


# ── SemanticFact supersession + staleness ─────────────────────────────────────
def test_superseded_by_points_at_a_real_fact_id():
    """Regression: SemanticFact had no fact_id, so superseded_by dangled."""
    old = SemanticFact(
        fact_id="f1", account_id="acme.com", fact_type=FactType.FUNDING_EVENT,
        value="Series B", source_url="https://x", confidence=0.9,
        observed_at=NOW - timedelta(days=400), superseded_by="f2",
    )
    new = SemanticFact(
        fact_id="f2", account_id="acme.com", fact_type=FactType.FUNDING_EVENT,
        value="Series C", source_url="https://y", confidence=0.95, observed_at=NOW,
    )

    assert old.superseded_by == new.fact_id
    assert not old.is_current
    assert new.is_current


def test_age_days_supports_the_sixty_day_staleness_flag():
    fact = SemanticFact(
        fact_id="f1", account_id="acme.com", fact_type=FactType.LAST_CONTACT,
        value="emailed", source_url="internal", confidence=1.0,
        observed_at=NOW - timedelta(days=90),
    )
    assert fact.age_days(now=NOW) == pytest.approx(90.0)
    assert fact.age_days(now=NOW) > 60


# ── memory write policy ───────────────────────────────────────────────────────
def test_high_quality_draft_enters_episodic_memory():
    d = decide_memory_write(_eval(pers=4.5, rel=4.5, spam=1.0))
    assert d.write_episodic is True
    assert d.write_negative_pattern is False


def test_spam_risk_alone_blocks_episodic_admission():
    d = decide_memory_write(_eval(pers=5.0, rel=5.0, spam=EPISODIC_MAX_SPAM_RISK + 1))
    assert d.write_episodic is False


def test_score_just_below_threshold_is_excluded():
    d = decide_memory_write(_eval(pers=EPISODIC_MIN_PERSONALIZATION - 0.1, rel=5.0))
    assert d.write_episodic is False


def test_threshold_boundary_is_inclusive():
    d = decide_memory_write(_eval(pers=EPISODIC_MIN_PERSONALIZATION, rel=4.0, spam=EPISODIC_MAX_SPAM_RISK))
    assert d.write_episodic is True


def test_rejected_low_scoring_draft_is_stored_as_a_failure_pattern():
    d = decide_memory_write(_eval(pers=1.0, rel=2.0, cta=1.5, spam=4.0, send=False))
    assert d.write_negative_pattern is True
    assert d.write_episodic is False


def test_middling_draft_goes_to_neither_store():
    d = decide_memory_write(_eval(pers=3.0, rel=3.0, cta=3.0, spam=1.0, send=False))
    assert d.write_episodic is False
    assert d.write_negative_pattern is False


def test_semantic_delta_is_always_written():
    for ev in (_eval(), _eval(pers=1.0, rel=1.0, send=False)):
        assert decide_memory_write(ev).write_semantic_delta is True


# ── PlaybookRule lifecycle ────────────────────────────────────────────────────
def test_rules_are_retired_not_deleted():
    rule = PlaybookRule(
        rule_id="r1", segment_key="fintech_vp-revops", rule_text="trigger angles win",
        variant_angle=VariantAngle.TRIGGER_EVENT_LED, support_n=42,
        effect_size=0.34, confidence=0.71, created_at=NOW, last_verified_at=NOW,
    )
    assert rule.is_active
    assert not rule.model_copy(update={"retired_at": NOW}).is_active
