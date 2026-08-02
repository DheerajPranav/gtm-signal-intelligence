"""Standalone mini-eval runner for the GTM agent rubrics.

Deterministic by design — no LLM calls. It applies the rubric's own gates to
pre-scored inputs, so it runs offline, hermetically, and identically every time.
Use it to regression-test a scoring model's outputs, or to sanity-check the gates
themselves against the bundled good/bad fixtures.

Usage:
    python -m gtm_agent_evals run --rubric email_quality --input-file drafts.jsonl
    python -m gtm_agent_evals run --rubric icp --input-file companies.jsonl --json
    python -m gtm_agent_evals list

Input is JSONL, one record per line. Expected shape per rubric:
    email_quality: {"id": "...", "scores": {"personalization": 4, "relevance": 4,
                    "cta": 3.5, "spam_risk": 1}, "expected_would_send": true}
    icp:           {"id": "...", "dimensions": {"firmographic": 7, "technographic": 6,
                    "behavioral": 8, "timing": 7}, "expected_band": "strong"}
    persona:       {"id": "...", "persona": {...required fields...},
                    "expected_complete": true}

The `expected_*` field is optional; when present the runner reports agreement.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Callable

from .rubrics import EmailRubric, ICPRubric, PersonaRubric


def _score_email(row: dict) -> dict:
    result = EmailRubric.evaluate_would_send(row.get("scores", {}))
    out = {"prediction": result["would_send"], "detail": {"failures": result["failures"]}}
    if "expected_would_send" in row:
        out["expected"] = row["expected_would_send"]
        out["agree"] = out["prediction"] == row["expected_would_send"]
    return out


def _score_icp(row: dict) -> dict:
    overall = ICPRubric.compute_overall_score(row.get("dimensions", {}))
    band = ICPRubric.band(overall)
    out = {"prediction": band, "detail": {"overall": round(overall, 2)}}
    if "expected_band" in row:
        out["expected"] = row["expected_band"]
        out["agree"] = band == row["expected_band"]
    return out


def _score_persona(row: dict) -> dict:
    persona = row.get("persona", {})
    complete = PersonaRubric.is_complete(persona)
    missing = [f for f in PersonaRubric.REQUIRED_FIELDS if f not in persona]
    out = {"prediction": complete, "detail": {"missing_fields": missing}}
    if "expected_complete" in row:
        out["expected"] = row["expected_complete"]
        out["agree"] = complete == row["expected_complete"]
    return out


RUBRICS: dict[str, Callable[[dict], dict]] = {
    "email_quality": _score_email,
    "icp": _score_icp,
    "persona": _score_persona,
}


def _load_jsonl(path: str) -> list[dict]:
    rows: list[dict] = []
    stream = sys.stdin if path == "-" else open(path, encoding="utf-8")
    try:
        for lineno, line in enumerate(stream, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SystemExit(f"error: {path}:{lineno}: invalid JSON — {exc}")
    finally:
        if stream is not sys.stdin:
            stream.close()
    return rows


def run(rubric: str, input_file: str, as_json: bool) -> int:
    scorer = RUBRICS[rubric]
    rows = _load_jsonl(input_file)
    results = []
    graded = 0
    agreed = 0
    for i, row in enumerate(rows):
        scored = scorer(row)
        scored["id"] = row.get("id", f"row_{i}")
        results.append(scored)
        if "agree" in scored:
            graded += 1
            agreed += int(scored["agree"])

    if as_json:
        summary = {
            "rubric": rubric,
            "count": len(results),
            "graded": graded,
            "agreement": (agreed / graded) if graded else None,
            "results": results,
        }
        print(json.dumps(summary, indent=2))
        return 0

    print(f"Rubric: {rubric}   ({len(results)} record(s))\n")
    for r in results:
        mark = ""
        if "agree" in r:
            mark = "  ✓" if r["agree"] else f"  ✗ (expected {r['expected']})"
        detail = ", ".join(f"{k}={v}" for k, v in r["detail"].items())
        print(f"  {r['id']:<20} → {str(r['prediction']):<8} [{detail}]{mark}")
    if graded:
        print(f"\nAgreement vs labels: {agreed}/{graded} = {agreed / graded:.0%}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gtm-evals", description="Deterministic mini-eval runner for GTM rubrics."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="Score a JSONL file against a rubric.")
    p_run.add_argument(
        "--rubric", required=True, choices=sorted(RUBRICS), help="Which rubric to apply."
    )
    p_run.add_argument(
        "--input-file", required=True, help="Path to JSONL input ('-' for stdin)."
    )
    p_run.add_argument("--json", action="store_true", help="Emit a JSON report.")

    sub.add_parser("list", help="List available rubrics.")

    args = parser.parse_args(argv)

    if args.command == "list":
        print("Available rubrics:")
        for name in sorted(RUBRICS):
            print(f"  - {name}")
        return 0
    return run(args.rubric, args.input_file, args.json)


if __name__ == "__main__":
    raise SystemExit(main())
