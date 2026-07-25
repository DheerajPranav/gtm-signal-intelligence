"""Labeled eval set for the scoring agent: 15 fictional target companies.

Unlike the Day-9 enrichment gold set (real companies, so ground truth is unverifiable
from memory), these companies are *fictional and constructed against the ICP*. Every
label is therefore honest by construction: the profile was written to match, partially
match, or violate Northstar's ICP, and the band is what the construction intended. This
is the one place ground truth can be asserted without a live lookup.

Bands: strong (clear ICP match), weak (partial), none (a hard disqualifier present).
Ordinals (none=0, weak=1, strong=2) drive the Spearman correlation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from gtm_outbound.models import CompanyProfile, Sourced, TargetCompany

Band = Literal["strong", "weak", "none"]
BAND_ORDINAL: dict[str, int] = {"none": 0, "weak": 1, "strong": 2}


def _s(value: str, domain: str) -> Sourced[str]:
    return Sourced[str](value=value, source_url=f"https://{domain}/about", confidence=0.9)


def _profile(domain: str, name: str, **fields) -> CompanyProfile:
    kw: dict = {"target": TargetCompany(domain=domain, name=name),
                "last_updated": datetime(2026, 7, 1, tzinfo=timezone.utc)}
    for k in CompanyProfile.SCALAR_FIELDS:
        if k in fields:
            kw[k] = _s(fields[k], domain)
    for k in CompanyProfile.LIST_FIELDS:
        if k in fields:
            kw[k] = [_s(v, domain) for v in fields[k]]
    return CompanyProfile(**kw)


# Each entry: (band, profile). Written so the band follows from the ICP, not vice versa.
GOLD: list[tuple[Band, CompanyProfile]] = [
    # ── 7 strong: B2B SaaS, right size/stage, required CRM + warehouse, live trigger ──
    ("strong", _profile(
        "flowmetric.io", "FlowMetric",
        industry="B2B SaaS", sub_industry="RevOps analytics", size_band="500-1000",
        funding_stage="Series C", tech_stack=["Salesforce", "Snowflake", "Gong"],
        recent_news=["Raised $40M Series C (Mar 2026)"],
        key_people=["Dana Cole, VP RevOps (hired Apr 2026)"],
        buying_signals=["Hired VP RevOps 3 months ago", "Open Sales Ops Analyst role"])),
    ("strong", _profile(
        "pipelaunch.com", "PipeLaunch",
        industry="B2B SaaS", sub_industry="marketing automation", size_band="200-500",
        funding_stage="Series B", tech_stack=["HubSpot", "BigQuery"],
        recent_news=["Named new CRO (Feb 2026)"],
        buying_signals=["CEO blogged about 'forecast accuracy' problems"])),
    ("strong", _profile(
        "cadencehq.com", "Cadence",
        industry="B2B SaaS", sub_industry="sales engagement", size_band="1000-2000",
        funding_stage="Series D", tech_stack=["Salesforce", "Snowflake", "Outreach"],
        key_people=["Sam Reyes, Head of Sales Operations (hired 2026)"],
        buying_signals=["Hired Head of Sales Ops", "Scaling AE team 40%"])),
    ("strong", _profile(
        "gridpoint.app", "GridPoint",
        industry="B2B SaaS", sub_industry="fintech infrastructure", size_band="200-500",
        funding_stage="Series C", tech_stack=["Salesforce", "BigQuery"],
        buying_signals=["Multiple RevOps job postings", "Team complaining about spreadsheet forecasting"])),
    ("strong", _profile(
        "northsignal.io", "NorthSignal",
        industry="B2B SaaS", sub_industry="observability", size_band="500-1000",
        funding_stage="Series C", tech_stack=["HubSpot", "Snowflake"],
        recent_news=["Closed $55M round (Jan 2026)"],
        buying_signals=["New VP of Sales in seat", "Recent funding round"])),
    ("strong", _profile(
        "clararev.com", "ClaraRev",
        industry="B2B SaaS", sub_industry="RevOps", size_band="200-500",
        funding_stage="Series B", tech_stack=["Salesforce", "Snowflake"],
        buying_signals=["Hired Head of Sales Ops", "Leadership posted about 'single source of truth'"])),
    ("strong", _profile(
        "vantatiles.com", "VantaTiles",
        industry="B2B SaaS", sub_industry="workflow software", size_band="500-1000",
        funding_stage="Series D", tech_stack=["Salesforce", "Snowflake", "Salesloft"],
        key_people=["Priya Anand, VP RevOps (hired 2026)"],
        buying_signals=["Hired RevOps leader", "Recent funding"])),

    # ── 4 weak: partial match — a dimension absent, borderline, or trigger-free ──
    ("weak", _profile(
        "brightledger.com", "BrightLedger",
        industry="B2B SaaS", sub_industry="accounting software", size_band="200-500",
        funding_stage="Series C", tech_stack=["Salesforce"],  # warehouse not researched
        buying_signals=["Hiring across GTM"])),  # no clear RevOps trigger
    ("weak", _profile(
        "tinyscale.io", "TinyScale",
        industry="B2B SaaS", sub_industry="developer tools", size_band="100-200",  # under 200
        funding_stage="Series B", tech_stack=["HubSpot", "Snowflake"],
        buying_signals=["Posted a RevOps opening"])),
    ("weak", _profile(
        "stablmotion.com", "StablMotion",
        industry="B2B SaaS", sub_industry="logistics SaaS", size_band="500-1000",
        funding_stage="Series C", tech_stack=["Salesforce", "Snowflake"])),  # no behavioral/timing
    ("weak", _profile(
        "orbitdesk.com", "OrbitDesk",
        industry="B2B SaaS", sub_industry="customer support", size_band="200-500",
        tech_stack=["HubSpot", "BigQuery"],  # funding stage not found
        buying_signals=["One mention of pipeline hygiene"])),

    # ── 4 none: a hard ICP disqualifier is present ──
    ("none", _profile(
        "shopfront.co", "ShopFront",
        industry="E-commerce retail", sub_industry="DTC apparel", size_band="1000-2000",
        tech_stack=["Shopify"],  # non-SaaS, no CRM/warehouse
        buying_signals=["Opening new retail stores"])),
    ("none", _profile(
        "seedlingapp.com", "Seedling",
        industry="B2B SaaS", sub_industry="note-taking", size_band="1-50",  # far too small
        funding_stage="Seed",
        buying_signals=["Just closed pre-seed"])),
    ("none", _profile(
        "paperpush.com", "PaperPush",
        industry="B2B SaaS", sub_industry="HR software", size_band="200-500",
        tech_stack=["Salesforce"],
        recent_news=["CTO: 'no plans to adopt a data warehouse; spreadsheets are fine'"],
        buying_signals=["Explicitly rejected warehouse adoption"])),  # hard technographic DQ
    ("none", _profile(
        "summitrev.com", "SummitRev",
        industry="B2B SaaS", sub_industry="revenue intelligence", size_band="1000-2000",
        funding_stage="Series D", tech_stack=["Salesforce", "Snowflake", "Clari"],
        recent_news=["Deployed Clari 6 months ago, team very satisfied"],
        buying_signals=["Happy with current forecasting stack"])),  # satisfied incumbent DQ
]


def gold_bands() -> list[str]:
    return [band for band, _ in GOLD]


def band_counts() -> dict[str, int]:
    counts = {"strong": 0, "weak": 0, "none": 0}
    for band, _ in GOLD:
        counts[band] += 1
    return counts
