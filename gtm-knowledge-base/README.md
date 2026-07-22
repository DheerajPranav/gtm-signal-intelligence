# gtm-knowledge-base

A **self-contained, consistent knowledge corpus** for a fictional B2B RevOps analytics company — **Northstar Analytics** — built to ground GTM AI tools: retrieval-augmented generation, ICP scoring, grounded outbound, and evals.

This is Day 3 of the GTM AI Engineering sprint. It is the shared source of truth that later projects (RAG chatbot, account research agent, outbound generator) retrieve against.

## Why a fixed corpus

Grounded generation and RAG are only as trustworthy as their source data. A **single, internally-consistent corpus** lets us:

- Ground every generated claim in a citable document.
- Write evals with known-correct answers (the facts are fixed).
- Detect hallucination — if a tool asserts a fact not in the corpus, it's invented.

## Contents

**30 markdown documents** across five categories, all consistent with one [canonical fact sheet](data/northstar/README.md):

| Category | Docs | What's inside |
|---|---|---|
| `product/` | 7 | Overview, 3 modules, integrations, security, pricing |
| `sales/` | 10 | ICP, positioning, discovery, objections, playbook, 4 battlecards, FAQ |
| `case-studies/` | 4 | Ledgerly, Forgestack, Cliniva, Adloom (all fictional) |
| `marketing/` | 5 | Homepage, 2 persona pages, 2 blog posts |
| `company/` | 4 | About, leadership, customer list, analyst quotes |

Every doc has YAML frontmatter and relative cross-links.

## Verify the corpus

```bash
bash scripts/check_corpus.sh
```

This asserts the corpus is complete and internally consistent:
- exactly **30** markdown docs, in the expected per-category counts;
- every doc has frontmatter;
- shared facts (ICP bounds, competitor set, pricing, locked metrics) appear where expected and are not contradicted.

Exit code `0` = corpus is intact. Non-zero = a check failed (details printed).

## Honesty note

Northstar Analytics, its customers, leadership, analysts, and press quotes are **fictional**, created for training/demos and labelled as such in the docs. No real organization or person is represented, and no fabricated LLM output is presented as genuine.

## Layout

```
gtm-knowledge-base/
├── README.md               ← you are here
├── data/northstar/
│   ├── README.md           ← canonical fact sheet + provenance
│   ├── product/  sales/  case-studies/  marketing/  company/
└── scripts/
    └── check_corpus.sh     ← corpus integrity gate
```
