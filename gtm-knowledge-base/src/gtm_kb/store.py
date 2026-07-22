"""Persistence: a Chroma vector store and a BM25 keyword index over the same chunks.

Both indexes are built from the identical chunk set so hybrid retrieval (Day 5) can
fuse them fairly. Vectors are supplied by our own embedder — Chroma is used purely
as a storage/ANN layer, so no onnx default-embedding model is pulled in.
"""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np

from .text import tokenize


def _chroma_client(chroma_dir: Path):
    import chromadb  # lazy: keeps import cost out of pure-chunking tests
    from chromadb.config import Settings

    return chromadb.PersistentClient(
        path=str(chroma_dir),
        settings=Settings(anonymized_telemetry=False, allow_reset=True),
    )


class VectorStore:
    """Thin wrapper over a persistent Chroma collection (cosine space)."""

    def __init__(self, chroma_dir: Path, collection: str) -> None:
        self.chroma_dir = Path(chroma_dir)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.collection = collection
        self.client = _chroma_client(self.chroma_dir)

    def reset(self):
        try:
            self.client.delete_collection(self.collection)
        except Exception:
            pass  # collection didn't exist yet
        self.col = self.client.get_or_create_collection(
            self.collection, metadata={"hnsw:space": "cosine"}
        )
        return self.col

    def _open(self):
        return self.client.get_collection(self.collection)

    def add(self, chunks, embeddings: np.ndarray) -> None:
        self.col.add(
            ids=[c.chunk_id for c in chunks],
            embeddings=[e.tolist() for e in embeddings],
            documents=[c.text for c in chunks],
            metadatas=[c.metadata() for c in chunks],
        )

    def query(self, embedding: np.ndarray, top_k: int) -> list[dict]:
        col = self._open()
        res = col.query(
            query_embeddings=[embedding.tolist()],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        out: list[dict] = []
        ids = res["ids"][0]
        for i, cid in enumerate(ids):
            out.append(
                {
                    "chunk_id": cid,
                    "text": res["documents"][0][i],
                    "metadata": res["metadatas"][0][i],
                    "distance": res["distances"][0][i],
                }
            )
        return out


class Bm25Store:
    """A BM25Okapi index plus the chunk records it was built from, pickled to disk."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._bm25 = None
        self._records: list[dict] = []

    def build_and_save(self, chunks) -> None:
        from rank_bm25 import BM25Okapi

        records = [
            {"chunk_id": c.chunk_id, "text": c.text, "metadata": c.metadata(),
             "tokens": tokenize(c.index_text)}
            for c in chunks
        ]
        bm25 = BM25Okapi([r["tokens"] for r in records])
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("wb") as f:
            pickle.dump({"records": records, "bm25": bm25}, f)
        self._bm25 = bm25
        self._records = records

    def load(self) -> "Bm25Store":
        with self.path.open("rb") as f:
            payload = pickle.load(f)
        self._bm25 = payload["bm25"]
        self._records = payload["records"]
        return self

    def query(self, question: str, top_k: int) -> list[dict]:
        if self._bm25 is None:
            self.load()
        scores = self._bm25.get_scores(tokenize(question))
        order = np.argsort(scores)[::-1][:top_k]
        out: list[dict] = []
        for i in order:
            rec = self._records[int(i)]
            out.append(
                {
                    "chunk_id": rec["chunk_id"],
                    "text": rec["text"],
                    "metadata": rec["metadata"],
                    "score": float(scores[int(i)]),
                }
            )
        return out
