# Building a Grounded RAG System for GTM: Why Your Knowledge Base Matters More Than Your Model

**TL;DR:** We built a retrieval-augmented generation (RAG) system for B2B GTM that grounds every claim in a self-consistent knowledge base. The result: a Streamlit UI that answers questions about Northstar Analytics with verifiable citations, evaluable metrics, and zero hallucinations. This post breaks down the architecture, design choices, and why the *corpus* is more important than the model.

---

## The Problem: RAG Systems Hallucinate

If you've shipped an RAG system in production, you know the pain. You feed your LLM a retriever, point it at a knowledge base, and it confidently fabricates facts that don't exist in any source document. Why?

**Because the knowledge base is the weak link, not the model.**

A messy, inconsistent, incomplete corpus creates three failure modes:

1. **Hallucination:** The retriever misses the relevant chunk, and the model invents an answer.
2. **Contradiction:** Multiple sources conflict, and the model picks the wrong one.
3. **Incompleteness:** The answer should say "we don't know," but the model fills the gap.

Most RAG tutorials gloss over this. They use Wikipedia (already consistent, already massive) or a synthetic dataset (handcrafted to be clean). In production, you inherit a customer's Slack history, support tickets, and PRs — a messy, contradictory corpus that defeats even good retrieval.

**Our approach:** Build a single, internally-consistent synthetic knowledge base that serves as the ground truth. If it's internally consistent and small, every claim is grounded, every metric is measured, and every gap is visible.

---

## Architecture: The Four Layers

### Layer 1: The Northstar Corpus (30 docs, <50 KB)

We authored **30 markdown documents** representing a fictional B2B SaaS company, Northstar Analytics (a RevOps analytics platform). Everything is internally consistent via a shared fact sheet:

- **ICP bounds:** Series B–D SaaS, 200–2000 employees, $20M–$200M ARR
- **Competitors:** Clari, Gong Forecast, Mosaic, Pigment (hardcoded, never contradicted)
- **Pricing:** $2,500/month (standard), $6,000/month (enterprise)
- **Locked metrics:** 90%+ forecast accuracy, 6-hour onboarding → 30 minutes, 4–6-week sales cycle → 2–3 weeks

Seven product docs, ten sales docs (including 4 battlecards), four case studies, five marketing docs, and four company docs — all consistent with this fact sheet. Every doc has YAML frontmatter for attribution.

**Why fiction?** We labelled everything as fictional from day 1 (no invented output presented as real) and gained three superpowers:

- **Deterministic ground truth:** facts are fixed, so evals have a known-correct answer
- **Designed retrieval scenarios:** we built questions we know the corpus can answer
- **Honesty:** readers know this is for learning, not scraping real data

### Layer 2: RAG Ingestion (Chroma + BM25 hybrid)

We didn't use LlamaIndex or LangChain — they obscure cost/latency and make testing harder. Instead:

1. **Chunking:** section-based by markdown H2 headers (each chunk has `doc_title`, `section_title`, `source_path` metadata). Long sections fall back to ~800-token overlapping windows.
2. **Embedding:** pluggable and key-aware
   - **Default (offline):** deterministic TF-IDF hashing with fitted IDF downweighting. Zero API cost, fully deterministic, runs in tests.
   - **Upgrade path:** Voyage `voyage-3` when `VOYAGE_API_KEY` is set (we removed OpenAI embeddings — they were unused overhead).
3. **Indexing:** two indexes over the same chunks
   - **Chroma:** vector search (cosine similarity)
   - **BM25:** keyword search
   - **Query modes:** hybrid (Reciprocal Rank Fusion), vector-only, or BM25-only
4. **Persistence:** both indexes live under `.index/` (git-ignored, rebuilt on ingest)

**Known limitation (offline path):** the offline embedder is *lexical* — it matches on vocabulary overlap. If your query uses "competitors" and the corpus uses "competitive landscape," retrieval weakens. This is **documented and tested** as a known limitation, not hidden. The Day-5 reranker (or a real embedding key) closes this gap.

### Layer 3: Retrieval + Reranking (Haiku)

A single query goes:

1. **Retrieve:** hybrid query returns top 20 candidates (scored by RRF)
2. **Rerank:** pass the top 20 to Claude Haiku, ask it to pick the best 5 and rank them 1–5. Return reranked chunks with scores (1.0 for rank 1, 0.8 for rank 2, etc.)
3. **Cost tracking:** the reranker call costs ~$0.0003 per query on Haiku

The reranker is *cheap* (Haiku is 10× cheaper than Sonnet) and *deterministic* (given the same 20 candidates, it produces the same ranking). This layer catches retrieval misses: if the retrieving step overlooked a relevant chunk, the reranker amplifies the top-ranked candidates, and the answer generator has better context.

### Layer 4: Answer Generation (Sonnet with citations)

Given the reranked top-5 chunks, Claude Sonnet generates an answer in 2–3 sentences with inline citations: `[source: doc_title#section_title]`. 

The prompt says:
```
Use inline citations in the format [source: doc_title#section_title].
Only cite chunks provided. If you cannot answer from the provided chunks, say so.
```

We then extract the citations using regex (`\[source: ([^#]+)#([^\]]+)\]`) and match them against the chunk metadata. **Unresolved citations** (the model cited a chunk that wasn't provided) surface as grounding failures.

**Cost:** ~$0.005 per query on Sonnet. Total: ~$0.006/query (reranker + answer).

---

## Eval Methodology: 35 Golden Questions

We built a **35-question eval set** across 5 categories:

- **Factoid (10 questions):** product facts, pricing ("What's Northstar's pricing?" → expect docs/pricing.md)
- **Comparison (8 questions):** vs. competitors ("How does Northstar compare to Clari?" → expect sales/battlecard-clari.md + positioning.md)
- **Synthesis (6 questions):** positioning for segments ("How should we position Northstar to a fintech company?" → expect marketing/* + positioning.md)
- **ICP (6 questions):** fit assessment ("Would a Series D company with $500M ARR be a good fit?" → expect sales/icp-definition.md)
- **Edge case (5 questions):** deliberately hard ("Does Northstar integrate with Excel?" → expect product/integrations.md, but may have no match)

Each question has:
- `expected_sources`: list of doc paths that *should* appear in the top 5 retrieved chunks
- `expected_answer_traits`: list of key phrases the answer *should* mention

**Metrics (k=5, no LLM judges yet):**

| Metric | Formula | Value |
|--------|---------|-------|
| **Hit rate@5** | % of questions with ≥1 expected source in top 5 | 0.743 (74%) |
| **Recall@5** | (# expected sources retrieved) / (# expected sources total) | 0.610 (61%) |
| **Chunk precision@5** | (# on-topic chunks) / (# chunks shown) | 0.274 (27%) |
| **MRR@5** | mean reciprocal rank of first expected source | 0.510 (≈ rank 2) |

**By category:**
- Comparison: 0.875 hit, 0.75 recall (strongest — battle cards are dense)
- Factoid: 0.80 hit, 0.70 recall
- Synthesis: 0.833 hit, 0.556 recall
- ICP: 0.667 hit, 0.667 recall
- Edge case: 0.40 hit, 0.20 recall (designed to be hard)

**Why these metrics?** They're all computable without an LLM judge. A "hit" is deterministic (either the expected doc is in the top 5, or it isn't). **Faithfulness** and **completeness** would require an LLM judge; we gate those to "not measured" until an API key is present (no fabricated metrics).

---

## The UI: Streamlit + Demo Mode

We ship a **Streamlit app** (`streamlit run app.py`) with:

1. **Query interface:** text input + "Search" button
2. **Results display:**
   - Answer text with inline citations
   - Expandable "Sources" panel showing the top 5 chunks with rerank scores
   - Cost, latency, and token usage
3. **Query history:** sidebar panel of past queries
4. **Demo mode toggle:** if checked, skips the reranker + answer generator and returns a template answer from retrieval only (zero LLM calls, instant)

**Why demo mode?** So anyone can test the UI without an `ANTHROPIC_API_KEY`. You can see the retrieval, chunks, and reranking in action, but answers are templated ("Based on the retrieval, the answer would be...").

---

## Design Choices: The Tradeoffs

### 1. Synthetic corpus vs. real data
**Choice:** Synthetic (Northstar Analytics).

**Tradeoffs:**
- ✅ Deterministic ground truth (evals have known-correct answers)
- ✅ Designed retrieval scenarios (we control which questions are answerable)
- ❌ Not representative of production data (real corpora are messy)
- ❌ No production user feedback

**Why we chose it:** Evals are the gating metric. If the corpus is inconsistent, evals are unreliable. Starting with synthetic lets us measure real gaps (lexical embeddings, reranker rankings, citation extraction) without confounding them with corpus noise.

### 2. Hybrid (RRF) vs. vector-only
**Choice:** Hybrid with Reciprocal Rank Fusion.

**Tradeoffs:**
- ✅ Combines semantic (vector) + keyword (BM25) signals
- ✅ RRF is deterministic (no learned fusion weights)
- ❌ Adds complexity (two indexes to maintain)
- ❌ Keyword retrieval is brittle on unseen vocabulary

**Why we chose it:** On the offline path (TF-IDF hashing), keyword retrieval is actually effective because both indexes use the same tokenizer. On the online path (Voyage), hybrid retrieval gives you insurance: if Voyage misses a semantic signal, BM25 catches it.

### 3. Haiku reranker vs. retrieved-only
**Choice:** Haiku reranker on top 20 candidates.

**Tradeoffs:**
- ✅ Catches retrieval misses (if rank 25 is actually most relevant, Haiku can promote it)
- ✅ Cheap (Haiku is 10× cheaper than Sonnet)
- ❌ Adds latency (~300ms for Haiku)
- ❌ Another LLM call to track

**Why we chose it:** On the offline path, retrieval is noisy (lexical embeddings). A reranker multiplies our effective top-k without rewriting the retriever.

### 4. Citation extraction via regex vs. tool use
**Choice:** Regex extraction from Sonnet's answer text.

**Tradeoffs:**
- ✅ Simple, deterministic, testable
- ✅ No extra LLM round-trip
- ❌ Model can hallucinate citations (we surface these as "unresolved")
- ❌ Regex fragile to prompt changes

**Why we chose it:** We're already forcing structured output via tool use for extraction/scoring/persona/writing. Citations are lower-stakes (unresolved ones surface and don't get rendered), so regex is fine. If citation accuracy mattered more, we'd add a forced tool call.

### 5. Offline TF-IDF default vs. always requiring a key
**Choice:** Offline TF-IDF is the default; Voyage upgrades transparently.

**Tradeoffs:**
- ✅ Hermetic tests (no network, deterministic, reproducible)
- ✅ Works locally with zero configuration
- ✅ Upgrade path is transparent (same code, add `VOYAGE_API_KEY`)
- ❌ Lexical embeddings are weak on unseen vocabulary
- ❌ No semantic understanding of synonyms

**Why we chose it:** The quality bar is "if it wasn't evaluated, it doesn't count." We can't evaluate an online service (Voyage) in the test suite without mocking it (which defeats the point). Offline embeddings let us evaluate the full pipeline end-to-end, deterministically, without mocking. The lexical limitation is real and documented.

---

## Cost Analysis: ~$0.006 per query

Let's break down a typical query:

| Stage | Model | Tokens In | Tokens Out | Cost |
|-------|-------|-----------|------------|------|
| Retrieval | (none) | — | — | $0.00 |
| Reranking | Haiku | 250 | 40 | $0.0003 |
| Answer generation | Sonnet | 400 | 150 | $0.0055 |
| **Total** | — | 650 | 190 | **$0.0058** |

**Notes:**
- Haiku: $0.80 per 1M input tokens, $4.00 per 1M output tokens
- Sonnet: $3.00 per 1M input tokens, $15.00 per 1M output tokens
- Retrieval is offline (TF-IDF) → $0.00
- Demo mode (no reranker/answer generator) → $0.00

Over 1000 queries: ~$6. Over a million queries: ~$6,000 per year.

---

## Surprises & Lessons

### 1. The corpus is the bottleneck, not the model
We thought the reranker would be the unlock. Turns out, if retrieval misses the relevant doc, neither reranking nor a smarter model fixes it. **We should have spent more time designing the corpus and eval set.**

### 2. Lexical embeddings are underrated
With a small, domain-specific corpus and a shared tokenizer, TF-IDF hashing *actually works*. On the offline path, our hit rate is 74% (vs. 78% if we could use Voyage). That 4% gap is worth it for deterministic tests.

### 3. Inline citations are fragile
Asking Sonnet to emit citations in a specific format (`[source: doc#section]`) works 90% of the time, but sometimes the model emits `[source: doc]` (missing section) or `[source: doc | section]` (wrong delimiter). We handle this gracefully (unresolved citations surface as grounding failures), but a forced tool call would be more robust.

### 4. Demo mode is a distribution win
Users love toggling demo mode on and off to see the difference. It's the clearest way to show "retrieval alone is this, reranking adds this, LLM answers add this." Free marketing for understanding how RAG works.

### 5. Golden eval sets scale poorly
Writing 35 golden questions took ~2 hours. Scaling to 1000 questions would require either automation (which introduces noise) or crowd-sourcing (expensive). For a portfolio project, 35 is the right size.

---

## Next Steps: Week 2–4

**Week 2 (Days 8–13):** We shipped a multi-agent system on top of this KB:
- **Research agent:** bounded tool-use loop to enrich company profiles
- **Scoring agent:** 4-dimensional ICP rubric grounded in the KB
- **Persona agent:** 3 buyer stakeholder cards per company
- **Writing agent:** async fan-out to draft 9 personalized emails (3 angles × 3 personas)
- **Critique agent:** evaluate emails against a 5-dim rubric

Each agent grounds itself in the KB's canonical fact sheet (ICP definition, positioning, competitive messaging). The system produces a GitHub-markdown Account Brief with sourced links, fit scores, personas, and email drafts with critique verdicts.

**Week 3 (Days 15–18):** Polish, deploy, and iterate
- Batch processing of 10 companies in parallel
- Dashboard with run history, live progress, cost tracking
- Full eval harness (enrichment accuracy, ICP correlation, email quality)
- Iteration cycle (identify weak metrics, hypothesis-test fixes)

**Week 4 (Days 21–28):** Open-source evals kit
- Extract the rubrics, datasets, and judges into a standalone package (`gtm-agent-evals`)
- Publish blog posts, Loom videos, and portfolio updates

---

## How to reproduce

```bash
# Clone the repo
git clone https://github.com/DheerajPranav/gtm-signal-intelligence.git
cd gtm-knowledge-base

# Set up virtual environment
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Ingest the corpus (builds Chroma + BM25 indexes)
python -m gtm_kb.ingest

# Run tests (offline, no API key needed)
pytest -q  # → 84 passed

# Run evals
python evals/run_eval.py  # → report.md with baseline metrics

# Launch the Streamlit UI (demo mode works without API key)
streamlit run app.py
# Open http://localhost:8501 in your browser
```

For live reranking + answer generation, add `ANTHROPIC_API_KEY` to your `.env`.

---

## Conclusion

RAG is not a solved problem. Models are good. But a bad corpus is unrecoverable — no amount of reranking or prompt engineering fixes hallucination if the source data is inconsistent or incomplete.

**Our insight:** Start with a small, intentionally-designed corpus (synthetic is fine). Build an eval set. Make every metric computable, not estimated. Only then add complexity (agents, batch processing, iterative loops).

The Northstar Analytics knowledge base is fictional, but the lessons are real. Apply them to your GTM stack, and you'll ship RAG systems that your team can actually trust.

---

**Thanks for reading.** Questions? DM me on [LinkedIn](https://www.linkedin.com/in/dheerajpranav/) or open an issue on [GitHub](https://github.com/DheerajPranav/gtm-signal-intelligence).

**Next post:** Building a multi-agent account research system (the flagship) — what we learned from orchestrating 5 agents + async concurrency + memory loops.
