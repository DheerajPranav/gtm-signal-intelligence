"""Retrieval over the persisted indexes — no LLM in the loop yet.

Modes:
  - "vector": Chroma ANN over embedder vectors.
  - "bm25":   keyword ranking.
  - "hybrid": Reciprocal Rank Fusion of the two (default).

Day 5 layers reranking + cited answer generation on top of this.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from .config import (
    BM25_FILENAME,
    CHROMA_SUBDIR,
    COLLECTION,
    INDEX_DIR,
    MANIFEST_FILENAME,
)
from .embeddings import embedder_from_manifest
from .store import Bm25Store, VectorStore

RRF_K = 60  # standard Reciprocal Rank Fusion constant


@dataclass(frozen=True)
class Result:
    chunk_id: str
    text: str
    metadata: dict
    score: float
    retriever: str  # "vector", "bm25", or "hybrid"


def _load_manifest(index_dir: Path) -> dict:
    path = index_dir / MANIFEST_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"No index manifest at {path}. Run `python -m gtm_kb.ingest` first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _rrf_fuse(ranked_lists: list[list[str]], k: int = RRF_K) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, cid in enumerate(ranked):
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
    return scores


def query(
    question: str,
    top_k: int = 5,
    mode: str = "hybrid",
    index_dir: Path = INDEX_DIR,
    embedder=None,
) -> list[Result]:
    index_dir = Path(index_dir)
    manifest = _load_manifest(index_dir)

    # Pull a wider candidate pool per retriever, then trim after fusion.
    pool = max(top_k * 4, 20)

    vector_hits: list[dict] = []
    bm25_hits: list[dict] = []

    if mode in ("vector", "hybrid"):
        embedder = embedder or embedder_from_manifest(manifest, index_dir)
        vs = VectorStore(chroma_dir=index_dir / CHROMA_SUBDIR, collection=COLLECTION)
        q_emb = embedder.embed_query(question)
        vector_hits = vs.query(q_emb, top_k=pool)

    if mode in ("bm25", "hybrid"):
        bm = Bm25Store(index_dir / BM25_FILENAME).load()
        bm25_hits = bm.query(question, top_k=pool)

    by_id: dict[str, dict] = {}
    for h in vector_hits + bm25_hits:
        by_id.setdefault(h["chunk_id"], h)

    if mode == "vector":
        ranked = [(h["chunk_id"], 1.0 - float(h["distance"])) for h in vector_hits]
    elif mode == "bm25":
        ranked = [(h["chunk_id"], float(h["score"])) for h in bm25_hits]
    else:  # hybrid
        fused = _rrf_fuse(
            [[h["chunk_id"] for h in vector_hits], [h["chunk_id"] for h in bm25_hits]]
        )
        ranked = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)

    results: list[Result] = []
    for cid, score in ranked[:top_k]:
        h = by_id[cid]
        results.append(
            Result(
                chunk_id=cid,
                text=h["text"],
                metadata=h["metadata"],
                score=round(float(score), 6),
                retriever=mode,
            )
        )
    return results


def _format(results: list[Result]) -> str:
    lines: list[str] = []
    for i, r in enumerate(results, 1):
        loc = f"{r.metadata.get('doc_title')} › {r.metadata.get('section_title')}"
        src = r.metadata.get("source_path")
        snippet = " ".join(r.text.split())
        if len(snippet) > 220:
            snippet = snippet[:220] + "…"
        lines.append(f"[{i}] {loc}  ({src})  score={r.score}\n    {snippet}")
    return "\n".join(lines) if lines else "(no results)"


DEFAULT_SANITY_Q = "What competitors does Northstar have?"


def main() -> None:
    ap = argparse.ArgumentParser(description="Query the Northstar knowledge base (retrieval only).")
    ap.add_argument("question", nargs="?", default=DEFAULT_SANITY_Q,
                    help=f"Question to retrieve for (default sanity query: {DEFAULT_SANITY_Q!r}).")
    ap.add_argument("--mode", choices=["hybrid", "vector", "bm25"], default="hybrid")
    ap.add_argument("--top-k", type=int, default=5)
    args = ap.parse_args()

    results = query(args.question, top_k=args.top_k, mode=args.mode)
    print(f"Q: {args.question}   [mode={args.mode}, top_k={args.top_k}]\n")
    print(_format(results))


if __name__ == "__main__":
    main()
