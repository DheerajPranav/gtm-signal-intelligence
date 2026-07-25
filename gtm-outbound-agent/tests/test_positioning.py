"""Positioning provider tests: persona grounding comes from the KB, or fails loudly."""

from __future__ import annotations

import pytest

from gtm_outbound.positioning import (
    POSITIONING_TERMS,
    KBPositioningProvider,
    PositioningNotFoundError,
    StaticPositioningProvider,
    _DEFAULT_DOCS,
)


def test_kb_provider_reads_real_positioning_and_persona_docs():
    g = KBPositioningProvider().get_positioning()
    assert "warehouse-native" in g.text.lower()
    assert "forecast accuracy" in g.text.lower()
    assert len(g.sources) == 3
    assert any("positioning.md" in s for s in g.sources)


def test_sources_are_repo_relative():
    for s in KBPositioningProvider().get_positioning().sources:
        assert "gtm-knowledge-base" in s
        assert not s.startswith("/")


def test_missing_doc_raises_rather_than_paraphrasing(tmp_path):
    provider = KBPositioningProvider(doc_paths=(tmp_path / "missing.md",))
    with pytest.raises(PositioningNotFoundError):
        provider.get_positioning()


def test_vocabulary_terms_actually_appear_in_the_corpus():
    """Drift guard: POSITIONING_TERMS must stay grounded in positioning.md itself, or the
    lexical proxy would be checking for words the KB never uses."""
    positioning_md = next(p for p in _DEFAULT_DOCS if p.name == "positioning.md")
    text = positioning_md.read_text(encoding="utf-8").lower()
    for term in POSITIONING_TERMS:
        assert term in text, f"{term!r} no longer in positioning.md"


def test_static_provider_returns_given_text():
    g = StaticPositioningProvider("pos text", sources=("t",)).get_positioning()
    assert g.text == "pos text" and g.sources == ("t",)
