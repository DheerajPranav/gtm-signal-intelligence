---
title: Northstar Analytics — Corpus README
doc_type: reference
---

# Northstar Analytics — Fictional Company Corpus

**Northstar Analytics is a fictional B2B RevOps analytics company** invented for GTM AI engineering training, demos, and evals. Nothing here is a real company, person, customer, quote, or metric. It exists so downstream tools (RAG, grounded generation, ICP scoring, outbound drafting) have a **consistent, self-contained knowledge base** to work against.

## The one-liner

> The RevOps analytics layer for teams outgrowing spreadsheets and BI tools not built for revenue data.

## Canonical facts (single source of truth)

Every document in this corpus is kept consistent with these facts. If you extend the corpus, do not contradict them.

- **Founded** 2019 · **HQ** San Francisco, remote-first (US+EU) · **Series B**, **$32M** raised · **~120** employees · **140+** customers.
- **Product:** three modules — [Pipeline Analytics](product/module-pipeline-analytics.md), [Forecast Accuracy](product/module-forecast-accuracy.md), [Rep Productivity](product/module-rep-productivity.md).
- **ICP:** B2B SaaS, 200–2000 employees, $20M–$200M ARR, Series B–D; Salesforce **or** HubSpot; Snowflake **or** BigQuery. See [ICP definition](sales/icp-definition.md).
- **Competitors:** Clari, Gong Forecast, Mosaic, Pigment (one battlecard each in `sales/`).
- **Pricing:** Core **$2,500/mo** (≤40 seats), Growth **$6,000/mo** (≤120 seats), Enterprise **custom**; add-on seats $25/seat/mo; 14-day proof-of-value pilot. See [pricing](product/pricing.md).
- **Locked metrics (reuse verbatim):** 90%+ forecast accuracy within two quarters (from ~70%, +20 pts); pipeline-review prep ~6 hours → ~30 minutes; 4–6 week implementation; ~12% quota-attainment lift within a year.
- **Security:** SOC 2 Type II, GDPR, ISO 27001 in progress; warehouse-native (data never leaves the customer warehouse on Enterprise). See [security](product/security.md).

## Structure (30 documents)

```
data/northstar/
├── product/       (7)  overview, 3 modules, integrations, security, pricing
├── sales/         (10) ICP, positioning, discovery, objections, playbook,
│                       4 battlecards, FAQ
├── case-studies/  (4)  Ledgerly, Forgestack, Cliniva, Adloom
├── marketing/     (5)  homepage, 2 persona pages, 2 blog posts
└── company/       (4)  about, leadership, customer-list, analyst-quotes
```

All docs use YAML frontmatter (`title`, `doc_type`, `audience`) and cross-link with relative markdown links.

## Provenance & honesty

This corpus was **hand-authored** as reference data — it is not LLM-generated marketing passed off as real. Customers, leadership, analysts, and press are explicitly labelled fictional. Per the project's quality bar, no fabricated *model output* is presented as genuine anywhere in this repo.

Verify integrity with `scripts/check_corpus.sh` from the repo root.
