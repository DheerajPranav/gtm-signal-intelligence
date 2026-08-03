# gtm-agent-evals

**The eval kit for GTM agents I wish existed when I started.**

Open-source LLM-judge rubrics for scoring ICP fit, building buyer personas, evaluating cold email quality, and conducting skeptical email critique. Framework-agnostic — use these rubrics to evaluate any company profile, persona, or email, not just output from the [gtm-outbound-agent](../gtm-outbound-agent/).

The LLM scores each dimension; the **pass/fail and overall numbers are computed in code** — so the gates are inspectable, testable, and adjustable without re-prompting. Every threshold and weight is documented in [`docs/CALIBRATION.md`](docs/CALIBRATION.md).

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

## Mini-eval runner

A standalone, **deterministic** runner scores a JSONL file against a rubric — no LLM
calls, so it's hermetic and identical every time. Use it to regression-test a scoring
model's outputs, or to sanity-check the gates against the bundled good/bad fixtures.

```bash
python -m gtm_agent_evals list          # -> email_quality, icp, persona
# or the installed console script:
gtm-evals run --rubric email_quality --input-file examples/data/email_quality.jsonl
```

```
Rubric: email_quality   (10 record(s))

  good_funding_hook    → True     [failures=[]]  ✓
  ...
  bad_spammy_hype      → False    [failures=['spam_risk 4 > 1.5 (max)']]  ✓

Agreement vs labels: 10/10 = 100%
```

Each rubric ships **5 passing / 5 failing** example records in
[`examples/data/`](examples/data/) with `expected_*` labels, so the runner reports
agreement and demonstrates that the gates actually separate good from bad. Input shapes and
`--json` output are documented in the module docstring; the anchors are explained in
[`docs/CALIBRATION.md`](docs/CALIBRATION.md).

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
# → rubric tests passing
```

## Open source

MIT License. Use these rubrics in your own GTM AI system, evals platform, or revenue intelligence tool. Attribution appreciated, not required.

**Built by:** Dheeraj Pranav  
**Part of:** [gtm-signal-intelligence](https://github.com/DheerajPranav/gtm-signal-intelligence)  
**Live repo:** Week 1-3 of a 4-week GTM AI engineering sprint  

## Integration examples (Day 20)

The package includes three production-ready integration examples:

### 1. LangChain Integration

Wrap rubrics as LangChain evaluators (framework-agnostic):

```python
from examples.langchain_integration import LangChainICPEvaluator

evaluator = LangChainICPEvaluator()
result = evaluator.evaluate({
    "firmographic": 7.0,
    "technographic": 6.0,
    "behavioral": 9.0,
    "timing": 6.0,
})
# → {"passed": True, "score": 7.55, ...}
```

**Includes:**
- `LangChainICPEvaluator`: ICP scoring wrapper
- `LangChainEmailEvaluator`: Email would-send decision
- `LangChainPersonaEvaluator`: Persona completeness check

### 2. External Dataset Evaluation Harness

Test rubrics on external datasets without agent dependency:

```python
from examples.external_dataset_evals import ExternalDatasetEvaluator

evaluator = ExternalDatasetEvaluator()
result = evaluator.eval_icp_dataset("gold_companies.jsonl")
# → {"rubric": "ICPRubric", "total": 100, "accuracy": 0.95, ...}

# Generate markdown report
report = evaluator.generate_report()
```

**Dataset formats (JSONL):**
```json
// ICP gold dataset
{"company": "Acme", "dimensions": {...}, "expected_score": 7.5}

// Email gold dataset
{"email_id": "123", "scores": {...}, "expected_would_send": true}

// Persona gold dataset
{"persona_id": "123", "persona": {...}, "expected_complete": true}
```

### 3. Streamlit Interactive Explorer

Visual rubric browser and scorer:

```bash
streamlit run examples/streamlit_app.py
```

**Features:**
- View all rubrics and dimension weights
- Interactive sliders to compute scores
- Threshold checking for would-send decisions
- Grounding terms by segment (fintech, devtools, etc.)
- Copy-paste ready system prompts

## Testing

```bash
# Test rubrics
pytest tests/test_rubrics.py -v

# Test integrations (requires examples in PYTHONPATH)
PYTHONPATH=. pytest tests/test_integrations.py -v

# All tests
PYTHONPATH=. pytest tests/ -v
# → 55 tests, all passing (22 rubric + 13 integration + 16 runner + 4 comparison)
```

## Next: Framework integration

- **LlamaIndex evals:** Use as custom eval metrics
- **OpenAI Evals:** Adapt for OpenAI eval harness
- **Hugging Face:** Integration with HF Evaluator API
- **HubSpot plugin:** Score deals and leads live via HubSpot API
