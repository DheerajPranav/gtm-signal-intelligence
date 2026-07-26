"""Day 13 critique eval: does the judge agree with a human on what to send?

A small **calibration set** of emails written to be clearly good or clearly bad, with a
would-send label assigned by construction (a hypey, generic, vague-CTA email is a no; a
specific, low-friction one is a yes). Because we wrote them, the labels are honest without a
live lookup — the same move as the scoring gold set.

Metrics (gated on a live model call, else `not measured`):
  would_send_agreement   Fraction where the judge's would_send matches the label.
  spam_gap               Mean spam_risk on the bad set minus the good set. A judge that
                         works should score the spammy emails riskier; a non-positive gap
                         means it isn't discriminating.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from gtm_outbound.agents.critique_agent import evaluate  # noqa: E402
from gtm_outbound.models import (  # noqa: E402
    BuyingInfluence,
    CompanyProfile,
    Department,
    EmailDraft,
    Persona,
    Seniority,
    Sourced,
    TargetCompany,
    VariantAngle,
)

NOW = datetime(2026, 7, 1, tzinfo=timezone.utc)


def _profile() -> CompanyProfile:
    def s(v):
        return Sourced[str](value=v, source_url="https://flowmetric.io/about", confidence=0.9)
    return CompanyProfile(
        target=TargetCompany(domain="flowmetric.io", name="FlowMetric"), last_updated=NOW,
        industry=s("B2B SaaS"), sub_industry=s("RevOps analytics"),
        size_band=s("500-1000"), funding_stage=s("Series C"),
        tech_stack=[s("Salesforce"), s("Snowflake")],
        buying_signals=[s("Hired VP RevOps 3 months ago")],
    )


def _persona() -> Persona:
    return Persona(id="p1__operations", title="VP RevOps", department=Department.OPERATIONS,
                   seniority=Seniority.VP, buying_influence=BuyingInfluence.ECONOMIC_BUYER,
                   pain_points=["pipeline hygiene is broken"], priorities=["forecast accuracy"],
                   objections=["already on spreadsheets"])


def _email(subject, body, hooks, angle=VariantAngle.PAIN_LED) -> EmailDraft:
    return EmailDraft(persona_id="p1__operations", variant_id="p1__operations__pain",
                      subject=subject, body=body, personalization_hooks=list(hooks),
                      variant_angle=angle)


# label = expected would_send. Written to be unambiguous at the extremes.
CALIBRATION: list[tuple[str, bool, EmailDraft]] = [
    ("good", True, _email(
        "Forecast accuracy after your RevOps hire",
        "Congrats on bringing on a VP RevOps. Teams your size on Salesforce + Snowflake "
        "usually hit 90% forecast accuracy within two quarters with Northstar. Worth 15 "
        "minutes next week to compare notes?",
        ["hired VP RevOps", "Salesforce + Snowflake", "Series C stage"])),
    ("good", True, _email(
        "Pipeline hygiene at FlowMetric",
        "Saw FlowMetric is scaling the sales team. Most RevOps leaders at this stage fight "
        "spreadsheet forecasting. Northstar sits on your warehouse and gives one source of "
        "truth. Open to a quick look Thursday?",
        ["scaling sales team", "warehouse-native", "spreadsheet forecasting"])),
    ("good", True, _email(
        "Question about your Q3 forecast process",
        "Quick one: how are you reconciling pipeline between Salesforce and the warehouse "
        "today? Northstar automates that for RevOps teams your size. Happy to send a 2-min "
        "Loom if useful.",
        ["Salesforce", "warehouse", "RevOps team"])),
    ("bad", False, _email(
        "REVOLUTIONARY AI TO 10X YOUR REVENUE!!!",
        "Dear Sir/Madam, our REVOLUTIONARY AI platform will TRANSFORM your business and 10X "
        "revenue INSTANTLY!! Don't miss out — LIMITED TIME! Reply NOW to unlock exclusive "
        "access to the future of sales!!!",
        ["your business", "the future", "exclusive access"])),
    ("bad", False, _email(
        "Touching base",
        "Hi there, I wanted to reach out to see if you'd be interested in learning more "
        "about our solution. We help companies like yours succeed. Let me know if you want "
        "to hop on a call sometime.",
        ["companies like yours", "our solution", "a call"])),
    ("bad", False, _email(
        "Partnership opportunity",
        "Hello, I came across your company and think there could be great synergy. Our "
        "best-in-class platform is used by industry leaders worldwide. Circle back if you'd "
        "like to explore synergies and take things to the next level.",
        ["your company", "industry leaders", "synergies"])),
]


def _has_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def run_eval(client: Any = None, offline: bool = False) -> dict:
    counts = {"good": sum(1 for lbl, _, _ in CALIBRATION if lbl == "good"),
              "bad": sum(1 for lbl, _, _ in CALIBRATION if lbl == "bad")}

    if offline or (client is None and not _has_key()):
        return {
            "mode": "offline", "total": len(CALIBRATION), "label_counts": counts,
            "would_send_agreement": None, "spam_gap": None,
            "note": f"Offline: no critique run. {len(CALIBRATION)} calibration emails ready.",
        }

    profile, persona = _profile(), _persona()
    agree = 0
    good_spam, bad_spam = [], []
    rows, errors = [], 0

    for label, expected, email in CALIBRATION:
        try:
            ev = evaluate(email, persona, profile, client=client)
        except Exception as e:
            errors += 1
            rows.append({"subject": email.subject, "error": f"{type(e).__name__}: {e}"})
            continue
        agree += int(ev.would_send == expected)
        (good_spam if label == "good" else bad_spam).append(ev.spam_risk)
        rows.append({"subject": email.subject, "label": label, "expected": expected,
                     "would_send": ev.would_send, "spam_risk": ev.spam_risk})

    scored = len(CALIBRATION) - errors
    return {
        "mode": "full", "total": len(CALIBRATION), "scored": scored, "errored": errors,
        "label_counts": counts,
        "would_send_agreement": round(agree / scored, 4) if scored else None,
        "spam_gap": (round(mean(bad_spam) - mean(good_spam), 4)
                     if good_spam and bad_spam else None),
        "rows": rows,
    }


def format_report(r: dict) -> str:
    def fmt(v: Any) -> str:
        return "not measured" if v is None else str(v)

    lines = [
        "# Critique Eval — Judge Calibration",
        "",
        f"**Mode:** `{r['mode']}`  ",
        f"**Calibration emails:** {r['total']} "
        f"({r['label_counts']['good']} good / {r['label_counts']['bad']} bad)",
        "",
    ]
    if r["would_send_agreement"] is None:
        lines += [
            "> **Not measured.** Critique needs a live model call and no `ANTHROPIC_API_KEY`",
            "> was present. The calibration set is ready; set the key and re-run.",
            "",
        ]
    lines += [
        "| Metric | Value | Reads well when |",
        "|---|---|---|",
        f"| Would-send agreement | {fmt(r['would_send_agreement'])} | → 1.0 |",
        f"| Spam gap (bad − good) | {fmt(r.get('spam_gap'))} | clearly positive |",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Evaluate the critique agent.")
    ap.add_argument("--offline", action="store_true", help="readiness only; critique nothing")
    args = ap.parse_args()

    results = run_eval(offline=args.offline)
    out = Path(__file__).parent
    (out / "critique_report.md").write_text(format_report(results), encoding="utf-8")
    print(f"mode={results['mode']}  agreement={results['would_send_agreement']}  "
          f"spam_gap={results.get('spam_gap')}")
    print(f"report -> {out / 'critique_report.md'}")


if __name__ == "__main__":
    main()
