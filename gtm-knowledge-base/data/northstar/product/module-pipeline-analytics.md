---
title: Pipeline Analytics Module
doc_type: product
audience: RevOps, Sales Ops, sales managers
---

# Pipeline Analytics

Pipeline Analytics is the Northstar module that keeps your pipeline honest. It scores hygiene, exposes where deals stall, and makes stage conversion measurable — so pipeline reviews start from facts instead of vibes.

## Core capabilities

### Pipeline hygiene scoring
Every open deal gets a hygiene score based on rules you configure: missing close dates, stale next steps, past-due opportunities, amounts that don't match line items, single-threaded contacts, and stage/age mismatches. Managers see a ranked list of the deals dragging the number down, and reps get a punch list before every review.

### Stage-conversion analysis
Northstar computes conversion rates and average time-in-stage across your funnel, segmented by segment, region, rep, source, and deal size. You can see exactly where deals leak — for example, that mid-market deals convert 3x better past the "Technical Validation" stage, so getting there earlier matters most.

### Deal inspection
A single deal view stitches together CRM fields, [Gong](integrations.md) activity, engagement from Outreach/Salesloft, and warehouse facts. Inspect any deal's full timeline, contact map, and risk flags without tab-hopping.

### Movement & slippage tracking
Northstar snapshots pipeline daily so you can answer the questions spreadsheets can't: what moved in or out of the quarter, which deals slipped and how many times, and how this week's pipeline compares to the same point last quarter.

## How it works

Pipeline Analytics reads opportunity and activity data from Salesforce or HubSpot and models it in your Snowflake or BigQuery warehouse. Syncs run hourly (15-minute near-real-time on Enterprise). Because the model lives in your warehouse, the same numbers power Northstar dashboards, Slack alerts, and any downstream BI tool.

## Signals it surfaces

- Deals with no activity in 14+ days
- Pushed close dates (and how many times)
- Stages entered without the prior stage's exit criteria met
- Coverage ratio vs target, by team and segment
- Single-threaded deals above a value threshold

## Outcomes

Teams use Pipeline Analytics to cut weekly review prep from **~6 hours to ~30 minutes** and to stop discovering slipped deals at quarter-end. It is included in the **Core** tier — see [pricing](pricing.md) — and pairs directly with [Forecast Accuracy](module-forecast-accuracy.md), which turns a clean pipeline into a trustworthy forecast.

Related: [product overview](overview.md), [ICP definition](../sales/icp-definition.md).
