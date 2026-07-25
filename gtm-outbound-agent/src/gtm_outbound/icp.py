"""ICP grounding: where the scoring agent gets Northstar's ideal-customer profile.

The scoring agent must not carry the ICP in its own prompt — that would let the rubric
drift away from the single source of truth the rest of the sprint grounds on. Instead it
pulls the ICP from the knowledge base at score-time, the same corpus the RAG assistant
answers from.

`KBICPProvider` reads the *canonical* ICP document directly. For a single doc marked
`priority: critical`, a direct read is both simpler and more reliable than a similarity
query that could rank it below a neighbour — and it keeps the vector store out of this
package's dependency tree. The provider is an injectable Protocol so tests use a static
string and never touch the filesystem.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol


@dataclass(frozen=True)
class ICPGrounding:
    """The ICP text handed to the scoring prompt, plus a citable source."""
    text: str
    source: str  # e.g. "gtm-knowledge-base/.../icp-definition.md"


class ICPProvider(Protocol):
    def get_icp(self) -> ICPGrounding: ...


# Path from this file up to the repo root, then into the KB corpus.
# icp.py -> gtm_outbound -> src -> gtm-outbound-agent -> <repo root>
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_ICP_DOC = (
    _REPO_ROOT / "gtm-knowledge-base" / "data" / "northstar" / "sales" / "icp-definition.md"
)


class ICPNotFoundError(RuntimeError):
    """The canonical ICP document could not be located — fail loudly, never guess."""


class KBICPProvider:
    """Reads Northstar's canonical ICP definition from the knowledge base corpus."""

    def __init__(self, doc_path: Optional[Path] = None) -> None:
        self.doc_path = doc_path or _DEFAULT_ICP_DOC

    def get_icp(self) -> ICPGrounding:
        if not self.doc_path.is_file():
            raise ICPNotFoundError(
                f"ICP document not found at {self.doc_path}. The scoring agent grounds "
                f"on the knowledge base and will not invent a rubric."
            )
        text = self.doc_path.read_text(encoding="utf-8")
        # Cite a repo-relative path so the source travels with the score.
        try:
            source = str(self.doc_path.resolve().relative_to(_REPO_ROOT))
        except ValueError:
            source = str(self.doc_path)
        return ICPGrounding(text=text, source=source)


class StaticICPProvider:
    """A fixed ICP string — for tests and offline runs, no filesystem access."""

    def __init__(self, text: str, source: str = "static") -> None:
        self._grounding = ICPGrounding(text=text, source=source)

    def get_icp(self) -> ICPGrounding:
        return self._grounding
