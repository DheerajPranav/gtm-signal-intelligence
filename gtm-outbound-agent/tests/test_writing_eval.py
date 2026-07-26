"""Day 12 writing-eval tests: metric arithmetic, hook-traceability proxy, and the gate."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "evals"))

from run_writing_eval import (  # noqa: E402
    eval_personas,
    eval_profile,
    format_report,
    hook_traceable,
    run_eval,
    score_drafts,
)

from gtm_outbound.models import EmailDraft, VariantAngle
from gtm_outbound.peerproof import StaticPeerProofProvider

from tests.test_research_agent import FakeMessage, FakeToolUse
from tests.test_writing_agent import VALID_EMAIL

PEER = StaticPeerProofProvider("Ledgerly fintech 92% forecast accuracy")


class AsyncClient:
    def __init__(self, email=VALID_EMAIL):
        self.email = email
        self.messages = self

    async def create(self, **kw):
        return FakeMessage(content=[FakeToolUse("record_email", self.email, id="t")])


def _draft(vid, angle, subject="s", body="a b c", hooks=("1", "2", "3")):
    return EmailDraft(persona_id=vid.split("__")[0], variant_id=vid, subject=subject,
                      body=body, personalization_hooks=list(hooks), variant_angle=angle)


# ── hook traceability proxy ───────────────────────────────────────────────────
def test_hook_grounded_in_source_is_traceable():
    src = {"revops", "snowflake", "series", "c"}
    assert hook_traceable("hired a RevOps leader on Snowflake", src) is True


def test_hook_with_no_source_overlap_is_not_traceable():
    assert hook_traceable("great weather today", {"revops", "snowflake"}) is False


def test_single_word_overlap_is_not_enough():
    assert hook_traceable("snowflake somewhere", {"snowflake"}) is False


# ── score_drafts arithmetic ───────────────────────────────────────────────────
def test_full_9_email_run_scores_perfectly():
    drafts = [
        _draft(f"p{p}__{a.value}", a)
        for p in range(1, 4) for a in VariantAngle.__members__.values()
        if a in (VariantAngle.PAIN_LED, VariantAngle.TRIGGER_EVENT_LED, VariantAngle.PEER_PROOF)
    ]
    r = score_drafts(drafts, {"a", "b", "c"}, n_personas=3)
    assert r["emails"] == 9
    assert r["angle_coverage"] == pytest.approx(1.0)
    assert r["subject_ok"] == 1.0 and r["body_ok"] == 1.0 and r["hooks_ok"] == 1.0


def test_over_length_subject_and_body_are_flagged():
    bad = [_draft("p1__pain", VariantAngle.PAIN_LED, subject="x" * 61, body="w " * 200)]
    r = score_drafts(bad, {"x"}, n_personas=1)
    assert r["subject_ok"] == 0.0
    assert r["body_ok"] == 0.0


def test_missing_angle_drops_coverage():
    two = [_draft("p1__pain", VariantAngle.PAIN_LED),
           _draft("p1__trigger", VariantAngle.TRIGGER_EVENT_LED)]  # no peer_proof
    r = score_drafts(two, {"a"}, n_personas=1)
    assert r["angle_coverage"] == 0.0


# ── fixtures ──────────────────────────────────────────────────────────────────
def test_fixture_has_a_profile_and_three_personas():
    assert eval_profile().target.domain == "flowmetric.io"
    assert len(eval_personas()) == 3


# ── gate ──────────────────────────────────────────────────────────────────────
def test_offline_reports_readiness_without_numbers():
    r = run_eval(offline=True)
    assert r["emails"] is None
    assert r["expected_emails"] == 9


def test_report_says_not_measured_offline():
    assert "not measured" in format_report(run_eval(offline=True))


def test_full_run_with_fake_client_produces_nine_scored_emails():
    r = run_eval(client=AsyncClient(), peer_provider=PEER)
    assert r["mode"] == "full"
    assert r["emails"] == 9
    assert r["angle_coverage"] == pytest.approx(1.0)
    assert r["wall_clock_s"] is not None
    assert r["under_90s"] is True


def test_full_run_hooks_trace_to_the_profile():
    # VALID_EMAIL hooks mention "VP RevOps", "Series C", "Snowflake" — all in the fixture.
    r = run_eval(client=AsyncClient(), peer_provider=PEER)
    assert r["hook_traceability"] > 0.0
