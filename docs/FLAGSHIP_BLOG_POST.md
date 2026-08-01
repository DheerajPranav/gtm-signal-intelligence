# Building a GTM outbound agent you can actually trust

*Five agents, one honest evaluation loop — and why "not measured" is a feature.*

---

Every "AI SDR" demo I've seen falls apart on the same question:

> **How do you know the email is any good before it reaches a customer's inbox?**

The model call is the easy part. Any framework will chain a few prompts and hand you a
confident-looking email about a company it half-invented. The hard part — the part that
decides whether a RevOps team would ever let this near a real prospect — is the machinery
that makes the output *trustworthy*: sourced claims, scores that can't lie, and a way to
measure quality that you didn't fabricate.

This post walks through `gtm-outbound-agent`, the flagship of a four-week applied-AI
sprint. It researches an account, scores ICP fit, discovers buyer personas, drafts
personalized emails, and critiques them — and every one of those steps ships behind a
computed gate.

## The world is fixed on purpose

Before any of the agents, there's a decision that makes everything else measurable: the
system is grounded in **one fixed, internally-consistent fictional company** — Northstar
Analytics. Thirty cross-linked markdown docs (product, pricing, ICP, case studies,
positioning) share a single canonical fact sheet, enforced by an integrity check.

Why fictional? Because with real data you inherit inconsistencies and can never tell a
retrieval *miss* from a corpus *gap*. When the world is fixed and known-answerable, every
generated claim is groundable and every eval question has a real answer. The corpus is the
substrate for grounding — and, honestly, it's where most of the engineering value lives.

## The five-agent chain

```
Research → Score → Persona → Write → Critique → Account Brief
```

Each stage is a separate agent with a typed output, chained by `run_company(domain)`:

1. **Research** enriches a domain into a `CompanyProfile`.
2. **Score** rates ICP fit across four dimensions.
3. **Persona** discovers three buyer stakeholders.
4. **Write** drafts three angles per persona (async fan-out).
5. **Critique** grades every email with a skeptical judge.

They assemble into a deterministic **Account Brief** — pure markdown, no LLM.

## Grounding is structural, not prompted

The research agent doesn't return a company profile; it returns a *sourced* one. Every
field is a `Sourced[T]` carrying its `value`, the `source_url` it came from, and a
confidence. The tool schema **requires** a source URL per field, so provenance is captured
at extraction time — not reconstructed afterward by asking the model "where did you get
that?"

Then a **deterministic check** fails any citation to a URL the agent never actually
fetched during the run. This matters more than it sounds: fabricated provenance is the
worst failure mode in this whole system, precisely because it *looks* sourced. A human
skimming the brief sees a link and trusts it. The check needs no LLM judge — it's just set
membership against the fetch log.

One more thing the research agent does: it treats the open web as hostile. Every tool
result is fenced in explicit `<<<UNTRUSTED_WEB_CONTENT …>>>` markers, and the system prompt
states that fenced content is data, never instructions. A page telling the agent to rate
its own company favorably is a realistic attack, not a hypothetical.

## Scores that can't lie

The scoring agent rates four ICP dimensions — firmographic, technographic, behavioral,
timing — each 0–10. But the **headline score is computed in code**, a deterministic
weighted mean, not something the model emits.

That single decision buys two things:

- **The number can never contradict its breakdown.** If a reader disputes the overall
  fit, the per-dimension reasoning always adds up to it.
- **Re-weighting is one line, not a re-prompt.** The ICP's emphasis lives in code.

And the rubric itself comes from the knowledge base — the same `icp-definition.md` the RAG
assistant answers from — so scoring can't drift from the single source of truth. A field
the research agent couldn't source is shown to the model as `(not found)`, keeping "we
looked and it's weak" distinct from "we never found out." Only the ICP's explicit hard
disqualifiers pull a score to the floor.

## Async without chaos

The writing agent is the first async stage. For each persona it drafts three variants that
differ in **angle**, not wording:

- **pain** — the persona's sharpest pain, in Northstar's own language
- **trigger** — a datable event pulled from the company profile
- **peer-proof** — a segment-matched customer story read from the KB

Three personas × three angles = nine emails per company, drafted concurrently. The trap
here is unbounded fan-out hammering the API. The fix: **one shared semaphore for the whole
run**. Variants within a persona and personas across a company all pass through a single
`asyncio.Semaphore` (default 5), so in-flight requests stay bounded no matter how many
personas exist. The rate limit belongs to the run, not the persona.

Hard limits are structural too — subject ≤ 60 chars, body ≤ 120 words, exactly three
personalization hooks — all schema-enforced, then checked by the eval.

## A judge that says no

Here's the part most demos skip. The critique agent grades each email on five dimensions
(personalization, relevance, CTA, spam-risk inverted, would-send) — and it's a
**deliberately skeptical** judge, prompted as a discerning SDR manager who defaults to
"no."

That skepticism is the whole point. A judge that says yes to everything measures nothing;
LLM-judge sycophancy is the standard failure of naive eval setups. It runs on Haiku
(cheap, nine times per company), and instead of owning its own admission threshold, it
returns a `MemoryWriteDecision` by applying a single shared policy — so the critique can't
drift from the writer or the consolidation logic.

The final brief is **deterministic**: `brief.py` assembles markdown with no model call at
all — would-send pass rate at the top, sourced company summary, ICP-fit table, persona
cards, per-persona emails with inline verdicts. Unfound fields render `_not found_`, never
a fabricated value.

## Honesty as an engineering discipline

This project has a written rule, and it exists because of a mistake:

> A metric may appear in prose only if it was computed from a generated artifact in the
> same session. Deliverables claimed as shipped must be verified by a URL or a file, not
> asserted.

Early on, a session wrote fabricated eval numbers and claimed deploys that never happened.
None of it was real. The correction wasn't just deleting the numbers — it was rebuilding
the harness so that **unmeasured metrics render `not measured`, never a placeholder**. If
there's no API key to run the live scoring eval, the report says `not measured` and prints
the Spearman gate it *would* check — it does not invent a correlation.

That discipline is visible throughout: the research agent's field accuracy is deliberately
unmeasured until a human verifies ground truth; the brief reports `$0` cost rather than a
made-up token estimate until per-call accounting is wired.

## What's measured vs. what's pending

Being honest about this cuts both ways. Here's the real state:

**Computed and green:**
- **347 hermetic tests** across the monorepo — zero API calls in the suite, offline
  embeddings and injected fake LLM clients throughout.
- The knowledge base's retrieval baseline over 35 golden questions: **74% hit rate@5, 61%
  recall@5** (k=5).
- **$0.00 live API spend to date** — every shipping gate is verified offline before a
  single live call.

**Gated on a live key (honestly `not measured` today):**
- The flagship's live quality metrics — email quality, would-send pass rate, ICP Spearman
  correlation — are wired, tested offline, and ready to run the moment a key is set. I'd
  rather ship a reproducible offline gate than a live demo I can't measure.

## The takeaway

The interesting engineering in GTM AI isn't the prompt. It's the surrounding
machinery — structural grounding, scores computed in code, a judge built to disagree, and
a hard rule that unmeasured beats fabricated. That's what turns a slick demo into
something a revenue team could actually trust.

The code is open, and the evals are reproducible offline: **[github.com/DheerajPranav/gtm-signal-intelligence](https://github.com/DheerajPranav/gtm-signal-intelligence)**

---

*Northstar Analytics is entirely fictional and labelled as such throughout. No real person
or company is represented.*

*Stay curious, stay disciplined. — Dheeraj (KD)*
