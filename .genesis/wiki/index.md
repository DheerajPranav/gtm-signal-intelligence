# Wiki Index — gtm-signal-intelligence

The project knowledge base. Same schema as the agentic-swe-kit wiki: concept pages in `concepts/`,
each with frontmatter and ≥2 `[[wikilinks]]`. The L3 RESEARCH loop writes here; G0 reads here first.

> **Read this file before any milestone (G0 step 1).** Pick candidate pages by name-matching the
> milestone's nouns, then drill in. The wiki is what prevents rebuilding work that already exists.

## Entities (the things this system has)
- **Northstar Analytics** — the fictional B2B RevOps analytics company the whole sprint sells for. Canonical facts (ICP, competitors, pricing, leadership) live in `gtm-knowledge-base/data/northstar/`. Single source of truth for all synthetic content.
- **CompanyDescription** — Day 1 structured record (Pydantic) returned by the `describe` CLI via forced tool use.
- **Lead** — Day 2 structured record (Pydantic): seniority/department/likely-buying-role enums + per-field confidence & evidence.
- **KB corpus** — Day 3: 30 markdown docs (7 product, 10 sales, 4 case studies, 5 marketing, 4 company) that Day 4+ RAG ingests.

## Concepts (how it works)
- **Structured output via tool use** — never string-parse an LLM; force a tool whose schema is derived from a Pydantic model, then validate. Applies to Day 1 (CompanyDescription) and Day 2 (Lead).
- **Cost tracking from call one** — `cost.py` context manager writes one JSONL line per billed call (tokens, cost, latency, stop_reason), flushed in `finally`. Pricing is promo-aware and raises on unknown models.
- **Untrusted GTM text** — lead/company blurbs are attacker-controlled; they ride as user content only and must never steer tool choice or policy.
- **Eval-or-it-doesn't-count** — no milestone ships without a computed gate. Where a live key is absent, deterministic mocks stand in so the pipeline is still verified, and no output is invented.

## Sources (research distilled by L3)
- **gtm_ai_sprint_master_plan.md** (repo root) — the 28-day plan; source of truth for scope, DoD, and Northstar facts. | filed 2026-07-22

## Seeded from agentic-swe-kit
Relevant global concept pages for this project's phases (pointers only — read on demand):
<!-- - $AGENTIC_SWE_WIKI_ROOT/clean-architecture/concepts/<Page>.md — when deciding boundaries -->
