---
title: Forecast Accuracy Module
doc_type: product
audience: CRO, VP Sales, RevOps
---

# Forecast Accuracy

Forecast Accuracy turns a clean pipeline into a forecast leadership can trust. It combines a structured submission workflow, AI-assisted predictions, and rigorous forecast-vs-actual scoring so accuracy improves quarter over quarter instead of staying a guessing game.

## Core capabilities

### Submission & roll-up workflow
Reps submit a commit and best-case each period; managers adjust and roll up; the CRO sees the full tree with every override visible. No more copy-pasting from a spreadsheet the night before the call. Every submission is versioned, so you can replay how the forecast evolved through the quarter.

### AI-assisted forecast
Northstar produces a data-driven forecast from pipeline coverage, historical stage-conversion, deal velocity, and rep-level submission history. It is **transparent by design**: every predicted number expands to show the deals and weights behind it. The AI is a second opinion next to the human commit, never a black box that replaces it.

### Commit vs best-case scenarios
Model the quarter across scenarios — worst case, commit, best case, and Northstar's AI number — and see the gap to target for each. Managers can pressure-test which deals need to land to hit commit.

### Forecast-vs-actual scoring
Northstar scores every past forecast against what actually closed, by rep, manager, and segment. Over time you learn who sandbags, who happy-ears, and where the model is weak — and accuracy compounds.

## The metric that matters

Customers typically start around **~70% forecast accuracy** and reach **90%+ within two quarters** of adopting Northstar — roughly a **+20 point** improvement. That is the number our [case studies](../case-studies/series-c-fintech.md) lead with.

## How it works

Forecast Accuracy builds on the same warehouse-native model as [Pipeline Analytics](module-pipeline-analytics.md). It reads from Salesforce or HubSpot and Snowflake or BigQuery, refreshes hourly, and writes commit/forecast fields back to the CRM via reverse ETL. Submission reminders and forecast-change alerts flow through Slack.

## Why it's different

Unlike bolt-on forecasting inside a conversation-intelligence tool (see the [Gong battlecard](../sales/battlecard-gong.md)) or an enterprise black box (see the [Clari battlecard](../sales/battlecard-clari.md)), Northstar's forecast is warehouse-native, transparent, and fast to deploy — **4–6 weeks**.

Forecast Accuracy is included in the **Core** tier ([pricing](pricing.md)). Related: [rep productivity](module-rep-productivity.md), [positioning](../sales/positioning.md).
