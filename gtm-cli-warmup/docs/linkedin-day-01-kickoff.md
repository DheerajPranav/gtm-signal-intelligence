# LinkedIn — Day 1 kickoff (draft)

Post this yourself; it's a draft, not a scheduled post.

---

I'm spending the next few weeks going deep on GTM AI Engineering, and building
in public.

Four things I'm shipping:

1. **A knowledge base** — hybrid retrieval (BM25 + vector, RRF-fused) over a
   synthetic B2B SaaS corpus, with a reranker and citation-anchored answers.
2. **A multi-agent outbound system** — account research → ICP scoring → persona
   modelling → personalised drafts → an LLM critic that decides whether a
   discerning SDR would actually send it.
3. **An open-source eval kit** — the LLM-judge rubrics for GTM agents I wish
   existed when I started.
4. **A portfolio site** tying it together, plus the writeups.

One rule for all of it: **if it wasn't evaluated, it doesn't count.** Every repo
gets a golden dataset, an eval harness, and cost-per-run in the README. Plenty of
demos look great and fall over on the 50th input. I want the numbers on the table.

Day 1 is deliberately unglamorous — a CLI that turns a company name into a
validated object, with token and dollar cost logged for every call. Two habits I
want automatic before anything harder: structured output through tool use, never
string parsing. And cost tracking from the first call, never bolted on later.

Following along is welcome. I'll post the misses too.

Stay curious, stay disciplined.
