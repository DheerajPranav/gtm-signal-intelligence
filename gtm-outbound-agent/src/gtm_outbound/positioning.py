"""Positioning grounding: the KB material the persona agent builds stakeholder cards from.

The Day-11 DoD requires persona cards to "reference Northstar language from the KB" — so,
like the scoring agent's ICP, the positioning must come from the corpus at build-time, not
be paraphrased into the agent's prompt where it could drift. `KBPositioningProvider` reads
Northstar's positioning doc plus the two buyer-persona pages and hands them to the agent
verbatim, with citable sources.

`POSITIONING_TERMS` mirrors the "Words we use" list in `positioning.md`. It is the anchor
for the eval's deterministic grounding proxy — a cheap lexical check, explicitly NOT a
semantic judge. A test asserts every term still appears in the source doc, so the list
cannot silently drift from the corpus.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol

# positioning.py -> gtm_outbound -> src -> gtm-outbound-agent -> <repo root>
_REPO_ROOT = Path(__file__).resolve().parents[3]
_KB = _REPO_ROOT / "gtm-knowledge-base" / "data" / "northstar"

_DEFAULT_DOCS = (
    _KB / "sales" / "positioning.md",
    _KB / "marketing" / "for-vp-revops.md",
    _KB / "marketing" / "for-vp-sales.md",
)

# Canonical Northstar vocabulary, mirroring positioning.md's "Use:" list plus its proof
# points. Lowercased; matched as substrings. Kept in sync with the corpus by a test.
POSITIONING_TERMS: frozenset[str] = frozenset({
    "source of truth",
    "warehouse-native",
    "forecast accuracy",
    "pipeline hygiene",
    "revops",
    "rep productivity",
    "transparent",
})


@dataclass(frozen=True)
class PositioningGrounding:
    text: str
    sources: tuple[str, ...]


class PositioningProvider(Protocol):
    def get_positioning(self) -> PositioningGrounding: ...


class PositioningNotFoundError(RuntimeError):
    """A positioning doc could not be located — fail loudly, never paraphrase from memory."""


class KBPositioningProvider:
    """Reads Northstar positioning + buyer-persona docs from the knowledge base."""

    def __init__(self, doc_paths: Optional[tuple[Path, ...]] = None) -> None:
        self.doc_paths = doc_paths or _DEFAULT_DOCS

    def get_positioning(self) -> PositioningGrounding:
        chunks: list[str] = []
        sources: list[str] = []
        for path in self.doc_paths:
            if not path.is_file():
                raise PositioningNotFoundError(
                    f"Positioning doc not found at {path}. The persona agent grounds on "
                    f"the knowledge base and will not invent Northstar messaging."
                )
            try:
                src = str(path.resolve().relative_to(_REPO_ROOT))
            except ValueError:
                src = str(path)
            sources.append(src)
            chunks.append(f"<<<KB source={src}>>>\n{path.read_text(encoding='utf-8')}\n>>>END")
        return PositioningGrounding(text="\n\n".join(chunks), sources=tuple(sources))


class StaticPositioningProvider:
    """A fixed positioning string — for tests and offline runs, no filesystem access."""

    def __init__(self, text: str, sources: tuple[str, ...] = ("static",)) -> None:
        self._grounding = PositioningGrounding(text=text, sources=sources)

    def get_positioning(self) -> PositioningGrounding:
        return self._grounding
