# Launch thread — Twitter/X (draft)

**Status:** Draft. Publishing is a user action. Fill the `[…]` links (portfolio is live;
Loom + blog are still to be recorded/published). Every number below is **computed**
(347→363 hermetic tests, RAG baseline, $0 live spend); the flagship's live *quality*
metrics are intentionally not claimed.

Attach screenshots where noted. Keep each tweet ≤ 280 chars.

---

**1/**
I spent 4 weeks going deep on GTM AI engineering.

Shipped 3 projects + an open-source eval kit. 363 tests. $0 in live API spend.

The theme: build agents you can actually *trust* — every claim sourced, every capability gated.

Here's what I built and learned. 🧵

**2/**
The flagship: a 5-agent cold-outbound system.

research → score → persona → write → critique → Account Brief

It researches an account, rates ICP fit, finds buyer personas, drafts emails, and grades them — chained into one deterministic brief.

[screenshot: architecture diagram]

**3/**
The part most "AI SDR" demos skip: grounding.

The research agent returns *sourced* fields — every value carries the URL it came from. A deterministic check fails any citation to a page it never actually fetched.

Fabricated provenance is the worst bug: it *looks* sourced.

**4/**
And the judge is skeptical on purpose.

The critique agent is prompted as a discerning SDR manager who defaults to "no." A judge that says yes to everything measures nothing.

[screenshot: an Account Brief with would-send verdicts]

**5/**
Then I packaged the eval logic into an open-source kit: `gtm-agent-evals`.

Framework-agnostic rubrics (ICP / persona / email / critique) with deterministic gates + a CLI runner. MIT licensed.

The LLM scores dimensions; the pass/fail is computed in code.

**6/**
Does the rubric actually work? I tested it on 5 great cold emails vs 5 templated ones.

Result: 5/5 great pass the would-send gate, 0/5 templated pass. Spam-risk gap +2.1.

It fails an email on its weakest dimension, not its average.

[screenshot: comparison table]

**7/**
Underneath it all: a hybrid-retrieval RAG knowledge base.

BM25 + vector via Reciprocal Rank Fusion, a reranker, cited answers — over a 30-doc corpus built to be internally consistent so every answer is groundable.

**8/**
Why a fictional corpus?

With real data you can't tell a retrieval *miss* from a data *gap*. A fixed, known-answerable world lets you measure the stack honestly.

Computed baseline: 74% hit rate@5, 61% recall@5.

**9/**
Cost economics: the whole sprint ran at **$0.00 live API spend**.

Every capability ships behind an offline, deterministic gate — fake LLM clients + offline embeddings — before a single live call. 363 hermetic tests, zero flakiness.

**10/**
The rule that made it portfolio-grade: **honesty as an engineering discipline.**

A metric appears in prose only if it was computed this session. No live key? The eval prints "not measured" — never a fabricated number.

**11/**
Everything's open and reproducible.

Portfolio: https://dheerajpranav.github.io/gtm-signal-intelligence/
Code: github.com/DheerajPranav/gtm-signal-intelligence
Blog: [flagship deep-dive — link]
Loom: [5-min walkthrough — link]

**12/**
Next: wiring live quality metrics + a production deploy.

If you're working on GTM AI — grounding, evals, agents — I'd love to compare notes. Open to GTM AI engineering / forward-deployed roles.

Stay curious, stay disciplined. ↩️ RT tweet 1 if useful.

---

## Notes for posting
- Tweets 2–4, 6 want screenshots (architecture, Account Brief, comparison table).
- Confirm the Loom + blog links exist before posting (or drop those lines).
- The portfolio link is live now; the LinkedIn vanity URL still needs confirming.
