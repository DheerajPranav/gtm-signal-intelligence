"""Citation parsing — the single source of truth for `[source: doc#section]` handling.

Both `answer_gen` and `rag` previously re-implemented this regex + chunk-matching
loop independently (and `answer_gen` then discarded its result). One function now
owns the format so the parser and the prompt that produces it can never drift.
"""

from __future__ import annotations

import re

from .models import Citation, RankedChunk

# `[source: doc_title#section_title]`. Both parts are non-greedy and forbid the
# delimiter that ends them, so adjacent citations can't be swallowed into one match.
CITATION_RE = re.compile(r"\[source:\s*([^#\]]+)#([^\]]+)\]", re.IGNORECASE)


def _norm(s: str) -> str:
    """Normalise for comparison: collapse whitespace, casefold."""
    return " ".join(s.split()).casefold()


def parse_citations(
    answer_text: str, chunks: list[RankedChunk]
) -> tuple[list[Citation], list[RankedChunk], list[str]]:
    """Resolve inline citations in `answer_text` against the chunks given to the model.

    Returns:
        (citations, cited_chunks, unresolved)
        - citations: deduplicated, in first-appearance order.
        - cited_chunks: the subset of `chunks` actually cited, same order as `citations`.
        - unresolved: raw `doc#section` strings the model emitted that match no chunk.
          These are grounding failures worth surfacing, not silently dropping.
    """
    # Index chunks by (doc, section). First chunk wins for a given key.
    by_key: dict[tuple[str, str], RankedChunk] = {}
    for chunk in chunks:
        key = (
            _norm(str(chunk.metadata.get("doc_title", ""))),
            _norm(str(chunk.metadata.get("section_title", ""))),
        )
        by_key.setdefault(key, chunk)

    citations: list[Citation] = []
    cited_chunks: list[RankedChunk] = []
    unresolved: list[str] = []
    seen: set[str] = set()

    for match in CITATION_RE.finditer(answer_text):
        doc_title = match.group(1).strip()
        section_title = match.group(2).strip()
        chunk = by_key.get((_norm(doc_title), _norm(section_title)))

        if chunk is None:
            raw = f"{doc_title}#{section_title}"
            if raw not in unresolved:
                unresolved.append(raw)
            continue

        if chunk.chunk_id in seen:
            continue
        seen.add(chunk.chunk_id)

        citations.append(
            Citation(
                doc_title=str(chunk.metadata.get("doc_title", doc_title)),
                section_title=str(chunk.metadata.get("section_title", section_title)),
                source_path=str(chunk.metadata.get("source_path", "")),
                chunk_id=chunk.chunk_id,
            )
        )
        cited_chunks.append(chunk)

    return citations, cited_chunks, unresolved


def format_citation(chunk: RankedChunk) -> str:
    """Render the citation marker for a chunk — used to build few-shot prompt text."""
    return (
        f"[source: {chunk.metadata.get('doc_title', '')}"
        f"#{chunk.metadata.get('section_title', '')}]"
    )
