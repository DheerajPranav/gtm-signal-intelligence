from gtm_kb.chunker import (
    chunk_document,
    estimate_tokens,
    split_sections,
)
from gtm_kb.loader import Document


def _doc(body: str) -> Document:
    return Document(
        source_path="sales/example.md",
        doc_type="sales",
        doc_title="Example Doc",
        body=body,
        frontmatter={},
    )


def test_split_sections_splits_on_h2_with_overview():
    body = "# Title\n\nIntro line.\n\n## First\n\nAlpha.\n\n## Second\n\nBeta."
    sections = split_sections(body)
    titles = [t for t, _ in sections]
    assert titles == ["(overview)", "First", "Second"]
    assert "Intro line." in sections[0][1]
    assert "Alpha." in sections[1][1]


def test_subheadings_stay_within_their_h2():
    body = "## Parent\n\ntext\n\n### Child\n\nmore text\n\n## Next\n\nx"
    sections = dict(split_sections(body))
    assert "### Child" in sections["Parent"]
    assert "more text" in sections["Parent"]


def test_chunk_metadata_propagates():
    chunks = chunk_document(_doc("# Title\n\nintro\n\n## Alpha\n\naaa\n\n## Beta\n\nbbb"))
    assert len(chunks) == 3
    for c in chunks:
        assert c.doc_type == "sales"
        assert c.doc_title == "Example Doc"
        assert c.source_path == "sales/example.md"
    # section titles captured; heading reattached in display text for non-overview
    assert chunks[1].section_title == "Alpha"
    assert chunks[1].text.startswith("## Alpha")
    # index_text is enriched with doc + section titles
    assert "Example Doc" in chunks[1].index_text


def test_chunk_ids_unique():
    chunks = chunk_document(_doc("## A\n\nx\n\n## B\n\ny\n\n## C\n\nz"))
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids))


def test_long_section_falls_back_to_overlapping_windows():
    long_body = "## Big\n\n" + " ".join(f"word{i}" for i in range(4000))
    chunks = chunk_document(_doc(long_body))
    # 4000 words ~ 5200 tokens >> 800, so it must split into multiple windows
    assert len(chunks) > 1
    assert all(c.section_title == "Big" for c in chunks)
    assert len({c.chunk_id for c in chunks}) == len(chunks)


def test_estimate_tokens_monotonic():
    assert estimate_tokens("one two three") < estimate_tokens("one two three four five six")
    assert estimate_tokens("") == 0
