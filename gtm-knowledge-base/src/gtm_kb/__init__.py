"""gtm_kb — Northstar knowledge-base RAG with retrieval, reranking, and cited answers.

Day-4 scope: load the 30-doc corpus, chunk it by markdown section, embed with a
pluggable (key-aware) embedder, and persist both a Chroma vector index and a BM25
keyword index. `query()` returns relevant chunks.

Day-5 scope: Haiku reranker (top 20 → top 5) + Sonnet answer generator with
inline citations + Streamlit UI + cost/latency tracking.
"""

from .config import CORPUS_DIR, INDEX_DIR
from .loader import Document, load_documents
from .chunker import Chunk, chunk_document
from .embeddings import HashingEmbedder, TfidfHashingEmbedder, get_embedder
from .models import RankedChunk, CitedAnswer, Citation, QueryResult
from .rag import RAGAssistant

# Note: `ingest`, `query`, `reranker`, `answer_gen` are intentionally NOT imported here.
# Importing them eagerly would double-import their modules when run as `python -m gtm_kb.ingest`.
# Import them directly: `from gtm_kb.ingest import ingest`, etc.

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
    "RankedChunk",
    "CitedAnswer",
    "Citation",
    "QueryResult",
    "RAGAssistant",
]
