"""Day 12 writing eval: does the fan-out produce 9 well-formed, grounded, on-angle emails?

Metrics map to the DoD:

  emails / angle_coverage   3 personas x 3 distinct angles = 9 emails, every angle present.
  subject_ok / body_ok      Fraction within the hard limits (<=60 chars, <=120 words).
  hook_traceability         Fraction of personalization hooks whose wording overlaps the
                            source data (profile + persona + case study). A lexical proxy,
                            NOT a semantic judge — it catches hooks that reference nothing in
                            the data, and nothing subtler.
  wall_clock_s              End-to-end fan-out time. Only meaningful on a live run (the DoD
                            target is < 90s); with a fake client it is ~0.

All model-dependent metrics are gated: no key -> readiness only, `not measured` never a
fabricated figure.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from gtm_outbound.agents.writing_agent import (  # noqa: E402
    ANGLES,
    BODY_MAX_WORDS,
    SUBJECT_MAX_CHARS,
    draft_all,
    word_count,
)
from gtm_outbound.agents.scoring_agent import render_profile  # noqa: E402
from gtm_outbound.models import (  # noqa: E402
    BuyingInfluence,
    Department,
    EmailDraft,
    Persona,
    Seniority,
)
from scoring_gold import GOLD  # noqa: E402

EVAL_DOMAIN = "flowmetric.io"


def eval_profile():
    return next(p for _, p in GOLD if p.target.domain == EVAL_DOMAIN)


def eval_personas() -> list[Persona]:
    return [
        Persona(id="p1__operations", title="VP RevOps", department=Department.OPERATIONS,
                seniority=Seniority.VP, buying_influence=BuyingInfluence.ECONOMIC_BUYER,
                pain_points=["pipeline hygiene is broken"], priorities=["forecast accuracy"],
                objections=["already on spreadsheets"]),
        Persona(id="p2__sales", title="VP Sales", department=Department.SALES,
                seniority=Seniority.VP, buying_influence=BuyingInfluence.CHAMPION,
                pain_points=["reps waste time on reporting"], priorities=["rep productivity"],
                objections=["change management"]),
        Persona(id="p3__finance", title="CRO", department=Department.FINANCE,
                seniority=Seniority.C_SUITE, buying_influence=BuyingInfluence.ECONOMIC_BUYER,
                pain_points=["board doesn't trust the forecast"], priorities=["forecast accuracy"],
                objections=["security review"]),
    ]


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower())) - _STOP


_STOP = {"the", "a", "an", "and", "or", "to", "of", "for", "in", "on", "with", "your",
         "you", "our", "we", "is", "are", "it", "at", "as", "by", "that", "this"}


def hook_traceable(hook: str, source_tokens: set[str]) -> bool:
    """A hook is traceable if at least two of its content words appear in the source data —
    two, not one, so a single stopword-ish coincidence doesn't count as grounding."""
    return len(_tokens(hook) & source_tokens) >= 2


def _has_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def score_drafts(drafts: list[EmailDraft], source_tokens: set[str], n_personas: int) -> dict:
    by_persona: dict[str, set[str]] = {}
    for d in drafts:
        by_persona.setdefault(d.persona_id, set()).add(d.variant_angle.value)
    full_coverage = sum(1 for a in by_persona.values() if len(a) == len(ANGLES))

    hooks = [h for d in drafts for h in d.personalization_hooks]
    return {
        "emails": len(drafts),
        "expected_emails": n_personas * len(ANGLES),
        "angle_coverage": round(full_coverage / n_personas, 4) if n_personas else None,
        "subject_ok": round(sum(len(d.subject) <= SUBJECT_MAX_CHARS for d in drafts) / len(drafts), 4) if drafts else None,
        "body_ok": round(sum(word_count(d.body) <= BODY_MAX_WORDS for d in drafts) / len(drafts), 4) if drafts else None,
        "hooks_ok": round(sum(len(d.personalization_hooks) == 3 for d in drafts) / len(drafts), 4) if drafts else None,
        "hook_traceability": round(sum(hook_traceable(h, source_tokens) for h in hooks) / len(hooks), 4) if hooks else None,
    }


def run_eval(
    client: Any = None,
    peer_provider: Any = None,
    offline: bool = False,
) -> dict:
    profile = eval_profile()
    personas = eval_personas()

    if offline or (client is None and not _has_key()):
        return {
            "mode": "offline",
            "company": profile.target.domain,
            "personas": len(personas),
            "expected_emails": len(personas) * len(ANGLES),
            "emails": None,
            "angle_coverage": None,
            "hook_traceability": None,
            "wall_clock_s": None,
            "note": (
                f"Offline: no emails drafted. {len(personas)} personas x {len(ANGLES)} angles "
                f"= {len(personas) * len(ANGLES)} emails expected on a live run."
            ),
        }

    if peer_provider is None:
        from gtm_outbound.peerproof import KBPeerProofProvider

        peer_provider = KBPeerProofProvider()

    source = render_profile(profile) + " " + " ".join(
        p.title + " " + " ".join(p.pain_points + p.priorities + p.objections) for p in personas
    )
    if peer_provider is not None:
        source += " " + peer_provider.get_case_study(profile).text
    source_tokens = _tokens(source)

    started = time.perf_counter()
    drafts = asyncio.run(
        draft_all(profile, personas, peer_provider=peer_provider, client=client)
    )
    wall = time.perf_counter() - started

    result = {"mode": "full", "company": profile.target.domain, "personas": len(personas)}
    result.update(score_drafts(drafts, source_tokens, len(personas)))
    result["wall_clock_s"] = round(wall, 3)
    result["under_90s"] = wall < 90
    return result


def format_report(r: dict) -> str:
    def fmt(v: Any) -> str:
        return "not measured" if v is None else str(v)

    lines = [
        "# Writing Eval — Async Fan-out",
        "",
        f"**Mode:** `{r['mode']}`  ",
        f"**Company:** {r['company']} · {r['personas']} personas · "
        f"expecting {r['expected_emails']} emails",
        "",
    ]
    if r.get("emails") is None:
        lines += [
            "> **Not measured.** Drafting needs live model calls and no `ANTHROPIC_API_KEY`",
            "> was present. The fixture is ready; set the key and re-run. Metrics below stay",
            "> `not measured` rather than fabricated.",
            "",
        ]
    lines += [
        "| Metric | Value | DoD |",
        "|---|---|---|",
        f"| Emails produced | {fmt(r.get('emails'))} | {r['expected_emails']} (3x3) |",
        f"| Angle coverage | {fmt(r.get('angle_coverage'))} | every persona all 3 angles |",
        f"| Subject <= {SUBJECT_MAX_CHARS} chars | {fmt(r.get('subject_ok'))} | 1.0 |",
        f"| Body <= {BODY_MAX_WORDS} words | {fmt(r.get('body_ok'))} | 1.0 |",
        f"| Hooks = 3 | {fmt(r.get('hooks_ok'))} | 1.0 |",
        f"| Hook traceability (proxy) | {fmt(r.get('hook_traceability'))} | hooks trace to data |",
        f"| Wall-clock (s) | {fmt(r.get('wall_clock_s'))} | < 90 |",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Evaluate the writing agent.")
    ap.add_argument("--offline", action="store_true", help="readiness only; draft nothing")
    args = ap.parse_args()

    results = run_eval(offline=args.offline)
    out = Path(__file__).parent
    (out / "writing_report.md").write_text(format_report(results), encoding="utf-8")
    print(f"mode={results['mode']}  emails={results.get('emails')}  "
          f"wall_clock_s={results.get('wall_clock_s')}")
    print(f"report -> {out / 'writing_report.md'}")


if __name__ == "__main__":
    main()
