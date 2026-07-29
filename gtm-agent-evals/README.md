# gtm-agent-evals

**Open-source LLM-judge rubric kit for GTM AI agents.**

Reusable evaluation rubrics for scoring ICP fit, building buyer personas, evaluating cold email quality, and conducting skeptical email critique. Framework-agnostic — use these rubrics to evaluate any company profile, persona, or email, not just output from the [gtm-outbound-agent](../gtm-outbound-agent/).

## Quick start

```bash
pip install gtm-agent-evals
```

```python
from gtm_agent_evals import ICPRubric, EmailRubric, CritiqueRubric

# Compute ICP fit score
fit_score = ICPRubric.compute_overall_score({
    "firmographic": 8.0,
    "technographic": 6.0,
    "behavioral": 9.0,  # RevOps hiring signal
    "timing": 7.0,
})
# → 8.0 (behavioral dominates at 0.45 weight)

# Validate persona completeness
from gtm_agent_evals import PersonaRubric
is_complete = PersonaRubric.is_complete({
    "title": "VP Revenue Operations",
    "department": "RevOps",
    "seniority": "vp",
    "pain_points": ["forecast accuracy", "pipeline visibility"],
    "priorities": ["ROI tracking", "cycle time"],
    "objections": ["cost", "implementation risk"],
    "buying_influence": "high",
})
# → True

# Get email scoring guidance
from gtm_agent_evals import EmailRubric
scoring_guide = EmailRubric.DIMENSIONS["personalization"]["scoring"]
# → {5: "A fact only research...", 4: "Company-specific...", ...}

# Get strict critique thresholds
from gtm_agent_evals import CritiqueRubric
should_send = CritiqueRubric.SHOULD_SEND_THRESHOLDS
# → {"personalization": 3.5, "relevance": 3.5, "cta": 3.0, "spam_risk": 1.5}
```

## Four rubrics

### 1. ICP Scoring Rubric (Day 10)

**Purpose:** Evaluate company fit across 4 dimensions.

**Dimensions:**
- **Firmographic** (0.20 weight): Company size, ARR, growth stage. Series B-D SaaS.
- **Technographic** (0.15 weight): Tech stack maturity (Salesforce, Snowflake, Looker).
- **Behavioral** (0.45 weight): RevOps hiring signals (VP hire, job postings, earnings mentions). **PRIMARY for RevOps platform.**
- **Timing** (0.20 weight): Recent hiring momentum, funding events, analyst coverage.

**Usage:**
```python
from gtm_agent_evals import ICPRubric

dimensions = {
    "firmographic": 7.0,    # Series C, 150 employees
    "technographic": 6.0,   # Salesforce + Snowflake
    "behavioral": 9.0,      # VP RevOps hire 2 months ago
    "timing": 6.0,          # Just closed Series B
}
fit_score = ICPRubric.compute_overall_score(dimensions)
# → 7.65 (behaviorally driven)
```

**Key insight:** A Series A with VP RevOps hire scores higher than Series D without RevOps leadership. Behavioral signal is **2.25× more important** than firmographic.

### 2. Persona Rubric (Day 11)

**Purpose:** Validate buyer persona completeness and grounding.

**Required fields:**
- Title (specific role, not generic)
- Department (Sales, RevOps, Marketing, etc.)
- Seniority (IC, Manager, Director, VP, C-Suite)
- Pain points (2-4, specific to segment)
- Priorities (2-4 operational goals)
- Objections (2-3 concerns they'll raise)
- Buying influence (high/medium/low)

**Usage:**
```python
from gtm_agent_evals import PersonaRubric, Seniority

persona = {
    "title": "VP Revenue Operations",
    "department": "RevOps",
    "seniority": Seniority.VP,
    "pain_points": [
        "Forecast accuracy (misses by 15-20% monthly)",
        "Pipeline visibility (no cross-functional view)",
    ],
    "priorities": ["ROI tracking", "Sales cycle compression"],
    "objections": ["Cost concern", "Implementation disruption"],
    "buying_influence": "high",
}

is_complete = PersonaRubric.is_complete(persona)
# → True
```

**Grounding:** Persona pain points should reference segment-specific vocabulary (e.g., "reconciliation" for fintech, "CI/CD" for devtools).

### 3. Email Rubric (Day 12)

**Purpose:** Score cold email quality across 5 dimensions.

**Dimensions (0-5 scale):**
- **Personalization:** Specific facts, not mail-merge templates. (5 = research-only fact; 0 = generic)
- **Relevance:** Pain framing matches persona's role and concerns. (5 = nails exact pain; 1 = misses mark)
- **CTA:** Specific, low-friction, time-bound ask. (5 = "15-min call Tue 2-4pm"; 1 = no ask)
- **Spam risk:** Would this trip filters? (5 = extreme signals; 1 = anti-spam design)
- **Would-send (bool):** Requires all dimensions to meet thresholds.

**Would-send gate (strict):**
- Personalization ≥ 3.5/5
- Relevance ≥ 3.5/5
- CTA ≥ 3.0/5
- Spam risk ≤ 1.5/5 (LOWER is better)

**Usage:**
```python
from gtm_agent_evals import EmailRubric

# Get scoring guide
guide = EmailRubric.DIMENSIONS["personalization"]["scoring"]
# {5: "A fact only research would surface...",
#  4: "Company-specific but public...", ...}

# Check would-send criteria
criteria = EmailRubric.DIMENSIONS["would_send"]["pass_criteria"]
# → Personalization must be ≥ 3.5, Relevance ≥ 3.5, etc.
```

**Key insight:** A 3/5 email is "technically fine" but usually not worth sending cold. Bias toward "no."

### 4. Critique Rubric (Day 13)

**Purpose:** Skeptical review of drafted emails; decide whether to send.

**System prompt template:**
```
You are a discerning B2B SDR manager reviewing cold outbound emails.
Be skeptical by default — most cold emails are mediocre.

Score five dimensions: personalization, relevance, CTA, spam_risk, would_send.

Would-send requires ALL thresholds met:
- Personalization >= 3.5/5
- Relevance >= 3.5/5
- CTA >= 3.0/5
- Spam risk <= 1.5/5

Be strict: if it reads like a template with one company name, don't send.
```

**Usage (as LLM system prompt):**
```python
from gtm_agent_evals import CritiqueRubric
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-3-5-haiku-20241022",
    max_tokens=500,
    system=CritiqueRubric.SYSTEM_PROMPT,
    messages=[
        {
            "role": "user",
            "content": f"Please critique this email...\n\n{email_text}",
        }
    ],
)
```

## Design principles

1. **Framework-agnostic**: Rubrics are data structures, not tied to any LLM framework.
2. **Computed gates**: Weights and thresholds are deterministic (not model-output). ICP score is computed, not asked of Claude.
3. **Honest scoring**: No inflated metrics. A 3/5 email is "ok", not "good". Critique rubric is deliberately skeptical.
4. **Grounded in practice**: Extracted from Days 10-13 of a production GTM AI system. Weights reflect real revenue-signal hierarchy.

## Testing

```bash
pip install -e ".[dev]"
pytest tests/
# → 30 tests, all passing
```

## Open source

MIT License. Use these rubrics in your own GTM AI system, evals platform, or revenue intelligence tool. Attribution appreciated, not required.

**Built by:** Dheeraj Pranav  
**Part of:** [gtm-signal-intelligence](https://github.com/DheerajPranav/gtm-signal-intelligence)  
**Live repo:** Week 1-3 of a 4-week GTM AI engineering sprint  

## Next: Framework integration

- **LangChain integration:** Load rubrics as prompt templates
- **LlamaIndex evals:** Use as custom eval metrics
- **OpenAI Evals:** Adapt for OpenAI eval harness
- **HubSpot plugin:** Score deals and leads live via HubSpot API
