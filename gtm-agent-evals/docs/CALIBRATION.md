# Calibration notes

Why the anchors, weights, and thresholds sit where they do. These are **deterministic
gates** — the LLM scores each dimension, but the pass/fail and overall numbers are
computed in code, so they can be inspected, tested, and adjusted without re-prompting.
Every value below is a design choice you can override for your own ICP; the point is that
the choice is explicit.

## ICP rubric — dimension weights

```
behavioral    0.45   technographic  0.15
firmographic  0.20   timing         0.20
```

- **Behavioral dominates (0.45).** For a RevOps platform, the strongest predictor of fit
  is a live buying signal — a VP RevOps hire in the last 12 months, open RevOps
  requisitions, "pipeline hygiene" language in earnings or blogs. A company can look right
  on paper and never buy; behavioral is what separates "fits the ICP" from "in-market now."
- **Firmographic is a baseline gate (0.20), not the headline.** Size and stage (Series B–D,
  200–2000 employees) qualify a company but don't predict urgency. Weighting it too high
  rewards big logos that aren't actually shopping.
- **Timing amplifies behavioral (0.20).** Recent hiring momentum, a funding event, or fresh
  analyst coverage make an existing behavioral signal actionable *now*.
- **Technographic is secondary (0.15).** A mature stack (Salesforce/HubSpot + a warehouse +
  a BI tool) indicates the infrastructure exists to adopt, but it's table stakes, not a
  differentiator.

The weights sum to 1.0, so the overall score stays on the same 0–10 scale as the
dimensions and can never exceed its inputs.

## ICP rubric — 3-band cutoffs

```
strong  overall >= 6.5
weak    4.0 <= overall < 6.5
none    overall < 4.0
```

- **6.5 for "strong."** With behavioral at 0.45, a company that scores ~8 on behavioral and
  ~6–7 elsewhere lands around 7 — clearly worth an SDR's time. Setting the bar at 6.5 keeps
  "strong" meaning *high behavioral intent*, not just a big, well-tooled company: a 9/9 on
  firmographic+technographic with weak behavioral (≈4) still can't reach it alone.
- **4.0 for "weak" vs "none."** Below ~4 the company is either too small/early or shows no
  signal at all — not worth outbound. Between 4.0 and 6.5 is the nurture band: real but not
  in-market.

These cutoffs are tuned so the bundled `examples/data/icp.jsonl` (5 strong / 3 weak /
2 none) classifies as labeled. Re-tune `ICPRubric.BAND_CUTOFFS` for your own ICP.

## Email rubric — would-send thresholds

```
personalization >= 3.5     cta        >= 3.0
relevance       >= 3.5     spam_risk  <= 1.5   (LOWER is better)
```

The gate is **AND across all four** — every dimension must clear its bar. This is
deliberate: a cold email fails on its weakest dimension, not its average. A brilliantly
personalized email with no clear ask still shouldn't go out.

- **Personalization / relevance at 3.5.** On the 0–5 anchor scale, 3 is "some specificity,
  but could apply to similar companies" and 4 is "company-specific." 3.5 forces the email
  past generic-with-a-name into genuinely specific territory — the whole point of research.
- **CTA at 3.0 (looser).** A specific, low-friction ask ("15 min Tuesday?") scores 3–5; the
  bar sits at 3.0 because a clear-but-not-time-bound ask is still sendable. CTA is necessary
  but not where most cold emails actually fail.
- **Spam-risk at 1.5, inverted.** This dimension scores *risk*, so lower is better. 1 is
  "anti-spam design (personalized, authentic)" and 2 is "minimal risk." Holding the ceiling
  at 1.5 keeps anything with even minor spam signals out.

**Missing dimensions fail closed.** In `EmailRubric.evaluate_would_send`, an absent score
defaults to the worst case (0, or 5 for spam-risk), so an incomplete input can never pass
by omission.

## Critique rubric — skeptical by construction

The critique system prompt tells the judge to be *a discerning SDR manager who defaults to
"no."* This is the standard guard against LLM-judge sycophancy: a judge that says yes to
everything measures nothing. The thresholds above are shared with the email rubric so the
writer and the critic can't drift apart. Calibrate by watching the **spam-gap** — bundled
"bad" examples should score materially worse than "good" ones; if they don't, the judge is
being too generous.

## Persona rubric — completeness gate

A persona is "complete" only if all seven fields are present (`title`, `department`,
`seniority`, `pain_points`, `priorities`, `objections`, `buying_influence`). This is a
structural gate, not a quality score — it catches the common failure of a model returning a
title and a vague pain and calling it a stakeholder card. Grounding and distinctness
(pain-point vocabulary per segment) are separate, softer checks; see `GROUNDING_TERMS`.

## Verifying the anchors

The bundled fixtures double as a calibration check:

```bash
python -m gtm_agent_evals run --rubric email_quality --input-file examples/data/email_quality.jsonl
python -m gtm_agent_evals run --rubric icp           --input-file examples/data/icp.jsonl
python -m gtm_agent_evals run --rubric persona       --input-file examples/data/persona.jsonl
```

Each ships 5 passing / 5 failing records with `expected_*` labels; the runner reports
agreement. If you change a weight or threshold, agreement drops until you re-tune the
fixtures — which is the point: the gates and their evidence move together.
