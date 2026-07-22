"""Shared tokenization used by every retriever, so the vector and keyword indexes
speak the same vocabulary.

Lowercase, alphanumeric tokens, minus a compact English stopword list (function
words + question words). Domain terms like "northstar" are deliberately NOT
stopwords — TF-IDF / BM25 idf already downweight ubiquitous terms without throwing
away signal.
"""

from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[a-z0-9]+")

STOPWORDS: frozenset[str] = frozenset(
    """
    a an the and or but if of to in on for with as at by from into about over under
    is are was were be been being do does did have has had having
    this that these those it its they them their you your we our us i he she his her
    will would can could should shall may might must not no nor yes
    what which who whom whose when where why how
    there here than then so such up down out off again more most some any all both each
    per via etc vs
    """.split()
)


def _fold_plural(tok: str) -> str:
    """Very light, symmetric plural folding so query/doc vocabularies align
    (e.g. "competitors" -> "competitor", "modules" -> "module"). Applied to both
    sides, so it only ever helps matching; not a real stemmer."""
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    return tok


def tokenize(text: str) -> list[str]:
    return [
        _fold_plural(t)
        for t in _TOKEN_RE.findall(text.lower())
        if t not in STOPWORDS
    ]
