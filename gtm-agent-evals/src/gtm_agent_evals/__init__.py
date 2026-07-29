"""GTM Agent Evals: Open-source LLM-judge rubric kit for GTM AI agents."""

from __future__ import annotations

from .rubrics import (
    ICPRubric,
    PersonaRubric,
    EmailRubric,
    CritiqueRubric,
)

__version__ = "0.1.0"
__all__ = [
    "ICPRubric",
    "PersonaRubric",
    "EmailRubric",
    "CritiqueRubric",
]
