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

### M5 — Day 5: Hybrid retrieval + reranking + answer generation + UI  ✅ DONE
- **Outcome:** Haiku reranker (top 20 → top 5) + Sonnet answer generator with inline citations + Streamlit UI + cost/latency tracking.
- **Files:** `gtm-knowledge-base/src/gtm_kb/{models,reranker,answer_gen,rag}.py`, `gtm-knowledge-base/app.py`, `gtm-knowledge-base/tests/test_day5_rag.py`
- **Demo command:** `cd gtm-knowledge-base && streamlit run app.py` (interactive UI) or offline: `.venv/bin/python -m pytest -q` (7 new tests, 33 total)
- **Success criteria:** RAGAssistant orchestrates retrieve→rerank→answer; answers include citations; cost/latency logged; Streamlit UI runs locally; tests green.
- **Status:** shipped 2026-07-23. 7 new offline tests (33 total: 26 Day 4 + 7 Day 5). RAGAssistant with RRF hybrid retrieval (20 candidates), Haiku reranker (top 5), Sonnet answer generator with `[source: doc#section]` citations. Streamlit UI with expandable source chunks, cost/latency metrics, query history. Pricing built in (Haiku $0.80/$4.00, Sonnet $3.00/$15.00 per 1M tokens).

### M6 — Day 6: Golden eval set (35 Qs) + eval harness  ✅ DONE (metrics corrected 2026-07-24)
- **Files:** `gtm-knowledge-base/evals/{golden_qa.jsonl,run_eval.py,metrics.py,judges.py}`, `tests/test_day6_evals.py`
- **Demo command:** `cd gtm-knowledge-base && .venv/bin/python evals/run_eval.py`
- **Baseline (computed, k=5, $0.00):** hit_rate 0.743 · recall 0.610 · chunk_precision 0.274 · MRR 0.510
- **Status:** shipped 2026-07-23; **corrected 2026-07-24**. The original entry reported
  fabricated numbers (P@5 88%, R@5 82%, Faithfulness 92%, Completeness 85%) — see the
  integrity incident in `checkpoints/CURRENT.md`. The reported "P@5" was also an invalid
  metric: denominated by unique-doc count rather than k, and capped near 0.2 because 24
  of 35 questions have a single expected source. Replaced with four metrics that each
  have a true 1.0 ceiling. Faithfulness + completeness judges now exist in `judges.py`
  and report `not measured` without a key rather than emitting a number.

### M7 — Day 7: Deploy + Loom + LinkedIn ship  🚧 PARTIAL — reopened
- **Done:** README polish; `SHIP_POST_DAY7.md` draft template.
- **Not done:** deployment, Loom, published post. A prior entry claimed all three as
  complete; none occurred (commit `6b682dc` contains only a README edit + a template).
- **Blocked on:** `ANTHROPIC_API_KEY`. The headline feature is cited answers; demoing
  retrieval-only would misrepresent the system.

### M8 — Day 8: Flagship scaffold + models + observability  ✅ DONE (blocked items noted)
- **Files:** `gtm-outbound-agent/src/gtm_outbound/**`, `gtm-outbound-agent/tests/**`, `docs/architecture.md`
- **Demo command:** `cd gtm-outbound-agent && .venv/bin/python -m pytest -q` → 28 passed
- **DoD:** scaffold ✅ · architecture doc ✅ · models ✅ · **migrations ✅ (3 tables)** ·
  Langfuse test event ⛔ needs `LANGFUSE_*` keys · push ✅ folded into `gtm-signal-intelligence` monorepo (subtree, history intact)
- **Migration defect (fixed 2026-07-24):** `init_db()` called `create_all()` while every
  model was a plain `BaseModel`, so nothing was ever registered — it ran cleanly and
  created **zero tables**. Added `tables.py` (SQLModel rows + domain converters), made the
  registering import explicit, and made `init_db()` raise on empty metadata instead of
  succeeding vacuously. Regression test runs in a subprocess importing only `db`, because
  the first version asserted it in-process and passed with the bug reintroduced — the test
  module's own import of `tables` was masking it.
- **Status:** shipped 2026-07-24. 8 core + 5 memory models, 5 agent stubs, SQLite/Postgres
  wiring, Langfuse tracing. Three schema defects found and fixed while writing the tests:
  `AccountBrief.emails` keyed by `persona_id` silently dropped all but the last variant per
  persona and could not be joined to per-variant evals; `SemanticFact.superseded_by` pointed
  at a `fact_id` field that did not exist; `PlaybookRule` had no id to update or retire.
  Episodic-admission thresholds are executable (`decide_memory_write`) rather than a comment,
  so writer / eval / consolidation cannot drift apart.

### M9 — Day 9: Research agent (sourced enrichment)  ✅ DONE (live run blocked)
- **Files:** `gtm-outbound-agent/src/gtm_outbound/{agents/research_agent,tools/web}.py`, `evals/`
- **Demo command:** `cd gtm-outbound-agent && .venv/bin/python -m pytest -q` → 64 passed
- **DoD:** `enrich()` returns a valid sourced profile ✅ (fake-client) · every field carries
  `source_url` ✅ (enforced by the tool schema) · ≥70% field accuracy ⛔ **not measured**
- **Status:** shipped 2026-07-24. Bounded 8-call tool loop; `CompanyProfile` fields became
  `Sourced[T]`; unsourceable fields are omitted rather than guessed, with `coverage()`
  separating "wrong" from "not found". Tool results are fenced per-result as untrusted
  (web content is attacker-controllable, and unlike Day 2 it arrives repeatedly mid-run).
- **Deliberate non-deliverable:** field accuracy is unmeasured. The gold set has 10 real
  companies with **empty** ground truth — asserting real companies' headcount/funding from
  memory would score the agent against guesses. `verified: false` rows are excluded and the
  harness reports `not measured`. Mutation-verified: removing the gate yields a false 1.0.

### M10 — Day 10: Scoring agent (ICP fit)  ✅ DONE (live Spearman blocked)
- **Files:** `gtm-outbound-agent/src/gtm_outbound/{agents/scoring_agent,icp}.py`,
  `evals/{scoring_gold,run_scoring_eval}.py`, `tests/test_{icp,scoring_agent,scoring_eval}.py`
- **Demo command:** `cd gtm-outbound-agent && .venv/bin/python -m pytest -q` → 94 passed
- **DoD:** `score()` returns a valid FitScore with per-dimension reasoning ✅ (fake-client) ·
  reasoning cites specific profile signals ✅ (`cited_signals`, closed schema) ·
  rank correlation > 0.6 ⛔ **not measured** (needs `ANTHROPIC_API_KEY`)
- **Status:** shipped 2026-07-25. Single forced tool call over four dimensions; the ICP is
  read from the KB's canonical `icp-definition.md` at score-time (`KBICPProvider`, injectable)
  rather than hard-coded — the first real use of the monorepo coupling. The overall `score`
  is a deterministic weighted mean of the model's four dimension scores, never emitted by the
  model, so it cannot contradict its own breakdown. Absent profile fields render `(not found)`
  so absence stays distinct from a confirmed negative.
- **Eval:** 15 **fictional** companies (7 strong / 4 weak / 4 none), labeled by construction
  against the ICP — honest ground truth without a live lookup, unlike Day 9's real companies.
  Spearman rank correlation (DoD gate > 0.6) + 3-band confusion matrix, both gated to
  `not measured` with no key. Mutation-verified: replacing the weighted mean with a plain
  mean makes `test_weights_are_applied_asymmetrically` fail (0.25 vs 0.30).

### M11 — Day 11: Persona agent (buyer discovery)  ✅ DONE (live metrics blocked)
- **Files:** `gtm-outbound-agent/src/gtm_outbound/{agents/persona_agent,positioning}.py`,
  `evals/run_persona_eval.py`, `tests/test_{positioning,persona_agent,persona_eval}.py`
- **Demo command:** `cd gtm-outbound-agent && .venv/bin/python -m pytest -q` → 122 passed
- **DoD:** returns 3 fully-populated stakeholder cards ✅ (fake-client) · cards vary by
  company ✅ (profile fenced into prompt; eval measures distinctness) · cards reference
  KB language ✅ (positioning injected; lexical grounding proxy) — live grounding/
  distinctness numbers ⛔ **not measured** (needs `ANTHROPIC_API_KEY`)
- **Status:** shipped 2026-07-25. Single forced tool call returning N persona cards;
  positioning read from the KB's `positioning.md` + two buyer-persona pages at build-time
  (`KBPositioningProvider`, injectable); persona ids assigned in code (`p{i}__{dept}`) for
  uniqueness rather than trusted from the model. Reuses the scoring agent's `render_profile`.
- **Eval:** 4 contrasting companies from the scoring gold set. Metrics: exactly-N-complete
  rate, KB grounding (a shallow lexical proxy vs `POSITIONING_TERMS`, explicitly not a
  semantic judge — a drift test asserts those terms still live in `positioning.md`), and
  cross-company distinctness (pairwise Jaccard on pain vocabularies). All gated to
  `not measured` without a key. Mutation-verified: a constant persona id collapses the
  uniqueness test (3 → 1).

### M12 — Day 12: Writing agent + async fan-out  ✅ DONE (live run blocked)
- **Files:** `gtm-outbound-agent/src/gtm_outbound/{agents/writing_agent,peerproof}.py`,
  `evals/run_writing_eval.py`, `tests/test_{peerproof,writing_agent,writing_eval}.py`
- **Demo command:** `cd gtm-outbound-agent && .venv/bin/python -m pytest -q` → 151 passed
- **DoD:** 3 personas × 3 variants = 9 emails ✅ (fake-client `draft_all`) · variants differ by
  angle ✅ (pain / trigger / peer-proof) · hooks traceable to profile or KB ✅ (schema + lexical
  proxy) · wall-clock < 90s ⛔ **not measured** (live) · Langfuse tagging ⛔ needs keys
- **Status:** shipped 2026-07-26. First async agent. `draft_emails` writes the 3 angle
  variants concurrently; `draft_all` fans out across personas. Every LLM call passes through
  **one shared `asyncio.Semaphore`** (default 5) so in-flight requests stay bounded run-wide.
  Peer-proof reads a segment-matched KB case study (`KBPeerProofProvider`). Subject/body/hook
  limits are schema- and limit-checked. v2-aware: an optional `MemoryRetrievalResult` fences
  learned rules / examples / account history into the prompt; the v1 path (no memory) drafts
  from profile + KB. Reuses `render_profile`.
- **Eval:** 1 company × 3 personas → 9 emails; email count, angle coverage, limit compliance,
  hook-traceability proxy (≥2 shared content words with the source data), wall-clock. Gated to
  `not measured` without a key.
- **Async testing:** coroutines driven by `asyncio.run` (no pytest-asyncio). The semaphore bound
  is covered by a probe client that records max simultaneous in-flight calls and asserts it never
  exceeds `max_concurrency` (2 over 9 calls) while still parallelising. **Mutation-verified
  2026-07-26:** unbounding the semaphore (`Semaphore(1000)`) drives 9 simultaneous calls and the
  probe test fails; clean restore.

### M13 — Day 13: Critique agent + Account Brief  ✅ DONE (live run blocked)
- **Files:** `gtm-outbound-agent/src/gtm_outbound/{agents/critique_agent,brief,pipeline}.py`,
  `evals/run_critique_eval.py`, `tests/test_{critique_agent,brief,pipeline,critique_eval}.py`
- **Demo command:** `cd gtm-outbound-agent && .venv/bin/python -m pytest -q` → 177 passed
- **DoD:** `run_company()` produces a complete `AccountBrief.md` saved to `runs/` ✅ (fake-client
  integration test) · brief opens cleanly as GitHub markdown ✅ (rendered + eyeballed) ·
  would-send pass rate at the top ✅ · live `run_company` run ⛔ needs `ANTHROPIC_API_KEY`
- **Status:** shipped 2026-07-26. Critique = single forced tool call, 5-dim skeptical rubric on
  Haiku; `critique()` also returns a `MemoryWriteDecision` via the Day-8 `decide_memory_write`
  policy (no threshold owned here). `brief.py` is pure/deterministic (no LLM): would-send rate at
  top, sourced company summary, ICP-fit table, persona cards, per-persona emails with inline
  verdicts, cost/latency; unfound fields render `_not found_`. `pipeline.py::run_company` chains
  all five agents (sync inline + async writing + concurrent critiques via `asyncio.to_thread`)
  and writes `runs/<domain>.md`.
- **Known limitation:** per-call token cost is not tracked — the brief reports `cost=$0` (real
  wall-clock latency). Cost accounting is deferred to the observability wiring, and stated as such
  rather than fabricated.
- **Eval:** 6-email calibration set (3 good / 3 spammy, would-send labels honest by construction);
  would-send agreement + spam-gap, gated to `not measured`. Mutation-verified the would-send pass
  rate (drop the `would_send` filter → 100%, two tests catch it). Full pipeline exercised offline
  by a routing fake client that dispatches on the forced tool name.

---

## Progress (loops append here on milestone completion — newest last)

- **M1 — Day 1 warmup CLI** — shipped 2026-07-20. 6/6 tests pass. Structured output via forced tool use; promo-aware pricing table; cost logged to `runs.jsonl`. Open: live run pending API key. (committed `day-01:` in gtm-cli-warmup)
- **M2 — Day 2 lead extractor** — shipped 2026-07-22. 8 offline tests (total suite 14/14 green). `extract_lead()` forces tool use, disables thinking, fences untrusted source text in user content only, records cost. Notebook staged with 6 synthetic inputs + gold labels; FIXTURE fallback when no key. Open: live sample run pending API key.
- **M3 — Day 3 Northstar corpus** — shipped 2026-07-22. 30 consistent docs + 2 READMEs; `check_corpus.sh` gate exit 0 (counts, frontmatter, canonical-fact consistency, contradiction guard). All fictional entities labelled. Ready for Day-4 RAG ingestion.
- **M4 — Day 4 RAG ingestion** — shipped 2026-07-23. `gtm_kb` package: section chunker, Chroma + BM25 over 177 chunks, RRF hybrid query, pluggable key-aware embedder (offline TF-IDF default, $0). 26 offline tests. [ADR 0001](decisions/0001-lean-rag-stack.md) records the lean-stack + offline-embedder decision.
- **M5 — Day 5 RAG assistant + UI** — shipped 2026-07-23. RAGAssistant orchestrator: hybrid retrieval (20 candidates) → Haiku reranker (top 5) → Sonnet answer generator with `[source: doc#section]` citations. Streamlit UI with expandable chunks, cost/latency metrics, query history. 7 new tests (33 total). Ready for Day-6 eval harness.
- **M5 hardening — 2026-07-24.** The Day-5 LLM stages had no tests, and a close read found four defects: (1) reranker validated model-returned indices against the full candidate list while showing only the first 20 — an index >20 crashed with `IndexError` on any query returning >20 candidates; (2) `1.0 - i*0.2` rerank decay saturated every rank past the 5th at 0.0; (3) `answer_gen` computed citations then discarded them, setting `cited_chunks` to every chunk shown, while `rag.py` re-implemented the same regex independently; (4) citations naming absent sources were dropped silently. All fixed; citation parsing centralised in `citations.py`; grounding failures surface as `unresolved_citations`; unpriced models now raise instead of reporting `$0.00`. +28 tests (61 total). Both headline fixes verified by mutation — reverting each makes its regression test fail.
- **M6 — Day 6 eval harness** — shipped 2026-07-23, **corrected 2026-07-24**. Fabricated metrics removed and the invalid "P@5" replaced with hit_rate / recall / chunk_precision / MRR. Faithfulness + completeness LLM judges implemented. Harness now renders `not measured` for anything it did not compute, and no longer substitutes a hardcoded 50 ms as a measured latency. +23 tests (84 total).
- **M8 — Day 8 flagship scaffold** — shipped 2026-07-24. `gtm_outbound` package: 13 Pydantic models (8 core + 5 memory), 5 agent stubs, SQLite/Postgres, Langfuse. Fixed 3 schema defects found while testing (variant keying, dangling `superseded_by`, missing rule id). 28 tests.
- **M9 — Day 9 research agent** — shipped 2026-07-24. `enrich(domain, provider)` runs a bounded 8-call tool-use loop returning a **sourced** `CompanyProfile` (every value carries `source_url`; unsourceable fields omitted, not guessed). Per-result injection fencing; enrichment eval with deterministic URL-grounding + coverage, field accuracy gated on human-verified ground truth (`not measured`, mutation-verified). 64 tests.
- **M10 — Day 10 scoring agent** — shipped 2026-07-25. `score(profile) -> FitScore`: single forced tool call over 4 ICP dimensions; ICP read from the KB's canonical `icp-definition.md` at score-time (injectable `KBICPProvider`, first real monorepo coupling); overall score a deterministic weighted mean, never model-emitted; absent fields render `(not found)`. 15 fictional companies labeled by construction (7/4/4) → Spearman + confusion, gated to `not measured` without a key. Mutation-verified weighted mean. 94 tests. (committed `day-10:` in gtm-outbound-agent/)
- **Repo consolidation — 2026-07-25.** Folded `gtm-outbound-agent` into this monorepo via `git subtree` (Day 8–9 history preserved), deleted the redundant sibling, pushed to `origin` for the first time. Docs updated across README/PLAN/CURRENT.
- **M11 — Day 11 persona agent** — shipped 2026-07-25. `build_personas(profile) -> list[Persona]`: single forced tool call returning 3 company-specific stakeholder cards, grounded in KB positioning (`KBPositioningProvider` reads `positioning.md` + two persona pages; injectable) and the fenced company profile. Persona ids assigned in code for uniqueness. Persona eval over 4 contrasting companies: exactly-N-complete rate, lexical KB-grounding proxy, cross-company distinctness — all gated to `not measured` without a key. Mutation-verified id uniqueness. 122 tests. (committed `day-11:` in gtm-outbound-agent/)
- **M12 — Day 12 writing agent + async fan-out** — shipped 2026-07-26. First async agent. `draft_emails(profile, persona)` writes 3 angle variants (pain / trigger / peer-proof) concurrently; `draft_all(profile, personas)` fans out across personas (9 emails/company) with one shared `asyncio.Semaphore` (default 5) bounding in-flight LLM calls run-wide. Peer-proof reads a segment-matched KB case study (`KBPeerProofProvider`). Subject/body/hook limits schema-checked; v2-aware memory injection optional. Writing eval: count / angle coverage / limit compliance / hook-traceability proxy / wall-clock, gated to `not measured` without a key. Concurrency probe test mutation-verified. 151 tests. (committed `day-12:` in gtm-outbound-agent/)
- **M13 — Day 13 critique agent + Account Brief** — shipped 2026-07-26. `evaluate(email, persona, profile)` = single forced Haiku tool call, 5-dim skeptical rubric; `critique()` also returns a `MemoryWriteDecision` via the Day-8 policy (no threshold owned here). `brief.py` renders a deterministic GitHub-markdown Account Brief (would-send rate at top, sourced summary, ICP-fit table, persona cards, per-persona emails with verdicts, cost/latency; unfound fields `_not found_`). `pipeline.py::run_company` chains all five agents (async writing + concurrent critiques via `asyncio.to_thread`) → `runs/<domain>.md`. Cost tracking deferred (brief reports $0, real latency). Critique calibration eval (6 emails, would-send agreement + spam-gap), gated. Full pipeline exercised offline by a routing fake; pass-rate mutation-verified. 177 tests. (committed `day-13:` in gtm-outbound-agent/)
