"""Day 13 end-to-end pipeline test. All five agents wired together with faked clients —
no network, no key — proving research -> score -> persona -> write -> critique -> brief
composes and writes a file. Order-independent: the fake routes by the forced tool name."""

from __future__ import annotations

import asyncio
from typing import Any

from gtm_outbound.icp import StaticICPProvider
from gtm_outbound.peerproof import StaticPeerProofProvider
from gtm_outbound.pipeline import run_company
from gtm_outbound.positioning import StaticPositioningProvider

from tests.test_research_agent import FakeMessage, FakeProvider, FakeToolUse

_SRC = {"value": "B2B SaaS", "source_url": "https://x/a", "confidence": 0.9}
_PERSONA_CARD = {
    "title": "VP RevOps", "department": "operations", "seniority": "vp",
    "buying_influence": "economic_buyer",
    "pain_points": ["pipeline hygiene"], "priorities": ["forecast accuracy"],
    "objections": ["spreadsheets"],
}

CANNED: dict[str, dict] = {
    "record_profile": {"industry": _SRC, "size_band": {**_SRC, "value": "500-1000"}},
    "record_fit_score": {
        "firmographic_score": 0.9, "technographic_score": 0.8,
        "behavioral_score": 0.8, "timing_score": 0.7,
        "dimension_reasoning": {k: "r" for k in
                                ("firmographic", "technographic", "behavioral", "timing")},
        "cited_signals": ["size_band: 500-1000"], "reasoning": "strong",
    },
    "record_personas": {"personas": [
        {**_PERSONA_CARD, "title": "VP RevOps", "department": "operations"},
        {**_PERSONA_CARD, "title": "VP Sales", "department": "sales"},
        {**_PERSONA_CARD, "title": "CRO", "department": "finance"},
    ]},
    "record_email": {"subject": "Forecast accuracy at Acme",
                     "body": "Short relevant body.",
                     "personalization_hooks": ["hired VP RevOps", "Series C", "Snowflake"]},
    "record_evaluation": {"personalization_score": 4.0, "relevance_score": 4.0,
                          "cta_score": 4.0, "spam_risk": 1.0, "would_send": True,
                          "reasoning": "solid"},
}


def _tool_name(kwargs: dict, default: str) -> str:
    tc = kwargs.get("tool_choice")
    if isinstance(tc, dict) and tc.get("type") == "tool":
        return tc["name"]
    return default  # research's 'auto' turn -> finish by recording the profile


class RoutingClient:
    """Sync fake: returns the canned tool_use matching the forced tool. Stateless (thread-safe
    for the concurrent critiques)."""
    def __init__(self):
        self.messages = self

    def create(self, **kwargs: Any) -> FakeMessage:
        name = _tool_name(kwargs, "record_profile")
        return FakeMessage(content=[FakeToolUse(name, CANNED[name], id=f"tu-{name}")])


class AsyncRoutingClient:
    def __init__(self):
        self.messages = self

    async def create(self, **kwargs: Any) -> FakeMessage:
        name = _tool_name(kwargs, "record_email")
        return FakeMessage(content=[FakeToolUse(name, CANNED[name], id=f"tu-{name}")])


def test_run_company_produces_a_complete_brief_and_file(tmp_path):
    brief, path = asyncio.run(run_company(
        "acme.com", FakeProvider(),
        icp_provider=StaticICPProvider("ICP text"),
        positioning_provider=StaticPositioningProvider("positioning"),
        peer_provider=StaticPeerProofProvider("case study"),
        sync_client=RoutingClient(),
        async_client=AsyncRoutingClient(),
        runs_dir=tmp_path,
    ))

    # 3 personas x 3 variants = 9 emails, every one critiqued.
    assert len(brief.personas) == 3
    assert len(brief.emails) == 9
    assert len(brief.evals) == 9
    assert set(brief.emails) == set(brief.evals)  # joined by variant_id

    # File written and renders as a brief.
    assert path.exists()
    md = path.read_text(encoding="utf-8")
    assert md.startswith("# Account Brief — acme.com")
    assert "Would-send pass rate:" in md
    assert "## Emails" in md


def test_run_company_measures_real_latency(tmp_path):
    brief, _ = asyncio.run(run_company(
        "acme.com", FakeProvider(),
        icp_provider=StaticICPProvider("ICP"),
        positioning_provider=StaticPositioningProvider("pos"),
        peer_provider=StaticPeerProofProvider("case"),
        sync_client=RoutingClient(), async_client=AsyncRoutingClient(),
        runs_dir=tmp_path,
    ))
    assert brief.latency_ms > 0  # real wall-clock, not a placeholder
