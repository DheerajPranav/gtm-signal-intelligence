# ADR 0001 — Lean RAG stack (Chroma + BM25) over LlamaIndex; offline TF-IDF fallback embedder

- **Date:** 2026-07-23
- **Status:** accepted
- **Phase / milestone:** M4 — Day 4 RAG ingestion

## Context

The Day-4 plan suggests LlamaIndex + Chroma + Voyage/OpenAI embeddings. Two forces
push against taking that verbatim: (1) the locked Approach A (notebook-first, prove
primitives, **reject framework-max**) and the quality bar's demand that cost/latency
be explicit and every stage unit-testable — LlamaIndex's abstractions obscure both;
and (2) no embedding API key is available in this environment, yet the pipeline must
be verifiable end-to-end without fabricating model output.

## Decision

Build the ingestion/retrieval layer directly on **Chroma (vectors) + rank_bm25
(keyword) + a hand-written section chunker**, behind a **pluggable, key-aware
embedder** whose default is a fitted, fully offline, deterministic **TF-IDF hashing**
embedder; Voyage/OpenAI are used automatically when their key is set.

## Consequences

- Positive: hermetic, deterministic tests (26, no network); explicit control of
  cost/persistence; transparent RRF hybrid; smaller dependency surface.
- Positive: the offline default lets the whole pipeline run and be graded now, and
  upgrades to semantic embeddings with zero code change when a key appears.
- Negative / cost: the offline embedder is lexical — queries whose key term is
  absent from the corpus vocabulary retrieve weakly (documented + tested as a known
  limitation, resolved by a real key or the Day-5 reranker).
- **Invariant (context-graph):** retrieval results must remain attributable
  (`source_path`, `doc_title`, `section_title` on every chunk).

## Alternatives rejected

- **LlamaIndex end-to-end** — framework opacity fights the log-cost-from-call-1 rule
  and the eval bar; overkill for 30 docs. Kept as a possible later swap.
- **Fabricating/omitting the embedding step without a key** — violates the "no
  invented output / eval-or-it-doesn't-count" bar. The offline deterministic
  embedder is the honest substitute.
