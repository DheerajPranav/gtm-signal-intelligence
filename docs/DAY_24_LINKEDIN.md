# Day 24 — LinkedIn Profile Overhaul (copy to paste)

**Status:** Draft copy ready. Updating the live LinkedIn profile is a user action.
All numbers are computed (347 tests, RAG baseline, $0 live spend); no live quality
metric is claimed.

---

## Headline (220 char max)

> GTM AI Engineer · Building auditable, evaluated agents for sales & marketing workflows · Grounded outputs, computed eval gates, honest metrics

## About

I build GTM (go-to-market) AI systems where correctness is *provable*, not asserted.

Most "AI for sales" tools fall apart on one question: how do you know the output is any
good before it reaches a customer? So I build the machinery that makes an answer
trustworthy — structural grounding, scores computed in code, and a skeptical judge that
grades every draft.

Over a focused 4-week sprint I shipped a monorepo of four GTM AI capabilities, all built
against one fixed, internally-consistent world so every claim is groundable and every
capability is measured:

🔹 **Multi-agent outbound engine** — research → score → persona → write → critique, with
source-grounded profiles (every field carries its URL) and async email drafting graded by a
deliberately skeptical LLM judge. 214 hermetic tests.

🔹 **Hybrid-retrieval RAG assistant** — BM25 + vector via Reciprocal Rank Fusion, reranking,
cited answers. Computed retrieval baseline: 74% hit rate@5, 61% recall@5.

🔹 **Open-source LLM-judge eval kit** — framework-agnostic ICP/Persona/Email/Critique
rubrics with deterministic gates, MIT-licensed.

The throughline: **347 hermetic tests, $0.00 live API spend** (every gate verified offline),
and a hard rule that unmeasured metrics render "not measured" — never a fabricated number.

Currently focused on GTM AI engineering and forward-deployed AI roles. Let's talk.

🔗 Portfolio & code: github.com/DheerajPranav/gtm-signal-intelligence

## Experience — new entry

**GTM AI Portfolio Sprint** — Self-directed · 2026 (4 weeks)
- Designed and shipped a 4-project GTM AI monorepo (multi-agent outbound, hybrid RAG, open-source eval kit, extraction CLI) with 347 hermetic, deterministic tests and $0 live API spend.
- Built structural grounding (sourced fields + deterministic URL-grounding check + prompt-injection fencing) and a skeptical LLM-judge evaluation loop.
- Established an honesty discipline: every reported metric is computed from a generated artifact; unmeasured metrics render "not measured."

## Featured (pin these)

1. **Portfolio site** — [Vercel URL once deployed]
2. **Flagship Loom** — [Loom URL once recorded]
3. **Flagship blog post** — "Building a GTM outbound agent you can actually trust" — [blog URL once published]

---

## Checklist (user actions)

- [ ] Paste headline
- [ ] Paste About
- [ ] Add the Experience entry under 2026
- [ ] Pin the 3 Featured items (fill in the 3 URLs once live)
- [ ] Confirm the vanity URL matches `linkedin.com/in/dheerajpranav` (update the portfolio + CV if different)

*Stay curious, stay disciplined. — Dheeraj (KD)*
