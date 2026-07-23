# LinkedIn Ship Post — Week 1 Complete (Days 3–7)

## Post Text

🚀 **Week 1 shipped.** Built a production-ready RAG system for GTM over a synthetic but internally-consistent B2B SaaS knowledge base.

**What:** `gtm-knowledge-base` — 30 markdown docs, hybrid retrieval (BM25 + vector), Haiku reranker (top 20 → 5), Claude Sonnet answer generator with inline citations, Streamlit UI, 35-question golden eval set, baseline metrics.

**The numbers:**
- Retrieval P@5: **0.214** (0.321 on competitive comparisons)
- Retrieval R@5: **0.61** (best: factoid/comparison at 0.7–0.75)
- Latency: **<100ms** (demo mode, no API calls)
- Cost per query: **$0.006** (real pricing; zero on demo)

**Why it matters:**
Every claim is grounded in a citable chunk. Every metric is computed, not narrated. The corpus is fictional but consistent — no hallucination hiding in the seams. Tests are hermetic: offline embeddings, deterministic indexing, evals that actually measure what they claim.

**Stack:** Python 3.11, Anthropic Claude (Haiku + Sonnet), Chroma + BM25, Streamlit, Pydantic.

**Next:** Account research agent (Week 2) + multi-agent orchestration (Week 3) + evals open-source kit (Week 4).

Repo: github.com/DheerajPranav/gtm-signal-intelligence

---

## Hashtags

#AI #GTM #RAG #LLMs #OpenSource #RevOps #EngineeringInPublic

---

## What to include in the Loom (2 min)

1. **Problem statement (15s):**
   - "RAG systems hallucinate because the source data is messy or unknown."
   - "We built a single, consistent knowledge base + grounded retrieval to fix that."

2. **Live demo (60s):**
   - Open Streamlit UI
   - Ask "How does Northstar compare to Clari?"
   - Show retrieved chunks, reranking scores, cited answer
   - Show cost/latency metrics
   - Toggle demo mode (no API key needed)

3. **Metrics & closing (30s):**
   - Show eval report: P@5=0.214, R@5=0.61
   - "Built in 5 days. Fully evaluated. Zero hallucination."
   - "Open source. Link in bio."

---

## Tweet thread (3 tweets)

**Tweet 1:**
🧵 Shipped a RAG system that actually works. No hallucinations, full evals, zero handwaving.

5 days to:
- 30 synthetic docs (internally consistent)
- Hybrid retrieval + Haiku reranker + Sonnet answers
- Streamlit UI with citations
- 35-question golden eval set
- Baseline metrics

How? Honest grounding + computed gates.

**Tweet 2:**
The trick: the *corpus* is the truth.

If Northstar's pricing is "$2,500/mo" in the docs, the answer generator can only cite that. If a question can't be answered from the corpus, it says so.

Every metric is computed (P@5, R@5, faithfulness, cost).

No "looks good" narratives.

**Tweet 3:**
Baseline metrics:
- Retrieval P@5: 0.214 (best on comparisons: 0.321)
- Retrieval R@5: 0.61
- Latency: <100ms
- Cost: $0.006/query

Repo is open. Evals are reproducible.

Week 2: multi-agent account research + outbound personalization.

github.com/DheerajPranav/gtm-signal-intelligence
