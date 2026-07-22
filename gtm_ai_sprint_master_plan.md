# GTM AI Engineering Sprint: 4-Week Master Plan

**Owner:** Dheeraj (KD)
**Duration:** 28 days
**Time budget:** 20 to 25 hours per week (approx 85 to 100 hours total)
**Target roles:** GTM AI Engineering, AI in Sales/Marketing, Forward-Deployed AI Engineer

---

## How to use this document with Claude Code

1. At the start of every coding session, share this file as system context so Claude Code knows the overall arc, tech stack, quality bar, and today's specific goals.
2. Point Claude Code to the current day section. Ask it to help execute that day's tasks only.
3. At the end of each day, append a progress log entry (template at the bottom) so tomorrow's session has continuity.
4. When in doubt, prefer shipping over polish. The Definition of Done for each day is the contract.

---

## The North Star

By end of Day 28, three pinned GitHub repos plus a portfolio site:

1. **`gtm-knowledge-base`** (Foundation): deployed hybrid-retrieval RAG over synthetic B2B SaaS docs, with real evals.
2. **`gtm-outbound-agent`** (Flagship): multi-agent account research and personalized outbound system with dashboard, batch mode, guardrails, evals, and observability.
3. **`gtm-agent-evals`** (Differentiator): open-source LLM-judge rubric kit for GTM agents.
4. **Portfolio site + CV + LinkedIn overhaul + 2 blog posts + 2 Looms + 20+ warm outreaches sent.**

---

## Non-negotiables (the quality bar)

Every repo must have:

- Clear README with problem, architecture diagram, demo GIF or Loom, eval results table, cost per run, run instructions, tech stack.
- An eval harness with a golden dataset. No exceptions. If it wasn't evaluated, it doesn't count.
- Cost and latency logging (tokens, dollars, p50, p95) baked in from Day 1.
- Observability via Langfuse from the first LLM call.
- Pydantic everywhere for data models.
- Reproducible run (a single `make demo` or `python -m ...` command).

Personal cadence:

- Ship a commit every day, even if small.
- Post on LinkedIn at least twice per week (kickoff + ship posts each week).
- Track time honestly in the progress log so you can debug your own pace.

---

## The fictional company (context for the KB and flagship)

**Northstar Analytics** is a fictional B2B RevOps analytics platform selling to Series B to Series D SaaS companies (200 to 2000 employees). Positioning: "The RevOps analytics layer for teams outgrowing spreadsheets and BI tools not built for revenue data."

**ICP:**
- Firmographic: B2B SaaS, 200 to 2000 employees, $20M to $200M ARR, Series B to D
- Technographic: Salesforce or HubSpot, Snowflake or BigQuery, using Looker/Tableau/Mode or spreadsheets
- Behavioral: hired a RevOps leader in last 12 months, published RevOps job openings, mentioned "pipeline hygiene" or "forecast accuracy" in earnings or blogs
- Buyer personas: VP of RevOps, Head of Sales Operations, CRO, VP of Sales

**Competitors (for battle cards):** Clari, Gong Forecast, Mosaic, Pigment

---

## Locked tech stack (do not re-litigate mid-sprint)

- **Language:** Python 3.11+
- **LLM:** Anthropic Claude Sonnet (default), Haiku (cheap steps), Opus (hard reasoning only)
- **Embeddings:** Voyage `voyage-3` or OpenAI `text-embedding-3-large` (pick one, stay with it)
- **Vector DB:** Chroma (local dev), Qdrant Cloud free tier (deployment)
- **RAG framework:** LlamaIndex (or framework-free where cleaner)
- **Agents:** PydanticAI or plain Anthropic SDK with tool use
- **Data validation:** Pydantic v2
- **Backend:** FastAPI
- **UI:** Streamlit (fast to ship), Next.js for portfolio site only
- **DB:** SQLite (dev), Postgres via Neon (prod)
- **Observability:** Langfuse (free tier)
- **Deploy:** Modal (backend), Streamlit Cloud (dashboards), Vercel (portfolio site)
- **Search tools:** Tavily API (free tier) or Anthropic web search
- **CI:** GitHub Actions (lint, test, eval smoke)

---

## Repo layout convention (use across all projects)

```
project-name/
├── README.md
├── pyproject.toml
├── .env.example
├── src/
│   └── project_name/
│       ├── __init__.py
│       ├── models.py         # Pydantic models
│       ├── prompts/          # versioned prompts (v1/, v2/)
│       ├── agents/           # agent implementations
│       ├── tools/            # tools available to agents
│       ├── evals/            # eval harness + datasets
│       └── observability.py  # Langfuse wiring
├── tests/
├── notebooks/                # exploratory work
├── data/                     # synthetic data, eval sets
├── docs/                     # architecture, blog draft
└── scripts/                  # entrypoints (run, eval, deploy)
```

---

# WEEK 1: Foundations + Knowledge Base

**Weekly target:** 22 hours
**Weekly ship:** GTM Knowledge Base deployed with evals + a warm-up CLI repo.

---

## Day 1 (Monday) — Anthropic SDK primitives + CLI warmup

**Time budget:** 3 hours

### Theory to internalize before coding (30 min)

Read/skim:
1. Anthropic Messages API overview: message roles, system prompt, sampling params.
2. Token counting basics and pricing per model.
3. Structured output via tool use (function calling) vs prompt-based JSON.
4. What "temperature" actually does (deterministic vs exploratory sampling).

Mental model to lock in: **an LLM call is a pure function `(system, messages, params) → response + usage`**. Everything else you build is engineering around that primitive.

### Build

Create `gtm-cli-warmup`. A CLI tool that takes a company name and outputs a 3-sentence description.

Requirements:
- Uses Anthropic SDK, Sonnet model.
- Reads API key from `.env`.
- Prints token usage and dollar cost per call.
- Wraps calls with a `cost_tracker` context manager that logs every call to a local JSONL file.
- Includes one Pydantic model `CompanyDescription` with fields `name`, `one_liner`, `industry`, `size_guess`.
- Uses tool-use to return structured output, not string parsing.

### Definition of Done

- [ ] Repo initialized with pyproject.toml, .env.example, README with usage.
- [ ] `python -m gtm_cli_warmup describe "Notion"` returns valid `CompanyDescription`.
- [ ] Every call logs tokens and cost to `runs.jsonl`.
- [ ] README shows a sample run with output.
- [ ] Committed and pushed.

### LinkedIn post (kickoff)

Draft and publish: "Starting a 4-week sprint to go deep on GTM AI Engineering. Building in public. Here's the plan: [1-line summary of the 4 projects]. Follow along."

### Commit template

```
day-01: warmup CLI with cost tracking and structured output

- Anthropic SDK basic setup
- Pydantic model for CompanyDescription
- Tool-use for structured output
- Cost tracker context manager writing to runs.jsonl
```

---

## Day 2 (Tuesday) — Structured outputs + Lead Extractor notebook

**Time budget:** 3 hours

### Theory (20 min)

- Pydantic v2 basics: `BaseModel`, `Field`, validators, `model_dump`.
- Tool use in Anthropic SDK: defining tools, forcing tool use, handling the response.
- Difference between JSON mode, tool use, and structured output libraries (Instructor, PydanticAI).

### Build

Inside a new folder `notebooks/lead_extractor/` (still in `gtm-cli-warmup` repo for now, or a separate `gtm-lead-extractor` repo if you want the credit):

- Pydantic `Lead` model: `full_name`, `title`, `seniority` (enum: IC, Manager, Director, VP, C-suite), `department` (enum), `likely_buying_role` (economic_buyer, champion, user, blocker, unknown), `confidence` per field, `evidence` per field.
- Function `extract_lead(text: str) -> Lead` using tool use.
- Test inputs: 3 LinkedIn "About" blurbs, 2 email signatures, 1 conference bio, all synthetic.
- Show extractions in the notebook with confidence and evidence.

### Definition of Done

- [ ] Notebook runs end-to-end.
- [ ] 6 test inputs extracted correctly (or failures analyzed in a markdown cell).
- [ ] Confidence and evidence populated per field.
- [ ] Committed with notebook rendered on GitHub.

### Commit template

```
day-02: structured lead extraction with confidence and evidence

- Pydantic Lead model with enums
- Tool-use based extractor
- 6 synthetic test inputs
```

---

## Day 3 (Wednesday) — Northstar Analytics data generation

**Time budget:** 3 hours

### Theory (15 min)

- Chunking strategies for RAG: fixed-size, semantic, section-based, hierarchical.
- Why hybrid search beats vector-only: recall vs precision, keyword vs semantic.

### Build

Create the repo `gtm-knowledge-base`. Inside `data/northstar/`, generate 30 markdown documents by prompting Claude:

**Product docs (7):**
- `product/overview.md`
- `product/module-pipeline-analytics.md`
- `product/module-forecast-accuracy.md`
- `product/module-rep-productivity.md`
- `product/integrations.md`
- `product/security.md`
- `product/pricing.md`

**Sales enablement (10):**
- `sales/icp-definition.md` (rich, this is critical for the flagship)
- `sales/positioning.md`
- `sales/discovery-questions.md`
- `sales/objection-handling.md`
- `sales/sales-playbook.md`
- `sales/battlecard-clari.md`
- `sales/battlecard-gong.md`
- `sales/battlecard-mosaic.md`
- `sales/battlecard-pigment.md`
- `sales/faq.md`

**Case studies (4):**
- `case-studies/series-c-fintech.md`
- `case-studies/series-b-devtools.md`
- `case-studies/series-d-vertical-saas.md`
- `case-studies/series-c-marketing-tech.md`

**Marketing (5):**
- `marketing/homepage.md`
- `marketing/for-vp-revops.md`
- `marketing/for-vp-sales.md`
- `marketing/blog-forecast-accuracy.md`
- `marketing/blog-pipeline-hygiene.md`

**Company (4):**
- `company/about.md`
- `company/leadership.md`
- `company/customer-list.md`
- `company/analyst-quotes.md`

Each doc should be 300 to 800 words, internally consistent, with realistic sections and headings.

### Definition of Done

- [ ] 30 markdown files committed under `data/northstar/`.
- [ ] Internally consistent (same ICP, same competitors, same pricing across docs).
- [ ] ICP doc has explicit firmographic, technographic, and behavioral signals sections.
- [ ] `data/northstar/README.md` explains the fictional company for anyone browsing the repo.

### Commit template

```
day-03: Northstar Analytics synthetic knowledge corpus

- 30 markdown docs across product, sales, case studies, marketing, company
- Internally consistent ICP and competitive positioning
```

---

## Day 4 (Thursday) — RAG stack setup and ingestion

**Time budget:** 2 hours

### Theory (15 min)

- Embedding models: dimensions, context windows, cost per 1M tokens.
- Vector DB basics: index types, cosine vs dot product, filters.
- Reciprocal Rank Fusion for combining rankings.

### Build

In `gtm-knowledge-base`:
- Install and configure LlamaIndex + Chroma + Anthropic + Voyage (or OpenAI) embeddings.
- Ingestion pipeline that:
  - Loads all 30 docs.
  - Section-based chunker (split by markdown H2 headings, fallback to 800 tokens with 100 overlap).
  - Extracts metadata: `doc_type`, `doc_title`, `section_title`, `source_path`.
  - Embeds and stores in Chroma with metadata.
  - Also builds a BM25 index over the same chunks.
- Simple `query(question: str, top_k: int)` function returning chunks (no LLM yet).

### Definition of Done

- [ ] `python -m gtm_kb.ingest` runs cleanly.
- [ ] Chroma DB persisted locally.
- [ ] BM25 index persisted locally.
- [ ] Quick sanity check: query "What competitors does Northstar have?" returns relevant chunks.

### Commit template

```
day-04: RAG ingestion with section-based chunking, Chroma, and BM25

- Metadata-rich chunks
- Persisted vector and keyword indexes
- Sanity query working
```

---

## Day 5 (Saturday) — Hybrid retrieval, reranking, answer generation, UI

**Time budget:** 5 hours

### Theory (20 min)

- LLM-as-reranker: pass top-k candidates to a cheaper model, ask it to rerank.
- Citation-anchored answers: why grounding matters and how to prompt for it.

### Build

- Hybrid retriever: run BM25 and vector search in parallel, fuse via RRF, return top 20.
- Reranker: prompt Claude Haiku to rerank top 20 down to top 5 based on the actual question.
- Answer generator: Claude Sonnet, given question + top 5 chunks, produces an answer WITH inline citations `[source: doc_title#section]`.
- Streamlit UI with:
  - Question input box.
  - Answer display with inline citations linked to expandable source chunks.
  - Retrieved chunks panel (for debugging).
  - Cost and latency panel per query.

### Definition of Done

- [ ] `streamlit run app.py` shows the UI locally.
- [ ] Every answer includes at least one citation.
- [ ] Cost per query displayed.
- [ ] 5 example queries produce sensible answers.

### Commit template

```
day-05: hybrid retrieval + reranking + cited answers + Streamlit UI

- RRF-fused BM25 + vector search
- Haiku reranker
- Sonnet answer generation with mandatory citations
- Streamlit UI with debug and cost panels
```

---

## Day 6 (Sunday morning) — Golden eval set and eval harness

**Time budget:** 4 hours

### Theory (20 min)

- LLM-as-judge basics: rubric design, pairwise vs pointwise, calibration.
- Retrieval metrics: precision@k, recall@k, MRR.
- Faithfulness vs completeness vs relevance.

### Build

- Create `evals/golden_qa.jsonl` with 35 questions:
  - 10 factoid ("What's the price of the Pipeline Analytics module?")
  - 8 comparison ("How does Northstar compare to Clari on forecast accuracy?")
  - 6 synthesis ("What's Northstar's positioning for a Series C fintech?")
  - 6 ICP-related ("Would a 100-person seed-stage company be a fit?")
  - 5 edge cases ("Does Northstar integrate with Excel?" when the answer is "not explicitly")
- Each entry: `question`, `expected_source_docs` (list), `expected_answer_traits` (list of things the answer must mention).
- Eval harness in `evals/run_eval.py`:
  - Retrieval P@5 (did the expected source appear in top 5).
  - Retrieval Recall@5.
  - Faithfulness (LLM-judge: does the answer only use info from cited chunks?).
  - Completeness (LLM-judge: does the answer cover the expected traits?).
  - Latency p50, p95.
  - Cost per query, avg.
- Output: markdown report `evals/report.md` with a results table.

### Definition of Done

- [ ] `python -m gtm_kb.evals.run` produces a full report.
- [ ] Baseline numbers logged.
- [ ] At least one iteration attempted (change chunking or prompt, re-run, log delta).

### Commit template

```
day-06: eval harness with retrieval, faithfulness, completeness, cost

- 35-question golden set across 5 categories
- LLM-judge for faithfulness and completeness
- Baseline report + one improvement iteration
```

---

## Day 7 (Sunday afternoon) — Deploy, Loom, LinkedIn ship

**Time budget:** 2 hours

### Build

- Deploy FastAPI backend on Modal or Railway.
- Deploy Streamlit UI on Streamlit Cloud.
- Add basic auth via query param secret or Streamlit's built-in auth.
- Update README with:
  - Hero section (what it is, live link).
  - Architecture diagram.
  - Eval results table.
  - Cost table (avg cost per query).
  - Local run instructions.
- Record 2-minute Loom: problem, live demo, cite an eval number, cost.

### Definition of Done

- [ ] Live URL working from a private browser window.
- [ ] README polished.
- [ ] Loom recorded and linked in README.
- [ ] LinkedIn ship post published with Loom + live link.

### LinkedIn post (ship)

Structure: "Week 1 shipped. Built [KB name] over synthetic B2B SaaS docs. Hybrid retrieval, Haiku reranker, Sonnet answers with citations. Eval results: [numbers]. Cost per query: $[X]. Loom: [link]. Live demo: [link]. Repo: [link]. Next week: the flagship."

### Commit template

```
day-07: deploy + README polish + Loom
```

---

# WEEK 2: Flagship Core Loop

**Weekly target:** 24 hours
**Weekly ship:** Working single-company end-to-end pipeline through all 5 agents.

---

## Day 8 (Monday) — Flagship system design + repo scaffold

**Time budget:** 3 hours

### Theory (30 min)

- Multi-agent orchestration patterns: sequential, parallel, hierarchical, event-driven.
- When to use one agent vs many (avoid over-engineering).
- Anthropic's "building effective agents" blog post (skim).

### Build

- Create `gtm-outbound-agent` repo with the repo layout convention.
- Draw architecture diagram in Excalidraw. Save to `docs/architecture.png`.
- Define Pydantic models in `models.py`:
  - `TargetCompany` (domain, name)
  - `CompanyProfile` (industry, sub_industry, size_band, funding_stage, tech_stack, recent_news, key_people, buying_signals)
  - `FitScore` (score, firmographic_score, technographic_score, behavioral_score, timing_score, reasoning)
  - `Persona` (title, department, pain_points, priorities, objections, buying_influence)
  - `EmailDraft` (persona_id, variant_id, subject, body, personalization_hooks)
  - `EmailEval` (personalization_score, relevance_score, cta_score, spam_risk, would_send, reasoning)
  - `AccountBrief` (target, profile, fit, personas, emails, evals, cost, latency, timestamp)
  - `RunTrace` (run_id, per_agent_traces, total_cost, total_latency)
- Set up SQLite with SQLAlchemy or SQLModel.
- Wire Langfuse: every LLM call decorated to trace.
- Empty stubs for the 5 agents: `research_agent.py`, `scoring_agent.py`, `persona_agent.py`, `writing_agent.py`, `critique_agent.py`.

### Definition of Done

- [ ] Repo scaffolded and pushed.
- [ ] Architecture diagram in `docs/`.
- [ ] All Pydantic models defined.
- [ ] SQLite migrations run.
- [ ] Langfuse dashboard shows a test event.

### Commit template

```
day-08: flagship scaffold + models + observability

- Multi-agent architecture doc
- Pydantic models for full pipeline
- SQLite + Langfuse wired
```

---

## Day 9 (Tuesday) — Research Agent (Enrichment)

**Time budget:** 3 hours

### Theory (20 min)

- Agentic search patterns: query decomposition, iterative refinement, stopping conditions.
- Tavily vs Anthropic web search vs SerpAPI: latency, cost, quality tradeoffs.

### Build

- Implement `research_agent.enrich(domain: str) -> CompanyProfile`.
- Tools available to agent: `web_search`, `fetch_page`, `news_search`.
- Prompt: given a domain, plan queries, execute in a loop with max 8 tool calls, synthesize CompanyProfile.
- Small eval set: `evals/enrichment_gold.jsonl` with 10 real public companies and hand-curated ground truth for size, industry, funding.
- Metrics: field accuracy, hallucination rate (LLM-judge checks if each fact appears in cited sources).

### Definition of Done

- [ ] `enrich("linear.app")` returns a valid, mostly-correct CompanyProfile in under 60s.
- [ ] Eval reports at least 70% field accuracy on 10 test companies.
- [ ] Every field has a `source_url` alongside it.

### Commit template

```
day-09: research agent with tool-use enrichment

- Multi-tool agent (search, fetch, news)
- CompanyProfile with sourced fields
- 10-company enrichment eval
```

---

## Day 10 (Wednesday) — Scoring Agent (ICP fit)

**Time budget:** 3 hours

### Theory (10 min)

- Rubric-based scoring vs freeform: reproducibility tradeoffs.
- How to prompt for calibrated scores (anchor examples).

### Build

- Implement `scoring_agent.score(profile: CompanyProfile) -> FitScore`.
- Pull ICP definition by querying the Knowledge Base (`gtm-knowledge-base` KB query endpoint or local RAG import).
- Prompt: given ICP + profile, score each of 4 dimensions with reasoning and cited signals.
- Eval set: 15 hand-labeled companies (7 strong fit, 4 weak, 4 not fit).
- Metric: Spearman rank correlation with your labels + confusion matrix on 3-band classification.

### Definition of Done

- [ ] `score(profile)` returns valid FitScore with per-dimension reasoning.
- [ ] Rank correlation > 0.6 on 15 labeled companies.
- [ ] Reasoning cites specific signals from the profile.

### Commit template

```
day-10: scoring agent with KB-grounded ICP rubric

- 4-dimension scoring with per-dim reasoning
- 15-company labeled eval
```

---

## Day 11 (Thursday) — Persona Agent

**Time budget:** 2 hours

### Build

- Implement `persona_agent.build_personas(profile: CompanyProfile) -> list[Persona]`.
- For each target company, identify 3 personas most likely to be economic buyers or champions for Northstar.
- For each persona, generate a stakeholder card: likely pain points (drawn from Northstar's positioning docs via KB), priorities, common objections, buying influence tier.
- Prompt strategy: pull persona-relevant sections from KB, ground the card in real Northstar positioning.

### Definition of Done

- [ ] Returns 3 personas with fully populated stakeholder cards.
- [ ] Cards vary meaningfully by company (a fintech vs a devtools company get different pain framing).
- [ ] All persona cards reference Northstar language from the KB.

### Commit template

```
day-11: persona agent grounded in KB positioning

- 3 personas per company
- Stakeholder cards with pains, priorities, objections
```

---

## Day 12 (Saturday) — Writing Agent + async fan-out

**Time budget:** 5 hours

### Theory (20 min)

- Async patterns in Python: `asyncio.gather`, semaphores for rate limiting.
- Prompt structure for personalized cold outbound: hook, relevance, value, CTA.

### Build

- Implement `writing_agent.draft_emails(profile, persona) -> list[EmailDraft]` producing 3 variants per persona.
- Variants should differ in angle: (1) pain-led, (2) trigger-event-led (using recent news from profile), (3) peer proof (using case study from KB).
- Each variant: subject (under 60 chars), body (under 120 words), 3 personalization hooks cited from profile.
- Async fan-out: personas processed concurrently, variants within a persona concurrent, with a semaphore of 5 concurrent LLM calls to avoid rate limits.
- Log every LLM call to Langfuse with tags.

### Definition of Done

- [ ] End-to-end: `run_company("linear.app")` produces 3 personas x 3 variants = 9 emails.
- [ ] Total wall-clock time under 90 seconds.
- [ ] Personalization hooks all traceable to profile or KB.

### Commit template

```
day-12: writing agent with async fan-out + 3 angles per persona

- Pain-led, trigger-led, peer-proof variants
- 9 personalized emails per company in < 90s
```

---

## Day 13 (Saturday eve to Sunday) — Critique Agent + Account Brief

**Time budget:** 5 hours

### Theory (15 min)

- LLM-judge design: rubric anchors, calibration set, avoiding sycophancy.
- Report generation with LLMs: sections, tone, length control.

### Build

- Implement `critique_agent.evaluate(email: EmailDraft, persona: Persona, profile: CompanyProfile) -> EmailEval`.
- Rubric:
  - Personalization (0 to 5): does it reference something specific and non-obvious?
  - Persona relevance (0 to 5): does the pain framing match the persona's actual concerns?
  - CTA clarity (0 to 5): is the ask specific, low-friction, and time-bound?
  - Spam risk (0 to 5, inverted): would this trip filters or feel automated?
  - Would-send (bool): would a discerning SDR actually send this?
- Assemble `AccountBrief` as a markdown document with sections: Company Summary, ICP Fit, Personas, Emails (per persona, with eval scores inline), Cost and Latency.

### Definition of Done

- [ ] `run_company("linear.app")` produces a complete AccountBrief.md saved to `runs/`.
- [ ] Brief opens cleanly on GitHub as a rendered markdown doc.
- [ ] Would-send pass rate reported at the top.

### Commit template

```
day-13: critique agent + account brief assembly

- 5-dim rubric with would-send binary
- Complete markdown brief per run
- Cost and latency reported
```

---

## Day 14 (Sunday) — Publish KB blog post + mid-sprint check-in

**Time budget:** 3 hours

### Build

- Write and publish the Week 1 blog post (2000 words) on Substack (NeuroTusks) or Medium:
  - Problem framing.
  - Architecture with diagram.
  - Design choices (why hybrid, why LlamaIndex, why Chroma).
  - Eval methodology and results.
  - Cost analysis.
  - Surprises and next steps.
- Post LinkedIn mid-sprint update: "Halfway through the sprint. KB shipped last week. Flagship's core loop is working today. Here's an early screenshot. Full ship next Sunday."

### Sign-off:

"Stay curious, stay disciplined. Dheeraj (KD)."

### Definition of Done

- [ ] Blog post published.
- [ ] LinkedIn post published.
- [ ] Flagship repo has a working end-to-end demo committed.

### Commit template

```
day-14: mid-sprint milestone

- Week 1 blog post live
- Flagship core loop demo committed
```

---

# WEEK 3: Flagship Polish, Batch, Deploy

**Weekly target:** 24 hours
**Weekly ship:** Flagship deployed with dashboard, batch mode, full evals, guardrails.

---

## Day 15 (Monday) — Batch mode + failure isolation

**Time budget:** 3 hours

### Theory (15 min)

- Retry patterns: exponential backoff, jitter, max attempts, circuit breakers.
- Idempotent job design.

### Build

- Implement batch runner: input a CSV or list of 10 domains, process each through the full pipeline concurrently (with a semaphore of 3 concurrent companies to respect rate limits).
- Failure isolation: one company failing doesn't kill the batch. Partial results persisted.
- Resume from checkpoint: `run_batch --resume run_id_xxx` picks up where it stopped.
- Store every run in SQLite.

### Definition of Done

- [ ] Batch of 10 companies completes in under 15 minutes.
- [ ] Killing the process mid-run and resuming works.
- [ ] Failed companies logged with error traces, batch continues.

### Commit template

```
day-15: batch mode with failure isolation and resume

- Concurrent processing with semaphore
- Checkpoint-based resume
- Per-company error isolation
```

---

## Day 16 (Tuesday) — Dashboard v1

**Time budget:** 3 hours

### Build

- Streamlit dashboard with these views:
  - Home: run history table, run a new batch button.
  - Live run view: progress bars per company, per-agent status.
  - Company drill-down: profile, fit score, personas, emails with eval scores, raw agent traces.
  - Cost dashboard: per-run cost, per-company cost, per-agent cost breakdown, cumulative sprint cost.
  - Eval dashboard: latest eval scores over time.

### Definition of Done

- [ ] All 5 views load without errors.
- [ ] A completed batch is fully explorable.
- [ ] Cost dashboard shows real numbers from SQLite.

### Commit template

```
day-16: Streamlit dashboard with 5 views

- Run history, live progress, drill-down, cost, eval
```

---

## Day 17 (Wednesday) — Full eval harness

**Time budget:** 3 hours

### Build

- Consolidate all evals into `evals/run_full_eval.py`:
  - Enrichment accuracy on 10 test companies.
  - ICP correlation on 15 labeled companies.
  - Email quality: run pipeline on 15 companies, judge every email with the critique rubric.
  - End-to-end would-send pass rate: what % of generated emails pass the would-send bar.
- Output: `evals/report.md` with a headline table (all metrics + baselines) and per-metric breakdowns.
- Log to Langfuse as a labeled experiment run.

### Definition of Done

- [ ] Full eval runs end-to-end in one command.
- [ ] Report generated with all metrics and baselines.
- [ ] Headline numbers copyable into README and CV.

### Commit template

```
day-17: full eval harness with report generation

- Enrichment, ICP, email quality, end-to-end pass rate
- Single-command reproducible report
```

---

## Day 18 (Thursday) — First iteration cycle

**Time budget:** 2 hours

### Build

- Run full eval, identify the 3 weakest metrics.
- For each: form a hypothesis, make one change (prompt, chunking, tool, retry logic), re-run.
- Log the before/after in `docs/iteration-log.md`.

### Definition of Done

- [ ] 3 hypotheses tested.
- [ ] Iteration log updated with deltas.
- [ ] At least one metric improved.

### Commit template

```
day-18: iteration cycle 1 with before/after

- 3 hypotheses tested
- Iteration log
```

---

## Day 19 (Saturday) — Second iteration + guardrails + prompt versioning

**Time budget:** 5 hours

### Build

- Second iteration cycle (same shape as Day 18).
- Guardrails:
  - Input validation: domain must resolve and return HTTP 200 before enrichment starts.
  - PII check: no personal emails, phone numbers, or home addresses in emails (regex + LLM check).
  - Output validation: every EmailDraft schema-validated before saving.
  - Refusal handling: if a persona pain would require making up a fact, agent must refuse and flag.
- Prompt versioning: move all prompts to `prompts/v1/*.md`, load by version, log version in Langfuse.
- Load test: run batch of 20 companies, capture p50 and p95 latency, note any rate limit hits.

### Definition of Done

- [ ] Iteration cycle 2 logged.
- [ ] All 4 guardrails implemented and tested.
- [ ] Prompts versioned.
- [ ] Load test results in `docs/load-test.md`.

### Commit template

```
day-19: guardrails, prompt versioning, load test

- 4 guardrails: input, PII, output, refusal
- Prompts moved to v1/ with version logging
- 20-company load test results
```

---

## Day 20 (Sunday morning) — Deploy flagship

**Time budget:** 4 hours

### Build

- Deploy backend on Modal (async batch workloads handle well).
- Deploy dashboard on Streamlit Cloud.
- Postgres on Neon (migrate from SQLite, keep both supported).
- Basic auth on the dashboard.
- Smoke test: run a 5-company batch on prod, verify everything works.

### Definition of Done

- [ ] Live URL for the dashboard.
- [ ] Prod smoke test batch completed successfully.
- [ ] Env vars documented in `.env.example`.
- [ ] Deploy instructions in `docs/deploy.md`.

### Commit template

```
day-20: prod deploy on Modal + Streamlit Cloud + Neon
```

---

## Day 21 (Sunday afternoon) — README polish + Loom + LinkedIn ship

**Time budget:** 4 hours

### Build

- Rewrite README as a product landing page:
  - Hero: what it is, why it exists, live link.
  - Demo GIF (record one with your dashboard).
  - Architecture diagram.
  - Eval results table (with baselines).
  - Cost table (avg cost per account, per email).
  - Tech stack.
  - Run instructions.
  - Credits.
- Record 5-minute Loom: problem, dashboard walkthrough with a live run, eval results, cost breakdown, architecture explanation.
- Draft flagship blog post outline (write it Day 23).
- Two LinkedIn posts: (a) flagship shipped with Loom + repo, (b) technical teaser for the blog.

### Sign-off:

"Stay curious, stay disciplined. Dheeraj (KD)."

### Definition of Done

- [ ] README polished.
- [ ] Loom recorded and linked.
- [ ] Two LinkedIn posts published.

### Commit template

```
day-21: flagship ship + README + Loom
```

---

# WEEK 4: Portfolio, Differentiator, Launch

**Weekly target:** 22 hours
**Weekly ship:** Portfolio site, CV, differentiator repo, launch content, cold outreach sent.

---

## Day 22 (Monday) — Portfolio site

**Time budget:** 3 hours

### Build

- Next.js on Vercel. Use a nice starter (e.g., Vercel template, Tailwind UI blocks, or one of the DevDreaming free templates).
- Sections:
  - Hero: name, one-liner ("GTM AI Engineer building auditable agents"), links to GitHub, LinkedIn, Substack.
  - Featured projects: KB, Flagship, Eval Kit (Day 25 to 26), CLI (mentioned smaller). Each with screenshot, one-liner, links.
  - "How I think about GTM AI" essay embed or link.
  - Contact: email + LinkedIn CTA.

### Definition of Done

- [ ] Site live on a custom subdomain or Vercel URL.
- [ ] All project links working.
- [ ] Mobile responsive.

### Commit template

```
day-22: portfolio site live on Vercel
```

---

## Day 23 (Tuesday) — Flagship blog post

**Time budget:** 3 hours

### Build

Publish 3000-word blog post on NeuroTusks (Substack):
- Problem framing (why GTM AI, why account research, why outbound).
- Architecture deep dive (agent by agent, with diagram).
- Design choices (why 5 agents, why async fan-out, why Streamlit for dashboard, why Modal).
- Eval methodology and results (headline table).
- Cost economics (cost per account, per email, unit economics).
- Failure modes and iteration log summary.
- What production hardening would need.
- What you'd change if starting over.

### Sign-off:

"Stay curious, stay disciplined. Dheeraj (KD)."

### Definition of Done

- [ ] Blog post published.
- [ ] Linked from portfolio site and flagship README.
- [ ] LinkedIn post announcing the blog.

### Commit template

```
day-23: flagship blog post published
```

---

## Day 24 (Wednesday) — CV + LinkedIn overhaul

**Time budget:** 3 hours

### Build

- CV rewrite. One page. For each of the 3 flagship projects, use the pattern:
  - "Built [X], a [system type] that [does Y]. [Concrete result with number]. Deployed on [Z]. [Cost or latency metric]."
- Add a "GTM AI Portfolio Sprint" section at the top with the 3 headline projects and portfolio link.
- LinkedIn:
  - Headline: "GTM AI Engineer. Building auditable, evaluated agents for sales and marketing workflows."
  - About: reframe with the sprint story and current focus.
  - Featured: pin portfolio site, flagship Loom, flagship blog post.
  - Experience: add "GTM AI Portfolio Sprint (self-directed, 4 weeks)" bullet under 2026 experience.

### Definition of Done

- [ ] CV PDF committed to `portfolio-site/public/cv.pdf` and linked.
- [ ] LinkedIn profile fully updated.
- [ ] Featured section pinned.

### Commit template

```
day-24: CV rewrite + LinkedIn overhaul
```

---

## Day 25 (Thursday) — Differentiator: package the eval kit

**Time budget:** 2.5 hours

### Build

Create repo `gtm-agent-evals`:
- Extract LLM-judge rubrics from flagship: email quality (5-dim), ICP fit (4-dim), enrichment quality (accuracy + hallucination).
- For each rubric:
  - Prompt in `prompts/`.
  - Pydantic result model.
  - Example calls in a notebook.
  - 5 example good outputs and 5 example bad outputs per rubric.
  - Calibration notes: why anchors are set the way they are.
- Mini runner: `python -m gtm_evals run --rubric email_quality --input-file drafts.jsonl` produces scores.
- README positioned as "The eval kit for GTM agents I wish existed when I started."

### Definition of Done

- [ ] Repo published.
- [ ] All 3 rubrics with examples and calibration notes.
- [ ] Runnable mini-eval.
- [ ] README with clear framing.

### Commit template

```
day-25: gtm-agent-evals initial release

- 3 LLM-judge rubrics with examples and calibration
- Standalone runner
```

---

## Day 26 (Friday) — Eval kit polish + Twitter thread draft

**Time budget:** 2.5 hours

### Build

- Add a comparison notebook: apply the email_quality rubric to 5 hand-crafted "great cold emails" from the internet vs 5 obviously templated ones. Show the rubric distinguishes them.
- Add a `CONTRIBUTING.md` inviting rubric contributions.
- Draft Twitter/X launch thread (10 to 12 tweets):
  - 1: "I spent 4 weeks going deep on GTM AI. Shipped 3 projects. Here's what I learned."
  - 2 to 4: flagship walkthrough with screenshots.
  - 5 to 6: eval kit with the good vs bad email comparison.
  - 7 to 8: KB and RAG choices.
  - 9 to 10: cost economics.
  - 11: portfolio + Loom + repo links.
  - 12: what's next + CTA.

### Definition of Done

- [ ] Comparison notebook committed.
- [ ] CONTRIBUTING.md added.
- [ ] Twitter thread drafted in `docs/launch/twitter-thread.md`.

### Commit template

```
day-26: eval kit polish + launch thread draft
```

---

## Day 27 (Saturday) — Launch

**Time budget:** 5 hours

### Build

- Post Twitter/X thread.
- Post LinkedIn long-form: "4 weeks ago I decided to go deep on GTM AI Engineering. Here's everything I shipped and what I learned." Include Loom, portfolio, repos.
- Post on: r/MachineLearning "I built" thread, r/salesengineering, Show HN for flagship, relevant Discord communities (Latent Space, AI Engineer, MLOps).
- Send DMs to 3 to 5 people you respect in GTM AI, asking for a quick reaction.

### Sign-off (for Substack roundup post if you do one):

"Stay curious, stay disciplined. Dheeraj (KD)."

### Definition of Done

- [ ] Twitter thread live.
- [ ] LinkedIn long-form live.
- [ ] Posted in 3+ communities.
- [ ] 3+ personal DMs sent.

---

## Day 28 (Sunday) — Cold outreach + retrospective + rest

**Time budget:** 3 hours

### Build

- Identify 20 to 25 targets across:
  - Heads of AI at sales tools (Clay, Apollo, Outreach, Salesloft, Gong, Attio, Rippling, Ramp, Cargo).
  - GTM Engineering leads at fast-growing SaaS (Ramp, Rippling, Vercel, Linear, Anthropic, OpenAI GTM, Perplexity).
  - AI hiring managers you've seen posting relevant roles.
- For each: 4-line message referencing something specific about their company, linking your flagship Loom, offering to walk them through it.
- Track all outreach in a spreadsheet (name, company, role, sent date, response).
- Write a personal retrospective (1000 words, private or on NeuroTusks): what worked, what didn't, what you'd do differently, what surprised you.
- Then rest.

### Definition of Done

- [ ] 20+ personalized outreaches sent.
- [ ] Outreach tracker started.
- [ ] Retrospective written.

---

# Daily Progress Log Template

Append this to a `PROGRESS.md` in each repo (or a single sprint log if you prefer):

```markdown
## Day N (YYYY-MM-DD)

**Time spent:** X hours
**Planned tasks:** [pulled from the plan]
**What actually shipped:**
- [bullet]
- [bullet]

**Blockers or surprises:**
- [bullet]

**Metrics logged today:**
- [e.g. retrieval P@5: 0.82]
- [total tokens used today: X, cost: $Y]

**Tomorrow's first action:**
- [one specific thing]

**Confidence level (1 to 5) on hitting week's ship goal:**
- N

```

---

# Global reminders

- Spend under $50 total on API costs across 4 weeks. If you're trending higher, switch more steps to Haiku.
- Do not chase framework churn mid-sprint. Ship with what's committed here.
- Every Sunday, review the week's progress log. Adjust the coming week if slipping, don't grind blindly.
- Sleep. Tired code is bad code.

Stay curious, stay disciplined.
