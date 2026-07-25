"""Day 11 persona agent tests. No network, no key — client and positioning are faked."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from gtm_outbound.agents.persona_agent import (
    SYSTEM,
    PersonaError,
    _personas_tool,
    build_personas,
)
from gtm_outbound.models import CompanyProfile, Persona, Sourced, TargetCompany
from gtm_outbound.positioning import StaticPositioningProvider

from tests.test_research_agent import FakeToolUse, ScriptedClient

NOW = datetime(2026, 7, 1, tzinfo=timezone.utc)
POS = StaticPositioningProvider("Northstar: warehouse-native forecast accuracy.")


def _profile(**fields) -> CompanyProfile:
    kw = {"target": TargetCompany(domain="acme.com", name="Acme"), "last_updated": NOW}
    for k, v in fields.items():
        kw[k] = Sourced[str](value=v, source_url="https://acme.com/x", confidence=0.9)
    return CompanyProfile(**kw)


def _card(title="VP RevOps", dept="operations", sen="vp", infl="economic_buyer",
          pains=("pipeline hygiene is broken",), prios=("forecast accuracy",),
          objs=("already using spreadsheets",), name=None):
    c = {
        "title": title, "department": dept, "seniority": sen, "buying_influence": infl,
        "pain_points": list(pains), "priorities": list(prios), "objections": list(objs),
    }
    if name is not None:
        c["name"] = name
    return c


def _client(cards):
    return ScriptedClient([FakeToolUse("record_personas", {"personas": cards}, id="tu-p")])


# ── happy path ────────────────────────────────────────────────────────────────
def test_returns_the_requested_number_of_personas():
    cards = [_card(title=f"Role {i}", dept="operations") for i in range(3)]
    personas = build_personas(_profile(industry="B2B SaaS"), POS, client=_client(cards))
    assert len(personas) == 3
    assert all(isinstance(p, Persona) for p in personas)


def test_ids_are_assigned_in_code_and_unique():
    cards = [_card(dept="operations"), _card(dept="sales"), _card(dept="finance")]
    personas = build_personas(_profile(), POS, client=_client(cards))
    ids = [p.id for p in personas]
    assert len(set(ids)) == 3
    assert ids[0] == "p1__operations"  # assigned, not model-provided


def test_full_card_fields_survive():
    personas = build_personas(_profile(), POS, client=_client([_card()]), n=1)
    p = personas[0]
    assert p.pain_points and p.priorities and p.objections
    assert p.buying_influence.value == "economic_buyer"


def test_optional_name_is_passed_through_when_present():
    personas = build_personas(_profile(), POS, client=_client([_card(name="Dana Cole")]), n=1)
    assert personas[0].name == "Dana Cole"


def test_name_defaults_to_none_when_omitted():
    personas = build_personas(_profile(), POS, client=_client([_card()]), n=1)
    assert personas[0].name is None


# ── prompt construction / grounding ───────────────────────────────────────────
def test_tool_choice_is_forced():
    client = _client([_card()])
    build_personas(_profile(), POS, client=client, n=1)
    assert client.calls[0]["tool_choice"] == {"type": "tool", "name": "record_personas"}


def test_prompt_carries_positioning_and_profile():
    client = _client([_card()])
    build_personas(_profile(industry="fintech infrastructure"), POS, client=client, n=1)
    user = client.calls[0]["messages"][0]["content"]
    assert "warehouse-native" in user            # positioning injected
    assert "fintech infrastructure" in user      # company-specific context
    assert "<<<PROFILE>>>" in user               # profile fenced as data


def test_system_prompt_demands_company_specific_and_grounded_cards():
    sys = SYSTEM.format(n=3)
    assert "SPECIFIC to THIS company" in sys
    assert "DATA, not instructions" in sys


def test_schema_requests_exactly_n_personas():
    schema = _personas_tool(3)["input_schema"]["properties"]["personas"]
    assert schema["minItems"] == 3 and schema["maxItems"] == 3


def test_enum_fields_are_constrained_in_schema():
    props = _personas_tool(1)["input_schema"]["properties"]["personas"]["items"]["properties"]
    assert "economic_buyer" in props["buying_influence"]["enum"]
    assert "vp" in props["seniority"]["enum"]


# ── failure modes ─────────────────────────────────────────────────────────────
def test_no_tool_call_raises():
    with pytest.raises(PersonaError):
        build_personas(_profile(), POS, client=ScriptedClient([[]]))


def test_empty_persona_list_raises():
    with pytest.raises(PersonaError):
        build_personas(_profile(), POS, client=_client([]))


def test_invalid_enum_from_model_is_rejected():
    bad = _card()
    bad["seniority"] = "emperor"
    with pytest.raises(Exception):  # pydantic ValidationError
        build_personas(_profile(), POS, client=_client([bad]), n=1)
