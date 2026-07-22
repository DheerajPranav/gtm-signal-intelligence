---
title: Integrations
doc_type: product
audience: RevOps, IT, data teams
---

# Integrations

Northstar is **warehouse-native**: it models your revenue data where it already lives and writes insights back to the tools your team uses. Standard integrations are included in every tier; the full set is available on [Growth and Enterprise](pricing.md).

## CRM (system of record)

- **Salesforce** — bi-directional sync of accounts, opportunities, activities, and forecast fields. Northstar writes hygiene scores and forecast/commit fields back via reverse ETL.
- **HubSpot** — deals, pipelines, engagements, and custom properties, with the same write-back support.

One of Salesforce or HubSpot is required — it is the system of record Northstar models against.

## Data warehouse (the foundation)

- **Snowflake**
- **BigQuery**

Northstar runs its data model *in your warehouse*. On the Enterprise tier this means **your revenue data never leaves your Snowflake or BigQuery account** — Northstar reads and writes in place. Warehouse connection is what makes the numbers reconcilable with everything else your data team builds.

## Activity & engagement

- **Gong** — import conversation and activity metadata to enrich deal inspection and rep productivity.
- **Outreach** and **Salesloft** — sequence and engagement data tied back to pipeline outcomes.

## BI & collaboration

- **Looker**, **Tableau**, **Mode** — because Northstar models in the warehouse, your existing BI tools can read the same governed tables. Northstar replaces the hand-rolled revenue reporting, not your whole BI stack.
- **Slack** — forecast-change alerts, hygiene nudges, and submission reminders.

## Marketing (sourced pipeline)

- **Marketo** — attribute marketing-sourced pipeline and tie campaigns to forecast impact.

## Provisioning & identity

- **SSO/SAML** via Okta and Azure AD, **SCIM** provisioning (Enterprise). See [security](security.md).

## Deployment

Typical implementation is **4–6 weeks**: connect the CRM and warehouse, map your pipeline stages and forecast categories, configure hygiene rules, and validate against a known quarter. Syncs run **hourly**, or **15-minute near-real-time on Enterprise**.

Because integration is warehouse-first, Northstar avoids the brittle, activity-capture-heavy agent approach of some competitors (see the [Clari battlecard](../sales/battlecard-clari.md)). Related: [product overview](overview.md), [pricing](pricing.md).
