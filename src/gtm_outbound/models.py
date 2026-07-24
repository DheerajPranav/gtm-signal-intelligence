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
    """Email draft from writing agent."""
    persona_id: str
    variant_id: str  # e.g., "v1_pain", "v2_trigger"
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
    """Complete account research + outreach package."""
    target: TargetCompany
    profile: CompanyProfile
    fit: FitScore
    personas: list[Persona]
    emails: dict[str, EmailDraft]  # persona_id -> email
    evals: dict[str, EmailEval]  # variant_id -> eval
    cost_usd: float
    latency_ms: float
    timestamp: datetime
    model_config = ConfigDict(extra="forbid")


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
    """Structured account fact with confidence and staleness tracking."""
    account_id: str
    fact_type: FactType
    value: str
    source_url: str
    confidence: float = Field(ge=0, le=1)
    observed_at: datetime
    superseded_by: Optional[str] = None  # reference to newer fact if updated
    model_config = ConfigDict(extra="forbid")


class PlaybookRule(BaseModel):
    """Learned rule: which angles work for which segments."""
    segment_key: str  # e.g., "fintech_vp-revops_series-b"
    rule_text: str  # e.g., "Trigger-event-led opens land 34% higher on personalization"
    variant_angle: VariantAngle
    support_n: int  # sample size this rule is based on
    effect_size: float  # e.g., 0.34 for 34% lift
    confidence: float = Field(ge=0, le=1)
    created_at: datetime
    last_verified_at: datetime
    model_config = ConfigDict(extra="forbid")


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
