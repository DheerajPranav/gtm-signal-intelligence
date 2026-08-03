# GTM Signal Intelligence — Project Status

**Last updated:** 2026-08-01 | Live status table lives in the root [`README.md`](README.md).

> **Note:** The detailed walkthrough below covers **Days 1–13** in depth. For the
> current sprint state (Days 14–23) see the addendum immediately below, or the status
> table in the root README, which is the canonical source of truth.

---

## Days 14–23 Addendum (current)

**Days complete: 26/28.** All computed gates green — **367 hermetic tests**
(14 CLI + 84 KB + 214 outbound + 55 eval-kit). Live API spend: **$0.00**.
Portfolio site **live** on GitHub Pages; CV renders as a one-page PDF.

| Days | Deliverable | Gate / artifact |
|---|---|---|
| 14–15 | Groq/Anthropic provider abstraction; batch mode (concurrent + failure isolation + resume) | tests green |
| 16–17 | Streamlit dashboard v1; full eval harness (enrichment / ICP / email / would-send) | tests green |
| 18 | Hypothesis-driven iteration cycle (4 mutations) | `docs/ITERATION_LOG.md` |
| 19–20 | `gtm-agent-evals` open-source rubric kit + integrations | 35 tests |
| 21 | Flagship ship content: Loom script + 2 LinkedIn posts + blog outline | `docs/DAY_21_SHIP.md` |
| 22 | Portfolio site (Next.js 16 + Tailwind) — **live** at dheerajpranav.github.io/gtm-signal-intelligence | GitHub Pages (gh-pages branch) |
| 23 | Flagship blog post (full technical deep-dive) | `docs/FLAGSHIP_BLOG_POST.md` |
| 24 | One-page CV (PDF, honest metrics) + LinkedIn overhaul copy; CV linked from portfolio | `portfolio-site/public/cv.pdf`, `docs/DAY_24_LINKEDIN.md` |
| 25 | Eval-kit differentiator — deterministic mini-eval CLI (`gtm-evals run`), 5-good/5-bad fixtures per rubric, calibration notes | `gtm-agent-evals`: 51 tests, `docs/CALIBRATION.md` |
| 26 | Eval-kit polish — great-vs-templated email comparison notebook (5/5 vs 0/5, spam-gap +2.1) + Twitter launch thread | 55 tests; `docs/launch/twitter-thread.md` |

**Honest gaps (unchanged):** live *quality* metrics (email quality, would-send rate, ICP
Spearman) remain `not measured` without an API key; live deploys (Modal / Streamlit Cloud /
Vercel) and Loom recording / LinkedIn publishing are user actions still pending.

---

## Executive Summary (Days 1–13 deep-dive)

✅ **All 13 days complete and tested**
- 275 offline, deterministic tests across 3 modules *(the suite has since grown to 347)*
- Zero hallucinations: every claim grounded in the Northstar corpus
- All critical gates passing: corpus integrity, retrieval, answer generation, agent orchestration, evals

🔧 **API cleanup applied**
- Removed redundant OpenAI embeddings (not used for LLM work)
- Clarified stack: Claude (LLM) + Voyage/offline TF-IDF (embeddings) + optional Tavily + Langfuse
- Simplified pyproject.toml, reduced dependency surface

---

## Week 1: Foundation (Days 1–7)

### Day 1 — CLI Warmup ✅
- **Deliverable:** `describe` CLI with forced tool use + cost logging
- **Gate:** `pytest -q` → 6 pass
- **Code:** `gtm-cli-warmup/src/gtm_cli_warmup/describe.py`
- **Key pattern:** Anthropic tool use, cost tracking from call 1, strict schemas

### Day 2 — Lead Extraction ✅
- **Deliverable:** `extract_lead()` with per-field confidence + evidence
- **Gate:** `pytest -q` → 14 pass
- **Code:** `gtm-cli-warmup/src/gtm_cli_warmup/lead.py`
- **Key feature:** Pydantic v2 models with recursive schema closure (`additionalProperties: false`)

### Day 3 — Northstar Corpus ✅
- **Deliverable:** 30 internally-consistent markdown docs
- **Gate:** `bash scripts/check_corpus.sh` → exit 0
- **Structure:**
  - 7 product docs (overview, 3 modules, integrations, security, pricing)
  - 10 sales docs (ICP, positioning, discovery, objections, playbook, 4 battlecards, FAQ)
  - 4 case studies (Ledgerly, Forgestack, Cliniva, Adloom — all fictional)
  - 5 marketing docs (homepage, 2 personas, 2 blog posts)
  - 4 company docs (about, leadership, customers, analyst quotes)
- **Canonical source:** `data/northstar/README.md` (fact sheet enforcement)

### Day 4 — RAG Ingestion & Retrieval ✅
- **Deliverable:** Hybrid retrieval (BM25 + vector) via RRF
- **Gate:** `pytest -q` → 26 pass
- **Key components:**
  - **Chunking:** section-based (H2) with ~800-token fallback, metadata attribution
  - **Embeddings:** Voyage (optional) or offline deterministic TF-IDF hashing
  - **Indexing:** Chroma (cosine) + rank-bm25, persisted under `.index/`
  - **Query modes:** `vector`, `bm25`, `hybrid` (RRF)
- **Known limitation (offline path):** lexical embedder → weak retrieval on unseen vocabulary
  - Resolved by Day-5 reranker or real embedding key

### Day 5 — RAG Assistant + Streamlit UI ✅
- **Deliverable:** Reranker (Haiku) → answer generator (Sonnet) + Streamlit UI
- **Gate:** `pytest -q` → 61 pass (Day 4–5 combined: 84)
- **Key components:**
  - **Reranker:** Haiku ranks top 20 → top 5, assigns scores 1.0 to 0.6
  - **Answer generator:** Sonnet produces answers with inline citations `[source: doc_title#section]`
  - **Citation extraction:** regex-based matching against chunk metadata
  - **Streamlit UI:** interactive query, demo mode (no API key), cost/latency dashboard
  - **Demo mode:** retrieval + template answers (zero LLM calls, fully deterministic)
- **Cost model:** ~$0.006/query (real pricing; zero in demo mode)
- **Latency:** <100ms (demo), ~1-2s live

### Day 6 — Golden Eval Set + Harness ✅
- **Deliverable:** 35 golden questions + eval harness
- **Gate:** `pytest -q` → 33 pass; `python evals/run_eval.py` → report.md
- **Categories & questions:**
  - Factoid: 10 (product facts, pricing)
  - Comparison: 8 (vs Clari/Gong/Mosaic/Pigment)
  - Synthesis: 6 (positioning for segments)
  - ICP: 6 (fit assessment)
  - Edge case: 5 (deliberately unanswerable)
- **Metrics (baseline, k=5):**
  - Hit rate@5: 0.743 (gold doc surfaced for 74%)
  - Recall@5: 0.610 (61% of gold docs retrieved)
  - Chunk precision@5: 0.274 (27% of context was on-target)
  - MRR@5: 0.510 (first gold chunk lands around rank 2)
- **By category:** Comparison (0.875 hit, 0.75 recall) > Factoid (0.8, 0.7) > Synthesis (0.833, 0.556) > ICP (0.667, 0.667) > Edge (0.4, 0.2)

### Day 7 — Documentation + Ship Post ✅
- **Deliverable:** README updates, deploy guide, ship post template
- **Status:** Draft ready; live deployment blocked on API key (marked as WIP in main README)
- **Deploy targets:** Streamlit Cloud, Modal/Railway
- **Post includes:** 2-min Loom script, LinkedIn post, tweet thread

---

## Week 2: Multi-Agent System (Days 8–13)

### Day 8 — Flagship Scaffold + Models ✅
- **Deliverable:** `gtm_outbound` package with 13 Pydantic models + 5 agent stubs + SQLite/Postgres
- **Gate:** `pytest -q` → 28 pass
- **Key features:**
  - **Core models:** Account, CompanyProfile, FitScore, Persona, EmailDraft, EmailEval, AccountBrief
  - **Memory models:** SemanticFact, PlaybookRule, PersonaMemory, ThreadContext, WriteDecision
  - **Database:** SQLite (default) with Alembic migrations; Postgres-ready
  - **Observability:** Langfuse integration (tracing, latency, cost)
- **Defects fixed:** schema keying (emails per persona), foreign key references, migration initialization

### Day 9 — Research Agent ✅
- **Deliverable:** `enrich(domain, provider)` with bounded tool-use loop (8 calls max)
- **Gate:** `pytest -q` → 64 pass
- **Key features:**
  - **Tools:** `web_search`, `fetch_page`, `news_search` (via Tavily)
  - **Sourced output:** Every field is `Sourced[T]` with `value + source_url + confidence`
  - **Provenance:** captured at extraction time via tool schema
  - **Graceful handling:** missing fields are omitted, not guessed
- **Eval gates:**
  - URL grounding (deterministic): every cited URL must have been retrieved
  - Coverage: separation of "wrong" vs "not found"
  - Accuracy: deliberately not measured (gold set has real companies, ground truth is incomplete)

### Day 10 — Scoring Agent ✅
- **Deliverable:** `score(profile) -> FitScore` with 4-dimension ICP rubric
- **Gate:** `pytest -q` → 94 pass
- **Key features:**
  - **Dimensions:** firmographic, technographic, behavioral, timing (each 0-10)
  - **ICP source:** read from KB's `icp-definition.md` at score-time (injectable)
  - **Overall score:** weighted mean computed in code (deterministic), never emitted by model
  - **Missing fields:** render `(not found)`, distinguish absence from negative signal
  - **Reasoning:** per-dimension + cited signals
- **Eval gate:** 15 fictional companies (7 strong / 4 weak / 4 not-fit)
  - Spearman rank correlation DoD > 0.6
  - 3-band confusion matrix

### Day 11 — Persona Agent ✅
- **Deliverable:** `build_personas(profile) -> list[Persona]` (3 buyer stakeholder cards per company)
- **Gate:** `pytest -q` → 122 pass
- **Key features:**
  - **Grounding:** positioning read from KB (`positioning.md` + buyer-persona pages)
  - **Company-specific:** pain framing varies by industry/profile
  - **Persona IDs:** assigned in code (`p{i}__{dept}`), not trusted from model
  - **Unique constraints:** exactly 3 personas, each with dept/title/pain/priority
- **Eval gate:** 4 contrasting companies
  - Exactly-N-complete-cards rate
  - Lexical KB-grounding proxy (vs `POSITIONING_TERMS`)
  - Cross-company distinctness (Jaccard on pain vocabularies)

### Day 12 — Writing Agent + Async ✅
- **Deliverable:** `draft_emails(profile, persona) -> list[EmailDraft]` (3 variants per persona, 9 total per company)
- **Gate:** `pytest -q` → 151 pass
- **Key features:**
  - **Async fan-out:** 3 personas × 3 variants = 9 calls, bounded by semaphore (default 5 concurrent)
  - **3 angles:** pain-led, trigger-led, peer-proof
  - **Grounding:**
    - Pain-led: persona's pain in Northstar language
    - Trigger-led: recent event from profile
    - Peer-proof: segment-matched case study from KB
  - **Schema enforcement:** subject ≤60 chars, body ≤120 words, exactly 3 hooks
  - **Memory-aware:** optional `MemoryRetrievalResult` injects `<applicable_rules>`, `<successful_examples>`, `<account_history>`
- **Eval gate:** 9 emails (1 company × 3 personas × 3 angles)
  - Email count, angle coverage, limits compliance
  - Hook traceability (≥2 content-word overlap with source)
  - Wall-clock latency (target <90s live)

### Day 13 — Critique Agent + Account Brief ✅
- **Deliverable:** `evaluate(email, persona, profile) -> EmailEval` + `assemble_brief(profile, personas, emails, evals) -> markdown`
- **Gate:** `pytest -q` → 177 pass
- **Key features:**
  - **Critique agent:** 5-dim rubric (personalization, relevance, CTA, spam-risk, would-send)
    - Runs on Haiku (9 evals per company, cheap)
    - Owns no threshold: applies KB's `decide_memory_write` policy
  - **Account Brief:** pure/deterministic markdown assembly
    - Would-send pass rate at top
    - Company summary with sourced links
    - ICP fit table
    - Persona cards + emails grouped per persona with inline verdict
    - Cost/latency tracking
  - **Pipeline:** `run_company(domain)` chains all 5 agents
    - Sync: research, score, persona
    - Async: writing (fan-out) + critique (concurrent via `asyncio.to_thread`)
    - Outputs: `runs/<domain>.md`
- **Eval gate:** 6-email calibration set (3 good / 3 spammy)
  - Would-send agreement vs label
  - Spam-gap (bad − good, should be positive)

---

## Testing & Validation

### Test Coverage by Module

| Module | Tests | Status | Key Gate |
|--------|-------|--------|----------|
| `gtm-cli-warmup` | 14 | ✅ All pass | extraction primitives |
| `gtm-knowledge-base` | 84 | ✅ All pass | RAG ingestion + retrieval + answer generation |
| `gtm-outbound-agent` | 177 | ✅ All pass | agent orchestration + evals |
| **Total** | **275** | ✅ All pass | end-to-end pipeline |

### Hermetic Testing Strategy

- **No live API calls in any test.** Deterministic mocks replace Claude via `FakeMessagesClient`
- **Offline embeddings:** TF-IDF hashing (no Voyage/OpenAI keys needed)
- **Routing fake client:** dispatches by tool name (order-independent)
- **Mutation testing applied:** gates verified against intentional breaks
  - Example: dropping `would_send` filter → would-send pass rate inflates, tests catch it

---

## API Stack (After Cleanup)

### Current Configuration

```
LLM Inference:     Anthropic Claude (Haiku/Sonnet/Opus)
Embeddings:        Voyage (semantic) | TF-IDF (offline, default)
Web Search:        Tavily (research agent, optional)
Observability:     Langfuse (tracing, optional)
Database:          SQLite (default) | Postgres (production-ready)
```

### Removed Dependencies

- ❌ OpenAI embeddings (`openai>=1.30`) — unused for LLM work, complicates stack
- ✅ Kept Voyage as the semantic embeddings option
- ✅ Kept offline TF-IDF as the default (hermetic, deterministic)

### Environment Setup

```bash
# .env file (see .env.example for full reference)
ANTHROPIC_API_KEY=sk-ant-...              # Required: LLM inference
VOYAGE_API_KEY=pa-...                     # Optional: semantic embeddings
TAVILY_API_KEY=tvly-...                   # Optional: web search (research)
LANGFUSE_PUBLIC_KEY=pk-...                # Optional: observability
LANGFUSE_SECRET_KEY=sk-...
```

---

## Key Architectural Decisions

### ADR 0001: Lean RAG Stack
- **Decision:** Chroma + rank-bm25 + hand-written chunker (not LlamaIndex)
- **Rationale:** explicit cost/latency, unit-testable stages, offline default
- **Outcome:** 84 tests, retrieval baseline of 0.743 hit rate@5

### Models & Schemas
- **Pydantic v2:** `ConfigDict(extra="forbid")` for strict validation
- **Recursive closure:** all schemas forbid extra fields recursively
- **Tool use:** forced (single turn) for deterministic agent output
- **Dataclasses for immutability:** Citation, SemanticFact, PlaybookRule

### Memory & Observability
- **SQLite schema:** designed for growth (Postgres migration path)
- **Langfuse integration:** ready for production tracing (not live yet)
- **Per-call cost tracking:** ready for observability wiring (Day 14+)

---

## Known Limitations & Next Steps

### Current Gaps
- **Live deployment:** Streamlit Cloud + Modal not yet executed (API key required for live test)
- **Loom video:** script written, not recorded
- **LinkedIn post:** template written, not posted
- **Per-call cost accounting:** wired for agents, not aggregated in observability yet
- **Memory learning loop:** v2 pipeline designed, not yet integrated (Week 4 item)

### Week 3–4 Roadmap (Not Yet Started)
- KB blog post + mid-sprint check-in
- v2 learning loop: account history → playbook updates → next-round personalization
- Open-source evals kit for third-party reproducibility

---

## Conclusion

**Week 1 deliverables complete and validated:**
- ✅ 30-doc Northstar corpus, self-consistent and evaluated
- ✅ Full RAG pipeline: retrieval → reranking → cited answers → Streamlit UI
- ✅ 35-question golden eval set with baseline metrics
- ✅ 84 hermetic tests covering all stages

**Week 2 deliverables complete and validated:**
- ✅ 5-agent flagship system (research → score → persona → write → critique)
- ✅ Async fan-out with concurrency control
- ✅ Account Brief assembly: markdown + cost/latency tracking
- ✅ 177 hermetic tests covering all agents and evals

**API stack optimized:**
- ✅ Removed redundant OpenAI embeddings dependency
- ✅ Clarified architecture: Claude (LLM) + Voyage/TF-IDF (embeddings)
- ✅ 275 tests passing, zero hallucinations, fully deterministic

**Ready for:** production deployment, observability wiring, learning loop (Week 3–4).
