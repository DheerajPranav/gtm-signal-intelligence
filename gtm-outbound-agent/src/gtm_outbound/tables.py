"""SQLModel persistence tables for the v2 memory layer.

Why these are separate from the Pydantic models in `models.py`:

`models.py` holds *domain* models — they validate LLM input/output, forbid extra
fields, and are what the agents pass around. Persistence has different needs
(primary keys, indexes, nullable columns, no `extra="forbid"`), and welding the two
together means a storage concern can silently change an agent's contract. The
converters below are the only bridge.

Why episodic *metadata* lives in SQL even though its embedding lives in Chroma:
the nightly consolidation job groups episodes by (industry x persona x angle) and
computes aggregate stats where n >= 10. That is a SQL `GROUP BY`, not a nearest-
neighbour search. Chroma stores the vector for similarity retrieval at write-time;
this table answers the aggregation queries that actually produce playbook rules.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from .models import (
    Department,
    EpisodicEntry,
    FactType,
    PlaybookRule,
    SemanticFact,
    Seniority,
    VariantAngle,
)


class SemanticFactRow(SQLModel, table=True):
    """Append-only account facts. An update inserts a new row and stamps
    `superseded_by` on the old one, so history stays auditable."""

    __tablename__ = "semantic_fact"

    fact_id: str = Field(primary_key=True)
    account_id: str = Field(index=True)  # every read is scoped to one account
    fact_type: FactType = Field(index=True)
    value: str
    source_url: str
    confidence: float
    observed_at: datetime = Field(index=True)  # staleness checks sort on this
    superseded_by: Optional[str] = Field(default=None, foreign_key="semantic_fact.fact_id")

    @classmethod
    def from_domain(cls, fact: SemanticFact) -> "SemanticFactRow":
        return cls(**fact.model_dump())

    def to_domain(self) -> SemanticFact:
        return SemanticFact.model_validate(self.model_dump())


class PlaybookRuleRow(SQLModel, table=True):
    """Learned rules. Consolidation retires rather than deletes, so a rule that
    stops holding leaves a trace instead of vanishing."""

    __tablename__ = "playbook_rule"

    rule_id: str = Field(primary_key=True)
    segment_key: str = Field(index=True)  # retrieval router looks up by segment
    rule_text: str
    variant_angle: VariantAngle
    support_n: int
    effect_size: float
    confidence: float
    created_at: datetime
    last_verified_at: datetime
    retired_at: Optional[datetime] = Field(default=None, index=True)

    @classmethod
    def from_domain(cls, rule: PlaybookRule) -> "PlaybookRuleRow":
        return cls(**rule.model_dump())

    def to_domain(self) -> PlaybookRule:
        return PlaybookRule.model_validate(self.model_dump())


class EpisodicEntryRow(SQLModel, table=True):
    """Episode metadata. The email body's embedding lives in Chroma under
    `embedding_id`; these columns exist so consolidation can aggregate."""

    __tablename__ = "episodic_entry"

    episode_id: str = Field(primary_key=True)
    variant_id: str = Field(index=True)
    account_domain: str = Field(index=True)

    # The consolidation grouping key. Indexed together because every rule-learning
    # query filters on this triple.
    industry: str = Field(index=True)
    persona_department: Department = Field(index=True)
    persona_seniority: Seniority = Field(index=True)
    variant_angle: VariantAngle = Field(index=True)

    sub_industry: str
    size_band: str
    funding_stage: str

    email_subject: str
    email_body: str
    personalization_score: float
    relevance_score: float
    cta_score: float
    spam_risk: float
    would_send: bool = Field(index=True)  # the headline eval metric filters on this
    embedding_id: str
    cost_usd: float
    timestamp: datetime = Field(index=True)  # learning curves are ordered by this

    @classmethod
    def from_domain(cls, entry: EpisodicEntry) -> "EpisodicEntryRow":
        return cls(**entry.model_dump())

    def to_domain(self) -> EpisodicEntry:
        return EpisodicEntry.model_validate(self.model_dump())


# Importing this module is what registers the tables on SQLModel.metadata.
# `db.init_db()` imports it explicitly for that reason — without it,
# create_all() runs happily and creates nothing.
ALL_TABLES = (SemanticFactRow, PlaybookRuleRow, EpisodicEntryRow)
