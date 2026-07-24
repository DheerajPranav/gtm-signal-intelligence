# gtm-knowledge-base

A **production-ready RAG system** over a self-contained, consistent knowledge corpus for **Northstar Analytics** — a fictional B2B RevOps platform. Built to ground GTM AI tools: retrieval-augmented generation, ICP scoring, grounded outbound, and evals.

**Week 1 complete:** Days 3–7 shipped a full RAG pipeline with retrieval, reranking, cited answers, Streamlit UI, 35-question golden eval set, baseline metrics, and deploy guide. The system is retrieval-grounded, fully evaluated, and cost-tracked.

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

## Days 5–6 — RAG assistant + evals

**Day 5** layers a **reranker** (Claude Haiku), **answer generator** (Claude Sonnet with citations), and **Streamlit UI** on top of retrieval.

**Day 6** adds a **golden eval set** (35 questions across 5 categories) and an **eval
harness** measuring four retrieval metrics plus two LLM-judge answer metrics.

> **Why not P@5?** An earlier version of this harness reported "P@5", but divided hits
> by the count of *unique docs retrieved* rather than by k — so the denominator varied
> per question and the values were not comparable. Compounding it, 24 of the 35
> questions have exactly one expected source, capping document precision near 0.2 on
> most of the set. The reported 0.214 was effectively at its ceiling while reading like
> a failure. It has been replaced by four metrics that each have a real 1.0 ceiling.

### Run evals

```bash
.venv/bin/python evals/run_eval.py          # retrieval only, no API key, $0
.venv/bin/python evals/run_eval.py --full   # + faithfulness & completeness judges
```

**Baseline — retrieval-only run, k=5, $0.00:**

| Metric | Value | Reads as |
|---|---|---|
| Hit rate@5 | **0.743** | a gold doc surfaced for 74% of questions |
| Recall@5 | **0.610** | 61% of all gold docs retrieved |
| Chunk precision@5 | **0.274** | 27% of the context window was on-target |
| MRR@5 | **0.510** | first gold chunk lands around rank 2 |

Faithfulness, completeness, latency and cost print as **not measured** in this mode.
They are never estimated — an unmeasured metric is not rendered as a number.

**By category:**

| Category | Q count | Hit rate@5 | Recall@5 | Notes |
|----------|---------|-----------|----------|-------|
| Comparison | 8 | 0.875 | 0.750 | vs Clari/Gong/Mosaic/Pigment — strongest |
| Synthesis | 6 | 0.833 | 0.556 | positioning for segments |
| Factoid | 10 | 0.800 | 0.700 | product facts, pricing |
| ICP | 6 | 0.667 | 0.667 | fit assessment |
| Edge case | 5 | 0.400 | 0.200 | deliberately unanswerable / boundary |

Edge cases scoring lowest is expected and desirable: several have no good answer in the
corpus, and the correct behaviour is to retrieve little and refuse.

## Quick start — RAG Streamlit UI

```bash
# Install & run the UI
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
STREAMLIT_SERVER_HEADLESS=true .venv/bin/streamlit run app.py
# Open http://localhost:8501 in your browser
```

**Features:**
- Hybrid retrieval (BM25 + vector via RRF)
- Haiku reranker (top 20 → top 5)
- Sonnet answer generator with citations
- **Demo mode**: toggle to test without API key (retrieval + template answers)
- Cost & latency tracking
- Query history & debug panels

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

## Day 7 — Deploy + documentation

**Deploy targets:**
- Streamlit UI: [Streamlit Cloud](https://streamlit.io/cloud)
- FastAPI backend (optional): Modal or Railway

**Local eval:** `evals/run_eval.py` runs in ~10s with demo mode (no API calls).

**Cost model:**
- Reranking (Haiku): $0.80 input + $4.00 output per 1M tokens
- Answer generation (Sonnet): $3.00 input + $15.00 output per 1M tokens
- Typical query: ~200 input tokens (reranker) + 50 output + 400 input + 200 output (answer) ≈ $0.006/query

**Environment setup:**

```bash
# .env file (required for live reranking + answer generation)
ANTHROPIC_API_KEY=sk-...
# VOYAGE_API_KEY=... (optional; defaults to offline TF-IDF)
# OPENAI_API_KEY=... (optional; defaults to offline TF-IDF)
```

## Layout

```
gtm-knowledge-base/
├── README.md               ← you are here
├── pyproject.toml          ← package config (Days 4–5)
├── app.py                  ← Streamlit UI (Day 5)
├── data/northstar/         ← 30-doc corpus (Day 3)
├── src/gtm_kb/
│   ├── loader.py, chunker.py, embeddings.py, text.py
│   ├── store.py            ← Chroma + BM25
│   ├── ingest.py           ← python -m gtm_kb.ingest (Day 4)
│   ├── query.py            ← hybrid retrieval (Day 4)
│   ├── reranker.py         ← Haiku reranker (Day 5)
│   ├── answer_gen.py       ← Sonnet + citations (Day 5)
│   ├── rag.py              ← full pipeline (Day 5)
│   └── models.py           ← Pydantic models (Day 5)
├── evals/
│   ├── golden_qa.jsonl     ← 35 golden questions (Day 6)
│   ├── run_eval.py         ← eval harness (Day 6)
│   └── report.md           ← baseline report (Day 6)
├── tests/                  ← 33 offline tests
└── scripts/
    └── check_corpus.sh     ← corpus integrity gate
```
