"""Pluggable, key-aware embedders.

`get_embedder()` picks a real API backend when the matching key is set
(Voyage, then OpenAI), and otherwise falls back to a fully offline, deterministic
bag-of-words hashing embedder. That fallback is a *real* (if simple) embedding —
cosine similarity over hashed term frequencies tracks lexical overlap — so the
pipeline retrieves genuinely relevant chunks without any network call and without
fabricating a model result. When a key is present the same pipeline transparently
upgrades to semantic embeddings.

Every backend returns L2-normalized float32 vectors, so cosine similarity reduces
to a dot product and the Chroma collection is created with cosine space.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Protocol

import numpy as np

from .config import EMBED_DIM
from .text import tokenize


def _l2_normalize(mat: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


def _bucket(token: str, dim: int) -> int:
    """Stable hash of a token into [0, dim). blake2b (not Python's salted hash())
    so buckets are identical across processes and runs."""
    h = int.from_bytes(hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest(), "little")
    return h % dim


class Embedder(Protocol):
    name: str
    dim: int

    def embed_documents(self, texts: list[str]) -> np.ndarray: ...
    def embed_query(self, text: str) -> np.ndarray: ...


class HashingEmbedder:
    """Deterministic bag-of-words feature-hashing embedder (offline, no deps
    beyond numpy). Raw term-frequency, L2-normalized. Kept as a simple baseline;
    the fitted TF-IDF variant below is the production offline default."""

    def __init__(self, dim: int = EMBED_DIM) -> None:
        self.dim = dim
        self.name = f"hashing-bow-{dim}"

    def _vector(self, text: str) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        for tok in tokenize(text):
            v[_bucket(tok, self.dim)] += 1.0
        return v

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return _l2_normalize(np.vstack([self._vector(t) for t in texts]))

    def embed_query(self, text: str) -> np.ndarray:
        return _l2_normalize(self._vector(text)[None, :])[0]


class TfidfHashingEmbedder:
    """Corpus-fitted TF-IDF over hashed term buckets — still fully offline and
    deterministic, but ubiquitous tokens (e.g. "northstar") are downweighted and
    discriminative ones upweighted, which sharply improves retrieval on the offline
    path. `fit()` learns the IDF vector; `save()`/`load()` persist it so queries
    embed in the same space as ingestion."""

    def __init__(self, dim: int = EMBED_DIM) -> None:
        self.dim = dim
        self.name = f"tfidf-hashing-{dim}"
        self.idf: np.ndarray | None = None

    def _counts(self, text: str) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        for tok in tokenize(text):
            v[_bucket(tok, self.dim)] += 1.0
        return v

    def fit(self, texts: list[str]) -> "TfidfHashingEmbedder":
        n = max(1, len(texts))
        df = np.zeros(self.dim, dtype=np.float64)
        for t in texts:
            df += (self._counts(t) > 0).astype(np.float64)
        # smoothed idf (as in sklearn's TfidfTransformer default)
        self.idf = (np.log((n + 1) / (df + 1)) + 1.0).astype(np.float32)
        return self

    def _weighted(self, text: str) -> np.ndarray:
        c = self._counts(text)
        return c * self.idf if self.idf is not None else c

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        if self.idf is None:
            self.fit(texts)
        return _l2_normalize(np.vstack([self._weighted(t) for t in texts]))

    def embed_query(self, text: str) -> np.ndarray:
        return _l2_normalize(self._weighted(text)[None, :])[0]

    def save(self, path: Path) -> None:
        if self.idf is None:
            raise RuntimeError("Cannot save an unfitted TfidfHashingEmbedder.")
        np.savez(str(path), idf=self.idf, dim=np.array([self.dim]))

    def load(self, path: Path) -> "TfidfHashingEmbedder":
        data = np.load(str(path))
        self.idf = data["idf"].astype(np.float32)
        self.dim = int(data["dim"][0])
        return self


class VoyageEmbedder:
    """Voyage AI embeddings (used when VOYAGE_API_KEY is set). Lazy-imports the
    SDK so it's only required when actually selected."""

    def __init__(self, model: str = "voyage-3", dim: int = 1024) -> None:
        self.name = f"voyage:{model}"
        self.dim = dim
        self.model = model

    def _client(self):
        try:
            import voyageai  # noqa: PLC0415
        except ImportError as e:  # pragma: no cover - only hit without the extra
            raise RuntimeError(
                "VOYAGE_API_KEY is set but the 'voyageai' package is not installed. "
                "Install with: pip install '.[voyage]'"
            ) from e
        return voyageai.Client()

    def _embed(self, texts: list[str], input_type: str) -> np.ndarray:
        result = self._client().embed(texts, model=self.model, input_type=input_type)
        return _l2_normalize(np.asarray(result.embeddings, dtype=np.float32))

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return self._embed(texts, "document")

    def embed_query(self, text: str) -> np.ndarray:
        return self._embed([text], "query")[0]


class OpenAIEmbedder:
    """OpenAI embeddings (used when OPENAI_API_KEY is set)."""

    def __init__(self, model: str = "text-embedding-3-small", dim: int = 1536) -> None:
        self.name = f"openai:{model}"
        self.dim = dim
        self.model = model

    def _client(self):
        try:
            from openai import OpenAI  # noqa: PLC0415
        except ImportError as e:  # pragma: no cover - only hit without the extra
            raise RuntimeError(
                "OPENAI_API_KEY is set but the 'openai' package is not installed. "
                "Install with: pip install '.[openai]'"
            ) from e
        return OpenAI()

    def _embed(self, texts: list[str]) -> np.ndarray:
        resp = self._client().embeddings.create(model=self.model, input=texts)
        return _l2_normalize(np.asarray([d.embedding for d in resp.data], dtype=np.float32))

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return self._embed(texts)

    def embed_query(self, text: str) -> np.ndarray:
        return self._embed([text])[0]


def get_embedder() -> Embedder:
    """Select an embedder from the environment. Voyage > OpenAI > offline TF-IDF."""
    if os.getenv("VOYAGE_API_KEY"):
        return VoyageEmbedder()
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIEmbedder()
    return TfidfHashingEmbedder()


def is_offline(name: str) -> bool:
    return name.startswith(("hashing-bow-", "tfidf-hashing-"))


def embedder_from_manifest(manifest: dict, index_dir: Path) -> Embedder:
    """Reconstruct the embedder used at ingest time so queries embed in the same
    space. The fitted TF-IDF embedder reloads its persisted IDF; API backends are
    re-selected from the environment."""
    from .config import EMBEDDER_FILENAME

    name = manifest.get("embedder", "")
    dim = int(manifest.get("embed_dim", EMBED_DIM))
    if name.startswith("tfidf-hashing-"):
        return TfidfHashingEmbedder(dim=dim).load(Path(index_dir) / EMBEDDER_FILENAME)
    if name.startswith("hashing-bow-"):
        return HashingEmbedder(dim=dim)
    return get_embedder()
