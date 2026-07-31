# Day 21 — Flagship Ship: Loom Script + LinkedIn Posts + Blog Outline

**Status:** Draft content ready. Two items require action before publishing:
1. **Record the Loom** (script below) — needs a screen recording of the dashboard.
2. **A live run** for any *quality* metric (email quality, would-send rate, ICP
   Spearman) needs `ANTHROPIC_API_KEY` or `GROQ_API_KEY`. Until then those stay
   `not measured` — do **not** put a number on them. Only the numbers marked
   **[computed]** below are real today.

## What's actually measured today (safe to publish)

- **[computed]** 347 hermetic tests passing — 14 CLI + 84 KB + 214 outbound + 35 eval-kit.
  Zero API calls in the suite (offline embeddings + injected fake LLM clients).
- **[computed]** RAG retrieval baseline over 35 golden questions (k=5):
  hit rate@5 **0.743**, recall@5 **0.61**, chunk precision@5 **0.274**, MRR@5 **0.510**.
- **[computed]** RAG cost *model*: ~**$0.006/query** at real Anthropic pricing; **$0** in demo mode.
- **[computed]** Live API spend to date: **$0.00** — every shipping gate verified offline.

## What is NOT yet measured (do not claim a number)

- Flagship email quality (avg critique 0–5), would-send pass rate, ICP Spearman
  correlation, enrichment accuracy — all gate to `not measured` without a live key
  (see `gtm-outbound-agent/evals/report.md`).
- Per-account / per-email dollar cost — per-call token cost isn't wired into the
  brief yet, so `run_company` reports `$0`. Cost is derivable from the pricing table
  once observability lands, but it hasn't been aggregated.

---

## 5-Minute Loom Script — "Grounded, evaluated multi-agent outbound"

**0:00–0:30 — The problem.**
> "Cold outbound AI tools hallucinate. They invent company facts, write generic emails,
> and there's no way to tell a good draft from a bad one before it hits a prospect's inbox.
> I built a multi-agent system where every claim is sourced, every email is critiqued, and
> every capability has a computed gate — not a 'looks good.'"

**0:30–1:30 — Architecture (show the diagram from the README).**
> "Five agents in a chain. Research enriches a domain into a *sourced* CompanyProfile —
> every field carries the URL it came from. Scoring rates ICP fit on four dimensions,
> grounded in the knowledge base's canonical ICP doc. Persona discovers three buyer
> stakeholders. Writing fans out async — three angles per persona, nine emails per company,
> bounded by one shared semaphore. Critique is a deliberately skeptical Haiku judge that
> defaults to 'no.' It all assembles into a deterministic Account Brief."

**1:30–3:00 — Dashboard walkthrough (screen-record `streamlit run dashboard.py`).**
> "Run history, live progress, cost trends, and drill-down into any account. Here's a batch
> run — concurrent companies with failure isolation, so one bad domain doesn't kill the run,
> and it resumes from checkpoint." *(Show a completed batch from `runs/`.)*

**3:00–4:00 — Honesty as a feature.**
> "Here's what makes this portfolio-grade. Every eval that needs a live model call and
> doesn't have a key renders `not measured` — never a fabricated number. The research agent's
> URL-grounding check fails a citation to any page it never actually fetched. The scoring
> agent's headline number is a deterministic weighted mean, so it can never contradict its own
> breakdown. 347 tests, all offline, all deterministic."

**4:00–5:00 — Numbers + close.**
> "The knowledge-base retrieval baseline is computed: 74% hit rate at 5, 61% recall. Live
> spend to date is zero — everything ships behind an offline gate first. The flagship's live
> quality metrics are gated and ready to run the moment a key is set. Repo's open, evals are
> reproducible. Stay curious, stay disciplined."

**Recording checklist:** demo mode / offline batch (no key needed) · dashboard on `localhost` ·
README architecture diagram on screen · `evals/report.md` visible for the "not measured" beat.

---

## LinkedIn Post A — Flagship shipped (Loom + repo)

🚀 **The flagship is built.** A multi-agent GTM outbound system that researches an account,
scores ICP fit, discovers buyer personas, drafts personalized emails, and critiques them —
where every claim is sourced and every capability has a computed gate.

**Five agents, one honest chain:**
→ **Research** — bounded tool-use loop → a *sourced* CompanyProfile (every field carries its source URL; web content is fenced as untrusted)
→ **Scoring** — 4-dimension ICP rubric read from the knowledge base; headline score is a deterministic weighted mean, never model-asserted
→ **Persona** — 3 company-specific buyer stakeholder cards, grounded in real positioning language
→ **Writing** — async fan-out, 3 angles per persona (pain / trigger / peer-proof), 9 emails/company, one shared semaphore
→ **Critique** — a skeptical Haiku judge that defaults to "no," plus a memory-write decision

**The engineering bar:**
- ✅ **347 hermetic tests** — zero API calls in the suite (offline embeddings + injected fake clients)
- ✅ Every unmeasured metric renders `not measured` — never a fabricated number
- ✅ Deterministic Account Brief: unfound fields render "not found," never invented
- ✅ Live API spend to date: **$0.00** — every gate verified offline before a single live call

The knowledge base underneath it: hybrid retrieval baseline of **74% hit rate@5 / 61% recall@5**
over 35 golden questions (computed).

Honest status: the live *quality* metrics (email quality, would-send rate) are gated and
ready — they run the moment an API key is set. I'd rather ship a reproducible offline gate
than a live demo I can't measure.

5-min walkthrough → [Loom link]
Repo → github.com/DheerajPranav/gtm-signal-intelligence

Stay curious, stay disciplined. Dheeraj (KD).

\#AI \#GTM \#MultiAgent \#LLMs \#OpenSource \#RevOps \#EngineeringInPublic \#Anthropic \#Python

---

## LinkedIn Post B — Technical teaser for the blog

Most "AI SDR" demos fall apart on one question: **how do you know the email is any good
before you send it?**

Here's the pattern I used in the flagship outbound system (blog post dropping this week):

**1. Grounding is structural, not prompted.** The research agent returns `Sourced[T]` —
every field carries a `source_url` captured at extraction time. A separate deterministic
check fails any citation to a URL the agent never fetched. Fabricated provenance is the worst
failure mode because it *looks* sourced.

**2. The judge is skeptical by construction.** The critique agent is a "discerning SDR
manager who defaults to no." That's the standard guard against LLM-judge sycophancy — a judge
that says yes to everything measures nothing.

**3. Unmeasured is a first-class value.** No live key? The eval prints `not measured`, never a
placeholder number. This project has a written rule: a metric appears in prose only if it was
computed from a generated artifact in the same session.

Full deep-dive on the architecture, the async fan-out, and the memory-write policy → [blog link this week]

Repo → github.com/DheerajPranav/gtm-signal-intelligence

\#AI \#GTM \#LLMs \#Evals \#EngineeringInPublic

---

## Flagship Blog Post — Outline (write Day 23)

**Working title:** "Building a GTM outbound agent you can actually trust: five agents, one honest evaluation loop"

1. **Hook** — the trust gap in AI outbound; hallucinated facts + unmeasurable quality.
2. **The world is fixed on purpose** — Northstar Analytics as a consistent fictional corpus, so every claim is groundable and every eval is answerable.
3. **The five-agent chain** — research → score → persona → write → critique; what each returns and why it's a separate agent.
4. **Grounding is structural** — `Sourced[T]`, deterministic URL-grounding check, injection fencing of untrusted web content.
5. **Scores that can't lie** — model scores dimensions, code computes the weighted mean; absence ≠ disqualification.
6. **Async without chaos** — one shared semaphore for the whole run, three angles not three rewordings.
7. **A judge that says no** — skeptical critique rubric, spam-risk inverted, memory-write decision owns no duplicate threshold.
8. **Honesty as an engineering discipline** — `not measured` over fabricated numbers; the integrity incident and the standing rule that came out of it.
9. **What's measured vs. what's pending** — 347 hermetic tests + RAG baseline (computed) vs. live quality metrics (gated on a key).
10. **Close** — reproducibility over demo theater; repo + eval kit links.

---

*Sign-off: Stay curious, stay disciplined. Dheeraj (KD).*
