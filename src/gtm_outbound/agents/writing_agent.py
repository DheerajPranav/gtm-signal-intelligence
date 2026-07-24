"""Writing Agent: Draft personalized emails.

V2 memory integration: retrieves episodic (examples), semantic (account history),
and procedural (playbook rules) at write-time.
"""

from __future__ import annotations

from ..models import CompanyProfile, Persona, EmailDraft, MemoryRetrievalResult


async def draft(
    profile: CompanyProfile,
    persona: Persona,
    memory: MemoryRetrievalResult | None = None,
) -> list[EmailDraft]:
    """Draft email variants for a persona.

    If memory is provided (v2), uses it to retrieve similar successful emails
    and applicable playbook rules.

    Args:
        profile: CompanyProfile.
        persona: Persona to write for.
        memory: (Optional) Retrieved memory for this (profile, persona) pair.

    Returns:
        List of EmailDraft variants.
    """
    # Day 12: Implement with Claude Sonnet + multi-variant drafting
    # If memory provided, inject <applicable_rules>, <examples>, <account_history>
    raise NotImplementedError("Day 12: Writing agent implementation")
