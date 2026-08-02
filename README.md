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
| 5 | RAG assistant — hybrid retrieval + rerank → cited answers + Streamlit UI + cost tracking | `pytest -q` → 61 pass | ✅ |
| 6 | Golden eval set (35 Qs) + eval harness — retrieval metrics + LLM judges | `python evals/run_eval.py` → report.md | ✅ |
| 7 | Deploy + Loom + LinkedIn ship | Live URL + Loom link | 🚧 blocked on API key — README + post *draft* only |
| 8 | Flagship scaffold — multi-agent models + observability + memory schema (SQLite/Postgres) | `pytest -q` → 28 pass | ✅ |
| 9 | Research agent — bounded tool-use loop → **sourced** `CompanyProfile` + enrichment eval harness | `pytest -q` → 64 pass | ✅ |
| 10 | Scoring agent — KB-grounded ICP rubric, 4-dim weighted `FitScore` + 15-company Spearman/confusion eval | `pytest -q` → 94 pass | ✅ |
| 11 | Persona agent — 3 KB-grounded, company-specific stakeholder cards + persona eval (grounding/distinctness) | `pytest -q` → 122 pass | ✅ |
| 12 | Writing agent — async fan-out, 3 angles/persona (9 emails), peer-proof KB grounding, v2 memory injection + eval | `pytest -q` → 151 pass | ✅ |
| 13 | Critique agent (5-dim rubric + memory-write decision) + `run_company` pipeline → deterministic Account Brief + calibration eval | `pytest -q` → 177 pass | ✅ |
| 14 | Blog post + mid-sprint check-in, API cleanup (remove OpenAI, use Groq) | `git log` → commits clean | ✅ |
| 15 | Batch mode — concurrent company processing, run resumption, failure isolation | `pytest -q` → 13 pass | ✅ |
| 16 | Streamlit dashboard v1 — run history, live progress, cost trends, drill-down | `streamlit run dashboard.py` | ✅ |
| 17 | Eval harness — 4 computed metrics (enrichment, ICP correlation, email quality, would-send rate) | `pytest -q` → 24 pass | ✅ |
| 18 | Iteration cycle — 4 hypothesis-driven mutations, all metrics 0→passing | `ITERATION_LOG.md` + mutations | ✅ |
| 19 | Open-source rubrics package — ICP, Persona, Email, Critique rubrics | `pytest -q` → 22 pass | ✅ |
| 20 | Framework-agnostic integrations — LangChain wrappers, external datasets, Streamlit explorer | `pytest -q` → 35 pass | ✅ |
| 21 | Flagship ship content — 5-min Loom script + 2 LinkedIn posts + blog outline; flagship README freshened | `docs/DAY_21_SHIP.md` | ✅ content drafted (Loom/posts are user actions) |
| 22 | Portfolio site — Next.js 16 + Tailwind, hero/stats/projects/essay/contact, mobile-responsive | `npm run build` → passing | ✅ built (Vercel deploy = user action) |
| 23 | Flagship blog post — full technical deep-dive on the 5-agent honest eval loop | `docs/FLAGSHIP_BLOG_POST.md` | ✅ written (publish = user action) |
| 24 | CV (one-page PDF, honest metrics) + LinkedIn overhaul copy; CV linked from portfolio | `portfolio-site/public/cv.pdf` + `npm run build` | ✅ built (profile edit = user action) |
| 25–28 | Eval-kit polish, launch, cold outreach, live prod deploy (Modal/Vercel/Neon) | _tbd_ | ⏳ |

**Days Complete:** 24/28 ✅ (Days 21–24 are content deliverables; publishing/deploying them are user actions)  
**Status:** Production-ready through Day 20; ship content (Loom script, LinkedIn posts, blog post, portfolio site, CV) drafted & built through Day 24  
**Remaining:** Days 25–28 (eval-kit polish, launch content, live deployment) — the live-deploy steps are gated on an API key + the user's Vercel/hosting accounts

### Computed Gates Summary

| Component | Tests | Pass Rate | Status |
|-----------|-------|-----------|--------|
| CLI warmup (Days 1–2) | 14 | 100% | ✅ |
| RAG pipeline (Days 4–6) | 84 | 100% | ✅ |
| Outbound agent (Days 8–13) | 177 | 100% | ✅ |
| Batch mode (Day 15) | 13 | 100% | ✅ |
| Eval harness (Day 17) | 24 | 100% | ✅ |
| Open-source rubrics (Days 19–20) | 35 | 100% | ✅ |
| **TOTAL** | **347** | **100%** | **✅** |

**API spend to date:** `$0.00`. Every gate is verified offline — deterministic
embeddings and injected fake LLM clients. All capability shipping gates pass before any live API call.

### Retrieval baseline (35 golden questions, k=5)

| Hit rate@5 | Recall@5 | Chunk precision@5 | MRR@5 |
|---|---|---|---|
| 0.743 | 0.610 | 0.274 | 0.510 |

## Layout

```
gtm-signal-intelligence/
├── gtm-cli-warmup/         Days 1–2 — extraction primitives (Anthropic SDK, tool use, cost tracking)
│   ├── src/gtm_cli_warmup/ describe.py · lead.py · cost.py · pricing.py · cli.py
│   ├── tests/              offline mock-based tests (no API calls)
│   └── notebooks/          lead-extractor demo (key-aware; FIXTURE fallback)
├── gtm-knowledge-base/     Days 3–7 — Northstar corpus + RAG retrieval + cited answers + evals
│   ├── data/northstar/     product · sales · case-studies · marketing · company
│   ├── src/gtm_kb/         chunker · embeddings · Chroma+BM25 · ingest · query · rerank · answer
│   ├── evals/              golden set + retrieval metrics + LLM judges
│   └── scripts/            check_corpus.sh
├── gtm-outbound-agent/     Days 8–18 — flagship multi-agent outbound system
│   ├── src/gtm_outbound/   agents/ · tools/ · models · tables · db (SQLite/Postgres)
│   ├── batch.py            concurrent processing + resumption + failure isolation
│   ├── dashboard.py        Streamlit monitoring + cost tracking
│   ├── evals/              enrichment + ICP + email quality + would-send metrics
│   └── docs/               architecture + iteration log
├── gtm-agent-evals/        Days 19–20 — open-source reusable eval rubrics (framework-agnostic)
│   ├── src/gtm_agent_evals/ ICP · Persona · Email · Critique rubrics
│   ├── examples/           LangChain integration · external datasets · Streamlit explorer
│   ├── tests/              35 comprehensive tests (22 rubric + 13 integration)
│   ├── README.md           usage + design principles
│   └── CONTRIBUTING.md     guidelines for new rubrics/integrations
├── portfolio-site/         Day 22 — Next.js 16 + Tailwind portfolio site (Vercel-ready)
│   └── src/app/            hero · stats · featured projects · essay · contact
├── docs/                   Progress docs (Days 1–23), ship content, architecture decisions, iteration logs
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

# Days 4–6 — RAG ingestion, retrieval, cited answers, evals (offline, no API key)
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m gtm_kb.ingest      # -> 30 docs, 177 chunks (Chroma + BM25)
.venv/bin/python -m pytest -q          # -> 84 passed
.venv/bin/python evals/run_eval.py     # -> evals/report.md (retrieval metrics)
streamlit run app.py                   # -> UI, demo mode needs no key

# Days 8–13 — flagship outbound agent (agents + critique + eval harness)
cd ../gtm-outbound-agent
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/python -m pytest -q          # -> 190 passed

# Days 15–18 — batch mode + dashboard + full eval harness + iteration cycle
.venv/bin/python -m gtm_outbound batch run --file data/sample_companies.csv
streamlit run dashboard.py             # -> live run monitoring + cost dashboard
.venv/bin/python evals/run_full_eval.py  # -> eval metrics (enrichment, ICP, email, would-send)

# Days 19–20 — open-source eval rubrics package (framework-agnostic)
cd ../gtm-agent-evals
python -m venv .venv && .venv/bin/pip install -e ".[dev]"
PYTHONPATH=.:$PYTHONPATH python -m pytest -q  # -> 35 passed (22 rubric + 13 integration)
python examples/langchain_integration.py      # -> ICP/Email/Persona evaluators
python examples/external_dataset_evals.py     # -> gold dataset testing + report
streamlit run examples/streamlit_app.py       # -> interactive rubric explorer

# Day 22 — portfolio site (Next.js 16 + Tailwind)
cd ../portfolio-site
npm install
npm run build                          # -> production build passes (static prerender)
npm run dev                            # -> http://localhost:3000
```

## Highlights so far

- **Prompt-injection-aware extraction.** Untrusted source text is fenced in explicit markers in the *user* turn only (never the system prompt), with a system instruction that fenced text is data, not instructions.
- **Closed, strict schemas.** JSON schemas are recursively closed (`additionalProperties: false` everywhere) so the model can't invent fields; enums are validated offline.
- **Honest pricing.** A promo-aware pricing table computes real cost per call and raises on unknown models rather than silently reporting `$0`.
- **A corpus built for grounding.** 30 cross-linked docs share one canonical fact sheet (ICP, competitors, pricing, locked metrics), enforced by an integrity check — the substrate for RAG and hallucination detection.

## Tech

**Stack:** Python 3.10+ · **Groq** (Mixtral, primary) + Anthropic Claude (fallback) · Pydantic v2 · pytest · Streamlit · SQLite/Postgres · Chroma + BM25 · Langfuse (optional)

**LLM Provider:** Groq (default, ~11× cheaper + ~50ms latency) with automatic Anthropic fallback. All modules support both APIs via unified provider abstraction (see [GROQ_MIGRATION.md](docs/GROQ_MIGRATION.md)).

---

*Portfolio sprint. Northstar Analytics is fictional. Built by Dheeraj Pranav.*
