# Architecture

Two systems documented here: the **v1 pipeline** (Days 8–14) and the **v2 learning
loop** (Weeks 5–6) that wraps it. v1 treats every account as new. v2 adds memory so
the agent improves across batches.

---

## v1 — the account pipeline

```
domains ──▶ Research ──▶ Scoring ──▶ Persona ──┬──▶ Writing ──▶ Critique ──▶ AccountBrief
             (Sonnet)    (Haiku)     (Haiku)   │     (Sonnet)    (Haiku)
             web search  KB query              └── per persona, N variants each
```

| Stage | Model | Input → Output | Day |
|---|---|---|---|
| Research | Sonnet + web search | `domain` → `CompanyProfile` | 9 |
| Scoring | Haiku + KB query | `CompanyProfile` → `FitScore` | 10 |
| Persona | Haiku | `CompanyProfile` → `[Persona]` | 11 |
| Writing | Sonnet | `(Profile, Persona)` → `[EmailDraft]` | 12 |
| Critique | Haiku | `EmailDraft` → `EmailEval` | 13 |

Cheap models do bounded, rubric-shaped work (scoring, critique); expensive models do
open-ended generation (research synthesis, writing). Critique deliberately uses a
*different* model from writing — a writer grading its own output is not a check.

### Keying

`EmailDraft.variant_id` is unique run-wide and is the key for both `AccountBrief.emails`
and `AccountBrief.evals`. Keying emails by `persona_id` instead silently drops every
variant but the last per persona, and makes drafts un-joinable to their evals — this
was a real defect, now covered by `test_multiple_variants_per_persona_all_survive`.

---

## v2 — the learning loop

Three memory layers, one read path, one write path, one background job.

```
                    ┌──────────────── WRITE-TIME READ ────────────────┐
                    │                                                 │
   ┌────────────────┴─────┐  ┌──────────────────┐  ┌─────────────────┴──┐
   │ PROCEDURAL           │  │ EPISODIC         │  │ SEMANTIC           │
   │ playbook rules       │  │ past good emails │  │ account facts      │
   │ "trigger beats pain  │  │ + their scores   │  │ funding, people,   │
   │  for fintech VPs"    │  │                  │  │ last contact       │
   │ Postgres             │  │ Chroma + SQL     │  │ Postgres           │
   └────────────┬─────────┘  └────────┬─────────┘  └─────────┬──────────┘
                └─────────────────────┼──────────────────────┘
                                      ▼
                        ┌─────────────────────────┐
                        │  Memory Retrieval Router │
                        │  → MemoryRetrievalResult │
                        └────────────┬─────────────┘
                                     ▼
                        ┌─────────────────────────┐
                        │  Writing Agent           │
                        │  <applicable_rules>      │
                        │  <successful_examples>   │
                        │  <account_history>       │
                        └────────────┬─────────────┘
                                     ▼
                        ┌─────────────────────────┐
                        │  Critique Agent          │
                        └────────────┬─────────────┘
                                     ▼
                        ┌─────────────────────────┐
                        │  decide_memory_write()   │  ← thresholds, in models.py
                        └────────────┬─────────────┘
                                     ▼
              episodic (if good) · negative (if bad) · semantic (always)
                                     │
                                     ▼
                        ┌─────────────────────────┐
                        │  Nightly Consolidation   │
                        │  GROUP BY segment,       │
                        │  n>=10 → synthesize rule │
                        └─────────────────────────┘
                                     │
                                     └──▶ updates PROCEDURAL, closing the loop
```

### Why each layer uses the store it does

| Layer | Store | Access pattern that decides it |
|---|---|---|
| Semantic | Postgres | Point lookup by `account_id`; supersession chains; staleness sort on `observed_at` |
| Procedural | Postgres | Lookup by `segment_key`; small table; needs update-in-place and retirement |
| Episodic — vectors | Chroma | "Find emails semantically like this one" at write-time |
| Episodic — metadata | Postgres | Consolidation does `GROUP BY (industry, persona, angle)` with `n>=10`. That is an aggregation, not a similarity search — a vector store answers it badly |

Episodic is deliberately **split across both**. The embedding answers "what looks like
this?"; the SQL row answers "what worked for this segment, and how often?"

### Write policy

`decide_memory_write()` in `models.py` is the single source of the thresholds:

- **Episodic** ← `personalization >= 4` AND `relevance >= 4` AND `spam_risk <= 2`.
  Admitting mediocre drafts would teach the writer to reproduce mediocrity.
- **Negative patterns** ← `would_send == False` AND any dimension `<= 2`. Kept in a
  separate index so the writer can be warned off failure shapes.
- **Semantic** ← always. Account facts are worth updating regardless of email quality.

Thresholds live in code, not in a prompt or a comment, so the writing agent, the eval
harness, and the consolidation job cannot drift apart on what "good" means.

### Staleness

`SemanticFact.age_days()` backs the >60-day rule: facts older than that must be flagged
before the writer relies on them. `superseded_by` points at another `fact_id` — facts are
never overwritten, so the account's history stays auditable.

---

## Observability

Every agent call is wrapped by `observability.trace_agent_call()`, and every LLM call is
logged with model, tokens, and cost. Langfuse is optional: with no keys set, the wrapper
is a no-op and the pipeline runs unchanged.

---

## What the v2 evals must show

Three headline metrics, all plotted against batch number:

1. **Would-send pass rate** — should rise as memory accumulates.
2. **Cost per accepted email** — should fall, as semantic memory lets research skip
   re-enrichment on known accounts.
3. **Personalization by (industry, persona)** — bucketed lift once a segment has enough
   examples, not an aggregate average that hides the effect.

Plus two robustness checks:

- **Memory attribution accuracy** — when the writer claims it applied a rule, does the
  critique agent agree the email reflects it?
- **Staleness detection** — are >60-day-old facts flagged before use?

The ablation table (no memory / episodic / semantic / procedural / all three) is the
result that matters; a learning curve without an ablation cannot separate "memory
helped" from "later batches were easier."
