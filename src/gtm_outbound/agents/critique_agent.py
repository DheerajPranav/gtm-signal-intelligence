"""Critique Agent: Score and evaluate email drafts.

V2 memory integration: after scoring, decides what gets written to memory
(episodic, semantic, negative patterns).
"""

from __future__ import annotations

from ..models import EmailDraft, EmailEval, MemoryWriteDecision


async def critique(email: EmailDraft) -> tuple[EmailEval, MemoryWriteDecision]:
    """Score an email draft on personalization, relevance, CTA, spam risk.

    Returns both the eval AND a memory write decision for v2.

    Args:
        email: EmailDraft to critique.

    Returns:
        (EmailEval scores, MemoryWriteDecision for what to store).
    """
    # Day 13: Implement with Claude Haiku (cheap scoring) + LLM-judge rules
    # MemoryWriteDecision logic:
    #   - write_episodic: personalization >= 4 AND relevance >= 4 AND spam <= 2
    #   - write_semantic_delta: always True (account facts always current)
    #   - write_negative_pattern: would_send=False AND any dimension <= 2
    raise NotImplementedError("Day 13: Critique agent implementation")
