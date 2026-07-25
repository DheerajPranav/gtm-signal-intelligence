"""Scoring Agent: Score company ICP fit using knowledge base."""

from __future__ import annotations

from ..models import CompanyProfile, FitScore


async def score(profile: CompanyProfile) -> FitScore:
    """Score ICP fit using Northstar knowledge base.

    Queries gtm-knowledge-base for ICP definition, scores profile on
    4 dimensions: firmographic, technographic, behavioral, timing.

    Args:
        profile: CompanyProfile to score.

    Returns:
        FitScore with breakdown + reasoning.
    """
    # Day 10: Implement with KB query + Claude scoring
    raise NotImplementedError("Day 10: Scoring agent implementation")
