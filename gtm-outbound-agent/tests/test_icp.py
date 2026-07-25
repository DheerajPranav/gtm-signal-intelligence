"""ICP provider tests: the scoring agent grounds on the KB, or fails loudly."""

from __future__ import annotations

from pathlib import Path

import pytest

from gtm_outbound.icp import (
    ICPNotFoundError,
    KBICPProvider,
    StaticICPProvider,
    _DEFAULT_ICP_DOC,
)


def test_kb_provider_reads_the_real_canonical_icp():
    grounding = KBICPProvider().get_icp()
    # Content the rubric depends on — proves we read the actual corpus, not a stub.
    assert "Ideal Customer Profile" in grounding.text
    assert "Series B" in grounding.text
    assert "warehouse" in grounding.text.lower()


def test_kb_provider_cites_a_repo_relative_source():
    source = KBICPProvider().get_icp().source
    assert source.endswith("icp-definition.md")
    assert "gtm-knowledge-base" in source
    assert not Path(source).is_absolute()  # travels with the score, not machine-specific


def test_missing_icp_doc_raises_rather_than_inventing_a_rubric(tmp_path):
    provider = KBICPProvider(doc_path=tmp_path / "nope.md")
    with pytest.raises(ICPNotFoundError):
        provider.get_icp()


def test_default_icp_doc_points_into_the_knowledge_base():
    assert _DEFAULT_ICP_DOC.name == "icp-definition.md"
    assert "gtm-knowledge-base" in str(_DEFAULT_ICP_DOC)


def test_static_provider_returns_what_it_was_given():
    g = StaticICPProvider("some icp text", source="unit-test").get_icp()
    assert g.text == "some icp text"
    assert g.source == "unit-test"
