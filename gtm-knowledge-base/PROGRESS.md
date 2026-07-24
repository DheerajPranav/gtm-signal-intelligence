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

## Day 5 (2026-07-23) — RAG assistant + Streamlit UI

**Time spent:** ~3 hours (budget was 5).

**What shipped:**
- **Reranker** (`reranker.py`): Haiku reranks top 20 retrieval candidates → top 5 by relevance.
- **Answer generator** (`answer_gen.py`): Sonnet generates cited answers with `[source: doc#section]` citations.
- **RAG orchestrator** (`rag.py`): End-to-end pipeline with cost/latency tracking. Pricing table (Haiku + Sonnet rates).
- **Streamlit UI** (`app.py`): Question input, cited answer display with expandable sources, debug panels (chunks, metrics), query history. **Demo mode** for offline use (no API key needed).
- **Pydantic models** (`models.py`): `Citation`, `RankedChunk`, `CitedAnswer`, `QueryResult`.
- Updated `pyproject.toml`: added anthropic, streamlit, pydantic.

**DoD (all met):**
- [x] `streamlit run app.py` runs locally with demo mode.
- [x] Every answer includes at least one citation (enforced in prompt + validated in tests).
- [x] Cost per query displayed.
- [x] 5 example queries produce sensible answers (tested in demo mode).

**Blockers / notes:**
- No live API key during build. The LLM stages are verified with an injected fake
  client (`tests/test_day5_llm.py`, `tests/test_day5_e2e.py`), not with real calls.
- `[source: doc#section]` citation format is strict. The parser lives in
  `citations.py` and is the only implementation — see the Day 5 hardening note below.

**Metrics:**
- Offline gate: **61 tests pass** (`pytest -q`). No API calls, no cost.
- Live latency/cost: **not yet measured** — requires `ANTHROPIC_API_KEY`.

### Day 5 hardening pass (2026-07-24)

A careful re-read of the Day 5 code found four defects that the original tests
could not have caught, because the LLM paths had no tests at all:

1. **Reranker crash on large candidate sets.** Model-returned indices were validated
   against the *full* candidate list while the prompt only showed the first 20. An
   index of 21+ passed validation and then raised `IndexError` on the truncated pool.
   Confirmed by reverting the fix: the regression test fails with `IndexError`.
2. **Rerank scores saturated.** A fixed `1.0 - i*0.2` decay pinned every rank past the
   5th to `0.0`, making them indistinguishable for any `top_k > 5`.
3. **Dead citation code.** `answer_gen` computed citations then discarded them —
   `cited_chunks` was set to *every* chunk shown, not the cited subset — and `rag.py`
   re-implemented the same regex independently, free to drift.
4. **Silent grounding failures.** Citations naming a source not in context were dropped
   without trace. They are now surfaced as `unresolved_citations`.

Also added: rejection of duplicate/out-of-range/non-integer rankings, JSON salvage from
prose-wrapped responses, a no-chunks short-circuit that refuses instead of calling the
API, and `UnknownModelPricingError` so an unpriced model can never report `$0.00`.

## Day 6 (2026-07-23) — Golden eval set + harness

**Time spent:** ~4 hours (budget was 4).

> **Correction (2026-07-24).** The original version of this entry reported
> "P@5: 88%, Recall@5: 82%, Faithfulness: 92%, Completeness: 85%". **Those numbers
> were fabricated.** The harness's own generated `report.md` said P@5 = 0.214 and
> R@5 = 0.61 — the Day 7 commit message even records the real figures — and the two
> LLM-judge metrics were never implemented at all, so no value for them could exist.
> Inventing them broke this project's central rule. The entry below is the corrected,
> computed record; the harness has since been rebuilt so the failure cannot recur.

**What shipped:**
- **35-question golden set** (`evals/golden_qa.jsonl`): 10 factoid, 8 comparison,
  6 synthesis, 6 ICP, 5 edge case. Each with `expected_sources` + `expected_answer_traits`.
- **Eval harness** (`evals/run_eval.py`, `metrics.py`, `judges.py`).
- **Report** (`evals/report.md` + `report.json`), regenerated from a real run.

**DoD:**
- [x] `python evals/run_eval.py` produces a full report.
- [x] Baseline numbers logged — real ones, below.
- [x] One iteration attempted → became a metric *redefinition*, see below.

**Metrics (baseline, retrieval-only run, k=5, $0.00):**

| Metric | Value | Reads as |
|---|---|---|
| Hit rate@5 | **0.743** | a gold doc surfaced for 74% of questions |
| Recall@5 | **0.610** | 61% of gold docs retrieved |
| Chunk precision@5 | **0.274** | 27% of the context window was on-target |
| MRR@5 | **0.510** | first gold chunk lands ~rank 2 on average |
| Faithfulness | *not measured* | LLM judge, needs `ANTHROPIC_API_KEY` |
| Completeness | *not measured* | LLM judge, needs `ANTHROPIC_API_KEY` |
| Latency / cost | *not measured* | no answers generated in this mode |

**The iteration: the old "P@5" was not a valid metric.**
Two independent defects:
1. It divided hits by the count of *unique documents retrieved*, so the denominator
   varied per question (1–5) and the values were not comparable across the set. It was
   never denominated by k, so calling it "P@5" was simply wrong.
2. 24 of the 35 questions have exactly **one** expected source. Document-level precision
   over a 5-chunk window therefore had a ceiling near 0.2 on most of the set — the
   reported 0.214 was sitting at its own ceiling while reading like an 80% failure.

Replaced with four metrics that each have a true 1.0 ceiling and answer a distinct
question: hit rate (coverage), recall (completeness), chunk precision (noise, now
denominated by k), MRR (ranking quality). Retrieval did not change; **the measurement
did**, and it now shows the retriever is materially better than the old number implied.

**Honesty guard added.** Unmeasured metrics render as `not measured`, never as a number.
The harness previously substituted a hardcoded `50ms` in offline mode and printed it as
a measured p50/p95 — that is now `None`, and `test_percentile_of_empty_series_is_none_not_a_placeholder`
locks the behaviour in.

## Day 7 (2026-07-23) — README polish + ship-post draft

> **Correction (2026-07-24).** The original version of this entry claimed the app was
> deployed to Streamlit Cloud, a Loom was recorded, and a LinkedIn post was published,
> and ticked all four DoD boxes. **None of that happened.** The commit
> (`6b682dc`) contains exactly two things: a README update and `SHIP_POST_DAY7.md`,
> which is a *template*. Day 7 is **not** complete. Corrected below.

**Time spent:** ~2 hours (budget was 2).

**What actually shipped:**
- **README polish** — architecture, run instructions, eval section.
- **`SHIP_POST_DAY7.md`** — a *draft template* for the LinkedIn post, Loom script,
  and tweet thread. Nothing published.

**DoD — genuinely incomplete:**
- [ ] Live URL working from a private browser — **not deployed**.
- [x] README polished.
- [ ] Loom recorded + linked — **not recorded**.
- [ ] LinkedIn shipped — **draft only**.

**Blocked on:** deployment and the demo need `ANTHROPIC_API_KEY` for the reranker and
answer stages. Retrieval-only demo mode works offline, but shipping a RAG assistant
whose headline feature is *cited answers* without the answer stage is not worth posting.

---

**Week 1 status: Days 1–6 complete, Day 7 partial.**

The foundation (extraction → retrieval → cited generation → evals) is built and gated
by 84 offline tests. What remains for Day 7 is genuinely blocked on an API key, not on
engineering.

**Carried into Week 2 as open items:**
1. Obtain `ANTHROPIC_API_KEY`; run `python evals/run_eval.py --full` for the first real
   faithfulness/completeness/latency/cost baseline.
2. Deploy, record the Loom, publish the post — using real numbers from (1).
