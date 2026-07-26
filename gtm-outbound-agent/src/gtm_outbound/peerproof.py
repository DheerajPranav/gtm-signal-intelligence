"""Peer-proof grounding: the KB case study the writing agent cites for the peer variant.

The peer-proof email angle only works if the story is *relevant* — a fintech prospect
should hear about a fintech customer, not a random logo. This provider picks the
segment-matched case study from the KB by the target's industry, and hands it over with a
citable source so the writing agent quotes a real Northstar customer story rather than
inventing one.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol

from .models import CompanyProfile

# peerproof.py -> gtm_outbound -> src -> gtm-outbound-agent -> <repo root>
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CASE_DIR = _REPO_ROOT / "gtm-knowledge-base" / "data" / "northstar" / "case-studies"

# Keyword -> case-study file. Order matters: first substring hit on the profile's
# industry/sub_industry wins. Default is the vertical-SaaS story.
_SEGMENT_MAP: tuple[tuple[str, str], ...] = (
    ("fintech", "series-c-fintech.md"),
    ("finance", "series-c-fintech.md"),
    ("devtool", "series-b-devtools.md"),
    ("developer", "series-b-devtools.md"),
    ("marketing", "series-c-marketing-tech.md"),
)
_DEFAULT_CASE = "series-d-vertical-saas.md"


@dataclass(frozen=True)
class PeerProof:
    text: str
    source: str
    matched_segment: str  # which keyword matched, or "default"


class PeerProofProvider(Protocol):
    def get_case_study(self, profile: CompanyProfile) -> PeerProof: ...


class PeerProofNotFoundError(RuntimeError):
    """The matched case study is missing — fail loudly, don't invent a customer story."""


def _segment_of(profile: CompanyProfile) -> tuple[str, str]:
    """Return (case_study_filename, matched_keyword) for a profile."""
    haystack = " ".join(
        v.value.lower()
        for v in (profile.industry, profile.sub_industry)
        if v is not None
    )
    for keyword, filename in _SEGMENT_MAP:
        if keyword in haystack:
            return filename, keyword
    return _DEFAULT_CASE, "default"


class KBPeerProofProvider:
    """Reads the segment-matched customer case study from the knowledge base."""

    def __init__(self, case_dir: Optional[Path] = None) -> None:
        self.case_dir = case_dir or _CASE_DIR

    def get_case_study(self, profile: CompanyProfile) -> PeerProof:
        filename, matched = _segment_of(profile)
        path = self.case_dir / filename
        if not path.is_file():
            raise PeerProofNotFoundError(
                f"Case study {path} not found. The peer-proof angle grounds on a real "
                f"Northstar customer story and will not fabricate one."
            )
        try:
            source = str(path.resolve().relative_to(_REPO_ROOT))
        except ValueError:
            source = str(path)
        return PeerProof(text=path.read_text(encoding="utf-8"), source=source,
                         matched_segment=matched)


class StaticPeerProofProvider:
    """A fixed case study — for tests and offline runs, no filesystem access."""

    def __init__(self, text: str, source: str = "static", matched: str = "static") -> None:
        self._proof = PeerProof(text=text, source=source, matched_segment=matched)

    def get_case_study(self, profile: CompanyProfile) -> PeerProof:
        return self._proof
