"""Reusable GTM evaluation rubrics extracted from Days 10-13 agents.

Each rubric is framework-agnostic and can be used to score any company profile,
persona, email, or critique — not just output from the gtm-outbound-agent.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Seniority(str, Enum):
    """Organizational seniority levels."""
    IC = "ic"
    MANAGER = "manager"
    DIRECTOR = "director"
    VP = "vp"
    C_SUITE = "c_suite"


@dataclass
class ICPDimension:
    """One scored dimension of ICP fit."""
    name: str
    score: float  # 0-10
    description: str
    examples: list[str]


class ICPRubric:
    """ICP Scoring Rubric (Day 10): 4 dimensions.

    Evaluate company fit on:
    1. Firmographic: company size, ARR, growth trajectory
    2. Technographic: tech stack, infrastructure maturity
    3. Behavioral: RevOps hires, budget discussions, job postings
    4. Timing: hiring momentum, funding events, analyst reports

    Overall score is weighted mean (not model-emitted):
    - Behavioral 0.45 (primary for RevOps platform)
    - Firmographic 0.20 (baseline gate)
    - Timing 0.20 (amplifies behavioral)
    - Technographic 0.15 (secondary)
    """

    WEIGHTS = {
        "firmographic": 0.20,
        "technographic": 0.15,
        "behavioral": 0.45,
        "timing": 0.20,
    }

    # Overall-score cutoffs for the 3-band classification. See docs/CALIBRATION.md
    # for why these sit where they do (behavioral-weighted, Series B-D RevOps ICP).
    BAND_CUTOFFS = {"strong": 6.5, "weak": 4.0}

    DIMENSION_DESCRIPTIONS = {
        "firmographic": (
            "Company size (headcount, ARR), growth stage (Series A-D), "
            "target employee count (200-2000). Series B-D SaaS preferred."
        ),
        "technographic": (
            "Tech stack maturity: Salesforce/HubSpot, Snowflake/BigQuery, "
            "Looker/Tableau/Mode. Stack indicates revenue ops infrastructure."
        ),
        "behavioral": (
            "RevOps buying signals: VP RevOps hire in last 12mo, "
            "RevOps job openings, 'pipeline hygiene' mentions in earnings/blogs. "
            "STRONGEST signal for Northstar."
        ),
        "timing": (
            "Recent hiring momentum (last 90 days), funding event (last 180 days), "
            "analyst coverage (Gartner, Forrester). Amplifies behavioral signal."
        ),
    }

    @staticmethod
    def compute_overall_score(dimensions: dict[str, float]) -> float:
        """Compute weighted overall score from 4 dimension scores.

        Args:
            dimensions: dict with keys firmographic, technographic, behavioral, timing
                       values 0-10

        Returns:
            Weighted overall score (0-10)
        """
        total = sum(
            dimensions.get(dim, 0) * weight
            for dim, weight in ICPRubric.WEIGHTS.items()
        )
        return min(10.0, max(0.0, total))

    @staticmethod
    def band(overall: float) -> str:
        """Map an overall score (0-10) to a 3-band label: strong / weak / none."""
        if overall >= ICPRubric.BAND_CUTOFFS["strong"]:
            return "strong"
        if overall >= ICPRubric.BAND_CUTOFFS["weak"]:
            return "weak"
        return "none"


@dataclass
class PersonaDimension:
    """One dimension of a buyer persona card."""
    title: str
    department: str
    seniority: Seniority
    pain_points: list[str]
    priorities: list[str]
    objections: list[str]
    buying_influence: str  # "high", "medium", "low"


class PersonaRubric:
    """Persona Building Rubric (Day 11): Buyer stakeholder cards.

    A complete persona card includes:
    - Title (specific role, not generic)
    - Department (Sales, Marketing, RevOps, etc.)
    - Seniority (IC, Manager, Director, VP, C-suite)
    - 2-4 pain points (specific to this company segment)
    - 2-4 priorities (what they care about operationally)
    - 2-3 objections (concerns they'll raise)
    - Buying influence (high/medium/low for Northstar)

    Eval gate: 3 complete personas per company.
    Grounding gate: pain points reference KB positioning for the company segment.
    Distinctness gate: personas differ in role and pain vocabulary across companies.
    """

    REQUIRED_FIELDS = {
        "title": "Specific role (e.g., VP Revenue Operations, not 'Operations Leader')",
        "department": "Department (Sales, Marketing, RevOps, Finance, etc.)",
        "seniority": "Seniority level (ic, manager, director, vp, c_suite)",
        "pain_points": "2-4 specific pain points for this segment",
        "priorities": "2-4 operational priorities",
        "objections": "2-3 concerns they'll raise about Northstar",
        "buying_influence": "Buying influence: high/medium/low",
    }

    GROUNDING_TERMS = {
        "fintech": ["cash flow", "reconciliation", "settlement", "compliance"],
        "devtools": ["deployment", "CI/CD", "testing", "observability"],
        "marketing": ["demand gen", "lead scoring", "attribution", "ROI"],
        "enterprise": ["governance", "audit", "scalability", "support"],
    }

    @staticmethod
    def is_complete(persona: dict) -> bool:
        """Check if a persona has all required fields."""
        return all(field in persona for field in PersonaRubric.REQUIRED_FIELDS)


@dataclass
class EmailDimension:
    """One dimension of email quality."""
    dimension: str  # personalization, relevance, cta, spam_risk, would_send
    score: float  # 0-5 (or bool for would_send)
    reasoning: str


class EmailRubric:
    """Email Writing Rubric (Day 12-13): Cold outbound quality.

    5 dimensions:
    1. Personalization (0-5): specific company facts, not mail-merge templates
    2. Relevance (0-5): pain framing matches persona's role and concerns
    3. CTA (0-5): specific, low-friction, time-bound ask
    4. Spam risk (0-5, HIGHER IS WORSE): would this trip filters or read automated?
    5. Would-send (bool): would YOU actually send this?

    Would-send requires:
    - Personalization >= 3.5/5
    - Relevance >= 3.5/5
    - CTA >= 3.0/5
    - Spam risk <= 1.5/5
    - Genuine insight (not just research facts with name)
    """

    DIMENSIONS = {
        "personalization": {
            "description": "Does it reference something SPECIFIC and non-obvious?",
            "max": 5,
            "scoring": {
                5: "A fact only research would surface (funding round, hire, job posting)",
                4: "Company-specific but publicly available (industry, recent news)",
                3: "Some specificity, but could apply to similar companies",
                2: "Generic with one company name inserted",
                1: "Pure template (no company context at all)",
                0: "Negative personalization (wrong industry/size/maturity)",
            },
        },
        "relevance": {
            "description": "Does the pain framing match THIS persona's concerns?",
            "max": 5,
            "scoring": {
                5: "Nails the exact pain this role experiences at this company size",
                4: "Aligned with role and company, but generic framing",
                3: "Relevant to the company, not specific to the persona's role",
                2: "Tangentially related",
                1: "Misses the mark entirely",
                0: "Wrong persona/role entirely",
            },
        },
        "cta": {
            "description": "Is the ask specific, low-friction, and time-bound?",
            "max": 5,
            "scoring": {
                5: "Specific ask (15-min call Tuesday 2-4pm), clear value",
                4: "Specific but not time-bound",
                3: "Vague ask, low friction ('let me know')",
                2: "High friction (long meeting, big commitment)",
                1: "No clear ask at all",
                0: "Demand or threat instead of ask",
            },
        },
        "spam_risk": {
            "description": "Would this trip filters or read as automated?",
            "max": 5,
            "scoring": {
                5: "Extreme spam signals (ALL CAPS, fake urgency, broken tokens)",
                4: "Multiple spam signals (generic greetings + hype language)",
                3: "Minor signals (generic opening, or one red flag)",
                2: "Minimal risk (authentic tone, no obvious signals)",
                1: "Anti-spam design (personalized, authentic, conversational)",
                0: "Authenticity signal (recipient-centric framing)",
            },
        },
        "would_send": {
            "description": "Would YOU actually send this? (Bool)",
            "max": None,  # Boolean
            "pass_criteria": {
                "personalization": 3.5,
                "relevance": 3.5,
                "cta": 3.0,
                "spam_risk": 1.5,  # LOWER is better
            },
        },
    }

    # Dimensions where a higher score is worse (inverted gate).
    _LOWER_IS_BETTER = ("spam_risk",)

    @staticmethod
    def evaluate_would_send(scores: dict) -> dict:
        """Deterministic would-send decision from per-dimension scores.

        Args:
            scores: dict with keys personalization, relevance, cta, spam_risk (0-5).

        Returns:
            {"would_send": bool, "failures": list[str]} — a failure per gate not met.
            Missing dimensions are treated as worst-case (0, or 5 for spam_risk) so an
            incomplete input can never pass by omission.
        """
        criteria = EmailRubric.DIMENSIONS["would_send"]["pass_criteria"]
        failures: list[str] = []
        for dim, threshold in criteria.items():
            if dim in EmailRubric._LOWER_IS_BETTER:
                value = scores.get(dim, 5.0)
                if value > threshold:
                    failures.append(f"{dim} {value} > {threshold} (max)")
            else:
                value = scores.get(dim, 0.0)
                if value < threshold:
                    failures.append(f"{dim} {value} < {threshold} (min)")
        return {"would_send": not failures, "failures": failures}


class CritiqueRubric:
    """Critique Rubric (Day 13): Skeptical email evaluation.

    5 dimensions (same as EmailRubric) + would-send gate:
    1. Personalization (0-5)
    2. Relevance (0-5)
    3. CTA (0-5)
    4. Spam risk (0-5, HIGHER IS WORSE)
    5. Would-send (bool): filtered by strict thresholds

    This rubric is used in the critique agent to score emails AFTER they're drafted,
    and to decide whether to include them in the Account Brief.

    Key insight: Skeptical scoring is the goal. A 3/5 email is "technically fine"
    but usually not worth sending cold. Bias toward "no" rather than "yes".
    """

    SYSTEM_PROMPT = """You are a discerning B2B SDR manager reviewing cold outbound emails.
Be skeptical by default — most cold emails are mediocre. Your job is to catch that,
not to be encouraging. Do not inflate scores.

Score five dimensions:
- Personalization (0-5): Does it reference something SPECIFIC and non-obvious about this
  company/persona? 5 = a fact only research would surface. 0 = generic.
- Relevance (0-5): Does the pain framing match THIS persona's actual concerns and seniority?
- CTA (0-5): Is the ask specific, low-friction, and time-bound? Vague "let me know" = low.
- Spam risk (0-5, HIGHER IS WORSE): Would this trip filters or read as automated?
  Hype, ALL CAPS, fake urgency raise it.
- Would-send (bool): ONLY if ALL dimensions meet strict thresholds AND email has
  genuine insight, not just research facts with a name.

Thresholds for would_send:
- Personalization >= 3.5/5
- Relevance >= 3.5/5
- CTA >= 3.0/5
- Spam risk <= 1.5/5

Be strict: if it reads like a template even with one company name, don't send."""

    SHOULD_SEND_THRESHOLDS = {
        "personalization": 3.5,
        "relevance": 3.5,
        "cta": 3.0,
        "spam_risk": 1.5,  # LOWER is better
    }
