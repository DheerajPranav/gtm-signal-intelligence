# GTM Signal Intelligence

> Turn raw GTM signals — company blurbs, lead bios, a knowledge base — into **structured, grounded, evaluated** revenue intelligence a RevOps/sales team could actually trust.

**GTM Signal Intelligence** is a case study in building GTM (go-to-market) AI you can trust. It turns unstructured signals — company blurbs, lead bios, a knowledge base — into structured, grounded, evaluated revenue intelligence, across four capabilities: structured extraction, retrieval-augmented generation, a multi-agent outbound system, and an open-source evaluation kit. Everything is grounded in one fixed, internally-consistent world — the fictional company **Northstar Analytics** — so every generated claim can be sourced and every capability can be measured.

## Engineering bar (non-negotiable)

- **If it wasn't evaluated, it doesn't count.** Every capability ships with a *computed* gate — a test or check that passes or fails, not a narrated "looks good."
- **Structured output via tool use only** — never string-parsing model text.
- **Cost, latency, and tokens logged from the first LLM call.** Total API spend is capped.
- **No fabricated model output.** Where no API key is present, pipelines are verified end-to-end with deterministic mocks, and nothing invented is presented as a real model result.
- **Honest data.** Northstar Analytics — its product, customers, leadership, metrics, and press — is entirely fictional and labelled as such throughout. No real person or company is represented.

## The system

Four capabilities, each shipped behind a **computed gate** — a test or check that passes or fails, not a narrated "looks good." **367 hermetic tests · $0.00 live API spend.**

**1. Multi-agent outbound engine** — *the flagship.* Research → score → persona → write → critique, chained into a deterministic Account Brief. Sourced company profiles (every field carries its URL, with a deterministic check against fabricated provenance), an ICP score computed in code, async email fan-out under one shared semaphore, and a deliberately skeptical LLM judge. **214 tests.** → [`gtm-outbound-agent/`](gtm-outbound-agent/)

**2. Hybrid-retrieval RAG knowledge base** — BM25 + vector retrieval via Reciprocal Rank Fusion, a reranker, and cited answers over a 30-doc internally-consistent corpus, with a 35-question golden eval set. **Computed baseline: 74% hit rate@5, 61% recall@5. 84 tests.** → [`gtm-knowledge-base/`](gtm-knowledge-base/)

**3. Open-source evaluation kit** *(MIT)* — framework-agnostic ICP / persona / email / critique rubrics with deterministic gates and a CLI runner. On a 5-great-vs-5-templated email test, the would-send gate cleanly separates them **5/5 vs 0/5**. **55 tests.** → [`gtm-agent-evals/`](gtm-agent-evals/)

**4. Structured-extraction primitives** — typed company/lead extraction via forced tool use (never string-parsing), recursively-closed strict schemas, real cost/latency/token logging from the first call. **14 tests.** → [`gtm-cli-warmup/`](gtm-cli-warmup/)

**Live:** portfolio at [dheerajpranav.github.io/gtm-signal-intelligence](https://dheerajpranav.github.io/gtm-signal-intelligence/). **Deploy configs** (Modal backend · Neon · Streamlit dashboard) in [`docs/DEPLOY.md`](docs/DEPLOY.md). Live model-quality metrics render `not measured` until an API key is supplied — never a fabricated number.

<details>
<summary><b>Build log</b> — how it came together, step by step</summary>

| # | Deliverable | Computed gate | Status |
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
| 22 | Portfolio site — Next.js 16 + Tailwind, hero/stats/projects/essay/contact, mobile-responsive | **live** → [dheerajpranav.github.io/gtm-signal-intelligence](https://dheerajpranav.github.io/gtm-signal-intelligence/) | ✅ deployed (GitHub Pages) |
| 23 | Flagship blog post — full technical deep-dive on the 5-agent honest eval loop | `docs/FLAGSHIP_BLOG_POST.md` | ✅ written (publish = user action) |
| 24 | CV (one-page PDF, honest metrics) + LinkedIn overhaul copy; CV linked from portfolio | `portfolio-site/public/cv.pdf` + `npm run build` | ✅ built (profile edit = user action) |
| 25 | Eval-kit differentiator — deterministic mini-eval CLI, good/bad fixtures, calibration notes | `pytest -q` → 51 pass; `gtm-evals run …` | ✅ |
| 26 | Eval-kit polish — great-vs-templated comparison notebook (rubric separates 5/5 vs 0/5) + Twitter launch thread | `pytest -q` → 55 pass; `docs/launch/twitter-thread.md` | ✅ |
| 27–28 | Launch + cold outreach + live prod deploy | drafts ready: `docs/launch/LAUNCH_CHECKLIST.md`, `docs/DEPLOY.md`, Modal config | 🧩 materials drafted; execution = user actions |

</details>

**Where it stands:** all four capabilities are built, tested, and — for the portfolio — deployed. The remaining open items (recording a walkthrough, publishing write-ups, cold outreach, and the live backend deploy) need a live API key and outbound accounts; the drafts and configs are ready under [`docs/`](docs/).

### Results at a glance

| Capability | Tests | Result |
|------------|:-----:|--------|
| Multi-agent outbound engine | 214 | source-grounded pipeline + deterministic Account Brief |
| RAG knowledge base | 84 | 74% hit@5 · 61% recall@5 (35 golden questions) |
| Evaluation kit | 55 | would-send gate separates 5/5 great vs 0/5 templated |
| Extraction primitives | 14 | typed output via forced tool use |
| **Total** | **367** | **100% passing · $0.00 live API spend** |

Every gate is verified offline — deterministic embeddings and injected fake LLM clients — so
all capability gates pass before any live API call, and unmeasured metrics render `not measured`.

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
PYTHONPATH=.:$PYTHONPATH python -m pytest -q  # -> 51 passed (22 rubric + 13 integration + 16 runner)
python -m gtm_agent_evals run --rubric email_quality --input-file examples/data/email_quality.jsonl  # -> 10/10 agreement
python examples/langchain_integration.py      # -> ICP/Email/Persona evaluators
python examples/external_dataset_evals.py     # -> gold dataset testing + report
streamlit run examples/streamlit_app.py       # -> interactive rubric explorer

# Day 22 — portfolio site (Next.js 16 + Tailwind)
cd ../portfolio-site
npm install
npm run build                          # -> production build passes (static prerender)
npm run dev                            # -> http://localhost:3000
```

## Engineering highlights

- **Prompt-injection-aware extraction.** Untrusted source text is fenced in explicit markers in the *user* turn only (never the system prompt), with a system instruction that fenced text is data, not instructions.
- **Closed, strict schemas.** JSON schemas are recursively closed (`additionalProperties: false` everywhere) so the model can't invent fields; enums are validated offline.
- **Honest pricing.** A promo-aware pricing table computes real cost per call and raises on unknown models rather than silently reporting `$0`.
- **A corpus built for grounding.** 30 cross-linked docs share one canonical fact sheet (ICP, competitors, pricing, locked metrics), enforced by an integrity check — the substrate for RAG and hallucination detection.

## Tech

**Stack:** Python 3.10+ · **Groq** (Mixtral, primary) + Anthropic Claude (fallback) · Pydantic v2 · pytest · Streamlit · SQLite/Postgres · Chroma + BM25 · Langfuse (optional)

**LLM Provider:** Groq (default, ~11× cheaper + ~50ms latency) with automatic Anthropic fallback. All modules support both APIs via unified provider abstraction (see [GROQ_MIGRATION.md](docs/GROQ_MIGRATION.md)).

---

*Built by Dheeraj Pranav. Northstar Analytics is fictional and labelled as such throughout — no real person or company is represented.*
