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
- [ ] Pushed — no remote configured yet

```bash
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest -q     # -> 28 passed
```

## Status

✅ **Complete (Day 8):**
- Pydantic models for v1 + v2 (core + memory)
- Agent stubs (5 agents wired but not implemented)
- Observability (Langfuse wiring)
- DB setup (SQLite + Postgres support)
- Architecture documentation

⏳ **Upcoming:**
- Day 9: Research agent (web search enrichment)
- Day 10: Scoring agent (ICP fit)
- Day 11: Persona agent (buyer discovery)
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
