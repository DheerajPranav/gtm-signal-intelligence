# PLAN — gtm-signal-intelligence

The machine-parseable implementation plan. Mirrors the milestone table in `DONE.html` (DONE.html is the
human/visual view; this is the one loops read). Sliced so each milestone ships in one L1 BUILD pass.

> Slicing rule: a milestone must have (a) a single clear outcome, (b) an exact **demo command** that
> proves it, and (c) a freeze boundary of files it may touch. If you can't write the demo command,
> the milestone is too vague — split it.

This spine tracks the **GTM AI Engineering 4-week sprint**. Source of truth for scope is
`gtm_ai_sprint_master_plan.md` at the repo root. Milestones below map 1:1 to sprint days.
Quality bar (locked): *if it wasn't evaluated, it doesn't count*. Structured output via tool use only,
never string parsing. Cost/latency logged from the first LLM call. API spend capped at $50 total.

---

## Brainstorm (G0.5 — approaches to the sprint's cognitive job)

> The cognitive job of the sprint: turn raw GTM signals (company text, lead blurbs, a knowledge base)
> into **structured, evaluated, grounded** revenue intelligence — extraction, retrieval, and generation
> that a RevOps/sales team could actually trust.

### Approach A — Notebook-first, prove primitives, then assemble
Build each capability (extraction, RAG, agents) as a small verified unit with its own eval, then compose.
- Strengths: every unit is independently testable; matches the "eval-or-it-doesn't-count" bar; cheap to debug.
- Weaknesses: slower to a flashy end-to-end demo; risk of over-building primitives.

### Approach B — End-to-end vertical slice first, backfill rigor
Ship a thin flagship pipeline day 1, then harden each stage.
- Strengths: impressive demo early; forces integration questions up front.
- Weaknesses: evals bolted on late (violates the bar); hard to attribute failures to a stage.

### Approach C — Buy/framework-max (LlamaIndex + PydanticAI end-to-end)
Lean maximally on frameworks; write minimal glue.
- Strengths: fastest raw build.
- Weaknesses: least learning/portfolio signal; framework opacity fights the "log cost from call 1" rule.

### Chosen: **A** — Notebook-first, prove primitives, then assemble.
Rationale: the sprint's explicit quality bar is evaluation and grounding, not demo flash. Building
verifiable units first (Day 1 CLI → Day 2 extractor → Day 3 corpus → Day 4-7 RAG) means every stage
carries its own computed gate, and the flagship (Week 2) composes parts that already passed VERIFY.

---

## Milestones (Week 1 — RAG assistant track)

### M1 — Day 1: Anthropic SDK primitives + warmup CLI  ✅ DONE
- **Outcome:** A `describe` CLI that returns a structured `CompanyDescription` via forced tool use, with per-call cost/latency/tokens logged to `runs.jsonl`.
- **Phase (swe-master):** implement + verify
- **Files / freeze boundary:** `gtm-cli-warmup/src/**`, `gtm-cli-warmup/tests/**`
- **Demo command:** `cd gtm-cli-warmup && .venv/bin/python -m pytest -q`  (live: `describe "Notion"` — blocked, no API key)
- **Success criteria:** tests green; structured output via tool use; promo-aware pricing; billed calls always logged.
- **Loops:** L1, L4
- **Skills:** canon + tdd
- **Token budget:** 50000
- **Status:** shipped 2026-07-20, 6/6 tests pass. Open item: live sample run pending `ANTHROPIC_API_KEY`.

### M2 — Day 2: Structured lead extraction (confidence + evidence)  ✅ DONE
- **Outcome:** `extract_lead(text) -> Lead` — a Pydantic `Lead` model (seniority/department/buying-role enums, per-field confidence + evidence) populated via tool use, demonstrated on 6 synthetic inputs in a notebook.
- **Phase:** implement + verify
- **Files:** `gtm-cli-warmup/notebooks/lead_extractor/**`, `gtm-cli-warmup/src/gtm_cli_warmup/lead.py`, tests
- **Demo command:** `cd gtm-cli-warmup && .venv/bin/python -m pytest tests/test_lead.py -q`  (live notebook: needs API key)
- **Success criteria:** schema + enums validated offline; extractor wired to tool use; mock-based test proves tool_use→Lead parsing deterministically; 6 synthetic inputs staged; per-field confidence/evidence populated.
- **Loops:** L1, L4
- **Skills:** canon + tdd
- **Token budget:** 50000
- **Status:** shipped 2026-07-22. 8 offline tests pass (schema closed everywhere, tool_use→typed `Lead`, bad-enum rejection, evidence required, untrusted text fenced in user content only, thinking disabled, ExtractError on no tool call). Notebook staged with 6 synthetic inputs + gold labels; runs live if key present, else labelled FIXTURE (never invents output). Live sample-run pending `ANTHROPIC_API_KEY`.

### M3 — Day 3: Northstar Analytics synthetic knowledge corpus  ✅ DONE
- **Outcome:** 30 internally-consistent markdown docs under `gtm-knowledge-base/data/northstar/` (7 product, 10 sales, 4 case studies, 5 marketing, 4 company) + data README, ready for RAG ingestion on Day 4.
- **Phase:** author + verify
- **Files:** `gtm-knowledge-base/**`
- **Demo command:** `bash gtm-knowledge-base/scripts/check_corpus.sh`  (asserts 30 docs, shared ICP/competitor/pricing facts present)
- **Success criteria:** 30 files committed; ICP doc has firmographic/technographic/behavioral sections; consistent competitors (Clari, Gong Forecast, Mosaic, Pigment), pricing, and ICP across docs; browsable README.
- **Loops:** L1, L4
- **Skills:** canon
- **Token budget:** 50000 (authored directly — no live API cost)
- **Status:** shipped 2026-07-22. 30 docs authored + 2 READMEs + `check_corpus.sh` (bash-3.2 compatible). Gate exit 0: per-category counts (7/10/4/5/4), frontmatter on all 30, canonical facts consistent (ICP 200–2000 / Series B–D / $20M–$200M, competitors Clari/Gong/Mosaic/Pigment, pricing $2,500/$6,000, metrics 90%+/6h→30min/4–6wk/+12%), contradiction guard clean. All customers/leaders/analysts labelled fictional — no invented model output presented as real.

### M4 — Day 4: RAG stack setup + ingestion  ✅ DONE
- **Outcome:** corpus chunked, embedded, indexed (Chroma + BM25); `query()` returns attributable chunks; sanity query works.
- **Files:** `gtm-knowledge-base/src/gtm_kb/**`, `gtm-knowledge-base/tests/**`, `gtm-knowledge-base/pyproject.toml`
- **Demo command:** `cd gtm-knowledge-base && .venv/bin/python -m gtm_kb.ingest && .venv/bin/python -m pytest -q`
- **Success criteria:** ingest runs clean (30 docs → 177 chunks); Chroma + BM25 persisted; hybrid/vector/bm25 query modes; results attributable.
- **Status:** shipped 2026-07-23. 26 offline tests pass. Lean stack (Chroma + rank_bm25 + direct chunker) with a pluggable key-aware embedder; offline default = fitted deterministic TF-IDF hashing (zero API cost). See [ADR 0001](decisions/0001-lean-rag-stack.md). Offline lexical limitation on out-of-vocab queries documented + tested.

### M5 — Day 5: Hybrid retrieval + reranking + answer generation + UI  ⏳ upcoming
### M6 — Day 6: Golden eval set (35 Qs) + eval harness  ⏳ upcoming
### M7 — Day 7: Deploy + Loom + LinkedIn ship  ⏳ upcoming

---

## Progress (loops append here on milestone completion — newest last)

- **M1 — Day 1 warmup CLI** — shipped 2026-07-20. 6/6 tests pass. Structured output via forced tool use; promo-aware pricing table; cost logged to `runs.jsonl`. Open: live run pending API key. (committed `day-01:` in gtm-cli-warmup)
- **M2 — Day 2 lead extractor** — shipped 2026-07-22. 8 offline tests (total suite 14/14 green). `extract_lead()` forces tool use, disables thinking, fences untrusted source text in user content only, records cost. Notebook staged with 6 synthetic inputs + gold labels; FIXTURE fallback when no key. Open: live sample run pending API key.
- **M3 — Day 3 Northstar corpus** — shipped 2026-07-22. 30 consistent docs + 2 READMEs; `check_corpus.sh` gate exit 0 (counts, frontmatter, canonical-fact consistency, contradiction guard). All fictional entities labelled. Ready for Day-4 RAG ingestion.
- **M4 — Day 4 RAG ingestion** — shipped 2026-07-23. `gtm_kb` package: section chunker, Chroma + BM25 over 177 chunks, RRF hybrid query, pluggable key-aware embedder (offline TF-IDF default, $0). 26 offline tests. [ADR 0001](decisions/0001-lean-rag-stack.md) records the lean-stack + offline-embedder decision.
