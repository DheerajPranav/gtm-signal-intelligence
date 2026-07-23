# GTM Signal Intelligence

> Turn raw GTM signals — company blurbs, lead bios, a knowledge base — into **structured, grounded, evaluated** revenue intelligence a RevOps/sales team could actually trust.

A four-week (28-day) applied-AI engineering sprint building a portfolio of GTM (go-to-market) AI capabilities: structured extraction, retrieval-augmented generation, agents, and the evals that keep them honest. Everything is built against one fixed, internally-consistent world — the fictional company **Northstar Analytics** — so every generated claim can be grounded and every capability can be measured.

## Engineering bar (non-negotiable)

- **If it wasn't evaluated, it doesn't count.** Every capability ships with a *computed* gate — a test or check that passes or fails, not a narrated "looks good."
- **Structured output via tool use only** — never string-parsing model text.
- **Cost, latency, and tokens logged from the first LLM call.** Total API spend is capped.
- **No fabricated model output.** Where no API key is present, pipelines are verified end-to-end with deterministic mocks, and nothing invented is presented as a real model result.
- **Honest data.** Northstar Analytics — its product, customers, leadership, metrics, and press — is entirely fictional and labelled as such throughout. No real person or company is represented.

## Status

| Day | Deliverable | Computed gate | Status |
|----:|-------------|---------------|--------|
| 1 | `describe` warmup CLI — structured company profile via forced tool use + cost logging | `pytest -q` → 6 pass | ✅ |
| 2 | `extract_lead()` — typed `Lead` with per-field confidence + evidence | `pytest -q` → 14 pass | ✅ |
| 3 | Northstar knowledge corpus — 30 consistent docs for RAG | `check_corpus.sh` → exit 0 | ✅ |
| 4 | RAG ingestion — section chunking, Chroma + BM25, hybrid query | `gtm_kb.ingest` + `pytest` → 26 pass | ✅ |
| 5 | RAG assistant — hybrid retrieval + rerank → cited answers + Streamlit UI + cost tracking | `streamlit run app.py` + `pytest` → 33 pass | ✅ |
| 6–7 | Golden eval set (35 Qs) + eval harness → deploy + Loom + LinkedIn ship | _tbd_ | ⏳ |
| 8–28 | Account research agent, outbound generation, and more (Weeks 2–4) | _tbd_ | ☐ |

**API spend to date:** `$0.00` — no live key yet; all Week-1 gates verified with deterministic mocks.

## Layout

```
gtm-signal-intelligence/
├── gtm-cli-warmup/         Days 1–2 — extraction primitives (Anthropic SDK, tool use, cost tracking)
│   ├── src/gtm_cli_warmup/ describe.py · lead.py · cost.py · pricing.py · cli.py
│   ├── tests/              offline mock-based tests (no API calls)
│   └── notebooks/          lead-extractor demo (key-aware; FIXTURE fallback)
├── gtm-knowledge-base/     Days 3–4 — Northstar corpus + RAG retrieval layer
│   ├── data/northstar/     product · sales · case-studies · marketing · company
│   ├── src/gtm_kb/         chunker · embeddings · Chroma+BM25 · ingest · query
│   ├── tests/              26 offline tests
│   └── scripts/            check_corpus.sh
├── .genesis/               engineering spine — plan, milestones, decisions, context graph
└── gtm_ai_sprint_master_plan.md   the full 4-week roadmap
```

## Reproduce the gates

```bash
# Days 1–2 — extraction primitives (offline, no API key needed)
cd gtm-cli-warmup
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest -q          # -> 14 passed

# Day 3 — knowledge corpus integrity
cd ../gtm-knowledge-base
bash scripts/check_corpus.sh           # -> CORPUS OK (exit 0)

# Day 4 — RAG ingestion + retrieval (offline, no API key needed)
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m gtm_kb.ingest      # -> 30 docs, 177 chunks (Chroma + BM25)
.venv/bin/python -m pytest -q          # -> 26 passed
```

## Highlights so far

- **Prompt-injection-aware extraction.** Untrusted source text is fenced in explicit markers in the *user* turn only (never the system prompt), with a system instruction that fenced text is data, not instructions.
- **Closed, strict schemas.** JSON schemas are recursively closed (`additionalProperties: false` everywhere) so the model can't invent fields; enums are validated offline.
- **Honest pricing.** A promo-aware pricing table computes real cost per call and raises on unknown models rather than silently reporting `$0`.
- **A corpus built for grounding.** 30 cross-linked docs share one canonical fact sheet (ICP, competitors, pricing, locked metrics), enforced by an integrity check — the substrate for RAG and hallucination detection.

## Tech

Python 3.11+ · Anthropic Claude (Sonnet default, Haiku for cheap extraction, Opus for hard reasoning) · Pydantic v2 · pytest. RAG/agent stack (embeddings, vector store, LlamaIndex, FastAPI/Streamlit, evals) lands in Weeks 1–4 as the milestones above ship.

---

*Portfolio sprint. Northstar Analytics is fictional. Built by Dheeraj Pranav.*
