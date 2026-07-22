---
title: Sales FAQ
doc_type: sales
audience: AEs, SDRs, prospects
---

# Sales FAQ

Quick answers to the questions prospects ask most. For depth, follow the links.

## Product

**What exactly is Northstar?**
The RevOps analytics layer for teams outgrowing spreadsheets and BI tools not built for revenue data. Three modules: [Pipeline Analytics](../product/module-pipeline-analytics.md), [Forecast Accuracy](../product/module-forecast-accuracy.md), and [Rep Productivity](../product/module-rep-productivity.md).

**Do you replace our CRM?**
No. Northstar sits on top of Salesforce or HubSpot and reads/writes to it. It's an analytics layer, not a system of record.

**Do you replace Looker/Tableau/Mode?**
No — we complement your BI. Northstar models in the same warehouse, so your BI can read the governed tables. We replace the hand-rolled *revenue* reporting, not your whole BI stack.

**Does the AI replace our forecast?**
No. The AI forecast is a **transparent second opinion** next to the human commit; every number traces to the deals behind it. See [Forecast Accuracy](../product/module-forecast-accuracy.md).

## Data & security

**Do you need a data warehouse?**
Snowflake or BigQuery is our strong fit and enables warehouse-native deployment. If you're adopting one soon, we can start on the CRM. No warehouse and no plan is usually a poor fit — see the [ICP](icp-definition.md).

**Does our data leave our environment?**
On Enterprise, **no** — warehouse-native deployment keeps data in your Snowflake/BigQuery. See [security](../product/security.md).

**Are you SOC 2 compliant?**
Yes, SOC 2 Type II, plus GDPR; ISO 27001 in progress. Report available under NDA.

## Integrations

**Do you integrate with Excel / spreadsheets?**
Not explicitly — Northstar is built to *replace* spreadsheet-based revenue reporting, not integrate with it. Data flows from your CRM and warehouse; you can export from Northstar, but spreadsheets aren't a supported source. (Honest answer for prospects who ask.)

**Do you work with Gong?**
Yes — we [import Gong activity](../product/integrations.md) to enrich deal inspection and rep productivity.

## Commercials

**How much does it cost?**
Core $2,500/mo (up to 40 seats), Growth $6,000/mo (up to 120 seats), Enterprise custom. Full detail: [pricing](../product/pricing.md).

**How long to deploy?**
4–6 weeks after a 14-day proof-of-value pilot.

**How do you compare to Clari?**
Warehouse-native, transparent, mid-market-priced, faster to deploy. See the [Clari battlecard](battlecard-clari.md).

Related: [objection handling](objection-handling.md), [positioning](positioning.md).
