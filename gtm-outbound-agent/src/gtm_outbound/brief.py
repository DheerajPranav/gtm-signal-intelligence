"""Account Brief assembly + markdown rendering.

Pure and deterministic: given the outputs of the five agents, `assemble_brief` builds the
`AccountBrief` model and `render_brief_md` turns it into a GitHub-renderable document. No
LLM here, so the whole reporting layer is testable offline — the numbers in the brief are
exactly the numbers the agents produced, never re-derived or rounded into something new.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from .models import (
    AccountBrief,
    CompanyProfile,
    EmailDraft,
    EmailEval,
    FitScore,
    Persona,
    Sourced,
)


def assemble_brief(
    profile: CompanyProfile,
    fit: FitScore,
    personas: list[Persona],
    drafts: list[EmailDraft],
    evals: dict[str, EmailEval],
    cost_usd: float,
    latency_ms: float,
    timestamp: datetime,
) -> AccountBrief:
    """Build an AccountBrief, keying emails and evals by the run-wide-unique variant_id."""
    return AccountBrief(
        target=profile.target,
        profile=profile,
        fit=fit,
        personas=personas,
        emails={d.variant_id: d for d in drafts},
        evals=evals,
        cost_usd=cost_usd,
        latency_ms=latency_ms,
        timestamp=timestamp,
    )


def would_send_pass_rate(brief: AccountBrief) -> Optional[float]:
    """Fraction of evaluated emails a discerning SDR would send. None if nothing evaluated."""
    if not brief.evals:
        return None
    return sum(1 for e in brief.evals.values() if e.would_send) / len(brief.evals)


def _fmt_sourced(v: Sourced) -> str:
    return f"{v.value} ([source]({v.source_url}))"


def _profile_summary(profile: CompanyProfile) -> list[str]:
    lines = []
    for name in CompanyProfile.SCALAR_FIELDS:
        got = getattr(profile, name)
        lines.append(f"- **{name.replace('_', ' ')}:** "
                     f"{_fmt_sourced(got) if got else '_not found_'}")
    for name in CompanyProfile.LIST_FIELDS:
        vals = getattr(profile, name)
        if vals:
            lines.append(f"- **{name.replace('_', ' ')}:** "
                         + "; ".join(_fmt_sourced(v) for v in vals))
    return lines


def render_brief_md(brief: AccountBrief) -> str:
    b = brief
    rate = would_send_pass_rate(b)
    rate_str = "not evaluated" if rate is None else f"{rate:.0%} ({sum(e.would_send for e in b.evals.values())}/{len(b.evals)})"

    out: list[str] = [
        f"# Account Brief — {b.target.name} (`{b.target.domain}`)",
        "",
        f"> **Would-send pass rate: {rate_str}** · "
        f"ICP fit: **{b.fit.score:.2f}** · "
        f"cost: ${b.cost_usd:.4f} · latency: {b.latency_ms:.0f} ms",
        "",
        f"_Generated {b.timestamp:%Y-%m-%d %H:%M UTC}. Northstar Analytics is fictional._",
        "",
        "## Company Summary",
        "",
        *_profile_summary(b.profile),
        "",
        "## ICP Fit",
        "",
        f"**Overall: {b.fit.score:.2f} / 1.00**",
        "",
        "| Dimension | Score |",
        "|---|---|",
        f"| Firmographic | {b.fit.firmographic_score:.2f} |",
        f"| Technographic | {b.fit.technographic_score:.2f} |",
        f"| Behavioral | {b.fit.behavioral_score:.2f} |",
        f"| Timing | {b.fit.timing_score:.2f} |",
        "",
        b.fit.reasoning,
        "",
    ]
    if b.fit.cited_signals:
        out += ["**Cited signals:** " + "; ".join(b.fit.cited_signals), ""]

    out += ["## Personas", ""]
    for p in b.personas:
        name = f"{p.name} — " if p.name else ""
        out += [
            f"### {name}{p.title}",
            f"_{p.seniority.value} · {p.department.value} · {p.buying_influence.value}_",
            "",
            f"- **Pain points:** {'; '.join(p.pain_points)}",
            f"- **Priorities:** {'; '.join(p.priorities)}",
            f"- **Objections:** {'; '.join(p.objections)}",
            "",
        ]

    out += ["## Emails", ""]
    for p in b.personas:
        drafts = b.emails_for_persona(p.id)
        if not drafts:
            continue
        out += [f"### For {p.title}", ""]
        for d in sorted(drafts, key=lambda x: x.variant_angle.value):
            ev = b.eval_for(d.variant_id)
            out += [
                f"#### {d.variant_angle.value} — {d.subject}",
                "",
                d.body,
                "",
                "_Hooks:_ " + "; ".join(d.personalization_hooks),
                "",
            ]
            if ev:
                verdict = "✅ send" if ev.would_send else "❌ hold"
                out += [
                    f"_Critique:_ {verdict} · personalization {ev.personalization_score:.0f}/5 · "
                    f"relevance {ev.relevance_score:.0f}/5 · CTA {ev.cta_score:.0f}/5 · "
                    f"spam-risk {ev.spam_risk:.0f}/5",
                    "",
                ]

    out += [
        "## Cost & Latency",
        "",
        f"- **Total cost:** ${b.cost_usd:.4f}",
        f"- **Total latency:** {b.latency_ms:.0f} ms",
        "",
    ]
    return "\n".join(out) + "\n"
