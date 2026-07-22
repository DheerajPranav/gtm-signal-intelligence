"""Section-based chunker.

Primary strategy: one chunk per markdown H2 section (plus a leading "overview"
chunk for the H1 + intro that precedes the first H2). Any section longer than
MAX_TOKENS is split into overlapping word-windows so no single chunk blows past
the embedder's useful context.

Each chunk carries rich metadata (doc_type, doc_title, section_title, source_path)
so retrieval results are attributable back to a specific place in a specific doc.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .config import MAX_TOKENS, OVERLAP_TOKENS, TOKENS_PER_WORD
from .loader import Document

_H2_RE = re.compile(r"^##\s+(.*)$")
_WORD_RE = re.compile(r"\S+")

OVERVIEW_TITLE = "(overview)"


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    text: str  # display text (section heading + body)
    doc_type: str
    doc_title: str
    section_title: str
    source_path: str
    chunk_index: int

    @property
    def index_text(self) -> str:
        """String actually fed to the embedder / BM25 — enriched with the doc and
        section titles so title words count toward retrieval."""
        return f"{self.doc_title}\n{self.section_title}\n{self.text}"

    def metadata(self) -> dict:
        return {
            "doc_type": self.doc_type,
            "doc_title": self.doc_title,
            "section_title": self.section_title,
            "source_path": self.source_path,
            "chunk_index": self.chunk_index,
        }


def estimate_tokens(text: str) -> int:
    """Cheap, dependency-free token estimate (~1.3 tokens per whitespace word)."""
    return round(len(_WORD_RE.findall(text)) * TOKENS_PER_WORD)


def split_sections(body: str) -> list[tuple[str, str]]:
    """Split markdown into (section_title, section_body) pairs by H2 heading.
    Content before the first H2 (the H1 title + any intro) becomes the overview
    section. Sub-headings (### and deeper) stay within their H2 section."""
    sections: list[tuple[str, str]] = []
    cur_title = OVERVIEW_TITLE
    cur_lines: list[str] = []

    def flush() -> None:
        text = "\n".join(cur_lines).strip()
        if text:
            sections.append((cur_title, text))

    for line in body.splitlines():
        m = _H2_RE.match(line)
        if m:
            flush()
            cur_title = m.group(1).strip()
            cur_lines = []
        else:
            cur_lines.append(line)
    flush()
    return sections


def _window_words(text: str, max_tokens: int, overlap_tokens: int) -> list[str]:
    """Slide a token-budget window over the text in word space, with overlap."""
    words = _WORD_RE.findall(text)
    max_words = max(1, int(max_tokens / TOKENS_PER_WORD))
    overlap_words = max(0, int(overlap_tokens / TOKENS_PER_WORD))
    step = max(1, max_words - overlap_words)
    windows: list[str] = []
    i = 0
    while i < len(words):
        windows.append(" ".join(words[i : i + max_words]))
        if i + max_words >= len(words):
            break
        i += step
    return windows


def chunk_document(doc: Document) -> list[Chunk]:
    chunks: list[Chunk] = []
    idx = 0
    for section_title, section_body in split_sections(doc.body):
        # Reattach the heading to the body for display/context (overview has none).
        if section_title == OVERVIEW_TITLE:
            display = section_body
        else:
            display = f"## {section_title}\n\n{section_body}"

        pieces = [display]
        if estimate_tokens(section_body) > MAX_TOKENS:
            heading = "" if section_title == OVERVIEW_TITLE else f"## {section_title}\n\n"
            pieces = [heading + w for w in _window_words(section_body, MAX_TOKENS, OVERLAP_TOKENS)]

        for piece in pieces:
            chunks.append(
                Chunk(
                    chunk_id=f"{doc.source_path}#{idx}",
                    text=piece,
                    doc_type=doc.doc_type,
                    doc_title=doc.doc_title,
                    section_title=section_title,
                    source_path=doc.source_path,
                    chunk_index=idx,
                )
            )
            idx += 1
    return chunks


def chunk_documents(docs: list[Document]) -> list[Chunk]:
    return [c for doc in docs for c in chunk_document(doc)]
