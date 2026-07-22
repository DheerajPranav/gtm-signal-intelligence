"""gtm_kb — Northstar knowledge-base RAG ingestion and retrieval.

Day-4 scope: load the 30-doc corpus, chunk it by markdown section, embed with a
pluggable (key-aware) embedder, and persist both a Chroma vector index and a BM25
keyword index. `query()` returns relevant chunks — no LLM in the loop yet (that
arrives Day 5: reranking + cited answers).
"""

from .config import CORPUS_DIR, INDEX_DIR
from .loader import Document, load_documents
from .chunker import Chunk, chunk_document
from .embeddings import HashingEmbedder, TfidfHashingEmbedder, get_embedder

# Note: `ingest` and `query` are intentionally NOT imported here. Importing them
# eagerly would double-import their modules when run as `python -m gtm_kb.ingest`
# (a RuntimeWarning). Import them directly: `from gtm_kb.ingest import ingest`.

__all__ = [
    "CORPUS_DIR",
    "INDEX_DIR",
    "Document",
    "load_documents",
    "Chunk",
    "chunk_document",
    "HashingEmbedder",
    "TfidfHashingEmbedder",
    "get_embedder",
]
