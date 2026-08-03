# Days 27–28 — Launch + cold outreach checklist

All drafts below use **computed** numbers only (367 hermetic tests, RAG baseline, $0 live
spend). Live flagship quality metrics stay unclaimed. Every item here is a **user action** —
posting, DMing, and outreach are yours to execute. Fill the `[…]` links first: the portfolio
is live; Loom + blog + Show HN links need to exist before you post them.

## Pre-flight (do these first)
- [ ] Record the 5-min Loom (script: `docs/DAY_21_SHIP.md`).
- [ ] Publish the flagship blog post (`docs/FLAGSHIP_BLOG_POST.md`) → get a URL.
- [ ] Confirm the LinkedIn vanity URL; update `portfolio-site/src/app/page.tsx` + `public/cv.html` if different, then redeploy.
- [ ] Fill the CV Experience/Education placeholders and regenerate `cv.pdf`.

---

## Day 27 — Launch (DoD: thread live · LinkedIn live · 3+ communities · 3+ DMs)

### 1. Twitter/X thread
- [ ] Post from `docs/launch/twitter-thread.md` (12 tweets). Attach screenshots on 2–4, 6.

### 2. LinkedIn long-form
- [ ] Post the draft below. Add Loom + portfolio + repo links. Pin to Featured.

> **4 weeks ago I decided to go deep on GTM AI Engineering. Here's everything I shipped — and what I learned.**
>
> The goal wasn't a demo. It was to build GTM AI you could actually *trust*: every claim sourced, every capability behind a computed gate, and honest metrics — or none at all.
>
> **What shipped (one monorepo, 367 hermetic tests, $0.00 live API spend):**
>
> 🔹 **A 5-agent outbound engine** — research → score → persona → write → critique → a deterministic Account Brief. The research agent returns *sourced* fields (every value carries its URL), a deterministic check fails fabricated provenance, and the critique judge is skeptical by construction (defaults to "no").
>
> 🔹 **A hybrid-retrieval RAG knowledge base** — BM25 + vector via Reciprocal Rank Fusion, reranking, cited answers over a 30-doc corpus built to be internally consistent. Computed baseline: 74% hit rate@5, 61% recall@5.
>
> 🔹 **An open-source LLM-judge eval kit** (`gtm-agent-evals`, MIT) — ICP/persona/email/critique rubrics with deterministic gates and a CLI runner. Tested on 5 great cold emails vs 5 templated: the gate passed 5/5 vs 0/5.
>
> **The three lessons:**
> 1. **Grounding is structural, not prompted.** Provenance you capture at extraction time beats provenance you reconstruct later.
> 2. **A judge that says yes to everything measures nothing.** Skepticism is a feature.
> 3. **"Not measured" beats a fabricated number.** Every metric I quote was computed from a generated artifact — no live key, no number.
>
> Portfolio: https://dheerajpranav.github.io/gtm-signal-intelligence/
> Code: github.com/DheerajPranav/gtm-signal-intelligence
> 5-min walkthrough: [Loom]
> Deep-dive: [blog]
>
> Open to GTM AI engineering / forward-deployed roles. If you're building in this space, I'd love to compare notes.
>
> Stay curious, stay disciplined. — Dheeraj (KD)

### 3. Community posts (pick 3+)
- [ ] **Show HN** — "Show HN: An auditable multi-agent GTM outbound system (open source)". Lead with the honesty angle (sourced claims, computed gates, `not measured`), link repo + portfolio. Reply fast to comments.
- [ ] **r/MachineLearning** — `[P]` project post; emphasize the eval methodology (deterministic gates, skeptical judge, hermetic tests), not the sales use-case.
- [ ] **r/salesengineering** (or r/sales) — frame around "would-send gate" and the great-vs-templated comparison.
- [ ] **Discords** — Latent Space, AI Engineer, MLOps: short intro + portfolio link in the #showcase / #projects channel.

> Community-post seed (adapt per venue): *"Spent 4 weeks building GTM AI I could trust —
> sourced claims, computed eval gates, and a rule that unmeasured stays 'not measured.'
> Open-sourced the eval kit. 367 hermetic tests, $0 live spend. Repo + write-up: [link].
> Happy to answer anything about the eval methodology."*

### 4. Personal DMs (3–5 people you respect)
- [ ] Send the DM template below to 3–5 people in GTM AI, asking for a quick reaction (not a job).

> DM: *"Hi [name] — big fan of [specific thing they built/wrote]. I just wrapped a 4-week
> build going deep on GTM AI: a sourced, evaluated multi-agent outbound system + an
> open-source eval kit. Would genuinely value your reaction to the eval approach if you
> have 5 min: [portfolio]. No ask beyond that."*

---

## Day 28 — Cold outreach + retrospective (DoD: 20+ sent · tracker · retro)

### 1. Build the target list (20–25)
Use `docs/launch/outreach-tracker.csv`. Suggested buckets (from the sprint plan):
- **Heads of AI at sales tools:** Clay, Apollo, Outreach, Salesloft, Gong, Attio, Rippling, Ramp, Cargo.
- **GTM Engineering leads at fast-growing SaaS:** Ramp, Rippling, Vercel, Linear, Perplexity, Anthropic/OpenAI GTM.
- **AI hiring managers** who've posted relevant roles recently.

### 2. Cold outreach message (4 lines, personalize line 1)
> *"Hi [name] — [one specific, current thing about their company/role]. I just built a
> sourced, evaluated multi-agent GTM outbound system (open source) and thought it might be
> relevant to how [company] thinks about [their thing]. 5-min walkthrough here: [Loom].
> Happy to give you the 10-min version if useful."*

- [ ] Personalize line 1 for each — no line-1 reuse. Send 20+.
- [ ] Log every send in the tracker (name, company, role, channel, sent date, status).

### 3. Retrospective (~1000 words, private)
- [x] Draft written → `docs/launch/RETROSPECTIVE.md` (edit to taste; consider keeping private / moving to Substack).
- [ ] Personalize + finalize before publishing anywhere.

### 4. Then rest.
> Sleep. Tired code is bad code. — the plan

---

## Sprint scoreboard (for your own reference)
- Days 1–26 complete; 367 hermetic tests; $0.00 live API spend.
- Live: portfolio (GitHub Pages). Ready-to-deploy: flagship backend (Modal), dashboard (Streamlit), DB (Neon) — see `docs/DEPLOY.md`.
- Still gated on a live key: flagship quality metrics + a real backend run.

*Stay curious, stay disciplined. — Dheeraj (KD)*
