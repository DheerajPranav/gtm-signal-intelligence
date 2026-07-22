---
title: Ideal Customer Profile (ICP)
doc_type: sales
audience: sales, marketing, SDRs, RevOps
priority: critical
---

# Ideal Customer Profile (ICP)

This is the single source of truth for who Northstar sells to. Every battlecard, persona, and outbound message should ground in it. Northstar's ICP is a **B2B SaaS company, 200–2000 employees, Series B to D, that has just hired (or is hiring) a RevOps leader and is outgrowing spreadsheets for revenue reporting.**

## Firmographic signals

- **Industry:** B2B SaaS (software as the core product).
- **Employees:** 200–2000.
- **Revenue:** $20M–$200M ARR.
- **Funding stage:** Series B, C, or D. (Pre-Series-B is usually too early — not enough pipeline complexity; post-Series-D/public often already has a Clari-class incumbent.)
- **Geography:** North America and Western Europe (English-first GTM).
- **Sales motion:** has a real sales team (AEs + managers), not purely self-serve; mid-market or enterprise deals with multi-stage pipelines.

## Technographic signals

- **CRM:** Salesforce **or** HubSpot (required — Northstar models against it).
- **Warehouse:** Snowflake **or** BigQuery (strong fit — enables warehouse-native deployment).
- **BI today:** Looker, Tableau, Mode, **or spreadsheets** — general-purpose tools being stretched to do revenue reporting they weren't built for.
- **Adjacent tools:** often already using Gong, Outreach, or Salesloft (integration surface).

## Behavioral / intent signals

- **Hired a RevOps or Sales Ops leader in the last 12 months** (strongest single trigger).
- **Published RevOps / Sales Ops / Revenue Analytics job openings.**
- **Mentioned "pipeline hygiene," "forecast accuracy," or "single source of truth"** in earnings calls, blogs, or leadership posts.
- Recent funding round (new board-level pressure on forecast discipline).
- New CRO or VP Sales in seat (often triggers a forecasting-process reset).
- Complaints about "spreadsheet forecasting" or "the numbers don't reconcile."

## Buyer personas

- **VP of RevOps** — primary economic buyer and champion.
- **Head of Sales Operations** — day-to-day champion and admin.
- **CRO** — economic buyer; cares about forecast accuracy and board credibility.
- **VP of Sales** — champion/user; cares about rep productivity and clean pipeline.

See persona pages: [for VP of RevOps](../marketing/for-vp-revops.md), [for VP of Sales](../marketing/for-vp-sales.md).

## Disqualifiers (poor fit)

- No data warehouse **and** no plan to adopt one (loses the core differentiator).
- Under ~200 employees / pre-Series-B (too little pipeline).
- Non-SaaS or heavily self-serve with no sales team.
- Already deeply deployed on a satisfied Clari/Pigment implementation with no pain.

## Why the fit is strong

Companies matching this profile feel three pains at once — messy pipeline, distrusted forecast, unclear rep productivity — exactly the [three modules](../product/overview.md) Northstar ships. The warehouse requirement is a feature, not a barrier: it's what lets Northstar deploy in [4–6 weeks](../product/integrations.md) and pass [security review](../product/security.md) fast.

Related: [positioning](positioning.md), [discovery questions](discovery-questions.md).
