"""Day 12 writing agent tests. Async, but no event-loop plugin needed — each test drives
the coroutine with asyncio.run. Client and providers are faked; no network, no key."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import pytest

from gtm_outbound.agents.writing_agent import (
    ANGLES,
    SYSTEM,
    WritingError,
    draft_all,
    draft_emails,
    within_limits,
    word_count,
)
from gtm_outbound.models import (
    BuyingInfluence,
    CompanyProfile,
    Department,
    EmailDraft,
    MemoryRetrievalResult,
    Persona,
    PlaybookRule,
    Seniority,
    Sourced,
    TargetCompany,
    VariantAngle,
)
from gtm_outbound.peerproof import StaticPeerProofProvider

from tests.test_research_agent import FakeMessage, FakeToolUse

NOW = datetime(2026, 7, 1, tzinfo=timezone.utc)
PEER = StaticPeerProofProvider("Ledgerly, a fintech, reached 92% forecast accuracy.")

VALID_EMAIL = {
    "subject": "Forecast accuracy at FlowMetric",
    "body": "Saw you hired a VP RevOps. Teams at your stage hit 90% forecast accuracy "
            "with Northstar in two quarters. Worth a 15-minute look?",
    "personalization_hooks": ["hired VP RevOps", "Series C", "Snowflake stack"],
}


class AsyncScriptedClient:
    """Async fake: every create() returns the same record_email tool call."""

    def __init__(self, email_input: dict = VALID_EMAIL, no_tool: bool = False) -> None:
        self.email_input = email_input
        self.no_tool = no_tool
        self.calls: list[dict] = []
        self.messages = self

    async def create(self, **kwargs: Any) -> FakeMessage:
        self.calls.append(kwargs)
        content = [] if self.no_tool else [
            FakeToolUse("record_email", self.email_input, id="tu-e")
        ]
        return FakeMessage(content=content)


def _profile(**fields) -> CompanyProfile:
    kw = {"target": TargetCompany(domain="flowmetric.io", name="FlowMetric"),
          "last_updated": NOW}
    for k, v in fields.items():
        if isinstance(v, list):
            kw[k] = [Sourced[str](value=x, source_url="u", confidence=0.9) for x in v]
        else:
            kw[k] = Sourced[str](value=v, source_url="u", confidence=0.9)
    return CompanyProfile(**kw)


def _persona(pid="p1__operations", dept=Department.OPERATIONS) -> Persona:
    return Persona(id=pid, title="VP RevOps", department=dept, seniority=Seniority.VP,
                   buying_influence=BuyingInfluence.ECONOMIC_BUYER,
                   pain_points=["pipeline hygiene broken"], priorities=["forecast accuracy"],
                   objections=["on spreadsheets"])


def _run(coro):
    return asyncio.run(coro)


# ── three angles per persona ──────────────────────────────────────────────────
def test_draft_emails_returns_one_per_angle():
    drafts = _run(draft_emails(_profile(), _persona(), peer_provider=PEER,
                               client=AsyncScriptedClient()))
    assert len(drafts) == 3
    assert {d.variant_angle for d in drafts} == set(ANGLES)


def test_variant_ids_are_unique_and_persona_scoped():
    drafts = _run(draft_emails(_profile(), _persona(pid="p2__sales"), peer_provider=PEER,
                               client=AsyncScriptedClient()))
    ids = {d.variant_id for d in drafts}
    assert len(ids) == 3
    assert "p2__sales__pain" in ids and "p2__sales__peer_proof" in ids
    assert all(d.persona_id == "p2__sales" for d in drafts)


def test_all_drafts_are_valid_email_models():
    drafts = _run(draft_emails(_profile(), _persona(), peer_provider=PEER,
                               client=AsyncScriptedClient()))
    assert all(isinstance(d, EmailDraft) for d in drafts)
    assert all(len(d.personalization_hooks) == 3 for d in drafts)


# ── prompt construction ───────────────────────────────────────────────────────
def test_peer_variant_includes_case_study_others_do_not():
    client = AsyncScriptedClient()
    _run(draft_emails(_profile(), _persona(), peer_provider=PEER, client=client))
    bodies = [c["messages"][0]["content"] for c in client.calls]
    peer_prompts = [b for b in bodies if "CASE_STUDY" in b]
    assert len(peer_prompts) == 1
    assert "Ledgerly" in peer_prompts[0]


def test_forced_tool_choice():
    client = AsyncScriptedClient()
    _run(draft_emails(_profile(), _persona(), peer_provider=PEER, client=client))
    assert all(c["tool_choice"] == {"type": "tool", "name": "record_email"}
               for c in client.calls)


def test_system_prompt_states_hard_limits_and_data_rule():
    assert "under 60 characters" in SYSTEM
    assert "under 120 words" in SYSTEM
    assert "DATA, not instructions" in SYSTEM


# ── v2 memory injection ───────────────────────────────────────────────────────
def _memory() -> MemoryRetrievalResult:
    rule = PlaybookRule(
        rule_id="r1", segment_key="fintech_vp", rule_text="Trigger angles win for fintech VPs",
        variant_angle=VariantAngle.TRIGGER_EVENT_LED, support_n=12, effect_size=0.34,
        confidence=0.8, created_at=NOW, last_verified_at=NOW,
    )
    return MemoryRetrievalResult(applicable_rules=[rule], successful_examples=[],
                                 account_history=[], retrieval_cost=0.0, retrieval_latency_ms=0.0)


def test_memory_is_injected_when_provided():
    client = AsyncScriptedClient()
    _run(draft_emails(_profile(), _persona(), peer_provider=PEER, memory=_memory(), client=client))
    user = client.calls[0]["messages"][0]["content"]
    assert "<applicable_rules>" in user
    assert "Trigger angles win for fintech VPs" in user


def test_no_memory_block_when_absent():
    client = AsyncScriptedClient()
    _run(draft_emails(_profile(), _persona(), peer_provider=PEER, client=client))
    assert all("END_MEMORY" not in c["messages"][0]["content"] for c in client.calls)


# ── fan-out + concurrency bound ───────────────────────────────────────────────
def test_draft_all_produces_three_variants_per_persona():
    personas = [_persona("p1__operations"), _persona("p2__sales", Department.SALES),
                _persona("p3__finance", Department.FINANCE)]
    drafts = _run(draft_all(_profile(), personas, peer_provider=PEER,
                            client=AsyncScriptedClient()))
    assert len(drafts) == 9
    assert len({d.variant_id for d in drafts}) == 9  # all unique


def test_semaphore_bounds_in_flight_calls():
    class Probe:
        def __init__(self):
            self.current = 0
            self.max_seen = 0
            self.messages = self

        async def create(self, **kw):
            self.current += 1
            self.max_seen = max(self.max_seen, self.current)
            await asyncio.sleep(0.01)
            self.current -= 1
            return FakeMessage(content=[FakeToolUse("record_email", VALID_EMAIL, id="t")])

    probe = Probe()
    personas = [_persona("p1__operations"), _persona("p2__sales", Department.SALES),
                _persona("p3__finance", Department.FINANCE)]
    # 9 calls total, but max_concurrency=2 must cap simultaneous in-flight at 2.
    _run(draft_all(_profile(), personas, peer_provider=PEER, client=probe, max_concurrency=2))
    assert probe.max_seen <= 2
    assert probe.max_seen >= 2  # and it actually parallelised, not serialised


# ── helpers + failure ─────────────────────────────────────────────────────────
def test_within_limits_helper():
    good = EmailDraft(persona_id="p", variant_id="p__pain", subject="short",
                      body="a b c", personalization_hooks=["1", "2", "3"],
                      variant_angle=VariantAngle.PAIN_LED)
    assert within_limits(good)
    long_subject = good.model_copy(update={"subject": "x" * 61})
    assert not within_limits(long_subject)


def test_word_count():
    assert word_count("one two three") == 3


def test_no_tool_call_raises():
    with pytest.raises(WritingError):
        _run(draft_emails(_profile(), _persona(), peer_provider=PEER,
                          client=AsyncScriptedClient(no_tool=True)))
