# Progress log — gtm-outbound-agent

The flagship Week-2 project: a multi-agent account-research → personalized-outbound
system. This is the per-project view; the sprint-wide log lives in
[`../.genesis/PLAN.md`](../.genesis/PLAN.md).

> **Note (2026-07-25):** this project was scaffolded as its own repo, then folded into the
> `gtm-signal-intelligence` monorepo via `git subtree` (Day 8–9 history preserved). This
> PROGRESS.md was backfilled at that point to match the convention used by the Week-1
> subprojects.

## Day 8 (2026-07-24) — Flagship scaffold + models + observability

**What shipped:** the `gtm_outbound` package — 13 Pydantic models (8 core + 5 memory),
5 agent stubs, SQLite/Postgres wiring, Langfuse tracing. Architecture doc covering the v1
pipeline and the v2 learning loop.

**Defects found and fixed while testing:** three schema bugs — `AccountBrief.emails` keyed
by `persona_id` silently dropped all but the last variant per persona; `SemanticFact`'s
`superseded_by` pointed at a `fact_id` that didn't exist; `PlaybookRule` had no id to update
or retire. Plus a **migration bug**: `init_db()` ran `create_all()` on empty metadata and
created **zero tables** — fixed with `tables.py` + an explicit registering import + a guard
that raises on empty metadata. Regression test runs in a subprocess importing only `db`
(the first version masked the bug by importing `tables` itself). 28 tests.

**Open:** Langfuse dashboard event needs `LANGFUSE_*` keys.

## Day 9 (2026-07-24) — Research agent (sourced enrichment)

**What shipped:** `enrich(domain, provider)` runs a bounded 8-call tool-use loop
(`web_search` / `fetch_page` / `news_search`) and returns a **sourced** `CompanyProfile` —
every value is a `Sourced[T]` carrying `value` + `source_url` + `confidence`, enforced by
the tool schema so provenance is captured at extraction time. Unsourceable fields are
**omitted, not guessed**; `coverage()` separates "wrong" from "not found". Tool results are
fenced per-result as untrusted web content.

**Eval:** URL-grounding (deterministic — every cited URL must have been retrieved) +
coverage. Field accuracy is **deliberately not measured**: the gold set has 10 *real*
companies with empty ground truth, because asserting real headcount/funding from memory
would score the agent against guesses. `verified: false` rows are excluded; mutation-verified
that removing the gate yields a false 1.0. 64 tests.

**Open:** live run needs `ANTHROPIC_API_KEY` + `TAVILY_API_KEY`; a human must verify the
gold set before accuracy can be reported.

## Day 10 (2026-07-25) — Scoring agent (ICP fit)

**What shipped:** `score(profile) -> FitScore` — a single forced tool call scoring four ICP
dimensions (firmographic / technographic / behavioral / timing). The ICP is read from the
KB's canonical `icp-definition.md` at score-time (`KBICPProvider`, injectable) rather than
hard-coded — the first real use of the monorepo coupling. The overall `score` is a
**deterministic weighted mean** of the model's four dimension scores, never emitted by the
model, so it can't contradict its own breakdown. Absent profile fields render `(not found)`
so absence stays distinct from a confirmed negative. Each score carries per-dimension
reasoning + `cited_signals`.

**Eval:** 15 **fictional** companies (7 strong / 4 weak / 4 not-fit), labeled honestly *by
construction* against the ICP — the one place ground truth needs no live lookup. Metrics:
Spearman rank correlation (DoD gate > 0.6) + 3-band confusion matrix, both gated to
`not measured` without a key. Mutation-verified the weighted mean (plain mean → 0.25 vs
0.30). +30 tests (94 total).

## Day 11 (2026-07-25) — Persona agent (buyer discovery)

**What shipped:** `build_personas(profile) -> list[Persona]` — a single forced tool call
returning 3 company-specific buyer-persona stakeholder cards. Positioning is read from the
KB (`positioning.md` + two buyer-persona pages) at build-time via `KBPositioningProvider`
(injectable), so cards use real Northstar language. The company profile is fenced into the
prompt so a fintech and a devtools company get different pain framing. Persona ids are
assigned **in code** (`p{i}__{dept}`) for uniqueness, not trusted from the model. Reuses the
scoring agent's `render_profile`.

**Eval:** 4 contrasting companies. Metrics: exactly-N-complete-cards rate, a **lexical
KB-grounding proxy** (vs `POSITIONING_TERMS`, explicitly not a semantic judge, drift-guarded
against `positioning.md`), and **cross-company distinctness** (pairwise Jaccard on pain
vocabularies). All gated to `not measured` without a key. Mutation-verified persona-id
uniqueness (constant id → 3 collapse to 1). +28 tests (122 total).

## Day 12 (2026-07-26) — Writing agent + async fan-out

**What shipped:** the first **async** agent. `draft_emails(profile, persona) -> list[EmailDraft]`
produces three variants that differ in *angle*, not just wording: **pain-led** (persona's
sharpest pain in Northstar language), **trigger-led** (a recent event from the profile), and
**peer-proof** (a segment-matched Northstar customer story). `draft_all(profile, personas)`
fans out across personas — 3 personas × 3 variants = 9 emails — with every LLM call passing
through **one shared `asyncio.Semaphore` (default 5)**, so total in-flight requests stay
bounded regardless of company size. Each variant is a single forced tool call; subject
(≤60 chars), body (≤120 words), and exactly 3 personalization hooks are schema/limit-checked.

**Grounding:** the peer-proof angle reads a segment-matched case study from the KB
(`KBPeerProofProvider` picks fintech / devtools / marketing / default by industry). Variant
ids are `{persona.id}__{angle}`, unique run-wide. **v2-aware:** an optional
`MemoryRetrievalResult` fences `<applicable_rules>`/`<successful_examples>`/`<account_history>`
into the prompt; with no memory (the v1 path) it drafts from profile + KB only.

**Eval:** `run_writing_eval.py` over one company × 3 personas → 9 emails. Metrics: email count,
angle coverage, subject/body/hooks limit compliance, **hook traceability** (a lexical proxy —
a hook must share ≥2 content words with the source data, explicitly not a semantic judge), and
wall-clock (DoD target < 90s, meaningful only live). All model-dependent metrics gated to
`not measured` without a key.

**Verified:** 151 tests (+29). Async tests drive coroutines with `asyncio.run` (no event-loop
plugin). The concurrency bound is covered by a **probe client** that records max simultaneous
in-flight calls and asserts it never exceeds the semaphore (2 with `max_concurrency=2` over 9
calls) while still parallelising — mutation-verified (unbounded semaphore → 9 simultaneous →
test fails). **Open:** live 9-email run + wall-clock need `ANTHROPIC_API_KEY`; Langfuse call
tagging deferred with the rest of the observability wiring.

## Day 13 (2026-07-26) — Critique agent + Account Brief

**What shipped:** the fifth agent and the assembly layer that turns five agents' output into a
shippable document.

- **Critique agent** — `evaluate(email, persona, profile) -> EmailEval`: a single forced tool
  call scoring five dimensions (personalization, relevance, CTA, spam-risk inverted, would-send)
  with a *deliberately skeptical* rubric to avoid judge sycophancy. Runs on **Haiku** (cheap;
  9× per company). `critique(...)` returns the eval **and** a `MemoryWriteDecision` by applying
  the Day-8 `decide_memory_write` policy — the agent owns no threshold of its own, so writer /
  critique / eval / consolidation can't drift apart.
- **Account Brief** — `brief.py` (`assemble_brief` + `render_brief_md`, pure/deterministic, no
  LLM) produces a GitHub-renderable markdown doc: **would-send pass rate at the top**, company
  summary with sourced links, ICP fit table, persona cards, emails grouped per persona with
  inline critique verdicts, and cost/latency. Unfound profile fields render `_not found_`, never
  fabricated.
- **Pipeline** — `pipeline.py::run_company(domain)` chains all five agents (sync research/score/
  persona/critique inline, async writing fan-out, the 9 critiques run concurrently via
  `asyncio.to_thread`), assembles the brief, and writes `runs/<domain>.md`. Latency is real
  wall-clock; **cost is passed through as 0.0 — per-call token accounting isn't wired yet** (it
  lands with observability), so the brief reports 0 rather than a fabricated figure.

**Eval:** `run_critique_eval.py` — a 6-email calibration set (3 clearly-good / 3 clearly-spammy,
would-send labels honest by construction). Metrics: would-send agreement vs label, and spam-gap
(bad − good spam-risk, should be clearly positive). Gated to `not measured` without a key.

**Verified:** 177 tests (+26). The whole pipeline is exercised end-to-end offline by a **routing
fake client** that dispatches by the forced tool name (order-independent), producing a real brief
file. Mutation-verified the would-send pass rate (dropping the `would_send` filter inflates it to
100% and two tests catch it). **Open:** live `run_company` run + Langfuse tagging + per-call cost
tracking need `ANTHROPIC_API_KEY` and the observability wiring.
