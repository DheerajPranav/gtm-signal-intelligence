"""Retrieval metrics.

Why not "P@5": the previous harness divided hits by the count of *unique documents*
retrieved, which makes the denominator vary per question (1-5) and the number
non-comparable across the set. It also labelled the result "P@5" when it was not
denominated by k at all.

Worse, 24 of the 35 golden questions have exactly one expected source. A chunk-set
of 5 can therefore never exceed 1/5 document-precision on those, so a "P@5" of 0.21
sat near its own ceiling while reading like an 80% failure.

These four metrics all have a real ceiling of 1.0 and answer distinct questions:
  hit_rate@k  — did we surface the right document at all?      (coverage)
  recall@k    — of the documents we needed, how many appeared?  (completeness)
  precision@k — how much of the context window was on-target?   (noise)
  mrr@k       — how near the top was the first good chunk?      (ranking quality)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalMetrics:
    hit_rate: float       # 1.0 if any expected doc appears in top-k, else 0.0
    recall: float         # unique expected docs found / expected docs
    chunk_precision: float  # retrieved chunks from an expected doc / k
    mrr: float            # 1 / rank of the first on-target chunk (0.0 if none)
    hits: int
    expected_count: int
    k: int

    def as_dict(self) -> dict:
        return {
            "hit_rate": round(self.hit_rate, 4),
            "recall": round(self.recall, 4),
            "chunk_precision": round(self.chunk_precision, 4),
            "mrr": round(self.mrr, 4),
            "hits": self.hits,
            "expected_count": self.expected_count,
        }


def compute_retrieval_metrics(
    retrieved_paths: list[str], expected_paths: list[str], k: int
) -> RetrievalMetrics:
    """Score one question's retrieval.

    Args:
        retrieved_paths: source_path per retrieved chunk, in rank order. May repeat —
            several chunks can come from the same document, which is exactly what
            chunk_precision is meant to capture.
        expected_paths: gold source documents for the question.
        k: the cut-off the retrieval was run at.
    """
    expected = set(expected_paths)
    if not expected:
        return RetrievalMetrics(0.0, 0.0, 0.0, 0.0, 0, 0, k)

    ranked = retrieved_paths[:k]

    on_target = [p for p in ranked if p in expected]
    found_docs = {p for p in ranked if p in expected}

    mrr = 0.0
    for rank, path in enumerate(ranked, start=1):
        if path in expected:
            mrr = 1.0 / rank
            break

    return RetrievalMetrics(
        hit_rate=1.0 if found_docs else 0.0,
        recall=len(found_docs) / len(expected),
        # Denominated by k, not by unique-doc count, so it is comparable across questions.
        chunk_precision=len(on_target) / k if k else 0.0,
        mrr=mrr,
        hits=len(found_docs),
        expected_count=len(expected),
        k=k,
    )
