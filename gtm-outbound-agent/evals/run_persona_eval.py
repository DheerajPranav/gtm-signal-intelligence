"""Day 11 persona eval: are the cards well-formed, KB-grounded, and company-specific?

Three metrics map to the three DoD clauses:

  count_ok        Fraction of companies that returned exactly N fully-populated cards.

  kb_grounding    Fraction of personas whose card text uses Northstar positioning language
                  (POSITIONING_TERMS). A DELIBERATELY SHALLOW lexical proxy, not a semantic
                  judge — it catches generic-B2B filler that name-drops no Northstar concept,
                  and nothing subtler. Labeled as a proxy so it is never read as "grounded."

  distinctness    Mean pairwise Jaccard distance between companies' pain-point vocabularies.
                  High = a fintech and a devtools company got different cards, which is the
                  "vary meaningfully by company" clause. Needs >= 2 companies.

All three need live model output, so all three are gated: no key -> readiness only, and the
metrics report `not measured` rather than a fabricated figure.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from itertools import combinations
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from gtm_outbound.agents.persona_agent import DEFAULT_N, build_personas  # noqa: E402
from gtm_outbound.models import Persona  # noqa: E402
from gtm_outbound.positioning import POSITIONING_TERMS  # noqa: E402
from scoring_gold import GOLD  # noqa: E402

# Contrasting industries so "varies by company" is actually testable.
EVAL_DOMAINS = ("gridpoint.app", "tinyscale.io", "stablmotion.com", "flowmetric.io")


def eval_profiles() -> list:
    by_domain = {p.target.domain: p for _, p in GOLD}
    return [by_domain[d] for d in EVAL_DOMAINS if d in by_domain]


def card_text(p: Persona) -> str:
    # Title is excluded on purpose: a "VP RevOps" title trivially contains "revops", so
    # counting it would mark every card grounded regardless of how the pains are framed.
    # The proxy is about the *framing* using Northstar language, not the job title.
    return " ".join([*p.pain_points, *p.priorities, *p.objections]).lower()


def is_grounded(p: Persona) -> bool:
    text = card_text(p)
    return any(term in text for term in POSITIONING_TERMS)


def _tokens(strings: list[str]) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", " ".join(strings).lower()))


def distinctness(pain_sets: list[set[str]]) -> Optional[float]:
    """Mean pairwise Jaccard distance. None with fewer than two companies."""
    if len(pain_sets) < 2:
        return None
    dists = []
    for a, b in combinations(pain_sets, 2):
        union = a | b
        jac = len(a & b) / len(union) if union else 0.0
        dists.append(1.0 - jac)
    return sum(dists) / len(dists)


def _has_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def run_eval(
    client: Any = None,
    positioning_provider: Any = None,
    n: int = DEFAULT_N,
    offline: bool = False,
) -> dict:
    profiles = eval_profiles()

    if offline or (client is None and not _has_key()):
        return {
            "mode": "offline",
            "companies": len(profiles),
            "personas_per_company": n,
            "count_ok": None,
            "kb_grounding": None,
            "distinctness": None,
            "note": (
                f"Offline: no personas built. {len(profiles)} contrasting companies ready "
                f"(target {n} personas each)."
            ),
        }

    if positioning_provider is None:
        from gtm_outbound.positioning import KBPositioningProvider

        positioning_provider = KBPositioningProvider()

    rows: list[dict] = []
    all_personas: list[Persona] = []
    pain_sets: list[set[str]] = []
    count_hits = 0
    errors = 0

    for profile in profiles:
        try:
            personas = build_personas(
                profile, positioning_provider=positioning_provider, client=client, n=n
            )
        except Exception as e:
            errors += 1
            rows.append({"domain": profile.target.domain, "error": f"{type(e).__name__}: {e}"})
            continue

        full = [
            p for p in personas
            if p.pain_points and p.priorities and p.objections
        ]
        if len(personas) == n and len(full) == n:
            count_hits += 1
        all_personas.extend(personas)
        pain_sets.append(_tokens([pp for p in personas for pp in p.pain_points]))
        rows.append({
            "domain": profile.target.domain,
            "n_personas": len(personas),
            "grounded": sum(is_grounded(p) for p in personas),
            "titles": [p.title for p in personas],
        })

    scored = [r for r in rows if "error" not in r]
    return {
        "mode": "full",
        "companies": len(profiles),
        "scored_companies": len(scored),
        "errored_companies": errors,
        "personas_per_company": n,
        "count_ok": round(count_hits / len(scored), 4) if scored else None,
        "kb_grounding": (
            round(sum(is_grounded(p) for p in all_personas) / len(all_personas), 4)
            if all_personas else None
        ),
        "distinctness": (
            round(d, 4) if (d := distinctness(pain_sets)) is not None else None
        ),
        "rows": rows,
    }


def format_report(r: dict) -> str:
    def fmt(v: Any) -> str:
        return "not measured" if v is None else str(v)

    lines = [
        "# Persona Eval — Buyer Discovery Agent",
        "",
        f"**Mode:** `{r['mode']}`  ",
        f"**Companies:** {r['companies']} (target {r['personas_per_company']} personas each)",
        "",
    ]
    if r["count_ok"] is None:
        lines += [
            "> **Not measured.** Persona discovery needs a live model call and no",
            "> `ANTHROPIC_API_KEY` was present. The contrasting company set is ready; set the",
            "> key and re-run. Metrics below stay `not measured` rather than fabricated.",
            "",
        ]
    lines += [
        "| Metric | Value | Maps to DoD |",
        "|---|---|---|",
        f"| Exactly N complete cards | {fmt(r['count_ok'])} | 3 fully-populated personas |",
        f"| KB grounding (lexical proxy) | {fmt(r.get('kb_grounding'))} | references Northstar language |",
        f"| Cross-company distinctness | {fmt(r.get('distinctness'))} | cards vary by company |",
        "",
    ]
    if r.get("rows"):
        lines += ["| Company | Personas | Grounded | Titles |", "|---|---|---|---|"]
        for row in r["rows"]:
            if "error" in row:
                lines.append(f"| {row['domain']} | — | — | ERROR: {row['error']} |")
            else:
                lines.append(
                    f"| {row['domain']} | {row['n_personas']} | "
                    f"{row['grounded']}/{row['n_personas']} | {', '.join(row['titles'])} |"
                )
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Evaluate the persona agent.")
    ap.add_argument("--offline", action="store_true",
                    help="report readiness only; build no personas")
    args = ap.parse_args()

    results = run_eval(offline=args.offline)
    out = Path(__file__).parent
    (out / "persona_report.md").write_text(format_report(results), encoding="utf-8")

    print(f"mode={results['mode']}  companies={results['companies']}")
    print(f"  count_ok      {results['count_ok']}")
    print(f"  kb_grounding  {results.get('kb_grounding')}")
    print(f"  distinctness  {results.get('distinctness')}")
    print(f"\nreport -> {out / 'persona_report.md'}")


if __name__ == "__main__":
    main()
