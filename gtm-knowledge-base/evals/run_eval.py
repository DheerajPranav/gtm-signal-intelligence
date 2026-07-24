"""Eval harness for the Northstar RAG assistant.

Two modes, and the report always states which one produced it:

  retrieval-only (default, no API key)
      Scores retrieval against the golden set. Answer-quality metrics are reported
      as "not measured" — never as a number.

  full (--full, requires ANTHROPIC_API_KEY)
      Also generates answers and runs the faithfulness and completeness judges.

Latency is only ever reported for stages that actually ran. The previous version
substituted a hardcoded 50ms in offline mode and printed it as a p50/p95
measurement; that is a fabricated result and is not permitted here.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from statistics import mean
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from gtm_kb.query import query as retrieve  # noqa: E402
from gtm_kb.rag import RAGAssistant  # noqa: E402
from judges import (  # noqa: E402
    judge_available,
    judge_completeness,
    judge_faithfulness,
    lexical_trait_coverage,
)
from metrics import compute_retrieval_metrics  # noqa: E402

TOP_K = 5


def load_golden_qa(filepath: Optional[Path] = None) -> list[dict]:
    path = filepath or Path(__file__).parent / "golden_qa.jsonl"
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def percentile(values: list[float], pct: float) -> Optional[float]:
    """Nearest-rank percentile. None for an empty series — never a placeholder."""
    if not values:
        return None
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, round(pct / 100 * len(ordered) + 0.5) - 1))
    return ordered[idx]


def run_eval(full: bool = False, client: Optional[Any] = None, k: int = TOP_K) -> dict:
    qa_set = load_golden_qa()

    if full and not judge_available(client):
        raise SystemExit(
            "--full requires ANTHROPIC_API_KEY (or an injected client). "
            "Run without --full for retrieval-only metrics."
        )

    assistant = RAGAssistant(client=client) if full else None

    per_question: list[dict] = []
    latencies: list[float] = []
    costs: list[float] = []
    faith_scores: list[float] = []
    complete_scores: list[float] = []
    lexical_scores: list[float] = []
    ungrounded_citation_count = 0

    for qa in qa_set:
        question = qa["question"]
        expected = qa["expected_sources"]
        traits = qa.get("expected_answer_traits", [])
        row: dict[str, Any] = {"question": question, "category": qa.get("category", "unknown")}

        if full:
            result = assistant.query(question, reranking_top_k=k)
            retrieved_paths = [c.metadata.get("source_path", "") for c in result.top_chunks_for_debug]
            latencies.append(result.latency_ms)
            costs.append(result.cost_usd)
            ungrounded_citation_count += len(result.unresolved_citations)

            faith = judge_faithfulness(
                result.answer_text, [c.text for c in result.top_chunks_for_debug], client=client
            )
            comp = judge_completeness(result.answer_text, traits, client=client)
            lex = lexical_trait_coverage(result.answer_text, traits)

            if faith.available:
                faith_scores.append(faith.score)
            if comp.available:
                complete_scores.append(comp.score)
            lexical_scores.append(lex)

            row.update(
                {
                    "faithfulness": faith.as_dict(),
                    "completeness": comp.as_dict(),
                    "lexical_trait_coverage": round(lex, 4),
                    "latency_ms": round(result.latency_ms, 1),
                    "cost_usd": result.cost_usd,
                    "unresolved_citations": result.unresolved_citations,
                }
            )
        else:
            hits = retrieve(question, top_k=k, mode="hybrid")
            retrieved_paths = [h.metadata.get("source_path", "") for h in hits]

        m = compute_retrieval_metrics(retrieved_paths, expected, k=k)
        row["retrieval"] = m.as_dict()
        per_question.append(row)

    agg = {
        f"hit_rate_at_{k}": round(mean(r["retrieval"]["hit_rate"] for r in per_question), 4),
        f"recall_at_{k}": round(mean(r["retrieval"]["recall"] for r in per_question), 4),
        f"chunk_precision_at_{k}": round(
            mean(r["retrieval"]["chunk_precision"] for r in per_question), 4
        ),
        f"mrr_at_{k}": round(mean(r["retrieval"]["mrr"] for r in per_question), 4),
    }

    # Answer-quality aggregates exist only when the judges actually ran.
    answer_quality: dict[str, Any] = {
        "measured": bool(full),
        "faithfulness": round(mean(faith_scores), 4) if faith_scores else None,
        "faithfulness_n": len(faith_scores),
        "completeness": round(mean(complete_scores), 4) if complete_scores else None,
        "completeness_n": len(complete_scores),
        "lexical_trait_coverage": round(mean(lexical_scores), 4) if lexical_scores else None,
        "ungrounded_citations": ungrounded_citation_count if full else None,
    }

    perf: dict[str, Any] = {
        "measured": bool(full),
        "latency_p50_ms": round(percentile(latencies, 50), 1) if latencies else None,
        "latency_p95_ms": round(percentile(latencies, 95), 1) if latencies else None,
        "avg_cost_per_query": round(mean(costs), 6) if costs else None,
        "total_cost_usd": round(sum(costs), 6) if costs else None,
    }

    by_category: dict[str, dict] = {}
    for row in per_question:
        cat = by_category.setdefault(row["category"], {"count": 0, "hit": 0.0, "recall": 0.0})
        cat["count"] += 1
        cat["hit"] += row["retrieval"]["hit_rate"]
        cat["recall"] += row["retrieval"]["recall"]
    for cat in by_category.values():
        cat["hit_rate"] = round(cat.pop("hit") / cat["count"], 4)
        cat["recall"] = round(cat.pop("recall") / cat["count"], 4)

    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mode": "full" if full else "retrieval-only",
        "k": k,
        "total_questions": len(qa_set),
        "retrieval": agg,
        "answer_quality": answer_quality,
        "performance": perf,
        "by_category": by_category,
        "questions": per_question,
    }


def _fmt(value: Optional[float], suffix: str = "") -> str:
    return "not measured" if value is None else f"{value}{suffix}"


def format_report(r: dict) -> str:
    k = r["k"]
    full = r["mode"] == "full"

    lines = [
        "# RAG Eval Report — Northstar Knowledge Base",
        "",
        f"**Generated:** {r['timestamp']}  ",
        f"**Mode:** `{r['mode']}`  ",
        f"**Questions:** {r['total_questions']}  ",
        f"**Cut-off:** k={k}",
        "",
    ]

    if not full:
        lines += [
            "> Retrieval-only run: no `ANTHROPIC_API_KEY` was present, so no answers were",
            "> generated. Faithfulness, completeness, latency and cost are reported as",
            "> **not measured** — they are not estimated or substituted.",
            "> Re-run with `--full` and a key to populate them.",
            "",
        ]

    lines += [
        "## Retrieval",
        "",
        "| Metric | Value | Reads as |",
        "|--------|-------|----------|",
        f"| Hit rate@{k} | {r['retrieval'][f'hit_rate_at_{k}']} | share of questions where a gold doc surfaced |",
        f"| Recall@{k} | {r['retrieval'][f'recall_at_{k}']} | share of gold docs retrieved |",
        f"| Chunk precision@{k} | {r['retrieval'][f'chunk_precision_at_{k}']} | share of the context window on-target |",
        f"| MRR@{k} | {r['retrieval'][f'mrr_at_{k}']} | how near the top the first gold chunk landed |",
        "",
        "## Answer quality",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Faithfulness (LLM judge) | {_fmt(r['answer_quality']['faithfulness'])} |",
        f"| Completeness (LLM judge) | {_fmt(r['answer_quality']['completeness'])} |",
        f"| Lexical trait coverage (deterministic proxy) | {_fmt(r['answer_quality']['lexical_trait_coverage'])} |",
        f"| Ungrounded citations emitted | {_fmt(r['answer_quality']['ungrounded_citations'])} |",
        "",
        "## Performance",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Latency p50 | {_fmt(r['performance']['latency_p50_ms'], 'ms')} |",
        f"| Latency p95 | {_fmt(r['performance']['latency_p95_ms'], 'ms')} |",
        f"| Avg cost / query | {_fmt(r['performance']['avg_cost_per_query'])} |",
        f"| Total cost | {_fmt(r['performance']['total_cost_usd'])} |",
        "",
        "## By category",
        "",
        f"| Category | Count | Hit rate@{k} | Recall@{k} |",
        "|----------|-------|----------|--------|",
    ]

    for cat, d in sorted(r["by_category"].items()):
        lines.append(f"| {cat} | {d['count']} | {d['hit_rate']} | {d['recall']} |")

    lines += ["", "## Per-question retrieval", "", f"| Question | Cat | Hit | Recall | MRR |", "|---|---|---|---|---|"]
    for q in r["questions"]:
        rm = q["retrieval"]
        lines.append(
            f"| {q['question'][:60]} | {q['category']} | {rm['hit_rate']} | {rm['recall']} | {rm['mrr']} |"
        )

    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Evaluate the Northstar RAG assistant.")
    ap.add_argument("--full", action="store_true", help="generate answers and run LLM judges (needs API key)")
    ap.add_argument("--k", type=int, default=TOP_K)
    args = ap.parse_args()

    results = run_eval(full=args.full, k=args.k)

    out_dir = Path(__file__).parent
    (out_dir / "report.md").write_text(format_report(results), encoding="utf-8")
    (out_dir / "report.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    k = results["k"]
    print(f"mode={results['mode']}  questions={results['total_questions']}")
    print(f"  hit_rate@{k}        {results['retrieval'][f'hit_rate_at_{k}']}")
    print(f"  recall@{k}          {results['retrieval'][f'recall_at_{k}']}")
    print(f"  chunk_precision@{k} {results['retrieval'][f'chunk_precision_at_{k}']}")
    print(f"  mrr@{k}             {results['retrieval'][f'mrr_at_{k}']}")
    if not results["answer_quality"]["measured"]:
        print("  answer quality      not measured (retrieval-only run)")
    print(f"\nreport -> {out_dir / 'report.md'}")


if __name__ == "__main__":
    main()
