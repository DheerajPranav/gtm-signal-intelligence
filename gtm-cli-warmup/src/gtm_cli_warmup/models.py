"""Pydantic models for the warmup CLI."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CompanyDescription(BaseModel):
    """A short, structured description of a company."""

    name: str = Field(description="The company's canonical name.")
    one_liner: str = Field(
        description="Exactly three sentences describing what the company does, "
        "who it sells to, and why it matters."
    )
    industry: str = Field(
        description="Primary industry, e.g. 'B2B SaaS - productivity software'."
    )
    size_guess: str = Field(
        description="Best guess at employee headcount band, e.g. '200-500'."
    )
