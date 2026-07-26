"""Peer-proof provider tests: the right case study, or a loud failure."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from gtm_outbound.models import CompanyProfile, Sourced, TargetCompany
from gtm_outbound.peerproof import (
    KBPeerProofProvider,
    PeerProofNotFoundError,
    StaticPeerProofProvider,
)

NOW = datetime(2026, 7, 1, tzinfo=timezone.utc)


def _profile(industry=None, sub=None) -> CompanyProfile:
    kw = {"target": TargetCompany(domain="x.com", name="X"), "last_updated": NOW}
    if industry:
        kw["industry"] = Sourced[str](value=industry, source_url="u", confidence=0.9)
    if sub:
        kw["sub_industry"] = Sourced[str](value=sub, source_url="u", confidence=0.9)
    return CompanyProfile(**kw)


def test_fintech_profile_gets_the_fintech_case_study():
    proof = KBPeerProofProvider().get_case_study(_profile(sub="fintech infrastructure"))
    assert "series-c-fintech.md" in proof.source
    assert proof.matched_segment == "fintech"
    assert len(proof.text) > 100


def test_devtools_profile_gets_the_devtools_case_study():
    proof = KBPeerProofProvider().get_case_study(_profile(sub="developer tools"))
    assert "series-b-devtools.md" in proof.source
    assert proof.matched_segment == "developer"


def test_unmatched_profile_falls_back_to_the_default_case_study():
    proof = KBPeerProofProvider().get_case_study(_profile(industry="logistics SaaS"))
    assert "series-d-vertical-saas.md" in proof.source
    assert proof.matched_segment == "default"


def test_missing_case_dir_raises(tmp_path):
    with pytest.raises(PeerProofNotFoundError):
        KBPeerProofProvider(case_dir=tmp_path).get_case_study(_profile(sub="fintech"))


def test_static_provider_returns_given_text():
    proof = StaticPeerProofProvider("case text", source="s").get_case_study(_profile())
    assert proof.text == "case text" and proof.source == "s"
