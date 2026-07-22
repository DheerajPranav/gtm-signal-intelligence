"""Six synthetic lead sources + gold labels for the Day-2 extractor.

All text is invented (no real people). Gold labels are the seniority / department /
buying-role a careful human would assign; they let a live run be *scored* rather
than eyeballed, which is the sprint's quality bar. Confidence/evidence are judged
qualitatively in the notebook.

Kinds: 3 LinkedIn "About" blurbs, 2 email signatures, 1 conference bio.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Sample:
    id: str
    kind: str  # linkedin_about | email_signature | conference_bio
    text: str
    gold_seniority: str
    gold_department: str
    gold_buying_role: str


SAMPLES: list[Sample] = [
    Sample(
        id="li-01-vp-revops",
        kind="linkedin_about",
        text=(
            "I lead Revenue Operations at a Series C fintech, owning the systems and "
            "numbers behind our go-to-market. Day to day that means forecasting, "
            "pipeline hygiene, comp plans, and keeping Salesforce honest. I've spent "
            "the last decade turning messy revenue data into decisions leadership can "
            "actually trust. Previously ran Sales Ops at two earlier-stage startups. "
            "Always happy to talk forecasting accuracy and RevOps tooling."
        ),
        gold_seniority="VP",
        gold_department="revenue_operations",
        gold_buying_role="economic_buyer",
    ),
    Sample(
        id="li-02-salesops-manager",
        kind="linkedin_about",
        text=(
            "Sales Operations Manager focused on making reps faster and forecasts less "
            "of a guess. I administer our CRM, build the dashboards the sales team lives "
            "in, and run the weekly pipeline review. I care a lot about clean data and "
            "hate spreadsheets that break every quarter. Currently evaluating tools that "
            "sit on top of Salesforce and Snowflake so we stop hand-rolling reports."
        ),
        gold_seniority="Manager",
        gold_department="sales_operations",
        gold_buying_role="champion",
    ),
    Sample(
        id="li-03-ae-ic",
        kind="linkedin_about",
        text=(
            "Account Executive selling into mid-market SaaS. I carry a quota, run my own "
            "pipeline, and close six-figure deals. I live in the CRM but I don't own it — "
            "I just want my forecast to be right and my dashboards to load. Outside of "
            "work I coach youth soccer."
        ),
        gold_seniority="IC",
        gold_department="sales",
        gold_buying_role="user",
    ),
    Sample(
        id="sig-01-cro",
        kind="email_signature",
        text=(
            "Marcus Delgado\n"
            "Chief Revenue Officer | Cadenza Health\n"
            "m: (415) 555-0148  |  marcus@cadenzahealth.com\n"
            "Book time: cadenzahealth.com/marcus"
        ),
        gold_seniority="C-suite",
        gold_department="executive",
        gold_buying_role="economic_buyer",
    ),
    Sample(
        id="sig-02-analyst",
        kind="email_signature",
        text=(
            "Priya Anand\n"
            "Revenue Analytics Analyst, GTM Data Team\n"
            "Helix Logistics Software\n"
            "priya.anand@helixlogistics.io"
        ),
        gold_seniority="IC",
        gold_department="data_analytics",
        gold_buying_role="user",
    ),
    Sample(
        id="bio-01-director-revops",
        kind="conference_bio",
        text=(
            "Jordan Whitfield is the Director of Revenue Operations at Forgestack, a "
            "Series B developer-tools company, where they built the RevOps function from "
            "scratch. At RevOpsCon 2026 Jordan will share how a four-person team replaced "
            "a wall of spreadsheets with a single source of truth for forecasting and "
            "pipeline. Before Forgestack, Jordan led BizOps at a marketplace startup and "
            "began their career in management consulting."
        ),
        gold_seniority="Director",
        gold_department="revenue_operations",
        gold_buying_role="champion",
    ),
]
