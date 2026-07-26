"""Day 13 Account Brief tests: assembly + markdown rendering, fully offline (no LLM)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from gtm_outbound.brief import assemble_brief, render_brief_md, would_send_pass_rate
from gtm_outbound.models import (
    BuyingInfluence,
    CompanyProfile,
    Department,
    EmailDraft,
    EmailEval,
    FitScore,
    Persona,
    Seniority,
    Sourced,
    TargetCompany,
    VariantAngle,
)

NOW = datetime(2026, 7, 1, tzinfo=timezone.utc)


def _profile() -> CompanyProfile:
    def s(v):
        return Sourced[str](value=v, source_url="https://acme.com/x", confidence=0.9)
    return CompanyProfile(target=TargetCompany(domain="acme.com", name="Acme"),
                          last_updated=NOW, industry=s("B2B SaaS"), size_band=s("500-1000"),
                          tech_stack=[s("Salesforce")])


def _fit() -> FitScore:
    return FitScore(score=0.82, firmographic_score=0.9, technographic_score=0.8,
                    behavioral_score=0.8, timing_score=0.7, reasoning="Strong fit overall.",
                    cited_signals=["size_band: 500-1000", "Salesforce"])


def _persona(pid="p1__operations") -> Persona:
    return Persona(id=pid, title="VP RevOps", department=Department.OPERATIONS,
                   seniority=Seniority.VP, buying_influence=BuyingInfluence.ECONOMIC_BUYER,
                   pain_points=["pipeline hygiene"], priorities=["forecast accuracy"],
                   objections=["spreadsheets"])


def _draft(angle, send_id) -> EmailDraft:
    return EmailDraft(persona_id="p1__operations",
                      variant_id=f"p1__operations__{angle.value}",
                      subject=f"Subject {angle.value}", body="Body text here.",
                      personalization_hooks=["h1", "h2", "h3"], variant_angle=angle)


def _eval(send=True, spam=1.0) -> EmailEval:
    return EmailEval(personalization_score=4, relevance_score=4, cta_score=4,
                     spam_risk=spam, would_send=send, reasoning="ok")


def _brief(sends=(True, True, False)):
    drafts = [_draft(a, i) for i, a in enumerate(
        (VariantAngle.PAIN_LED, VariantAngle.TRIGGER_EVENT_LED, VariantAngle.PEER_PROOF))]
    evals = {d.variant_id: _eval(send=s) for d, s in zip(drafts, sends)}
    return assemble_brief(_profile(), _fit(), [_persona()], drafts, evals,
                          cost_usd=0.1234, latency_ms=4200.0, timestamp=NOW)


# ── assembly ──────────────────────────────────────────────────────────────────
def test_emails_and_evals_are_keyed_by_variant_id():
    b = _brief()
    assert set(b.emails) == set(b.evals)
    assert len(b.emails) == 3
    assert len(b.emails_for_persona("p1__operations")) == 3


def test_would_send_pass_rate():
    assert would_send_pass_rate(_brief(sends=(True, True, False))) == pytest.approx(2 / 3)
    assert would_send_pass_rate(_brief(sends=(True, True, True))) == pytest.approx(1.0)


def test_pass_rate_is_none_when_nothing_evaluated():
    b = _brief()
    b.evals.clear()
    assert would_send_pass_rate(b) is None


# ── rendering ─────────────────────────────────────────────────────────────────
def test_render_has_all_required_sections():
    md = render_brief_md(_brief())
    for heading in ("# Account Brief", "## Company Summary", "## ICP Fit",
                    "## Personas", "## Emails", "## Cost & Latency"):
        assert heading in md


def test_render_puts_pass_rate_at_the_top():
    md = render_brief_md(_brief(sends=(True, True, False)))
    header = md.split("## Company Summary")[0]
    assert "Would-send pass rate: 67%" in header


def test_render_shows_per_email_verdicts():
    md = render_brief_md(_brief(sends=(True, False, True)))
    assert "✅ send" in md and "❌ hold" in md


def test_render_shows_cost_and_latency():
    md = render_brief_md(_brief())
    assert "$0.1234" in md
    assert "4200 ms" in md


def test_render_marks_unfound_fields_not_fabricated():
    md = render_brief_md(_brief())
    assert "_not found_" in md  # funding_stage/sub_industry were never set


def test_render_is_valid_nonempty_markdown():
    md = render_brief_md(_brief())
    assert md.startswith("# Account Brief — Acme")
    assert md.endswith("\n")
