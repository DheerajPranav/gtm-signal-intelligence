# RAG Eval Report — Northstar Knowledge Base

**Generated:** 2026-07-24 23:03:12  
**Mode:** `retrieval-only`  
**Questions:** 35  
**Cut-off:** k=5

> Retrieval-only run: no `ANTHROPIC_API_KEY` was present, so no answers were
> generated. Faithfulness, completeness, latency and cost are reported as
> **not measured** — they are not estimated or substituted.
> Re-run with `--full` and a key to populate them.

## Retrieval

| Metric | Value | Reads as |
|--------|-------|----------|
| Hit rate@5 | 0.7429 | share of questions where a gold doc surfaced |
| Recall@5 | 0.6095 | share of gold docs retrieved |
| Chunk precision@5 | 0.2743 | share of the context window on-target |
| MRR@5 | 0.5095 | how near the top the first gold chunk landed |

## Answer quality

| Metric | Value |
|--------|-------|
| Faithfulness (LLM judge) | not measured |
| Completeness (LLM judge) | not measured |
| Lexical trait coverage (deterministic proxy) | not measured |
| Ungrounded citations emitted | not measured |

## Performance

| Metric | Value |
|--------|-------|
| Latency p50 | not measured |
| Latency p95 | not measured |
| Avg cost / query | not measured |
| Total cost | not measured |

## By category

| Category | Count | Hit rate@5 | Recall@5 |
|----------|-------|----------|--------|
| comparison | 8 | 0.875 | 0.75 |
| edge_case | 5 | 0.4 | 0.2 |
| factoid | 10 | 0.8 | 0.7 |
| icp | 6 | 0.6667 | 0.6667 |
| synthesis | 6 | 0.8333 | 0.5555 |

## Per-question retrieval

| Question | Cat | Hit | Recall | MRR |
|---|---|---|---|---|
| What is Northstar Analytics? | factoid | 1.0 | 1.0 | 1.0 |
| What is Northstar's pricing? | factoid | 1.0 | 1.0 | 1.0 |
| What modules does Northstar offer? | factoid | 1.0 | 1.0 | 0.5 |
| Does Northstar integrate with Salesforce? | factoid | 1.0 | 1.0 | 0.5 |
| What is the target company size for Northstar? | factoid | 0.0 | 0.0 | 0.0 |
| How long does it take to see results with Northstar? | factoid | 1.0 | 0.5 | 0.2 |
| Does Northstar have security certifications? | factoid | 1.0 | 1.0 | 1.0 |
| What industries does Northstar serve? | factoid | 1.0 | 0.5 | 0.3333 |
| Who is the CEO of Northstar? | factoid | 0.0 | 0.0 | 0.0 |
| What is Northstar's ARR? | factoid | 1.0 | 1.0 | 1.0 |
| How does Northstar compare to Clari? | comparison | 1.0 | 1.0 | 1.0 |
| What are the key differences between Northstar and Gong Fore | comparison | 1.0 | 1.0 | 1.0 |
| How does Northstar's pricing compare to Mosaic? | comparison | 1.0 | 0.5 | 1.0 |
| What advantages does Northstar have over Pigment? | comparison | 1.0 | 1.0 | 1.0 |
| Why would a RevOps leader choose Northstar over competitors? | comparison | 0.0 | 0.0 | 0.0 |
| How is Northstar different from traditional BI tools? | comparison | 1.0 | 1.0 | 0.5 |
| What makes Northstar's forecast accuracy better than others? | comparison | 1.0 | 1.0 | 0.2 |
| How does Northstar help with pipeline hygiene? | comparison | 1.0 | 0.5 | 0.25 |
| What is Northstar's value prop for a Series C fintech? | synthesis | 1.0 | 0.5 | 1.0 |
| How would Northstar help a VP of Sales at a 500-person SaaS  | synthesis | 0.0 | 0.0 | 0.0 |
| What's the business case for Northstar for a Series B devtoo | synthesis | 1.0 | 1.0 | 1.0 |
| How does Northstar address forecast accuracy problems? | synthesis | 1.0 | 0.3333 | 0.2 |
| What specific pain points does Northstar solve for vertical  | synthesis | 1.0 | 1.0 | 0.25 |
| How would you position Northstar to a marketing tech company | synthesis | 1.0 | 0.5 | 1.0 |
| Would Northstar be a good fit for a 50-person Series A start | icp | 1.0 | 1.0 | 0.2 |
| Is Northstar suitable for a 5,000-person enterprise? | icp | 0.0 | 0.0 | 0.0 |
| Would a Series D company with $500M ARR be a good fit for No | icp | 1.0 | 1.0 | 1.0 |
| Is Northstar designed for companies without Salesforce? | icp | 0.0 | 0.0 | 0.0 |
| Would a bootstrapped SaaS company benefit from Northstar? | icp | 1.0 | 1.0 | 0.5 |
| Is Northstar a good fit for a company using Tableau for anal | icp | 1.0 | 1.0 | 1.0 |
| Does Northstar integrate with Excel? | edge_case | 0.0 | 0.0 | 0.0 |
| Can you use Northstar without a modern data warehouse? | edge_case | 1.0 | 0.5 | 1.0 |
| Does Northstar work with non-English companies? | edge_case | 1.0 | 0.5 | 0.2 |
| Can smaller teams (3 people) use Northstar effectively? | edge_case | 0.0 | 0.0 | 0.0 |
| What if a company has multiple Salesforce instances? | edge_case | 0.0 | 0.0 | 0.0 |
