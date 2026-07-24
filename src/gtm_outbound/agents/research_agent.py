"""Research Agent: Enrich company profiles via web search and news."""

from __future__ import annotations

from ..models import TargetCompany, CompanyProfile


async def enrich(domain: str) -> CompanyProfile:
    """Research a company and return enriched profile.

    Tools available: web_search, fetch_page, news_search.
    Max 8 tool calls per query.

    Args:
        domain: Company domain (e.g., "linear.app").

    Returns:
        CompanyProfile with industry, size, funding, tech stack, etc.
    """
    # Day 9: Implement with Anthropic SDK + tool use
    raise NotImplementedError("Day 9: Research agent implementation")
