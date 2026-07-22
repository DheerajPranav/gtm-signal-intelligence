"""Load the Northstar corpus: read the 30 category docs, parse YAML-ish
frontmatter, and return typed Documents.

The frontmatter in this corpus is simple flat `key: value` scalars, so we parse
it directly rather than take a YAML dependency. Anything more exotic would warrant
PyYAML — noted, not needed here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .config import CATEGORIES, CORPUS_DIR

_H1_RE = re.compile(r"^#\s+(.*)$", re.MULTILINE)


@dataclass(frozen=True)
class Document:
    source_path: str  # relative to the corpus root, e.g. "sales/positioning.md"
    doc_type: str
    doc_title: str
    body: str  # markdown with the frontmatter block stripped
    frontmatter: dict = field(default_factory=dict)


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body). If there's no leading `---` block, the
    whole text is the body and the dict is empty."""
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    # lines[0] is the opening '---'; find the closing one.
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm_lines = lines[1:i]
            body = "\n".join(lines[i + 1 :]).lstrip("\n")
            fm: dict = {}
            for line in fm_lines:
                if not line.strip() or ":" not in line:
                    continue
                key, _, raw = line.partition(":")
                fm[key.strip()] = _strip_quotes(raw)
            return fm, body
    # Unterminated frontmatter — treat as plain body.
    return {}, text


def _title_from_body(body: str, fallback: str) -> str:
    m = _H1_RE.search(body)
    return m.group(1).strip() if m else fallback


def load_document(path: Path, corpus_dir: Path = CORPUS_DIR) -> Document:
    text = path.read_text(encoding="utf-8")
    fm, body = parse_frontmatter(text)
    rel = path.relative_to(corpus_dir).as_posix()
    doc_type = fm.get("doc_type") or path.parent.name
    doc_title = fm.get("title") or _title_from_body(body, fallback=path.stem)
    return Document(
        source_path=rel,
        doc_type=doc_type,
        doc_title=doc_title,
        body=body,
        frontmatter=fm,
    )


def load_documents(corpus_dir: Path = CORPUS_DIR) -> list[Document]:
    """Load every corpus doc across the five category folders, sorted for
    deterministic ordering."""
    docs: list[Document] = []
    for category in CATEGORIES:
        cat_dir = corpus_dir / category
        for path in sorted(cat_dir.glob("*.md")):
            docs.append(load_document(path, corpus_dir))
    return docs
