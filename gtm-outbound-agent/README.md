# GTM Outbound Agent

> Multi-agent account research and personalized outbound generation system. Queries the Northstar knowledge base, scores ICP fit, discovers personas, drafts personalized emails, and critiques them. v2 adds a learning loop: episodic, semantic, and procedural memory so the agent improves batch-to-batch.

## Architecture (v1)

```
                    ┌─────────────────────────────────────────────┐
                    │  Input: List of target domains              │
                    └────────────────┬────────────────────────────┘
                                     ▼
                         ┌─────────────────────────┐
                         │  Research Agent         │ (web search, news, fetch)
                         │  → CompanyProfile       │
                         └────────────┬────────────┘
                                      ▼
                         ┌─────────────────────────┐
                         │  Scoring Agent          │ (KB query + rubric)
                         │  → FitScore             │
                         └────────────┬────────────┘
                                      ▼
                         ┌─────────────────────────┐
                         │  Persona Agent          │ (structured extraction)
                         │  → [Persona, ...]       │
                         └────────────┬────────────┘
                                      ▼
                    ┌────────────────────────────────────┐
                    │  For each Persona:                 │
                    │  ┌──────────────────────────────┐  │
                    │  │  Writing Agent               │  │
                    │  │  → [EmailDraft, ...]         │  │
                    │  └────────┬─────────────────────┘  │
                    │           ▼                        │
                    │  ┌──────────────────────────────┐  │
                    │  │  Critique Agent              │  │
                    │  │  → EmailEval + would_send?   │  │
                    │  └──────────────────────────────┘  │
                    └────────────────────────────────────┘
                                      ▼
                         ┌─────────────────────────┐
                         │  Output: AccountBrief   │ (complete brief + evals)
                         └─────────────────────────┘
```

## v2 Learning Loop Architecture

Three memory layers augment the writing pipeline:

- **Episodic memory** (vector store): Past successful emails + scores, tagged with segment metadata (industry, persona, angle)
- **Semantic memory** (Postgres): Account facts (last contact, known people, funding events, pain points, etc.)
- **Procedural memory** (Postgres): Playbook rules learned nightly ("For fintech VP RevOps, trigger-event angles convert 34% higher")

At write-time, a **retrieval router** queries all three layers and stuffs the context into the writing agent. After critique, a **memory write hook** decides what gets persisted. A nightly **consolidation job** scans episodic memory to synthesize new procedural rules.

## Tech Stack

- **Language:** Python 3.11+
- **LLM:** Anthropic Claude (Sonnet for research + writing, Haiku for scoring + critique)
- **Web search:** Tavily API (or Anthropic web search)
- **Vector DB:** Chroma (v2 episodic memory)
- **Structured DB:** SQLite (dev) / Postgres (prod) for semantic + procedural memory
- **Observability:** Langfuse
- **Structured output:** Pydantic v2 + tool use
- **UI:** Streamlit (dashboard + v2 memory browser + learning curves)

## Day 8 Checklist

- [x] Repo scaffolded
- [x] Architecture diagram — [`docs/architecture.md`](docs/architecture.md)
- [x] Pydantic models (v1 core + v2 memory) — 8 core + 5 memory
- [x] SQLite + Postgres support wired
- [x] **SQLite migrations run** — 3 tables, verified in a subprocess that imports only `db`
- [x] Langfuse observability wiring
- [x] Agent stubs (5 agents with signatures)
- [x] 28 tests pass
- [ ] Langfuse dashboard shows a test event — **blocked**, needs `LANGFUSE_*` keys
- [x] Pushed — folded into the `gtm-signal-intelligence` monorepo (history preserved via `git subtree`)

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest -q     # -> 28 passed
```

## Day 9 — Research Agent

`enrich(domain, provider)` runs a bounded tool-use loop (`web_search`, `fetch_page`,
`news_search`, max 8 calls) and returns a **sourced** `CompanyProfile`.

- **Provenance is structural.** Every value is a `Sourced[T]` carrying `value`,
  `source_url`, `confidence`. The tool schema requires `source_url` per field, so
  provenance is captured at extraction time rather than reconstructed afterwards.
- **Gaps beat guesses.** No field is required. A field the agent cannot source is
  omitted, and `coverage()` reports how much was found — so the eval can tell "wrong"
  apart from "not found".
- **Injection-aware.** Every tool result is fenced in `<<<UNTRUSTED_WEB_CONTENT …>>>`
  markers with the source URL attached, and the system prompt states that fenced content
  is data. Web pages are attacker-controllable; a page telling the agent to rate its own
  company favourably is a realistic attack, not a hypothetical.
- **Degrades, doesn't abort.** Tool failures return as text so the agent can adapt;
  budget exhaustion forces the final answer instead of truncating the run.

### Eval

```bash
.venv/bin/python evals/run_enrichment_eval.py --offline   # gold-set readiness, no network
.venv/bin/python evals/run_enrichment_eval.py             # live run
```

| Metric | Status | Depends on |
|---|---|---|
| URL grounding | computable now | nothing — deterministic |
| Field coverage | computable now | nothing |
| Field accuracy | **not measured** | hand-verified ground truth |

**URL grounding** checks that every cited `source_url` was actually retrieved during the
run. A citation to a URL the agent never fetched is fabricated provenance — the worst
failure mode here, because it looks sourced. This needs no LLM judge.

**Field accuracy is deliberately unmeasured.** `evals/enrichment_gold.jsonl` ships with
10 real companies and *empty* ground truth. Filling in headcount and funding stage from
memory would produce an accuracy figure measured against guesses. The harness excludes
`verified: false` rows and reports `not measured` until a human populates them — see
[`evals/README.md`](evals/README.md).

## Day 10 — Scoring Agent

`score(profile) -> FitScore` scores ICP fit across four dimensions (firmographic,
technographic, behavioral, timing) in a single forced tool call, grounded in the
knowledge base.

- **The ICP comes from the KB, not the prompt.** `KBICPProvider` reads Northstar's
  canonical `icp-definition.md` from the sibling `gtm-knowledge-base/` corpus at
  score-time, so the rubric can't drift from the single source of truth the RAG
  assistant also answers from. The provider is injectable — tests use a static string.
- **The overall score is derived, not asserted.** The model scores the four dimensions;
  the headline `score` is a deterministic weighted mean (behavioral + firmographic
  weighted highest, per the ICP's own emphasis). The number can never contradict its
  breakdown, and re-weighting is one line, not a re-prompt.
- **Absence ≠ disqualification.** A field the research agent couldn't source is shown to
  the model as `(not found)`, so "we looked and it's weak" stays distinct from "we never
  found out" — only the ICP's explicit hard disqualifiers pull a score to the floor.
- **Grounded reasoning.** Every score carries per-dimension reasoning plus `cited_signals`
  quoting the specific profile facts used.

### Eval

15 **fictional** companies (7 strong / 4 weak / 4 not-fit), labeled by construction
against the ICP — the one place ground truth can be asserted without a live lookup
(contrast Day 9's real companies). Metrics: **Spearman rank correlation** (DoD gate
> 0.6) and a **3-band confusion matrix**. Both need live scores, so both are gated:
no key → `not measured`, never a fabricated correlation.

```bash
.venv/bin/python evals/run_scoring_eval.py --offline   # gold-set readiness, no key
.venv/bin/python evals/run_scoring_eval.py             # live run (needs ANTHROPIC_API_KEY)
```

## Day 11 — Persona Agent

`build_personas(profile) -> list[Persona]` returns N (default 3) buyer-persona
stakeholder cards in a single forced tool call, grounded in the company profile *and*
Northstar's KB positioning.

- **Positioning comes from the KB.** `KBPositioningProvider` reads Northstar's
  `positioning.md` plus the two buyer-persona pages at build-time (injectable, like the
  scoring agent's ICP), so cards use real Northstar language instead of paraphrase.
- **Cards are company-specific.** The profile (industry, size, stack, signals) is fenced
  into the prompt so a fintech and a devtools company get different pain framing — the
  eval measures this as cross-company distinctness.
- **Ids are assigned in code** (`p{i}__{department}`), not trusted from the model, so
  they are unique and stable for joining emails to personas downstream.

### Eval

Runs 4 contrasting companies (fintech / devtools / logistics / RevOps) drawn from the
scoring gold set. Metrics: exactly-N-complete-cards rate, **KB grounding** (a deliberately
shallow lexical proxy against Northstar's "words we use" — explicitly not a semantic
judge), and **cross-company distinctness** (pairwise Jaccard distance of pain vocabularies).
All three need live output, so all three gate to `not measured` without a key.

```bash
.venv/bin/python evals/run_persona_eval.py --offline   # readiness, no key
.venv/bin/python evals/run_persona_eval.py             # live run (needs ANTHROPIC_API_KEY)
```

## Status

✅ **Complete (Day 8):**
- Pydantic models for v1 + v2 (core + memory)
- Agent stubs (5 agents wired but not implemented)
- Observability (Langfuse wiring)
- DB setup (SQLite + Postgres support)
- Architecture documentation

✅ **Complete (Day 9):** research agent, sourced profiles, injection fencing,
enrichment eval harness. Open: needs `ANTHROPIC_API_KEY` + `TAVILY_API_KEY`
for a live run, and a human to verify the gold set before accuracy can be reported.

✅ **Complete (Day 10):** scoring agent, KB-grounded ICP rubric, deterministic weighted
overall, 15-company labeled eval (Spearman + confusion matrix). Open: live
Spearman needs `ANTHROPIC_API_KEY`.

✅ **Complete (Day 11):** persona agent, KB positioning grounding, company-specific
cards, persona eval (count / grounding proxy / distinctness). **122 tests.** Open: live
metrics need `ANTHROPIC_API_KEY`.

⏳ **Upcoming:**
- Day 12: Writing agent (email drafting, v2-aware)
- Day 13: Critique agent (scoring + memory write decision)
- Day 14: Integration + evals

📅 **Week 5-6 extension (v2 Learning Loop):**
- Episodic + semantic + procedural memory layers
- Memory retrieval router (at write-time)
- Memory write hook (after critique)
- Consolidation job (nightly rule learning)
- Eval harness (baseline metrics, learning curves, ablation study)
- Streamlit dashboard enhancements

---

**Portfolio sprint.** Northstar Analytics is fictional. Built by Dheeraj Pranav.
