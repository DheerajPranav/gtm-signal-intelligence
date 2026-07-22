# gtm-cli-warmup

Day 1 of a 4-week GTM AI Engineering sprint. A small CLI that turns a company
name into a validated `CompanyDescription`, and logs the tokens, dollars, and
latency of every LLM call to `runs.jsonl`.

The point isn't the CLI. The point is the two habits it establishes for every
project that follows: **structured output via tool use** (never string parsing)
and **cost/latency logging from the first call** (never bolted on later).

## The mental model

An LLM call is a pure function:

```
(system, messages, params) → response + usage
```

Everything else — retries, schemas, evals, agents — is engineering built around
that primitive. `describe.py` is that function with a schema on the output and a
meter on the side.

## Architecture

```
cli.py            argparse, .env loading, rendering
  └─ cost.py      cost_tracker() context manager → runs.jsonl
       └─ describe.py    one Anthropic call, tool_choice forced
            ├─ models.py    CompanyDescription (Pydantic v2)
            └─ pricing.py   per-model rates, promo-aware
```

**Structured output.** `CompanyDescription.model_json_schema()` becomes the
tool's `input_schema`. `tool_choice` forces the model to call it, `strict: true`
guarantees the input validates, and `model_validate` turns the tool input back
into a typed object. No JSON-in-prose, no regex, no repair loop.

**Cost tracking.** `cost_tracker()` is a context manager that flushes in a
`finally` block — a call that was billed gets logged even if the run later
raises. Cached tokens are priced separately (writes at 1.25x input, reads at
0.1x), so the numbers stay right once prompt caching arrives in week 2.

**Promo-aware pricing.** Sonnet 5 has an introductory rate through 2026-08-31.
`rates_for()` takes a date and picks the rate actually in effect, so cost logs
don't silently drift when the promo lapses. Unknown models raise rather than
reporting $0 — a silent zero is worse than a crash.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env      # add your ANTHROPIC_API_KEY
```

## Usage

```bash
.venv/bin/python -m gtm_cli_warmup describe "Notion"
.venv/bin/python -m gtm_cli_warmup describe "Linear" --json
```

### Sample run

> Not yet recorded — pending the first run against a live API key. Paste real
> output here after running; do not fill this in by hand.

### What lands in `runs.jsonl`

One JSON object per API call:

```json
{
  "run_id": "a3f9c21b4d80",
  "operation": "describe",
  "model": "claude-sonnet-5",
  "timestamp": "2026-07-20T14:02:11.481+00:00",
  "latency_ms": 0,
  "input_tokens": 0,
  "output_tokens": 0,
  "cache_creation_tokens": 0,
  "cache_read_tokens": 0,
  "cost_usd": 0.0,
  "stop_reason": "tool_use",
  "error": null,
  "metadata": { "company": "Notion" }
}
```

(Shape is real; the numbers are zeroed placeholders until the first live run.)

## Tests

```bash
.venv/bin/python -m pytest -q
```

Six tests covering promo-rate boundaries, cache-token pricing, unknown-model
failure, JSONL output, and flush-on-exception. No API calls — the tracker takes
any object with a `usage` attribute, so responses are faked.

## Tech stack

Python 3.11+ · Anthropic SDK (`claude-sonnet-5`) · Pydantic v2 · python-dotenv ·
pytest

## Cost

Thinking is explicitly disabled for this task — it's a cheap, well-specified
extraction where reasoning would add latency and tokens without improving the
answer. Expected cost is a fraction of a cent per call; the measured number goes
here after the first live run.

## Sprint context

Project 0 of 4. Next: structured lead extraction (Day 2), then the
`gtm-knowledge-base` hybrid-retrieval RAG with a real eval harness.
