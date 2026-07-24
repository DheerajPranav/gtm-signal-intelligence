"""Pydantic models for the flagship outbound agent (v1 + v2 memory-aware)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Core Enums
# ============================================================================

class Seniority(str, Enum):
    IC = "ic"
    MANAGER = "manager"
    DIRECTOR = "director"
    VP = "vp"
    C_SUITE = "c_suite"


class Department(str, Enum):
    SALES = "sales"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    FINANCE = "finance"
    PRODUCT = "product"
    ENGINEERING = "engineering"
    OTHER = "other"


class BuyingInfluence(str, Enum):
    ECONOMIC_BUYER = "economic_buyer"
    CHAMPION = "champion"
    USER = "user"
    BLOCKER = "blocker"
    UNKNOWN = "unknown"


class VariantAngle(str, Enum):
    PAIN_LED = "pain"
    TRIGGER_EVENT_LED = "trigger"
    PEER_PROOF = "peer_proof"
    COMPETITIVE = "competitive"


class FactType(str, Enum):
    LAST_CONTACT = "last_contact"
    KNOWN_PEOPLE = "known_people"
    FUNDING_EVENT = "funding_event"
    PRODUCT_CHANGE = "product_change"
    HIRING_SIGNAL = "hiring_signal"
    PAIN_POINT = "pain_point"
    USED_ANGLE = "used_angle"


# ============================================================================
# Core v1 Models — Research + Scoring + Personas + Writing + Critique
# ============================================================================

class TargetCompany(BaseModel):
    domain: str
    name: str
    model_config = ConfigDict(extra="forbid")


class CompanyProfile(BaseModel):
    """Enriched company data from research agent."""
    target: TargetCompany
    industry: str
    sub_industry: str
    size_band: str  # e.g., "100-500", "500-1000"
    funding_stage: str  # e.g., "Series B", "Series C"
    tech_stack: list[str]
    recent_news: list[str]
    key_people: list[str]
    buying_signals: list[str]
    last_updated: datetime
    model_config = ConfigDict(extra="forbid")


class FitScore(BaseModel):
    """ICP fit score from scoring agent."""
    score: float = Field(ge=0, le=1)
    firmographic_score: float = Field(ge=0, le=1)
    technographic_score: float = Field(ge=0, le=1)
    behavioral_score: float = Field(ge=0, le=1)
    timing_score: float = Field(ge=0, le=1)
    reasoning: str
    model_config = ConfigDict(extra="forbid")


class Persona(BaseModel):
    """Buyer persona discovered by persona agent."""
    id: str
    name: Optional[str] = None
    title: str
    department: Department
    seniority: Seniority
    pain_points: list[str]
    priorities: list[str]
    objections: list[str]
    buying_influence: BuyingInfluence
    model_config = ConfigDict(extra="forbid")


class EmailDraft(BaseModel):
    """Email draft from writing agent.

    `variant_id` is unique across the whole run, not just within a persona — one
    persona gets several variants, so it is the only safe key for joining a draft
    to its eval.
    """
    persona_id: str
    variant_id: str  # e.g., "persona-3__pain", unique run-wide
    subject: str
    body: str
    personalization_hooks: list[str]
    variant_angle: VariantAngle
    model_config = ConfigDict(extra="forbid")


class EmailEval(BaseModel):
    """Critique agent's scoring."""
    personalization_score: float = Field(ge=0, le=5)
    relevance_score: float = Field(ge=0, le=5)
    cta_score: float = Field(ge=0, le=5)
    spam_risk: float = Field(ge=0, le=5)
    would_send: bool
    reasoning: str
    model_config = ConfigDict(extra="forbid")


class AccountBrief(BaseModel):
    """Complete account research + outreach package.

    Both maps are keyed by `variant_id`. Keying emails by `persona_id` instead
    would silently drop every variant but the last for a persona, and would make
    emails un-joinable to evals, which are necessarily per-variant.
    """
    target: TargetCompany
    profile: CompanyProfile
    fit: FitScore
    personas: list[Persona]
    emails: dict[str, EmailDraft]  # variant_id -> draft
    evals: dict[str, EmailEval]    # variant_id -> eval for that draft
    cost_usd: float
    latency_ms: float
    timestamp: datetime
    model_config = ConfigDict(extra="forbid")

    def emails_for_persona(self, persona_id: str) -> list[EmailDraft]:
        """All variants drafted for one persona."""
        return [e for e in self.emails.values() if e.persona_id == persona_id]

    def eval_for(self, variant_id: str) -> Optional[EmailEval]:
        return self.evals.get(variant_id)


class RunTrace(BaseModel):
    """Observability: per-agent costs and latencies."""
    run_id: str
    research_cost: float
    research_latency_ms: float
    scoring_cost: float
    scoring_latency_ms: float
    persona_cost: float
    persona_latency_ms: float
    writing_cost: float
    writing_latency_ms: float
    critique_cost: float
    critique_latency_ms: float
    total_cost: float
    total_latency_ms: float
    timestamp: datetime
    model_config = ConfigDict(extra="forbid")


# ============================================================================
# v2 Memory Models — Episodic + Semantic + Procedural
# ============================================================================

class EpisodicEntry(BaseModel):
    """Successful (or failed) email in the episodic memory store."""
    episode_id: str
    variant_id: str  # joins back to the EmailDraft/EmailEval this episode came from
    account_domain: str
    persona_department: Department
    persona_seniority: Seniority
    variant_angle: VariantAngle
    email_subject: str
    email_body: str
    personalization_score: float = Field(ge=0, le=5)
    relevance_score: float = Field(ge=0, le=5)
    cta_score: float = Field(ge=0, le=5)
    spam_risk: float = Field(ge=0, le=5)
    would_send: bool
    embedding_id: str  # reference to vector store
    cost_usd: float
    timestamp: datetime
    industry: str
    sub_industry: str
    size_band: str
    funding_stage: str
    model_config = ConfigDict(extra="forbid")


class SemanticFact(BaseModel):
    """Structured account fact with confidence and staleness tracking.

    Facts are append-only: an update writes a new row and sets `superseded_by`
    on the old one, so the history stays auditable instead of being overwritten.
    """
    fact_id: str  # target of another fact's `superseded_by`; without it that pointer dangles
    account_id: str
    fact_type: FactType
    value: str
    source_url: str
    confidence: float = Field(ge=0, le=1)
    observed_at: datetime
    superseded_by: Optional[str] = None  # fact_id of the row that replaced this one
    model_config = ConfigDict(extra="forbid")

    @property
    def is_current(self) -> bool:
        return self.superseded_by is None

    def age_days(self, now: Optional[datetime] = None) -> float:
        """Staleness input for the >60-day flag the v2 eval requires."""
        return ((now or datetime.utcnow()) - self.observed_at).total_seconds() / 86400


class PlaybookRule(BaseModel):
    """Learned rule: which angles work for which segments."""
    rule_id: str  # needed so consolidation can update/retire a specific rule
    segment_key: str  # e.g., "fintech_vp-revops_series-b"
    rule_text: str  # e.g., "Trigger-event-led opens land 34% higher on personalization"
    variant_angle: VariantAngle
    support_n: int = Field(ge=0)  # sample size this rule is based on
    effect_size: float  # e.g., 0.34 for 34% lift
    confidence: float = Field(ge=0, le=1)
    created_at: datetime
    last_verified_at: datetime
    retired_at: Optional[datetime] = None  # consolidation retires rather than deletes
    model_config = ConfigDict(extra="forbid")

    @property
    def is_active(self) -> bool:
        return self.retired_at is None


class MemoryRetrievalResult(BaseModel):
    """What memory returned at write-time for the writing agent."""
    applicable_rules: list[PlaybookRule]
    successful_examples: list[EpisodicEntry]  # top 5 by score
    account_history: list[SemanticFact]
    retrieval_cost: float
    retrieval_latency_ms: float
    model_config = ConfigDict(extra="forbid")


class MemoryWriteDecision(BaseModel):
    """What gets written to memory after critique."""
    write_episodic: bool  # True if scores meet thresholds
    write_semantic_delta: bool  # Always true (account facts are always current)
    write_negative_pattern: bool  # True if would_send=False and scores low
    reasoning: str
    model_config = ConfigDict(extra="forbid")


# Thresholds gating what enters episodic memory. Kept here rather than inline in
# the critique agent so the eval harness and the consolidation job read the same
# numbers the writer used — a drift between them would silently poison the store.
EPISODIC_MIN_PERSONALIZATION = 4.0
EPISODIC_MIN_RELEVANCE = 4.0
EPISODIC_MAX_SPAM_RISK = 2.0
NEGATIVE_PATTERN_MAX_SCORE = 2.0


def decide_memory_write(evaluation: EmailEval) -> MemoryWriteDecision:
    """Apply the episodic-admission policy to a critique result.

    Only high-quality drafts become few-shot exemplars; letting mediocre ones in
    would teach the writing agent to reproduce mediocrity.
    """
    qualifies = (
        evaluation.personalization_score >= EPISODIC_MIN_PERSONALIZATION
        and evaluation.relevance_score >= EPISODIC_MIN_RELEVANCE
        and evaluation.spam_risk <= EPISODIC_MAX_SPAM_RISK
    )

    scored_poorly = min(
        evaluation.personalization_score,
        evaluation.relevance_score,
        evaluation.cta_score,
    ) <= NEGATIVE_PATTERN_MAX_SCORE
    is_negative = not evaluation.would_send and scored_poorly

    if qualifies:
        reason = "meets episodic admission thresholds"
    elif is_negative:
        reason = "rejected draft with a weak dimension — stored as a failure pattern"
    else:
        reason = "middling result — recorded as account history only"

    return MemoryWriteDecision(
        write_episodic=qualifies,
        write_semantic_delta=True,  # account facts are always worth updating
        write_negative_pattern=is_negative,
        reasoning=reason,
    )
