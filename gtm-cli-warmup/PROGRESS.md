# Progress log — gtm-cli-warmup

## Day 1 (2026-07-20)

**Time spent:** ~1 hour (budget was 3)

**Planned tasks:** Anthropic SDK primitives, warmup CLI with structured output
via tool use, cost tracker writing to `runs.jsonl`, README, first commit.

**What actually shipped:**
- Repo scaffolded to the sprint's layout convention (`src/`, `tests/`, `.env.example`).
- `CompanyDescription` Pydantic model; schema derived from it drives the tool definition.
- `describe_company()` — one Anthropic call, `tool_choice` forced, `strict: true`,
  thinking disabled (cheap extraction, reasoning adds no value here).
- `cost_tracker()` context manager → one JSONL line per call with tokens, cost,
  latency, stop_reason. Flushes in `finally`, so billed calls are always logged.
- Promo-aware pricing table: Sonnet 5 intro rate expires 2026-08-31, `rates_for()`
  picks by date. Unknown models raise instead of reporting $0.
- 6 passing tests, no API calls (fake `usage` objects).

**Blockers or surprises:**
- No `ANTHROPIC_API_KEY` in the environment, so the live run is not done. README's
  sample-run section is deliberately empty rather than filled with invented output.
  **This is the one open Day 1 item.**
- Sonnet 5 runs adaptive thinking by default when `thinking` is omitted — not the
  4.6 behaviour. Set `{"type": "disabled"}` explicitly rather than relying on the
  default, or every call quietly pays for reasoning it doesn't need.

**Metrics logged today:**
- Tokens/cost: none yet — no live call made.
- Tests: 6 passed.

**Tomorrow's first action:**
- Add `ANTHROPIC_API_KEY` to `.env`, run `describe "Notion"`, paste the real output
  and cost into the README, then start Day 2 (Pydantic `Lead` model with per-field
  confidence and evidence).

**Confidence level (1 to 5) on hitting week's ship goal:** 4

---

## Day 2 (2026-07-22)

**Time spent:** ~1.5 hours (budget was 3)

**Planned tasks:** structured lead extraction — a Pydantic `Lead` model with
per-field confidence + evidence, populated via tool use, demonstrated on synthetic
inputs.

**What actually shipped:**
- `src/gtm_cli_warmup/lead.py` — `Lead` model with typed enums (`Seniority`,
  `Department`, `BuyingRole`) and per-field `{value, confidence, evidence}` wrappers.
- `extract_lead(text, tracker, client=None)` — one Anthropic call, `tool_choice`
  forced to `record_lead`, `strict: true`, thinking disabled. Schema is closed
  recursively (`additionalProperties: false` everywhere) so the model can't invent
  fields.
- **Prompt-injection guard:** untrusted source text is fenced in
  `<<<SOURCE_TEXT … SOURCE_TEXT>>>` markers inside *user* content only (never the
  system prompt), with a system instruction that text between markers is DATA.
- 8 offline tests (`tests/test_lead.py`) using a `RecordingClient` fake that
  captures `create()` kwargs — proves: schema closed everywhere; well-formed
  tool_use → typed `Lead`; bad enum rejected; evidence required; cost recorded;
  tool forced + thinking disabled; untrusted text fenced in user content only;
  `ExtractError` when no tool call. **Total suite: 14 passed.**
- Notebook `notebooks/lead_extractor/` staged with 6 synthetic inputs + gold labels
  (3 LinkedIn about, 2 email signatures, 1 conference bio). Key-aware: runs live
  extraction with gold scoring if `ANTHROPIC_API_KEY` present, else renders a
  labelled **FIXTURE** — never invents model output.

**Blockers or surprises:**
- Still no `ANTHROPIC_API_KEY`, so the live notebook run + gold-accuracy numbers are
  pending. Wired to run the moment a key exists; no fabricated output committed.
- Anthropic strict tool schemas require every nested object to set
  `additionalProperties: false` — Pydantic's `model_json_schema()` doesn't do this,
  so `_close_schema()` walks the tree and closes each node.

**Metrics logged today:**
- Tokens/cost: none yet — no live call made (offline mock tests only).
- Tests: 14 passed (6 Day-1 + 8 Day-2).

**Confidence level (1 to 5) on hitting week's ship goal:** 4

---

## Day 3 (2026-07-22)

**Time spent:** ~1.5 hours (budget was 3)

**Planned tasks:** build the shared Northstar Analytics knowledge corpus that later
RAG/agent projects retrieve against.

**What actually shipped (in sibling repo `gtm-knowledge-base/`):**
- **30 internally-consistent markdown docs** under `data/northstar/`: 7 product,
  10 sales (ICP, positioning, discovery, objections, playbook, 4 battlecards, FAQ),
  4 case studies, 5 marketing, 4 company. All with YAML frontmatter + relative
  cross-links, all consistent with one canonical fact sheet.
- Two READMEs (corpus fact sheet + repo README) and
  `scripts/check_corpus.sh` — a **bash-3.2-compatible integrity gate** asserting
  per-category counts, frontmatter, canonical-fact consistency (ICP bounds,
  competitor set, pricing, locked metrics) and a contradiction guard. **Gate exit 0.**
- Every fictional customer/leader/analyst is explicitly labelled fictional — no
  invented LLM output presented as genuine.

**Blockers or surprises:**
- macOS ships bash 3.2 (no associative arrays); first draft of `check_corpus.sh`
  used `declare -A` and failed. Rewrote counts with a `case` function. One regex
  over-escaped the `$` in the ARR band; simplified to `20M.*200M`. Gate green after.

**Metrics logged today:**
- Docs: 30 (7/10/4/5/4). Corpus gate: exit 0. No API cost (authored directly).

**Confidence level (1 to 5) on hitting week's ship goal:** 4
