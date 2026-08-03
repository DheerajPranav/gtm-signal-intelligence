"""Comparison: does the email rubric actually separate great cold emails from templated ones?

Five hand-written "great" cold emails (specific trigger, tight pain, low-friction ask,
authentic tone) vs. five obviously templated / spammy ones. We run the deterministic
would-send gate (EmailRubric.evaluate_would_send) and show it cleanly splits them.

Scoring the raw *text* into the five dimensions is the one step that needs judgment:

- With ANTHROPIC_API_KEY set, `score_email_text` asks Claude to score the dimensions
  (structured tool use), and the deterministic gate decides would-send from those scores.
- With no key, it falls back to the bundled hand-scores below — assigned by applying the
  rubric anchors by hand, so the demo runs offline and reproducibly. These are labelled
  illustrative, not a live model run.

Either way, the *decision* (would-send) is computed by the rubric, not asserted.

Run:  python examples/email_comparison.py
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from gtm_agent_evals import EmailRubric

EMAILS: list[dict] = [
    # ---- Five great cold emails -------------------------------------------------
    {
        "id": "g1_funding_trigger",
        "label": "great",
        "text": (
            "Subject: your Series C + 40 new AEs\n\n"
            "Saw Northstar closed the $60M round last week and you're hiring 40 AEs into "
            "H2. That kind of ramp usually breaks pipeline hygiene before the reps even "
            "hit quota. We helped Forgestack keep forecast accuracy above 90% through a "
            "similar doubling. Worth 15 minutes Tuesday to compare notes on ramp-proofing "
            "the pipeline?"
        ),
        "scores": {"personalization": 5, "relevance": 4.5, "cta": 4, "spam_risk": 1},
    },
    {
        "id": "g2_job_posting_pain",
        "label": "great",
        "text": (
            "Subject: your open RevOps Analyst req\n\n"
            "Your RevOps Analyst posting lists 'reconciling Salesforce and the warehouse "
            "by hand' as a core duty — that's usually a sign forecasts are being rebuilt "
            "in spreadsheets. We automate exactly that join. Open to a short call Thursday "
            "to see if it'd save your team the manual reconciliation?"
        ),
        "scores": {"personalization": 4, "relevance": 4, "cta": 3.5, "spam_risk": 1},
    },
    {
        "id": "g3_peer_proof",
        "label": "great",
        "text": (
            "Subject: how Ledgerly cut deal-desk cycle 30%\n\n"
            "You mentioned 'quote turnaround' as a 2026 priority on the earnings call. "
            "Ledgerly, similar size and also fintech, cut deal-desk cycle time 30% by "
            "wiring approvals into their CRM. Happy to walk through what they changed — "
            "would 20 minutes Wednesday work?"
        ),
        "scores": {"personalization": 4.5, "relevance": 4.5, "cta": 4, "spam_risk": 0.5},
    },
    {
        "id": "g4_specific_metric",
        "label": "great",
        "text": (
            "Subject: 11 days of AE ramp\n\n"
            "Congrats on the Gartner mention. Fast-growing teams like yours tell us new "
            "AEs lose ~11 days a quarter to CRM cleanup instead of selling. We give that "
            "time back. If that number rings true, is a quick Friday call worth it?"
        ),
        "scores": {"personalization": 4, "relevance": 3.5, "cta": 3, "spam_risk": 1},
    },
    {
        "id": "g5_named_person",
        "label": "great",
        "text": (
            "Subject: for your new VP RevOps\n\n"
            "Congrats on Priya joining as VP RevOps last month — first 90 days usually "
            "means an audit of pipeline data quality. That's exactly where we plug in; "
            "Cliniva's VP used us to get a clean baseline in week two. Want me to send "
            "the 2-page teardown, or grab 15 minutes next week?"
        ),
        "scores": {"personalization": 5, "relevance": 4, "cta": 4, "spam_risk": 1},
    },
    # ---- Five templated / spammy emails ----------------------------------------
    {
        "id": "t1_mail_merge",
        "label": "templated",
        "text": (
            "Subject: Quick question {{first_name}}\n\n"
            "Hi {{first_name}}, I hope this email finds you well! I wanted to reach out "
            "because I think {{company}} could really benefit from our solution. We help "
            "companies like yours drive growth. Do you have 30 minutes this week to hop "
            "on a call?"
        ),
        "scores": {"personalization": 1.5, "relevance": 2, "cta": 2, "spam_risk": 3},
    },
    {
        "id": "t2_generic_value",
        "label": "templated",
        "text": (
            "Subject: Grow your revenue\n\n"
            "Hello, We are a leading provider of revenue solutions trusted by hundreds of "
            "companies. Our platform leverages cutting-edge AI to optimize your sales. "
            "Let me know if you'd like to learn more!"
        ),
        "scores": {"personalization": 1, "relevance": 2, "cta": 2, "spam_risk": 3},
    },
    {
        "id": "t3_hype_spam",
        "label": "templated",
        "text": (
            "Subject: 🚀🚀 10X YOUR PIPELINE NOW!!!\n\n"
            "ACT FAST — this offer won't last! Our REVOLUTIONARY platform GUARANTEES 10X "
            "results. Don't miss out!!! Reply YES to claim your FREE demo today!!!"
        ),
        "scores": {"personalization": 2, "relevance": 2, "cta": 3, "spam_risk": 4},
    },
    {
        "id": "t4_vague_ask",
        "label": "templated",
        "text": (
            "Subject: touching base\n\n"
            "Hi there, Just wanted to touch base and see if revenue operations is a "
            "priority for you this year. We do a lot in this space. Let me know your "
            "thoughts whenever you get a chance!"
        ),
        "scores": {"personalization": 3, "relevance": 3.5, "cta": 1.5, "spam_risk": 2},
    },
    {
        "id": "t5_wrong_fit",
        "label": "templated",
        "text": (
            "Subject: Partnership opportunity\n\n"
            "Dear Sir/Madam, We offer world-class SEO and social media marketing packages "
            "starting at $99/month. Boost your online presence today! Interested in a "
            "partnership?"
        ),
        "scores": {"personalization": 1, "relevance": 1, "cta": 2, "spam_risk": 3},
    },
]


def score_email_text(email: dict) -> tuple[dict, str]:
    """Return (dimension_scores, source). Uses Claude if a key is present, else the
    bundled hand-scores. Source is 'llm' or 'illustrative'."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        try:
            return _score_with_llm(email["text"]), "llm"
        except Exception:  # pragma: no cover - network/SDK issues fall back cleanly
            pass
    return email["scores"], "illustrative"


def _score_with_llm(text: str) -> dict:  # pragma: no cover - requires a live key
    import anthropic

    client = anthropic.Anthropic()
    tool = {
        "name": "score_email",
        "description": "Score a cold email on the GTM email rubric (0-5 per dimension).",
        "input_schema": {
            "type": "object",
            "properties": {
                "personalization": {"type": "number"},
                "relevance": {"type": "number"},
                "cta": {"type": "number"},
                "spam_risk": {"type": "number"},
            },
            "required": ["personalization", "relevance", "cta", "spam_risk"],
            "additionalProperties": False,
        },
    }
    msg = client.messages.create(
        model="claude-3-5-haiku-latest",
        max_tokens=300,
        tools=[tool],
        tool_choice={"type": "tool", "name": "score_email"},
        messages=[{"role": "user", "content": f"{EmailRubric.__doc__}\n\nEmail:\n{text}"}],
    )
    for block in msg.content:
        if block.type == "tool_use":
            return dict(block.input)
    raise RuntimeError("model did not return a tool call")


@dataclass
class Row:
    id: str
    label: str
    would_send: bool
    scores: dict
    source: str


def evaluate_all() -> list[Row]:
    rows: list[Row] = []
    for email in EMAILS:
        scores, source = score_email_text(email)
        decision = EmailRubric.evaluate_would_send(scores)
        rows.append(Row(email["id"], email["label"], decision["would_send"], scores, source))
    return rows


def summarize(rows: list[Row]) -> dict:
    great = [r for r in rows if r.label == "great"]
    templated = [r for r in rows if r.label == "templated"]
    great_send = sum(r.would_send for r in great)
    templated_send = sum(r.would_send for r in templated)
    avg = lambda rs: sum(r.scores.get("spam_risk", 0) for r in rs) / len(rs)
    return {
        "great_would_send": f"{great_send}/{len(great)}",
        "templated_would_send": f"{templated_send}/{len(templated)}",
        "separated": great_send == len(great) and templated_send == 0,
        "spam_gap": round(avg(templated) - avg(great), 2),  # positive = templated worse
    }


def main() -> int:
    rows = evaluate_all()
    source = rows[0].source if rows else "illustrative"
    print(f"Email rubric comparison  (scores source: {source})\n")
    print(f"  {'id':<22} {'label':<10} would_send")
    print(f"  {'-' * 22} {'-' * 10} {'-' * 10}")
    for r in rows:
        print(f"  {r.id:<22} {r.label:<10} {r.would_send}")
    s = summarize(rows)
    print(
        f"\n  great: {s['great_would_send']} would-send   "
        f"templated: {s['templated_would_send']} would-send"
    )
    print(f"  spam-risk gap (templated - great): +{s['spam_gap']}")
    print(f"  cleanly separated: {s['separated']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
