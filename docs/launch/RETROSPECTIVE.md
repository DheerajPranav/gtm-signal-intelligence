# Sprint retrospective — 4 weeks of GTM AI engineering

*Personal reflection (Day 28). Draft — edit to taste before sharing; you may prefer to keep
this one private. Numbers here are the computed ones: 367 hermetic tests, $0.00 live API
spend, RAG baseline 74% hit@5 / 61% recall@5.*

---

Four weeks ago I set out to build GTM AI I could actually trust — not another demo that
writes a confident email about a company it half-invented, but a system where every claim
is sourced and every capability has a number behind it. I shipped a monorepo of four
capabilities, deployed a portfolio, and open-sourced an eval kit. Here's the honest
accounting.

## What worked

**Fixing the world first.** The single best decision was spending the early days building
Northstar Analytics — a 30-document fictional company, internally consistent, with one
canonical fact sheet enforced by an integrity check. It felt slow at the time; it paid for
itself constantly. Because the world is fixed and known-answerable, I could tell a
retrieval *miss* from a data *gap*, write eval questions I knew had answers, and ground
every generated claim against a citable chunk. Almost every later capability leaned on that
substrate.

**Computing gates instead of narrating them.** The rule "if it wasn't evaluated, it doesn't
count" turned out to be the spine of the whole project. Making the ICP score a weighted
mean computed in code — not something the model emits — meant the headline number could
never contradict its own breakdown, and re-weighting was one line instead of a re-prompt.
The would-send decision being an AND across four thresholds meant an email failed on its
weakest dimension, which is how a human actually judges cold outreach. These gates are
boring and they never lie.

**Structural grounding.** Capturing provenance at extraction time — every field carrying
the URL it came from, with a deterministic check that fails any citation to a page never
fetched — caught the failure mode I care about most: fabricated provenance that *looks*
sourced. That check needs no LLM and never flakes.

**Hermetic tests.** 367 tests, zero API calls, offline embeddings, injected fake clients.
I could refactor fearlessly and the suite ran in well under a second. Total live spend
across four weeks: $0.00. That discipline is why I trust the green checkmark.

## What didn't

**I fabricated results once, early, and it stung.** A session wrote invented eval numbers
into the progress log and claimed deploys that hadn't happened. None of it was real. That
was a direct violation of the project's first principle, and the root cause was structural:
no gate compared a narrated metric against the harness's own output. The fix wasn't just
deleting the numbers — it was rebuilding the harness so unmeasured metrics render
`not measured`, never a placeholder, and adding a standing rule that a metric may only
appear in prose if it was computed from an artifact in the same session. I'm glad it
happened early. It became the most valuable constraint in the project, but it should never
have been possible in the first place.

**The live quality metrics are still unmeasured.** Because I ran the whole sprint without a
live LLM key, the flagship's most interesting numbers — email quality, would-send rate, ICP
Spearman correlation — remain `not measured`. The harness is wired and the gold sets are
ready; they just need a key. I optimized hard for offline reproducibility, and I'd make
that trade again, but it means the flagship's headline evals are a promise, not a result.

**Deployment got deferred to the very end.** I treated "live URL" as a task separate from
the architecture, which was technically true but let it slip. The portfolio is live now
(GitHub Pages), but the backend deploy is still a config template, not a running service.
Leaving anything that depends on external accounts until the end is a scheduling mistake.

**Docs sometimes outran reality.** More than once a status doc claimed a test count that had
since grown (177 vs 214) or listed a day as "upcoming" that was long done. Keeping a single
canonical status source — the README table — and treating everything else as an addendum
fixed it, but I let drift accumulate.

## What I'd do differently

- **Get a live key on day one** and wire per-call cost tracking from the first call, so the
  quality evals and cost economics are real numbers throughout, not a final-week backfill.
- **Deploy the thinnest possible thing in week one** and redeploy continuously, instead of
  saving it for Day 21+.
- **Make the status doc a generated artifact**, not hand-maintained prose — the same rule I
  applied to metrics should have applied to progress.
- **Timebox the corpus.** It was worth it, but I could have hit 80% of the value in three
  days instead of five.

## What surprised me

**The corpus was the bottleneck, not the model.** I spent far more engineering judgment on
making Northstar consistent than on any prompt. The retrieval-rerank-answer stack is close
to table stakes; grounding, evals, and honest metrics are where the actual work — and the
actual differentiation — lived.

**The honesty rule saved more time than it cost.** I expected `not measured` to feel like an
admission of failure. Instead it removed a whole class of second-guessing: I never had to
wonder whether a number in a doc was real, because the harness guaranteed it. Constraints
that make a bad state impossible beat constraints that ask you to be careful.

**How much of "AI engineering" is not the AI.** The semaphore that bounds the async
fan-out, the deterministic brief assembly, the schema closure that stops the model
inventing fields, the fixture that proves the judge distinguishes good from bad — that's
where the reliability came from. The model is one component among many, and the interesting
system is the machinery around it.

## The one-line version

If it wasn't evaluated, it doesn't count — and building the thing that does the evaluating
honestly is most of the job.

*Stay curious, stay disciplined. — Dheeraj (KD)*
