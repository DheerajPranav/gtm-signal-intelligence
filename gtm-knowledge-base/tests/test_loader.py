from gtm_kb.loader import load_documents, parse_frontmatter


def test_loads_exactly_30_docs():
    docs = load_documents()
    assert len(docs) == 30


def test_every_doc_has_core_fields():
    for d in load_documents():
        assert d.doc_type, f"missing doc_type: {d.source_path}"
        assert d.doc_title.strip(), f"empty title: {d.source_path}"
        assert "/" in d.source_path  # category/filename.md
        assert d.body.strip()


def test_doc_type_reflects_frontmatter():
    by_path = {d.source_path: d for d in load_documents()}
    # doc_type is a semantic frontmatter label; it usually matches the folder but
    # need not (e.g. case-studies/*.md declare doc_type "case-study").
    assert by_path["sales/positioning.md"].doc_type == "sales"
    assert by_path["product/pricing.md"].doc_type == "product"
    assert by_path["case-studies/series-b-devtools.md"].doc_type == "case-study"
    # every doc_type is a non-empty lowercase slug
    for d in by_path.values():
        assert d.doc_type and d.doc_type == d.doc_type.lower()


def test_frontmatter_parser_handles_quoted_title_with_colon():
    text = '---\ntitle: "Blog: Forecast Accuracy — Part 1"\ndoc_type: marketing\n---\n\n# Heading\n\nBody.'
    fm, body = parse_frontmatter(text)
    assert fm["title"] == "Blog: Forecast Accuracy — Part 1"
    assert fm["doc_type"] == "marketing"
    assert body.startswith("# Heading")


def test_no_frontmatter_returns_whole_body():
    fm, body = parse_frontmatter("# Just a heading\n\ntext")
    assert fm == {}
    assert body.startswith("# Just a heading")
