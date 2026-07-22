"""Ingestion pipeline: load -> chunk -> embed -> persist (Chroma + BM25).

Run with:  python -m gtm_kb.ingest

Idempotent: each run resets the Chroma collection and overwrites the BM25/chunks/
manifest files, so re-ingesting is always safe.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from .chunker import chunk_documents
from .config import (
    BM25_FILENAME,
    CHROMA_SUBDIR,
    CHUNKS_FILENAME,
    COLLECTION,
    CORPUS_DIR,
    EMBEDDER_FILENAME,
    INDEX_DIR,
    MANIFEST_FILENAME,
)
from .embeddings import get_embedder, is_offline
from .loader import load_documents
from .store import Bm25Store, VectorStore


def _write_chunks_jsonl(path: Path, chunks) -> None:
    with path.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps({"chunk_id": c.chunk_id, "text": c.text, "metadata": c.metadata()}) + "\n")


def ingest(
    corpus_dir: Path = CORPUS_DIR,
    index_dir: Path = INDEX_DIR,
    embedder=None,
    verbose: bool = False,
) -> dict:
    index_dir = Path(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)
    embedder = embedder or get_embedder()

    t0 = time.perf_counter()
    docs = load_documents(corpus_dir)
    chunks = chunk_documents(docs)
    if not chunks:
        raise RuntimeError(f"No chunks produced from corpus at {corpus_dir}")

    index_texts = [c.index_text for c in chunks]
    # Fit corpus-dependent embedders (e.g. TF-IDF) before embedding, then persist
    # their learned state so queries embed in the same space.
    if hasattr(embedder, "fit"):
        embedder.fit(index_texts)
    embeddings = embedder.embed_documents(index_texts)
    if hasattr(embedder, "save"):
        embedder.save(index_dir / EMBEDDER_FILENAME)

    # Vector index (Chroma).
    vs = VectorStore(chroma_dir=index_dir / CHROMA_SUBDIR, collection=COLLECTION)
    vs.reset()
    vs.add(chunks, embeddings)

    # Keyword index (BM25).
    bm = Bm25Store(index_dir / BM25_FILENAME)
    bm.build_and_save(chunks)

    # Raw chunk records + manifest.
    _write_chunks_jsonl(index_dir / CHUNKS_FILENAME, chunks)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "corpus_dir": str(corpus_dir),
        "doc_count": len(docs),
        "chunk_count": len(chunks),
        "embedder": embedder.name,
        "embed_dim": int(embedder.dim),
        "vector_space": "cosine",
        "elapsed_sec": round(time.perf_counter() - t0, 3),
        # Offline embedders make no API calls; API backends would log real cost.
        "embedding_cost_usd": 0.0 if is_offline(embedder.name) else None,
    }
    (index_dir / MANIFEST_FILENAME).write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    if verbose:
        print(json.dumps(manifest, indent=2))
    return manifest


def main() -> None:
    manifest = ingest(verbose=False)
    print("Ingestion complete.")
    print(f"  docs:        {manifest['doc_count']}")
    print(f"  chunks:      {manifest['chunk_count']}")
    print(f"  embedder:    {manifest['embedder']} (dim={manifest['embed_dim']}, {manifest['vector_space']})")
    print(f"  elapsed:     {manifest['elapsed_sec']}s")
    print(f"  index dir:   {INDEX_DIR}")
    if is_offline(manifest["embedder"]):
        print("  note:        offline deterministic embedder (no API key found). "
              "Set VOYAGE_API_KEY or OPENAI_API_KEY for semantic embeddings.")


if __name__ == "__main__":
    main()
