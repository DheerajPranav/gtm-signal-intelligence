"""Day 9 enrichment eval: field accuracy, URL grounding, and coverage.

Three metrics, with very different measurement costs:

  url_grounding   Every `source_url` the agent cited must be a URL it actually
                  retrieved during the run. Fully deterministic — an invented URL is
                  caught with no model and no network. This is the strongest available
                  hallucination signal and it always runs.

  coverage        Fraction of scalar fields the agent managed to source at all.
                  Separates "wrong" from "didn't find", which a bare accuracy number
                  conflates.

  field_accuracy  Requires hand-verified ground truth. Rows with `verified: false` are
                  EXCLUDED and counted separately; if none are verified the metric
                  reports `not measured` rather than a number. See evals/README.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gtm_outbound.agents.research_agent import ResearchTrace, enrich  # noqa: E402
from gtm_outbound.models import CompanyProfile  # noqa: E402

SCALAR_FIELDS = ("industry", "sub_industry", "size_band", "funding_stage")


@dataclass
class RowResult:
    domain: str
    verified: bool
    coverage: float
    url_grounding: Optional[float]
    field_hits: int = 0
    field_comparable: int = 0
    ungrounded_urls: list[str] = field(default_factory=list)
    error: Optional[str] = None


def load_gold(path: Optional[Path] = None) -> list[dict]:
    p = path or Path(__file__).parent / "enrichment_gold.jsonl"
    with open(p, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def retrieved_urls(trace: ResearchTrace) -> set[str]:
    """URLs the agent asked for. `fetch_page` is the only tool that names a URL up
    front; search results are discovered, so grounding is checked against the union of
    fetched URLs and whatever the provider returned (recorded by the caller)."""
    return {
        args["url"]
        for name, args in trace.tool_calls
        if name == "fetch_page" and "url" in args
    }


def score_url_grounding(profile: CompanyProfile, seen_urls: set[str]) -> tuple[float, list[str]]:
    """Fraction of cited URLs that the agent actually retrieved.

    A citation to a URL that never appeared in any tool result is fabricated
    provenance — the most damaging failure mode here, because it looks sourced.
    """
    cited = [v.source_url for v in profile.sourced_values()]
    if not cited:
        return 1.0, []  # nothing claimed, nothing fabricated
    bad = [u for u in cited if u not in seen_urls]
    return (len(cited) - len(bad)) / len(cited), sorted(set(bad))


def score_fields(profile: CompanyProfile, expected: dict) -> tuple[int, int]:
    """(hits, comparable). Null expectations are skipped, not counted as misses."""
    hits = comparable = 0
    for name in SCALAR_FIELDS:
        want = expected.get(name)
        if want is None:
            continue
        comparable += 1
        got = getattr(profile, name)
        if got is not None and got.value.strip().casefold() == str(want).strip().casefold():
            hits += 1
    return hits, comparable


def run_eval(
    provider: Any = None,
    client: Any = None,
    gold_path: Optional[Path] = None,
    offline: bool = False,
) -> dict:
    gold = load_gold(gold_path)
    rows: list[RowResult] = []

    if offline:
        # Report what can be known without running anything: how much of the gold set
        # is actually usable. Never emit accuracy or grounding figures here.
        verified = sum(1 for g in gold if g.get("verified"))
        return {
            "mode": "offline",
            "total_rows": len(gold),
            "verified_rows": verified,
            "field_accuracy": None,
            "url_grounding": None,
            "coverage": None,
            "rows": [],
            "note": (
                "Offline run: no enrichment executed. "
                f"{verified}/{len(gold)} gold rows are verified."
            ),
        }

    if provider is None:
        from gtm_outbound.tools.web import TavilyProvider

        provider = TavilyProvider()

    for entry in gold:
        domain = entry["domain"]
        try:
            profile, trace = enrich(
                domain, provider, client=client, name=entry.get("name")
            )
        except Exception as e:  # one bad domain must not sink the run
            rows.append(
                RowResult(domain, bool(entry.get("verified")), 0.0, None,
                          error=f"{type(e).__name__}: {e}")
            )
            continue

        seen = retrieved_urls(trace) | set(getattr(provider, "served_urls", set()))
        grounding, bad = score_url_grounding(profile, seen)
        hits, comparable = score_fields(profile, entry.get("expected", {}))

        rows.append(
            RowResult(
                domain=domain,
                verified=bool(entry.get("verified")),
                coverage=profile.coverage(),
                url_grounding=grounding,
                field_hits=hits,
                field_comparable=comparable,
                ungrounded_urls=bad,
            )
        )

    ok = [r for r in rows if r.error is None]
    scored = [r for r in ok if r.verified and r.field_comparable]
    total_comparable = sum(r.field_comparable for r in scored)

    return {
        "mode": "full",
        "total_rows": len(gold),
        "verified_rows": sum(1 for r in rows if r.verified),
        "errored_rows": sum(1 for r in rows if r.error),
        # Gated: unverified ground truth cannot produce an accuracy number.
        "field_accuracy": (
            round(sum(r.field_hits for r in scored) / total_comparable, 4)
            if total_comparable
            else None
        ),
        "field_accuracy_n": total_comparable,
        "url_grounding": (
            round(mean(r.url_grounding for r in ok if r.url_grounding is not None), 4)
            if ok else None
        ),
        "coverage": round(mean(r.coverage for r in ok), 4) if ok else None,
        "rows": [r.__dict__ for r in rows],
    }


def format_report(r: dict) -> str:
    def fmt(v: Any) -> str:
        return "not measured" if v is None else str(v)

    lines = [
        "# Enrichment Eval — Research Agent",
        "",
        f"**Mode:** `{r['mode']}`  ",
        f"**Gold rows:** {r['total_rows']} ({r['verified_rows']} verified)",
        "",
    ]

    if not r["verified_rows"]:
        lines += [
            "> **Field accuracy is not measured.** No gold row has `verified: true`, so",
            "> there is no ground truth to score against. Populate",
            "> `evals/enrichment_gold.jsonl` (see `evals/README.md`) and re-run.",
            "> Grounding and coverage do not depend on ground truth and are reported below.",
            "",
        ]

    lines += [
        "| Metric | Value | Depends on |",
        "|---|---|---|",
        f"| Field accuracy | {fmt(r['field_accuracy'])} | verified ground truth |",
        f"| URL grounding | {fmt(r.get('url_grounding'))} | nothing — fully deterministic |",
        f"| Field coverage | {fmt(r.get('coverage'))} | nothing |",
        "",
    ]

    if r.get("rows"):
        lines += ["| Domain | Verified | Coverage | Grounding | Fields |", "|---|---|---|---|---|"]
        for row in r["rows"]:
            fields = (
                f"{row['field_hits']}/{row['field_comparable']}"
                if row["field_comparable"] else "—"
            )
            lines.append(
                f"| {row['domain']} | {'yes' if row['verified'] else 'no'} | "
                f"{row['coverage']} | {fmt(row['url_grounding'])} | {fields} |"
            )

    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Evaluate the research agent.")
    ap.add_argument("--offline", action="store_true",
                    help="report gold-set readiness only; run no enrichment")
    args = ap.parse_args()

    results = run_eval(offline=args.offline)
    out = Path(__file__).parent
    (out / "enrichment_report.md").write_text(format_report(results), encoding="utf-8")

    print(f"mode={results['mode']}  rows={results['total_rows']}  "
          f"verified={results['verified_rows']}")
    if results["field_accuracy"] is None:
        print("  field accuracy   not measured (no verified ground truth)")
    else:
        print(f"  field accuracy   {results['field_accuracy']} (n={results['field_accuracy_n']})")
    print(f"  url grounding    {results.get('url_grounding')}")
    print(f"  coverage         {results.get('coverage')}")
    print(f"\nreport -> {out / 'enrichment_report.md'}")


if __name__ == "__main__":
    main()
