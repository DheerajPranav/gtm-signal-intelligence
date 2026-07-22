# gtm-knowledge-base

A **self-contained, consistent knowledge corpus** for a fictional B2B RevOps analytics company — **Northstar Analytics** — built to ground GTM AI tools: retrieval-augmented generation, ICP scoring, grounded outbound, and evals.

This is Days 3–4 of the GTM AI Engineering sprint: **Day 3** authored the corpus; **Day 4** built the retrieval layer (`gtm_kb`) that ingests it into a vector + keyword index and answers queries. It is the shared source of truth that later projects (RAG chatbot, account research agent, outbound generator) retrieve against.

## Why a fixed corpus

Grounded generation and RAG are only as trustworthy as their source data. A **single, internally-consistent corpus** lets us:

- Ground every generated claim in a citable document.
- Write evals with known-correct answers (the facts are fixed).
- Detect hallucination — if a tool asserts a fact not in the corpus, it's invented.

## Contents

**30 markdown documents** across five categories, all consistent with one [canonical fact sheet](data/northstar/README.md):

| Category | Docs | What's inside |
|---|---|---|
| `product/` | 7 | Overview, 3 modules, integrations, security, pricing |
| `sales/` | 10 | ICP, positioning, discovery, objections, playbook, 4 battlecards, FAQ |
| `case-studies/` | 4 | Ledgerly, Forgestack, Cliniva, Adloom (all fictional) |
| `marketing/` | 5 | Homepage, 2 persona pages, 2 blog posts |
| `company/` | 4 | About, leadership, customer list, analyst quotes |

Every doc has YAML frontmatter and relative cross-links.

## Verify the corpus

```bash
bash scripts/check_corpus.sh
```

This asserts the corpus is complete and internally consistent:
- exactly **30** markdown docs, in the expected per-category counts;
- every doc has frontmatter;
- shared facts (ICP bounds, competitor set, pricing, locked metrics) appear where expected and are not contradicted.

Exit code `0` = corpus is intact. Non-zero = a check failed (details printed).

## Day 4 — RAG ingestion & retrieval (`gtm_kb`)

The `gtm_kb` package turns the corpus into a searchable index and answers queries
(retrieval only — the LLM reranker and cited answers arrive Day 5).

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"

.venv/bin/python -m gtm_kb.ingest                                  # build the indexes
.venv/bin/python -m gtm_kb.query "How does Northstar compare to Clari and Gong?"
.venv/bin/python -m pytest -q                                      # 26 tests, fully offline
```

**Pipeline** (`load → chunk → embed → persist`):

- **Chunking** is section-based — one chunk per markdown H2 (plus a leading
  overview chunk), falling back to ~800-token overlapping windows for long
  sections. Each chunk carries `doc_type`, `doc_title`, `section_title`, and
  `source_path`, so every retrieved result is attributable.
- **Two indexes over the same chunks**: a **Chroma** vector index (cosine) and a
  **BM25** keyword index, both persisted under `.index/` (git-ignored, rebuilt by
  `ingest`). `query()` supports `--mode vector | bm25 | hybrid`; hybrid fuses the
  two with Reciprocal Rank Fusion.
- **Pluggable, key-aware embedder.** With `VOYAGE_API_KEY` or `OPENAI_API_KEY` set,
  ingestion uses real semantic embeddings. With no key it falls back to a fully
  **offline, deterministic TF-IDF hashing embedder** — a real (if lexical) embedding
  that needs no network and fabricates nothing, so the whole pipeline is verifiable
  and the tests are hermetic.

**Known limitation (offline path).** The offline embedder is *lexical*: it matches
on shared vocabulary. A query whose key term is absent from the corpus — e.g. the
literal *"What competitors does Northstar have?"* (the corpus uses the names
*Clari/Gong/Mosaic/Pigment* and the word *"competition"*, not *"competitors"*) —
returns brand-level context rather than the battlecards. Ask it in the corpus's own
words (*"How does Northstar compare to Clari and Gong?"*) and retrieval nails the
battlecards, positioning, and competitive-plays sections. A real semantic embedding
key, or the Day-5 LLM reranker, closes this gap. This trade-off is deliberately
tested, not hidden (see `tests/test_ingest_query.py`).

## Honesty note

Northstar Analytics, its customers, leadership, analysts, and press quotes are **fictional**, created for training/demos and labelled as such in the docs. No real organization or person is represented, and no fabricated LLM output is presented as genuine.

## Layout

```
gtm-knowledge-base/
├── README.md               ← you are here
├── pyproject.toml          ← gtm_kb package (Day 4)
├── data/northstar/
│   ├── README.md           ← canonical fact sheet + provenance
│   ├── product/  sales/  case-studies/  marketing/  company/
├── src/gtm_kb/             ← RAG pipeline
│   ├── loader.py  chunker.py  embeddings.py  text.py
│   ├── store.py            ← Chroma + BM25
│   ├── ingest.py           ← python -m gtm_kb.ingest
│   └── query.py            ← python -m gtm_kb.query
├── tests/                  ← 26 offline tests
└── scripts/
    └── check_corpus.sh     ← corpus integrity gate
```
