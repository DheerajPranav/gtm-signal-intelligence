# Enrichment eval — how to populate the gold set

`enrichment_gold.jsonl` ships with **10 real companies and empty ground truth**. This is
deliberate, and the harness will not report an accuracy number until you fill it in.

## Why it's empty

The Day 9 DoD asks for "hand-curated ground truth" and "at least 70% field accuracy."
Ground truth here means claims about **real companies** — headcount, funding stage,
industry. Those change constantly, and no one authoring this file can verify them from
memory. Pre-filling plausible-looking values would produce an accuracy number measured
against guesses, which is worse than no number: it looks rigorous and isn't.

This repo already had one incident where invented metrics were written into a progress
log (see `../../gtm-signal-intelligence/.genesis/checkpoints/CURRENT.md`). The empty
file and the verification gate exist so that cannot recur here.

## How to populate

For each row, look the company up and fill `expected`, then flip `verified` to `true`:

```jsonc
{
  "domain": "linear.app",
  "name": "Linear",
  "verified": true,                    // <- flip once you've checked
  "expected": {
    "industry": "B2B SaaS",
    "sub_industry": "project management",
    "size_band": "50-200",             // use the bands the agent emits
    "funding_stage": "Series C"
  },
  "sources": ["https://…"],            // where you verified it
  "verified_on": "2026-07-24"
}
```

Guidance:

- **`size_band`** — match the agent's banding (`"50-200"`, `"200-500"`, `"500-1000"`,
  `"1000+"`). Comparison is exact-match on the band string, so a mismatch in convention
  reads as a wrong answer.
- **Partial rows are fine.** Leave a field `null` if you can't verify it; the harness
  skips nulls rather than counting them as misses.
- **Record `verified_on`.** Funding stage and headcount go stale; a year-old gold set
  measures drift, not accuracy.

## Running it

```bash
# Grounding checks only — no API key, no network.
.venv/bin/python evals/run_enrichment_eval.py --offline

# Full run: live research against each domain.
.venv/bin/python evals/run_enrichment_eval.py
```

Rows with `verified: false` are excluded from field accuracy and counted separately, so
the report always states how much of the set actually backed the number.

---

# Other evals in this directory

The same discipline applies to every harness here: anything needing a live model call is
**gated** — with no `ANTHROPIC_API_KEY` the run reports readiness and prints `not measured`
rather than a fabricated figure. All three have an `--offline` mode.

| Harness | Day | Ground truth | Live metrics |
|---|---|---|---|
| `run_enrichment_eval.py` | 9 | 10 real companies (`enrichment_gold.jsonl`), **unverified by design** | field accuracy (gated on human verification) |
| `run_scoring_eval.py` | 10 | 15 **fictional** companies (`scoring_gold.py`), labeled by construction | Spearman rank correlation (DoD > 0.6) + 3-band confusion |
| `run_persona_eval.py` | 11 | 4 contrasting companies (reused from `scoring_gold.py`) | exactly-N-complete rate, KB-grounding proxy, cross-company distinctness |

Why the scoring/persona gold sets *can* assert ground truth while enrichment can't: their
companies are **fictional and constructed against a rubric**, so the intended label is known
by design. The enrichment set describes **real** companies, whose headcount and funding
can't be verified from memory — so that one stays empty until a human fills it in.

```bash
.venv/bin/python evals/run_scoring_eval.py --offline
.venv/bin/python evals/run_persona_eval.py --offline
```
