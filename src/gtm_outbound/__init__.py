"""gtm_outbound — Multi-agent GTM outbound system with optional v2 learning loop.

Week 2: Flagship Core Loop (Days 8-14)
- Day 8: Scaffold + models + observability
- Day 9: Research Agent (enrichment via web search)
- Day 10: Scoring Agent (ICP fit)
- Day 11: Persona Agent (buyer discovery)
- Day 12: Writing Agent (email drafting)
- Day 13: Critique Agent (email evaluation)
- Day 14: Integration + evals

Week 5-6 extension: v2 Learning Loop
- Episodic memory (successful/failed emails)
- Semantic memory (account facts)
- Procedural memory (playbook rules)
- Memory retrieval router
- Nightly consolidation job
"""

from .models import (
    # Core v1 models
    TargetCompany,
    CompanyProfile,
    FitScore,
    Persona,
    EmailDraft,
    EmailEval,
    AccountBrief,
    RunTrace,
    # v2 Memory models
    EpisodicEntry,
    SemanticFact,
    PlaybookRule,
    MemoryRetrievalResult,
    MemoryWriteDecision,
)

__all__ = [
    "TargetCompany",
    "CompanyProfile",
    "FitScore",
    "Persona",
    "EmailDraft",
    "EmailEval",
    "AccountBrief",
    "RunTrace",
    "EpisodicEntry",
    "SemanticFact",
    "PlaybookRule",
    "MemoryRetrievalResult",
    "MemoryWriteDecision",
]
