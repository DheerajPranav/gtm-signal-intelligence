---
title: Security & Compliance
doc_type: product
audience: IT, security, procurement, RevOps
---

# Security & Compliance

Northstar handles revenue data — some of the most sensitive data a company owns. Security is built into the architecture, not bolted on.

## Certifications & compliance

- **SOC 2 Type II** — audited annually; report available under NDA to Enterprise prospects and customers.
- **GDPR** — compliant; DPA available; EU data residency option.
- **ISO 27001** — certification in progress.
- Annual third-party **penetration test**; summary letter available on request.

## Warehouse-native architecture (the key control)

Northstar's biggest security advantage is architectural. On the **Enterprise** tier, Northstar deploys **warehouse-native**: the data model runs inside your own **Snowflake or BigQuery** account and **your revenue data never leaves your warehouse**. Northstar reads and writes in place rather than copying your pipeline into a third-party system. This shrinks the trust surface dramatically and usually shortens security review.

## Data protection

- **Encryption:** AES-256 at rest, TLS 1.2+ in transit.
- **Access control:** SSO/SAML (Okta, Azure AD), SCIM provisioning, and role-based access control (RBAC) down to the team and field level.
- **Audit logging:** every data access and configuration change is logged and exportable.
- **Least privilege:** Northstar requests scoped, revocable credentials to your CRM and warehouse.

## Sub-processors & data handling

Northstar publishes its **sub-processor list** and notifies customers of changes. Standard (non-warehouse-native) deployments process data in US or EU regions per customer choice. Data retention and deletion follow documented policies and honor customer deletion requests.

## Reliability

- Hourly syncs (15-minute near-real-time on Enterprise).
- Documented backup and disaster-recovery procedures.
- Status page and incident-notification process.

## Procurement support

For security reviews we provide: the SOC 2 Type II report, a completed CAIQ/SIG questionnaire, the DPA, the pen-test summary, and an architecture diagram of the warehouse-native deployment. This is typically why Northstar clears security review faster than heavier, data-copying platforms.

See also: [integrations](integrations.md), [pricing](pricing.md), and the [ICP definition](../sales/icp-definition.md) — security review speed is a real differentiator for the RevOps and IT buyers in our ICP.
