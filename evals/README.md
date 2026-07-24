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
