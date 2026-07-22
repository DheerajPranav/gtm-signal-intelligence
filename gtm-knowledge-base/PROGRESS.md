# Progress log — gtm-knowledge-base

## Day 3 (2026-07-22) — Northstar corpus

Authored **30 internally-consistent markdown docs** (7 product, 10 sales, 4 case
studies, 5 marketing, 4 company) grounded in one canonical fact sheet, plus a
`check_corpus.sh` integrity gate (counts, frontmatter, canonical-fact consistency,
contradiction guard — exit 0). See the umbrella README for the fact sheet.

## Day 4 (2026-07-23) — RAG ingestion & retrieval (`gtm_kb`)

**Time spent:** ~2 hours (budget was 2).

**Planned tasks:** stand up the retrieval layer — chunk the corpus, embed into a
vector store + BM25, expose a `query()` that returns chunks (no LLM yet).

**What shipped:**
- `gtm_kb` package (src-layout, hatchling): `loader` (frontmatter-aware),
  `chunker` (section-based by H2, ~800-token overlapping fallback, attributable
  metadata), `embeddings`, `text` (shared tokenizer), `store` (Chroma + BM25),
  `ingest`, `query`.
- **Two indexes over the same chunks**: Chroma (cosine) + BM25, persisted to
  `.index/` (git-ignored). `query()` supports vector / bm25 / **hybrid (RRF)**.
- **Pluggable key-aware embedder**: Voyage/OpenAI when a key is set; otherwise a
  fitted **offline deterministic TF-IDF hashing embedder** (blake2b buckets, IDF
  downweighting of ubiquitous terms), persisted so queries embed in the same space.
- Shared tokenizer with stopword removal + light plural folding, so vector and
  keyword indexes share vocabulary.
- **26 offline tests**, including an end-to-end ingest→query gate on the real corpus.

**DoD (all met):**
- [x] `python -m gtm_kb.ingest` runs cleanly → 30 docs, 177 chunks.
- [x] Chroma DB persisted locally (`.index/chroma/`).
- [x] BM25 index persisted locally (`.index/bm25.pkl`).
- [x] Sanity query returns relevant chunks.

**Blockers / honest notes:**
- No embedding API key present, so ingestion used the offline TF-IDF fallback
  (zero API cost). The pipeline transparently upgrades to semantic embeddings when
  a key is set — no code change.
- The offline lexical embedder underperforms on queries whose key term is absent
  from the corpus vocabulary (the literal "competitors" query — corpus uses the
  names + "competition"). Documented and *tested as a known limitation* rather than
  hidden; a real key or the Day-5 reranker closes it. Comparison-style queries in
  corpus vocabulary retrieve the battlecards/positioning cleanly.
- Deviation from the plan's suggested LlamaIndex: went lean (Chroma + rank_bm25 +
  a direct chunker) for transparency and hermetic testability — consistent with the
  locked Approach A (reject framework-max). See `.genesis/decisions/`.

**Metrics logged today:**
- Docs 30 → chunks 177. Tests: 26 passed. Embedding API cost: $0.00 (offline).

**Next (Day 5):** hybrid retrieval + Haiku reranker + Sonnet cited answers +
Streamlit UI (needs `ANTHROPIC_API_KEY`).
